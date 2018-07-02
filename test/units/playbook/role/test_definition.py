import logging
import os.path

import pytest

from ansible import errors
from ansible.playbook.role import definition

log = logging.getLogger(__name__)


def test_role_definition(mocker):
    res = definition.RoleDefinition(play=None, role_basedir=None, variable_manager=None, loader=None)

    assert isinstance(res, definition.RoleDefinition)


def test_role_definition_load_role_path_from_content_path(mocker):
    mock_loader = mocker.Mock(name='MockDataLoader')
    mock_loader.get_basedir = mocker.Mock(return_value='/dev/null/roles')
    mock_loader.path_exists = mocker.Mock(return_value=True)

    content_path = '/dev/null/content/'
    mocker.patch('ansible.playbook.role.definition.C.DEFAULT_CONTENT_PATH',
                 [content_path])
    rd = definition.RoleDefinition(play=None, role_basedir=None, variable_manager=None, loader=mock_loader)

    role_name = 'namespace.repo.role'
    res = rd._load_role_path(role_name)

    log.debug('res: %s', res)
    assert isinstance(res, tuple)
    assert res[0] == role_name
    assert res[1] == os.path.join(content_path, 'namespace/repo/roles/role')


def test_role_definition_load_role_path_from_role_path(mocker):
    mock_loader = mocker.Mock(name='MockDataLoader')
    mock_loader.get_basedir = mocker.Mock(return_value='/dev/null/playbook_rel_roles_dir')
    mock_loader.path_exists = mocker.Mock(return_value=True)

    content_path = '/dev/null/content/'
    role_path = '/dev/null/the_default_roles_path'
    mocker.patch('ansible.playbook.role.definition.C.DEFAULT_CONTENT_PATH',
                 [content_path])
    mocker.patch('ansible.playbook.role.definition.C.DEFAULT_ROLES_PATH',
                 [role_path])
    rd = definition.RoleDefinition(play=None, role_basedir='/dev/null/role_basedir', variable_manager=None, loader=mock_loader)

    role_name = 'some_role'
    rd.preprocess_data({'role': role_name})
    res = rd._load_role_path(role_name)

    log.debug('res: %s', res)
    assert isinstance(res, tuple)
    # The playbook rel roles/ dir is the first path checked
    assert res[1] == '/dev/null/playbook_rel_roles_dir/roles/some_role'


def test_role_definition_load_role_path_from_role_path_not_found(mocker):
    mock_loader = mocker.Mock(name='MockDataLoader')
    mock_loader.get_basedir = mocker.Mock(return_value='/dev/null/playbook_rel_roles_dir')
    mock_loader.path_exists = mocker.Mock(return_value=False)

    content_path = '/dev/null/content/'
    role_path = '/dev/null/the_default_roles_path'
    mocker.patch('ansible.playbook.role.definition.C.DEFAULT_CONTENT_PATH',
                 [content_path])
    mocker.patch('ansible.playbook.role.definition.C.DEFAULT_ROLES_PATH',
                 [role_path])
    rd = definition.RoleDefinition(play=None, role_basedir='/dev/null/role_basedir', variable_manager=None, loader=mock_loader)

    role_name = 'some_role'
    with pytest.raises(errors.AnsibleError, match='.'):
        # pres = rd.preprocess_data({'role': role_name})
        pres = rd.preprocess_data(role_name)
        log.debug('pres: %s', pres)
        rd._load_role_path(role_name)


def test_role_definition_load_role_no_name_in_role_ds(mocker):
    mock_loader = mocker.Mock(name='MockDataLoader')
    mock_loader.get_basedir = mocker.Mock(return_value='/dev/null/playbook_rel_roles_dir')
    mock_loader.path_exists = mocker.Mock(return_value=True)

    content_path = '/dev/null/content/'
    role_path = '/dev/null/the_default_roles_path'
    mocker.patch('ansible.playbook.role.definition.C.DEFAULT_CONTENT_PATH',
                 [content_path])
    mocker.patch('ansible.playbook.role.definition.C.DEFAULT_ROLES_PATH',
                 [role_path])
    rd = definition.RoleDefinition(play=None, role_basedir='/dev/null/role_basedir', variable_manager=None, loader=mock_loader)

    role_name = 'some_role'
    with pytest.raises(errors.AnsibleError, match='role definitions must contain a role name'):
        rd.preprocess_data({'stuff': role_name,
                            'things_i_like': ['cheese', 'naps']})


@pytest.mark.parametrize("role_name,expected",
                         [('namespace.repo.role', 'namespace/repo/roles/role'),
                          ('a.a.a', 'a/a/roles/a'),
                          ('too.many.dots.lets.assume.extra.dots.are.role.name',
                           'too/many/roles/dots.lets.assume.extra.dots.are.role.name'),
                          # valid if role names can include sub paths? should raise an error?
                          ('ns.repo.role/name/roles/role', 'ns/repo/roles/role/name/roles/role'),
                          # DWIM
                          ('geerlingguy.apache', 'geerlingguy/apache/roles/apache'),

                          # these are actually legit 'role_name' inside ansible
                          # they get used as relative paths
                          ('../../some_dir/foo', None),
                          ('../some_dir.foo.bar', None),
                          ('.', None),
                          ('/', None),
                          ('./foo', None),
                          ('.', None),

                          ('justaname', None),
                          ('namespace_dot.', None),
                          ('somenamespace/somerepo/roles/somerole', None),

                          (None, None),
                          ])
def test_role_name_to_relative_content_path(role_name, expected):
    res = definition.role_name_to_relative_content_path(role_name)
    log.debug('res: %s', res)
    assert res == expected


def test_find_role_in_content_path_invalid_role_name(mocker):
    mock_loader = mocker.Mock(return_value=False)
    res = definition.find_role_in_content_path('justaname', mock_loader, '/dev/null/foo')

    assert res is None


def test_find_role_in_content_path_loader_cant_find(mocker):
    mock_loader = mocker.Mock(path_exists=mocker.Mock(return_value=False))
    res = definition.find_role_in_content_path('namespace.repo.rolename', mock_loader, ['/dev/null/foo'])

    assert res is None


def test_find_role_in_content_path_loader(mocker):
    content_search_path = '/dev/null/foo'
    role_name = 'namespace.repo.rolename'
    mock_loader = mocker.Mock(path_exists=mocker.Mock(return_value=True))
    res = definition.find_role_in_content_path(role_name, mock_loader, [content_search_path])

    assert isinstance(res, tuple)
    assert res[0] == role_name
    assert res[1] == os.path.join(content_search_path, 'namespace/repo/roles/rolename')
