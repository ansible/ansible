# -*- coding: utf-8 -*-

import os
import ast
import unittest
from ansible import utils


class TestModules(unittest.TestCase):

    def list_all_modules(self):
        paths = utils.plugins.module_finder._get_paths()
        paths = [x for x in paths if os.path.isdir(x)]
        module_list = []
        for path in paths:
            for (dirpath, dirnames, filenames) in os.walk(path):
                for filename in filenames:
                    (path, ext) = os.path.splitext(filename)
                    if ext != ".ps1":
                        module_list.append(os.path.join(dirpath, filename))
        return module_list

    def test_ast_parse(self):
        module_list = self.list_all_modules()
        ERRORS = []
        # attempt to parse each module with ast
        for m in module_list:
            try:
                ast.parse(''.join(open(m)))
            except Exception, e:
                ERRORS.append((m, e))
        assert len(ERRORS) == 0, "get_docstring errors: %s" % ERRORS
