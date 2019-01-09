# Copyright: (c) 2018 Red Hat Inc.
# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import errno
import json

from units.compat.mock import patch
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase
from tempfile import mkstemp
import xml.etree.ElementTree as ET


fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')
fixture_data = {}


def load_fixture(name):
    path = os.path.join(fixture_path, name)

    if path in fixture_data:
        return fixture_data[path]

    with open(path) as f:
        data = f.read()

    try:
        data = json.loads(data)
    except ValueError:
        pass

    fixture_data[path] = data
    return data


class TestPFSenseModule(ModuleTestCase):
    def __init__(self, *args, **kwargs):
        super(TestPFSenseModule, self).__init__(*args, **kwargs)
        self.xml_result = None
        self.tmp_file = None

    def setUp(self):
        """ mocking up """
        super(TestPFSenseModule, self).setUp()

        self.mock_parse = patch('ansible.module_utils.networking.pfsense.pfsense.ET.parse')
        self.parse = self.mock_parse.start()

        self.mock_shutil_move = patch('ansible.module_utils.networking.pfsense.pfsense.shutil.move')
        self.shutil_move = self.mock_shutil_move.start()

        self.mock_phpshell = patch('ansible.module_utils.networking.pfsense.pfsense.PFSenseModule.phpshell')
        self.phpshell = self.mock_phpshell.start()
        self.phpshell.return_value = (0, '', '')

        self.mock_mkstemp = patch('ansible.module_utils.networking.pfsense.pfsense.mkstemp')
        self.mkstemp = self.mock_mkstemp.start()
        self.mkstemp.return_value = mkstemp()
        self.tmp_file = self.mkstemp.return_value[1]

        self.maxDiff = None

    def tearDown(self):
        """ mocking down """
        super(TestPFSenseModule, self).tearDown()

        self.mock_parse.stop()
        self.mock_shutil_move.stop()
        self.mock_phpshell.stop()
        self.mock_mkstemp.stop()

        try:
            if self.tmp_file is not None:
                os.remove(self.tmp_file)
        except OSError as exception:
            if exception.errno != errno.ENOENT:
                raise

    def execute_module(self, failed=False, changed=False, commands=None, sort=True, defaults=False, msg=''):
        self.load_fixtures(commands)

        if failed:
            result = self.failed()
            self.assertTrue(result['failed'], result)
        else:
            result = self.changed(changed)

        if not failed:
            self.assertEqual(result['changed'], changed, result)
        else:
            self.assertEqual(result['msg'], msg)

        if commands is not None:
            if sort:
                self.assertEqual(sorted(commands), sorted(result['commands']), result['commands'])
            else:
                self.assertEqual(commands, result['commands'], result['commands'])

        return result

    def failed(self):
        with self.assertRaises(AnsibleFailJson) as exc:
            self.module.main()

        result = exc.exception.args[0]
        self.assertTrue(result['failed'], result)
        return result

    def changed(self, changed=False):
        with self.assertRaises(AnsibleExitJson) as exc:
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], changed, result)
        return result

    def load_fixtures(self, commands=None):
        pass

    def load_xml_result(self):
        """ load the resulting xml if not already loaded """
        if self.xml_result is None:
            self.xml_result = ET.parse(self.tmp_file)

    @staticmethod
    def find_xml_tag(parent_tag, elt_filter):
        """ return alias named name, having type aliastype """
        for tag in parent_tag:
            found = True
            for key, value in elt_filter.items():
                elt = tag.find(key)
                if elt is not None:
                    if elt.text is None and value is None:
                        continue
                    if elt.text is not None and elt.text == value:
                        continue
                found = False
                break
            if found:
                return tag
        return None

    def assert_xml_elt_value(self, parent_tag_name, elt_filter, elt_name, elt_value):
        """ check the xml elt exist and has the exact value given """
        self.load_xml_result()
        parent_tag = self.xml_result.find(parent_tag_name)
        if parent_tag is None:
            self.fail('Unable to find tag ' + parent_tag_name)

        tag = self.find_xml_tag(parent_tag, elt_filter)
        if tag is None:
            self.fail('Tag not found: ' + json.dumps(elt_filter))

        self.assert_xml_elt_equal(tag, elt_name, elt_value)

    def assert_xml_elt_dict(self, parent_tag_name, elt_filter, elts):
        """ check all the xml elt in elts exist and have the exact value given """
        self.load_xml_result()
        parent_tag = self.xml_result.find(parent_tag_name)
        if parent_tag is None:
            self.fail('Unable to find tag ' + parent_tag_name)

        tag = self.find_xml_tag(parent_tag, elt_filter)
        if tag is None:
            self.fail('Tag not found: ' + json.dumps(elt_filter))

        for elt_name, elt_value in elts.items():
            self.assert_xml_elt_equal(tag, elt_name, elt_value)

    def assert_has_xml_tag(self, parent_tag_name, elt_filter, absent=False):
        """ check the xml elt exist (or not if absent is True) """
        self.load_xml_result()
        parent_tag = self.xml_result.find(parent_tag_name)
        if parent_tag is None:
            self.fail('Unable to find tag ' + parent_tag_name)

        tag = self.find_xml_tag(parent_tag, elt_filter)
        if absent and tag is not None:
            self.fail('Tag found: ' + json.dumps(elt_filter))
        elif not absent and tag is None:
            self.fail('Tag not found: ' + json.dumps(elt_filter))
        return tag

    def assert_find_xml_elt(self, tag, elt_name):
        elt = tag.find(elt_name)
        if elt is None:
            self.fail('Element not found: ' + elt_name)
        return elt

    def assert_not_find_xml_elt(self, tag, elt_name):
        elt = tag.find(elt_name)
        if elt is not None:
            self.fail('Element found: ' + elt_name)
        return elt

    def assert_xml_elt_equal(self, tag, elt_name, elt_value):
        elt = tag.find(elt_name)
        if elt is None:
            self.fail('Element not found: ' + elt_name)
        if elt.text != elt_value:
            self.fail('Element <' + elt_name + '> differs. Expected: \'' + elt_value + '\' result: \'' + elt.text + '\'')
        return elt

    def assert_xml_elt_is_none_or_empty(self, tag, elt_name):
        elt = tag.find(elt_name)
        if elt is None:
            self.fail('Element not found: ' + elt_name)
        if elt.text is not None and elt.text:
            self.fail('Element <' + elt_name + '> differs. Expected: NoneType result: \'' + elt.text + '\'')
        return elt
