# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 The Meson development team

import typing as T
import pprint

from mesonbuild.options import OptionKey

from . import backends
from mesonbuild import build, hermeticbuild, interpreter


class HermeticBackend(backends.Backend):

    name = 'hermetic'

    def __init__(self, build: build.Build, interpreter: interpreter.Interpreter):
        super().__init__(build, interpreter)
        self.hermetic_state: hermeticbuild.HermeticState = hermeticbuild.HermeticState()

    def generate(self, capture: bool = False, vslite_ctx: T.Optional[T.Dict] = None) -> T.Optional[T.Dict]:
        self._generate_c_and_cpp_flags()

        self.hermetic_state.c_std = self.environment.coredata.get_option(OptionKey('c_std'))
        self.hermetic_state.cpp_std = self.environment.coredata.get_option(OptionKey('cpp_std'))

        self._generate_static_and_shared_libs()
        self._generate_custom_targets()

        return self.hermetic_state

    def _generate_c_and_cpp_flags(self):
        for flag in self.build.projects_args.host['']['c']:
            if '"' in flag:
                # Makes flags that use "" work when generated in a hermetic build system
                # End result of a a flag like "-DPACKAGE_VERSION="24.3.0-devel"" -> "-DPACKAGE_VERSION=\"24.3.0-devel\""
                # When generating
                clean_flag = flag.replace('"', r'\"')
                self.hermetic_state.conlyflags.append(clean_flag)
            else:
                self.hermetic_state.conlyflags.append(flag)

        for flag in self.build.projects_args.host['']['cpp']:
            if '"' in flag:
                    clean_flag = flag.replace('"', r'\"')
                    self.hermetic_state.cppflags.append(clean_flag)
            else:
                self.hermetic_state.cppflags.append(flag)


    def _generate_static_and_shared_libs(self):
        static_libs = []
        shared_libs = []
        targets = self.build.get_build_targets()
        for target in targets:
            library = targets[target]
            if isinstance(library, build.StaticLibrary):
                static_libs.append(library)
            elif isinstance(library, build.SharedLibrary):
                shared_libs.append(library)

        for lib in static_libs:
            # Convert from a meson StaticLibrary to a hermetic StaticLibrary
            hermetic_sl = hermeticbuild.HermeticStaticLibrary()
            hermetic_sl.convert_from_meson(lib)

            self.hermetic_state.static_libraries.append(hermetic_sl)
            
        for lib in shared_libs:
            hermetic_sl = hermeticbuild.HermeticSharedLibrary()
            hermetic_sl.convert_from_meson(lib)

            self.hermetic_state.shared_libraries.append(hermetic_sl)

    def _generate_custom_targets(self):
        targets = self.build.get_custom_targets()
        for target in targets:
            custom_target = targets[target]
            hermetic_ct = hermeticbuild.HermeticCustomTarget()
            hermetic_ct.convert_from_meson(custom_target)

            self.hermetic_state.custom_targets.append(hermetic_ct)

            python_target = hermetic_ct.emit_python_target()

            if python_target:
                self.hermetic_state.python_targets.append(python_target)