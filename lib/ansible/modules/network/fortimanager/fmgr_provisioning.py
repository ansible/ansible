#!/usr/bin/python
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fmgr_provisioning
version_added: "2.7"
author: Andrew Welsh (@Ghilli3)
short_description: Provision devices via FortiMananger
description:
  - Add model devices on the FortiManager using jsonrpc API and have them pre-configured,
    so when central management is configured, the configuration is pushed down to the
    registering devices

options:
  adom:
    description:
      - The administrative domain (admon) the configuration belongs to
    required: true
  vdom:
    description:
      - The virtual domain (vdom) the configuration belongs to
  host:
    description:
      - The FortiManager's Address.
    required: true
  username:
    description:
      - The username to log into the FortiManager
    required: true
  password:
    description:
      - The password associated with the username account.
    required: false

  policy_package:
    description:
      - The name of the policy package to be assigned to the device.
    required: True
  name:
    description:
      - The name of the device to be provisioned.
    required: True
  group:
    description:
      - The name of the device group the provisioned device can belong to.
    required: False
  serial:
    description:
      - The serial number of the device that will be provisioned.
    required: True
  platform:
    description:
      - The platform of the device, such as model number or VM.
    required: True
  description:
    description:
      - Description of the device to be provisioned.
    required: False
  os_version:
    description:
      - The Fortinet OS version to be used for the device, such as 5.0 or 6.0.
    required: True
  minor_release:
    description:
      - The minor release number such as 6.X.1, as X being the minor release.
    required: False
  patch_release:
    description:
      - The patch release number such as 6.0.X, as X being the patch release.
    required: False
  os_type:
    description:
      - The Fortinet OS type to be pushed to the device, such as 'FOS' for FortiOS.
    required: True
'''

EXAMPLES = '''
- name: Create FGT1 Model Device
  fmgr_provisioning:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    adom: "root"
    vdom: "root"
    policy_package: "default"
    name: "FGT1"
    group: "Ansible"
    serial: "FGVM000000117994"
    platform: "FortiGate-VM64"
    description: "Provisioned by Ansible"
    os_version: '6.0'
    minor_release: 0
    patch_release: 0
    os_type: 'fos'


- name: Create FGT2 Model Device
  fmgr_provisioning:
    host: "{{ inventory_hostname }}"
    username: "{{ username }}"
    password: "{{ password }}"
    adom: "root"
    vdom: "root"
    policy_package: "test_pp"
    name: "FGT2"
    group: "Ansible"
    serial: "FGVM000000117992"
    platform: "FortiGate-VM64"
    description: "Provisioned by Ansible"
    os_version: '5.0'
    minor_release: 6
    patch_release: 0
    os_type: 'fos'

'''

RETURN = """
api_result:
  description: full API response, includes status code and message
  returned: always
  type: str
"""

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.network.fortimanager.fortimanager import AnsibleFortiManager

# check for pyFMG lib
try:
    from pyFMG.fortimgr import FortiManager
    HAS_PYFMGR = True
except ImportError:
    HAS_PYFMGR = False


def dev_group_exists(fmg, dev_grp_name, adom):
    datagram = {
        'adom': adom,
        'name': dev_grp_name,
    }

    url = '/dvmdb/adom/{adom}/group/{dev_grp_name}'.format(adom=adom, dev_grp_name=dev_grp_name)
    response = fmg.get(url, datagram)
    return response


def prov_template_exists(fmg, prov_template, adom, vdom):
    datagram = {
        'name': prov_template,
        'adom': adom,
    }

    url = '/pm/devprof/adom/{adom}/devprof/{name}'.format(adom=adom, name=prov_template)
    response = fmg.get(url, datagram)
    return response


def create_model_device(fmg, name, serial, group, platform, os_version,
                        os_type, minor_release, patch_release=0, adom='root'):
    datagram = {
        'adom': adom,
        'flags': ['create_task', 'nonblocking'],
        'groups': [{'name': group, 'vdom': 'root'}],
        'device': {
            'mr': minor_release,
            'name': name,
            'sn': serial,
            'mgmt_mode': 'fmg',
            'device action': 'add_model',
            'platform_str': platform,
            'os_ver': os_version,
            'os_type': os_type,
            'patch': patch_release,
            'desc': 'Provisioned by Ansible',
        }
    }

    url = '/dvm/cmd/add/device'
    response = fmg.execute(url, datagram)
    return response


def update_flags(fmg, name):
    datagram = {
        'flags': ['is_model', 'linked_to_model']
    }
    url = 'dvmdb/device/{name}'.format(name=name)
    response = fmg.update(url, datagram)
    return response


def assign_provision_template(fmg, template, adom, target):
    datagram = {
        'name': template,
        'type': 'devprof',
        'description': 'Provisioned by Ansible',
        'scope member': [{'name': target}]
    }
    url = "/pm/devprof/adom/{adom}".format(adom=adom)
    response = fmg.update(url, datagram)
    return response


def set_devprof_scope(self, provisioning_template, adom, provision_targets):
    """
    GET the DevProf (check to see if exists)
    """
    fields = dict()
    targets = []
    fields["name"] = provisioning_template
    fields["type"] = "devprof"
    fields["description"] = "CreatedByAnsible"

    for target in provision_targets.strip().split(","):
        # split the host on the space to get the mask out
        new_target = {"name": target}
        targets.append(new_target)

    fields["scope member"] = targets

    body = {"method": "set", "params": [{"url": "/pm/devprof/adom/{adom}".format(adom=adom),
                                         "data": fields, "session": self.session}]}
    response = self.make_request(body).json()
    return response


def assign_dev_grp(fmg, grp_name, device_name, vdom, adom):
    datagram = {
        'name': device_name,
        'vdom': vdom,
    }
    url = "/dvmdb/adom/{adom}/group/{grp_name}/object member".format(adom=adom, grp_name=grp_name)
    response = fmg.set(url, datagram)
    return response


def update_install_target(fmg, device, pp='default', vdom='root', adom='root'):
    datagram = {
        'scope member': [{'name': device, 'vdom': vdom}],
        'type': 'pkg'
    }
    url = '/pm/pkg/adom/{adom}/{pkg_name}'.format(adom=adom, pkg_name=pp)
    response = fmg.update(url, datagram)
    return response


def install_pp(fmg, device, pp='default', vdom='root', adom='root'):
    datagram = {
        'adom': adom,
        'flags': 'nonblocking',
        'pkg': pp,
        'scope': [{'name': device, 'vdom': vdom}],
    }
    url = 'securityconsole/install/package'
    response = fmg.execute(url, datagram)
    return response


def main():

    argument_spec = dict(
        adom=dict(required=False, type="str"),
        vdom=dict(required=False, type="str"),
        host=dict(required=True, type="str"),
        password=dict(fallback=(env_fallback, ["ANSIBLE_NET_PASSWORD"]), no_log=True),
        username=dict(fallback=(env_fallback, ["ANSIBLE_NET_USERNAME"]), no_log=True),

        policy_package=dict(required=False, type="str"),
        name=dict(required=False, type="str"),
        group=dict(required=False, type="str"),
        serial=dict(required=True, type="str"),
        platform=dict(required=True, type="str"),
        description=dict(required=False, type="str"),
        os_version=dict(required=True, type="str"),
        minor_release=dict(required=False, type="str"),
        patch_release=dict(required=False, type="str"),
        os_type=dict(required=False, type="str"),

    )

    module = AnsibleModule(argument_spec, supports_check_mode=True, )

    # check if params are set
    if module.params["host"] is None or module.params["username"] is None:
        module.fail_json(msg="Host and username are required for connection")

    # check if login failed
    fmg = AnsibleFortiManager(module, module.params["host"], module.params["username"], module.params["password"])
    response = fmg.login()

    if "FortiManager instance connnected" not in str(response):
        module.fail_json(msg="Connection to FortiManager Failed")
    else:

        if module.params["policy_package"] is None:
            module.params["policy_package"] = 'default'
        if module.params["adom"] is None:
            module.params["adom"] = 'root'
        if module.params["vdom"] is None:
            module.params["vdom"] = 'root'
        if module.params["platform"] is None:
            module.params["platform"] = 'FortiGate-VM64'
        if module.params["os_type"] is None:
            module.params["os_type"] = 'fos'

        results = create_model_device(fmg,
                                      module.params["name"],
                                      module.params["serial"],
                                      module.params["group"],
                                      module.params["platform"],
                                      module.params["os_ver"],
                                      module.params["os_type"],
                                      module.params["minor_release"],
                                      module.params["patch_release"],
                                      module.params["adom"])
        if results[0] != 0:
            module.fail_json(msg="Create model failed", **results)

        results = update_flags(fmg, module.params["name"])
        if results[0] != 0:
            module.fail_json(msg="Update device flags failed", **results)

        # results = assign_dev_grp(fmg, 'Ansible', 'FGVM000000117992', 'root', 'root')
        # if not results[0] == 0:
        #     module.fail_json(msg="Setting device group failed", **results)

        results = update_install_target(fmg, module.params["name"], module.params["policy_package"])
        if results[0] != 0:
            module.fail_json(msg="Adding device target to package failed", **results)

        results = install_pp(fmg, module.params["name"], module.params["policy_package"])
        if results[0] != 0:
            module.fail_json(msg="Installing policy package failed", **results)

        fmg.logout()

        # results is returned as a tuple
        return module.exit_json(**results[1])


if __name__ == "__main__":
    main()
