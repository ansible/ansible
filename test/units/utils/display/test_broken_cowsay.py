# -*- coding: utf-8 -*-
# Copyright (c) 2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


from ansible.utils.display import Display
from mock import MagicMock


def test_display_with_fake_cowsay_binary(capsys, mocker):
    mocker.patch("ansible.constants.ANSIBLE_COW_PATH", "./cowsay.sh")

    def mock_communicate(input=None, timeout=None):
        return b"", b""

    mock_popen = MagicMock()
    mock_popen.return_value.communicate = mock_communicate
    mock_popen.return_value.returncode = 1
    mocker.patch("subprocess.Popen", mock_popen)

    display = Display()
    assert not hasattr(display, "cows_available")
    assert display.b_cowsay is None
