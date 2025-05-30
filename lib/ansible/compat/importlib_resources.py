# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.utils.display import Display as _Display

from importlib.resources import files  # pylint: disable=unused-import

HAS_IMPORTLIB_RESOURCES = True

_Display().deprecated(
    msg="The `ansible.compat.importlib_resources` module is deprecated.",
    help_text="Use `importlib.resources` from the Python standard library instead.",
    version="2.23",
)
