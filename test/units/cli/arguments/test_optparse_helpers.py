# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

import pytest

from ansible.cli.arguments import optparse_helpers as opt_help


class TestOptparseHelpersVersion:

    def test_version(self):
        ver = opt_help.version('ansible-cli-test')
        assert 'ansible-cli-test' in ver
        assert 'python version' in ver
