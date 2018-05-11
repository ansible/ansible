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
module: bigip_iapp_template
short_description: Manages TCL iApp templates on a BIG-IP
description:
  - Manages TCL iApp templates on a BIG-IP. This module will allow you to
    deploy iApp templates to the BIG-IP and manage their lifecycle. The
    conventional way to use this module is to import new iApps as needed
    or by extracting the contents of the iApp archive that is provided at
    downloads.f5.com and then importing all the iApps with this module.
    This module can also update existing iApps provided that the source
    of the iApp changed while the name stayed the same. Note however that
    this module will not reconfigure any services that may have been
    created using the C(bigip_iapp_service) module. iApps are normally
    not updated in production. Instead, new versions are deployed and then
    existing services are changed to consume that new template. As such,
    the ability to update templates in-place requires the C(force) option
    to be used.
version_added: 2.4
options:
  force:
    description:
      - Specifies whether or not to force the uploading of an iApp. When
        C(yes), will force update the iApp even if there are iApp services
        using it. This will not update the running service though. Use
        C(bigip_iapp_service) to do that. When C(no), will update the iApp
        only if there are no iApp services using the template.
    type: bool
  name:
    description:
      - The name of the iApp template that you want to delete. This option
        is only available when specifying a C(state) of C(absent) and is
        provided as a way to delete templates that you may no longer have
        the source of.
  content:
    description:
      - Sets the contents of an iApp template directly to the specified
        value. This is for simple values, but can be used with lookup
        plugins for anything complex or with formatting. C(content) must
        be provided when creating new templates.
  state:
    description:
      - Whether the iApp template should exist or not.
    default: present
    choices:
      - present
      - absent
  partition:
    description:
      - Device partition to manage resources on.
    default: Common
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Add the iApp contained in template iapp.tmpl
  bigip_iapp_template:
    content: "{{ lookup('template', 'iapp.tmpl') }}"
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
  delegate_to: localhost

- name: Update a template in place
  bigip_iapp_template:
    content: "{{ lookup('template', 'iapp-new.tmpl') }}"
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
  delegate_to: localhost

- name: Update a template in place that has existing services created from it.
  bigip_iapp_template:
    content: "{{ lookup('template', 'iapp-new.tmpl') }}"
    force: yes
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
  delegate_to: localhost
'''

RETURN = r'''
# only common fields returned
'''

import re
import uuid

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from library.module_utils.network.f5.bigip import HAS_F5SDK
    from library.module_utils.network.f5.bigip import F5Client
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import cleanup_tokens
    from library.module_utils.network.f5.common import f5_argument_spec
    try:
        from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
        from f5.utils.iapp_parser import NonextantTemplateNameException
    except ImportError:
        HAS_F5SDK = False
except ImportError:
    from ansible.module_utils.network.f5.bigip import HAS_F5SDK
    from ansible.module_utils.network.f5.bigip import F5Client
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import cleanup_tokens
    from ansible.module_utils.network.f5.common import f5_argument_spec
    try:
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
        from f5.utils.iapp_parser import NonextantTemplateNameException
    except ImportError:
        HAS_F5SDK = False

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


class Parameters(AnsibleF5Parameters):
    api_attributes = []

    returnables = []

    @property
    def name(self):
        if self._values['name']:
            return self._values['name']
        if self._values['content']:
            try:
                name = self._get_template_name()
                return name
            except NonextantTemplateNameException:
                raise F5ModuleError(
                    "No template name was found in the template"
                )
        return None

    @property
    def content(self):
        if self._values['content'] is None:
            return None
        result = self._squash_template_name_prefix()
        if self._values['name']:
            result = self._replace_template_name(result)
        return result

    @property
    def checksum(self):
        return self._values['tmplChecksum']

    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result

    def _squash_template_name_prefix(self):
        """Removes the template name prefix

        The IappParser in the SDK treats the partition prefix as part of
        the iApp's name. This method removes that partition from the name
        in the iApp so that comparisons can be done properly and entries
        can be created properly when using REST.

        :return string
        """
        pattern = r'sys\s+application\s+template\s+/Common/'
        replace = 'sys application template '
        return re.sub(pattern, replace, self._values['content'])

    def _replace_template_name(self, template):
        """Replaces template name at runtime

        To allow us to do the switch-a-roo with temporary templates and
        checksum comparisons, we need to take the template provided to us
        and change its name to a temporary value so that BIG-IP will create
        a clone for us.

        :return string
        """
        pattern = r'sys\s+application\s+template\s+[^ ]+'
        replace = 'sys application template {0}'.format(self._values['name'])
        return re.sub(pattern, replace, template)

    def _get_template_name(self):
        # There is a bug in the iApp parser in the F5 SDK that prevents us from
        # using it in all cases to get the name of an iApp. So we'll use this
        # pattern for now and file a bug with the F5 SDK
        pattern = r'sys\s+application\s+template\s+(?P<path>\/[^\{}"\'*?|#]+\/)?(?P<name>[^\{}"\'*?|#]+)'
        matches = re.search(pattern, self.content)
        try:
            result = matches.group('name').strip()
        except IndexError:
            result = None
        if result:
            return result
        raise NonextantTemplateNameException


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.have = None
        self.want = Parameters(params=self.module.params)
        self.changes = Parameters()

    def exec_module(self):
        result = dict()
        changed = False
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

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def update(self):
        self.have = self.read_current_from_device()

        if not self.templates_differ():
            return False

        if not self.want.force and self.template_in_use():
            return False

        if self.module.check_mode:
            return True

        self._remove_iapp_checksum()
        # The same process used for creating (load) can be used for updating
        self.create_on_device()
        self._generate_template_checksum_on_device()
        return True

    def template_in_use(self):
        collection = self.client.api.tm.sys.application.services.get_collection()
        fullname = '/{0}/{1}'.format(self.want.partition, self.want.name)
        for resource in collection:
            if resource.template == fullname:
                return True
        return False

    def read_current_from_device(self):
        self._generate_template_checksum_on_device()
        resource = self.client.api.tm.sys.application.templates.template.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result = resource.attrs
        return Parameters(params=result)

    def absent(self):
        changed = False
        if self.exists():
            changed = self.remove()
        return changed

    def exists(self):
        result = self.client.api.tm.sys.application.templates.template.exists(
            name=self.want.name,
            partition=self.want.partition
        )
        return result

    def _remove_iapp_checksum(self):
        """Removes the iApp tmplChecksum

        This is required for updating in place or else the load command will
        fail with a "AppTemplate ... content does not match the checksum"
        error.

        :return:
        """
        resource = self.client.api.tm.sys.application.templates.template.load(
            name=self.want.name,
            partition=self.want.partition
        )
        resource.modify(tmplChecksum=None)

    def templates_differ(self):
        # BIG-IP can generate checksums of iApps, but the iApp needs to be
        # on the box to do this. Additionally, the checksum is MD5, but it
        # is not an MD5 of the entire content of the template. Instead, it
        # is a hash of some portion of the template that is unknown to me.
        #
        # The code below is responsible for uploading the provided template
        # under a unique name and creating a checksum for it so that that
        # checksum can be compared to the one of the existing template.
        #
        # Using this method we can compare the checksums of the existing
        # iApp and the iApp that the user is providing to the module.
        backup = self.want.name

        # Override whatever name may have been provided so that we can
        # temporarily create a new template to test checksums with
        self.want.update({
            'name': 'ansible-{0}'.format(str(uuid.uuid4()))
        })

        # Create and remove temporary template
        temp = self._get_temporary_template()

        # Set the template name back to what it was originally so that
        # any future operations only happen on the real template.
        self.want.update({
            'name': backup
        })
        if temp.checksum != self.have.checksum:
            return True
        return False

    def _get_temporary_template(self):
        self.create_on_device()
        temp = self.read_current_from_device()
        self.remove_from_device()
        return temp

    def _generate_template_checksum_on_device(self):
        generate = 'tmsh generate sys application template {0} checksum'.format(
            self.want.name
        )
        self.client.api.tm.util.bash.exec_cmd(
            'run',
            utilCmdArgs='-c "{0}"'.format(generate)
        )

    def create(self):
        if self.module.check_mode:
            return True
        self.create_on_device()
        if self.exists():
            return True
        else:
            raise F5ModuleError("Failed to create the iApp template")

    def create_on_device(self):
        remote_path = "/var/config/rest/downloads/{0}".format(self.want.name)
        load_command = 'tmsh load sys application template {0}'.format(remote_path)

        template = StringIO(self.want.content)

        upload = self.client.api.shared.file_transfer.uploads
        upload.upload_stringio(template, self.want.name)
        output = self.client.api.tm.util.bash.exec_cmd(
            'run',
            utilCmdArgs='-c "{0}"'.format(load_command)
        )

        if hasattr(output, 'commandResult'):
            result = output.commandResult
            if 'Syntax Error' in result:
                raise F5ModuleError(output.commandResult)

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the iApp template")
        return True

    def remove_from_device(self):
        resource = self.client.api.tm.sys.application.templates.template.load(
            name=self.want.name,
            partition=self.want.partition
        )
        resource.delete()


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(),
            state=dict(
                default='present',
                choices=['present', 'absent']
            ),
            force=dict(
                type='bool'
            ),
            content=dict(),
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
        supports_check_mode=spec.supports_check_mode
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
