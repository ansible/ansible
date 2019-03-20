#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_asm_policy
short_description: Manage BIG-IP ASM policies
description:
   - Manage BIG-IP ASM policies.
version_added: 2.5
deprecated:
  removed_in: '2.12'
  alternative: bigip_asm_policy_manage
  why: >
    The bigip_asm_policy module has been split into three new modules to handle import, export and general policy
    management. This will allow scalability of the asm policy management as well as ease of maintenance.
    Additionally to further reduce the burden of having multiple smaller module F5 has created asm_policy
    role in Ansible Galaxy for a more declarative way of ASM policy management.
options:
  active:
    description:
      - If C(yes) will apply and activate existing inactive policy. If C(no), it will
        deactivate existing active policy. Generally should be C(yes) only in cases where
        you want to activate new or existing policy.
    default: no
    type: bool
  name:
    description:
      - The ASM policy to manage or create.
    required: True
  state:
    description:
      - When C(state) is C(present), and C(file) or C(template) parameter is provided,
        new ASM policy is imported and created with the given C(name).
      - When C(state) is present and no C(file) or C(template) parameter is provided
        new blank ASM policy is created with the given C(name).
      - When C(state) is C(absent), ensures that the policy is removed, even if it is
        currently active.
    choices:
      - present
      - absent
    default: present
  file:
    description:
      - Full path to a policy file to be imported into the BIG-IP ASM.
      - Policy files exported from newer versions of BIG-IP cannot be imported into older
        versions of BIG-IP. The opposite, however, is true; you can import older into
        newer.
  template:
    description:
      - An ASM policy built-in template. If the template does not exist we will raise an error.
      - Once the policy has been created, this value cannot change.
      - The C(Comprehensive), C(Drupal), C(Fundamental), C(Joomla),
        C(Vulnerability Assessment Baseline), and C(Wordpress) templates are only available
        on BIG-IP versions >= 13.
    choices:
      - ActiveSync v1.0 v2.0 (http)
      - ActiveSync v1.0 v2.0 (https)
      - Comprehensive
      - Drupal
      - Fundamental
      - Joomla
      - LotusDomino 6.5 (http)
      - LotusDomino 6.5 (https)
      - OWA Exchange 2003 (http)
      - OWA Exchange 2003 (https)
      - OWA Exchange 2003 with ActiveSync (http)
      - OWA Exchange 2003 with ActiveSync (https)
      - OWA Exchange 2007 (http)
      - OWA Exchange 2007 (https)
      - OWA Exchange 2007 with ActiveSync (http)
      - OWA Exchange 2007 with ActiveSync (https)
      - OWA Exchange 2010 (http)
      - OWA Exchange 2010 (https)
      - Oracle 10g Portal (http)
      - Oracle 10g Portal (https)
      - Oracle Applications 11i (http)
      - Oracle Applications 11i (https)
      - PeopleSoft Portal 9 (http)
      - PeopleSoft Portal 9 (https)
      - Rapid Deployment Policy
      - SAP NetWeaver 7 (http)
      - SAP NetWeaver 7 (https)
      - SharePoint 2003 (http)
      - SharePoint 2003 (https)
      - SharePoint 2007 (http)
      - SharePoint 2007 (https)
      - SharePoint 2010 (http)
      - SharePoint 2010 (https)
      - Vulnerability Assessment Baseline
      - Wordpress
  partition:
    description:
      - Device partition to manage resources on.
    default: Common
extends_documentation_fragment: f5
author:
  - Wojciech Wypior (@wojtek0806)
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Import and activate ASM policy
  bigip_asm_policy:
    name: new_asm_policy
    file: /root/asm_policy.xml
    active: yes
    state: present
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Import ASM policy from template
  bigip_asm_policy:
    name: new_sharepoint_policy
    template: SharePoint 2007 (http)
    state: present
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Create blank ASM policy
  bigip_asm_policy:
    name: new_blank_policy
    state: present
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Create blank ASM policy and activate
  bigip_asm_policy:
    name: new_blank_policy
    active: yes
    state: present
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Activate ASM policy
  bigip_asm_policy:
    name: inactive_policy
    active: yes
    state: present
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Deactivate ASM policy
  bigip_asm_policy:
    name: active_policy
    state: present
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Import and activate ASM policy in Role
  bigip_asm_policy:
    name: new_asm_policy
    file: "{{ role_path }}/files/asm_policy.xml"
    active: yes
    state: present
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Import ASM binary policy
  bigip_asm_policy:
    name: new_asm_policy
    file: "/root/asm_policy.plc"
    active: yes
    state: present
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost
'''

RETURN = r'''
active:
  description: Set when activating/deactivating ASM policy
  returned: changed
  type: bool
  sample: yes
state:
  description: Action performed on the target device.
  returned: changed
  type: str
  sample: absent
file:
  description: Local path to ASM policy file.
  returned: changed
  type: str
  sample: /root/some_policy.xml
template:
  description: Name of the built-in ASM policy template
  returned: changed
  type: str
  sample: OWA Exchange 2007 (https)
name:
  description: Name of the ASM policy to be managed/created
  returned: changed
  type: str
  sample: Asm_APP1_Transparent
'''

import os
import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from distutils.version import LooseVersion


try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.icontrol import upload_file
    from library.module_utils.network.f5.icontrol import tmos_version
    from library.module_utils.network.f5.icontrol import module_provisioned
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.icontrol import upload_file
    from ansible.module_utils.network.f5.icontrol import tmos_version
    from ansible.module_utils.network.f5.icontrol import module_provisioned


class Parameters(AnsibleF5Parameters):
    updatables = [
        'active',
    ]

    returnables = [
        'name',
        'template',
        'file',
        'active',
    ]

    api_attributes = [
        'name',
        'file',
        'active',
    ]
    api_map = {
        'filename': 'file',
    }

    @property
    def template_link(self):
        if self._values['template_link'] is not None:
            return self._values['template_link']
        collection = self._templates_from_device()
        for resource in collection['items']:
            if resource['name'] == self.template.upper():
                return dict(link=resource['selfLink'])
        return None

    @property
    def full_path(self):
        return fq_name(self.name)

    def _templates_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/asm/policy-templates/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)

        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return response

    def to_return(self):
        result = {}
        for returnable in self.returnables:
            result[returnable] = getattr(self, returnable)
        result = self._filter_params(result)
        return result


class V1Parameters(Parameters):
    @property
    def template(self):
        if self._values['template'] is None:
            return None
        template_map = {
            'ActiveSync v1.0 v2.0 (http)': 'POLICY_TEMPLATE_ACTIVESYNC_V1_0_V2_0_HTTP',
            'ActiveSync v1.0 v2.0 (https)': 'POLICY_TEMPLATE_ACTIVESYNC_V1_0_V2_0_HTTPS',
            'LotusDomino 6.5 (http)': 'POLICY_TEMPLATE_LOTUSDOMINO_6_5_HTTP',
            'LotusDomino 6.5 (https)': 'POLICY_TEMPLATE_LOTUSDOMINO_6_5_HTTPS',
            'OWA Exchange 2003 (http)': 'POLICY_TEMPLATE_OWA_EXCHANGE_2003_HTTP',
            'OWA Exchange 2003 (https)': 'POLICY_TEMPLATE_OWA_EXCHANGE_2003_HTTPS',
            'OWA Exchange 2003 with ActiveSync (http)': 'POLICY_TEMPLATE_OWA_EXCHANGE_2003_WITH_ACTIVESYNC_HTTP',
            'OWA Exchange 2003 with ActiveSync (https)': 'POLICY_TEMPLATE_OWA_EXCHANGE_2003_WITH_ACTIVESYNC_HTTPS',
            'OWA Exchange 2007 (http)': 'POLICY_TEMPLATE_OWA_EXCHANGE_2007_HTTP',
            'OWA Exchange 2007 (https)': 'POLICY_TEMPLATE_OWA_EXCHANGE_2007_HTTPS',
            'OWA Exchange 2007 with ActiveSync (http)': 'POLICY_TEMPLATE_OWA_EXCHANGE_2007_WITH_ACTIVESYNC_HTTP',
            'OWA Exchange 2007 with ActiveSync (https)': 'POLICY_TEMPLATE_OWA_EXCHANGE_2007_WITH_ACTIVESYNC_HTTPS',
            'OWA Exchange 2010 (http)': 'POLICY_TEMPLATE_OWA_EXCHANGE_2010_HTTP',
            'OWA Exchange 2010 (https)': 'POLICY_TEMPLATE_OWA_EXCHANGE_2010_HTTPS',
            'Oracle 10g Portal (http)': 'POLICY_TEMPLATE_ORACLE_10G_PORTAL_HTTP',
            'Oracle 10g Portal (https)': 'POLICY_TEMPLATE_ORACLE_10G_PORTAL_HTTPS',
            'Oracle Applications 11i (http)': 'POLICY_TEMPLATE_ORACLE_APPLICATIONS_11I_HTTP',
            'Oracle Applications 11i (https)': 'POLICY_TEMPLATE_ORACLE_APPLICATIONS_11I_HTTPS',
            'PeopleSoft Portal 9 (http)': 'POLICY_TEMPLATE_PEOPLESOFT_PORTAL_9_HTTP',
            'PeopleSoft Portal 9 (https)': 'POLICY_TEMPLATE_PEOPLESOFT_PORTAL_9_HTTPS',
            'Rapid Deployment Policy': 'POLICY_TEMPLATE_RAPID_DEPLOYMENT',
            'SAP NetWeaver 7 (http)': 'POLICY_TEMPLATE_SAP_NETWEAVER_7_HTTP',
            'SAP NetWeaver 7 (https)': 'POLICY_TEMPLATE_SAP_NETWEAVER_7_HTTPS',
            'SharePoint 2003 (http)': 'POLICY_TEMPLATE_SHAREPOINT_2003_HTTP',
            'SharePoint 2003 (https)': 'POLICY_TEMPLATE_SHAREPOINT_2003_HTTPS',
            'SharePoint 2007 (http)': 'POLICY_TEMPLATE_SHAREPOINT_2007_HTTP',
            'SharePoint 2007 (https)': 'POLICY_TEMPLATE_SHAREPOINT_2007_HTTPS',
            'SharePoint 2010 (http)': 'POLICY_TEMPLATE_SHAREPOINT_2010_HTTP',
            'SharePoint 2010 (https)': 'POLICY_TEMPLATE_SHAREPOINT_2010_HTTPS'
        }
        if self._values['template'] in template_map:
            return template_map[self._values['template']]
        else:
            raise F5ModuleError(
                "The specified template is not valid for this version of BIG-IP."
            )


class V2Parameters(Parameters):
    @property
    def template(self):
        if self._values['template'] is None:
            return None
        template_map = {
            'ActiveSync v1.0 v2.0 (http)': 'POLICY_TEMPLATE_ACTIVESYNC_V1_0_V2_0_HTTP',
            'ActiveSync v1.0 v2.0 (https)': 'POLICY_TEMPLATE_ACTIVESYNC_V1_0_V2_0_HTTPS',
            'Comprehensive': 'POLICY_TEMPLATE_COMPREHENSIVE',  # v13
            'Drupal': 'POLICY_TEMPLATE_DRUPAL',  # v13
            'Fundamental': 'POLICY_TEMPLATE_FUNDAMENTAL',  # v13
            'Joomla': 'POLICY_TEMPLATE_JOOMLA',  # v13
            'LotusDomino 6.5 (http)': 'POLICY_TEMPLATE_LOTUSDOMINO_6_5_HTTP',
            'LotusDomino 6.5 (https)': 'POLICY_TEMPLATE_LOTUSDOMINO_6_5_HTTPS',
            'OWA Exchange 2003 (http)': 'POLICY_TEMPLATE_OWA_EXCHANGE_2003_HTTP',
            'OWA Exchange 2003 (https)': 'POLICY_TEMPLATE_OWA_EXCHANGE_2003_HTTPS',
            'OWA Exchange 2003 with ActiveSync (http)': 'POLICY_TEMPLATE_OWA_EXCHANGE_2003_WITH_ACTIVESYNC_HTTP',
            'OWA Exchange 2003 with ActiveSync (https)': 'POLICY_TEMPLATE_OWA_EXCHANGE_2003_WITH_ACTIVESYNC_HTTPS',
            'OWA Exchange 2007 (http)': 'POLICY_TEMPLATE_OWA_EXCHANGE_2007_HTTP',
            'OWA Exchange 2007 (https)': 'POLICY_TEMPLATE_OWA_EXCHANGE_2007_HTTPS',
            'OWA Exchange 2007 with ActiveSync (http)': 'POLICY_TEMPLATE_OWA_EXCHANGE_2007_WITH_ACTIVESYNC_HTTP',
            'OWA Exchange 2007 with ActiveSync (https)': 'POLICY_TEMPLATE_OWA_EXCHANGE_2007_WITH_ACTIVESYNC_HTTPS',
            'OWA Exchange 2010 (http)': 'POLICY_TEMPLATE_OWA_EXCHANGE_2010_HTTP',
            'OWA Exchange 2010 (https)': 'POLICY_TEMPLATE_OWA_EXCHANGE_2010_HTTPS',
            'Oracle 10g Portal (http)': 'POLICY_TEMPLATE_ORACLE_10G_PORTAL_HTTP',
            'Oracle 10g Portal (https)': 'POLICY_TEMPLATE_ORACLE_10G_PORTAL_HTTPS',
            'Oracle Applications 11i (http)': 'POLICY_TEMPLATE_ORACLE_APPLICATIONS_11I_HTTP',
            'Oracle Applications 11i (https)': 'POLICY_TEMPLATE_ORACLE_APPLICATIONS_11I_HTTPS',
            'PeopleSoft Portal 9 (http)': 'POLICY_TEMPLATE_PEOPLESOFT_PORTAL_9_HTTP',
            'PeopleSoft Portal 9 (https)': 'POLICY_TEMPLATE_PEOPLESOFT_PORTAL_9_HTTPS',
            'Rapid Deployment Policy': 'POLICY_TEMPLATE_RAPID_DEPLOYMENT',
            'SAP NetWeaver 7 (http)': 'POLICY_TEMPLATE_SAP_NETWEAVER_7_HTTP',
            'SAP NetWeaver 7 (https)': 'POLICY_TEMPLATE_SAP_NETWEAVER_7_HTTPS',
            'SharePoint 2003 (http)': 'POLICY_TEMPLATE_SHAREPOINT_2003_HTTP',
            'SharePoint 2003 (https)': 'POLICY_TEMPLATE_SHAREPOINT_2003_HTTPS',
            'SharePoint 2007 (http)': 'POLICY_TEMPLATE_SHAREPOINT_2007_HTTP',
            'SharePoint 2007 (https)': 'POLICY_TEMPLATE_SHAREPOINT_2007_HTTPS',
            'SharePoint 2010 (http)': 'POLICY_TEMPLATE_SHAREPOINT_2010_HTTP',
            'SharePoint 2010 (https)': 'POLICY_TEMPLATE_SHAREPOINT_2010_HTTPS',
            'Vulnerability Assessment Baseline': 'POLICY_TEMPLATE_VULNERABILITY_ASSESSMENT',  # v13
            'Wordpress': 'POLICY_TEMPLATE_WORDPRESS'  # v13
        }
        return template_map[self._values['template']]


class Changes(Parameters):
    @property
    def template(self):
        if self._values['template'] is None:
            return None
        template_map = {
            'POLICY_TEMPLATE_ACTIVESYNC_V1_0_V2_0_HTTP': 'ActiveSync v1.0 v2.0 (http)',
            'POLICY_TEMPLATE_ACTIVESYNC_V1_0_V2_0_HTTPS': 'ActiveSync v1.0 v2.0 (https)',
            'POLICY_TEMPLATE_COMPREHENSIVE': 'Comprehensive',
            'POLICY_TEMPLATE_DRUPAL': 'Drupal',
            'POLICY_TEMPLATE_FUNDAMENTAL': 'Fundamental',
            'POLICY_TEMPLATE_JOOMLA': 'Joomla',
            'POLICY_TEMPLATE_LOTUSDOMINO_6_5_HTTP': 'LotusDomino 6.5 (http)',
            'POLICY_TEMPLATE_LOTUSDOMINO_6_5_HTTPS': 'LotusDomino 6.5 (https)',
            'POLICY_TEMPLATE_OWA_EXCHANGE_2003_HTTP': 'OWA Exchange 2003 (http)',
            'POLICY_TEMPLATE_OWA_EXCHANGE_2003_HTTPS': 'OWA Exchange 2003 (https)',
            'POLICY_TEMPLATE_OWA_EXCHANGE_2003_WITH_ACTIVESYNC_HTTP': 'OWA Exchange 2003 with ActiveSync (http)',
            'POLICY_TEMPLATE_OWA_EXCHANGE_2003_WITH_ACTIVESYNC_HTTPS': 'OWA Exchange 2003 with ActiveSync (https)',
            'POLICY_TEMPLATE_OWA_EXCHANGE_2007_HTTP': 'OWA Exchange 2007 (http)',
            'POLICY_TEMPLATE_OWA_EXCHANGE_2007_HTTPS': 'OWA Exchange 2007 (https)',
            'POLICY_TEMPLATE_OWA_EXCHANGE_2007_WITH_ACTIVESYNC_HTTP': 'OWA Exchange 2007 with ActiveSync (http)',
            'POLICY_TEMPLATE_OWA_EXCHANGE_2007_WITH_ACTIVESYNC_HTTPS': 'OWA Exchange 2007 with ActiveSync (https)',
            'POLICY_TEMPLATE_OWA_EXCHANGE_2010_HTTP': 'OWA Exchange 2010 (http)',
            'POLICY_TEMPLATE_OWA_EXCHANGE_2010_HTTPS': 'OWA Exchange 2010 (https)',
            'POLICY_TEMPLATE_ORACLE_10G_PORTAL_HTTP': 'Oracle 10g Portal (http)',
            'POLICY_TEMPLATE_ORACLE_10G_PORTAL_HTTPS': 'Oracle 10g Portal (https)',
            'POLICY_TEMPLATE_ORACLE_APPLICATIONS_11I_HTTP': 'Oracle Applications 11i (http)',
            'POLICY_TEMPLATE_ORACLE_APPLICATIONS_11I_HTTPS': 'Oracle Applications 11i (https)',
            'POLICY_TEMPLATE_PEOPLESOFT_PORTAL_9_HTTP': 'PeopleSoft Portal 9 (http)',
            'POLICY_TEMPLATE_PEOPLESOFT_PORTAL_9_HTTPS': 'PeopleSoft Portal 9 (https)',
            'POLICY_TEMPLATE_RAPID_DEPLOYMENT': 'Rapid Deployment Policy',
            'POLICY_TEMPLATE_SAP_NETWEAVER_7_HTTP': 'SAP NetWeaver 7 (http)',
            'POLICY_TEMPLATE_SAP_NETWEAVER_7_HTTPS': 'SAP NetWeaver 7 (https)',
            'POLICY_TEMPLATE_SHAREPOINT_2003_HTTP': 'SharePoint 2003 (http)',
            'POLICY_TEMPLATE_SHAREPOINT_2003_HTTPS': 'SharePoint 2003 (https)',
            'POLICY_TEMPLATE_SHAREPOINT_2007_HTTP': 'SharePoint 2007 (http)',
            'POLICY_TEMPLATE_SHAREPOINT_2007_HTTPS': 'SharePoint 2007 (https)',
            'POLICY_TEMPLATE_SHAREPOINT_2010_HTTP': 'SharePoint 2010 (http)',
            'POLICY_TEMPLATE_SHAREPOINT_2010_HTTPS': 'SharePoint 2010 (https)',
            'POLICY_TEMPLATE_VULNERABILITY_ASSESSMENT': 'Vulnerability Assessment Baseline',
            'POLICY_TEMPLATE_WORDPRESS': 'Wordpress',
        }
        return template_map[self._values['template']]


class Difference(object):
    def __init__(self, want, have=None):
        self.want = want
        self.have = have

    def compare(self, param):
        try:
            result = getattr(self, param)
            return result
        except AttributeError:
            return self.__default(param)

    def __default(self, param):
        attr1 = getattr(self.want, param)
        try:
            attr2 = getattr(self.have, param)
            if attr1 != attr2:
                return attr1
        except AttributeError:
            return attr1

    @property
    def active(self):
        if self.want.active is True and self.have.active is False:
            return True
        if self.want.active is False and self.have.active is True:
            return False


class BaseManager(object):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.module = kwargs.get('module', None)
        self.have = None
        self.changes = Changes()

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        if state == "present":
            changed = self.present()
        elif state == "absent":
            changed = self.absent()

        changes = self.changes.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        return result

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.client.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = Changes(params=changed)

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def _update_changed_options(self):
        diff = Difference(self.want, self.have)
        updatables = Parameters.updatables
        changed = dict()
        for k in updatables:
            change = diff.compare(k)
            if change is None:
                continue
            else:
                if isinstance(change, dict):
                    changed.update(change)
                else:
                    changed[k] = change
        if changed:
            self.changes = Changes(params=changed)
            return True
        return False

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def absent(self):
        if not self.exists():
            return False
        else:
            return self.remove()

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/asm/policies/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)

        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if any(p['name'] == self.want.name and p['partition'] == self.want.partition for p in response['items']):
            return True
        return False

    def _file_is_missing(self):
        if self.want.template and self.want.file is None:
            return False
        if self.want.template is None and self.want.file is None:
            return False
        if not os.path.exists(self.want.file):
            return True
        return False

    def create(self):
        if self.want.active is None:
            self.want.update(dict(active=False))
        if self._file_is_missing():
            raise F5ModuleError(
                "The specified ASM policy file does not exist"
            )
        self._set_changed_options()
        if self.module.check_mode:
            return True

        if self.want.template is None and self.want.file is None:
            self.create_blank()
        else:
            if self.want.template is not None:
                self.create_from_template()
            elif self.want.file is not None:
                self.create_from_file()

        if self.want.active:
            self.activate()
            return True
        else:
            return True

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
        self.update_on_device()
        if self.changes.active:
            self.activate()
        return True

    def activate(self):
        self.have = self.read_current_from_device()
        task_id = self.apply_on_device()
        if self.wait_for_task(task_id, 'apply'):
            return True
        else:
            raise F5ModuleError('Apply policy task failed.')

    def wait_for_task(self, task_id, task):
        uri = ''
        if task == 'apply':
            uri = "https://{0}:{1}/mgmt/tm/asm/tasks/apply-policy/{2}".format(
                self.client.provider['server'],
                self.client.provider['server_port'],
                task_id
            )
        elif task == 'import':
            uri = "https://{0}:{1}/mgmt/tm/asm/tasks/import-policy/{2}".format(
                self.client.provider['server'],
                self.client.provider['server_port'],
                task_id
            )
        while True:
            resp = self.client.api.get(uri)

            try:
                response = resp.json()
            except ValueError as ex:
                raise F5ModuleError(str(ex))

            if 'code' in response and response['code'] == 400:
                if 'message' in response:
                    raise F5ModuleError(response['message'])
                else:
                    raise F5ModuleError(resp.content)

            if response['status'] in ['COMPLETED', 'FAILURE']:
                break
            time.sleep(1)

        if response['status'] == 'FAILURE':
            return False
        if response['status'] == 'COMPLETED':
            return True

    def _get_policy_id(self):
        name = self.want.name
        partition = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/asm/policies/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)

        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        policy_id = next(
            (p['id'] for p in response['items'] if p['name'] == name and p['partition'] == partition), None
        )

        if not policy_id:
            raise F5ModuleError("The policy was not found")
        return policy_id

    def update_on_device(self):
        params = self.changes.api_params()
        policy_id = self._get_policy_id()
        uri = "https://{0}:{1}/mgmt/tm/asm/policies/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            policy_id
        )
        if not params['active']:
            resp = self.client.api.patch(uri, json=params)

            try:
                response = resp.json()
            except ValueError as ex:
                raise F5ModuleError(str(ex))

            if 'code' in response and response['code'] == 400:
                if 'message' in response:
                    raise F5ModuleError(response['message'])
                else:
                    raise F5ModuleError(resp.content)

    def create_blank(self):
        self.create_on_device()
        if self.exists():
            return True
        else:
            raise F5ModuleError(
                'Failed to create ASM policy: {0}'.format(self.want.name)
            )

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError(
                'Failed to delete ASM policy: {0}'.format(self.want.name)
            )
        return True

    def is_activated(self):
        if self.want.active is True:
            return True
        else:
            return False

    def read_current_from_device(self):
        policy_id = self._get_policy_id()
        uri = "https://{0}:{1}/mgmt/tm/asm/policies/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            policy_id
        )
        resp = self.client.api.get(uri)

        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

        response.update((dict(self_link=response['selfLink'])))

        return Parameters(params=response)

    def upload_file_to_device(self, content, name):
        url = 'https://{0}:{1}/mgmt/shared/file-transfer/uploads'.format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        try:
            upload_file(self.client, url, content, name)
        except F5ModuleError:
            raise F5ModuleError(
                "Failed to upload the file."
            )

    def import_to_device(self):
        name = os.path.split(self.want.file)[1]
        self.upload_file_to_device(self.want.file, name)
        time.sleep(2)

        full_name = fq_name(self.want.partition, self.want.name)
        cmd = 'tmsh load asm policy {0} file /var/config/rest/downloads/{1}'.format(full_name, name)

        uri = "https://{0}:{1}/mgmt/tm/util/bash/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        args = dict(
            command='run',
            utilCmdArgs='-c "{0}"'.format(cmd)
        )
        resp = self.client.api.post(uri, json=args)

        try:
            response = resp.json()
            if 'commandResult' in response:
                if 'Unexpected Error' in response['commandResult']:
                    raise F5ModuleError(response['commandResult'])
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return True

    def remove_temp_policy_from_device(self):
        name = os.path.split(self.want.file)[1]
        tpath_name = '/var/config/rest/downloads/{0}'.format(name)
        uri = "https://{0}:{1}/mgmt/tm/util/unix-rm/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        args = dict(
            command='run',
            utilCmdArgs=tpath_name
        )
        resp = self.client.api.post(uri, json=args)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def apply_on_device(self):
        uri = "https://{0}:{1}/mgmt/tm/asm/tasks/apply-policy/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        params = dict(policyReference={'link': self.have.self_link})
        resp = self.client.api.post(uri, json=params)

        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return response['id']

    def create_from_template_on_device(self):
        full_name = fq_name(self.want.partition, self.want.name)
        cmd = 'tmsh create asm policy {0} policy-template {1}'.format(full_name, self.want.template)
        uri = "https://{0}:{1}/mgmt/tm/util/bash/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        args = dict(
            command='run',
            utilCmdArgs='-c "{0}"'.format(cmd)
        )
        resp = self.client.api.post(uri, json=args)

        try:
            response = resp.json()
            if 'commandResult' in response:
                if 'Unexpected Error' in response['commandResult']:
                    raise F5ModuleError(response['commandResult'])
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        # we need to remove active from params as API will raise an error if the active is set to True,
        # policies can only be activated via apply-policy task endpoint.
        params.pop('active')
        uri = "https://{0}:{1}/mgmt/tm/asm/policies/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.post(uri, json=params)

        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 401, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        time.sleep(2)
        return response['selfLink']

    def remove_from_device(self):
        policy_id = self._get_policy_id()
        uri = "https://{0}:{1}/mgmt/tm/asm/policies/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            policy_id
        )
        response = self.client.api.delete(uri)
        if response.status in [200, 201]:
            return True
        raise F5ModuleError(response.content)


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.kwargs = kwargs

    def exec_module(self):
        if not module_provisioned(self.client, 'asm'):
            raise F5ModuleError(
                "ASM must be provisioned to use this module."
            )
        if self.version_is_less_than_13():
            manager = self.get_manager('v1')
        else:
            manager = self.get_manager('v2')
        return manager.exec_module()

    def get_manager(self, type):
        if type == 'v1':
            return V1Manager(**self.kwargs)
        elif type == 'v2':
            return V2Manager(**self.kwargs)

    def version_is_less_than_13(self):
        version = tmos_version(self.client)
        if LooseVersion(version) < LooseVersion('13.0.0'):
            return True
        else:
            return False


class V1Manager(BaseManager):
    def __init__(self, *args, **kwargs):
        module = kwargs.get('module', None)
        client = F5RestClient(**module.params)
        super(V1Manager, self).__init__(client=client, module=module)
        self.want = V1Parameters(params=module.params, client=client)

    def create_from_file(self):
        self.import_to_device()
        self.remove_temp_policy_from_device()

    def create_from_template(self):
        self.create_from_template_on_device()


class V2Manager(BaseManager):
    def __init__(self, *args, **kwargs):
        module = kwargs.get('module', None)
        client = F5RestClient(**module.params)
        super(V2Manager, self).__init__(client=client, module=module)
        self.want = V2Parameters(params=module.params, client=client)

    def create_from_template(self):
        if not self.create_from_template_on_device():
            return False

    def create_from_file(self):
        if not self.import_to_device():
            return False
        self.remove_temp_policy_from_device()


class ArgumentSpec(object):
    def __init__(self):
        self.template_map = [
            'ActiveSync v1.0 v2.0 (http)',
            'ActiveSync v1.0 v2.0 (https)',
            'Comprehensive',
            'Drupal',
            'Fundamental',
            'Joomla',
            'LotusDomino 6.5 (http)',
            'LotusDomino 6.5 (https)',
            'OWA Exchange 2003 (http)',
            'OWA Exchange 2003 (https)',
            'OWA Exchange 2003 with ActiveSync (http)',
            'OWA Exchange 2003 with ActiveSync (https)',
            'OWA Exchange 2007 (http)',
            'OWA Exchange 2007 (https)',
            'OWA Exchange 2007 with ActiveSync (http)',
            'OWA Exchange 2007 with ActiveSync (https)',
            'OWA Exchange 2010 (http)',
            'OWA Exchange 2010 (https)',
            'Oracle 10g Portal (http)',
            'Oracle 10g Portal (https)',
            'Oracle Applications 11i (http)',
            'Oracle Applications 11i (https)',
            'PeopleSoft Portal 9 (http)',
            'PeopleSoft Portal 9 (https)',
            'Rapid Deployment Policy',
            'SAP NetWeaver 7 (http)',
            'SAP NetWeaver 7 (https)',
            'SharePoint 2003 (http)',
            'SharePoint 2003 (https)',
            'SharePoint 2007 (http)',
            'SharePoint 2007 (https)',
            'SharePoint 2010 (http)',
            'SharePoint 2010 (https)',
            'Vulnerability Assessment Baseline',
            'Wordpress',
        ]
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(
                required=True,
            ),
            file=dict(type='path'),
            template=dict(
                choices=self.template_map
            ),
            active=dict(
                type='bool'
            ),
            state=dict(
                default='present',
                choices=['present', 'absent']
            ),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            )
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        mutually_exclusive=[
            ['file', 'template']
        ]
    )

    client = F5RestClient(**module.params)

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
