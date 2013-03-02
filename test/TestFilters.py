'''
Test bundled filters
'''

import unittest, tempfile, shutil
from ansible import playbook, inventory, callbacks

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

        out = open(dest).read()
        self.assertEqual(DEST, out)

