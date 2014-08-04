# -*- coding: utf-8 -*-

import unittest
import os
import os.path
import re
import tempfile
import yaml
import passlib.hash
import string
import StringIO
import copy

from nose.plugins.skip import SkipTest

import ansible.utils
import ansible.errors
import ansible.constants as C
import ansible.utils.template as template2
from ansible.module_utils.splitter import split_args

from ansible import __version__

import sys
reload(sys)
sys.setdefaultencoding("utf8") 

class TestUtils(unittest.TestCase):

    def test_before_comment(self):
        ''' see if we can detect the part of a string before a comment.  Used by INI parser in inventory '''
 
        input    = "before # comment"
        expected = "before "
        actual   = ansible.utils.before_comment(input)
        self.assertEqual(expected, actual)

        input    = "before \# not a comment"
        expected = "before # not a comment"
        actual  =  ansible.utils.before_comment(input)
        self.assertEqual(expected, actual)

        input = ""
        expected = ""
        actual = ansible.utils.before_comment(input)
        self.assertEqual(expected, actual)

        input = "#"
        expected = ""
        actual = ansible.utils.before_comment(input)
        self.assertEqual(expected, actual)

    #####################################
    ### check_conditional tests

    def test_check_conditional_jinja2_literals(self):
        # see http://jinja.pocoo.org/docs/templates/#literals

        # none
        self.assertEqual(ansible.utils.check_conditional(
            None, '/', {}), True)
        self.assertEqual(ansible.utils.check_conditional(
            '', '/', {}), True)

        # list
        self.assertEqual(ansible.utils.check_conditional(
            ['true'], '/', {}), True)
        self.assertEqual(ansible.utils.check_conditional(
            ['false'], '/', {}), False)

        # non basestring or list
        self.assertEqual(ansible.utils.check_conditional(
            {}, '/', {}), {})

        # boolean
        self.assertEqual(ansible.utils.check_conditional(
            'true', '/', {}), True)
        self.assertEqual(ansible.utils.check_conditional(
            'false', '/', {}), False)
        self.assertEqual(ansible.utils.check_conditional(
            'True', '/', {}), True)
        self.assertEqual(ansible.utils.check_conditional(
            'False', '/', {}), False)

        # integer
        self.assertEqual(ansible.utils.check_conditional(
            '1', '/', {}), True)
        self.assertEqual(ansible.utils.check_conditional(
            '0', '/', {}), False)

        # string, beware, a string is truthy unless empty
        self.assertEqual(ansible.utils.check_conditional(
            '"yes"', '/', {}), True)
        self.assertEqual(ansible.utils.check_conditional(
            '"no"', '/', {}), True)
        self.assertEqual(ansible.utils.check_conditional(
            '""', '/', {}), False)


    def test_check_conditional_jinja2_variable_literals(self):
        # see http://jinja.pocoo.org/docs/templates/#literals

        # boolean
        self.assertEqual(ansible.utils.check_conditional(
            'var', '/', {'var': 'True'}), True)
        self.assertEqual(ansible.utils.check_conditional(
            'var', '/', {'var': 'true'}), True)
        self.assertEqual(ansible.utils.check_conditional(
            'var', '/', {'var': 'False'}), False)
        self.assertEqual(ansible.utils.check_conditional(
            'var', '/', {'var': 'false'}), False)

        # integer
        self.assertEqual(ansible.utils.check_conditional(
            'var', '/', {'var': '1'}), True)
        self.assertEqual(ansible.utils.check_conditional(
            'var', '/', {'var': 1}), True)
        self.assertEqual(ansible.utils.check_conditional(
            'var', '/', {'var': '0'}), False)
        self.assertEqual(ansible.utils.check_conditional(
            'var', '/', {'var': 0}), False)

        # string, beware, a string is truthy unless empty
        self.assertEqual(ansible.utils.check_conditional(
            'var', '/', {'var': '"yes"'}), True)
        self.assertEqual(ansible.utils.check_conditional(
            'var', '/', {'var': '"no"'}), True)
        self.assertEqual(ansible.utils.check_conditional(
            'var', '/', {'var': '""'}), False)

        # Python boolean in Jinja2 expression
        self.assertEqual(ansible.utils.check_conditional(
            'var', '/', {'var': True}), True)
        self.assertEqual(ansible.utils.check_conditional(
            'var', '/', {'var': False}), False)


    def test_check_conditional_jinja2_expression(self):
        self.assertEqual(ansible.utils.check_conditional(
            '1 == 1', '/', {}), True)
        self.assertEqual(ansible.utils.check_conditional(
            'bar == 42', '/', {'bar': 42}), True)
        self.assertEqual(ansible.utils.check_conditional(
            'bar != 42', '/', {'bar': 42}), False)


    def test_check_conditional_jinja2_expression_in_variable(self):
        self.assertEqual(ansible.utils.check_conditional(
            'var', '/', {'var': '1 == 1'}), True)
        self.assertEqual(ansible.utils.check_conditional(
            'var', '/', {'var': 'bar == 42', 'bar': 42}), True)
        self.assertEqual(ansible.utils.check_conditional(
            'var', '/', {'var': 'bar != 42', 'bar': 42}), False)

    def test_check_conditional_jinja2_unicode(self):
        self.assertEqual(ansible.utils.check_conditional(
            u'"\u00df"', '/', {}), True)
        self.assertEqual(ansible.utils.check_conditional(
            u'var == "\u00df"', '/', {'var': u'\u00df'}), True)


    #####################################
    ### key-value parsing

    def test_parse_kv_basic(self):
        self.assertEqual(ansible.utils.parse_kv('a=simple b="with space" c="this=that"'),
                {'a': 'simple', 'b': 'with space', 'c': 'this=that'})
        self.assertEqual(ansible.utils.parse_kv('msg=АБВГД'),
                {'msg': 'АБВГД'})


    def test_jsonify(self):
        self.assertEqual(ansible.utils.jsonify(None), '{}')
        self.assertEqual(ansible.utils.jsonify(dict(foo='bar', baz=['qux'])),
               '{"baz": ["qux"], "foo": "bar"}')
        expected = '''{
    "baz": [
        "qux"
    ], 
    "foo": "bar"
}'''
        self.assertEqual(ansible.utils.jsonify(dict(foo='bar', baz=['qux']), format=True), expected)

    def test_is_failed(self):
        self.assertEqual(ansible.utils.is_failed(dict(rc=0)), False)
        self.assertEqual(ansible.utils.is_failed(dict(rc=1)), True)
        self.assertEqual(ansible.utils.is_failed(dict()), False)
        self.assertEqual(ansible.utils.is_failed(dict(failed=False)), False)
        self.assertEqual(ansible.utils.is_failed(dict(failed=True)), True)
        self.assertEqual(ansible.utils.is_failed(dict(failed='True')), True)
        self.assertEqual(ansible.utils.is_failed(dict(failed='true')), True)

    def test_is_changed(self):
        self.assertEqual(ansible.utils.is_changed(dict()), False)
        self.assertEqual(ansible.utils.is_changed(dict(changed=False)), False)
        self.assertEqual(ansible.utils.is_changed(dict(changed=True)), True)
        self.assertEqual(ansible.utils.is_changed(dict(changed='True')), True)
        self.assertEqual(ansible.utils.is_changed(dict(changed='true')), True)

    def test_path_dwim(self):
        self.assertEqual(ansible.utils.path_dwim(None, __file__),
               __file__)
        self.assertEqual(ansible.utils.path_dwim(None, '~'),
               os.path.expanduser('~'))
        self.assertEqual(ansible.utils.path_dwim(None, 'TestUtils.py'),
               __file__.rstrip('c'))

    def test_path_dwim_relative(self):
        self.assertEqual(ansible.utils.path_dwim_relative(__file__, 'units', 'TestUtils.py',
                                                          os.path.dirname(os.path.dirname(__file__))),
               __file__.rstrip('c'))

    def test_json_loads(self):
        self.assertEqual(ansible.utils.json_loads('{"foo": "bar"}'), dict(foo='bar'))

    def test_parse_json(self):
        # leading junk
        self.assertEqual(ansible.utils.parse_json('ansible\n{"foo": "bar"}'), dict(foo="bar"))

        # "baby" json
        self.assertEqual(ansible.utils.parse_json('foo=bar baz=qux'), dict(foo='bar', baz='qux'))

        # No closing quotation
        try:
            ansible.utils.parse_json('foo=bar "')
        except ValueError:
            pass
        else:
            raise AssertionError('Incorrect exception, expected ValueError')

        # Failed to parse
        try:
            ansible.utils.parse_json('{')
        except ansible.errors.AnsibleError:
            pass
        else:
            raise AssertionError('Incorrect exception, expected ansible.errors.AnsibleError')

        # boolean changed/failed
        self.assertEqual(ansible.utils.parse_json('changed=true'), dict(changed=True))
        self.assertEqual(ansible.utils.parse_json('changed=false'), dict(changed=False))
        self.assertEqual(ansible.utils.parse_json('failed=true'), dict(failed=True))
        self.assertEqual(ansible.utils.parse_json('failed=false'), dict(failed=False))

        # rc
        self.assertEqual(ansible.utils.parse_json('rc=0'), dict(rc=0))

        # Just a string
        self.assertEqual(ansible.utils.parse_json('foo'), dict(failed=True, parsed=False, msg='foo'))

    def test_parse_yaml(self):
        #json
        self.assertEqual(ansible.utils.parse_yaml('{"foo": "bar"}'), dict(foo='bar'))

        # broken json
        try:
            ansible.utils.parse_yaml('{')
        except ansible.errors.AnsibleError:
            pass
        else:
            raise AssertionError

        # broken json with path_hint
        try:
            ansible.utils.parse_yaml('{', path_hint='foo')
        except ansible.errors.AnsibleError:
            pass
        else:
            raise AssertionError

        # yaml with front-matter
        self.assertEqual(ansible.utils.parse_yaml("---\nfoo: bar"), dict(foo='bar'))
        # yaml no front-matter
        self.assertEqual(ansible.utils.parse_yaml('foo: bar'), dict(foo='bar'))
        # yaml indented first line (See #6348)
        self.assertEqual(ansible.utils.parse_yaml(' - foo: bar\n   baz: qux'), [dict(foo='bar', baz='qux')])

    def test_process_common_errors(self):
        # no quote
        self.assertTrue('YAML thought it' in ansible.utils.process_common_errors('', 'foo: {{bar}}', 6))

        # extra colon
        self.assertTrue('an extra unquoted colon' in ansible.utils.process_common_errors('', 'foo: bar:', 8))

        # match
        self.assertTrue('same kind of quote' in ansible.utils.process_common_errors('', 'foo: "{{bar}}"baz', 6))
        self.assertTrue('same kind of quote' in ansible.utils.process_common_errors('', "foo: '{{bar}}'baz", 6))

        # unbalanced
        self.assertTrue('We could be wrong' in ansible.utils.process_common_errors('', 'foo: "bad" "wolf"', 6))
        self.assertTrue('We could be wrong' in ansible.utils.process_common_errors('', "foo: 'bad' 'wolf'", 6))


    def test_process_yaml_error(self):
        data = 'foo: bar\n baz: qux'
        try:
            ansible.utils.parse_yaml(data)
        except yaml.YAMLError, exc:
            try:
                ansible.utils.process_yaml_error(exc, data, __file__)
            except ansible.errors.AnsibleYAMLValidationFailed, e:
                self.assertTrue('Syntax Error while loading' in e.msg)
            else:
                raise AssertionError('Incorrect exception, expected AnsibleYAMLValidationFailed')

        data = 'foo: bar\n baz: {{qux}}'
        try:
            ansible.utils.parse_yaml(data)
        except yaml.YAMLError, exc:
            try:
                ansible.utils.process_yaml_error(exc, data, __file__)
            except ansible.errors.AnsibleYAMLValidationFailed, e:
                self.assertTrue('Syntax Error while loading' in e.msg)
            else:
                raise AssertionError('Incorrect exception, expected AnsibleYAMLValidationFailed')

        data = '\xFF'
        try:
            ansible.utils.parse_yaml(data)
        except yaml.YAMLError, exc:
            try:
                ansible.utils.process_yaml_error(exc, data, __file__)
            except ansible.errors.AnsibleYAMLValidationFailed, e:
                self.assertTrue('Check over' in e.msg)
            else:
                raise AssertionError('Incorrect exception, expected AnsibleYAMLValidationFailed')

        data = '\xFF'
        try:
            ansible.utils.parse_yaml(data)
        except yaml.YAMLError, exc:
            try:
                ansible.utils.process_yaml_error(exc, data, None)
            except ansible.errors.AnsibleYAMLValidationFailed, e:
                self.assertTrue('Could not parse YAML.' in e.msg)
            else:
                raise AssertionError('Incorrect exception, expected AnsibleYAMLValidationFailed')

    def test_parse_yaml_from_file(self):
        test = os.path.join(os.path.dirname(__file__), 'inventory_test_data',
                            'common_vars.yml')
        encrypted = os.path.join(os.path.dirname(__file__), 'inventory_test_data',
                                 'encrypted.yml')
        broken = os.path.join(os.path.dirname(__file__), 'inventory_test_data',
                              'broken.yml')

        try:
            ansible.utils.parse_yaml_from_file(os.path.dirname(__file__))
        except ansible.errors.AnsibleError:
            pass
        else:
            raise AssertionError('Incorrect exception, expected AnsibleError')

        self.assertEqual(ansible.utils.parse_yaml_from_file(test), yaml.safe_load(open(test)))

        self.assertEqual(ansible.utils.parse_yaml_from_file(encrypted, 'ansible'), dict(foo='bar'))

        try:
            ansible.utils.parse_yaml_from_file(broken)
        except ansible.errors.AnsibleYAMLValidationFailed, e:
            self.assertTrue('Syntax Error while loading' in e.msg)
        else:
            raise AssertionError('Incorrect exception, expected AnsibleYAMLValidationFailed')

    def test_merge_hash(self):
        self.assertEqual(ansible.utils.merge_hash(dict(foo='bar', baz='qux'), dict(foo='baz')),
               dict(foo='baz', baz='qux'))
        self.assertEqual(ansible.utils.merge_hash(dict(foo=dict(bar='baz')), dict(foo=dict(bar='qux'))),
               dict(foo=dict(bar='qux')))

    def test_md5s(self):
        self.assertEqual(ansible.utils.md5s('ansible'), '640c8a5376aa12fa15cf02130ce239a6')
        # Need a test that causes UnicodeEncodeError See 4221

    def test_md5(self):
        self.assertEqual(ansible.utils.md5(os.path.join(os.path.dirname(__file__), 'ansible.cfg')),
                         'fb7b5b90ea63f04bde33e804b6fad42c')
        self.assertEqual(ansible.utils.md5(os.path.join(os.path.dirname(__file__), 'ansible.cf')),
                         None)

    def test_default(self):
        self.assertEqual(ansible.utils.default(None, lambda: {}), {})
        self.assertEqual(ansible.utils.default(dict(foo='bar'), lambda: {}), dict(foo='bar'))

    def test__gitinfo(self):
        # this fails if not run from git clone
        # self.assertEqual('last updated' in ansible.utils._gitinfo())
        # missing test for git submodule
        # missing test outside of git clone
        pass

    def test_version(self):
        version = ansible.utils.version('ansible')
        self.assertTrue(version.startswith('ansible %s' % __version__))
        # this fails if not run from git clone
        # self.assertEqual('last updated' in version)

    def test_getch(self):
        # figure out how to test this
        pass

    def test_sanitize_output(self):
        self.assertEqual(ansible.utils.sanitize_output('password=foo'), 'password=VALUE_HIDDEN')
        self.assertEqual(ansible.utils.sanitize_output('foo=user:pass@foo/whatever'),
                         'foo=user:********@foo/whatever')
        self.assertEqual(ansible.utils.sanitize_output('foo=http://username:pass@wherever/foo'),
                         'foo=http://username:********@wherever/foo')
        self.assertEqual(ansible.utils.sanitize_output('foo=http://wherever/foo'),
                         'foo=http://wherever/foo')

    def test_increment_debug(self):
        ansible.utils.VERBOSITY = 0
        ansible.utils.increment_debug(None, None, None, None)
        self.assertEqual(ansible.utils.VERBOSITY, 1)

    def test_base_parser(self):
        output = ansible.utils.base_parser(output_opts=True)
        self.assertTrue(output.has_option('--one-line') and output.has_option('--tree'))

        runas = ansible.utils.base_parser(runas_opts=True)
        for opt in ['--sudo', '--sudo-user', '--user', '--su', '--su-user']:
            self.assertTrue(runas.has_option(opt))

        async = ansible.utils.base_parser(async_opts=True)
        self.assertTrue(async.has_option('--poll') and async.has_option('--background'))

        connect = ansible.utils.base_parser(connect_opts=True)
        self.assertTrue(connect.has_option('--connection'))

        subset = ansible.utils.base_parser(subset_opts=True)
        self.assertTrue(subset.has_option('--limit'))

        check = ansible.utils.base_parser(check_opts=True)
        self.assertTrue(check.has_option('--check'))

        diff = ansible.utils.base_parser(diff_opts=True)
        self.assertTrue(diff.has_option('--diff'))

    def test_do_encrypt(self):
        salt_chars = string.ascii_letters + string.digits + './'
        salt = ansible.utils.random_password(length=8, chars=salt_chars)
        hash = ansible.utils.do_encrypt('ansible', 'sha256_crypt', salt=salt)
        self.assertTrue(passlib.hash.sha256_crypt.verify('ansible', hash))

        hash = ansible.utils.do_encrypt('ansible', 'sha256_crypt')
        self.assertTrue(passlib.hash.sha256_crypt.verify('ansible', hash))

        hash = ansible.utils.do_encrypt('ansible', 'md5_crypt', salt_size=4)
        self.assertTrue(passlib.hash.md5_crypt.verify('ansible', hash))


        try:
            ansible.utils.do_encrypt('ansible', 'ansible')
        except ansible.errors.AnsibleError:
            pass
        else:
            raise AssertionError('Incorrect exception, expected AnsibleError')

    def test_last_non_blank_line(self):
        self.assertEqual(ansible.utils.last_non_blank_line('a\n\nb\n\nc'), 'c')
        self.assertEqual(ansible.utils.last_non_blank_line(''), '')

    def test_filter_leading_non_json_lines(self):
        self.assertEqual(ansible.utils.filter_leading_non_json_lines('a\nb\nansible!\n{"foo": "bar"}'),
                         '{"foo": "bar"}\n')
        self.assertEqual(ansible.utils.filter_leading_non_json_lines('a\nb\nansible!\n["foo", "bar"]'),
                         '["foo", "bar"]\n')
        self.assertEqual(ansible.utils.filter_leading_non_json_lines('a\nb\nansible!\nfoo=bar'),
                         'foo=bar\n')

    def test_boolean(self):
        self.assertEqual(ansible.utils.boolean("true"), True)
        self.assertEqual(ansible.utils.boolean("True"), True)
        self.assertEqual(ansible.utils.boolean("TRUE"), True)
        self.assertEqual(ansible.utils.boolean("t"), True)
        self.assertEqual(ansible.utils.boolean("T"), True)
        self.assertEqual(ansible.utils.boolean("Y"), True)
        self.assertEqual(ansible.utils.boolean("y"), True)
        self.assertEqual(ansible.utils.boolean("1"), True)
        self.assertEqual(ansible.utils.boolean(1), True)
        self.assertEqual(ansible.utils.boolean("false"), False)
        self.assertEqual(ansible.utils.boolean("False"), False)
        self.assertEqual(ansible.utils.boolean("0"), False)
        self.assertEqual(ansible.utils.boolean(0), False)
        self.assertEqual(ansible.utils.boolean("foo"), False)

    #def test_make_sudo_cmd(self):
    #    cmd = ansible.utils.make_sudo_cmd('root', '/bin/sh', '/bin/ls')
    #    self.assertTrue(isinstance(cmd, tuple))
    #    self.assertEqual(len(cmd), 3)
    #    self.assertTrue('-u root' in cmd[0])
    #    self.assertTrue('-p "[sudo via ansible, key=' in cmd[0] and cmd[1].startswith('[sudo via ansible, key'))
    #    self.assertTrue('echo SUDO-SUCCESS-' in cmd[0] and cmd[2].startswith('SUDO-SUCCESS-'))
    #    self.assertTrue('sudo -k' in cmd[0])

    def test_make_su_cmd(self):
        cmd = ansible.utils.make_su_cmd('root', '/bin/sh', '/bin/ls')
        self.assertTrue(isinstance(cmd, tuple))
        self.assertEqual(len(cmd), 3)
        self.assertTrue('root -c "/bin/sh' in cmd[0] or ' root -c /bin/sh' in cmd[0])
        self.assertTrue(re.compile(cmd[1]))
        self.assertTrue('echo SUDO-SUCCESS-' in cmd[0] and cmd[2].startswith('SUDO-SUCCESS-'))

    def test_to_unicode(self):
        uni = ansible.utils.to_unicode(u'ansible')
        self.assertTrue(isinstance(uni, unicode))
        self.assertEqual(uni, u'ansible')

        none = ansible.utils.to_unicode(None)
        self.assertTrue(isinstance(none, type(None)))
        self.assertTrue(none is None)

        utf8 = ansible.utils.to_unicode('ansible')
        self.assertTrue(isinstance(utf8, unicode))
        self.assertEqual(utf8, u'ansible')

    def test_is_list_of_strings(self):
        self.assertEqual(ansible.utils.is_list_of_strings(['foo', 'bar', u'baz']), True)
        self.assertEqual(ansible.utils.is_list_of_strings(['foo', 'bar', True]), False)
        self.assertEqual(ansible.utils.is_list_of_strings(['one', 2, 'three']), False)

    def test_safe_eval(self):
        # Not basestring
        self.assertEqual(ansible.utils.safe_eval(len), len)
        self.assertEqual(ansible.utils.safe_eval(1), 1)
        self.assertEqual(ansible.utils.safe_eval(len, include_exceptions=True), (len, None))
        self.assertEqual(ansible.utils.safe_eval(1, include_exceptions=True), (1, None))

        # module
        self.assertEqual(ansible.utils.safe_eval('foo.bar('), 'foo.bar(')
        self.assertEqual(ansible.utils.safe_eval('foo.bar(', include_exceptions=True), ('foo.bar(', None))

        # import
        self.assertEqual(ansible.utils.safe_eval('import foo'), 'import foo')
        self.assertEqual(ansible.utils.safe_eval('import foo', include_exceptions=True), ('import foo', None))

        # valid simple eval
        self.assertEqual(ansible.utils.safe_eval('True'), True)
        self.assertEqual(ansible.utils.safe_eval('True', include_exceptions=True), (True, None))

        # valid eval with lookup
        self.assertEqual(ansible.utils.safe_eval('foo + bar', dict(foo=1, bar=2)), 3)
        self.assertEqual(ansible.utils.safe_eval('foo + bar', dict(foo=1, bar=2), include_exceptions=True), (3, None))

        # invalid eval
        self.assertEqual(ansible.utils.safe_eval('foo'), 'foo')
        nameerror = ansible.utils.safe_eval('foo', include_exceptions=True)
        self.assertTrue(isinstance(nameerror, tuple))
        self.assertEqual(nameerror[0], 'foo')
        self.assertTrue(isinstance(nameerror[1], NameError))

    def test_listify_lookup_plugin_terms(self):
        basedir = os.path.dirname(__file__)
        self.assertEqual(ansible.utils.listify_lookup_plugin_terms('things', basedir, dict()),
                         ['things'])
        self.assertEqual(ansible.utils.listify_lookup_plugin_terms('things', basedir, dict(things=['one', 'two'])),
                         ['one', 'two'])

    def test_deprecated(self):
        sys_stderr = sys.stderr
        sys.stderr = StringIO.StringIO()
        ansible.utils.deprecated('Ack!', '0.0')
        out = sys.stderr.getvalue()
        self.assertTrue('0.0' in out)
        self.assertTrue('[DEPRECATION WARNING]' in out)

        sys.stderr = StringIO.StringIO()
        ansible.utils.deprecated('Ack!', None)
        out = sys.stderr.getvalue()
        self.assertTrue('0.0' not in out)
        self.assertTrue('[DEPRECATION WARNING]' in out)

        sys.stderr = StringIO.StringIO()
        warnings = C.DEPRECATION_WARNINGS
        C.DEPRECATION_WARNINGS = False
        ansible.utils.deprecated('Ack!', None)
        out = sys.stderr.getvalue()
        self.assertTrue(not out)
        C.DEPRECATION_WARNINGS = warnings

        sys.stderr = sys_stderr

        try:
            ansible.utils.deprecated('Ack!', '0.0', True)
        except ansible.errors.AnsibleError, e:
            self.assertTrue('0.0' not in e.msg)
            self.assertTrue('[DEPRECATED]' in e.msg)
        else:
            raise AssertionError("Incorrect exception, expected AnsibleError")

    def test_warning(self):
        sys_stderr = sys.stderr
        sys.stderr = StringIO.StringIO()
        ansible.utils.warning('ANSIBLE')
        out = sys.stderr.getvalue()
        sys.stderr = sys_stderr
        self.assertTrue('[WARNING]: ANSIBLE' in out)

    def test_combine_vars(self):
        one = {'foo': {'bar': True}, 'baz': {'one': 'qux'}}
        two = {'baz': {'two': 'qux'}}
        replace = {'baz': {'two': 'qux'}, 'foo': {'bar': True}}
        merge = {'baz': {'two': 'qux', 'one': 'qux'}, 'foo': {'bar': True}}

        C.DEFAULT_HASH_BEHAVIOUR = 'replace'
        self.assertEqual(ansible.utils.combine_vars(one, two), replace)

        C.DEFAULT_HASH_BEHAVIOUR = 'merge'
        self.assertEqual(ansible.utils.combine_vars(one, two), merge)

    def test_err(self):
        sys_stderr = sys.stderr
        sys.stderr = StringIO.StringIO()
        ansible.utils.err('ANSIBLE')
        out = sys.stderr.getvalue()
        sys.stderr = sys_stderr
        self.assertEqual(out, 'ANSIBLE\n')

    def test_exit(self):
        sys_stderr = sys.stderr
        sys.stderr = StringIO.StringIO()
        try:
            ansible.utils.exit('ansible')
        except SystemExit, e:
            self.assertEqual(e.code, 1)
            self.assertEqual(sys.stderr.getvalue(), 'ansible\n')
        else:
            raise AssertionError('Incorrect exception, expected SystemExit')
        finally:
            sys.stderr = sys_stderr

    def test_unfrackpath(self):
        os.environ['TEST_ROOT'] = os.path.dirname(os.path.dirname(__file__))
        self.assertEqual(ansible.utils.unfrackpath('$TEST_ROOT/units/../units/TestUtils.py'), __file__.rstrip('c'))

    def test_is_executable(self):
        self.assertEqual(ansible.utils.is_executable(__file__), 0)

        bin_ansible = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                   'bin', 'ansible')
        self.assertNotEqual(ansible.utils.is_executable(bin_ansible), 0)

    def test_get_diff(self):
        standard = dict(
            before_header='foo',
            after_header='bar',
            before='fooo',
            after='foo'
        )

        standard_expected = """--- before: foo
+++ after: bar
@@ -1 +1 @@
-fooo+foo"""

        # workaround py26 and py27 difflib differences        
        standard_expected = """-fooo+foo"""
        diff = ansible.utils.get_diff(standard)
        diff = diff.split('\n')
        del diff[0]
        del diff[0]
        del diff[0]
        diff = '\n'.join(diff)
        self.assertEqual(diff, unicode(standard_expected))

    def test_split_args(self):
        # split_args is a smarter shlex.split for the needs of the way ansible uses it

        def _split_info(input, desired, actual):
            print "SENT: ", input
            print "WANT: ", desired 
            print "GOT: ", actual

        def _test_combo(input, desired):
            actual = split_args(input)
            _split_info(input, desired, actual)
            assert actual == desired

        # trivial splitting
        _test_combo('a b=c d=f',                   ['a', 'b=c', 'd=f' ])

        # mixed quotes
        _test_combo('a b=\'c\' d="e" f=\'g\'',     ['a', "b='c'", 'd="e"', "f='g'" ])

        # with spaces
        # FIXME: this fails, commenting out only for now
        # _test_combo('a "\'one two three\'"',     ['a', "'one two three'" ])

        # TODO: ...
        # jinja2 preservation
        _test_combo('a {{ y }} z',                   ['a', '{{ y }}', 'z' ])

        # jinja2 preservation with spaces and filters and other hard things
        _test_combo(
            'a {{ x | filter(\'moo\', \'param\') }} z {{ chicken }} "waffles"', 
            ['a', "{{ x | filter('moo', 'param') }}", 'z', '{{ chicken }}', '"waffles"']
        )

        # invalid quote detection
        with self.assertRaises(Exception):
            split_args('hey I started a quote"')
        with self.assertRaises(Exception):
            split_args('hey I started a\' quote')

        # jinja2 loop blocks with lots of complexity
        _test_combo(
            # in memory of neighbors cat
            # we only preserve newlines inside of quotes
            'a {% if x %} y {%else %} {{meow}} {% endif %} "cookie\nchip"\ndone',
            ['a', '{% if x %}', 'y', '{%else %}', '{{meow}}', '{% endif %}', '"cookie\nchip"', 'done']
        )

        # test space preservation within quotes
        _test_combo(
            'content="1 2  3   4    "  foo=bar',
            ['content="1 2  3   4    "', 'foo=bar']
        )

        # invalid jinja2 nesting detection
        # invalid quote nesting detection
    
    def test_clean_data(self):
        # clean data removes jinja2 tags from data
        self.assertEqual(
            ansible.utils._clean_data('this is a normal string', from_remote=True),
            'this is a normal string'
        )
        self.assertEqual(
            ansible.utils._clean_data('this string has a {{variable}}', from_remote=True),
            'this string has a {#variable#}'
        )
        self.assertEqual(
            ansible.utils._clean_data('this string has a {{variable with a\nnewline}}', from_remote=True),
            'this string has a {#variable with a\nnewline#}'
        )
        self.assertEqual(
            ansible.utils._clean_data('this string is from inventory {{variable}}', from_inventory=True),
            'this string is from inventory {{variable}}'
        )
        self.assertEqual(
            ansible.utils._clean_data('this string is from inventory too but uses lookup {{lookup("foo","bar")}}', from_inventory=True),
            'this string is from inventory too but uses lookup {#lookup("foo","bar")#}'
        )
        self.assertEqual(
            ansible.utils._clean_data('this string has JSON in it: {"foo":{"bar":{"baz":"oops"}}}', from_remote=True),
            'this string has JSON in it: {"foo":{"bar":{"baz":"oops"}}}'
        )
        self.assertEqual(
            ansible.utils._clean_data('this string contains unicode: ¢ £ ¤ ¥', from_remote=True),
            'this string contains unicode: ¢ £ ¤ ¥'
        )


