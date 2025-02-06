#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2024 Brandon Nguyen

'''
Converts meson build files to hermetic build system (Soong, Bazel)

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
import typing as T

from typing import Any
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from mesonbuild.backend.hermeticbackend import HermeticState
from mesonbuild import environment, coredata

jinja_env = Environment(
    loader=FileSystemLoader(Path(__file__).parent.resolve() / 'templates/')
)

if T.TYPE_CHECKING:
    from mesonbuild.coredata import SharedCMDOptions

    class CMDOptions(SharedCMDOptions):

        configdir: str

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
        self._cpu_family: str = ''
        self._cpu: str = ''
        self._host_machine: str = ''
        self._build_machine: str = ''
        # project_config.meson_options
        self._meson_options: dict[str, int | bool | str] = {}
        try:
            with open(self._path, "rb") as f:
                data = tomllib.load(f)
                self._toml_data = data
                self.parse_config_data()
        except Exception as e:
            print('Error opening file:', e)

    
    @property
    def build(self):
        return self._build
    
    @property
    def project_name(self):
        return self._project_name
    
    @property
    def cpu_family(self):
        return self._cpu_family
    
    @property
    def cpu(self):
        return self._cpu
    
    @property
    def host_machine(self):
        return self._host_machine
    
    @property
    def build_machine(self):
        return self._build_machine

    def project_options(self) -> list[str]:
        opts = []
        for key in self._meson_options:
            opt = f'-D{key}={self._meson_options[key]}'
            opts.append(opt)
        return opts

    def cmd_options(self):
        pass


    def parse_config_data(self):
        project_config_dict = self._toml_data.get('project_config')
        self._build = self._toml_data.get('build')
        self._project_name = project_config_dict.get('name')
        self._cpu_family = project_config_dict.get('host_machine').get('cpu_family')
        self._cpu = project_config_dict.get('host_machine').get('cpu')
        self._host_machine = project_config_dict.get('host_machine').get('host_machine')
        self._build_machine = project_config_dict.get('host_machine').get('build_machine')
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
    def __init__(self, build_state: HermeticState):
        self._build_state = build_state
        self._path_to_template = Path(self._build_type.lower() + '/' + self._template_file_name)

    def render(self) -> str:
        raise NotImplementedError('Not implemented')


def generate(hermetic_config: HermeticConfig, cmd_opts):
    env = environment.Environment('./', './', cmd_opts)

def main():
    parser = argparse.ArgumentParser(description='Generates hermetic build files from meson')
    parser.add_argument('--config', 
                        required=True,
                        help='The path to a valid config file (toml).',)

    args = parser.parse_args()
    # options = T.cast('SharedCMDOptions', args)

    config = HermeticConfig(args.config)
    # generate(config, options)
    print(config)


if __name__ == '__main__':
    main()