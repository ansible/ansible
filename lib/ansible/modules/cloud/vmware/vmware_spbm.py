#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: vmware_spbm
short_description: VMware Storage Profile Utilities
description:
    - Create, Destroy VM Storage Profiles
version_added: 2.3
author:
    - Prasanna Nanda <pnanda@cloudsimple.com>
notes:
    - Tested on vSphere 6.5
requirements:
    - "python >= 2.7"
    - PyVmomi
options:
    name:
        description:
            - Name of the storage profile to Create
        reequired: True
    state:
        description:
            - Valid values are present or absent
        required: True
    description:
        description:
            - Some Text Describing the Storage profile
        required: False
extends_documentation_fragment: vmware.documentation
'''

EXAPMPLES = '''
# Create Storage Profile
  - name: Create a Storage Profile
    vmware_spbm:
      hostname: A vCenter host
      username: vCenter username
      password: vCenter password
      name: Name of the storage profile to create
      description: Text Describing Storage Profile
      state: present|absent
'''
try:
    from pyVmomi import vim, pbm, vmodl
    from pyVim.connect import SoapStubAdapter
    from pyVim.connect import SmartConnect, Disconnect
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

from ansible.module_utils.vmware import *
from ansible.module_utils.basic import *
from  ansible.module_utils.SPBMClient import SPBMClient

class vmware_spbm(object):
    def __init__(self,module):
        self.module  = module
        self.name    = module.params['name']
        self.description = module.params['description']
        self.desiredstate   = module.params['state']
        self.rules = module.params['rules']
        self.currentstate = 'absent'
        try:
            context = None
            context = ssl._create_unverified_context()
            si = SmartConnect(host=module.params['hostname'],
                              user=module.params['username'],
                              pwd=module.params['password'],
                              port=443,
                              sslContext=context)
            atexit.register(Disconnect, si)
            self.spbmclient = SPBMClient(vc_si=si,hostname=module.params['hostname'])
        except vmodl.RuntimeFault as runtime_fault:
            module.fail_json(msg=runtime_fault.msg)
        except vmodl.MethodFault as method_fault:
            module.fail_json(msg=method_fault.msg)
        except Exception as e:
            module.fail_json(msg=str(e))
        atexit.register(Disconnect, si)


    def process_state(self):
        profiles = self.spbmclient.get_profiles()
        if not profiles:
            self.module.fail_json(changed=False,msg="Could not retreive Storage Profile Information from vCenter")
        else:
            for profile in profiles:
                if self.module.params['name'] == profile.name:
                    self.currentstate = 'present'
        # Current State of System and Desired State are same
        if self.currentstate == self.desiredstate:
            self.module.exit_json(changed=False)

        # Profile is absent and you need to create one
        if self.currentstate == 'absent' and self.desiredstate == 'present':
            profileId = self.spbmclient.create_storage_profile(profile_name=self.name, description=self.description,rules=self.rules)
            if profileId:
                self.module.exit_json(changed=True,msg="Created Storage Profile {} and ID {}".format(self.name,profileId.uniqueId))
            else:
                self.module.fail_json(changed=False,msg="Failed to Create Storage Profile {}".format(self.name))

        # Profile is Present and you need to delete one
        if self.currentstate == 'present' and self.desiredstate == 'absent':
            results = self.spbmclient.delete_storage_profile(profile_name=self.name)
            if len(results) == 0:
                self.module.exit_json(changed=True,msg="Deleted Storage Profile {}".format(self.name))
            else:
                profile_op_outcome = results[0]
                if profile_op_outcome.fault is not None:
                    self.module.fail_json(changed=False,msg=str(profile_op_outcome.fault))

def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(name=dict(required=True, type='str'),
                         description=dict(required=False, type='str', default='Sample Storage Profile'),
                         rules=dict(required=False, type='list', default=[{'stripeWidth': 1}]),
                         state=dict(default='present', choices=['present', 'absent'], type='str')))
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    if not HAS_PYVMOMI:
        module.fail_json(msg=HAS_PYVMOMI)
    spbm = vmware_spbm(module)
    spbm.process_state()
    #module.exit_json(changed=True)

if __name__ == '__main__':
    main()
