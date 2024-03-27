# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import sys

import pytest

from ansible import constants as C
from ansible.cli.arguments import option_helpers as opt_help
from ansible import __path__ as ansible_path
from ansible.release import __version__ as ansible_version

cpath = C.DEFAULT_MODULE_PATH

FAKE_PROG = "ansible-cli-test"
VERSION_OUTPUT = opt_help.version(prog=FAKE_PROG)


@pytest.mark.parametrize(
    "must_have",
    [
        FAKE_PROG + " [core %s]" % ansible_version,
        "config file = %s" % C.CONFIG_FILE,
        "configured module search path = %s" % cpath,
        "ansible python module location = %s" % ":".join(ansible_path),
        "ansible collection location = %s" % ":".join(C.COLLECTIONS_PATHS),
        "executable location = ",
        "python version = %s" % "".join(sys.version.splitlines()),
    ],
)
def test_option_helper_version(must_have):
    assert must_have in VERSION_OUTPUT
