#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2015, René Moser <mail@renemoser.net>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: cs_iso
short_description: Manages ISO images on Apache CloudStack based clouds.
description:
    - Register and remove ISO images.
version_added: '2.0'
author: "René Moser (@resmo)"
options:
  name:
    description:
      - Name of the ISO.
    required: true
  url:
    description:
      - URL where the ISO can be downloaded from. Required if C(state) is present.
    required: false
    default: null
  os_type:
    description:
      - Name of the OS that best represents the OS of this ISO. If the iso is bootable this parameter needs to be passed. Required if C(state) is present.
    required: false
    default: null
  is_ready:
    description:
      - This flag is used for searching existing ISOs. If set to C(true), it will only list ISO ready for deployment e.g. successfully downloaded and installed. Recommended to set it to C(false).
    required: false
    default: false
    aliases: []
  is_public:
    description:
      - Register the ISO to be publicly available to all users. Only used if C(state) is present.
    required: false
    default: false
  is_featured:
    description:
      - Register the ISO to be featured. Only used if C(state) is present.
    required: false
    default: false
  is_dynamically_scalable:
    description:
      - Register the ISO having XS/VMWare tools installed inorder to support dynamic scaling of VM cpu/memory. Only used if C(state) is present.
    required: false
    default: false
    aliases: []
  checksum:
    description:
      - The MD5 checksum value of this ISO. If set, we search by checksum instead of name.
    required: false
    default: false
  bootable:
    description:
      - Register the ISO to be bootable. Only used if C(state) is present.
    required: false
    default: true
  domain:
    description:
      - Domain the ISO is related to.
    required: false
    default: null
  account:
    description:
      - Account the ISO is related to.
    required: false
    default: null
  project:
    description:
      - Name of the project the ISO to be registered in.
    required: false
    default: null
  zone:
    description:
      - Name of the zone you wish the ISO to be registered or deleted from. If not specified, first zone found will be used.
    required: false
    default: null
  iso_filter:
    description:
      - Name of the filter used to search for the ISO.
    required: false
    default: 'self'
    choices: [ 'featured', 'self', 'selfexecutable','sharedexecutable','executable', 'community' ]
  state:
    description:
      - State of the ISO.
    required: false
    default: 'present'
    choices: [ 'present', 'absent' ]
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# Register an ISO if ISO name does not already exist.
- local_action:
    module: cs_iso
    name: Debian 7 64-bit
    url: http://mirror.switch.ch/ftp/mirror/debian-cd/current/amd64/iso-cd/debian-7.7.0-amd64-netinst.iso
    os_type: Debian GNU/Linux 7(64-bit)

# Register an ISO with given name if ISO md5 checksum does not already exist.
- local_action:
    module: cs_iso
    name: Debian 7 64-bit
    url: http://mirror.switch.ch/ftp/mirror/debian-cd/current/amd64/iso-cd/debian-7.7.0-amd64-netinst.iso
    os_type: Debian GNU/Linux 7(64-bit)
    checksum: 0b31bccccb048d20b551f70830bb7ad0

# Remove an ISO by name
- local_action:
    module: cs_iso
    name: Debian 7 64-bit
    state: absent

# Remove an ISO by checksum
- local_action:
    module: cs_iso
    name: Debian 7 64-bit
    checksum: 0b31bccccb048d20b551f70830bb7ad0
    state: absent
'''

RETURN = '''
---
id:
  description: UUID of the ISO.
  returned: success
  type: string
  sample: a6f7a5fc-43f8-11e5-a151-feff819cdc9f
name:
  description: Name of the ISO.
  returned: success
  type: string
  sample: Debian 7 64-bit
display_text:
  description: Text to be displayed of the ISO.
  returned: success
  type: string
  sample: Debian 7.7 64-bit minimal 2015-03-19
zone:
  description: Name of zone the ISO is registered in.
  returned: success
  type: string
  sample: zuerich
status:
  description: Status of the ISO.
  returned: success
  type: string
  sample: Successfully Installed
is_ready:
  description: True if the ISO is ready to be deployed from.
  returned: success
  type: boolean
  sample: true
checksum:
  description: MD5 checksum of the ISO.
  returned: success
  type: string
  sample: 0b31bccccb048d20b551f70830bb7ad0
created:
  description: Date of registering.
  returned: success
  type: string
  sample: 2015-03-29T14:57:06+0200
domain:
  description: Domain the ISO is related to.
  returned: success
  type: string
  sample: example domain
account:
  description: Account the ISO is related to.
  returned: success
  type: string
  sample: example account
project:
  description: Project the ISO is related to.
  returned: success
  type: string
  sample: example project
'''

try:
    from cs import CloudStack, CloudStackException, read_config
    has_lib_cs = True
except ImportError:
    has_lib_cs = False

# import cloudstack common
from ansible.module_utils.cloudstack import *


class AnsibleCloudStackIso(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackIso, self).__init__(module)
        self.returns = {
            'checksum': 'checksum',
            'status':   'status',
            'isready':  'is_ready',
        }
        self.iso = None

    def register_iso(self):
        iso = self.get_iso()
        if not iso:

            args                            = {}
            args['zoneid']                  = self.get_zone('id')
            args['domainid']                = self.get_domain('id')
            args['account']                 = self.get_account('name')
            args['projectid']               = self.get_project('id')
            args['bootable']                = self.module.params.get('bootable')
            args['ostypeid']                = self.get_os_type('id')
            args['name']                    = self.module.params.get('name')
            args['displaytext']             = self.module.params.get('name')
            args['checksum']                = self.module.params.get('checksum')
            args['isdynamicallyscalable']   = self.module.params.get('is_dynamically_scalable')
            args['isfeatured']              = self.module.params.get('is_featured')
            args['ispublic']                = self.module.params.get('is_public')

            if args['bootable'] and not args['ostypeid']:
                self.module.fail_json(msg="OS type 'os_type' is requried if 'bootable=true'.")

            args['url'] = self.module.params.get('url')
            if not args['url']:
                self.module.fail_json(msg="URL is requried.")

            self.result['changed'] = True
            if not self.module.check_mode:
                res = self.cs.registerIso(**args)
                iso = res['iso'][0]
        return iso


    def get_iso(self):
        if not self.iso:

            args                = {}
            args['isready']     = self.module.params.get('is_ready')
            args['isofilter']   = self.module.params.get('iso_filter')
            args['domainid']    = self.get_domain('id')
            args['account']     = self.get_account('name')
            args['projectid']   = self.get_project('id')
            args['zoneid']      = self.get_zone('id')

            # if checksum is set, we only look on that.
            checksum = self.module.params.get('checksum')
            if not checksum:
                args['name'] = self.module.params.get('name')

            isos = self.cs.listIsos(**args)
            if isos:
                if not checksum:
                    self.iso = isos['iso'][0]
                else:
                    for i in isos['iso']:
                        if i['checksum'] == checksum:
                            self.iso = i
                            break
        return self.iso


    def remove_iso(self):
        iso = self.get_iso()
        if iso:
            self.result['changed'] = True

            args                = {}
            args['id']          = iso['id']
            args['projectid']   = self.get_project('id')
            args['zoneid']      = self.get_zone('id')

            if not self.module.check_mode:
                res = self.cs.deleteIso(**args)
        return iso



def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        name = dict(required=True),
        url = dict(default=None),
        os_type = dict(default=None),
        zone = dict(default=None),
        iso_filter = dict(default='self', choices=[ 'featured', 'self', 'selfexecutable','sharedexecutable','executable', 'community' ]),
        domain = dict(default=None),
        account = dict(default=None),
        project = dict(default=None),
        checksum = dict(default=None),
        is_ready = dict(type='bool', default=False),
        bootable = dict(type='bool', default=True),
        is_featured = dict(type='bool', default=False),
        is_dynamically_scalable = dict(type='bool', default=False),
        state = dict(choices=['present', 'absent'], default='present'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    if not has_lib_cs:
        module.fail_json(msg="python library cs required: pip install cs")

    try:
        acs_iso = AnsibleCloudStackIso(module)

        state = module.params.get('state')
        if state in ['absent']:
            iso = acs_iso.remove_iso()
        else:
            iso = acs_iso.register_iso()

        result = acs_iso.get_result(iso)

    except CloudStackException as e:
        module.fail_json(msg='CloudStackException: %s' % str(e))

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
