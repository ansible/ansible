#!/usr/bin/env python
# coding: utf-8

import unittest
import yaml
from ansible.utils import pybook
import pprint

def check_text(text, supposed_res):
    res = pybook.run_pybook_file(text)
    
    assert res == supposed_res, pprint.pprint(res)

class TestPybook(unittest.TestCase):

    def test_list(self):
        text = """
with mapping:
    pass
"""
        check_text(text, [{}])

    def test_map(self):
        text = """
with sequence("key"):
    pass
"""
        check_text(text, {"key": []})

    def test_append(self):
        text = """
with sequence("key"):
    append(True)
"""
        check_text(text, {"key": [True]})

    def test_populate_yaml(self):
        text = """
populate_yaml('''
---
  - name: create user
    user: name=user shell=/bin/bash
''')
"""
        check_text(text, [{
            "name": "create user",
            "user": "name=user shell=/bin/bash"
        }])
