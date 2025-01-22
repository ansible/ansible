# -*- coding: utf-8 -*-
# Copyright:
#   (c) 2023 Ansible Project
# License: GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from unittest.mock import MagicMock, patch
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args
from ansible.modules import uri


class TestUri(ModuleTestCase):

    def test_main_no_args(self):
        """Module must fail if called with no args."""
        with self.assertRaises(AnsibleFailJson):
            set_module_args({})
            uri.main()

    def test_main_no_force(self):
        """The "force" parameter to fetch_url() must be absent or false when the module is called without "force"."""
        set_module_args({"url": "http://example.com/"})
        resp = MagicMock()
        resp.headers.get_content_type.return_value = "text/html"
        info = {"url": "http://example.com/", "status": 200}
        with patch.object(uri, "fetch_url", return_value=(resp, info)) as fetch_url:
            with self.assertRaises(AnsibleExitJson):
                uri.main()
            fetch_url.assert_called_once()
            assert not fetch_url.call_args[1].get("force")

    def test_main_force(self):
        """The "force" parameter to fetch_url() must be true when the module is called with "force"."""
        set_module_args({"url": "http://example.com/", "force": True})
        resp = MagicMock()
        resp.headers.get_content_type.return_value = "text/html"
        info = {"url": "http://example.com/", "status": 200}
        with patch.object(uri, "fetch_url", return_value=(resp, info)) as fetch_url:
            with self.assertRaises(AnsibleExitJson):
                uri.main()
            fetch_url.assert_called_once()
            assert fetch_url.call_args[1].get("force")
