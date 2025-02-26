# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 The Meson development team

import typing as T

from . import backends
from mesonbuild import build, hermeticbuild, interpreter


class HermeticBackend(backends.Backend):

    name = 'hermetic'

    def __init__(self, build: build.Build, interpreter: interpreter.Interpreter):
        super().__init__(build, interpreter)
        self.hermetic_state: hermeticbuild.HermeticState = hermeticbuild.HermeticState()

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
            hermetic_sl = hermeticbuild.HermeticStaticLibrary()
            hermetic_sl.convert_from_meson(lib)

            self.hermetic_state.static_libraries.append(hermetic_sl)