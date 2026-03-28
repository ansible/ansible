# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible import constants as C
from ansible.utils.display import Display

display = Display()

NOPES = frozenset(['$', '@', ':', '\\', '/', ';', '%', '(', ')', '"', "'", '`', '{{', '}}'])
REQUIRED_UNIQUE = frozenset(['pid', 'timestamp'])
REQUIRED_NAME = frozenset(['basename', 'stripname'])


def get_validated_backup_file_name_template(tmplt: str) -> str:

    bad = set()
    for required in REQUIRED_NAME:
        if required in tmplt:
            break
    else:
        bad.add("Required name variable (basename or stripname) not found in backup file template")

    for required in REQUIRED_UNIQUE:
        if required in tmplt:
            break
    else:
        bad.add("Required uniqueness variable (pid or timestamp) not found in backup file template")

    failed = set()
    for nope in NOPES:
        if nope in tmplt:
            failed.add(nope)
    if failed:
        bad.add(f"Invalid character(s) {','.join(failed)} found in backup file template")

    if bad:
        for bad_thing in bad:
            display.warning(bad_thing)
        display.warning("Invalid custom backup file name template, using default.")
        tmplt = C.config.get_configuration_definition('BACKUP_FILE_NAME_TEMPLATE')['default']

    return tmplt
