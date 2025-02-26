# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 The Meson development team

import typing as T
import pprint

from . import backends
from mesonbuild import build

class HermeticState:

    def __init__(self):
        self.shared_libraries: list[SharedLibrary] = []
        self.static_libraries: list[StaticLibrary] = []
        self.genrules: list[Genrule] = []
        self.python_binary_hosts: list[PythonBinaryHost] = []

class StaticLibrary:

    def __init__(self):
        self.name: str = ''
        self.dirs: list[str] = []
        self.visibility: list[str] = []
        self.srcs: list[str] = []
        # In Bazel, these headers are one merged list.
        self.generated_headers: list[str] = []
        self.generated_sources: list[str] = []
        # In Bazel, these c options are copts
        self.copts: list[str] = []
        self.cstd: str = ''
        self.cpp_std: str = ''
        self.conlyflags: list[str] = []
        self.cppflags: list[str] = []

        self.deps: list[str] = []
        self.target_compatible_with: list[str] = []

        self.local_include_dirs: list[str] = []
        self.static_libs: list[str] = []
        self.whole_static_libs: list[str] = []
        self.shared_libs: list[str] = []
        self.header_libs: list[str] = []

    def convert_from_meson(self, meson_sl: build.StaticLibrary):
        self.name = meson_sl.get_basename()
        self.srcs = [s.fname for s in meson_sl.sources]
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

        if self.name == 'mesa_util':
            pprint.pp(self.srcs)
            pprint.pp(self.local_include_dirs)
            pprint.pp(self.generated_sources)
            pprint.pp(self.generated_headers)

    def __str__(self):
        return f'@StaticLibrary({self.name})'

class SharedLibrary(StaticLibrary):
    """
    Exactly same metadata as StaticLibrary besides how it's generated in Soong and Bazel files
    """
    def __str__(self):
        return f'@SharedLibrary({self.name})'

class Genrule:

    def __init__(self):
        self.name: str = ''
        self.srcs: list[str] = []
        self.out: list[str] = []  # 'outs' in bazel
        self.tools: list[str] = []
        self.export_include_dirs: list[str] = []
        self.cmd: str = ''

class PythonBinaryHost:

    def __init__(self):
        self.name: str = ''
        self.srcs: list[str] = []
        self.main: str = ''
        self.imports: list[str] = []
        self.version = {}

class HermeticBackend(backends.Backend):

    name = 'hermetic'

    def __init__(self, build, interpreter):
        super().__init__(build, interpreter)
        self.hermetic_state = HermeticState()

    def generate(self, capture: bool = False, vslite_ctx: T.Optional[T.Dict] = None) -> T.Optional[T.Dict]:
        self._generate_static_libs()
        return self.hermetic_state
    
    def _generate_static_libs(self):
        static_libs = []
        targets = self.build.get_build_targets()
        for target in targets:
            library = targets[target]
            if isinstance(library, build.StaticLibrary):
                static_libs.append(library)

        for lib in static_libs:
            # Convert from a meson StaticLibrary to a hermetic StaticLibrary
            hermetic_sl = StaticLibrary()
            hermetic_sl.convert_from_meson(lib)

            self.hermetic_state.static_libraries.append(hermetic_sl)