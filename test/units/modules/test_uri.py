# -*- coding: utf-8 -*-
# Copyright:
#   (c) 2023 Ansible Project
# License: GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import json

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

    def test_utf8_bom_handling(self, capsys):
        """Test that UTF-8 BOM is properly handled in response content.

        The uri module should strip the UTF-8 BOM (Byte Order Mark) from
        response content before parsing JSON to prevent parsing errors.
        """
        # UTF-8 BOM bytes (EF BB BF) followed by valid JSON
        bom_content = b'\xef\xbb\xbf{"name": "dollarsign"}'
        expected_json = {"name": "dollarsign"}

        # Mock the HTTP response with BOM content
        resp = MagicMock()
        # Set up headers mock with proper content type and charset
        headers_mock = MagicMock()
        headers_mock.get_content_type.return_value = "application/json"

        # Create a more specific mock for the charset parameter
        def get_param_mock(param=None):
            """Return charset parameter when requested, mimicking HTTP header behavior.

            The uri module uses this method to extract charset information from headers.
            """
            if param == "charset":
                return "utf-8"
            return None

        headers_mock.get_param = get_param_mock
        resp.headers = headers_mock

        resp.read.return_value = bom_content
        # The fp and closed attributes are required to properly simulate an HTTP response object
        # as the uri module checks for these properties during processing
        resp.fp = MagicMock()
        resp.closed = False

        # Mock successful HTTP response info
        info = {"url": "http://example.com/", "status": 200}

        module_args = {"url": "http://example.com/", "return_content": True}

        with patch.object(uri, "fetch_url", return_value=(resp, info)) as mock_fetch_url, \
             patch_module_args(module_args):

            # Module should exit normally after processing
            with pytest.raises(SystemExit):
                uri.main()

            mock_fetch_url.assert_called_once()

            # Capture and verify the module output
            captured = capsys.readouterr()

            # Parse the JSON output from the module
            try:
                output = json.loads(captured.out)
            except json.JSONDecodeError as e:
                pytest.fail(f"Module output is not valid JSON: {e}")

            # These assertions verify two critical aspects of BOM handling:
            # 1. The JSON was successfully parsed (BOM was properly stripped)
            # 2. The content matches what we expect after BOM removal
            assert "json" in output, "Module output should contain 'json' key"
            assert output["json"] == expected_json, (
                f"Expected {expected_json}, but got {output['json']}"
            )
