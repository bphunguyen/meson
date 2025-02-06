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

class SharedLibrary:
    pass

class StaticLibrary:
    pass

class Genrule:
    pass

class PythonBinaryHost:
    pass

class HermeticBackend(backends.Backend):

    name = 'hermetic'

    def generate(self, capture: bool = False, vslite_ctx: T.Optional[T.Dict] = None) -> T.Optional[T.Dict]:
        print('CALLED')
        return {}