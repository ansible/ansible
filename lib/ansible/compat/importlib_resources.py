# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import sys

HAS_IMPORTLIB_RESOURCES = False

if sys.version_info < (3, 10):
    try:
        from importlib_resources import files  # type: ignore[import]  # pylint: disable=unused-import
    except ImportError:
        files = None  # type: ignore[assignment]
    else:
        HAS_IMPORTLIB_RESOURCES = True
else:
    from importlib.resources import files
    HAS_IMPORTLIB_RESOURCES = True
