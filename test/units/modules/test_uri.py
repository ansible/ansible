# -*- coding: utf-8 -*-
# Copyright:
#   (c) 2023 Ansible Project
# License: GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ansible.module_utils.testing import patch_module_args
from ansible.modules import uri


class TestUri:

    def test_main_no_args(self):
        """Module must fail if called with no args."""
        with pytest.raises(SystemExit), \
             patch_module_args():
            uri.main()

    def test_main_no_force(self, mocker):
        """The "force" parameter to fetch_url() must be absent or false when the module is called without "force"."""
        resp = MagicMock()
        resp.headers.get_content_type.return_value = "text/html"
        info = {"url": "http://example.com/", "status": 200}
        with patch.object(uri, "fetch_url", return_value=(resp, info)) as fetch_url, \
             patch_module_args({"url": "http://example.com/"}):
            with pytest.raises(SystemExit):
                uri.main()
            fetch_url.assert_called_once()
            assert not fetch_url.call_args[1].get("force")

    def test_main_force(self):
        """The "force" parameter to fetch_url() must be true when the module is called with "force"."""
        resp = MagicMock()
        resp.headers.get_content_type.return_value = "text/html"
        info = {"url": "http://example.com/", "status": 200}
        with patch.object(uri, "fetch_url", return_value=(resp, info)) as fetch_url, \
             patch_module_args({"url": "http://example.com/", "force": True}):
            with pytest.raises(SystemExit):
                uri.main()
            fetch_url.assert_called_once()
            assert fetch_url.call_args[1].get("force")
