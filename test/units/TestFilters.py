'''
Test bundled filters
'''

import os.path
import unittest, tempfile, shutil
from ansible import playbook, inventory, callbacks
import ansible.runner.filter_plugins.core

INVENTORY = inventory.Inventory(['localhost'])

BOOK = '''
- hosts: localhost
  vars:
    var: { a: [1,2,3] }
  tasks:
  - template: src=%s dest=%s
'''

SRC = '''
-
{{ var|to_json }}
-
{{ var|to_nice_json }}
-
{{ var|to_yaml }}
-
{{ var|to_nice_yaml }}
'''

DEST = '''
-
{"a": [1, 2, 3]}
-
{
    "a": [
        1, 
        2, 
        3
    ]
}
-
a: [1, 2, 3]

-
a:
- 1
- 2
- 3
'''

class TestFilters(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(dir='/tmp')

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def temp(self, name, data=''):
        '''write a temporary file and return the name'''
        name = self.tmpdir + '/' + name
        with open(name, 'w') as f:
            f.write(data)
        return name

    def test_bool_none(self):
        a = ansible.runner.filter_plugins.core.bool(None)
        assert a == None

    def test_bool_true(self):
        a = ansible.runner.filter_plugins.core.bool(True)
        assert a == True

    def test_bool_yes(self):
        a = ansible.runner.filter_plugins.core.bool('Yes')
        assert a == True

    def test_bool_no(self):
        a = ansible.runner.filter_plugins.core.bool('Foo')
        assert a == False

    def test_quotes(self):
        a = ansible.runner.filter_plugins.core.quote('ls | wc -l')
        assert a == "'ls | wc -l'"

    def test_fileglob(self):
        pathname = os.path.join(os.path.dirname(__file__), '*')
        a = ansible.runner.filter_plugins.core.fileglob(pathname)
        assert __file__ in a

    def test_regex(self):
        a = ansible.runner.filter_plugins.core.regex('ansible', 'ansible',
                                                     match_type='findall')
        assert a == True

    def test_match_case_sensitive(self):
        a = ansible.runner.filter_plugins.core.match('ansible', 'ansible')
        assert a == True

    def test_match_case_insensitive(self):
        a = ansible.runner.filter_plugins.core.match('ANSIBLE', 'ansible',
                                                     True)
        assert a == True

    def test_match_no_match(self):
        a = ansible.runner.filter_plugins.core.match(' ansible', 'ansible')
        assert a == False

    def test_search_case_sensitive(self):
        a = ansible.runner.filter_plugins.core.search(' ansible ', 'ansible')
        assert a == True

    def test_search_case_insensitive(self):
        a = ansible.runner.filter_plugins.core.search(' ANSIBLE ', 'ansible',
                                                      True)
        assert a == True

    def test_regex_replace_case_sensitive(self):
        a = ansible.runner.filter_plugins.core.regex_replace('ansible', '^a.*i(.*)$',
                                                      'a\\1')
        assert a == 'able'

    def test_regex_replace_case_insensitive(self):
        a = ansible.runner.filter_plugins.core.regex_replace('ansible', '^A.*I(.*)$',
                                                      'a\\1', True)
        assert a == 'able'

    def test_regex_replace_no_match(self):
        a = ansible.runner.filter_plugins.core.regex_replace('ansible', '^b.*i(.*)$',
                                                      'a\\1')
        assert a == 'ansible'

    #def test_filters(self):

        # this test is pretty low level using a playbook, hence I am disabling it for now -- MPD.
        #return

        #src = self.temp('src.j2', SRC)
        #dest = self.temp('dest.txt')
        #book = self.temp('book', BOOK % (src, dest))

        #playbook.PlayBook(
        #    playbook  = book,
        #    inventory = INVENTORY,
        #    transport = 'local',
        #    callbacks = callbacks.PlaybookCallbacks(),
        #    runner_callbacks = callbacks.DefaultRunnerCallbacks(),
        #    stats  = callbacks.AggregateStats(),
        #).run()

        #out = open(dest).read()
        #self.assertEqual(DEST, out)

    def test_version_compare(self):
        self.assertTrue(ansible.runner.filter_plugins.core.version_compare(0, 1.1, 'lt', False))
        self.assertTrue(ansible.runner.filter_plugins.core.version_compare(1.1, 1.2, '<'))

        self.assertTrue(ansible.runner.filter_plugins.core.version_compare(1.2, 1.2, '=='))
        self.assertTrue(ansible.runner.filter_plugins.core.version_compare(1.2, 1.2, '='))
        self.assertTrue(ansible.runner.filter_plugins.core.version_compare(1.2, 1.2, 'eq'))


        self.assertTrue(ansible.runner.filter_plugins.core.version_compare(1.3, 1.2, 'gt'))
        self.assertTrue(ansible.runner.filter_plugins.core.version_compare(1.3, 1.2, '>'))

        self.assertTrue(ansible.runner.filter_plugins.core.version_compare(1.3, 1.2, 'ne'))
        self.assertTrue(ansible.runner.filter_plugins.core.version_compare(1.3, 1.2, '!='))
        self.assertTrue(ansible.runner.filter_plugins.core.version_compare(1.3, 1.2, '<>'))

        self.assertTrue(ansible.runner.filter_plugins.core.version_compare(1.1, 1.1, 'ge'))
        self.assertTrue(ansible.runner.filter_plugins.core.version_compare(1.2, 1.1, '>='))

        self.assertTrue(ansible.runner.filter_plugins.core.version_compare(1.1, 1.1, 'le'))
        self.assertTrue(ansible.runner.filter_plugins.core.version_compare(1.0, 1.1, '<='))

        self.assertTrue(ansible.runner.filter_plugins.core.version_compare('12.04', 12, 'ge'))
