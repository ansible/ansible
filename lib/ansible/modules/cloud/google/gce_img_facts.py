#!/usr/bin/python
# Copyright 2013 Google Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: gce_img_facts
version_added: "2.6"
short_description: Collect GCE image facts
description:
     - Collect facts about Google Compute Engine (GCE) images.
options:
  filter:
    description:
      - Filter to apply on image selection. Below filter options are available.
      -     archiveSizeBytes: Archived image size in bytes.
      -     creationTimestamp: Image creation timestamp.
      -     description: Desciption.
      -     diskSizeGb: Boot disk size in Gb.
      -     family: Image family.
      -     id: Image id.
      -     name: Image name.
      -     selfLink: Image self link.
      -     sourceDisk: Source disk of image.
      -     sourceDiskId: Id of source disk of image.
      -     sourceType: Type of source disk.
      -     status: Status of image.
      - Python patterns can be used with above filter options.
    required: false
    default: {}
  project_id:
    description:
      - your GCE project ID
    required: false
    default: null
  service_account_email:
    description:
      - service account email
    required: false
    default: null
  credentials_file:
    description:
      - path to the JSON file associated with the service account email
    default: null
    required: false

requirements:
    - "python >= 2.6"
    - "apache-libcloud >= 0.13.3, >= 0.17.0 if using JSON credentials"
notes:
  - JSON credentials strongly preferred.
author: "Rahul Paigavan (@Rahul-CSI) <rahul.paigavan@cambridgesemantics.com>"
'''

EXAMPLES = '''
# Basic gce fact collect example. Collect the facts for GCE images.
- name: Collect gce facts for images.
  gce_img_facts:
    service_account_email: "your-sa@your-project-name.iam.gserviceaccount.com"
    credentials_file: "/path/to/your-key.json"
    project_id: "your-project-name"

# Collect the facts for GCE images with filter as below
# Image created in Jan 2018 (creationTimestamp)
# Image having description x86_64 (description)
# Image with boot disk size between 10-19 (diskSizeGb)
# Image with self link having projects/centos-cloud (selfLink)
- name: Collect gce facts for multiple instances with base_name.
  gce_img_facts:
    filter:
      "creationTimestamp": "^2018-01.*"
      "description": "x86_64"
      "diskSizeGb": "1\\d"
      "selfLink": "projects/centos-cloud"
    service_account_email: "your-sa@your-project-name.iam.gserviceaccount.com"
    credentials_file: "/path/to/your-key.json"
    project_id: "your-project-name"

# Collect the facts for GCE images with filter as below
# Image with source type as RAW (sourceType)
# Image with READY status (status)
# Image with centos or rhel family (family)
# Image with name starting with centos and created on
#   29th Jan 2018. (name)
- name: Collect gce facts for list of instances with instance_names.
  gce_img_facts:
    filter:
      "sourceType": "^RAW$"
      "status": "^READY$"
      "family": "centos.*|rhel.*"
      "name": "^centos.*v20180129$"
    service_account_email: "your-sa@your-project-name.iam.gserviceaccount.com"
    credentials_file: "/path/to/your-key.json"
    project_id: "your-project-name"

---
# Example Playbook for collecting image facts.
- name: Image Facts Examples
  hosts: localhost
  vars:
    service_account_email: "your-sa@your-project-name.iam.gserviceaccount.com"
    credentials_file: "/path/to/your-key.json"
    project_id: "your-project-name"
  tasks:
    - name: Collect instance facts
      gce_img_facts:
        filter:
          "creationTimestamp": "^2018-01.*"
          "description": "x86_64"
          "diskSizeGb": "1\\d"
          "selfLink": "projects/centos-cloud"
          "sourceType": "^RAW$"
          "status": "^READY$"
          "family": "centos.*|rhel.*"
          "name": "^centos.*v20180129$"
        service_account_email: "{{ service_account_email }}"
        credentials_file: "{{ credentials_file }}"
        project_id: "{{ project_id }}"
      register: gce_img_facts

    - name: Print image facts
      debug:
        msg: "{{ gce_img_facts }}"
'''

RETURN = '''
archiveSizeBytes:
    description: Archived image size in bytes.
    returned: always
    type: string
    sample: 2267256256
creationTimestamp:
    description: Image creation timestamp.
    returned: always
    type: string
    sample: 2017-11-23T22:00:48.225-08:00
description:
    description: Description of the image.
    returned: always
    type: string
    sample: This is centos-7 image.
diskSizeGb:
    description: Boot disk size in Gb.
    returned: always
    type: string
    sample: 10
family:
    description: Image family.
    returned: always
    type: string
    sample: centos-7
id:
    description: ID of the image.
    returned: always
    type: string
    sample: 1719168448950045567
licenses:
    description: Image license details.
    returned: always
    type: list of dict
    sample: [{"charges_use_fee": true, "id": "centos-7", "name": "centos-7"}]
name:
    description: Name of the image.
    returned: always
    type: string
    sample: centos-7-v20180129
rawDisk:
    description: Raw disk details.
    returned: always
    type: dict
    sample: {"containerType": "TAR", "source": ""}
selfLink:
    description: Link to image.
    returned: always
    type: string
    sample: "https://www.googleapis.com/compute/v1/projects/centos-cloud/global/images/centos-7-v20180129"
sourceDisk:
    description: Source disk from which this disk is created.
    returned: always
    type: string
    sample: "https://www.googleapis.com/compute/v1/projects/centos-cloud/global/images/centos-6-v20170129"
sourceDiskId:
    description: Id of the source disk.
    returned: always
    type: string
    sample: 2125839325795407273
sourceType:
    description: Type of the source disk.
    returned: always
    type: string
    sample: RAW
status:
    description: Status of the disk.
    returned: always
    type: string
    sample: READY
'''

try:
    import libcloud
    import re
    from libcloud.compute.types import Provider
    gce_provider = Provider.GCE
    HAS_LIBCLOUD = True
except ImportError:
    HAS_LIBCLOUD = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.gce import gce_connect, unexpected_error_msg


def _get_image_info(images, image_filter={}):
    """Retrieves image facts of all image objects from the list of images

    images: Object containing list of image objects.
    image_filter: Dictionary of filters to select images

    Returns a list of dictionary matched as pesr image_filter,
    Each dictionary contains facts about one image.
    """

    def _get_value(param):
        if (param in image.extra and image.extra[param]):
            return image.extra[param]

    image_list = []
    for image in images:
        image_license = []
        if 'licenses' in image.extra:
            for license in image.extra['licenses']:
                license_dict = {
                    'id': license.id,
                    'name': license.name,
                    'charges_use_fee': license.charges_use_fee
                }
                image_license.append(license_dict)

        image_list.append({
            'name': image.name,
            'archiveSizeBytes': _get_value('archiveSizeBytes'),
            'creationTimestamp': _get_value('creationTimestamp'),
            'description': _get_value('description'),
            'diskSizeGb': _get_value('diskSizeGb'),
            'family': _get_value('family'),
            'id': image.id,
            'licenses': image_license,
            'rawDisk': _get_value('rawDisk'),
            'selfLink': _get_value('selfLink'),
            'sourceDisk': _get_value('sourceDisk'),
            'sourceDiskId': _get_value('sourceDiskId'),
            'sourceType': _get_value('sourceType'),
            'status': _get_value('status'),
        })

    if image_filter:
        valid_filter_options = [
            'archiveSizeBytes', 'creationTimestamp', 'description',
            'diskSizeGb', 'family', 'id', 'name', 'selfLink',
            'sourceDisk', 'sourceDiskId', 'sourceType', 'status']
        if all([option in valid_filter_options for option in image_filter]):
            for filt in image_filter:
                pattern = re.compile(image_filter[filt])
                image_list = list(filter(
                    lambda item: (
                        (isinstance(item[filt], basestring)) and
                        (pattern.search(item[filt]))
                    ), image_list))
        else:
            module.fail_json(
                msg='Invalid image_filter option given.' +
                ' Supported filter options are : ' +
                ','.join(valid_filter_options))
    return image_list


def image_info(module, gce, image_filter={}):
    """Collects the information of a list of images.

    module: Ansible module object
    gce: authenticated GCE connection object
    image_filter: Dict of filters to select images

    Returns a list of dictionaries, each dictionary contains information
    about the image.
    """
    changed = False

    try:
        images = gce.list_images()
    except Exception as e:
        module.fail_json(msg=unexpected_error_msg(e), changed=False)

    return (changed, _get_image_info(images, image_filter))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            filters=dict(type='dict', default={}),
            service_account_email=dict(),
            credentials_file=dict(type='path'),
            project_id=dict(),
        )
    )

    if not HAS_LIBCLOUD:
        module.fail_json(msg='libcloud with GCE support \
            (0.17.0+) required for this module')

    gce = gce_connect(module)
    changed = False
    filters = module.params.get('filters')

    (changed, images) = image_info(module, gce, filters)
    json_output = {}
    json_output['images'] = images
    json_output['changed'] = changed

    module.exit_json(**json_output)

if __name__ == '__main__':
    main()
