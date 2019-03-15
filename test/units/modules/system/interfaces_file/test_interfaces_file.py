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

from units.compat import unittest
from ansible.modules.system import interfaces_file
from shutil import copyfile, move
import difflib
import inspect
import io
import json
import os
import re
import shutil
import tempfile


class AnsibleFailJson(Exception):
    pass


class ModuleMocked():
    def atomic_move(self, src, dst):
        move(src, dst)

    def backup_local(self, path):
        backupp = os.path.join("/tmp", os.path.basename(path) + ".bak")
        copyfile(path, backupp)
        return backupp

    def fail_json(self, msg):
        raise AnsibleFailJson(msg)


module = ModuleMocked()
fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'input')
golden_output_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'golden_output')


class TestInterfacesFileModule(unittest.TestCase):
    def getTestFiles(self, include_filter=None, exclude_filter=None):
        flist = next(os.walk(fixture_path))[2]
        if include_filter:
            flist = filter(lambda x: re.match(include_filter, x), flist)
        if exclude_filter:
            flist = filter(lambda x: not re.match(exclude_filter, x), flist)
        return flist

    def compareFileToBackup(self, path, backup):
        with open(path) as f1:
            with open(backup) as f2:
                diffs = difflib.context_diff(f1.readlines(),
                                             f2.readlines(),
                                             fromfile=os.path.basename(path),
                                             tofile=os.path.basename(backup))
        # Restore backup
        move(backup, path)
        deltas = [d for d in diffs]
        self.assertTrue(len(deltas) == 0)

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

    def test_revert(self):
        testcases = {
            "revert": [
                {
                    'iface': 'eth0',
                    'option': 'mtu',
                    'value': '1350',
                }
            ],
        }
        for testname, options_list in testcases.items():
            for testfile in self.getTestFiles():
                with tempfile.NamedTemporaryFile() as temp_file:
                    src_path = os.path.join(fixture_path, testfile)
                    path = temp_file.name
                    shutil.copy(src_path, path)
                    lines, ifaces = interfaces_file.read_interfaces_file(module, path)
                    backupp = module.backup_local(path)
                    options = options_list[0]
                    for state in ['present', 'absent']:
                        fail_json_iterations = []
                        options['state'] = state
                        try:
                            _, lines = interfaces_file.setInterfaceOption(module, lines,
                                                                          options['iface'], options['option'], options['value'], options['state'])
                        except AnsibleFailJson as e:
                            fail_json_iterations.append("fail_json message: %s\noptions:\n%s" %
                                                        (str(e), json.dumps(options, sort_keys=True, indent=4, separators=(',', ': '))))
                        interfaces_file.write_changes(module, [d['line'] for d in lines if 'line' in d], path)

                    self.compareStringWithFile("\n=====\n".join(fail_json_iterations), "%s_%s.exceptions.txt" % (testfile, testname))

                    self.compareInterfacesLinesToFile(lines, testfile, "%s_%s" % (testfile, testname))
                    self.compareInterfacesToFile(ifaces, testfile, "%s_%s.json" % (testfile, testname))
                    self.compareFileToBackup(path, backupp)

    def test_change_method(self):
        testcases = {
            "change_method": [
                {
                    'iface': 'eth1',
                    'option': 'method',
                    'value': 'dhcp',
                    'state': 'present',
                }
            ],
        }
        for testname, options_list in testcases.items():
            for testfile in self.getTestFiles():
                with tempfile.NamedTemporaryFile() as temp_file:
                    src_path = os.path.join(fixture_path, testfile)
                    path = temp_file.name
                    shutil.copy(src_path, path)
                    lines, ifaces = interfaces_file.read_interfaces_file(module, path)
                    backupp = module.backup_local(path)
                    options = options_list[0]
                    fail_json_iterations = []
                    try:
                        changed, lines = interfaces_file.setInterfaceOption(module, lines, options['iface'], options['option'],
                                                                            options['value'], options['state'])
                        # When a changed is made try running it again for proper idempotency
                        if changed:
                            changed_again, lines = interfaces_file.setInterfaceOption(module, lines, options['iface'],
                                                                                      options['option'], options['value'], options['state'])
                            self.assertFalse(changed_again,
                                             msg='Second request for change should return false for {0} running on {1}'.format(testname,
                                                                                                                               testfile))
                    except AnsibleFailJson as e:
                        fail_json_iterations.append("fail_json message: %s\noptions:\n%s" %
                                                    (str(e), json.dumps(options, sort_keys=True, indent=4, separators=(',', ': '))))
                    interfaces_file.write_changes(module, [d['line'] for d in lines if 'line' in d], path)

                    self.compareStringWithFile("\n=====\n".join(fail_json_iterations), "%s_%s.exceptions.txt" % (testfile, testname))

                    self.compareInterfacesLinesToFile(lines, testfile, "%s_%s" % (testfile, testname))
                    self.compareInterfacesToFile(ifaces, testfile, "%s_%s.json" % (testfile, testname))
                    # Restore backup
                    move(backupp, path)

    def test_inet_inet6(self):
        testcases = {
            "change_ipv4": [
                {
                    'iface': 'eth0',
                    'address_family': 'inet',
                    'option': 'address',
                    'value': '192.168.0.42',
                    'state': 'present',
                }
            ],
            "change_ipv6": [
                {
                    'iface': 'eth0',
                    'address_family': 'inet6',
                    'option': 'address',
                    'value': 'fc00::42',
                    'state': 'present',
                }
            ],
            "change_ipv4_pre_up": [
                {
                    'iface': 'eth0',
                    'address_family': 'inet',
                    'option': 'pre-up',
                    'value': 'XXXX_ipv4',
                    'state': 'present',
                }
            ],
            "change_ipv6_pre_up": [
                {
                    'iface': 'eth0',
                    'address_family': 'inet6',
                    'option': 'pre-up',
                    'value': 'XXXX_ipv6',
                    'state': 'present',
                }
            ],
            "change_ipv4_post_up": [
                {
                    'iface': 'eth0',
                    'address_family': 'inet',
                    'option': 'post-up',
                    'value': 'XXXX_ipv4',
                    'state': 'present',
                }
            ],
            "change_ipv6_post_up": [
                {
                    'iface': 'eth0',
                    'address_family': 'inet6',
                    'option': 'post-up',
                    'value': 'XXXX_ipv6',
                    'state': 'present',
                }
            ],
        }
        for testname, options_list in testcases.items():
            for testfile in self.getTestFiles():
                with tempfile.NamedTemporaryFile() as temp_file:
                    src_path = os.path.join(fixture_path, testfile)
                    path = temp_file.name
                    shutil.copy(src_path, path)
                    lines, ifaces = interfaces_file.read_interfaces_file(module, path)
                    backupp = module.backup_local(path)
                    options = options_list[0]
                    fail_json_iterations = []
                    try:
                        _, lines = interfaces_file.setInterfaceOption(module, lines, options['iface'], options['option'],
                                                                      options['value'], options['state'], options['address_family'])
                    except AnsibleFailJson as e:
                        fail_json_iterations.append("fail_json message: %s\noptions:\n%s" %
                                                    (str(e), json.dumps(options, sort_keys=True, indent=4, separators=(',', ': '))))
                    interfaces_file.write_changes(module, [d['line'] for d in lines if 'line' in d], path)

                    self.compareStringWithFile("\n=====\n".join(fail_json_iterations), "%s_%s.exceptions.txt" % (testfile, testname))

                    self.compareInterfacesLinesToFile(lines, testfile, "%s_%s" % (testfile, testname))
                    self.compareInterfacesToFile(ifaces, testfile, "%s_%s.json" % (testfile, testname))
                    # Restore backup
                    move(backupp, path)
