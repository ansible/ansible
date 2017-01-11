#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Jasper Lievisse Adriaanse <j@jasper.la>
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
#

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: imgadm
short_description: Manage SmartOS images
description:
    - Manage SmartOS virtual machine images through imgadm(1M)
version_added: "2.3"
author: Jasper Lievisse Adriaanse (@jasperla)
options:
    force:
        required: false
        choices: [ yes, no ]
        description:
          - Force a given operation (where supported by imgadm(1M)).
    pool:
        required: false
        default: zones
        description:
          - zpool to import to or delete images from.
    source:
        required: false
        description:
          - URI for the image source.
    state:
        required: true
        choices: [ present, absent, deleted, imported, updated, vacuumed ]
        description:
          - State the object operated on should be in. C(imported) is an alias for
            for C(present) and C(deleted) for C(absent). When set to C(vacuumed)
            and C(uuid) to C(*), it will remove all unused images.
    type:
        required: false
        choices: [ imgapi, docker, dsapi ]
        default: imgapi
        description:
          - Type for image sources.
    uuid:
        required: false
        description:
          - Image UUID. Can either be a full UUID or C(*) for all images.
requirements:
    - python >= 2.6
'''

EXAMPLES = '''
- name: Import an image
  imgadm:
    uuid: '70e3ae72-96b6-11e6-9056-9737fd4d0764'
    state: imported

- name: Delete an image
  imgadm:
    uuid: '70e3ae72-96b6-11e6-9056-9737fd4d0764'
    state: deleted

- name: Update all images
  imgadm:
    uuid: '*'
    state: updated

- name: Update a single image
  imgadm:
    uuid: '70e3ae72-96b6-11e6-9056-9737fd4d0764'
    state: updated

- name: Add a source
  imgadm:
    source: 'https://datasets.project-fifo.net'
    state: present

- name: Add a Docker source
  imgadm:
    source: 'https://docker.io'
    type: docker
    state: present

- name: Remove a source
  imgadm:
    source: 'https://docker.io'
    state: absent
'''

RETURN = '''
source:
    description: Source that is managed.
    returned: When not managing an image.
    type: string
    sample: https://datasets.project-fifo.net
uuid:
    description: UUID for an image operated on.
    returned: When not managing an image source.
    type: string
    sample: 70e3ae72-96b6-11e6-9056-9737fd4d0764
state:
    description: State of the target, after execution.
    returned: success
    type: string
    sample: 'present'
'''

from ansible.module_utils.basic import AnsibleModule
import re

# Shortcut for the imgadm(1M) command. While imgadm(1M) supports a
# -E option to return any errors in JSON, the generated JSON does not play well
# with the JSON parsers of Python. The returned message contains '\n' as part of
# the stacktrace, which breaks the parsers.
IMGADM = 'imgadm'


# Helper method to massage stderr
def errmsg(stderr):
    match = re.match('^imgadm .*?: error \(\w+\): (.*): .*', stderr)
    if match:
        return match.groups()[0]
    else:
        return 'Unexpected failure'


def update_images(module):
    uuid = module.params['uuid']
    cmd = IMGADM + ' update'

    if uuid != '*':
        cmd = '{0} {1}'.format(cmd, uuid)

    (rc, stdout, stderr) = module.run_command(cmd)

    # There is no feedback from imgadm(1M) to determine if anything
    # was actually changed. So treat this as an 'always-changes' operation.
    # Note that 'imgadm -v' produces unparseable JSON...
    return rc, stdout, errmsg(stderr), True


def manage_sources(module, present):
    force = module.params['force']
    source = module.params['source']
    imgtype = module.params['type']

    cmd = IMGADM + ' sources'

    if force:
        cmd += ' -f'

    if present:
        cmd = '{0} -a {1} -t {2}'.format(cmd, source, imgtype)
        (rc, stdout, stderr) = module.run_command(cmd)

        # Check the various responses.
        # Note that trying to add a source with the wrong type is handled
        # above as it results in a non-zero status.
        changed = True

        regex = 'Already have "{0}" image source "{1}", no change'.format(imgtype, source)
        if re.match(regex, stdout):
            changed = False

        regex = 'Added "%s" image source "%s"' % (imgtype, source)
        if re.match(regex, stdout):
            changed = True

        # Fallthrough, assume changes
        return (rc, stdout, errmsg(stderr), changed)
    else:
        # Type is ignored by imgadm(1M) here
        cmd += ' -d %s' % (source)
        (rc, stdout, stderr) = module.run_command(cmd)

        changed = True

        regex = 'Do not have image source "%s", no change' % (source)
        if re.match(regex, stdout):
            changed = False

        regex = 'Deleted ".*" image source "%s"' % (source)
        if re.match(regex, stdout):
            changed = True

        return (rc, stdout, errmsg(stderr), changed)


def manage_images(module, present):
    uuid = module.params['uuid']
    pool = module.params['pool']
    state = module.params['state']

    if state == 'vacuumed':
        # Unconditionally pass '--force', otherwise we're prompted with 'y/N'
        cmd = '{0} vacuum -f'.format(IMGADM)

        (rc, stdout, stderr) = module.run_command(cmd)

        if rc == 0:
            if stdout == '':
                changed = False
            else:
                changed = True

        return (rc, stdout, errmsg(stderr), changed)

    if present:
        cmd = '{0} import -P {1} -q {2}'.format(IMGADM, pool, uuid)

        changed = False
        (rc, stdout, stderr) = module.run_command(cmd)

        regex = 'Image {0} \(.*\) is already installed, skipping'.format(uuid)
        if re.match(regex, stdout):
            changed = False

        regex = '.*ActiveImageNotFound.*'
        if re.match(regex, stderr):
            changed = False

        regex = 'Imported image {0}'.format(uuid)
        if re.match(regex, stdout):
            changed = True
    else:
        cmd = '{0} delete -P {1} {2}'.format(IMGADM, pool, uuid)

        changed = False
        (rc, stdout, stderr) = module.run_command(cmd)

        regex = '.*ImageNotInstalled.*'
        if re.match(regex, stderr):
            # Even if the 'rc' was non-zero (3), we handled the situation
            # in order to determine if there was a change, so set rc to success.
            rc = 0
            changed = False

        regex = 'Deleted image {0}'.format(uuid)
        if re.match(regex, stdout):
            changed = True

    return (rc, stdout, errmsg(stderr), changed)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            force=dict(default=None, type='bool'),
            pool=dict(default='zones'),
            source=dict(default=None),
            state=dict(default=None, required=True, choices=['present', 'absent', 'deleted', 'imported', 'updated', 'vacuumed']),
            type=dict(default='imgapi', choices=['imgapi', 'docker', 'dsapi']),
            uuid=dict(default=None)
        ),
        # This module relies largely on imgadm(1M) to enforce idempotency, which does not
        # provide a "noop" (or equivalent) mode to do a dry-run.
        supports_check_mode=False,
    )

    uuid = module.params['uuid']
    source = module.params['source']
    state = module.params['state']

    # Since there are a number of (natural) aliases, prevent having to look
    # them up everytime we operate on `state`.
    if state in ['present', 'imported', 'updated']:
        present = True
    else:
        present = False

    stderr = stdout = ''
    rc = 0
    result = {'state': state}
    changed = False

    # Perform basic UUID validation upfront.
    if uuid and uuid != '*':
        if not re.match('^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$', uuid, re.IGNORECASE):
            module.fail_json(msg='Provided value for uuid option is not a valid UUID.')

    # Either manage sources or images.
    if module.params['source']:
        (rc, stdout, stderr, changed) = manage_sources(module, present)
        result['source'] = source
    else:
        result['uuid'] = uuid

        if state == 'updated':
            (rc, stdout, stderr, changed) = update_images(module)
        else:
            # Make sure operate on a single image for the following actions
            if (uuid == '*') and (state != 'vacuumed'):
                module.fail_json(msg='Can only specify uuid as "*" when updating image(s)')

            (rc, stdout, stderr, changed) = manage_images(module, present)

    if rc != 0:
        if stderr:
            module.fail_json(msg=stderr)
        else:
            module.fail_json(msg=stdout)

    result['changed'] = changed

    module.exit_json(**result)


if __name__ == '__main__':
    main()
