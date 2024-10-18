# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.utils.display import Display

display = Display()

NOPES = frozenset(['$', '@', ':', '\\', '/', ';', '%', '{', '(', '}', ')', '"', "'", '`'])
REQUIRED_UNIQUE = frozenset(['pid', 'timestamp'])
REQUIRED_NAME = frozenset(['basename', 'stripname'])


def get_validated_backup_file_name_template(tmplt: str) -> str:

    try:
        for required in REQUIRED_NAME:
            if required in tmplt:
                break
        else:
            raise AnsibleError("Required name variable (basename or stripname) not")

        for required in REQUIRED_UNIQUE:
            if required in tmplt:
                break
        else:
            raise AnsibleError("Required uniquness variable (pid or timestamp) not")

        for nope in NOPES:
            if nope in tmplt:
                raise AnsibleError(f"Invalid character ' {nope} '")

    except AnsibleError as e:
        display.warning(f"{e} found in backup file name template, falling back to default.")
        tmplt = C.config.get_configuration_definition('BACKUP_FILE_NAME_TEMPLATE')['default']

    return tmplt
