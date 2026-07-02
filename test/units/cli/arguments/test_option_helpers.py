# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import sys

import pytest
import pytest_mock

from ansible import constants as C
from ansible.cli.arguments import option_helpers as opt_help
from ansible.cli.arguments.option_helpers import version
from ansible import __path__ as ansible_path
from ansible.release import __version__ as ansible_version

cpath = C.DEFAULT_MODULE_PATH

FAKE_PROG = u'ansible-cli-test'
VERSION_OUTPUT = opt_help.version(prog=FAKE_PROG)


@pytest.mark.parametrize(
    'must_have', [
        FAKE_PROG + u' [core %s]' % ansible_version,
        u'config file = %s' % C.CONFIG_FILE,
        u'configured module search path = %s' % cpath,
        u'ansible python module location = %s' % ':'.join(ansible_path),
        u'ansible collection location = %s' % ':'.join(C.COLLECTIONS_PATHS),
        u'executable location = ',
        u'python version = %s' % ''.join(sys.version.splitlines()),
    ]
)
def test_option_helper_version(must_have):
    assert must_have in VERSION_OUTPUT


def test_libyaml_version_known(mocker: pytest_mock.MockerFixture) -> None:
    import yaml._yaml
    mocker.patch.object(yaml._yaml, 'get_version_string', return_value='1.2.3')
    result = version()
    assert 'with libyaml v1.2.3' in result


def test_libyaml_version_unknown(mocker: pytest_mock.MockerFixture) -> None:
    import yaml._yaml
    mocker.patch.object(yaml._yaml, 'get_version_string', side_effect=NotImplementedError)
    result = version()
    assert 'with libyaml, version unknown' in result
