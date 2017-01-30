#!/usr/bin/python

# (c) 2017, Alberto Murillo <alberto.murillo.silva@intel.com>
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

import os
from ansible.module_utils.basic import AnsibleModule


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: swupd
short_description: Manages bundles with I(swupd)
description:
    - "Manages bundles with the I(swupd) update manager, which is used by the
      Clear Linux Project for Intel Architecture"
version_added: "2.3"
author:
    - "Alberto Murillo (@albertomurillo)"
options:
    name:
        description:
            - Name of the bundle to install or remove.
        required: false
        default: null
        aliases: ['bundle']
    state:
        description:
            - Indicates the desired bundle state. C(present) ensures the bundle
              is installed while C(absent) ensures the bundle is not installed.
        required: false
        default: present
        choices: ["present", "absent"]
    update:
        description:
            - Updates the OS to the latest version
        required: false
        default: no
        aliases: ['upgrade']
        choices: ['yes', 'no']
    verify:
        description:
            - Verify file system
        required: false
        default: null
        choices: ['yes', 'no']
    manifest:
        description:
            - Manifest to verify against to
        required: false
        default: null
        aliases: ['release', 'version']
    format:
        description:
            - The format suffix for version file downloads
        required: false
        default: null
    url:
        description:
            - Overrides both I(contenturl) and I(versionurl)
        required: false
        default: null
    contenturl:
        description:
            - url for content file download
        required: false
        default: null
    versionurl:
        description:
            - url for version string download
        required: false
        default: null
'''

EXAMPLES = '''
- name Update the OS to the latest version
  swupd:
    update: yes

- name: Installs the "foo" bundle
  swupd:
    name: foo
    state: present

- name: Removes the "foo" bundle
  swupd:
    name: foo
    state: absent

- name: Check integrity of filesystem
  swupd:
    verify: yes

- name: Downgrade OS to release 12920
  swupd:
    verify: yes
    manifest: 12920
'''

FILES_NOT_MATCH = "files did not match"
FILES_REPLACED = "missing files were replaced"
FILES_FIXED = "files were fixed"
FILES_DELETED = "files were deleted"


def _get_cmd(module, command):
    p = module.params
    cmd = "%s %s" % (SWUPD_CMD, command)

    if p["format"]:
        cmd += " --format=%s" % (p["format"])
    if p["manifest"]:
        cmd += " --manifest=%s" % (p["manifest"])
    if p["url"]:
        cmd += " --url=%s" % (p["url"])
    else:
        if p["contenturl"] and command != "check-update":
            cmd += " --contenturl=%s" % (p["contenturl"])
        if p["versionurl"]:
            cmd += " --versionurl=%s" % (p["versionurl"])

    return cmd


def _is_bundle_installed(module, bundle):
    try:
        os.stat("/usr/share/clear/bundles/%s" % bundle)
    except OSError:
        return False

    return True


def _needs_update(module):
    cmd = _get_cmd(module, "check-update")
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)

    if rc == 0:
        return True

    if rc == 1:
        return False

    module.fail_json(msg="Unkown Error", stdout=stdout, stderr=stderr)


def _needs_verify(module):
    cmd = _get_cmd(module, "verify")
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)

    if rc != 0:
        module.fail_json(msg="Unkown Error", stdout=stdout, stderr=stderr)

    if FILES_NOT_MATCH in stdout:
        return True

    return False


def swupd_install(module, bundle):
    """Installs a bundle with `swupd bundle-add bundle`"""
    if module.check_mode:
        module.exit_json(changed=not _is_bundle_installed(module, bundle))

    if _is_bundle_installed(module, bundle):
        module.exit_json(changed=False, msg="Bundle %s is already installed" % bundle)

    cmd = _get_cmd(module, "bundle-add %s" % bundle)
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)

    if rc == 0:
        module.exit_json(changed=True, msg="Bundle %s installed" % bundle, stdout=stdout, stderr=stderr)

    if rc == 18:
        module.exit_json(Changed=False, msg="Bundle name %s is invalid" % bundle, stdout=stdout, stderr=stderr)

    module.fail_json(msg="Unkown Error", stdout=stdout, stderr=stderr)


def swupd_remove(module, bundle):
    """Removes a bundle with `swupd bundle-remove bundle`"""
    if module.check_mode:
        module.exit_json(changed=_is_bundle_installed(module, bundle))

    if not _is_bundle_installed(module, bundle):
        module.exit_json(changed=False, msg="Bundle %s not installed" % bundle)

    cmd = _get_cmd(module, "bundle-remove %s" % bundle)
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)

    if rc == 0:
        module.exit_json(changed=True, msg="Bundle %s removed" % bundle, stdout=stdout, stderr=stderr)

    module.fail_json(msg="Unkown Error", stdout=stdout, stderr=stderr)


def swupd_update(module):
    """Updates the os with `swupd update`"""
    if module.check_mode:
        module.exit_json(changed=_needs_update(module))

    if not _needs_update(module):
        module.exit_json(changed=False, msg="There are no updates available")

    cmd = _get_cmd(module, "update")
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)

    if rc == 0:
        module.exit_json(changed=True, msg="Update successful", stdout=stdout, stderr=stderr)

    module.fail_json(msg="Unkown Error", stdout=stdout, stderr=stderr)


def swupd_verify(module):
    """Verifies filesystem agains specified or current version"""
    if module.check_mode:
        module.exit_json(changed=_needs_verify(module))

    if not _needs_verify(module):
        module.exit_json(changed=False, msg="No files where changed")

    cmd = _get_cmd(module, "verify --fix")
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)

    if rc == 0 and (FILES_REPLACED in stdout or FILES_FIXED in stdout or FILES_DELETED in stdout):
        module.exit_json(changed=True, msg="Fix successful", stdout=stdout, stderr=stderr)

    module.fail_json(msg="Unkown Error", stdout=stdout, stderr=stderr)


def main():
    """The main function."""
    module = AnsibleModule(
        argument_spec=dict(
            contenturl=dict(default=None, type='str'),
            format=dict(default=None, type='str'),
            manifest=dict(default=None, aliases=['release', 'version'], type='int'),
            name=dict(aliases=['bundle'], type='str'),
            state=dict(default='present', choices=['present', 'absent']),
            update=dict(default='no', aliases=['bundle'], type='bool'),
            url=dict(default=None, type='str'),
            verify=dict(default='no', type='bool'),
            versionurl=dict(default=None, type='str'),
        ),
        required_one_of=[['name', 'update', 'verify']],
        mutually_exclusive=[['name', 'update', 'verify']],
        supports_check_mode=True
    )

    p = module.params

    global SWUPD_CMD
    SWUPD_CMD = module.get_bin_path("swupd", False)

    if not SWUPD_CMD:
        module.fail_json(msg="Could not find swupd.")

    if p['update']:
        swupd_update(module)

    if p['verify']:
        swupd_verify(module)

    if p['state'] == "present":
        swupd_install(module, p['name'])

    if p['state'] == "absent":
        swupd_remove(module, p['name'])


if __name__ == '__main__':
    main()
