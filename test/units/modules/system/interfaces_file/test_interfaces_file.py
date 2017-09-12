# (c) 2017, Roman Belyakovsky <ihryamzik () gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from ansible.compat.tests import unittest
import ansible.module_utils.basic
from ansible.modules.system import interfaces_file
import os
import json
import sys
import io
import inspect
import json


class AnsibleFailJson(Exception):
    pass


class ModuleMocked():
    def fail_json(self, msg):
        raise AnsibleFailJson(msg)
        pass


module = ModuleMocked()
fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'input')
golden_output_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'golden_output')


class TestInterfacesFileModule(unittest.TestCase):
    def getTestFiles(self):
        return next(os.walk(fixture_path))[2]

    def compareInterfacesLinesToFile(self, interfaces_lines, path, testname=None):
        if not testname:
            testname = "%s.%s" % (path, inspect.stack()[1][3])
        self.compareStringWithFile("".join([d['line'] for d in interfaces_lines if 'line' in d]), testname)

    def compareInterfacesToFile(self, ifaces, path, testname=None):
        if not testname:
            testname = "%s.%s.json" % (path, inspect.stack()[1][3])
        self.compareStringWithFile(json.dumps(ifaces, sort_keys=True, indent=4, separators=(',', ': ')), testname)

    def compareStringWithFile(self, string, path):
        # self.assertEqual("","_",msg=path)
        testfilepath = os.path.join(golden_output_path, path)
        goldenstring = string
        if not os.path.isfile(testfilepath):
            f = io.open(testfilepath, 'wb')
            f.write(string)
            f.close()
        else:
            with open(testfilepath, 'r') as goldenfile:
                goldenstring = goldenfile.read()
                goldenfile.close()
        self.assertEqual(string, goldenstring)

    def test_no_changes(self):
        for testfile in self.getTestFiles():
            path = os.path.join(fixture_path, testfile)
            lines, ifaces = interfaces_file.read_interfaces_file(module, path)
            self.compareInterfacesLinesToFile(lines, testfile)
            self.compareInterfacesToFile(ifaces, testfile)

    def test_add_up_aoption_to_aggi(self):
        testcases = {
            "add_aggi_up": [
                {
                    'iface': 'aggi',
                    'option': 'up',
                    'value': 'route add -net 224.0.0.0 netmask 240.0.0.0 dev aggi',
                    'state': 'present',
                }
            ],
            "add_and_delete_aggi_up": [
                {
                    'iface': 'aggi',
                    'option': 'up',
                    'value': 'route add -net 224.0.0.0 netmask 240.0.0.0 dev aggi',
                    'state': 'present',
                },
                {
                    'iface': 'aggi',
                    'option': 'up',
                    'value': None,
                    'state': 'absent',
                },
            ],
            "set_aggi_slaves": [
                {
                    'iface': 'aggi',
                    'option': 'slaves',
                    'value': 'int1  int3',
                    'state': 'present',
                },
            ],
            "set_aggi_and_eth0_mtu": [
                {
                    'iface': 'aggi',
                    'option': 'mtu',
                    'value': '1350',
                    'state': 'present',
                },
                {
                    'iface': 'eth0',
                    'option': 'mtu',
                    'value': '1350',
                    'state': 'present',
                },
            ],
        }
        for testname, options_list in testcases.items():
            for testfile in self.getTestFiles():
                path = os.path.join(fixture_path, testfile)
                lines, ifaces = interfaces_file.read_interfaces_file(module, path)
                fail_json_iterations = []
                for i, options in enumerate(options_list):
                    try:
                        _, lines = interfaces_file.setInterfaceOption(module, lines, options['iface'], options['option'], options['value'], options['state'])
                    except AnsibleFailJson as e:
                        fail_json_iterations.append("[%d] fail_json message: %s\noptions:\n%s" %
                                                    (i, str(e), json.dumps(options, sort_keys=True, indent=4, separators=(',', ': '))))
                self.compareStringWithFile("\n=====\n".join(fail_json_iterations), "%s_%s.exceptions.txt" % (testfile, testname))

                self.compareInterfacesLinesToFile(lines, testfile, "%s_%s" % (testfile, testname))
                self.compareInterfacesToFile(ifaces, testfile, "%s_%s.json" % (testfile, testname))
