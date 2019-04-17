#!/usr/bin/python
# Copyright: (c) 2018, Hewlett Packard Enterprise Development LP
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
short_description: Manage HPE StoreServ 3PAR CPG
author:
  - Farhan Nomani (@farhan7500)
  - Gautham P Hegde (@gautamphegde)
description:
  - Create and delete CPG on HPE 3PAR.
module: ss_3par_cpg
options:
  cpg_name:
    description:
      - Name of the CPG.
    type: str
    required: true
  disk_type:
    choices:
      - FC
      - NL
      - SSD
    description:
      - Specifies that physical disks must have the specified device type.
    type: str
  domain:
    description:
      - Specifies the name of the domain in which the object will reside.
    type: str
  growth_increment:
    description:
      - Specifies the growth increment(in MiB, GiB or TiB) the amount of logical disk storage
       created on each auto-grow operation.
    type: str
  growth_limit:
    description:
      - Specifies that the autogrow operation is limited to the specified
       storage amount that sets the growth limit(in MiB, GiB or TiB).
    type: str
  growth_warning:
    description:
      - Specifies that the threshold(in MiB, GiB or TiB) of used logical disk space when exceeded
       results in a warning alert.
    type: str
  high_availability:
    choices:
      - PORT
      - CAGE
      - MAG
    description:
      - Specifies that the layout must support the failure of one port pair,
       one cage, or one magazine.
    type: str
  raid_type:
    choices:
      - R0
      - R1
      - R5
      - R6
    description:
      - Specifies the RAID type for the logical disk.
    type: str
  set_size:
    description:
      - Specifies the set size in the number of chunklets.
    type: int
  state:
    choices:
      - present
      - absent
    description:
      - Whether the specified CPG should exist or not.
    required: true
    type: str
  secure:
    description:
      - Specifies whether the certificate needs to be validated while communicating.
    type: bool
    default: no
extends_documentation_fragment: hpe3par
version_added: '2.8'
'''


EXAMPLES = r'''
    - name: Create CPG sample_cpg
      ss_3par_cpg:
        storage_system_ip: 10.10.10.1
        storage_system_username: username
        storage_system_password: password
        state: present
        cpg_name: sample_cpg
        domain: sample_domain
        growth_increment: 32000 MiB
        growth_limit: 64000 MiB
        growth_warning: 48000 MiB
        raid_type: R6
        set_size: 8
        high_availability: MAG
        disk_type: FC
        secure: no

    - name: Delete CPG sample_cpg
      ss_3par_cpg:
        storage_system_ip: 10.10.10.1
        storage_system_username: username
        storage_system_password: password
        state: absent
        cpg_name: sample_cpg
        secure: no
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.storage.hpe3par import hpe3par
try:
    from hpe3par_sdk import client
    from hpe3parclient import exceptions
    HAS_3PARCLIENT = True
except ImportError:
    HAS_3PARCLIENT = False


def validate_set_size(raid_type, set_size):
    if raid_type:
        set_size_array = client.HPE3ParClient.RAID_MAP[raid_type]['set_sizes']
        if set_size in set_size_array:
            return True
    return False


def cpg_ldlayout_map(ldlayout_dict):
    if ldlayout_dict['RAIDType'] is not None and ldlayout_dict['RAIDType']:
        ldlayout_dict['RAIDType'] = client.HPE3ParClient.RAID_MAP[
            ldlayout_dict['RAIDType']]['raid_value']
    if ldlayout_dict['HA'] is not None and ldlayout_dict['HA']:
        ldlayout_dict['HA'] = getattr(
            client.HPE3ParClient, ldlayout_dict['HA'])
    return ldlayout_dict


def create_cpg(
        client_obj,
        cpg_name,
        domain,
        growth_increment,
        growth_limit,
        growth_warning,
        raid_type,
        set_size,
        high_availability,
        disk_type):
    try:
        if not validate_set_size(raid_type, set_size):
            return (False, False, "Set size %s not part of RAID set %s" % (set_size, raid_type))
        if not client_obj.cpgExists(cpg_name):
            ld_layout = dict()
            disk_patterns = []
            if disk_type:
                disk_type = getattr(client.HPE3ParClient, disk_type)
                disk_patterns = [{'diskType': disk_type}]
            ld_layout = {
                'RAIDType': raid_type,
                'setSize': set_size,
                'HA': high_availability,
                'diskPatterns': disk_patterns}
            ld_layout = cpg_ldlayout_map(ld_layout)
            if growth_increment is not None:
                growth_increment = hpe3par.convert_to_binary_multiple(
                    growth_increment)
            if growth_limit is not None:
                growth_limit = hpe3par.convert_to_binary_multiple(
                    growth_limit)
            if growth_warning is not None:
                growth_warning = hpe3par.convert_to_binary_multiple(
                    growth_warning)
            optional = {
                'domain': domain,
                'growthIncrementMiB': growth_increment,
                'growthLimitMiB': growth_limit,
                'usedLDWarningAlertMiB': growth_warning,
                'LDLayout': ld_layout}
            client_obj.createCPG(cpg_name, optional)
        else:
            return (True, False, "CPG already present")
    except exceptions.ClientException as e:
        return (False, False, "CPG creation failed | %s" % (e))
    return (True, True, "Created CPG %s successfully." % cpg_name)


def delete_cpg(
        client_obj,
        cpg_name):
    try:
        if client_obj.cpgExists(cpg_name):
            client_obj.deleteCPG(cpg_name)
        else:
            return (True, False, "CPG does not exist")
    except exceptions.ClientException as e:
        return (False, False, "CPG delete failed | %s" % e)
    return (True, True, "Deleted CPG %s successfully." % cpg_name)


def main():
    module = AnsibleModule(argument_spec=hpe3par.cpg_argument_spec(),
                           required_together=[['raid_type', 'set_size']])
    if not HAS_3PARCLIENT:
        module.fail_json(msg='the python hpe3par_sdk library is required (https://pypi.org/project/hpe3par_sdk)')

    if len(module.params["cpg_name"]) < 1 or len(module.params["cpg_name"]) > 31:
        module.fail_json(msg="CPG name must be at least 1 character and not more than 31 characters")

    storage_system_ip = module.params["storage_system_ip"]
    storage_system_username = module.params["storage_system_username"]
    storage_system_password = module.params["storage_system_password"]
    cpg_name = module.params["cpg_name"]
    domain = module.params["domain"]
    growth_increment = module.params["growth_increment"]
    growth_limit = module.params["growth_limit"]
    growth_warning = module.params["growth_warning"]
    raid_type = module.params["raid_type"]
    set_size = module.params["set_size"]
    high_availability = module.params["high_availability"]
    disk_type = module.params["disk_type"]
    secure = module.params["secure"]

    wsapi_url = 'https://%s:8080/api/v1' % storage_system_ip
    try:
        client_obj = client.HPE3ParClient(wsapi_url, secure)
    except exceptions.SSLCertFailed:
        module.fail_json(msg="SSL Certificate Failed")
    except exceptions.ConnectionError:
        module.fail_json(msg="Connection Error")
    except exceptions.UnsupportedVersion:
        module.fail_json(msg="Unsupported WSAPI version")
    except Exception as e:
        module.fail_json(msg="Initializing client failed. %s" % e)

    if storage_system_username is None or storage_system_password is None:
        module.fail_json(msg="Storage system username or password is None")
    if cpg_name is None:
        module.fail_json(msg="CPG Name is None")

    # States
    if module.params["state"] == "present":
        try:
            client_obj.login(storage_system_username, storage_system_password)
            return_status, changed, msg = create_cpg(
                client_obj,
                cpg_name,
                domain,
                growth_increment,
                growth_limit,
                growth_warning,
                raid_type,
                set_size,
                high_availability,
                disk_type
            )
        except Exception as e:
            module.fail_json(msg="CPG create failed | %s" % e)
        finally:
            client_obj.logout()

    elif module.params["state"] == "absent":
        try:
            client_obj.login(storage_system_username, storage_system_password)
            return_status, changed, msg = delete_cpg(
                client_obj,
                cpg_name
            )
        except Exception as e:
            module.fail_json(msg="CPG create failed | %s" % e)
        finally:
            client_obj.logout()

    if return_status:
        module.exit_json(changed=changed, msg=msg)
    else:
        module.fail_json(msg=msg)


if __name__ == '__main__':
    main()
