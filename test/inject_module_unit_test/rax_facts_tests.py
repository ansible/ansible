import StringIO
import unittest

try:
    from novaclient.tests.v1_1 import fakes
except:
    raise SystemExit('"python-novaclient" module not installed')

try:
    import fixtures
except ImportError:
    raise SystemExit('"fixtures" module not installed')

try:
    import testtools
except ImportError:
    raise SystemExit('"testtools" module not installed')


def setup_rax_module(module, rax_module):
    rax_module.cloudservers = fakes.FakeClient()
    return rax_module


class RaxFactsTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(RaxFactsTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.sys_stdout = sys.stdout
        self.sys_stderr = sys.stderr
        sys.stdout = StringIO.StringIO()
        sys.stderr = StringIO.StringIO()

    def tearDown(self):
        sys.stdout = self.sys_stdout
        sys.stderr = self.sys_stderr

    def run_main(self):
        try:
            main()
        except SystemExit:
            pass
        return json.loads(sys.stdout.getvalue())

    def test_correct_id(self):
        global MODULE_ARGS
        MODULE_ARGS = 'id=1234'
        output = self.run_main()
        self.assertTrue(isinstance(output, dict), 'Parsed JSON is not a dict')
        self.assertNotEqual(output['ansible_facts'], {}, 'ansible_facts is empty')
        self.assertEqual(output['ansible_facts'].get('rax_id'), 1234, 'The ID of the server does not match')

    def test_incorrect_id(self):
        global MODULE_ARGS
        MODULE_ARGS = 'id=12345'
        output = self.run_main()
        self.assertTrue(isinstance(output, dict), 'Parsed JSON is not a dict')
        self.assertEqual(output['ansible_facts'], {}, 'ansible_facts is not empty')

    @unittest.skip('The FakeClient does not currently support filtered queries')
    def test_correct_name(self):
        global MODULE_ARGS
        MODULE_ARGS = 'name=sample-server3'
        output = self.run_main()
        self.assertTrue(isinstance(output, dict), 'Parsed JSON is not a dict')
        self.assertNotEqual(output['ansible_facts'], {}, 'ansible_facts is empty')
        self.assertEqual(output['ansible_facts'].get('rax_name'), 'sample-server3', 'The name of the server does not match')

    @unittest.skip('The FakeClient does not currently support filtered queries')
    def test_incorrect_name(self):
        global MODULE_ARGS
        MODULE_ARGS = 'name=ansible'
        output = self.run_main()
        self.assertEqual(output['ansible_facts'], {}, 'ansible_facts is not empty')

    @unittest.skip('The FakeClient does not currently support filtered queries')
    def test_multi_name_match(self):
        global MODULE_ARGS
        MODULE_ARGS = 'name=sample-server'
        output = self.run_main()
        multi = {
            'msg': 'Multiple servers found matching provided search parameters',
            'failed': True
        }
        self.assertEqual(output.get('failed'), multi['failed'], 'Response did not indicate a failure')
        self.assertEqual(output.get('msg'), multi['msg'], 'Response did not indicate multiple matches')

    def test_correct_ip(self):
        global MODULE_ARGS
        MODULE_ARGS = 'address=1.2.3.4'
        output = self.run_main()
        self.assertEqual(output['ansible_facts'].get('rax_id'), 1234, 'The ID of the server does not match')

    def test_incorrect_ip(self):
        global MODULE_ARGS
        MODULE_ARGS = 'address=11.22.33.44'
        output = self.run_main()
        self.assertEqual(output['ansible_facts'], {}, 'ansible_facts is not empty')

    def test_mutually_exclusive(self):
        global MODULE_ARGS
        MODULE_ARGS = 'address=1.2.3.4 id=1.2.3.4'
        output = self.run_main()
        self.assertEqual(output.get('failed'), True, 'Response did not indicate a failure')
        self.assertTrue('parameters are mutually exclusive' in output.get('msg'), 'No error indicating mutually exclusive argument failure')


unittest.main()
