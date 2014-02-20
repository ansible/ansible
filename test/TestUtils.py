# -*- coding: utf-8 -*-

import unittest
import os
import os.path
import tempfile

from nose.plugins.skip import SkipTest

import ansible.utils
import ansible.utils.template as template2

import sys
reload(sys)
sys.setdefaultencoding("utf8") 

class TestUtils(unittest.TestCase):

    #####################################
    ### check_conditional tests

    def test_check_conditional_jinja2_literals(self):
        # see http://jinja.pocoo.org/docs/templates/#literals

        # boolean
        assert(ansible.utils.check_conditional(
            'true', '/', {}) == True)
        assert(ansible.utils.check_conditional(
            'false', '/', {}) == False)
        assert(ansible.utils.check_conditional(
            'True', '/', {}) == True)
        assert(ansible.utils.check_conditional(
            'False', '/', {}) == False)

        # integer
        assert(ansible.utils.check_conditional(
            '1', '/', {}) == True)
        assert(ansible.utils.check_conditional(
            '0', '/', {}) == False)

        # string, beware, a string is truthy unless empty
        assert(ansible.utils.check_conditional(
            '"yes"', '/', {}) == True)
        assert(ansible.utils.check_conditional(
            '"no"', '/', {}) == True)
        assert(ansible.utils.check_conditional(
            '""', '/', {}) == False)


    def test_check_conditional_jinja2_variable_literals(self):
        # see http://jinja.pocoo.org/docs/templates/#literals

        # boolean
        assert(ansible.utils.check_conditional(
            'var', '/', {'var': 'True'}) == True)
        assert(ansible.utils.check_conditional(
            'var', '/', {'var': 'true'}) == True)
        assert(ansible.utils.check_conditional(
            'var', '/', {'var': 'False'}) == False)
        assert(ansible.utils.check_conditional(
            'var', '/', {'var': 'false'}) == False)

        # integer
        assert(ansible.utils.check_conditional(
            'var', '/', {'var': '1'}) == True)
        assert(ansible.utils.check_conditional(
            'var', '/', {'var': 1}) == True)
        assert(ansible.utils.check_conditional(
            'var', '/', {'var': '0'}) == False)
        assert(ansible.utils.check_conditional(
            'var', '/', {'var': 0}) == False)

        # string, beware, a string is truthy unless empty
        assert(ansible.utils.check_conditional(
            'var', '/', {'var': '"yes"'}) == True)
        assert(ansible.utils.check_conditional(
            'var', '/', {'var': '"no"'}) == True)
        assert(ansible.utils.check_conditional(
            'var', '/', {'var': '""'}) == False)

        # Python boolean in Jinja2 expression
        assert(ansible.utils.check_conditional(
            'var', '/', {'var': True}) == True)
        assert(ansible.utils.check_conditional(
            'var', '/', {'var': False}) == False)


    def test_check_conditional_jinja2_expression(self):
        assert(ansible.utils.check_conditional(
            '1 == 1', '/', {}) == True)
        assert(ansible.utils.check_conditional(
            'bar == 42', '/', {'bar': 42}) == True)
        assert(ansible.utils.check_conditional(
            'bar != 42', '/', {'bar': 42}) == False)


    def test_check_conditional_jinja2_expression_in_variable(self):
        assert(ansible.utils.check_conditional(
            'var', '/', {'var': '1 == 1'}) == True)
        assert(ansible.utils.check_conditional(
            'var', '/', {'var': 'bar == 42', 'bar': 42}) == True)
        assert(ansible.utils.check_conditional(
            'var', '/', {'var': 'bar != 42', 'bar': 42}) == False)

    def test_check_conditional_jinja2_unicode(self):
        assert(ansible.utils.check_conditional(
            u'"\u00df"', '/', {}) == True)
        assert(ansible.utils.check_conditional(
            u'var == "\u00df"', '/', {'var': u'\u00df'}) == True)


    #####################################
    ### key-value parsing

    def test_parse_kv_basic(self):
        assert (ansible.utils.parse_kv('a=simple b="with space" c="this=that"') ==
                {'a': 'simple', 'b': 'with space', 'c': 'this=that'})

