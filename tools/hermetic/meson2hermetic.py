#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2024 Brandon Nguyen

'''
Converts meson build files to a hermetic build system (Soong, Bazel)
Emits the hermetic build files directly in directory.

Intended Usage:
    Within the target directory run command:
    ```
    python ~/<path>/<to>/tools/hermetic/meson2hermetic.py --config=/path/to/aosp.toml
    ```

This scripts requires python 3.11 to run.

Dependencies Used:
 - jinja2

config file format example:

# aosp.toml
build = 'Soong'

[project_config]
name = 'android_aarch64_drivers'

[project_config.host_machine]
cpu_family = 'aarch64'
cpu = 'aarch64'
host_machine = 'android'
build_machine = 'linux'

[project_config.meson_options]
platforms = 'android'
android-libbacktrace = 'disabled'
gallium-drivers = ''
vulkan-drivers = 'freedreno,gfxstream'
freedreno-kmds = 'kgsl'
platform-sdk-version = 33
# config file end
'''

import argparse
import tomllib
import enum
import typing as T
import os
import pprint

from typing import Any
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from mesonbuild import build, environment, coredata, interpreter, mlog, hermeticbuild
from mesonbuild.envconfig import MachineInfo
from mesonbuild.options import OptionKey
from mesonbuild.utils.universal import set_meson_command

jinja_env = Environment(
    loader=FileSystemLoader(Path(__file__).parent.resolve() / 'templates/')
)

if T.TYPE_CHECKING:
    from mesonbuild.coredata import SharedCMDOptions

    class CMDOptions(SharedCMDOptions):

        configdir: str

class DefaultCMDOptions(enum.Enum):
    SOURCE_DIR = os.getcwd()
    BUILD_DIR = os.getcwd() + '/hermetic-build'
    CROSS_FILE = []
    NATIVE_FILE = []
    BACKEND = 'hermetic'

class HermeticConfig:
    '''
    The data structure to represent the .toml file passed via --config
    '''
    def __init__(self, config_file: Path):
        self._path: Path = config_file
        self._toml_data: dict[str, Any] = {}
        self._build: str = ''
        # project_config
        self._project_name: str = ''
        # project_config.host_machine
        self._host_machine: dict[str, str] = {}
        self._build_machine: dict[str, str] = {}
        self._target_machine: dict[str, str] = {}
        # project_config.meson_options
        self._meson_options: dict[str, int | bool | str] = {}
        try:
            with open(self._path, "rb") as f:
                data = tomllib.load(f)
                self._toml_data = data
                self.parse_config_data()
        except Exception as e:
            exit(f'Error trying to open config file:', e)

    
    @property
    def build(self):
        return self._build
    
    @property
    def project_name(self):
        return self._project_name
    
    @property
    def host_machine(self) -> dict[str, str]:
        return self._host_machine
    
    @property
    def build_machine(self) -> dict[str, str]:
        return self._build_machine
    
    @property
    def target_machine(self) -> dict[str, str]:
        return self._target_machine
    
    @property
    def meson_options(self):
        return self._meson_options

    def project_options(self) -> list[str]:
        opts = []
        for key in self._meson_options:
            opt = f'{key}={str(self._meson_options[key]).lower()}'
            opts.append(opt)
        return opts

    def parse_config_data(self):
        project_config_dict = self._toml_data.get('project_config')
        self._build = self._toml_data.get('build')
        self._project_name = project_config_dict.get('name')

        if project_config_dict.get('host_machine'):
            self._host_machine = project_config_dict.get('host_machine')

        if project_config_dict.get('build_machine'):
            self._host_machine = project_config_dict.get('host_machine')

        if project_config_dict.get('target_machine'):
            self._host_machine = project_config_dict.get('host_machine')

        self._meson_options = project_config_dict.get('meson_options')
        for key in self._meson_options:
            setattr(self, key, self._meson_options[key])

    def __contains__(self, key):
        return key in self.__dict__
    
    def __str__(self):
        return f'''
HermeticConfig({self._path})
build: {self._build}
project_name: {self._project_name}
cpu_family: {self._cpu_family}
cpu: {self._cpu}
host_machine: {self._host_machine}
build_machine: {self._build_machine}
meson_options: {self._meson_options}
        '''

class HermeticCodeGenerator:
    '''
    Parent class for any class that generates code via jinja2 templates
    '''
    def __init__(self, build_state: hermeticbuild.HermeticState):
        self._build_state = build_state
        self._path_to_template = Path(self._build_type.lower() + '/' + self._template_file_name)

    def render(self) -> str:
        raise NotImplementedError('Not implemented')


def render_build_file(hermetic_state: hermeticbuild.HermeticState, build_type = 'Soong'):
    print(hermetic_state)


def generate(config: HermeticConfig, cmd_opts: argparse.Namespace):
    env = environment.Environment(cmd_opts.sourcedir,
                                  cmd_opts.builddir,
                                  cmd_opts,)
    
    # Override native compiler options
    # if config.host_machine:
    #     env.machines.host = MachineInfo.from_literal(config.host_machine)
    # if config.build_machine:
    #     env.machines.build = MachineInfo.from_literal(config.build_machine)
    # if config.target_machine:
    #     env.machines.target = MachineInfo.from_literal(config.target_machine)

    b = build.Build(env)
    
    if env.is_cross_build():
        print('Building with cross compilation configurations...')

    user_defined_options = T.cast('CMDOptions', argparse.Namespace(**vars(cmd_opts)))
    d = {OptionKey.from_string(k): config.meson_options[k] for k in config.meson_options}
    d.update(user_defined_options.cmd_line_options)
    user_defined_options.cmd_line_options = d

    intr = interpreter.Interpreter(b, user_defined_options=user_defined_options)

    try:
        print(f'Interpreting {cmd_opts.sourcedir}/meson.build ...')
        intr.run()
    except Exception as e:
        raise e
    
    hermetic_state = intr.backend.generate()
    render_build_file(hermetic_state)

def create_default_options(args: argparse.Namespace) -> argparse.Namespace:
    options = T.cast('CMDOptions', args)

    # Configure option defaults
    options.configdir = args.config
    options.sourcedir = DefaultCMDOptions.SOURCE_DIR.value
    options.builddir = DefaultCMDOptions.BUILD_DIR.value
    options.cross_file = DefaultCMDOptions.CROSS_FILE.value
    options.backend = DefaultCMDOptions.BACKEND.value
    options.projectoptions = []
    options.native_file = []
    options.cmd_line_options = {}
    options.wipe = False
    options.pager = False

    return options

def main():
    parser = argparse.ArgumentParser(description='Generates hermetic build files from meson')
    parser.add_argument('--config', 
                        required=True,
                        help='The path to a valid config file (toml).',)

    args = parser.parse_args()
    config = HermeticConfig(args.config)

    mlog.set_quiet()

    # meson command is not relevant to our script, but we have to set
    # to bypass 'no command' error
    set_meson_command('NULL')

    options = create_default_options(args)

    # Add in our own configs/options
    options.projectoptions = config.project_options()
    coredata.parse_cmd_line_options(options)
    generate(config, options)


if __name__ == '__main__':
    main()