# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import json

import pytest


@pytest.mark.parametrize("stdin", [{}], indirect=["stdin"])
def test_get_bin_path_warning(am, capfd):
    am.get_bin_path("non_existent_cmd", warning="skipping non_existent_cmd")

    with pytest.raises(SystemExit):
        am.exit_json()
    out, dummy = capfd.readouterr()
    expected_warning = ["Unable to find non_existent_cmd, skipping non_existent_cmd"]
    assert json.loads(out)["warnings"] == expected_warning
