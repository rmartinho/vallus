# Ogonek
#
# Written in 2015 by Martinho Fernandes <martinho.fernandes@gmail.com>
#
# To the extent possible under law, the author(s) have dedicated all copyright and related
# and neighboring rights to this software to the public domain worldwide. This software is
# distributed without any warranty.
#
# You should have received a copy of the CC0 Public Domain Dedication along with this software.
# If not, see <http://creativecommons.org/publicdomain/zero/1.0/>.
#
# GNU toolchain

import itertools

class Toolchain:
    def compiler(self):
        return 'g++'
    def linker(self):
        return 'g++'
    def archiver(self):
        return 'ar'

    def max_warnings(self):
        return ['-pedantic', '-Wall', '-Wextra', '-Werror']

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
                    ['-MMD','-MF ' + dep_output],
                    ['-c', '-std=c++11', '-pthread'],
                    self.debug_flags() if debug else self.opt_flags(),
                    self.lto_flags() if lto and not debug else [],
                    warnings,
                    [self.include('include')],
                    (self.dep_include(i) for i in includes),
                    (self.define(*kv) for kv in defines),
                    [extraflags],
                    ['-o', output],
                    [input]
                ))

    def linker_command(self,
                       command = 'g++',
                       libraries = [],
                       debug = False,
                       lto = True,
                       extraflags = '',
                       input = '',
                       output = ''):
        return ' '.join(itertools.chain(
                    [command],
                    ['-std=c++11', '-pthread'],
                    self.lto_flags() if lto and not debug else [],
                    [extraflags],
                    ['-o', output],
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
                    ['rcs'],
                    [extraflags],
                    [output],
                    [input]
                ))

    def library_command(self,
                        command = linker,
                        extraflags = '',
                        input = '',
                        output = ''):
        return 'foo'

    def program_name(self, output):
        return output
    def archive_name(self, output):
        return 'lib' + output + '.a'
    def library_name(self, output):
        return 'lib' + output + '.so'

    def include(self, i):
        return '-I' + i;
    def dep_include(self, i):
        return '-isystem' + i
    def define(self, k, v=None):
        return '-D' + (k + '=' + v if v else k)
    def library(self, l):
        return '-l' + l;

    def debug_flags(self):
        return ['-g', '-Og']
    def opt_flags(self):
        return ['-O3']
    def lto_flags(self):
        return ['-flto']

    def ninja_deps_style(self):
        return 'gcc'
