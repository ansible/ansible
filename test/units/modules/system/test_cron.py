from unittest import TestCase

from ansible.modules.system import cron
from units.compat.mock import ANY, call, patch
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args


class TestCronTab(TestCase):
    pass


@patch('ansible.modules.system.cron.CronTab')
class TestCron(ModuleTestCase):

    def test_without_any_parameters(self, crontab_mock):
        """When required parameters are not supplied, an error is returned"""
        with self.assertRaises(AnsibleFailJson):
            set_module_args({})
            cron.main()

    def test_add_crontab(self, crontab_mock):
        """When no job exists, it is created."""
        NAME = 'test task'
        JOB = '/test/job'
        set_module_args({
            'name': NAME,
            'job': JOB,
        })

        # No previous job exists
        crontab_mock.return_value.find_job.return_value = []

        with self.assertRaises(AnsibleExitJson) as result:
            cron.main()
            self.assertTrue(result.exception.args[0]['changed'])
            self.assertEqual('present', result.exception.args[0]['state'])
            self.assertEqual(NAME in result.exception.args[0]['jobs'])

        # A CronTab object is constructed, doesn't find a job, and creates one:
        get_cron_job = crontab_mock.return_value.get_cron_job
        crontab_mock.assert_has_calls([
            call(ANY, None, None),
            call().get_cron_job('*', '*', '*', '*', '*', JOB, None, False),
            call().find_job(NAME, get_cron_job.return_value),
        ])
        crontab_mock.assert_has_calls([
            call().add_job(NAME, get_cron_job.return_value),
            call().get_jobnames(),
            call().get_envnames(),
            call().write(),
        ])

    def test_update_crontab(self, crontab_mock):
        """When job exists, it is updated."""
        NAME = 'test task'
        JOB = '/updated/job'
        set_module_args({
            'name': NAME,
            'user': 'testuser',
            'job': JOB,
        })

        # An old job is already set up:
        crontab_mock.return_value.find_job.return_value = [NAME, '* * * * * testuser /old/job']

        with self.assertRaises(AnsibleExitJson) as result:
            cron.main()
            self.assertTrue(result.exception.args[0]['changed'])
            self.assertEqual('present', result.exception.args[0]['state'])
            self.assertEqual(NAME in result.exception.args[0]['jobs'])

        # A CronTab object is constructed, finds a job, and updates it:
        get_cron_job = crontab_mock.return_value.get_cron_job
        crontab_mock.assert_has_calls([
            call(ANY, 'testuser', None),
            call().get_cron_job('*', '*', '*', '*', '*', JOB, None, False),
            call().find_job(NAME, get_cron_job.return_value),
        ])
        crontab_mock.assert_has_calls([
            call().update_job(NAME, get_cron_job.return_value),
            call().get_jobnames(),
            call().get_envnames(),
            call().write(),
        ])

    def test_delete_crontab(self, crontab_mock):
        """When job exists and is deleted, it is removed."""
        NAME = 'test task'
        set_module_args({
            'name': NAME,
            'state': 'absent',
        })

        # Finds an old job is already set up:
        crontab_mock.return_value.find_job.return_value = [NAME, '* * * * * /old/job']

        with self.assertRaises(AnsibleExitJson) as result:
            cron.main()
            self.assertTrue(result.exception.args[0]['changed'])
            self.assertEqual('absent', result.exception.args[0]['state'])
            self.assertEqual(NAME in result.exception.args[0]['jobs'])

        # A CronTab object is constructed, finds a job, and deletes it:
        crontab_mock.assert_has_calls([
            call(ANY, None, None),
            call().find_job(NAME),
        ])
        crontab_mock.assert_has_calls([
            call().remove_job(NAME),
            call().get_jobnames(),
            call().get_envnames(),
            call().write(),
        ])
