#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'supported_by': 'community',
    'status': ['preview']
}


DOCUMENTATION = '''
---
version_added: "1.1"
author:
  - Naval Patel (@navalkp)
  - Prashant Bhosale (@prabhosa)
module: lxca_updaterepo
short_description: Custom module for lxca updaterepo config utility
description:
  - This module update repository on LXCA

options:

  repo_key:
    description:
      - used with updaterepo command following values are used.
      - "supportedMts - Returns a list of supported machine types"
      - "size - Returns the repository size"
      - "lastRefreshed - Returns the timestamp of the last repository refresh"
      - "importDir - Returns the import directory for the repository."
      - "publicKeys - Returns the supported signed keys"
      - "updates - Returns information about all firmware updates"
      - "updatesByMt - Returns information about firmware updates for the specified
                       machine type"
      - "updatesByMtByComp - Returns the update component names for the specified
                       machine type"
    choices:
      - None
      - supportedMts
      - size
      - lastRefreshed
      - importDir
      - publicKeys
      - updates
      - updatesByMt
      - updatesByMtByComp


  lxca_action:
    description:
    - action performed on lxca, Used with following commands with option for lxca_action
    - "updaterepo
            read - Reloads the repository files. The clears the update information in cache and
                          reads the update file again from the repository.
            refresh - Retrieves information about the latest available firmware updates from
                        the Lenovo Support website, and stores the information to
                        the firmware-updates repository.
            acquire - Downloads the specified firmware updates from Lenovo Support website,
                       and stores the updates to the firmware-updates repository.
            delete - Deletes the specified firmware updates from the firmware-updates
                      repository."
    choices:
      - None
      - read
      - refresh
      - acquire
      - delete

  machine_type:
    description:
      - used with command updaterepo
      - its string with value like '7903'

  fixids:
    description:
      - its string with value like 'lnvgy_sw_lxca-fw-repository-pack_1-1.0.1_anyos_noarch'

  scope:
    description:
      - used with command updaterepo, following are possible values
      - all - When lxca_action=refresh is specified, this parameter returns information about all versions of all
                firmware updates that are available for all supported devices.
      - latest - When lxca_action=refresh is specified, this parameter returns information about the most current
               version of all firmware updates for all supported devices.
      - payloads - When lxca_action=acquire is specified, this parameter returns information about specific
                firmware updates.
    choices:
      - all
      - latest
      - payloads
      - None

  file_type:
    description:
      - used with command updaterepo,   When lxca_action=delete is specified, this parameter
        is used. You can specify one of the following values
      - all - Deletes selected update-package files (payload, change history, readme, and metadata files)
      - payloads - Deletes only the selected payload image files
    choices:
      - None
      - all
      - payloads

  command_options:
    description:
      options to perform updaterepo operation
    default: updaterepo
    choices:
        - updaterepo

extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = r'''
# Query updaterepo from LXCA
- name: get all updaterepo from LXCA
  lxca_updaterepo:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    repo_key: size
    command_options: updaterepo

# Reload repository file updaterepo
- name: reload repository file
  lxca_updaterepo:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    lxca_action: read
    command_options: updaterepo

# Retrieves information about the latest available firmware updates
- name: Refresh repository from lenovo site
  lxca_updaterepo:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    lxca_action: read
    machine_type: 7903
    command_options: updaterepo

# Downloads the specified firmware updates
- name: dwonload firmware updates from lenovo site to LXCA
  lxca_updaterepo:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    lxca_action: acquire
    machine_type: 7903
    scope: payloads
    fixids: ibm_fw_imm2_1aoo78j-6.20_anyos_noarch
    command_options: updaterepo

# delete repository file
- name: delete config profile with id
  lxca_updaterepo:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    lxca_action: delete
    machine_type: 7903
    file_type: payloads
    fixids: ibm_fw_imm2_1aoo78j-6.20_anyos_noarch
    command_options: updaterepo


'''

import traceback
from ansible.module_utils.basic import AnsibleModule
try:
    from pylxca import connect
    from pylxca import disconnect
    from pylxca import updaterepo
    HAS_PYLXCA = True
except Exception:
    HAS_PYLXCA = False


SUCCESS_MSG = "Success %s result"
__changed__ = False
PYLXCA_REQUIRED = 'Lenovo xClarity Administrator Python Client pylxca is required for this module.'


def has_pylxca(module):
    """
    Check pylxca is installed
    :param module:
    """
    if not HAS_PYLXCA:
        module.fail_json(msg=PYLXCA_REQUIRED)


def _get_updaterepo(module, lxca_con):
    global __changed__
    result = updaterepo(lxca_con,
                        module.params['repo_key'],
                        module.params['lxca_action'],
                        module.params['machine_type'],
                        module.params['scope'],
                        module.params['fixids'],
                        module.params['file_type'],)
    if module.params['lxca_action']:
        __changed__ = True
    return result


def setup_module_object():
    """
    this function merge argument spec and create ansible module object
    :return:
    """
    args_spec = dict(LXCA_COMMON_ARGS)
    args_spec.update(INPUT_ARG_SPEC)
    module = AnsibleModule(argument_spec=args_spec, supports_check_mode=False)

    return module


def setup_conn(module):
    """
    this function create connection to LXCA
    :param module:
    :return:  lxca connection
    """
    lxca_con = None
    try:
        lxca_con = connect(module.params['auth_url'],
                           module.params['login_user'],
                           module.params['login_password'],
                           module.params['noverify'], )
    except Exception as exception:
        error_msg = '; '.join((e) for e in exception.args)
        module.fail_json(msg=error_msg, exception=traceback.format_exc())
    return lxca_con


def validate_parameters(module):
    """
    validate parameters mostly it will be place holder
    :param module:
    """
    pass


FUNC_DICT = {
    'updaterepo': _get_updaterepo,
}


LXCA_COMMON_ARGS = dict(
    login_user=dict(required=True),
    login_password=dict(required=True, no_log=True),
    auth_url=dict(required=True),
    noverify=dict(default=True)
)


INPUT_ARG_SPEC = dict(
    command_options=dict(default='updaterepo', choices=list(FUNC_DICT)),
    repo_key=dict(default=None,
                  choices=[None, 'supportedMts', 'size', 'lastRefreshed',
                           'importDir', 'publicKeys', 'updates',
                           'updatesByMt', 'updatesByMtByComp']),
    lxca_action=dict(default=None, choices=['read', 'refresh', 'acquire', 'delete', None]),
    machine_type=dict(default=None),
    fixids=dict(default=None),
    scope=dict(default=None, choices=['all', 'latest', 'payloads', None]),
    file_type=dict(default=None, choices=[None, 'all', 'payloads']),
)


def execute_module(module, lxca_con):
    """
    This function invoke commands
    :param module: Ansible module object
    :param lxca_con:  lxca connection object
    """
    try:
        result = FUNC_DICT[module.params['command_options']](module, lxca_con)
        disconnect(lxca_con)
        module.exit_json(changed=__changed__,
                         msg=SUCCESS_MSG % module.params['command_options'],
                         result=result)
    except Exception as exception:
        error_msg = '; '.join((e) for e in exception.args)
        disconnect(lxca_con)
        module.fail_json(msg=error_msg, exception=traceback.format_exc())


def run_tasks(module, lxca_con):
    """

    :param module: Ansible module object
    :param lxca_con:  lxca connection object
    """
    execute_module(module, lxca_con)


def main():
    module = setup_module_object()
    has_pylxca(module)
    validate_parameters(module)
    lxca_con = setup_conn(module)
    run_tasks(module, lxca_con)


if __name__ == '__main__':
    main()
