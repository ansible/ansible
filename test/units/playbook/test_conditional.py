from __future__ import annotations

import unittest

import pytest

from ansible.vars.hostvars import HostVarsVars
from units.mock.loader import DictDataLoader
from unittest.mock import MagicMock

from ansible._internal._templating._engine import TemplateEngine
from ansible.utils.datatag.tags import TrustedAsTemplate
from ansible import errors

from ansible.playbook import conditional

TRUST = TrustedAsTemplate()


class TestConditional(unittest.TestCase):
    def setUp(self):
        self.loader = DictDataLoader({})
        self.cond = conditional.Conditional(loader=self.loader)
        self.templar = TemplateEngine(loader=self.loader, variables={})

    def _eval_con(self, when=None, variables=None):
        when = self._trust(when or [])
        variables = self._trust(variables or {})
        self.cond.when = when
        ret = self.cond.evaluate_conditional(self.templar, variables)
        return ret

    def _trust(self, value):
        if isinstance(value, dict):
            return {self._trust(k): self._trust(v) for k, v in value.items()}

        if isinstance(value, list):
            return [self._trust(item) for item in value]

        if isinstance(value, str):
            return TrustedAsTemplate().tag(value)

        return value

    def test_false(self):
        when = [u"False"]
        ret = self._eval_con(when, {})
        self.assertFalse(ret)

    def test_true(self):
        when = [u"True"]
        ret = self._eval_con(when, {})
        self.assertTrue(ret)

    def test_true_boolean(self):
        self.cond.when = [True]
        m = MagicMock()
        ret = self.cond.evaluate_conditional(m, {})
        self.assertTrue(ret)
        self.assertFalse(m.is_template.called)

    def test_false_boolean(self):
        self.cond.when = [False]
        m = MagicMock()
        ret = self.cond.evaluate_conditional(m, {})
        self.assertFalse(ret)
        self.assertFalse(m.is_template.called)

    def test_undefined(self):
        with pytest.raises(errors.AnsibleUndefinedVariable,
                           match="Error while evaluating conditional: 'some_undefined_thing' is undefined"):
            self._eval_con([u"{{ some_undefined_thing }}"], {})

    def test_defined(self):
        variables = {'some_defined_thing': True}
        when = [u"{{ some_defined_thing }}"]
        ret = self._eval_con(when, variables)
        self.assertTrue(ret)

    def test_dict_defined_values(self):
        variables = {'dict_value': 1,
                     'some_defined_dict': {'key1': 'value1',
                                           'key2': '{{ dict_value }}'}}

        when = [u"some_defined_dict is defined"]
        ret = self._eval_con(when, variables)
        self.assertTrue(ret)

    def test_dict_defined_values_is_defined(self):
        variables = {'dict_value': 1,
                     'some_defined_dict': {'key1': 'value1',
                                           'key2': '{{ dict_value }}'}}

        when = [u"some_defined_dict.key1 is defined"]
        ret = self._eval_con(when, variables)
        self.assertTrue(ret)

    def test_dict_defined_multiple_values_is_defined(self):
        variables = {'dict_value': 1,
                     'some_defined_dict': {'key1': 'value1',
                                           'key2': '{{ dict_value }}'}}

        when = [u"some_defined_dict.key1 is defined",
                u"some_defined_dict.key2 is not undefined"]
        ret = self._eval_con(when, variables)
        self.assertTrue(ret)

    def test_nested_hostvars_undefined_values(self):
        variables = dict(
            hostvars=dict(
                host3=HostVarsVars(dict(key1=TRUST.tag('{{ undefined_dict_value }}')), None, 'host3'),
            ),
            some_dict=dict(some_dict_key1=TRUST.tag('{{ hostvars["host3"] }}')),
        )

        with pytest.raises(errors.AnsibleUndefinedVariable,
                           match="Error while evaluating conditional: 'undefined_dict_value' is undefined"):
            self._eval_con(["some_dict.some_dict_key1 == hostvars.host3"], variables)

    def test_undefined_comparision_in_expression(self) -> None:
        with pytest.raises(errors.AnsibleUndefinedVariable, match='Error while evaluating conditional: \'bogus_var\' is undefined'):
            self._eval_con([TRUST.tag('bogus_var == "foo"')])

    def test_dict_undefined_values_bare(self):
        variables = {'dict_value': 1,
                     'some_defined_dict_with_undefined_values': {'key1': 'value1',
                                                                 'key2': '{{ dict_value }}',
                                                                 'key3': '{{ undefined_dict_value }}'
                                                                 }}

        with pytest.raises(errors.AnsibleUndefinedVariable,
                           match="Error while evaluating conditional: 'undefined_dict_value' is undefined"):
            self._eval_con([u"some_defined_dict_with_undefined_values"], variables)

    def test_is_defined(self):
        variables = {'some_defined_thing': True}
        when = [u"some_defined_thing is defined"]
        ret = self._eval_con(when, variables)
        self.assertTrue(ret)

    def test_is_undefined(self):
        variables = {'some_defined_thing': True}
        when = [u"some_defined_thing is undefined"]
        ret = self._eval_con(when, variables)
        self.assertFalse(ret)

    def test_is_undefined_and_defined(self):
        variables = {'some_defined_thing': True}
        when = [u"some_defined_thing is undefined", u"some_defined_thing is defined"]
        ret = self._eval_con(when, variables)
        self.assertFalse(ret)

    def test_is_undefined_and_defined_reversed(self):
        variables = {'some_defined_thing': True}
        when = [u"some_defined_thing is defined", u"some_defined_thing is undefined"]
        ret = self._eval_con(when, variables)
        self.assertFalse(ret)

    def test_is_not_undefined(self):
        variables = {'some_defined_thing': True}
        when = [u"some_defined_thing is not undefined"]
        ret = self._eval_con(when, variables)
        self.assertTrue(ret)

    def test_is_not_defined(self):
        variables = {'some_defined_thing': True}
        when = [u"some_undefined_thing is not defined"]
        ret = self._eval_con(when, variables)
        self.assertTrue(ret)

    def test_is_hostvars_quotes_is_defined(self):
        variables = {'hostvars': {'some_host': {}},
                     'compare_targets_single': "hostvars['some_host']",
                     'compare_targets_double': 'hostvars["some_host"]',
                     'compare_targets': {'double': '{{ compare_targets_double }}',
                                         'single': "{{ compare_targets_single }}"},
                     }
        when = [u"hostvars['some_host'] is defined",
                u'hostvars["some_host"] is defined',
                u"compare_targets.double is defined",
                u"compare_targets.single is defined"]
        ret = self._eval_con(when, variables)
        self.assertTrue(ret)

    def test_is_hostvars_host_is_defined(self):
        variables = {'hostvars': {'some_host': {}, }}
        when = [u"hostvars['some_host'] is defined"]
        ret = self._eval_con(when, variables)
        self.assertTrue(ret)

    def test_is_hostvars_host_undefined_is_defined(self):
        variables = {'hostvars': {'some_host': {}, }}
        when = [u"hostvars['some_undefined_host'] is defined"]
        ret = self._eval_con(when, variables)
        self.assertFalse(ret)

    def test_is_hostvars_host_undefined_is_undefined(self):
        variables = {'hostvars': {'some_host': {}, }}
        when = [u"hostvars['some_undefined_host'] is undefined"]
        ret = self._eval_con(when, variables)
        self.assertTrue(ret)

    def test_is_hostvars_host_undefined_is_not_defined(self):
        variables = {'hostvars': {'some_host': {}, }}
        when = [u"hostvars['some_undefined_host'] is not defined"]
        ret = self._eval_con(when, variables)
        self.assertTrue(ret)
