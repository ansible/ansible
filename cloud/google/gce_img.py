#!/usr/bin/python
# Copyright 2015 Google Inc. All Rights Reserved.
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

"""An Ansible module to utilize GCE image resources."""

import sys

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.gce import *

try:
  from libcloud.compute.types import Provider
  from libcloud.compute.providers import get_driver
  from libcloud.common.google import GoogleBaseError
  from libcloud.common.google import ResourceNotFoundError
  _ = Provider.GCE
except ImportError:
  print('failed=True '
        "msg='libcloud with GCE support is required for this module.'")
  sys.exit(1)

DOCUMENTATION = '''
---
module: gce_img
short_description: utilize GCE image resources
description:
    - This module can create and delete GCE private images from gzipped
      compressed tarball containing raw disk data or from existing detached
      disks in any zone. U(https://cloud.google.com/compute/docs/images)
options:
  name:
    description:
      - the name of the image to create
    required: true
    default: null
    aliases: []
  source:
    description:
      - the source disk or the Google Cloud Storage URI to create the image from
    required: false
    default: null
    aliases: []
  state:
    description:
      - desired state of the image
    required: false
    default: "present"
    choices: ["active", "present", "absent", "deleted"]
    aliases: []
  zone:
    description:
      - the zone of the disk specified by source
    required: false
    default: "us-central1-a"
    aliases: []
  service_account_email:
    version_added: "1.6"
    description:
      - service account email
    required: false
    default: null
    aliases: []
  pem_file:
    version_added: "1.6"
    description:
      - path to the pem file associated with the service account email
    required: false
    default: null
    aliases: []
  project_id:
    version_added: "1.6"
    description:
      - your GCE project ID
    required: false
    default: null
    aliases: []

requirements: [ "libcloud" ]
author: Peter Tan <ptan@google.com>
'''

EXAMPLES = '''
# Create an image named test-image from the disk 'test-disk' in zone us-central1-a.
- gce_img:
    name: test-image
    source: test-disk
    zone: us-central1-a
    state: present

# Delete an image named test-image in zone us-central1-a.
- gce_img:
    name: test-image
    zone: us-central1-a
    state: deleted
'''


def main():
  module = AnsibleModule(
      argument_spec=dict(
          name=dict(required=True),
          source=dict(),
          state=dict(default='present'),
          zone=dict(default='us-central1-a'),
          service_account_email=dict(),
          pem_file=dict(),
          project_id=dict(),
      )
  )

  gce = gce_connect(module)

  name = module.params.get('name')
  source = module.params.get('source')
  state = module.params.get('state')
  zone = module.params.get('zone')
  changed = False

  try:
    image = gce.ex_get_image(name)
  except GoogleBaseError, e:
    module.fail_json(msg=str(e), changed=False)

  # user wants to create an image.
  if state in ['active', 'present'] and not image:
    if not source:
      module.fail_json(msg='Must supply a source', changed=False)

    if source.startswith('https://storage.googleapis.com'):
      # source is a Google Cloud Storage URI
      volume = source
    else:
      try:
        volume = gce.ex_get_volume(source, zone)
      except ResourceNotFoundError:
        module.fail_json(msg='Disk %s not found in zone %s' % (source, zone),
                         changed=False)
      except GoogleBaseError, e:
        module.fail_json(msg=str(e), changed=False)

    try:
      image = gce.ex_create_image(name, volume)
      changed = True
    except GoogleBaseError, e:
      module.fail_json(msg=str(e), changed=False)

  # user wants to delete the image.
  if state in ['absent', 'deleted'] and image:
    try:
      gce.ex_delete_image(image)
      changed = True
    except GoogleBaseError, e:
      module.fail_json(msg=str(e), changed=False)

  module.exit_json(changed=changed, name=name)
  sys.exit(0)

main()
