import logging

from ansible.playbook.role import definition
from ansible.playbook.role import requirement

log = logging.getLogger(__name__)


def test_role_requirement():
    rr = requirement.RoleRequirement()

    assert isinstance(rr, requirement.RoleRequirement)
    assert isinstance(rr, definition.RoleDefinition)


def test_repo_url_to_repo_name():
    repo_url = 'http://git.example.com/repos/repo.git'
    res = requirement.RoleRequirement.repo_url_to_role_name(repo_url)

    log.debug('res: %s', res)

    assert res == 'repo'


def test_role_spec_parse():

    res = requirement.RoleRequirement.role_spec_parse('foo.bar')

    log.debug('res: %s', res)

    assert isinstance(res, dict)
    assert res['name'] == 'foo.bar'
    assert res['src'] == 'foo.bar'


def test_role_spec_parse_example():
    role_spec = 'git+http://git.example.com/repos/repo.git,v1.0'
    res = requirement.RoleRequirement.role_spec_parse(role_spec)

    # {'scm': 'git', 'src': 'http://git.example.com/repos/repo.git',
    #  'version': 'v1.0', 'name': 'repo'}
    log.debug('res: %s', res)

    assert isinstance(res, dict)
    assert res['name'] == 'repo'
    assert res['scm'] == 'git'
    assert res['src'] == 'http://git.example.com/repos/repo.git'
    assert res['version'] == 'v1.0'


def test_role_yaml_parse_dict_old_style():
    role_yaml = {'role': "galaxy.role,v1.2.3,role_name", 'other_vars': "here"}
    res = requirement.RoleRequirement.role_yaml_parse(role_yaml)

    log.debug('res: %s', res)
    # {'scm': None, 'src': 'galaxy.role', 'version': 'v1.2.3', 'name': 'role_name'}
    assert isinstance(res, dict)
    assert res['name'] == 'role_name'
    assert res['version'] == 'v1.2.3'
    assert res['src'] == 'galaxy.role'

#
# def test_role_yaml_parse_dict_new_style():
#     # NOTE: the example in the comments for role_yaml_parse fails
#     role_yaml = {'src': 'git+http://github.com/some_galaxy/some_role,v1.2.3,role_name', 'other_vars': "here"}
#
#     res = requirement.RoleRequirement.role_yaml_parse(role_yaml)
#
#     log.debug('res: %s', res)
#     # {'scm': None, 'src': 'galaxy.role', 'version': 'v1.2.3', 'name': 'role_name'}
#     assert isinstance(res, dict)
#     assert res['name'] == 'role_name'
#     assert res['version'] == 'v1.2.3'
#     assert res['src'] == 'galaxy.role'
#


def test_role_yaml_parse_string():
    role_yaml = 'galaxy.role,v1.2.3,role_name'
    res = requirement.RoleRequirement.role_yaml_parse(role_yaml)

    log.debug('res: %s', res)

    assert isinstance(res, dict)
    assert res['name'] == 'role_name'
    assert res['version'] == 'v1.2.3'
    assert res['src'] == 'galaxy.role'
