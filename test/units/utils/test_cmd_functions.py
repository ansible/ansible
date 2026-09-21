# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import shlex
import sys

from unittest import mock

from ansible.utils import cmd_functions

# child that writes to both streams and exits non-zero
_PROG = f'{shlex.quote(sys.executable)} -c "import sys; sys.stdout.write(\'out\'); sys.stderr.write(\'err\'); sys.exit(3)"'


def test_run_cmd_captures_output_and_rc():
    assert cmd_functions.run_cmd(_PROG) == (3, b'out', b'err')


def test_run_cmd_live_is_deprecated():
    with mock.patch.object(cmd_functions, 'display') as display:
        assert cmd_functions.run_cmd(_PROG, live=True) == (3, b'out', b'err')

    display.deprecated.assert_called_once()
