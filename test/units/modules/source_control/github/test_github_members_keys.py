# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Sebastián Estrella <sestrella.me@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.modules.source_control.github import github_members_keys
from units.compat import mock
from units.modules import utils


class TestGithubMembersKeys(utils.ModuleTestCase):
    def setUp(self):
        super(TestGithubMembersKeys, self).setUp()
        self.module = github_members_keys

    def test_token_is_required(self):
        with self.assertRaises(utils.AnsibleFailJson) as exec_info:
            utils.set_module_args({
                'organization': 'organization',
                'team': 'team'
            })
            self.module.main()

        self.assertEqual(
            exec_info.exception.args[0]['msg'],
            'missing required arguments: token'
        )

    def test_organization_is_required(self):
        with self.assertRaises(utils.AnsibleFailJson) as exec_info:
            utils.set_module_args({
                'token': 'token',
                'team': 'team'
            })
            self.module.main()

        self.assertEqual(
            exec_info.exception.args[0]['msg'],
            'missing required arguments: organization'
        )

    def test_team_is_required(self):
        with self.assertRaises(utils.AnsibleFailJson) as exec_info:
            utils.set_module_args({
                'token': 'token',
                'organization': 'organization'
            })
            self.module.main()

        self.assertEqual(
            exec_info.exception.args[0]['msg'],
            'missing required arguments: team'
        )

    @mock.patch.object(github_members_keys.GithubClient, 'get_organization_team')
    def test_members_keys(self, team):
        team.return_value.get_members_keys.return_value = [
            github_members_keys.MemberKeys(
                member=mock.Mock(login='user1'),
                keys=[
                    mock.Mock(id=1, key='ssh-rsa AAA...'),
                    mock.Mock(id=2, key='ssh-rsa BBB...')
                ]
            ),
            github_members_keys.MemberKeys(
                member=mock.Mock(login='user2'),
                keys=[
                    mock.MagicMock(id=3, key='ssh-rsa CCC...')
                ]
            )
        ]

        with self.assertRaises(utils.AnsibleExitJson) as exec_info:
            utils.set_module_args({
                'token': 'token',
                'organization': 'organization',
                'team': 'team'
            })
            self.module.main()

        self.assertEqual(exec_info.exception.args[0]['members_keys'], [
            'ssh-rsa AAA... user1-1',
            'ssh-rsa BBB... user1-2',
            'ssh-rsa CCC... user2-3'
        ])

    @mock.patch.object(github_members_keys.GithubClient, 'get_organization_team')
    def test_missing_members(self, team):
        team.return_value.get_members_keys.return_value = [
            github_members_keys.MemberKeys(
                member=mock.Mock(login='user1'),
                keys=[
                    mock.Mock(id=1, key='ssh-rsa AAA...'),
                ]
            )
        ]

        with self.assertRaises(utils.AnsibleFailJson) as exec_info:
            utils.set_module_args({
                'token': 'token',
                'organization': 'organization',
                'team': 'team',
                'mandatory_members': ['user1', 'user2']
            })
            self.module.main()

        self.assertEqual(
            exec_info.exception.args[0]['msg'],
            '[\'user1\'] does not include all mandatory members [\'user2\']'
        )

    @mock.patch.object(github_members_keys.GithubClient, 'get_organization_team')
    def test_mandatory_member_has_no_keys(self, team):
        team.return_value.get_members_keys.return_value = [
            github_members_keys.MemberKeys(
                member=mock.Mock(login='user1'),
                keys=[]
            ),
            github_members_keys.MemberKeys(
                member=mock.Mock(login='user2'),
                keys=[
                    mock.Mock(id=1, key='ssh-rsa CCC...'),
                ]
            )
        ]

        with self.assertRaises(utils.AnsibleFailJson) as exec_info:
            utils.set_module_args({
                'token': 'token',
                'organization': 'organization',
                'team': 'team',
                'mandatory_members': ['user1', 'user2']
            })
            self.module.main()

        self.assertEqual(
            exec_info.exception.args[0]['msg'],
            'Mandatory member user1 has no keys'
        )
