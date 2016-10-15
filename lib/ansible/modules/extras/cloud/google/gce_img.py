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

DOCUMENTATION = '''
---
module: gce_img
version_added: "1.9"
short_description: utilize GCE image resources
description:
    - This module can create and delete GCE private images from gzipped
      compressed tarball containing raw disk data or from existing detached
      disks in any zone. U(https://cloud.google.com/compute/docs/images)
options:
  name:
    description:
      - the name of the image to create or delete
    required: true
    default: null
  description:
    description:
      - an optional description
    required: false
    default: null
  family:
    description:
      - an optional family name
    required: false
    default: null
    version_added: "2.2"
  source:
    description:
      - the source disk or the Google Cloud Storage URI to create the image from
    required: false
    default: null
  state:
    description:
      - desired state of the image
    required: false
    default: "present"
    choices: ["present", "absent"]
  zone:
    description:
      - the zone of the disk specified by source
    required: false
    default: "us-central1-a"
  timeout:
    description:
      - timeout for the operation
    required: false
    default: 180
    version_added: "2.0"
  service_account_email:
    description:
      - service account email
    required: false
    default: null
  pem_file:
    description:
      - path to the pem file associated with the service account email
    required: false
    default: null
  project_id:
    description:
      - your GCE project ID
    required: false
    default: null
requirements:
    - "python >= 2.6"
    - "apache-libcloud"
author: "Tom Melendez (supertom)"
'''

EXAMPLES = '''
# Create an image named test-image from the disk 'test-disk' in zone us-central1-a.
- gce_img:
    name: test-image
    source: test-disk
    zone: us-central1-a
    state: present

# Create an image named test-image from a tarball in Google Cloud Storage.
- gce_img:
    name: test-image
    source: https://storage.googleapis.com/bucket/path/to/image.tgz
    
# Alternatively use the gs scheme
- gce_img:
    name: test-image
    source: gs://bucket/path/to/image.tgz

# Delete an image named test-image.
- gce_img:
    name: test-image
    state: absent
'''


try:
  import libcloud
  from libcloud.compute.types import Provider
  from libcloud.compute.providers import get_driver
  from libcloud.common.google import GoogleBaseError
  from libcloud.common.google import ResourceExistsError
  from libcloud.common.google import ResourceNotFoundError
  _ = Provider.GCE
  has_libcloud = True
except ImportError:
  has_libcloud = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.gce import gce_connect


GCS_URI = 'https://storage.googleapis.com/'


def create_image(gce, name, module):
  """Create an image with the specified name."""
  source = module.params.get('source')
  zone = module.params.get('zone')
  desc = module.params.get('description')
  timeout = module.params.get('timeout')
  family = module.params.get('family')

  if not source:
    module.fail_json(msg='Must supply a source', changed=False)

  if source.startswith(GCS_URI):
    # source is a Google Cloud Storage URI
    volume = source
  elif source.startswith('gs://'):
    # libcloud only accepts https URI.
    volume = source.replace('gs://', GCS_URI)
  else:
    try:
      volume = gce.ex_get_volume(source, zone)
    except ResourceNotFoundError:
      module.fail_json(msg='Disk %s not found in zone %s' % (source, zone),
                       changed=False)
    except GoogleBaseError as e:
      module.fail_json(msg=str(e), changed=False)

  gce_extra_args = {}
  if family is not None:
    gce_extra_args['family'] = family

  old_timeout = gce.connection.timeout
  try:
    gce.connection.timeout = timeout
    gce.ex_create_image(name, volume, desc, use_existing=False, **gce_extra_args)
    return True
  except ResourceExistsError:
    return False
  except GoogleBaseError as e:
    module.fail_json(msg=str(e), changed=False)
  finally:
    gce.connection.timeout = old_timeout


def delete_image(gce, name, module):
  """Delete a specific image resource by name."""
  try:
    gce.ex_delete_image(name)
    return True
  except ResourceNotFoundError:
    return False
  except GoogleBaseError as e:
    module.fail_json(msg=str(e), changed=False)


def main():
  module = AnsibleModule(
      argument_spec=dict(
          name=dict(required=True),
          family=dict(),
          description=dict(),
          source=dict(),
          state=dict(default='present', choices=['present', 'absent']),
          zone=dict(default='us-central1-a'),
          service_account_email=dict(),
          pem_file=dict(type='path'),
          project_id=dict(),
          timeout=dict(type='int', default=180)
      )
  )

  if not has_libcloud:
    module.fail_json(msg='libcloud with GCE support is required.')

  gce = gce_connect(module)

  name = module.params.get('name')
  state = module.params.get('state')
  family = module.params.get('family')
  changed = False

  if family is not None and hasattr(libcloud, '__version__') and libcloud.__version__ <= '0.20.1':
    module.fail_json(msg="Apache Libcloud 1.0.0+ is required to use 'family' option",
                     changed=False)

  # user wants to create an image.
  if state == 'present':
    changed = create_image(gce, name, module)

  # user wants to delete the image.
  if state == 'absent':
    changed = delete_image(gce, name, module)

  module.exit_json(changed=changed, name=name)

if __name__ == '__main__':
    main()
