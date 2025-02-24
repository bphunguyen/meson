# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 The Meson development team

import typing as T

from . import backends

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

    def generate(self, capture: bool = False, vslite_ctx: T.Optional[T.Dict] = None) -> T.Optional[T.Dict]:
        print('CALLED')
        return {}