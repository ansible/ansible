#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, 2017 Jasper Lievisse Adriaanse <j@jasper.la>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


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
        type: bool
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
    type: str
    sample: https://datasets.project-fifo.net
uuid:
    description: UUID for an image operated on.
    returned: When not managing an image source.
    type: str
    sample: 70e3ae72-96b6-11e6-9056-9737fd4d0764
state:
    description: State of the target, after execution.
    returned: success
    type: str
    sample: 'present'
'''

import re

from ansible.module_utils.basic import AnsibleModule

# Shortcut for the imgadm(1M) command. While imgadm(1M) supports a
# -E option to return any errors in JSON, the generated JSON does not play well
# with the JSON parsers of Python. The returned message contains '\n' as part of
# the stacktrace, which breaks the parsers.


class Imgadm(object):
    def __init__(self, module):
        self.module = module
        self.params = module.params
        self.cmd = module.get_bin_path('imgadm', required=True)
        self.changed = False
        self.uuid = module.params['uuid']

        # Since there are a number of (natural) aliases, prevent having to look
        # them up everytime we operate on `state`.
        if self.params['state'] in ['present', 'imported', 'updated']:
            self.present = True
        else:
            self.present = False

        # Perform basic UUID validation upfront.
        if self.uuid and self.uuid != '*':
            if not re.match('^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$', self.uuid, re.IGNORECASE):
                module.fail_json(msg='Provided value for uuid option is not a valid UUID.')

    # Helper method to massage stderr
    def errmsg(self, stderr):
        match = re.match(r'^imgadm .*?: error \(\w+\): (.*): .*', stderr)
        if match:
            return match.groups()[0]
        else:
            return 'Unexpected failure'

    def update_images(self):
        if self.uuid == '*':
            cmd = '{0} update'.format(self.cmd)
        else:
            cmd = '{0} update {1}'.format(self.cmd, self.uuid)

        (rc, stdout, stderr) = self.module.run_command(cmd)

        if rc != 0:
            self.module.fail_json(msg='Failed to update images: {0}'.format(self.errmsg(stderr)))

        # There is no feedback from imgadm(1M) to determine if anything
        # was actually changed. So treat this as an 'always-changes' operation.
        # Note that 'imgadm -v' produces unparseable JSON...
        self.changed = True

    def manage_sources(self):
        force = self.params['force']
        source = self.params['source']
        imgtype = self.params['type']

        cmd = '{0} sources'.format(self.cmd)

        if force:
            cmd += ' -f'

        if self.present:
            cmd = '{0} -a {1} -t {2}'.format(cmd, source, imgtype)
            (rc, stdout, stderr) = self.module.run_command(cmd)

            if rc != 0:
                self.module.fail_json(msg='Failed to add source: {0}'.format(self.errmsg(stderr)))

            # Check the various responses.
            # Note that trying to add a source with the wrong type is handled
            # above as it results in a non-zero status.

            regex = 'Already have "{0}" image source "{1}", no change'.format(imgtype, source)
            if re.match(regex, stdout):
                self.changed = False

            regex = 'Added "%s" image source "%s"' % (imgtype, source)
            if re.match(regex, stdout):
                self.changed = True
        else:
            # Type is ignored by imgadm(1M) here
            cmd += ' -d %s' % source
            (rc, stdout, stderr) = self.module.run_command(cmd)

            if rc != 0:
                self.module.fail_json(msg='Failed to remove source: {0}'.format(self.errmsg(stderr)))

            regex = 'Do not have image source "%s", no change' % source
            if re.match(regex, stdout):
                self.changed = False

            regex = 'Deleted ".*" image source "%s"' % source
            if re.match(regex, stdout):
                self.changed = True

    def manage_images(self):
        pool = self.params['pool']
        state = self.params['state']

        if state == 'vacuumed':
            # Unconditionally pass '--force', otherwise we're prompted with 'y/N'
            cmd = '{0} vacuum -f'.format(self.cmd)

            (rc, stdout, stderr) = self.module.run_command(cmd)

            if rc != 0:
                self.module.fail_json(msg='Failed to vacuum images: {0}'.format(self.errmsg(stderr)))
            else:
                if stdout == '':
                    self.changed = False
                else:
                    self.changed = True
        if self.present:
            cmd = '{0} import -P {1} -q {2}'.format(self.cmd, pool, self.uuid)

            (rc, stdout, stderr) = self.module.run_command(cmd)

            if rc != 0:
                self.module.fail_json(msg='Failed to import image: {0}'.format(self.errmsg(stderr)))

            regex = r'Image {0} \(.*\) is already installed, skipping'.format(self.uuid)
            if re.match(regex, stdout):
                self.changed = False

            regex = '.*ActiveImageNotFound.*'
            if re.match(regex, stderr):
                self.changed = False

            regex = 'Imported image {0}.*'.format(self.uuid)
            if re.match(regex, stdout.splitlines()[-1]):
                self.changed = True
        else:
            cmd = '{0} delete -P {1} {2}'.format(self.cmd, pool, self.uuid)

            (rc, stdout, stderr) = self.module.run_command(cmd)

            regex = '.*ImageNotInstalled.*'
            if re.match(regex, stderr):
                # Even if the 'rc' was non-zero (3), we handled the situation
                # in order to determine if there was a change.
                self.changed = False

            regex = 'Deleted image {0}'.format(self.uuid)
            if re.match(regex, stdout):
                self.changed = True


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

    imgadm = Imgadm(module)

    uuid = module.params['uuid']
    source = module.params['source']
    state = module.params['state']

    result = {'state': state}

    # Either manage sources or images.
    if source:
        result['source'] = source
        imgadm.manage_sources()
    else:
        result['uuid'] = uuid

        if state == 'updated':
            imgadm.update_images()
        else:
            # Make sure operate on a single image for the following actions
            if (uuid == '*') and (state != 'vacuumed'):
                module.fail_json(msg='Can only specify uuid as "*" when updating image(s)')
            imgadm.manage_images()

    result['changed'] = imgadm.changed
    module.exit_json(**result)


if __name__ == '__main__':
    main()
