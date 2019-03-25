# Copyright (c) 2018 Antoine Catton
# MIT License (see licenses/MIT-license.txt or https://opensource.org/licenses/MIT)
import copy
import json

import pytest

from ansible.modules.packaging.language import gem
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args


def get_command(run_command):
    """Generate the command line string from the patched run_command"""
    args = run_command.call_args[0]
    command = args[0]
    return ' '.join(command)


class TestGem(ModuleTestCase):
    def setUp(self):
        super(TestGem, self).setUp()
        self.rubygems_path = ['/usr/bin/gem']
        self.mocker.patch(
            'ansible.modules.packaging.language.gem.get_rubygems_path',
            lambda module: copy.deepcopy(self.rubygems_path),
        )

    @pytest.fixture(autouse=True)
    def _mocker(self, mocker):
        self.mocker = mocker

    def patch_installed_versions(self, versions):
        """Mocks the versions of the installed package"""

        target = 'ansible.modules.packaging.language.gem.get_installed_versions'

        def new(module, remote=False):
            return versions

        return self.mocker.patch(target, new)

    def patch_rubygems_version(self, version=None):
        target = 'ansible.modules.packaging.language.gem.get_rubygems_version'

        def new(module):
            return version

        return self.mocker.patch(target, new)

    def patch_run_command(self):
        target = 'ansible.module_utils.basic.AnsibleModule.run_command'
        return self.mocker.patch(target)

    def test_fails_when_user_install_and_install_dir_are_combined(self):
        set_module_args({
            'name': 'dummy',
            'user_install': True,
            'install_dir': '/opt/dummy',
        })

        with pytest.raises(AnsibleFailJson) as exc:
            gem.main()

        result = exc.value.args[0]
        assert result['failed']
        assert result['msg'] == "install_dir requires user_install=false"

    def test_passes_install_dir_to_gem(self):
        # XXX: This test is extremely fragile, and makes assuptions about the module code, and how
        #      functions are run.
        #      If you start modifying the code of the module, you might need to modify what this
        #      test mocks. The only thing that matters is the assertion that this 'gem install' is
        #      invoked with '--install-dir'.

        set_module_args({
            'name': 'dummy',
            'user_install': False,
            'install_dir': '/opt/dummy',
        })

        self.patch_rubygems_version()
        self.patch_installed_versions([])
        run_command = self.patch_run_command()

        with pytest.raises(AnsibleExitJson) as exc:
            gem.main()

        result = exc.value.args[0]
        assert result['changed']
        assert run_command.called

        assert '--install-dir /opt/dummy' in get_command(run_command)

    def test_passes_install_dir_and_gem_home_when_uninstall_gem(self):
        # XXX: This test is also extremely fragile because of mocking.
        #      If this breaks, the only that matters is to check whether '--install-dir' is
        #      in the run command, and that GEM_HOME is passed to the command.
        set_module_args({
            'name': 'dummy',
            'user_install': False,
            'install_dir': '/opt/dummy',
            'state': 'absent',
        })

        self.patch_rubygems_version()
        self.patch_installed_versions(['1.0.0'])

        run_command = self.patch_run_command()

        with pytest.raises(AnsibleExitJson) as exc:
            gem.main()

        result = exc.value.args[0]

        assert result['changed']
        assert run_command.called

        assert '--install-dir /opt/dummy' in get_command(run_command)

        update_environ = run_command.call_args[1].get('environ_update', {})
        assert update_environ.get('GEM_HOME') == '/opt/dummy'

    def test_passes_add_force_option(self):
        set_module_args({
            'name': 'dummy',
            'force': True,
        })

        self.patch_rubygems_version()
        self.patch_installed_versions([])
        run_command = self.patch_run_command()

        with pytest.raises(AnsibleExitJson) as exc:
            gem.main()

        result = exc.value.args[0]
        assert result['changed']
        assert run_command.called

        assert '--force' in get_command(run_command)
