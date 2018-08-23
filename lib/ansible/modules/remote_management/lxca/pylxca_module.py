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
version_added: "1.0"
author: Prashant Bhosale, Naval Patel
module: pylxca_module
short_description: custom module for pylxca utility
description:
  - This module returns/displays a inventory details of chassis, cmms, nodes,
    switches, fans, powersupplies, fanmuxes etc.

  - It also displays/perform config operations like manage, unmanage,
    config pattern, config profile, config targets, update firmware, update policy,
    update management server, update osimamge and os deployment.
  - Examples can found at
    for Inventory operations
    U(https://github.com/lenovo/ansible.lenovo-lxca/tree/master/roles/lenovo.lxca-inventory/tasks)
    for config operations
    U(https://github.com/lenovo/ansible.lenovo-lxca/tree/master/roles/lenovo.lxca-config/tasks)

options:
  login_user:
    description:
      The username for use in HTTP basic authentication.

    required: true

  login_password:
    description:
      The password for use in HTTP basic authentication.
    required: true

  auth_url:
    description:
      lxca https full web address
    required: true

  command_options:
    description:
      there are three types of commands inventory, config and others
    required: true
    choices:
        - chassis
        - cmms
        - nodes
        - discover
        - fans
        - fanmuxes
        - ffdc
        - jobs
        - lxcalog
        - powersupplies
        - scalablesystem
        - switches
        - tasks
        - users
        - get_configpatterns
        - get_particular_configpattern
        - import_configpatterns
        - apply_configpatterns
        - get_configstatus
        - configprofiles
        - configtargets
        - manage
        - unmanage
        - manage_status
        - unmanage_status
        - osimages
        - updaterepo
        - update_firmware
        - update_firmware_all
        - update_firmware_query_status
        - update_firmware_query_comp
        - get_managementserver_pkg
        - update_managementserver_pkg
        - import_managementserver_pkg
        - updatepolicy
        - get_storedcredentials
        - create_storedcredentials
        - update_storedcredentials
        - delete_storedcredentials
        - connect

  lxca_action:
    description:
    - action performed on lxca, Used with following commands with option for lxca_action
    - "update_firmware, update_all_firmware_withpolicy
            (apply  Applies the associated firmware to the submitted components.
            power  Perform power action on selected endpoint.
            cancelApply Cancels the firmware update request to the selected components.)"
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
    - "configprofiles
            delete - delete profile
            unassign - unassign profile"

    - "update_managementserver_pkg
            apply   - install a management-server update.
            refresh - Retrieves information (metadata) about the latest available
                   management-server updates from the Lenovo XClarity Support website.
            acquire - Downloads the specified management-server update packages from the
                      Lenovo XClarity Support website."

    - "import_managementserver_pkg
            import - import management package"


    choices:
        - None
        - apply
        - power
        - cancelApply
        - read
        - refresh
        - acquire
        - delete
        - unassign
        - import

  uuid:
    description:
      of device, this is string with length greater than 16.

  id:
    description:
      this is numeric string

  endpoint_ip:
    description:
      - Used with following command
      - "manage - ip of endpoint to be managed
             i.e 10.240.72.172"
      - "unamange - combination of ip,uuid of device and type of device
             i.e 10.240.72.172;46920C143355486F97C19A34ABC7D746;Chassis
             type have following options
                Chassis
                ThinkServer
                Storage
                Rackswitch
                Rack-Tower"

  jobid:
    description:
      Id of job, to get status of it

  user:
    description:
      credential for login to device

  password:
    description:
      for login to device

  recovery_password:
    description:
      recovery password to be set in device

  force:
    description:
        Perform force operation. set to 'True'.
  description:
    description:
      detail about storedcredential.

  storedcredential_id:
    description:
        stored credential id to be used for operation


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

  mode:
    description:
      - "used with command update_firmware, update_all_firmware_withpolicy
        Indicates when to activate the update. This can be one of the following values."
      - "immediate - Uses Immediate Activaton mode when applying firmware updates to
                               the selected endpoints."
      - "delayed - Uses Delayed Activaton mode when applying firmware updates to the
                               selected endpoints."

    choices:
      - immediate
      - delayed
      - None

  server:
    description:
      - used with command update_firmware
      - "string of format uuid,mt or uuid,fixids,mt
                fixid: lnvgy_fw_imm2_tcoo15m-2.50_anyos_noarch
                Component name
                name: IMM2 (Backup)"

      - "Example '7C5E041E3CCA11E18B715CF3FC112D8A,IMM2 (Backup)' or
                '7C5E041E3CCA11E18B715CF3FC112D8A,lnvgy_fw_imm2_tcoo15m-2.50_anyos_noarch,IMM2 (Backup)'"

  storage:
    description:
      - used with command update_firmware
      - "string of format uuid,mt or uuid,fixids,mt
                fixid: lnvgy_fw_imm2_tcoo15m-2.50_anyos_noarch
                Component name
                name: IMM2 (Backup)"

      - "Example '7C5E041E3CCA11E18B715CF3FC112D8A,IMM2 (Backup)' or
                '7C5E041E3CCA11E18B715CF3FC112D8A,lnvgy_fw_imm2_tcoo15m-2.50_anyos_noarch,IMM2 (Backup)'"

  cmm:
    description:
      - used with command update_firmware
      - "string of format uuid,mt or uuid,fixids,mt
                fixid: lnvgy_fw_imm2_tcoo15m-2.50_anyos_noarch
                Component name
                name: IMM2 (Backup)"

      - "Example '7C5E041E3CCA11E18B715CF3FC112D8A,IMM2 (Backup)' or
                '7C5E041E3CCA11E18B715CF3FC112D8A,lnvgy_fw_imm2_tcoo15m-2.50_anyos_noarch,IMM2 (Backup)'"

  switch:
    description:
      - used with command update_firmware
      - "string of format uuid,mt or uuid,fixids,mt
                fixid: lnvgy_fw_imm2_tcoo15m-2.50_anyos_noarch
                Component name
                name: IMM2 (Backup)"

      - "Example '7C5E041E3CCA11E18B715CF3FC112D8A,IMM2 (Backup)' or
                '7C5E041E3CCA11E18B715CF3FC112D8A,lnvgy_fw_imm2_tcoo15m-2.50_anyos_noarch,IMM2 (Backup)'"

  uuid_list:
    description:
      - used with command update_all_firmware_withpolicy. Apply firmware to uuid in list
      - "example ['38D9D7DBCB713C12A210E60C74A0E931','00000000000010008000542AA2D3CB00']"

  policy_info:
    description:
      - used with command updatepolicy following values are possible
      - "FIRMWARE - Get List of Applicable Frimware policies"
      - "RESULTS - List  the persisted compare result for servers to which a policy is assigned"
      - "COMPARE_RESULTS -Check compliant with the assigned compliance policy using the job or task ID
                         that was returned when the compliance policy was assigned."
      - "NAMELIST -  Returns the available compliance policies"

    choices:
      - None
      - FIRMWARE
      - RESULTS
      - COMPARE_RESULTS
      - NAMELIST

  policy_name:
    description:
        used with command updatepolicy, name of policy to be applied

  policy_type:
    description:
      - used with command updatepolicy, policy applied to value specified it can have following value
      - CMM - Chassis Management Module
      - IOSwitch - Flex switch
      - RACKSWITCH - RackSwitch switch
      - STORAGE - Lenovo Storage system
      - SERVER - Compute node or rack server
    choices:
      - CMM
      - IOSwitch
      - RACKSWITCH
      - STORAGE
      - SERVER
      - None
  update_list:
    description:
      - used with command task to update task status this is used with action=update
      - example
        [{'jobUID':'9','percentage':50},{'jobUID':'8','percentage':50}]"

  machine_type:
    description:
      - used with command updaterepo
      - its string with value like '7903'

  fixids:
    description:
      - used with command updaterepo , get_particular_managementserver_pkg and update_managementserver_pkg
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
      - used with command updaterepo,   When lxca_action=delete or lxca_action=export is specified, this parameter
        is used. You can specify one of the following values
      - all - Deletes selected update-package files (payload, change history, readme, and metadata files)
      - payloads - Deletes only the selected payload image files
    choices:
      - None
      - all
      - payloads

  endpoint:
    description:
      - used with command configprofiles, apply_configpatterns and get_configstatus,
      - its uuid of deivce for node, rack, tower
      - endpointdid for flex

  restart:
    description:
      - used with command configprofiles and apply_configpatterns
      - when to activate the configurations. This can be one of the following values
      - defer - Activate IMM settings but do not restart the server.
      - immediate - Activate all settings and restart the server immediately
      - pending - Manually activate the server profile and restart the server. this can be used
                       with apply_configpatterns only.
    choices:
      - None
      - defer
      - immediate
      - pending

  type:
    description:
      - used with apply_configpatterns valid values are
    choices:
      - None
      - node
      - rack
      - tower
      - flex

  powerdown:
    description:
      used with command configprofiles to power down server

  resetimm:
    description:
      used with command configprofiles to reset imm

  pattern_update_dict:
    description:
      used with command import_configpatterns to import pattern specified in this variable as dict.

  includeSettings:
    description:
      used with command get_configpatterns to get detailed settings of configpattern set this to 'True'

  config_pattern_name:
    description:
      name of config pattern

  config_profile_name:
    description:
      name of config profile

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

  osimages_info:
    description:
      - Used with osimage it can have following values
      - globalSettings - Setting global values used in os deployment
      - hostPlatforms - Used for deploying os images
      - remoteFileServers - Used for remote ftp, http server operations
    choices:
      - globalSettings
      - hostPlatforms
      - remoteFileServers
      - None

  osimages_dict:
    type:
      dict
    description:
      Used with osimage it is used for setting osimage and os deployment parameters.

  unittest:
    description:
      - Used with unittest. set to "True" when invokved from unittest

requirements:
  - pylxca
'''

EXAMPLES = '''
# Following links have example tasks using this module
# for Inventory operations
# U(https://github.com/lenovo/ansible.lenovo-lxca/tree/master/roles/lenovo.lxca-inventory/tasks)

# for config operations
# U(https://github.com/lenovo/ansible.lenovo-lxca/tree/master/roles/lenovo.lxca-config/tasks)
# get cmms info
- name: get cmms data from LXCA
  pylxca_module:
    command_options: cmms
    login_userr: USERID
    login_password: CME44ibm
    auth_url: "https://10.243.15.168"
'''

try:
    from pylxca import chassis
    from pylxca import cmms
    from pylxca import nodes
    from pylxca import discover
    from pylxca import fans
    from pylxca import fanmuxes
    from pylxca import ffdc
    from pylxca import jobs
    from pylxca import lxcalog
    from pylxca import powersupplies
    from pylxca import scalablesystem
    from pylxca import switches
    from pylxca import tasks
    from pylxca import users
    from pylxca import configpatterns
    from pylxca import configprofiles
    from pylxca import configtargets
    from pylxca import manage
    from pylxca import unmanage
    from pylxca import osimages
    from pylxca import updaterepo
    from pylxca import updatecomp
    from pylxca import managementserver
    from pylxca import updatepolicy
    from pylxca import storedcredentials
    from pylxca import connect
    HAS_PYLXCA = True
except Exception:
    HAS_PYLXCA = False

from ansible.module_utils.basic import AnsibleModule


__ip_map__ = dict()
__changed__ = False


def find_conn_obj(kwargs):
    """
    Find connection object in map and return if its already there for url
    :param kwargs: uses url from this dict
    :return: connection if already exist.
    """
    global __ip_map__

    if __ip_map__.get(kwargs.get('url')) is not None:
        return __ip_map__.get(kwargs.get('url'))
    return None


def _get_connect_lxca(module, kwargs):
    global __ip_map__

    _conn_lxca = None

    try:
        _conn_lxca = find_conn_obj(kwargs)
        if _conn_lxca is None:
            _conn_lxca = connect(kwargs.get('auth_url'), kwargs.get(
                'login_user'), kwargs.get('login_password'), "True")
        __ip_map__.update({kwargs.get('auth_url'): _conn_lxca})
        if _conn_lxca is None:
            module.fail_json(msg="Error connecting with: %s" %
                             kwargs.get('auth_url'))
    except Exception:
        module.fail_json(
            msg="Error authenticating with provided credentials: %s" % kwargs.get('auth_url'))
    return _conn_lxca


def _get_chassis_inventory(module, kwargs):
    result = None
    try:
        result = chassis(_get_connect_lxca(module, kwargs))
    except Exception as err:
        module.fail_json(msg="Error getting chassis inventory" + str(err))
    return result


def _get_cmms_inventory(module, kwargs):
    result = None
    try:
        result = cmms(_get_connect_lxca(module, kwargs), kwargs.get('uuid'))
    except Exception as err:
        module.fail_json(msg="Error getting cmms inventory" + str(err))
    return result


def _get_configstatus(module, kwargs):
    result = None
    try:
        result = configpatterns(_get_connect_lxca(module, kwargs), endpoint=kwargs.get(
            'endpoint'), status=kwargs.get('status'))
        if 'items' in result and len(result['items']) and result['items'][0]:
            result = result['items'][0]
    except Exception as err:
        module.fail_json(msg="Error in configstatus " + str(err))
    return result


def _get_configpatterns(module, kwargs):
    result = None
    try:
        result = configpatterns(_get_connect_lxca(module, kwargs))
    except Exception as err:
        module.fail_json(msg="Error in configpatterns " + str(err))
    return result


def _get_particular_configpattern(module, kwargs):
    result = None
    try:
        pattern_dict = {}
        pattern_dict['id'] = kwargs.get('id')
        pattern_dict['includeSettings'] = kwargs.get('includeSettings')
        result = configpatterns(_get_connect_lxca(
            module, kwargs), **pattern_dict)
    except Exception as err:
        module.fail_json(
            msg="Error in getting particular configpattern " + str(err))
    return result


def _apply_configpatterns(module, kwargs):
    global __changed__
    result = None
    try:
        pattern_dict = {}
        pattern_dict['id'] = kwargs.get('id')
        pattern_dict['name'] = kwargs.get('config_pattern_name')
        pattern_dict['endpoint'] = kwargs.get('endpoint')
        pattern_dict['restart'] = kwargs.get('restart')
        pattern_dict['type'] = kwargs.get('type')
        result = configpatterns(_get_connect_lxca(module, kwargs),
                                **pattern_dict)
        __changed__ = True
    except Exception as err:
        module.fail_json(msg="Error in applying configpatterns" + str(err))
    return result


def _import_configpatterns(module, kwargs):
    global __changed__
    result = None
    try:
        pattern_dict = {}
        pattern_dict['pattern_update_dict'] = kwargs.get('pattern_update_dict')
        result = configpatterns(_get_connect_lxca(module, kwargs),
                                **pattern_dict)
        __changed__ = True
    except Exception as err:
        module.fail_json(msg="Error in import configpatterns" + str(err))
    return result


def _get_configprofiles(module, kwargs):
    global __changed__
    result = None
    delete_profile = None
    unassign_profile = None
    try:
        action = kwargs.get("lxca_action")
        if action:
            if action.lower() in ['delete']:
                delete_profile = 'True'
                __changed__ = True
            elif action.lower() in ['unassign']:
                unassign_profile = 'True'
                __changed__ = True
        result = configprofiles(_get_connect_lxca(module, kwargs),
                                kwargs.get('id'),
                                kwargs.get('config_profile_name'),
                                kwargs.get('endpoint'),
                                kwargs.get('restart'),
                                delete_profile,
                                unassign_profile,
                                kwargs.get('powerdown'),
                                kwargs.get('resetimm'),
                                kwargs.get('force'),)
# kwargs.get('delete_profile'), kwargs.get('unassign') )
    except Exception as err:
        module.fail_json(msg="Error getting configprofiles" + str(err))
    return result


def _get_configtargets(module, kwargs):
    result = None
    try:
        result = configtargets(_get_connect_lxca(
            module, kwargs), kwargs.get('id'))
    except Exception as err:
        module.fail_json(msg="Error getting configtargets" + str(err))
    return result


def _get_discover(module, kwargs):
    result = None
    try:
        result = discover(_get_connect_lxca(module, kwargs),
                          kwargs.get('discovery_ip'))
    except Exception as err:
        module.fail_json(msg="Error discovery " + str(err))
    return result


def _get_fans(module, kwargs):
    result = None
    try:
        result = fans(_get_connect_lxca(module, kwargs), kwargs.get('uuid'))
    except Exception as err:
        module.fail_json(msg="Error getting fans inventory " + str(err))
    return result


def _get_fanmuxes(module, kwargs):
    result = None
    try:
        result = fanmuxes(_get_connect_lxca(
            module, kwargs), kwargs.get('uuid'))
    except Exception as err:
        module.fail_json(msg="Error getting fanmuxes inventory " + str(err))
    return result


def _get_ffdc(module, kwargs):
    result = None
    try:
        result = ffdc(_get_connect_lxca(module, kwargs), kwargs.get('uuid'))
    except Exception as err:
        module.fail_json(msg="Error getting ffdc inventory " + str(err))
    return result


def _get_jobs(module, kwargs):
    result = None
    try:
        result = jobs(_get_connect_lxca(module, kwargs), kwargs.get('id'))
    except Exception as err:
        module.fail_json(msg="Error getting jobs inventory " + str(err))
    return result


def _get_lxcalog(module, kwargs):
    result = None
    try:
        result = lxcalog(_get_connect_lxca(module, kwargs))
    except Exception as err:
        module.fail_json(msg="Error getting lxcalog " + str(err))
    return result


def _manage_endpoint(module, kwargs):
    global __changed__
    result = None

    try:
        result = manage(_get_connect_lxca(module, kwargs), kwargs.get('endpoint_ip'),
                        kwargs.get('user'), kwargs.get('password'),
                        kwargs.get('recovery_password'), None, kwargs.get(
                            'force'),
                        kwargs.get('storedcredential_id'))
        __changed__ = True
    except Exception as err:
        module.fail_json(msg=" Fail to manage the endpoint" + str(err))
    return result


def _manage_status(module, kwargs):
    result = None
    try:
        result = manage(_get_connect_lxca(module, kwargs), None,
                        None, None, None, kwargs.get('jobid'))
    except Exception as err:
        module.fail_json(msg="Error getting info abt jobid" + str(err))
    return result


def _unmanage_endpoint(module, kwargs):
    global __changed__
    result = None

    try:
        result = unmanage(_get_connect_lxca(module, kwargs), kwargs.get(
            'endpoint_ip'), kwargs.get('force'), None)
        __changed__ = True
    except Exception as err:
        module.fail_json(msg=" Fail to unmanage the endpoint" + str(err))
    return result


def _unmanage_status(module, kwargs):
    result = None
    try:
        result = unmanage(_get_connect_lxca(module, kwargs),
                          None, None, kwargs.get('jobid'))
    except Exception as err:
        module.fail_json(msg="Error getting info abt jobid" + str(err))
    return result


def _get_nodes(module, kwargs):
    result = None
    try:
        result = nodes(_get_connect_lxca(module, kwargs), kwargs.get('uuid'))
    except Exception as err:
        module.fail_json(msg="Error getting nodes inventory " + str(err))
    return result


def _get_powersupplies(module, kwargs):
    result = None
    try:
        result = powersupplies(_get_connect_lxca(
            module, kwargs), kwargs.get('uuid'))
    except Exception as err:
        module.fail_json(msg="Error getting powersupplies inventory " + str(err))
    return result


def _get_scalablesystem(module, kwargs):
    result = None
    try:
        result = scalablesystem(_get_connect_lxca(
            module, kwargs), kwargs.get('id'))
    except Exception as err:
        module.fail_json(
            msg="Error getting scalablesystem inventory " + str(err))
    return result


def _get_switches_inventory(module, kwargs):
    result = None
    try:
        result = switches(_get_connect_lxca(
            module, kwargs), kwargs.get('uuid'))
    except Exception as err:
        module.fail_json(msg="Error getting switches " + str(err))
    return result


def _get_tasks(module, kwargs):
    global __changed__
    result = None
    tasks_dict = {}
    job_uid = kwargs.get("id")
    action = kwargs.get("lxca_action")
    if action in ['cancel', 'delete']:
        tasks_dict['jobUID'] = job_uid
        tasks_dict['action'] = action
        __changed__ = True
    elif action in ['update']:
        tasks_dict['action'] = action
        update_list = kwargs.get("update_list")
        tasks_dict['updateList'] = update_list
        __changed__ = True
    else:
        tasks_dict['jobUID'] = job_uid
    try:
        result = tasks(_get_connect_lxca(module, kwargs), **tasks_dict)
    except Exception as err:
        module.fail_json(msg="Error getting tasks " + str(err))
    return result


def _get_updaterepo_info(module, kwargs):
    result = None
    try:
        result = updaterepo(_get_connect_lxca(module, kwargs),
                            kwargs.get('repo_key'),
                            kwargs.get('lxca_action'),
                            kwargs.get('machine_type'),
                            kwargs.get('scope'),
                            kwargs.get('fixids'),
                            kwargs.get('file_type'))
    except Exception as err:
        module.fail_json(msg="Error retriving firmware info." + str(err))
    return result


def _update_firmware(module, kwargs):
    global __changed__
    result = None
    try:
        result = updatecomp(_get_connect_lxca(module, kwargs), mode=kwargs.get('mode'),
                            action=kwargs.get('lxca_action'), cmm=kwargs.get('cmm'),
                            switch=kwargs.get('switch'), server=kwargs.get('server'),
                            storage=kwargs.get('storage'))
        __changed__ = True
    except Exception as err:
        module.fail_json(msg="Error updating firmware " + str(err))
    return result


def _transform_devicelist(devicelist, uuid_list):
    ret_device_list = []
    for dev in devicelist:
        new_dict = {}
        for dev_type in dev.keys():  # SwitchList
            new_list = []
            for sw_dev in dev[dev_type]:
                if not sw_dev['UUID'] in uuid_list:
                    continue
                cm_list = []
                for cm_dev in sw_dev['Components']:
                    cm_list.append({'Component': cm_dev})
                sw_dev['Components'] = cm_list
                new_list.append(sw_dev)
            if len(new_list) > 0:
                new_dict[dev_type] = new_list
        if len(new_dict) > 0:
            ret_device_list.append(new_dict)
    return ret_device_list


def _valid_compliance_policies(policy_list):
    uuid_list = []
    for comp_policy in policy_list:
        if 'uuid' in comp_policy.keys():
            if 'currentPolicy' in comp_policy.keys() and len(comp_policy['currentPolicy']) > 0:
                uuid_list.append(comp_policy['uuid'])

    return uuid_list


def _update_firmware_all(module, kwargs):
    global __changed__
    result = None
    try:
        rep = updatepolicy(_get_connect_lxca(module, kwargs), info="NAMELIST")
        uuid_list = _valid_compliance_policies(rep['policies'])
        if len(uuid_list) == 0:
            module.fail_json(msg="No policy assigned to any device")
            return result

        dev_uuid_list = []
        if 'uuid_list' in kwargs:
            dev_uuid_list = kwargs.get('uuid_list')
            if len(dev_uuid_list) > 0:
                # getting common uuid of two list
                uuid_list = list(set(dev_uuid_list).intersection(uuid_list))

        rep = updatecomp(_get_connect_lxca(module, kwargs), query='components')
        ret_dev_list = rep['DeviceList']
        mod_dev_list = _transform_devicelist(ret_dev_list, uuid_list)
        if len(mod_dev_list) == 0:
            module.fail_json(
                msg="No updateable component with assigned policy found")
            return result

        result = updatecomp(_get_connect_lxca(module, kwargs), mode=kwargs.get(
            'mode'), action=kwargs.get('lxca_action'), dev_list=mod_dev_list)
        __changed__ = True
    except Exception as err:
        module.fail_json(msg="Error updating all device firmware " + str(err))
    return result


def _update_firmware_query_status(module, kwargs):
    result = None
    try:
        result = updatecomp(_get_connect_lxca(module, kwargs), query='status')
    except Exception as err:
        module.fail_json(msg="Error updating firmware " + str(err))
    return result


def _update_firmware_query_comp(module, kwargs):
    result = None
    try:
        result = updatecomp(_get_connect_lxca(
            module, kwargs), query='components')
    except Exception as err:
        module.fail_json(msg="Error updating firmware " + str(err))
    return result


def _get_managementserver_pkg(module, kwargs):
    result = None
    try:
        result = managementserver(_get_connect_lxca(module, kwargs),
                                  kwargs.get('update_key'),
                                  kwargs.get('fixids'),
                                  kwargs.get('type'))
    except Exception as err:
        module.fail_json(msg="Error retriving managementserver info." + str(err))
    return result


def _update_managementserver_pkg(module, kwargs):
    global __changed__
    result = None
    try:
        result = managementserver(_get_connect_lxca(module, kwargs),
                                  kwargs.get('update_key'),
                                  kwargs.get('fixids'),
                                  kwargs.get('type'),
                                  kwargs.get('lxca_action'),)
        __changed__ = True
    except Exception as err:
        module.fail_json(
            msg="Error retriving update managementserver." + str(err))
    return result


def _import_managementserver_pkg(module, kwargs):
    global __changed__
    result = None
    try:
        result = managementserver(_get_connect_lxca(module, kwargs),
                                  kwargs.get('update_key'),
                                  kwargs.get('fixids'),
                                  kwargs.get('type'),
                                  kwargs.get('lxca_action'),
                                  kwargs.get('files'),
                                  kwargs.get('jobid'))
        __changed__ = True
    except Exception as err:
        module.fail_json(msg="Error import managementserver ." + str(err))
    return result


def _get_updatepolicy(module, kwargs):
    result = None
    try:
        result = updatepolicy(_get_connect_lxca(module, kwargs),
                              kwargs.get('policy_info'),
                              kwargs.get('jobid'),
                              kwargs.get('uuid'),
                              kwargs.get('policy_name'),
                              kwargs.get('policy_type'))
    except Exception as err:
        module.fail_json(msg="Error getting updatepolicy " + str(err))
    return result


def _get_osimages(module, kwargs):
    result = None
    try:
        osimages_info = kwargs.get('osimages_info')
        osimages_dict = kwargs.get('osimages_dict')
        if osimages_info and osimages_dict:
            result = osimages(_get_connect_lxca(module, kwargs),
                              osimages_info,
                              **osimages_dict)
        elif osimages_dict:
            result = osimages(_get_connect_lxca(module, kwargs),
                              **osimages_dict)

        elif osimages_info:
            result = osimages(_get_connect_lxca(module, kwargs),
                              osimages_info)
        else:
            result = osimages(_get_connect_lxca(module, kwargs))

    except Exception as err:
        module.fail_json(msg="Error processing osimages " + str(err))
    return result


def _get_users(module, kwargs):
    result = None
    try:
        result = users(_get_connect_lxca(module, kwargs), kwargs.get('id'))
    except Exception as err:
        module.fail_json(msg="Error getting users " + str(err))
    return result


def _get_storedcredentials(module, kwargs):
    result = None
    try:
        result = storedcredentials(_get_connect_lxca(
            module, kwargs), kwargs.get('storedcredential_id'))
    except Exception as err:
        module.fail_json(msg="Error getting stored credential " + str(err))
    return result


def _create_storedcredentials(module, kwargs):
    global __changed__
    result = None
    try:
        result = storedcredentials(_get_connect_lxca(module, kwargs),
                                   user_name=kwargs.get('user'),
                                   password=kwargs.get('password'),
                                   description=kwargs.get('description'),)
        __changed__ = True
    except Exception as err:
        module.fail_json(msg="Error create stored credential " + str(err))
    return result


def _update_storedcredentials(module, kwargs):
    global __changed__
    result = None
    try:
        result = storedcredentials(_get_connect_lxca(module, kwargs),
                                   id=kwargs.get('storedcredential_id'),
                                   user_name=kwargs.get('user'),
                                   password=kwargs.get('password'),
                                   description=kwargs.get('description'),)
        __changed__ = True
    except Exception as err:
        module.fail_json(msg="Error getting stored credential " + str(err))
    return result


def _delete_storedcredentials(module, kwargs):
    global __changed__
    result = None
    try:
        result = storedcredentials(_get_connect_lxca(module, kwargs),
                                   delete_id=kwargs.get('storedcredential_id'))
        __changed__ = True
    except Exception as err:
        module.fail_json(msg="Error getting stored credential " + str(err))
    return result


FUNC_DICT = {
    'connect': _get_connect_lxca,
    'chassis': _get_chassis_inventory,
    'cmms': _get_cmms_inventory,
    'get_configpatterns': _get_configpatterns,
    'get_particular_configpattern': _get_particular_configpattern,
    'import_configpatterns': _import_configpatterns,
    'apply_configpatterns': _apply_configpatterns,
    'get_configstatus': _get_configstatus,
    'configprofiles': _get_configprofiles,
    'configtargets': _get_configtargets,
    'discover': _get_discover,
    'fans': _get_fans,
    'fanmuxes': _get_fanmuxes,
    'ffdc': _get_ffdc,
    'jobs': _get_jobs,
    'lxcalog': _get_lxcalog,
    'manage': _manage_endpoint,
    'unmanage': _unmanage_endpoint,
    'manage_status': _manage_status,
    'unmanage_status': _unmanage_status,
    'nodes': _get_nodes,
    'osimages': _get_osimages,
    'powersupplies': _get_powersupplies,
    'scalablesystem': _get_scalablesystem,
    'switches': _get_switches_inventory,
    'tasks': _get_tasks,
    'updaterepo': _get_updaterepo_info,
    'update_firmware': _update_firmware,
    'update_firmware_all': _update_firmware_all,
    'update_firmware_query_status': _update_firmware_query_status,
    'update_firmware_query_comp': _update_firmware_query_comp,
    'get_managementserver_pkg': _get_managementserver_pkg,
    'update_managementserver_pkg': _update_managementserver_pkg,
    'import_managementserver_pkg': _import_managementserver_pkg,
    'updatepolicy': _get_updatepolicy,
    'users': _get_users,
    'get_storedcredentials': _get_storedcredentials,
    'create_storedcredentials': _create_storedcredentials,
    'update_storedcredentials': _update_storedcredentials,
    'delete_storedcredentials': _delete_storedcredentials

}


# ===========================================
# Main
#

def main():
    """
    Main entry point for this module
    :return:
    """
    module = AnsibleModule(
        argument_spec=dict(
            login_user=dict(default=None, required=False),
            login_password=dict(default=None, required=False, no_log=True),
            command_options=dict(choices=list(FUNC_DICT)),
            lxca_action=dict(default=None,
                             choices=['apply', 'power', 'cancelApply', 'read',
                                      'refresh', 'acquire', 'delete', 'unassign',
                                      'import', None]),
            auth_url=dict(default=None),
            uuid=dict(default=None),
            id=dict(default=None),
            endpoint_ip=dict(default=None),
            jobid=dict(default=None),
            user=dict(default=None, required=False),
            password=dict(default=None, required=False, no_log=True),
            force=dict(default=None),
            description=dict(default=None),
            recovery_password=dict(default=None, no_log=True),
            repo_key=dict(default=None,
                          choices=[None, 'supportedMts', 'size', 'lastRefreshed',
                                   'importDir', 'publicKeys', 'updates',
                                   'updatesByMt', 'updatesByMtByComp']),
            mode=dict(default=None, choices=[None, 'immediate', 'delayed']),
            server=dict(default=None),
            storage=dict(default=None),
            switch=dict(default=None),
            cmm=dict(default=None),
            policy_info=dict(default=None,
                             choices=[None, 'FIRMWARE', 'RESULTS', 'COMPARE_RESULTS',
                                      'NAMELIST']),
            policy_name=dict(default=None),
            policy_type=dict(default=None,
                             choices=['CMM', 'IOSwitch', 'RACKSWITCH', 'STORAGE', 'SERVER', None]),
            update_list=dict(default=None, type=('list')),
            machine_type=dict(default=None),
            fixids=dict(default=None),
            scope=dict(default=None, choices=['all', 'latest', 'payloads', None]),
            file_type=dict(default=None, choices=[None, 'all', 'payloads']),
            endpoint=dict(default=None),
            restart=dict(default=None, choices=[None, 'defer', 'immediate', 'pending']),
            type=dict(default=None, choices=[None, 'node', 'rack', 'tower', 'flex']),
            config_pattern_name=dict(default=None),
            config_profile_name=dict(default=None),
            powerdown=dict(default=None),
            resetimm=dict(default=None),
            pattern_update_dict=dict(default=None, type=('dict')),
            includeSettings=dict(default=None),
            osimages_info=dict(default=None,
                               choices=[None, 'globalSettings', 'hostPlatforms',
                                        'remoteFileServers']),
            osimages_dict=dict(default=None, type=('dict')),
            update_key=dict(default=None,
                            choices=['all', 'currentVersion', 'history', 'importDir',
                                     'size', 'updates', 'updatedDate', None]),
            files=dict(default=None),
            unittest=dict(default=None),
            uuid_list=dict(default=None, type=('list')),
            storedcredential_id=dict(default=None)
        ),
        check_invalid_arguments=False,
        supports_check_mode=False,
    )

    if not HAS_PYLXCA:
        module.fail_json(changed=False, msg="Install pylxca")

    rslt = None
    command_options = module.params['command_options']

    rslt = FUNC_DICT[command_options](module, module.params)
    if module.params['unittest']:
        return rslt

    if command_options == "connect":
        if rslt:
            module.exit_json(changed=False, msg="Success %s result" %
                             command_options, result="Connected successfully")
    if not rslt:
        module.fail_json(changed=False, msg="Fail to get %s result" %
                         command_options, result=rslt)
    else:
        module.exit_json(changed=__changed__, msg="Success %s result" %
                         command_options, result=rslt)
    return rslt


if __name__ == '__main__':
    main()
