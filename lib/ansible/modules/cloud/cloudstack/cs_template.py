#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2015, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_template
short_description: Manages templates on Apache CloudStack based clouds.
description:
  - Register templates from an URL.
  - Create templates from a ROOT volume of a stopped VM or its snapshot.
  - Update (since version 2.7), extract and delete templates.
version_added: '2.0'
author: René Moser (@resmo)
options:
  name:
    description:
      - Name of the template.
    type: str
    required: true
  url:
    description:
      - URL of where the template is hosted on I(state=present).
      - URL to which the template would be extracted on I(state=extracted).
      - Mutually exclusive with I(vm).
    type: str
  vm:
    description:
      - VM name the template will be created from its volume or alternatively from a snapshot.
      - VM must be in stopped state if created from its volume.
      - Mutually exclusive with I(url).
    type: str
  snapshot:
    description:
      - Name of the snapshot, created from the VM ROOT volume, the template will be created from.
      - I(vm) is required together with this argument.
    type: str
  os_type:
    description:
      - OS type that best represents the OS of this template.
    type: str
  checksum:
    description:
      - The MD5 checksum value of this template.
      - If set, we search by checksum instead of name.
    type: str
  is_ready:
    description:
      - "Note: this flag was not implemented and therefore marked as deprecated."
      - Deprecated, will be removed in version 2.11.
    type: bool
  is_public:
    description:
      - Register the template to be publicly available to all users.
      - Only used if I(state) is C(present).
    type: bool
  is_featured:
    description:
      - Register the template to be featured.
      - Only used if I(state) is C(present).
    type: bool
  is_dynamically_scalable:
    description:
      - Register the template having XS/VMWare tools installed in order to support dynamic scaling of VM CPU/memory.
      - Only used if I(state) is C(present).
    type: bool
  cross_zones:
    description:
      - Whether the template should be synced or removed across zones.
      - Only used if I(state) is C(present) or C(absent).
    default: no
    type: bool
  mode:
    description:
      - Mode for the template extraction.
      - Only used if I(state=extracted).
    type: str
    default: http_download
    choices: [ http_download, ftp_upload ]
  domain:
    description:
      - Domain the template, snapshot or VM is related to.
    type: str
  account:
    description:
      - Account the template, snapshot or VM is related to.
    type: str
  project:
    description:
      - Name of the project the template to be registered in.
    type: str
  zone:
    description:
      - Name of the zone you wish the template to be registered or deleted from.
      - If not specified, first found zone will be used.
    type: str
  template_filter:
    description:
      - Name of the filter used to search for the template.
      - The filter C(all) was added in 2.7.
    type: str
    default: self
    choices: [ all, featured, self, selfexecutable, sharedexecutable, executable, community ]
  template_find_options:
    description:
      - Options to find a template uniquely.
      - More than one allowed.
    type: list
    choices: [ display_text, checksum, cross_zones ]
    version_added: '2.7'
    aliases: [ template_find_option ]
    default: []
  hypervisor:
    description:
      - Name the hypervisor to be used for creating the new template.
      - Relevant when using I(state=present).
      - Possible values are C(KVM), C(VMware), C(BareMetal), C(XenServer), C(LXC), C(HyperV), C(UCS), C(OVM), C(Simulator).
    type: str
  requires_hvm:
    description:
      - Whether the template requires HVM or not.
      - Only considered while creating the template.
    type: bool
  password_enabled:
    description:
      - Enable template password reset support.
    type: bool
  template_tag:
    description:
      - The tag for this template.
    type: str
  sshkey_enabled:
    description:
      - True if the template supports the sshkey upload feature.
      - Only considered if I(url) is used (API limitation).
    type: bool
  is_routing:
    description:
      - Sets the template type to routing, i.e. if template is used to deploy routers.
      - Only considered if I(url) is used.
    type: bool
  format:
    description:
      - The format for the template.
      - Only considered if I(state=present).
    type: str
    choices: [ QCOW2, RAW, VHD, OVA ]
  is_extractable:
    description:
      - Allows the template or its derivatives to be extractable.
    type: bool
  details:
    description:
      - Template details in key/value pairs.
    type: str
  bits:
    description:
      - 32 or 64 bits support.
    type: int
    default: 64
    choices: [ 32, 64 ]
  display_text:
    description:
      - Display text of the template.
    type: str
  state:
    description:
      - State of the template.
    type: str
    default: present
    choices: [ present, absent, extracted ]
  poll_async:
    description:
      - Poll async jobs until job has finished.
    default: yes
    type: bool
  tags:
    description:
      - List of tags. Tags are a list of dictionaries having keys I(key) and I(value).
      - "To delete all tags, set a empty list e.g. I(tags: [])."
    type: list
    aliases: [ tag ]
    version_added: '2.4'
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: register a systemvm template
  cs_template:
    name: systemvm-vmware-4.5
    url: "http://packages.shapeblue.com/systemvmtemplate/4.5/systemvm64template-4.5-vmware.ova"
    hypervisor: VMware
    format: OVA
    cross_zones: yes
    os_type: Debian GNU/Linux 7(64-bit)
  delegate_to: localhost

- name: Create a template from a stopped virtual machine's volume
  cs_template:
    name: Debian 9 (64-bit) 20GB ({{ ansible_date_time.date }})
    vm: debian-9-base-vm
    os_type: Debian GNU/Linux 9 (64-bit)
    zone: tokio-ix
    password_enabled: yes
    is_public: yes
  delegate_to: localhost

# Note: Use template_find_option(s) when a template name is not unique
- name: Create a template from a stopped virtual machine's volume
  cs_template:
    name: Debian 9 (64-bit)
    display_text: Debian 9 (64-bit) 20GB ({{ ansible_date_time.date }})
    template_find_option: display_text
    vm: debian-9-base-vm
    os_type: Debian GNU/Linux 9 (64-bit)
    zone: tokio-ix
    password_enabled: yes
    is_public: yes
  delegate_to: localhost

- name: create a template from a virtual machine's root volume snapshot
  cs_template:
    name: Debian 9 (64-bit) Snapshot ROOT-233_2015061509114
    snapshot: ROOT-233_2015061509114
    os_type: Debian GNU/Linux 9 (64-bit)
    zone: tokio-ix
    password_enabled: yes
    is_public: yes
  delegate_to: localhost

- name: Remove a template
  cs_template:
    name: systemvm-4.2
    cross_zones: yes
    state: absent
  delegate_to: localhost
'''

RETURN = '''
---
id:
  description: UUID of the template or extracted object.
  returned: success
  type: str
  sample: a6f7a5fc-43f8-11e5-a151-feff819cdc9f
name:
  description: Name of the template or extracted object.
  returned: success
  type: str
  sample: Debian 7 64-bit
display_text:
  description: Display text of the template.
  returned: if available
  type: str
  sample: Debian 7.7 64-bit minimal 2015-03-19
checksum:
  description: MD5 checksum of the template.
  returned: if available
  type: str
  sample: 0b31bccccb048d20b551f70830bb7ad0
status:
  description: Status of the template or extracted object.
  returned: success
  type: str
  sample: Download Complete
is_ready:
  description: True if the template is ready to be deployed from.
  returned: if available
  type: bool
  sample: true
is_public:
  description: True if the template is public.
  returned: if available
  type: bool
  sample: true
is_featured:
  description: True if the template is featured.
  returned: if available
  type: bool
  sample: true
is_extractable:
  description: True if the template is extractable.
  returned: if available
  type: bool
  sample: true
format:
  description: Format of the template.
  returned: if available
  type: str
  sample: OVA
os_type:
  description: Type of the OS.
  returned: if available
  type: str
  sample: CentOS 6.5 (64-bit)
password_enabled:
  description: True if the reset password feature is enabled, false otherwise.
  returned: if available
  type: bool
  sample: false
sshkey_enabled:
  description: true if template is sshkey enabled, false otherwise.
  returned: if available
  type: bool
  sample: false
cross_zones:
  description: true if the template is managed across all zones, false otherwise.
  returned: if available
  type: bool
  sample: false
template_type:
  description: Type of the template.
  returned: if available
  type: str
  sample: USER
created:
  description: Date of registering.
  returned: success
  type: str
  sample: 2015-03-29T14:57:06+0200
template_tag:
  description: Template tag related to this template.
  returned: if available
  type: str
  sample: special
hypervisor:
  description: Hypervisor related to this template.
  returned: if available
  type: str
  sample: VMware
mode:
  description: Mode of extraction
  returned: on state=extracted
  type: str
  sample: http_download
state:
  description: State of the extracted template
  returned: on state=extracted
  type: str
  sample: DOWNLOAD_URL_CREATED
url:
  description: Url to which the template is extracted to
  returned: on state=extracted
  type: str
  sample: "http://1.2.3.4/userdata/eb307f13-4aca-45e8-b157-a414a14e6b04.ova"
tags:
  description: List of resource tags associated with the template.
  returned: if available
  type: list
  sample: '[ { "key": "foo", "value": "bar" } ]'
zone:
  description: Name of zone the template is registered in.
  returned: success
  type: str
  sample: zuerich
domain:
  description: Domain the template is related to.
  returned: success
  type: str
  sample: example domain
account:
  description: Account the template is related to.
  returned: success
  type: str
  sample: example account
project:
  description: Name of project the template is related to.
  returned: success
  type: str
  sample: Production
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together,
)


class AnsibleCloudStackTemplate(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackTemplate, self).__init__(module)
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
            'format': 'format',
            'hypervisor': 'hypervisor',
            'url': 'url',
            'extractMode': 'mode',
            'state': 'state',
        }

    def _get_args(self):
        args = {
            'name': self.module.params.get('name'),
            'displaytext': self.get_or_fallback('display_text', 'name'),
            'bits': self.module.params.get('bits'),
            'isdynamicallyscalable': self.module.params.get('is_dynamically_scalable'),
            'isextractable': self.module.params.get('is_extractable'),
            'isfeatured': self.module.params.get('is_featured'),
            'ispublic': self.module.params.get('is_public'),
            'passwordenabled': self.module.params.get('password_enabled'),
            'requireshvm': self.module.params.get('requires_hvm'),
            'templatetag': self.module.params.get('template_tag'),
            'ostypeid': self.get_os_type(key='id'),
        }

        if not args['ostypeid']:
            self.module.fail_json(msg="Missing required arguments: os_type")

        return args

    def get_root_volume(self, key=None):
        args = {
            'account': self.get_account(key='name'),
            'domainid': self.get_domain(key='id'),
            'projectid': self.get_project(key='id'),
            'virtualmachineid': self.get_vm(key='id'),
            'type': "ROOT"
        }
        volumes = self.query_api('listVolumes', **args)
        if volumes:
            return self._get_by_key(key, volumes['volume'][0])
        self.module.fail_json(msg="Root volume for '%s' not found" % self.get_vm('name'))

    def get_snapshot(self, key=None):
        snapshot = self.module.params.get('snapshot')
        if not snapshot:
            return None

        args = {
            'account': self.get_account(key='name'),
            'domainid': self.get_domain(key='id'),
            'projectid': self.get_project(key='id'),
            'volumeid': self.get_root_volume('id'),
            'fetch_list': True,
        }
        snapshots = self.query_api('listSnapshots', **args)
        if snapshots:
            for s in snapshots:
                if snapshot in [s['name'], s['id']]:
                    return self._get_by_key(key, s)
        self.module.fail_json(msg="Snapshot '%s' not found" % snapshot)

    def present_template(self):
        template = self.get_template()
        if template:
            template = self.update_template(template)
        elif self.module.params.get('url'):
            template = self.register_template()
        elif self.module.params.get('vm'):
            template = self.create_template()
        else:
            self.fail_json(msg="one of the following is required on state=present: url, vm")
        return template

    def create_template(self):
        template = None
        self.result['changed'] = True

        args = self._get_args()
        snapshot_id = self.get_snapshot(key='id')
        if snapshot_id:
            args['snapshotid'] = snapshot_id
        else:
            args['volumeid'] = self.get_root_volume('id')

        if not self.module.check_mode:
            template = self.query_api('createTemplate', **args)

            poll_async = self.module.params.get('poll_async')
            if poll_async:
                template = self.poll_job(template, 'template')

        if template:
            template = self.ensure_tags(resource=template, resource_type='Template')

        return template

    def register_template(self):
        required_params = [
            'format',
            'url',
            'hypervisor',
        ]
        self.module.fail_on_missing_params(required_params=required_params)
        template = None
        self.result['changed'] = True
        args = self._get_args()
        args.update({
            'url': self.module.params.get('url'),
            'format': self.module.params.get('format'),
            'checksum': self.module.params.get('checksum'),
            'isextractable': self.module.params.get('is_extractable'),
            'isrouting': self.module.params.get('is_routing'),
            'sshkeyenabled': self.module.params.get('sshkey_enabled'),
            'hypervisor': self.get_hypervisor(),
            'domainid': self.get_domain(key='id'),
            'account': self.get_account(key='name'),
            'projectid': self.get_project(key='id'),
        })

        if not self.module.params.get('cross_zones'):
            args['zoneid'] = self.get_zone(key='id')
        else:
            args['zoneid'] = -1

        if not self.module.check_mode:
            self.query_api('registerTemplate', **args)
            template = self.get_template()
        return template

    def update_template(self, template):
        args = {
            'id': template['id'],
            'displaytext': self.get_or_fallback('display_text', 'name'),
            'format': self.module.params.get('format'),
            'isdynamicallyscalable': self.module.params.get('is_dynamically_scalable'),
            'isrouting': self.module.params.get('is_routing'),
            'ostypeid': self.get_os_type(key='id'),
            'passwordenabled': self.module.params.get('password_enabled'),
        }
        if self.has_changed(args, template):
            self.result['changed'] = True
            if not self.module.check_mode:
                self.query_api('updateTemplate', **args)
                template = self.get_template()

        args = {
            'id': template['id'],
            'isextractable': self.module.params.get('is_extractable'),
            'isfeatured': self.module.params.get('is_featured'),
            'ispublic': self.module.params.get('is_public'),
        }
        if self.has_changed(args, template):
            self.result['changed'] = True
            if not self.module.check_mode:
                self.query_api('updateTemplatePermissions', **args)
                # Refresh
                template = self.get_template()

        if template:
            template = self.ensure_tags(resource=template, resource_type='Template')

        return template

    def _is_find_option(self, param_name):
        return param_name in self.module.params.get('template_find_options')

    def _find_option_match(self, template, param_name, internal_name=None):
        if not internal_name:
            internal_name = param_name

        if param_name in self.module.params.get('template_find_options'):
            param_value = self.module.params.get(param_name)

            if not param_value:
                self.fail_json(msg="The param template_find_options has %s but param was not provided." % param_name)

            if template[internal_name] == param_value:
                return True
        return False

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
            for tmpl in templates['template']:

                if self._is_find_option('cross_zones') and not self._find_option_match(
                        template=tmpl,
                        param_name='cross_zones',
                        internal_name='crossZones'):
                    continue

                if self._is_find_option('checksum') and not self._find_option_match(
                        template=tmpl,
                        param_name='checksum'):
                    continue

                if self._is_find_option('display_text') and not self._find_option_match(
                        template=tmpl,
                        param_name='display_text',
                        internal_name='displaytext'):
                    continue

                if not template_found:
                    template_found = tmpl
                # A cross zones template has one entry per zone but the same id
                elif tmpl['id'] == template_found['id']:
                    continue
                else:
                    self.fail_json(msg="Multiple templates found matching provided params. Please use template_find_options.")

        return template_found

    def extract_template(self):
        template = self.get_template()
        if not template:
            self.module.fail_json(msg="Failed: template not found")

        args = {
            'id': template['id'],
            'url': self.module.params.get('url'),
            'mode': self.module.params.get('mode'),
            'zoneid': self.get_zone(key='id')
        }
        self.result['changed'] = True

        if not self.module.check_mode:
            template = self.query_api('extractTemplate', **args)

            poll_async = self.module.params.get('poll_async')
            if poll_async:
                template = self.poll_job(template, 'template')
        return template

    def remove_template(self):
        template = self.get_template()
        if template:
            self.result['changed'] = True

            args = {
                'id': template['id']
            }
            if not self.module.params.get('cross_zones'):
                args['zoneid'] = self.get_zone(key='id')

            if not self.module.check_mode:
                res = self.query_api('deleteTemplate', **args)

                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    res = self.poll_job(res, 'template')
        return template

    def get_result(self, template):
        super(AnsibleCloudStackTemplate, self).get_result(template)
        if template:
            if 'isextractable' in template:
                self.result['is_extractable'] = True if template['isextractable'] else False
            if 'isfeatured' in template:
                self.result['is_featured'] = True if template['isfeatured'] else False
            if 'ispublic' in template:
                self.result['is_public'] = True if template['ispublic'] else False
        return self.result


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        display_text=dict(),
        url=dict(),
        vm=dict(),
        snapshot=dict(),
        os_type=dict(),
        is_ready=dict(type='bool', removed_in_version='2.11'),
        is_public=dict(type='bool'),
        is_featured=dict(type='bool'),
        is_dynamically_scalable=dict(type='bool'),
        is_extractable=dict(type='bool'),
        is_routing=dict(type='bool'),
        checksum=dict(),
        template_filter=dict(default='self', choices=['all', 'featured', 'self', 'selfexecutable', 'sharedexecutable', 'executable', 'community']),
        template_find_options=dict(type='list', choices=['display_text', 'checksum', 'cross_zones'], aliases=['template_find_option'], default=[]),
        hypervisor=dict(),
        requires_hvm=dict(type='bool'),
        password_enabled=dict(type='bool'),
        template_tag=dict(),
        sshkey_enabled=dict(type='bool'),
        format=dict(choices=['QCOW2', 'RAW', 'VHD', 'OVA']),
        details=dict(),
        bits=dict(type='int', choices=[32, 64], default=64),
        state=dict(choices=['present', 'absent', 'extracted'], default='present'),
        cross_zones=dict(type='bool', default=False),
        mode=dict(choices=['http_download', 'ftp_upload'], default='http_download'),
        zone=dict(),
        domain=dict(),
        account=dict(),
        project=dict(),
        poll_async=dict(type='bool', default=True),
        tags=dict(type='list', aliases=['tag']),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        mutually_exclusive=(
            ['url', 'vm'],
            ['zone', 'cross_zones'],
        ),
        supports_check_mode=True
    )

    acs_tpl = AnsibleCloudStackTemplate(module)

    state = module.params.get('state')
    if state == 'absent':
        tpl = acs_tpl.remove_template()

    elif state == 'extracted':
        tpl = acs_tpl.extract_template()
    else:
        tpl = acs_tpl.present_template()

    result = acs_tpl.get_result(tpl)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
