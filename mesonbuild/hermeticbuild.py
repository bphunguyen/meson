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

        # Global flags used amongst all Static/Shared Libraries
        self.conlyflags: T.List[str] = []
        self.cppflags: T.List[str] = []

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
        # In Bazel, these c options are copts
        self.copts: T.List[str] = []
        self.cstd: str = ''
        self.cpp_std: str = ''
        self.conlyflags: T.List[str] = []
        self.cppflags: T.List[str] = []

        self.deps: T.List[str] = []
        self.target_compatible_with: T.List[str] = []

        self.local_include_dirs: T.List[str] = []
        self.static_libs: T.List[str] = []
        self.whole_static_libs: T.List[str] = []
        self.shared_libs: T.List[str] = []
        self.header_libs: T.List[str] = []

    def convert_from_meson(self, meson_sl: build.StaticLibrary):
        self.name = meson_sl.get_basename()
        self.srcs = [s.fname for s in meson_sl.sources]
        self.subdir = meson_sl.subdir

        for include_dir in meson_sl.include_dirs:
            self.local_include_dirs.extend(include_dir.incdirs)

        # Removes any duplicates from the list of generated sources
        generated_sources: list[str] = list(set([source.name for source in meson_sl.get_generated_sources()]))
        
        for source in generated_sources:
            if source.endswith('.h') and source not in self.generated_headers:
                self.generated_headers.append(source)
            elif (source.endswith('.c') or source.endswith('.cpp')) and source not in self.generated_sources:
                self.generated_sources.append(source)
            else: # sources that don't end with any file extension
                self.generated_sources.append(source)

        self.cstd = meson_sl

        # DO NOT SUBMIT: Here for debugging purposes
        if self.name == 'mesa_util':
            pprint.pp(self.srcs)
            pprint.pp(self.local_include_dirs)
            pprint.pp(self.generated_sources)
            pprint.pp(self.generated_headers)
            

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

class PythonBinaryHost:

    def __init__(self):
        self.name: str = ''
        self.srcs: T.List[str] = []
        self.main: str = ''
        self.imports: T.List[str] = []
        self.version: T.Dict[T.Any, T.Any] = {}