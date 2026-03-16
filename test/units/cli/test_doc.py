from __future__ import annotations

import pytest

from ansible import constants as C
from ansible.cli.doc import DocCLI, RoleMixin
from ansible.plugins.loader import module_loader, init_plugin_loader


C.ANSIBLE_NOCOLOR = True
TTY_IFY_DATA = {
    # No substitutions
    'no-op': 'no-op',
    'no-op Z(test)': 'no-op Z(test)',
    # Simple cases of all substitutions
    'I(italic)': "`italic`",
    'B(bold)': '*bold*',
    'M(ansible.builtin.module)': '[ansible.builtin.module]',
    'U(https://docs.ansible.com)': 'https://docs.ansible.com',
    'L(the user guide,https://docs.ansible.com/user-guide.html)': 'the user guide <https://docs.ansible.com/user-guide.html>',
    'R(the user guide,user-guide)': 'the user guide',
    'C(/usr/bin/file)': "`/usr/bin/file'",
    'HORIZONTALLINE': '\n{0}\n'.format('-' * 13),
    # Multiple substitutions
    'The M(ansible.builtin.yum) module B(MUST) be given the C(package) parameter.  See the R(looping docs,using-loops) for more info':
    "The [ansible.builtin.yum] module *MUST* be given the `package' parameter.  See the looping docs for more info",
    # Problem cases
    'IBM(International Business Machines)': 'IBM(International Business Machines)',
    'L(the user guide, https://docs.ansible.com/)': 'the user guide <https://docs.ansible.com/>',
    'R(the user guide, user-guide)': 'the user guide',
    # de-rsty refs and anchors
    'yolo :ref:`my boy` does stuff': 'yolo `my boy` does stuff',
    '.. seealso:: Something amazing': 'See also: Something amazing',
    '.. seealso:: Troublesome multiline\n Stuff goes htere': 'See also: Troublesome multiline\n Stuff goes htere',
    '.. note:: boring stuff': 'Note: boring stuff',
}


@pytest.mark.parametrize('text, expected', sorted(TTY_IFY_DATA.items()))
def test_ttyify(text, expected):
    assert DocCLI.tty_ify(text) == expected


def test_rolemixin__build_summary():
    obj = RoleMixin()
    role_name = 'test_role'
    collection_name = 'test.units'
    argspec = {
        'main': {'short_description': 'main short description'},
        'alternate': {'short_description': 'alternate short description'},
    }
    meta = {}
    expected = {
        'collection': collection_name,
        'description': 'UNDOCUMENTED',
        'entry_points': {
            'main': argspec['main']['short_description'],
            'alternate': argspec['alternate']['short_description'],
        }
    }

    fqcn, summary = obj._build_summary(role_name, collection_name, meta, argspec)
    assert fqcn == '.'.join([collection_name, role_name])
    assert summary == expected


def test_rolemixin__build_summary_empty_argspec():
    obj = RoleMixin()
    role_name = 'test_role'
    collection_name = 'test.units'
    argspec = {}
    meta = {}
    expected = {
        'collection': collection_name,
        'description': 'UNDOCUMENTED',
        'entry_points': {}
    }

    fqcn, summary = obj._build_summary(role_name, collection_name, meta, argspec)
    assert fqcn == '.'.join([collection_name, role_name])
    assert summary == expected


def test_rolemixin__build_doc():
    obj = RoleMixin()
    role_name = 'test_role'
    path = '/a/b/c'
    collection_name = 'test.units'
    entrypoint_filter = 'main'
    argspec = {
        'main': {'short_description': 'main short description'},
        'alternate': {'short_description': 'alternate short description'},
    }
    expected = {
        'path': path,
        'collection': collection_name,
        'entry_points': {
            'main': argspec['main'],
        }
    }
    fqcn, doc = obj._build_doc(role_name, path, collection_name, argspec, entrypoint_filter)
    assert fqcn == '.'.join([collection_name, role_name])
    assert doc == expected


def test_rolemixin__build_doc_no_filter_match():
    obj = RoleMixin()
    role_name = 'test_role'
    path = '/a/b/c'
    collection_name = 'test.units'
    entrypoint_filter = 'doesNotExist'
    argspec = {
        'main': {'short_description': 'main short description'},
        'alternate': {'short_description': 'alternate short description'},
    }
    fqcn, doc = obj._build_doc(role_name, path, collection_name, argspec, entrypoint_filter)
    assert fqcn == '.'.join([collection_name, role_name])
    assert doc is None


def test_builtin_modules_list():
    args = ['ansible-doc', '-l', 'ansible.builtin', '-t', 'module']
    obj = DocCLI(args=args)
    obj.parse()
    init_plugin_loader()
    result = obj._list_plugins('module', module_loader)
    assert len(result) > 0


def test_legacy_modules_list():
    args = ['ansible-doc', '-l', 'ansible.legacy', '-t', 'module']
    obj = DocCLI(args=args)
    obj.parse()
    result = obj._list_plugins('module', module_loader)
    assert len(result) > 0
