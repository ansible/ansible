# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

import urllib.error

from units.compat import unittest
from units.compat.mock import call, create_autospec, mock_open, patch
from ansible.module_utils.basic import AnsibleModule

from cloud.somebodyscomputer import firstmod


class TestFirstMod(unittest.TestCase):

    @patch('cloud.somebodyscomputer.firstmod.open_url')
    def test__fetch__happy_path(self, open_url):
        # Setup
        url = "https://www.google.com"

        # mock the return value of open_url
        stream = open_url.return_value
        stream.read.return_value = "<html><head></head><body>Hello</body></html>"
        stream.getcode.return_value = 200
        open_url.return_value = stream

        # Exercise
        data = firstmod.fetch(url)

        # Verify
        self.assertEqual(stream.read.return_value, data)

        self.assertEqual(1, open_url.call_count)

        expected = call(url)
        self.assertEqual(expected, open_url.call_args)

    @patch('cloud.somebodyscomputer.firstmod.open_url')
    def test__fetch__not_found(self, open_url):
        # Setup
        url = "http://blahblah.non.existent"

        open_url.side_effect = urllib.error.URLError("Unknown URL")

        # Exercise
        with self.assertRaises(firstmod.FetchError):
            firstmod.fetch(url)

    @patch('cloud.somebodyscomputer.firstmod.write')
    @patch('cloud.somebodyscomputer.firstmod.fetch')
    def test__save_data__happy_path(self, fetch, write):
        # Setup
        mod_cls = create_autospec(AnsibleModule)
        mod = mod_cls.return_value
        mod.params = dict(
            url="https://www.google.com",
            dest="/tmp/firstmod.txt"
        )

        # Exercise
        firstmod.save_data(mod)

        # Verify
        self.assertEqual(1, mod.exit_json.call_count)

        expected = call(msg="Data saved", changed=True)
        self.assertEqual(expected, mod.exit_json.call_args)

        self.assertEqual(1, fetch.call_count)

        expected = call(mod.params["url"])
        self.assertEqual(expected, fetch.call_args)

        self.assertEqual(1, write.call_count)

        expected = call(fetch.return_value, mod.params["dest"])
        self.assertEqual(expected, write.call_args)

    @patch('cloud.somebodyscomputer.firstmod.write')
    @patch('cloud.somebodyscomputer.firstmod.fetch')
    def test__save_data__fetch_failure(self, fetch, write):
        # Setup
        mod_cls = create_autospec(AnsibleModule)
        mod = mod_cls.return_value
        mod.params = dict(
            url="https://www.google.com",
            dest="/tmp/firstmod.txt"
        )

        fetch.side_effect = firstmod.FetchError

        # Exercise
        firstmod.save_data(mod)

        # Verify
        self.assertEqual(1, mod.fail_json.call_count)

        self.assertEqual(1, fetch.call_count)

        expected = call(mod.params["url"])
        self.assertEqual(expected, fetch.call_args)

        self.assertEqual(0, write.call_count)

    @patch('cloud.somebodyscomputer.firstmod.write')
    @patch('cloud.somebodyscomputer.firstmod.fetch')
    def test__save_data__write_failure(self, fetch, write):
        # Setup
        mod_cls = create_autospec(AnsibleModule)
        mod = mod_cls.return_value
        mod.params = dict(
            url="https://www.google.com",
            dest="/tmp/firstmod.txt"
        )

        write.side_effect = firstmod.WriteError

        # Exercise
        firstmod.save_data(mod)

        # Verify
        self.assertEqual(1, mod.fail_json.call_count)

        self.assertEqual(1, fetch.call_count)

        expected = call(mod.params["url"])
        self.assertEqual(expected, fetch.call_args)

        self.assertEqual(1, write.call_count)

        expected = call(fetch.return_value, mod.params["dest"])
        self.assertEqual(expected, write.call_args)

    def test__write__happy_path(self):
        # Setup
        data = "Somedata here"
        dest = "/path/to/file.txt"

        # Exercise
        o_open = "cloud.somebodyscomputer.firstmod.open"
        m_open = mock_open()
        with patch(o_open, m_open, create=True):
            firstmod.write(data, dest)

        # Verify
        expected = call(dest, "w")
        self.assertEqual(expected, m_open.mock_calls[0])

        expected = call().write(data)
        self.assertEqual(expected, m_open.mock_calls[2])

    def test__write__write_error(self):
        # Setup
        data = "Somedata here"
        dest = "/path/to/file.txt"

        o_open = "cloud.somebodyscomputer.firstmod.open"
        m_open = mock_open()
        m_open.side_effect = IOError

        # Exercise
        with self.assertRaises(firstmod.WriteError):
            with patch(o_open, m_open, create=True):
                firstmod.write(data, dest)

        # Verify
        self.assertEqual(1, m_open.call_count)

        expected = call(dest, "w")
        self.assertEqual(expected, m_open.mock_calls[0])

