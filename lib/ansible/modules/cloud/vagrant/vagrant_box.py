#!/usr/bin/python
# coding: utf-8 -*-

# Copyright (c), Chafik Belhaoues  <chafik.bel@gmail.com>, 2017
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: vagrant_box
short_description: Manage Vagrant boxes
version_added: "2.5"
author: "Chafik Belhaoues (@africanzoe)"
description:
   - This module can add|remove|update a Vagrant box on a target host.
options:
    box:
      description:
        - The name of the box to be managed, it could be a path to a file, URL or shorthand name from Vagrant cloud.
      aliases: ['path', 'url']
      required: true
      default: None
    state:
      description:
        - Indicate the desired state of the box
      choices: ['present', 'absent', 'updated']
      required: false
      default: present
    force:
      description:
        - Specify wether to force the add or remove actions.
      required: false
      default: false
    version:
      description:
        - Specify the version of the managed box.
      required: false
      default: latest
      N.B: please consider using an explicit version with the state "absent".
    provider:
      description:
        - Specify the provider for the box.
      choices: ['virtualbox', 'libvirt', 'hyperv', 'vmware_desktop']
      required: false
      default: "virtualbox"
    insecure:
      description:
        - Indicate that the SSL certificates will not be verified if the URL is an HTTPS URL.
      required: false
      default: false
    trust_location:
      description:
        - Indicate wether to trust 'Location' header from HTTP redirects and use the same credentials for subsequent urls as for the initial one or not.
      required: false
      default: false
    cacert:
      description:
        - The path on the target host to the FILE that contains CA certificate for SSL download.
      required: false
      default: false
    capath:
      description:
        - The path on the target host to the DIRECTORY for the CA used to verify the peer.
      required: false
      default: false
    cert:
      description:
        - The path on the target host to the a client certificate to use when downloading the box, if necessary.
      required: false
      default: false
    name:
      description:
        - The name to give to the box if added from a file.
        - When adding a box from a catalog, the name is included in the catalog entry and should not be specified.
      required: false
      default: false
    checksum:
      description:
        - The checksum for the box that is downloaded.
      required: false
      default: false
    checksum_type:
      description:
        - The hash algorithm used for the checksum.
      choices: ['md5', 'sha1', 'sha256']
      required: false
      default: sha256
'''
EXAMPLES = '''
---
- name: Add Debian 9 box
  vagrant_box:
    box: "debian/stretch64"
    state: "present"
    provider: "virtualbox"
    version: "9.2.0"
    force: false

- name: Remove Ubuntu xenial64 box
  vagrant_box:
    box: "ubuntu/xenial64"
    state: "absent"
    provider: "virtualbox"
    version: "20170914.2.0"

- name: Update Centos 7 box
  vagrant_box:
    box: "centos/7"
    state: "updated"
    provider: "virtualbox"
'''

RETURN = '''
changed:
    description: True if the action is performed successfuly and made the change
    type: bool
    returned: always
rc:
    description: exit code of the module
    type: bool
    returned: always
'''

import os
import re

from ansible.module_utils.basic import AnsibleModule


class VagrantBox:
    def __init__(self, module):
        self.module = module
        self.changed = False
        self.box = module.params.get('box')
        self.state = module.params.get('state')
        self.force = module.params.get('force')
        self.version = module.params.get('version')
        self.provider = module.params.get('provider')
        self.insecure = module.params.get('insecure')
        self.trust_location = module.params.get('trust_location')
        self.cacert = module.params.get('cacert')
        self.capath = module.params.get('capath')
        self.cert = module.params.get('cert')
        self.name = module.params.get('name')
        self.checksum = module.params.get('checksum')
        self.checksum_type = module.params.get('checksum_type')

    def ispresent(self):
        cmd = "vagrant box list"
        rc, out, err = self.module.run_command(cmd)
        if self.version is not "latest":
            result = re.search('%s[ \t]*\(%s, %s\)' % (self.box, self.provider, self.version), out)

            if result:
                return True
            else:
                return False

    def add(self):
        if self.ispresent() and not self.force:
            self.module.exit_json(changed=False, stdout="The box %s version: %s for provider: %s already exists" % (self.box, self.version, self.provider))

        opts_list = ['--clean']
        opts_dict = dict()
        # options only that DO NOT need a value
        if self.force:
            opts_list.append('--force')
        if self.insecure:
            opts_list.append('--insecure')
        if self.trust_location:
            opts_list.append('--location-trusted')

        # options that NEED a value
        opts_dict['--provider'] = self.provider
        if self.cacert is not None:
            opts_dict['--cacert'] = self.cacert
        if self.capath is not None:
            opts_dict['--capath'] = self.capath
        if self.cert is not None:
            opts_dict['--cert'] = self.cert
        if self.version is not "latest":
            opts_dict['--box-version'] = self.version

        # conditional options, they are added ONLY IF the box is a filename
        if os.path.exists(self.box):
            if self.name is not None:
                opts_dict['--name'] = self.name
            if self.checksum is not None:
                opts_dict['--checksum'] = self.checksum
            opts_dict['--checksum-type'] = self.checksum_type

        if opts_dict:
            for k, v in opts_dict.items():
                opts_list.append(str(k) + " " + str(v))

        cmd = "vagrant box add %s %s" % (self.box, " ".join(opts_list))
        rc, out, err = self.module.run_command(cmd)

        if rc == 0:
            self.module.exit_json(changed=True, rc=rc, stdout=out, stderr=err)
        elif "already exists" in err:
            self.module.exit_json(changed=False, stdout="The box %s version: %s for provider: %s already exists" % (self.box, self.version, self.provider))
        else:
            self.module.fail_json(rc=rc, stdout=out, stderr=err)

    def delete(self):
        if not self.ispresent():
            self.module.exit_json(changed=False, stdout="The box %s version: %s for provider: %s already removed" % (self.box, self.version, self.provider))

        opts_list = []
        if self.force:
            opts_list.append('--force')
        if self.provider:
            opts_list.append('--provider %s' % self.provider)
        if self.version is not "latest":
            opts_list.append('--box-version "%s"' % self.version)

        cmd = "vagrant box remove %s %s" % (self.box, " ".join(opts_list))
        rc, out, err = self.module.run_command(cmd)

        if rc == 0:
            self.module.exit_json(changed=True, rc=rc, stdout=out, stderr=err)
        elif "interface with the UI" in err:
            self.module.fail_json(msg="The box %s is still in use by at least one Vagrant environment, use 'force' flag to force the deletion" % self.box)
        else:
            self.module.fail_json(msg=err)

    def update(self):
        if not self.ispresent() and self.version is not "latest":
            self.module.fail_json(msg="The box %s version: %s for provider: %s does not exist" % (self.box, self.version, self.provider))

        cmd = "vagrant box update --box %s --provider %s" % (self.box, self.provider)
        rc, out, err = self.module.run_command(cmd)

        if "is running the latest version" in out:
            self.module.exit_json(changed=False, rc=rc, stdout=out, stderr=err)
        elif rc == 0:
            self.module.exit_json(changed=True, rc=rc, stdout=out, stderr=err)
        else:
            self.module.fail_json(msg=err)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            box=dict(required=True, aliases=['path', 'url'], default=None),
            state=dict(required=False, choices=['present', 'absent', 'updated'], default="present"),
            force=dict(required=False, default=False, type='bool'),
            version=dict(required=False, default="latest"),
            provider=dict(required=False, choices=['hyperv', 'libvirt', 'virtualbox', 'vmware_desktop'], default="virtualbox"),
            insecure=dict(required=False, default=False, type='bool'),
            trust_location=dict(required=False, default=False, type='bool'),
            cacert=dict(required=False, default=None, type='path'),
            capath=dict(required=False, default=None, type='path'),
            cert=dict(required=False, default=None, type='path'),
            name=dict(required=False, default=None),
            checksum=dict(required=False, default=None),
            checksum_type=dict(required=False, choices=['md5', 'sha1', 'sha256'], default="sha256"),
        ),
        supports_check_mode=False,
    )

    vbox = VagrantBox(module)
    state = module.params.get('state')
    if state == "present":
        vbox.add()
    elif state == "absent":
        vbox.delete()
    else:
        vbox.update()

if __name__ == '__main__':
    main()
