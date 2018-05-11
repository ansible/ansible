#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: bigip_asm_policy
short_description: Manage BIG-IP ASM policies
description:
   - Manage BIG-IP ASM policies.
version_added: 2.5
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
    server: lb.mydomain.com
    user: admin
    password: secret
    name: new_asm_policy
    file: /root/asm_policy.xml
    active: yes
    state: present
  delegate_to: localhost

- name: Import ASM policy from template
  bigip_asm_policy:
    server: lb.mydomain.com
    user: admin
    password: secret
    name: new_sharepoint_policy
    template: SharePoint 2007 (http)
    state: present
  delegate_to: localhost

- name: Create blank ASM policy
  bigip_asm_policy:
    server: lb.mydomain.com
    user: admin
    password: secret
    name: new_blank_policy
    state: present
  delegate_to: localhost

- name: Create blank ASM policy and activate
  bigip_asm_policy:
    server: lb.mydomain.com
    user: admin
    password: secret
    name: new_blank_policy
    active: yes
    state: present
  delegate_to: localhost

- name: Activate ASM policy
  bigip_asm_policy:
    server: lb.mydomain.com
    user: admin
    password: secret
    name: inactive_policy
    active: yes
    state: present
  delegate_to: localhost

- name: Deactivate ASM policy
  bigip_asm_policy:
    server: lb.mydomain.com
    user: admin
    password: secret
    name: active_policy
    state: present
  delegate_to: localhost

- name: Import and activate ASM policy in Role
  bigip_asm_policy:
    server: lb.mydomain.com
    user: admin
    password: secret
    name: new_asm_policy
    file: "{{ role_path }}/files/asm_policy.xml"
    active: yes
    state: present
  delegate_to: localhost

- name: Import ASM binary policy
  bigip_asm_policy:
    server: lb.mydomain.com
    user: admin
    password: secret
    name: new_asm_policy
    file: "/root/asm_policy.plc"
    active: yes
    state: present
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
  type: string
  sample: absent
file:
  description: Local path to ASM policy file.
  returned: changed
  type: string
  sample: /root/some_policy.xml
template:
  description: Name of the built-in ASM policy template
  returned: changed
  type: string
  sample: OWA Exchange 2007 (https)
name:
  description: Name of the ASM policy to be managed/created
  returned: changed
  type: string
  sample: Asm_APP1_Transparent
'''

import os
import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from distutils.version import LooseVersion

try:
    from library.module_utils.network.f5.bigip import HAS_F5SDK
    from library.module_utils.network.f5.bigip import F5Client
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import cleanup_tokens
    from library.module_utils.network.f5.common import fqdn_name
    from library.module_utils.network.f5.common import f5_argument_spec
    try:
        from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False
except ImportError:
    from ansible.module_utils.network.f5.bigip import HAS_F5SDK
    from ansible.module_utils.network.f5.bigip import F5Client
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import cleanup_tokens
    from ansible.module_utils.network.f5.common import fqdn_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    try:
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False


class Parameters(AnsibleF5Parameters):
    updatables = [
        'active'
    ]

    returnables = [
        'name', 'template', 'file', 'active'
    ]

    api_attributes = [
        'name', 'file', 'active'
    ]
    api_map = {
        'filename': 'file'
    }

    @property
    def template_link(self):
        if self._values['template_link'] is not None:
            return self._values['template_link']
        collection = self._templates_from_device()
        for resource in collection:
            if resource.name == self.template.upper():
                return dict(link=resource.selfLink)
        return None

    @property
    def full_path(self):
        return fqdn_name(self.name)

    def _templates_from_device(self):
        collection = self.client.api.tm.asm.policy_templates_s.get_collection()
        return collection

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

        try:
            if state == "present":
                changed = self.present()
            elif state == "absent":
                changed = self.absent()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        changes = self.changes.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        return result

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
        policies = self.client.api.tm.asm.policies_s.get_collection()
        if any(p.name == self.want.name and p.partition == self.want.partition for p in policies):
            return True
        return False

    def _file_is_missing(self):
        if self.want.template and self.want.file is None:
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
        task = self.apply_on_device()
        if self.wait_for_task(task):
            return True
        else:
            raise F5ModuleError('Apply policy task failed.')

    def wait_for_task(self, task):
        while True:
            task.refresh()
            if task.status in ['COMPLETED', 'FAILURE']:
                break
            time.sleep(1)
        if task.status == 'FAILURE':
            return False
        if task.status == 'COMPLETED':
            return True

    def update_on_device(self):
        params = self.changes.api_params()
        policies = self.client.api.tm.asm.policies_s.get_collection()
        name = self.want.name
        partition = self.want.partition
        resource = next((p for p in policies if p.name == name and p.partition == partition), None)
        if resource:
            if not params['active']:
                resource.modify(**params)

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
        policies = self.client.api.tm.asm.policies_s.get_collection()
        for policy in policies:
            if policy.name == self.want.name and policy.partition == self.want.partition:
                params = policy.attrs
                params.update(dict(self_link=policy.selfLink))
                return Parameters(params=params)
        raise F5ModuleError("The policy was not found")

    def import_to_device(self):
        self.client.api.tm.asm.file_transfer.uploads.upload_file(self.want.file)
        time.sleep(2)
        name = os.path.split(self.want.file)[1]
        tasks = self.client.api.tm.asm.tasks
        result = tasks.import_policy_s.import_policy.create(
            name=self.want.name,
            partition=self.want.partition,
            filename=name
        )
        return result

    def apply_on_device(self):
        tasks = self.client.api.tm.asm.tasks
        result = tasks.apply_policy_s.apply_policy.create(
            policyReference={'link': self.have.self_link}
        )
        return result

    def create_from_template_on_device(self):
        tasks = self.client.api.tm.asm.tasks
        result = tasks.import_policy_s.import_policy.create(
            name=self.want.name,
            partition=self.want.partition,
            policyTemplateReference=self.want.template_link
        )
        time.sleep(2)
        return result

    def create_on_device(self):
        result = self.client.api.tm.asm.policies_s.policy.create(
            name=self.want.name,
            partition=self.want.partition
        )
        return result

    def remove_from_device(self):
        policies = self.client.api.tm.asm.policies_s.get_collection()
        name = self.want.name
        partition = self.want.partition
        resource = next((p for p in policies if p.name == name and p.partition == partition), None)
        if resource:
            resource.delete()


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.client = kwargs.get('client', None)
        self.kwargs = kwargs

    def exec_module(self):
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
        version = self.client.api.tmos_version
        if LooseVersion(version) < LooseVersion('13.0.0'):
            return True
        else:
            return False


class V1Manager(BaseManager):
    def __init__(self, *args, **kwargs):
        client = kwargs.get('client', None)
        module = kwargs.get('module', None)
        super(V1Manager, self).__init__(client=client, module=module)
        self.want = V1Parameters(params=module.params, client=client)

    def create_from_file(self):
        self.import_to_device()
        self.remove_temp_policy_from_device()

    def create_from_template(self):
        self.create_from_template_on_device()

    def create_from_template_on_device(self):
        full_name = fqdn_name(self.want.partition, self.want.name)
        cmd = 'tmsh create asm policy {0} policy-template {1}'.format(full_name, self.want.template)
        self.client.api.tm.util.bash.exec_cmd(
            'run',
            utilCmdArgs='-c "{0}"'.format(cmd)
        )

    def remove_temp_policy_from_device(self):
        name = os.path.split(self.want.file)[1]
        tpath_name = '/var/config/rest/downloads/{0}'.format(name)
        self.client.api.tm.util.unix_rm.exec_cmd('run', utilCmdArgs=tpath_name)

    def import_to_device(self):
        self.client.api.shared.file_transfer.uploads.upload_file(self.want.file)
        time.sleep(2)
        name = os.path.split(self.want.file)[1]
        full_name = fqdn_name(self.want.partition, self.want.name)
        cmd = 'tmsh load asm policy {0} file /var/config/rest/downloads/{1}'.format(full_name, name)
        self.client.api.tm.util.bash.exec_cmd(
            'run',
            utilCmdArgs='-c "{0}"'.format(cmd)
        )
        return True


class V2Manager(BaseManager):
    def __init__(self, *args, **kwargs):
        client = kwargs.get('client', None)
        module = kwargs.get('module', None)
        super(V2Manager, self).__init__(client=client, module=module)
        self.want = V2Parameters(params=module.params, client=client)

    def create_from_template(self):
        task = self.create_from_template_on_device()
        if not task:
            return False
        if not self.wait_for_task(task):
            raise F5ModuleError('Import policy task failed.')

    def create_from_file(self):
        task = self.import_to_device()
        if not task:
            return False
        if not self.wait_for_task(task):
            raise F5ModuleError('Import policy task failed.')


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
            file=dict(),
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
    if not HAS_F5SDK:
        module.fail_json(msg="The python f5-sdk module is required")

    try:
        client = F5Client(**module.params)
        mm = ModuleManager(module=module, client=client)
        results = mm.exec_module()
        cleanup_tokens(client)
        module.exit_json(**results)
    except F5ModuleError as e:
        cleanup_tokens(client)
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
