# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 The Meson development team
import typing as T
import pprint

from . import build

class HermeticState:

    def __init__(self):
        self.shared_libraries: T.List[HermeticSharedLibrary] = []
        self.static_libraries: T.List[HermeticStaticLibrary] = []
        self.genrules: T.List[Genrule] = []
        self.python_binary_hosts: T.List[PythonBinaryHost] = []

        # Global flags used amongst all Static/Shared Libraries in Soong
        self.conlyflags: T.List[str] = []
        self.cppflags: T.List[str] = []

        # Bazel version of c/cpp flags
        self.copts: T.List[str] = []

        # TODO: Figure out where these project options are defined
        self.cstd: str = ''
        self.cpp_std: str = ''

    def __str__(self):
        return f'HermeticState:\n\tshared_libraries len: {len(self.shared_libraries)}' \
            f'\n\tstatic_libraries len: {len(self.static_libraries)}' \
            f'\n\tgenrules len: {len(self.genrules)}' \
            f'\n\tpython_binary_hosts len: {len(self.python_binary_hosts)}'


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

    def convert_from_meson(self, meson_sl: build.StaticLibrary):
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
    """
    Exactly same metadata as StaticLibrary besides how it's generated in Soong and Bazel files
    """
    def __str__(self):
        return f'@SharedLibrary({self.name})'

class Genrule:

    def __init__(self):
        self.name: str = ''
        self.srcs: T.List[str] = []
        self.out: T.List[str] = []  # 'outs' in bazel
        self.tools: T.List[str] = []
        self.export_include_dirs: T.List[str] = []
        self.cmd: str = ''

    def convert_from_meson(self, custom_target: build.CustomTarget):
        pass

class PythonBinaryHost:

    def __init__(self):
        self.name: str = ''
        self.srcs: T.List[str] = []
        self.main: str = ''
        self.imports: T.List[str] = []
        self.version: T.Dict[T.Any, T.Any] = {}