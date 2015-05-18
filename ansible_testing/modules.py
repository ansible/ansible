#!/usr/bin/env python

from __future__ import print_function

import os
import ast
import argparse

from ansible.utils.module_docs import get_docstring, BLACKLIST_MODULES


class ModuleValidator(object):
    def __init__(self, path):
        self.path = path
        self.basename = os.path.basename(self.path)
        self.name, _ = os.path.splitext(self.basename)

        self.errors = []
        self.warnings = []

        with open(path) as f:
            text = f.read()
        self.length = len(text.splitlines())
        self.ast = ast.parse(text)

    def _just_docs(self):
        for child in self.ast.body:
            if not isinstance(child, ast.Assign):
                return False
        return True

    def _find_module_utils(self):
        linenos = []
        for child in self.ast.body:
            found_module_utils_import = False
            if isinstance(child, ast.ImportFrom):
                if child.module.startswith('ansible.module_utils.'):
                    found_module_utils_import = True
                    linenos.append(child.lineno)

                    if not child.names:
                        self.errors.append('%s: not a "from" import"' %
                                           child.module)

                    found_alias = False
                    for name in child.names:
                        if isinstance(name, ast.alias):
                            found_alias = True
                            if name.asname or name.name != '*':
                                self.errors.append('%s: did not import "*"' %
                                                   child.module)

                if found_module_utils_import and not found_alias:
                    self.errors.append('%s: did not import "*"' % child.module)

        if not linenos:
            self.errors.append('Did not find a module_utils import')

        return linenos

    def _find_main_call(self):
        lineno = False
        if_bodies = []
        for child in self.ast.body:
            if isinstance(child, ast.If):
                try:
                    if child.test.left.id == '__name__':
                        if_bodies.extend(child.body)
                except AttributeError:
                    pass

        bodies = self.ast.body
        bodies.extend(if_bodies)

        for child in bodies:
            if isinstance(child, ast.Expr):
                if isinstance(child.value, ast.Call):
                    if (isinstance(child.value.func, ast.Name) and
                            child.value.func.id == 'main'):
                        lineno = child.lineno
                        if lineno < self.length - 1:
                            self.errors.append('Call to main() not the last '
                                               'line')

        if not lineno:
            self.errors.append('Did not find a call to main')

        return lineno or 0

    def _find_has_import(self):
        for child in self.ast.body:
            found_try_except_import = False
            found_has = False
            if isinstance(child, ast.TryExcept):
                bodies = child.body
                bodies.extend([h.body for h in child.handlers])
                for grandchild in bodies:
                    if isinstance(grandchild, ast.Import):
                        found_try_except_import = True
                    elif isinstance(grandchild, ast.Assign):
                        for target in grandchild.targets:
                            if target.id.lower().startswith('has_'):
                                found_has = True
            if found_try_except_import and not found_has:
                self.warnings.append('Found Try/Except block without HAS_ '
                                     'assginment')

    def validate(self):
        if set([self.basename, self.name]) & set(BLACKLIST_MODULES):
            return

        doc, examples, ret = get_docstring(self.path)
        if not bool(doc):
            self.errors.append('Invalid or no DOCUMENTATION provided')
        if not bool(examples):
            self.errors.append('No EXAMPLES provided')
        if not bool(ret):
            self.warnings.append('No RETURN provided')

        if not self._just_docs():
            module_utils = self._find_module_utils()
            main = self._find_main_call()
            for mu in module_utils:
                if mu < main - 10:
                    self.errors.append('module_utils import not near main()')

            self._find_has_import()

    def report(self, warnings=False):
        if self.errors or (warnings and self.warnings):
            print('=' * 76)
            print(self.basename)
            print('=' * 76)

        for error in self.errors:
            print('ERROR: %s' % error)
        if warnings:
            for warning in self.warnings:
                print('WARNING: %s' % warning)

        if self.errors or (warnings and self.warnings):
            print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('modules', help='Path to modules')
    parser.add_argument('-w', '--warnings', help='Show warnings',
                        action='store_true')
    args = parser.parse_args()

    for root, dirs, files in os.walk(args.modules):
        for filename in files:
            path = os.path.join(root, filename)
            if not path.endswith('.py') or filename == '__init__.py':
                continue
            mv = ModuleValidator(os.path.abspath(path))
            mv.validate()
            mv.report(args.warnings)


if __name__ == '__main__':
    main()
