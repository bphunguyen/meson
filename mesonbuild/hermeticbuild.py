# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 The Meson development team
from __future__ import annotations

import typing as T
import os

from mesonbuild.utils import universal
from mesonbuild.utils.core import MesonException

from . import build

class HermeticState:

    def __init__(self):
        self.shared_libraries: T.List[HermeticSharedLibrary] = []
        self.static_libraries: T.List[HermeticStaticLibrary] = []
        self.custom_targets: T.List[HermeticCustomTarget] = []
        self.python_targets: T.List[HermeticPythonTarget] = []

        # Global flags used amongst all Static/Shared Libraries
        self.conlyflags: T.List[str] = []
        self.cppflags: T.List[str] = []

        self.cstd: str = ''
        self.cpp_std: str = ''

    def copts(self):
        pass

    def __str__(self):
        return f'HermeticState:\n\tshared_libraries len: {len(self.shared_libraries)}' \
            f'\n\tstatic_libraries len: {len(self.static_libraries)}' \
            f'\n\tcustom_targets len: {len(self.custom_targets)}' \
            f'\n\tpython_targets len: {len(self.python_targets)}'


class HermeticStaticLibrary:

    def __init__(self):
        self.name: str = ''
        self.subdir: str = '' # Location of this StaticLibrary's definition
        self.dirs: T.List[str] = []
        self.visibility: T.List[str] = []
        self.srcs: T.List[str] = []
        # In Bazel, these headers are one merged list.
        self.generated_headers: T.List[str] = []
        self.generated_sources: T.List[str] = []

        # Bazel specific attributes
        self.deps: T.List[str] = []
        self.target_compatible_with: T.List[str] = []

        # Soong specific attributes
        self.local_include_dirs: T.List[str] = []
        self.static_libs: T.List[str] = []
        self.whole_static_libs: T.List[str] = []
        self.shared_libs: T.List[str] = []
        self.header_libs: T.List[str] = [] # TODO: Add dependency support in .toml config

    def convert_from_meson(self, meson_sl: build.StaticLibrary) -> None:
        self.name = meson_sl.get_basename()
        self.srcs = [s.fname for s in meson_sl.sources]
        self.subdir = meson_sl.subdir

        for include_dir in meson_sl.include_dirs:
            for dir in include_dir.incdirs:
                self.local_include_dirs.append(f'{include_dir.curdir}/{dir}')

        # Removes any duplicates from the list of generated sources
        generated_sources: list[str] = list(set([source.name for source in meson_sl.get_generated_sources()]))

        for source in generated_sources:
            if source.endswith('.h') and source not in self.generated_headers:
                self.generated_headers.append(source)
            elif (source.endswith('.c') or source.endswith('.cpp')) and source not in self.generated_sources:
                self.generated_sources.append(source)
            else: # sources that don't end with any file extension
                self.generated_sources.append(source)

        for target in meson_sl.link_targets:
            if isinstance(target, build.StaticLibrary):
                self.static_libs.append(target.name)
            elif isinstance(target, build.SharedLibrary):
                self.shared_libs(target.name)

        for target in meson_sl.link_whole_targets:
            if isinstance(target, build.StaticLibrary):
                self.static_libs.append(target.name)


    def __str__(self):
        return f'@StaticLibrary({self.name})'

class HermeticSharedLibrary(HermeticStaticLibrary):
    '''
    Exactly same metadata as StaticLibrary besides how it's generated in Soong and Bazel files
    '''
    def __str__(self):
        return f'@SharedLibrary({self.name})'

class HermeticCustomTarget:

    def __init__(self):
        self.name: str = ''
        self.srcs: T.List[str] = []
        self.out: T.List[str] = []  # 'outs' in bazel
        self.tools: T.List[str] = []
        self.export_include_dirs: T.List[str] = []

        self.python_script = ''
        self.python_script_target_name = ''

    def convert_from_meson(self, custom_target: build.CustomTarget) -> None:
        self.name = custom_target.name

        for src in custom_target.sources:
            if isinstance(src, (universal.File)):
                self.srcs.append(src.fname)
            else:
                # TODO: handle all other possible types
                raise MesonException(f'Type: {type(src)} not handled, exiting...')
        
        for out in custom_target.outputs:
            self.out.append(out)

        program_args = self.srcs + self.out

        if len(custom_target.command) != 0 and custom_target.command[0].endswith('.py'):
            self.python_script = custom_target.command[0]
        else:
            for arg in program_args:
                if arg.endswith('.py'):
                    self.python_script = arg
                    break
        
        if self.python_script:
            self.python_script_target_name = self.name + '_' + os.path.basename(self.python_script)
            self.tools.append(self.python_script_target_name)

        self.export_include_dirs.append(custom_target.subdir)

    def emit_python_target(self) -> T.Union[HermeticPythonTarget, None]:
        '''
        Not all custom targets have valid python targets.
        Function may return None for those cases.
        '''
        if not self.python_script:
            return None
        
        python_custom_target = HermeticPythonTarget(self)
        return python_custom_target
    
    def __str__(self):
        return f'HermeticCustomTarget({self.name})'

class HermeticPythonTarget(HermeticCustomTarget):

    def __init__(self):
        self.main: str = ''
        self.imports: T.List[str] = []
        self.version: T.Dict[T.Any, T.Any] = {}
        self.libs: T.List[str] = []

    def __init__(self, custom_target: HermeticCustomTarget = None):
        super().__init__()
        if custom_target is None:
            return
        
        self.main = custom_target.python_script
        self.name = custom_target.python_script_target_name
        
        self.srcs = [t for t in custom_target.srcs.copy() if t.endswith('.py')]
        self.imports = [os.path.dirname(t) for t in custom_target.srcs.copy() if t.endswith('.py')]

        self.out = custom_target.out.copy()
        self.export_include_dirs = custom_target.export_include_dirs.copy()

    def __str__(self):
        return f'HermeticPythonTarget({self.name})'