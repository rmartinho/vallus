#!/usr/bin/python
# Vallus
#
# Written in 2015 by Martinho Fernandes <rmf@rmf.io>
#
# To the extent possible under law, the author(s) have dedicated all copyright and related
# and neighboring rights to this software to the public domain worldwide. This software is
# distributed without any warranty.
#
# You should have received a copy of the CC0 Public Domain Dedication along with this software.
# If not, see <http://creativecommons.org/publicdomain/zero/1.0/>.
#
# Heavily opinionated build tools for my hobby projects

from os import path
import os
import fnmatch
import re
import sys
import argparse

from . import ninja_syntax
from .toolchain import gnu
from .toolchain import llvm
from .toolchain import ms

# util functions
def get_files(root, pattern):
    pattern = fnmatch.translate(pattern)
    for dir, dirs, files in os.walk(root):
        for f in files:
            if re.match(pattern, f):
                yield path.join(dir, f)

def object_file(src):
    return path.join('obj', re.sub(r'\.c\+\+$', '.o', src))

def _build_objects(ninja, root):
    src_files = list(get_files(root, '*.c++'))
    obj_files = [object_file(fn) for fn in src_files]
    for fn in src_files:
        ninja.build(object_file(fn), 'cxx',
                    inputs = fn)
    return obj_files

def _target_alias(ninja, alias, output):
    ninja.build(alias, 'phony',
                inputs = output)

class Vallus:
    def __init__(self):
        self._includes = []
        self._depends = []
        self._defines = []
        self._libraries = []
        self._targets = []

    # setup
    def include(self, inc):
        self._includes.append(inc)
    def includes(self, *incs):
        self._includes.extend(incs)
    def depend_include(self, inc):
        self._depends.append(inc)
    def depend_includes(self, *incs):
        self._depends.extend(incs)

    def define(self, name, value=None):
        self._defines.append((name, value) if value else name)
    def defines(self, *defs):
        self._defines.extend(defs)

    def library(self, lib):
        self._libraries.append(lib)
    def libraries(self, *libs):
        self._libraries.extend(libs)

    def bootstrap(self, default='docs', custom=None):
        # arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('--debug', action='store_true', help='compile with debug information')
        parser.add_argument('--cxx', default=None, metavar='executable', help='compiler name to use (default depends on toolchain)')

        tool_arg = parser.add_mutually_exclusive_group()
        tool_arg.add_argument('--gnu', action='store_true', help='use a GNU toolchain (default)')
        tool_arg.add_argument('--llvm', action='store_true', help='use an LLVM toolchain')
        tool_arg.add_argument('--ms', action='store_true', help='use a Microsoft toolchain')

        parser.add_argument('--boost-dir', default=None, metavar='path', help='path of boost folder (i.e. the folder with include/ and lib/ subfolders)')
        parser.add_argument('--no-lto', action='store_true', help='do not perform link-time optimisation')
        args = parser.parse_args()

        tools = toolchain.ms.Toolchain() if args.ms else toolchain.llvm.Toolchain() if args.llvm else toolchain.gnu.Toolchain()
        compiler = args.cxx if args.cxx else tools.compiler()
        linker = args.cxx if args.cxx else tools.linker()
        archiver = tools.archiver()

        # preamble
        ninja = ninja_syntax.Writer(open('build.ninja', 'w'))
        ninja.variable('ninja_required_version', '1.3')
        ninja.variable('builddir', 'obj' + os.sep)
        ninja.variable('msvc_deps_prefix', 'Note: including file:')

        # rules
        ninja.rule('bootstrap',
                command = ' '.join(['python'] + sys.argv),
                generator = True,
                description = 'BOOTSTRAP')
        all_includes = self._includes + [path.join('deps', i, 'include') for i in self._depends]
        if(args.boost_dir):
            all_includes.append(args.boost_dir)
        ninja.rule('cxx',
                command = tools.compiler_command(
                        command = compiler,
                        dep_output = '$out.d',
                        debug = args.debug,
                        lto = not args.no_lto,
                        warnings = tools.max_warnings(),
                        includes = all_includes,
                        defines = self._defines,
                        extraflags = '$extraflags',
                        input = '$in',
                        output = '$out'
                    ),
                deps = tools.ninja_deps_style(),
                depfile = '$out.d',
                description = 'C++ $in')
        ninja.rule('link',
                command = tools.linker_command(
                        command = linker,
                        debug = args.debug,
                        lto = not args.no_lto,
                        libraries = self._libraries,
                        libpaths = ['bin'],
                        extraflags = '$extraflags',
                        input = '$in',
                        output = '$out'
                    ),
                description = 'LINK $out')
        ninja.rule('lib',
                command = tools.archiver_command(
                        command = archiver,
                        extraflags = '$extraflags',
                        input = '$in',
                        output = '$out'
                    ),
                description = 'AR $in')
        ninja.rule('dylib',
                command = tools.library_command(
                        command = linker,
                        extraflags = '$extraflags',
                        input = '$in',
                        output = '$out'
                    ),
                description = 'LIB $in')

        ninja.rule('site',
                command = ' '.join(['jekyll', 'build', '--quiet', '--source', '$in', '--destination', '$out']),
                description = 'JEKYLL $in')

        # bootstrap build edge
        ninja.build('build.ninja', 'bootstrap',
                implicit = sys.argv[0])

        # user-defined targets
        for target in self._targets:
            target.build(tools, ninja)

        # Custom ninja settings
        if custom:
            custom(tools, ninja)

        # default target
        ninja.default(default)

    class ProgramTarget:
        def __init__(self, target, output, root):
            self.target = target
            self.root = root
            self.output = output

        def build(self, tools, ninja):
            objects = _build_objects(ninja, self.root)
            binary = path.join('bin', tools.program_name(self.output))
            ninja.build(binary, 'link',
                        inputs = objects) # TODO internal dependencies
            _target_alias(ninja, self.target, binary)

    class StaticLibraryTarget:
        def __init__(self, target, output, root):
            self.target = target
            self.root = root
            self.output = output

        def build(self, tools, ninja):
            objects = _build_objects(ninja, self.root)
            binary = path.join('bin', tools.archive_name(self.output))
            ninja.build(binary, 'lib',
                        inputs = objects)
            _target_alias(ninja, self.target, binary)

    class DynamicLibraryTarget:
        def __init__(self, target, output, root):
            self.target = target
            self.root = root
            self.output = output

        def build(self, tools, ninja):
            objects = _build_objects(ninja, self.root)
            binary = path.join('bin', tools.library_name(self.output))
            ninja.build(binary, 'dylib',
                        inputs = objects)
            _target_alias(ninja, self.target, binary)

    class DocumentationTarget:
        def __init__(self, target, output, root):
            self.target = target
            self.root = root
            self.output = output

        def build(self, tools, ninja):
            site = self.output
            site_files = list(get_files(self.root, '*'))
            ninja.build(site, 'site',
                    inputs = self.root,
                    implicit = site_files)

            ninja.build(self.target, 'phony',
                    inputs = site)

    def program(self, target, output, root='src'):
        self._targets.append(self.ProgramTarget(target, output, root))
    def test_runner(self, target='test', output='test', root='test'):
        self.program(target, output, root)
    def static_library(self, target, output, root='src'):
        self._targets.append(self.StaticLibraryTarget(target, output, root))
    def dynamic_library(self, target, output, root='src'):
        self._targets.append(self.DynamicLibraryTarget(target, output, root))
    def documentation(self, target='docs', output=path.join('dist', 'doc'), root='doc'):
        self._targets.append(self.DocumentationTarget(target, output, root))
