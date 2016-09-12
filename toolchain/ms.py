# Ogonek
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
# Microsoft toolchain

import itertools

class Toolchain:
    def compiler(self):
        return 'cl'
    def linker(self):
        return 'link'
    def archiver(self):
        return 'lib'

    def max_warnings(self):
        return ['/W3', '/WX']

    def compiler_command(self,
                         command = 'g++',
                         dep_output = None,
                         debug = False,
                         lto = True,
                         warnings = [],
                         includes = [],
                         defines = [],
                         extraflags = '',
                         input = '',
                         output = ''):
        return ' '.join(itertools.chain(
                    [command],
                    ['/showIncludes'],
                    ['/nologo', '/c', '/TP', '/EHsc'],
                    self.debug_flags() if debug else self.opt_flags(),
                    self.compiler_lto_flags() if lto and not debug else [],
                    warnings,
                    [self.include('include')],
                    (self.dep_include(i) for i in includes),
                    (self.define(*kv) for kv in defines),
                    [extraflags],
                    ['/Fo' + output],
                    [input]
                ))

    def linker_command(self,
                       command = 'g++',
                       libraries = [],
                       libpaths = [],
                       debug = False,
                       lto = True,
                       extraflags = '',
                       input = '',
                       output = ''):
        return ' '.join(itertools.chain(
                    [command],
                    ['/NOLOGO'],
                    (self.libpath(p) for p in libpaths),
                    self.linker_lto_flags() if lto and not debug else [],
                    [extraflags],
                    ['/OUT:' + output],
                    [input],
                    (self.library(l) for l in libraries)
                ))


    def archiver_command(self,
                         command = 'ar',
                         extraflags = '',
                         input = '',
                         output = ''):
        return ' '.join(itertools.chain(
                    [command],
                    ['/NOLOGO'],
                    ['/OUT:' + output],
                    [extraflags],
                    [input]
                ))

    def library_command(self,
                        command = linker,
                        extraflags = '',
                        input = '',
                        output = ''):
        return 'foo'

    def program_name(self, output):
        return output + '.exe'
    def archive_name(self, output):
        return output + '.lib'
    def library_name(self, output):
        return output + '.dll'

    def include(self, i):
        return '/I' + i;
    def dep_include(self, i):
        return '/I' + i;
    def define(self, k, v=None):
        return '/D' + (k + '=' + v if v else k)
    def library(self, l):
        return l;
    def libpath(self, p):
        return '/LIBPATH:' + p;

    def debug_flags(self):
        return ['/MDd', '/ZI', '/Od', '/RTC1']
    def opt_flags(self):
        return ['/MD', '/O2', '/Oy-', '/Oi']
    def compiler_lto_flags(self):
        return ['/GL']
    def linker_lto_flags(self):
        return ['/LTCG']

    def ninja_deps_style(self):
        return 'msvc'
