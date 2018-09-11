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
module: lxca_managementserver
short_description: Custom module for lxca managementserver config utility
description:
  - This module update management server repository on LXCA

options:

  update_key:
    description:
      - Used with managementserver commands following are valid options
        Returns the specified type of update. This can be one of the following values.
      - C(all) - Returns all information. This is the default value.
      - C(currentVersion) - Returns the current version of Lenovo XClarity Administrator.
      - C(history)  Returns the history of management-server updates.
      - C(importDir) Returns the directory for the management-server updates repository.
      - C(size) - Returns the repository size (in bytes).
      - C(updates) - Returns information about all updates packages.
      - C(updatedDate) - Returns the date when the last update was performed.

    choices:
      - None
      - all
      - currentVersion
      - history
      - importDir
      - size
      - updates
      - updatedDate

  files:
    description:
      - Used with managementserver commands to import files to LXCA file can be specified as comma separated string
      - example
      - '/home/naval/updates/updates/lnvgy_sw_lxca_thinksystemrepo1-1.3.2_anyos_noarch.txt,
         /home/naval/updates/updates/lnvgy_sw_lxca_thinksystemrepo1-1.3.2_anyos_noarch.chg,
         /home/naval/updates/updates/lnvgy_sw_lxca_thinksystemrepo1-1.3.2_anyos_noarch.xml'


  lxca_action:
    description:
    - action performed on lxca, Used with following commands with option for lxca_action
    - "update_managementserver_pkg
            apply   - install a management-server update.
            refresh - Retrieves information (metadata) about the latest available
                   management-server updates from the Lenovo XClarity Support website.
            acquire - Downloads the specified management-server update packages from the
                      Lenovo XClarity Support website.
            delete  - Use the DELETE method to delete update packages.
            import  - import fixids files"
    choices:
      - None
      - apply
      - refresh
      - acquire
      - delete
      - import

  fixids:
    description:
      - its string with value like 'lnvgy_sw_lxca-fw-repository-pack_1-1.0.1_anyos_noarch'

  type:
    description:
      - changeHistory. Returns the change-history file for the specified management-server update
      - readme. Returns the readme file for the specified management-server update
    choices:
      - None
      - changeHistory
      - readme

  jobid:
    description:
      Id of job, to get status of it


  command_options:
    description:
      options to perform managementserver operation
    default: managementserver
    choices:
        - managementserver
        - get_managementserver_pkg
        - update_managementserver_pkg
        - import_managementserver_pkg

extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = r'''
# Query managementserver
- name: get managementserver details from LXCA
  lxca_managementserver:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    update_key: filetypes
    type: changeHistory
    fixids: lnvgy_sw_lxca-fw-repository-pack_1-1.0.1_anyos_noarch
    command_options: get_managementserver_pkg

# update managementserver
- name: update management server
  lxca_managementserver:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    lxca_action: refresh
    command_options: update_managementserver_pkg

# update managementserver download fixids
- name: update management server
  lxca_managementserver:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    lxca_action: acquire
    fixids: ibm_fw_imm2_1aoo78j-6.20_anyos_noarch
    command_options: update_managementserver_pkg

# update managementserver delete fixids
- name: update management server
  lxca_managementserver:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    lxca_action: delete
    fixids: ibm_fw_imm2_1aoo78j-6.20_anyos_noarch
    command_options: update_managementserver_pkg

# import files to managementserver
- name: import management server
  lxca_managementserver:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    lxca_action: import
    files: /home/naval/updates/updates/lnvgy_sw_lxca_thinksystemrepo1-1.3.2_anyos_noarch.xml
    command_options: import_managementserver_pkg

'''

import traceback
from ansible.module_utils.basic import AnsibleModule
try:
    from pylxca import connect
    from pylxca import disconnect
    from pylxca import managementserver
    HAS_PYLXCA = True
except Exception:
    HAS_PYLXCA = False


__changed__ = False
SUCCESS_MSG = "Success %s result"
PYLXCA_REQUIRED = 'Lenovo xClarity Administrator Python Client pylxca is required for this module.'


def has_pylxca(module):
    """
    Check pylxca is installed
    :param module:
    """
    if not HAS_PYLXCA:
        module.fail_json(msg=PYLXCA_REQUIRED)


def _get_managementserver_pkg(module, lxca_con):
    result = managementserver(lxca_con,
                              module.params['update_key'],
                              module.params['fixids'],
                              module.params['type'])
    return result


def _update_managementserver_pkg(module, lxca_con):
    global __changed__
    result = managementserver(lxca_con,
                              module.params['update_key'],
                              module.params['fixids'],
                              module.params['type'],
                              module.params['lxca_action'],)
    __changed__ = True
    return result


def _import_managementserver_pkg(module, lxca_con):
    global __changed__
    result = managementserver(lxca_con,
                              module.params['update_key'],
                              module.params['fixids'],
                              module.params['type'],
                              module.params['lxca_action'],
                              module.params['files'],
                              module.params['jobid'],)
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
    'managementserver': _get_managementserver_pkg,
    'get_managementserver_pkg': _get_managementserver_pkg,
    'update_managementserver_pkg': _update_managementserver_pkg,
    'import_managementserver_pkg': _import_managementserver_pkg,
}


LXCA_COMMON_ARGS = dict(
    login_user=dict(required=True),
    login_password=dict(required=True, no_log=True),
    auth_url=dict(required=True),
    noverify=dict(default=True)
)


INPUT_ARG_SPEC = dict(
    command_options=dict(default='managementserver',
                         choices=['managementserver',
                                  'get_managementserver_pkg',
                                  'update_managementserver_pkg',
                                  'import_managementserver_pkg']),
    update_key=dict(default=None,
                    choices=['all', 'currentVersion', 'history', 'importDir',
                             'size', 'updates', 'updatedDate', None]),
    files=dict(default=None),
    lxca_action=dict(default=None, choices=['apply', 'refresh', 'acquire',
                                            'delete', 'import', None]),
    type=dict(default=None, choices=['changeHistory', 'readme', None]),
    fixids=dict(default=None),
    jobid=dict(default=None),
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
