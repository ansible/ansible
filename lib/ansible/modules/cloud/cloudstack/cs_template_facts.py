#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2018, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_template_facts
short_description: Gathering facts of templates on Apache CloudStack based clouds.
description:
  - Gathering facts of templates.
version_added: "2.6"
author: "René Moser (@resmo)"
options:
  name:
    description:
      - Name of the template.
    required: true
  domain:
    description:
      - Domain the template is related to.
  account:
    description:
      - Account the template is related to.
  project:
    description:
      - Name of the project the template to be registered in.
  zone:
    description:
      - Name of the zone the template is registered in.
  template_filter:
    description:
      - Name of the filter used to search for the template.
    default: self
    choices: [ all, featured, self, selfexecutable, sharedexecutable, executable, community ]
  cross_zones:
    description:
      - Whether the template should be synced or removed across zones.
      - Only used if C(state) is present or absent.
    default: no
    type: bool
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: Gather facts of a template
  local_action:
    module: cs_template_facts
    name: systemvm-vmware-4.5

- name: Wait until a template becomes ready
  local_action:
    module: cs_template_facts
    name: systemvm-vmware-{{ cloudstrack_major_version }}
  register: template
  until: template.is_ready
  retries: 400

'''

RETURN = '''
---
id:
  description: UUID of the template.
  returned: success
  type: string
  sample: a6f7a5fc-43f8-11e5-a151-feff819cdc9f
name:
  description: Name of the template.
  returned: success
  type: string
  sample: Debian 7 64-bit
display_text:
  description: Display text of the template.
  returned: success
  type: string
  sample: Debian 7.7 64-bit minimal 2015-03-19
checksum:
  description: MD5 checksum of the template.
  returned: success
  type: string
  sample: 0b31bccccb048d20b551f70830bb7ad0
status:
  description: Status of the template.
  returned: success
  type: string
  sample: Download Complete
is_ready:
  description: True if the template is ready to be deployed from.
  returned: success
  type: boolean
  sample: true
is_public:
  description: True if the template is public.
  returned: success
  type: boolean
  sample: true
is_featured:
  description: True if the template is featured.
  returned: success
  type: boolean
  sample: true
is_extractable:
  description: True if the template is extractable.
  returned: success
  type: boolean
  sample: true
format:
  description: Format of the template.
  returned: success
  type: string
  sample: OVA
os_type:
  description: Typo of the OS.
  returned: success
  type: string
  sample: CentOS 6.5 (64-bit)
password_enabled:
  description: True if the reset password feature is enabled, false otherwise.
  returned: success
  type: boolean
  sample: false
sshkey_enabled:
  description: true if template is sshkey enabled, false otherwise.
  returned: success
  type: boolean
  sample: false
cross_zones:
  description: true if the template is managed across all zones, false otherwise.
  returned: success
  type: boolean
  sample: false
template_type:
  description: Type of the template.
  returned: success
  type: string
  sample: USER
created:
  description: Date of registering.
  returned: success
  type: string
  sample: 2015-03-29T14:57:06+0200
template_tag:
  description: Template tag related to this template.
  returned: success
  type: string
  sample: special
hypervisor:
  description: Hypervisor related to this template.
  returned: success
  type: string
  sample: VMware
mode:
  description: Mode of extraction
  returned: success
  type: string
  sample: http_download
state:
  description: State of the extracted template
  returned: success
  type: string
  sample: DOWNLOAD_URL_CREATED
url:
  description: Url to which the template is extracted to
  returned: success
  type: string
  sample: "http://1.2.3.4/userdata/eb307f13-4aca-45e8-b157-a414a14e6b04.ova"
tags:
  description: List of resource tags associated with the template.
  returned: success
  type: dict
  sample: '[ { "key": "foo", "value": "bar" } ]'
zone:
  description: Name of zone the template is registered in.
  returned: success
  type: string
  sample: zuerich
domain:
  description: Domain the template is related to.
  returned: success
  type: string
  sample: example domain
account:
  description: Account the template is related to.
  returned: success
  type: string
  sample: example account
project:
  description: Name of project the template is related to.
  returned: success
  type: string
  sample: Production
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together,
)


class AnsibleCloudStackTemplateFacts(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackTemplateFacts, self).__init__(module)
        self.returns = {
            'checksum': 'checksum',
            'status': 'status',
            'isready': 'is_ready',
            'templatetag': 'template_tag',
            'sshkeyenabled': 'sshkey_enabled',
            'passwordenabled': 'password_enabled',
            'tempaltetype': 'template_type',
            'ostypename': 'os_type',
            'crossZones': 'cross_zones',
            'isextractable': 'is_extractable',
            'isfeatured': 'is_featured',
            'ispublic': 'is_public',
            'format': 'format',
            'hypervisor': 'hypervisor',
            'url': 'url',
            'extractMode': 'mode',
            'state': 'state',
        }

    def get_template(self):
        args = {
            'name': self.module.params.get('name'),
            'templatefilter': self.module.params.get('template_filter'),
            'domainid': self.get_domain(key='id'),
            'account': self.get_account(key='name'),
            'projectid': self.get_project(key='id')
        }

        cross_zones = self.module.params.get('cross_zones')
        if not cross_zones:
            args['zoneid'] = self.get_zone(key='id')

        template_found = None

        templates = self.query_api('listTemplates', **args)
        if templates:
            checksum = self.module.params.get('checksum')
            display_text = self.module.params.get('display_text')

            for tmpl in templates['template']:
                if tmpl['crossZones'] != cross_zones:
                    continue

                if checksum and 'checksum' in tmpl and tmpl['checksum'] != checksum:
                    continue

                if display_text and not tmpl['displaytext'].startswith(display_text):
                    continue

                if not template_found:
                    template_found = tmpl

                # A cross zones template has one entry per zone but the same id
                elif tmpl['id'] == template_found['id']:
                    continue

                else:
                    self.fail_json(msg="Multiple templates found matching provided params. Please specifiy more precisely.")

        return template_found

    def get_facts(self):
        template = self.get_template()
        if not template:
            self.module.fail_json(msg="Template not found: %s" % self.module.params.get('name'))
        return self.get_result(template)


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        display_text=dict(),
        template_filter=dict(default='self', choices=['all', 'featured', 'self', 'selfexecutable', 'sharedexecutable', 'executable', 'community']),
        cross_zones=dict(type='bool', default=False),
        zone=dict(),
        domain=dict(),
        account=dict(),
        project=dict(),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    acs_template_facts = AnsibleCloudStackTemplateFacts(module)
    template_facts = acs_template_facts.get_facts()
    module.exit_json(**template_facts)


if __name__ == '__main__':
    main()
