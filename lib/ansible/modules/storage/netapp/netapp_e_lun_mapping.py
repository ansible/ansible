#!/usr/bin/python

# (c) 2016, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: netapp_e_lun_mapping
author:
    - Kevin Hulquest (@hulquest)
    - Nathan Swartz (@ndswartz)
short_description: NetApp E-Series create, delete, or modify lun mappings
description:
     - Create, delete, or modify mappings between a volume and a targeted host/host+ group.
version_added: "2.2"
extends_documentation_fragment:
    - netapp.eseries
options:
  state:
    description:
      - Present will ensure the mapping exists, absent will remove the mapping.
    required: True
    choices: ["present", "absent"]
  target:
    description:
      - The name of host or hostgroup you wish to assign to the mapping
      - If omitted, the default hostgroup is used.
      - If the supplied I(volume_name) is associated with a different target, it will be updated to what is supplied here.
    required: False
  volume_name:
    description:
      - The name of the volume you wish to include in the mapping.
    required: True
    aliases:
        - volume
  lun:
    description:
      - This option is deprecated and will have no effect on the module's outcome
      - LUN value will be determine by the storage-system.
    version_added: 2.7
    required: no
  target_type:
    description:
      - This option is deprecated and will have no effect on the module's outcome
      - Target type is determined by the host or host group definition.
    version_added: 2.7
    required: no
'''

EXAMPLES = '''
---
    - name: Map volume1 to the host target host1
      netapp_e_lun_mapping:
        ssid: 1
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        validate_certs: no
        state: present
        target: host1
        volume: volume1
    - name: Delete the lun mapping between volume1 and host1
      netapp_e_lun_mapping:
        ssid: 1
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        validate_certs: yes
        state: absent
        target: host1
        volume: volume1
'''
RETURN = '''
msg:
    description: success of the module
    returned: always
    type: string
    sample: Lun mapping is complete
'''
import json
import logging
from pprint import pformat

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netapp import request, eseries_host_argument_spec
from ansible.module_utils._text import to_native

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}


class LunMapping(object):
    def __init__(self):
        argument_spec = eseries_host_argument_spec()
        argument_spec.update(dict(
            state=dict(required=True, choices=["present", "absent"]),
            target=dict(required=False, default=None),
            volume_name=dict(required=True, aliases=["volume"]),
            lun=dict(required=False),
            target_type=dict(required=False)))
        self.module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
        args = self.module.params

        self.state = args["state"] in ["present"]
        self.target = args["target"]
        self.volume = args["volume_name"]
        self.ssid = args["ssid"]
        self.url = args["api_url"]
        self.check_mode = self.module.check_mode
        self.creds = dict(url_username=args["api_username"],
                          url_password=args["api_password"],
                          validate_certs=args["validate_certs"])
        self.mapping_info = None

        if not self.url.endswith('/'):
            self.url += '/'

    def update_mapping_info(self):
        """Collect the current state of the storage array."""
        response = None
        try:
            rc, response = request(self.url + "storage-systems/%s/graph" % self.ssid,
                                   method="GET", headers=HEADERS, **self.creds)

        except Exception as error:
            self.module.fail_json(
                msg="Failed to retrieve storage array graph. Id [%s]. Error [%s]" % (self.ssid, to_native(error)))

        # Create dictionary containing host/cluster references mapped to their names
        target_reference = {}
        target_name = {}
        for host in response["storagePoolBundle"]["host"]:
            target_reference.update({host["hostRef"]: host["name"]})
            target_name.update({host["name"]: host["hostRef"]})
        for cluster in response["storagePoolBundle"]["cluster"]:
            target_reference.update({cluster["clusterRef"]: cluster["name"]})
            target_name.update({cluster["name"]: cluster["clusterRef"]})

        volume_reference = {}
        volume_name = {}
        lun_name = {}
        for volume in response["volume"]:
            volume_reference.update({volume["volumeRef"]: volume["name"]})
            volume_name.update({volume["name"]: volume["volumeRef"]})
            if volume["listOfMappings"]:
                lun_name.update({volume["name"]: volume["listOfMappings"][0]["lun"]})

        # Build current mapping object
        self.mapping_info = dict(lun_mapping=[dict(volume_reference=mapping["volumeRef"],
                                                   map_reference=mapping["mapRef"],
                                                   lun_mapping_reference=mapping["lunMappingRef"],
                                                   ) for mapping in response["storagePoolBundle"]["lunMapping"]],
                                 volume_by_reference=volume_reference,
                                 volume_by_name=volume_name,
                                 lun_by_name=lun_name,
                                 target_by_reference=target_reference,
                                 target_by_name=target_name)

    def get_lun_mapping(self):
        """Find the matching lun mapping reference.

        Returns: tuple(bool, int): contains volume match and volume mapping reference
        """
        target_match = False
        reference = None

        # Verify volume and target exist if needed for expected state.
        if self.state:
            if self.volume not in self.mapping_info["volume_by_name"].keys():
                self.module.fail_json(msg="Volume does not exist. Id [%s]." % self.ssid)
            if self.target and self.target not in self.mapping_info["target_by_name"].keys():
                self.module.fail_json(msg="Target does not exist. Id [%s'." % self.ssid)

        for lun_mapping in self.mapping_info["lun_mapping"]:

            # Find matching volume reference
            if lun_mapping["volume_reference"] == self.mapping_info["volume_by_name"][self.volume]:
                reference = lun_mapping["lun_mapping_reference"]

                # Determine if lun mapping is attached to target
                if (lun_mapping["map_reference"] in self.mapping_info["target_by_reference"].keys() and
                        self.mapping_info["target_by_reference"][lun_mapping["map_reference"]] == self.target):
                    target_match = True

        return target_match, reference

    def update(self):
        """Execute the changes the require changes on the storage array."""
        self.update_mapping_info()
        target_match, lun_reference = self.get_lun_mapping()
        update = (self.state and not target_match) or (not self.state and target_match)

        if update and not self.check_mode:
            try:
                if self.state:
                    body = dict()
                    target = None if not self.target else self.mapping_info["target_by_name"][self.target]
                    if target:
                        body.update(dict(targetId=target))

                    if lun_reference:
                        rc, response = request(self.url + "storage-systems/%s/volume-mappings/%s/move"
                                               % (self.ssid, lun_reference), method="POST", data=json.dumps(body),
                                               headers=HEADERS, **self.creds)
                    else:
                        body.update(dict(mappableObjectId=self.mapping_info["volume_by_name"][self.volume]))
                        rc, response = request(self.url + "storage-systems/%s/volume-mappings" % self.ssid,
                                               method="POST", data=json.dumps(body), headers=HEADERS, **self.creds)

                else:   # Remove existing lun mapping for volume and target
                    rc, response = request(self.url + "storage-systems/%s/volume-mappings/%s"
                                           % (self.ssid, lun_reference),
                                           method="DELETE", headers=HEADERS, **self.creds)
            except Exception as error:
                self.module.fail_json(
                    msg="Failed to update storage array lun mapping. Id [%s]. Error [%s]"
                        % (self.ssid, to_native(error)))

        self.module.exit_json(msg="Lun mapping is complete.", changed=update)


def main():
    lun_mapping = LunMapping()
    lun_mapping.update()


if __name__ == '__main__':
    main()
