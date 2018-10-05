import json

import pytest
from ansible.modules.web_infrastructure import django_manage

pytestmark = pytest.mark.usefixtures('patch_ansible_module')

TESTCASE_NO_ARGUMENTS = [
    'cleanup',
    'validate',
    'my_custom_command',
]

TESTCASE_NO_INPUT_COMMANDS = [
    "flush",
    "syncdb",
    "migrate",
    "test",
    "collectstatic",
]


def dummy_run_command(module, cmd, *args, **kwargs):
    return 0, "", ""


def base_test(mocker, module_arguments):
    arguments_as_dict = json.loads(module_arguments)['ANSIBLE_MODULE_ARGS']

    mocker.patch.object(django_manage.AnsibleModule,
                        'run_command',
                        new=dummy_run_command)
    mocker.spy(django_manage.AnsibleModule, 'run_command')

    with pytest.raises(SystemExit):
        django_manage.main()

    return arguments_as_dict


@pytest.mark.parametrize(argnames='patch_ansible_module',
                         argvalues=[
                             {
                                 "command": cmd_name,
                                 "app_path": "dummy.path.to.module"
                             }
                             for cmd_name in TESTCASE_NO_ARGUMENTS
                         ],
                         indirect=['patch_ansible_module'])
def test_no_arguments(mocker, patch_ansible_module):
    arguments = base_test(mocker=mocker, module_arguments=patch_ansible_module)

    assert django_manage.AnsibleModule.run_command.call_count == 1

    arg_list = django_manage.AnsibleModule.run_command.call_args_list
    args, kwargs = arg_list[0]

    assert args[1] == './manage.py %s' % arguments["command"]
    assert kwargs['cwd'] == arguments["app_path"]


@pytest.mark.parametrize(argnames='patch_ansible_module',
                         argvalues=[
                             {
                                 "command": cmd_name,
                                 "app_path": "dummy.path.to.module"
                             }
                             for cmd_name in TESTCASE_NO_INPUT_COMMANDS
                         ],
                         indirect=['patch_ansible_module'])
def test_no_input_commands(mocker, patch_ansible_module):
    arguments = base_test(mocker=mocker, module_arguments=patch_ansible_module)

    assert django_manage.AnsibleModule.run_command.call_count == 1

    arg_list = django_manage.AnsibleModule.run_command.call_args_list
    args, kwargs = arg_list[0]

    assert args[1] == './manage.py %s --noinput' % arguments["command"]
    assert kwargs['cwd'] == arguments["app_path"]


@pytest.mark.parametrize(argnames='patch_ansible_module',
                         argvalues=[
                             {
                                 "command": "test --parallel",
                                 "failfast": True,
                                 "app_path": "dummy.path.to.module"
                             }
                         ],
                         indirect=['patch_ansible_module'])
def test_failfast_with_arguments(mocker, patch_ansible_module):
    """
    Tests that failfast does not break when passing arguments to the command as reported in #42027
    """
    arguments = base_test(mocker=mocker, module_arguments=patch_ansible_module)

    assert django_manage.AnsibleModule.run_command.call_count == 1

    arg_list = django_manage.AnsibleModule.run_command.call_args_list
    args, kwargs = arg_list[0]

    assert args[1] == './manage.py %s --failfast' % arguments["command"]
    assert kwargs['cwd'] == arguments["app_path"]
