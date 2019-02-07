#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Google
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# ----------------------------------------------------------------------------
#
#     ***     AUTO GENERATED CODE    ***    AUTO GENERATED CODE     ***
#
# ----------------------------------------------------------------------------
#
#     This file is automatically generated by Magic Modules and manual
#     changes will be clobbered when the file is regenerated.
#
#     Please read more about how to change this file at
#     https://www.github.com/GoogleCloudPlatform/magic-modules
#
# ----------------------------------------------------------------------------

from __future__ import absolute_import, division, print_function

__metaclass__ = type

################################################################################
# Documentation
################################################################################

ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ["preview"], 'supported_by': 'community'}

DOCUMENTATION = '''
---
module: gcp_compute_disk_facts
description:
- Gather facts for GCP Disk
short_description: Gather facts for GCP Disk
version_added: 2.7
author: Google Inc. (@googlecloudplatform)
requirements:
- python >= 2.6
- requests >= 2.18.4
- google-auth >= 1.3.0
options:
  filters:
    description:
    - A list of filter value pairs. Available filters are listed here U(https://cloud.google.com/sdk/gcloud/reference/topic/filters.)
    - Each additional filter in the list will act be added as an AND condition (filter1
      and filter2) .
  zone:
    description:
    - A reference to the zone where the disk resides.
    required: true
extends_documentation_fragment: gcp
'''

EXAMPLES = '''
- name:  a disk facts
  gcp_compute_disk_facts:
      zone: us-central1-a
      filters:
      - name = test_object
      project: test_project
      auth_kind: serviceaccount
      service_account_file: "/tmp/auth.pem"
'''

RETURN = '''
items:
  description: List of items
  returned: always
  type: complex
  contains:
    labelFingerprint:
      description:
      - The fingerprint used for optimistic locking of this resource. Used internally
        during updates.
      returned: success
      type: str
    creationTimestamp:
      description:
      - Creation timestamp in RFC3339 text format.
      returned: success
      type: str
    description:
      description:
      - An optional description of this resource. Provide this property when you create
        the resource.
      returned: success
      type: str
    id:
      description:
      - The unique identifier for the resource.
      returned: success
      type: int
    lastAttachTimestamp:
      description:
      - Last attach timestamp in RFC3339 text format.
      returned: success
      type: str
    lastDetachTimestamp:
      description:
      - Last dettach timestamp in RFC3339 text format.
      returned: success
      type: str
    licenses:
      description:
      - Any applicable publicly visible licenses.
      returned: success
      type: list
    name:
      description:
      - Name of the resource. Provided by the client when the resource is created.
        The name must be 1-63 characters long, and comply with RFC1035. Specifically,
        the name must be 1-63 characters long and match the regular expression `[a-z]([-a-z0-9]*[a-z0-9])?`
        which means the first character must be a lowercase letter, and all following
        characters must be a dash, lowercase letter, or digit, except the last character,
        which cannot be a dash.
      returned: success
      type: str
    sizeGb:
      description:
      - Size of the persistent disk, specified in GB. You can specify this field when
        creating a persistent disk using the sourceImage or sourceSnapshot parameter,
        or specify it alone to create an empty persistent disk.
      - If you specify this field along with sourceImage or sourceSnapshot, the value
        of sizeGb must not be less than the size of the sourceImage or the size of
        the snapshot.
      returned: success
      type: int
    users:
      description:
      - 'Links to the users of the disk (attached instances) in form: project/zones/zone/instances/instance
        .'
      returned: success
      type: list
    sourceImage:
      description:
      - The source image used to create this disk. If the source image is deleted,
        this field will not be set.
      - 'To create a disk with one of the public operating system images, specify
        the image by its family name. For example, specify family/debian-8 to use
        the latest Debian 8 image: projects/debian-cloud/global/images/family/debian-8
        Alternatively, use a specific version of a public operating system image:
        projects/debian-cloud/global/images/debian-8-jessie-vYYYYMMDD To create a
        disk with a private image that you created, specify the image name in the
        following format: global/images/my-private-image You can also specify a private
        image by its image family, which returns the latest version of the image in
        that family. Replace the image name with family/family-name: global/images/family/my-private-family
        .'
      returned: success
      type: str
    zone:
      description:
      - A reference to the zone where the disk resides.
      returned: success
      type: str
    sourceImageEncryptionKey:
      description:
      - The customer-supplied encryption key of the source image. Required if the
        source image is protected by a customer-supplied encryption key.
      returned: success
      type: complex
      contains:
        rawKey:
          description:
          - Specifies a 256-bit customer-supplied encryption key, encoded in RFC 4648
            base64 to either encrypt or decrypt this resource.
          returned: success
          type: str
        sha256:
          description:
          - The RFC 4648 base64 encoded SHA-256 hash of the customer-supplied encryption
            key that protects this resource.
          returned: success
          type: str
        kmsKeyName:
          description:
          - The name of the encryption key that is stored in Google Cloud KMS.
          returned: success
          type: str
    sourceImageId:
      description:
      - The ID value of the image used to create this disk. This value identifies
        the exact image that was used to create this persistent disk. For example,
        if you created the persistent disk from an image that was later deleted and
        recreated under the same name, the source image ID would identify the exact
        version of the image that was used.
      returned: success
      type: str
    diskEncryptionKey:
      description:
      - Encrypts the disk using a customer-supplied encryption key.
      - After you encrypt a disk with a customer-supplied key, you must provide the
        same key if you use the disk later (e.g. to create a disk snapshot or an image,
        or to attach the disk to a virtual machine).
      - Customer-supplied encryption keys do not protect access to metadata of the
        disk.
      - If you do not provide an encryption key when creating the disk, then the disk
        will be encrypted using an automatically generated key and you do not need
        to provide a key to use the disk later.
      returned: success
      type: complex
      contains:
        rawKey:
          description:
          - Specifies a 256-bit customer-supplied encryption key, encoded in RFC 4648
            base64 to either encrypt or decrypt this resource.
          returned: success
          type: str
        sha256:
          description:
          - The RFC 4648 base64 encoded SHA-256 hash of the customer-supplied encryption
            key that protects this resource.
          returned: success
          type: str
        kmsKeyName:
          description:
          - The name of the encryption key that is stored in Google Cloud KMS.
          returned: success
          type: str
    sourceSnapshot:
      description:
      - The source snapshot used to create this disk. You can provide this as a partial
        or full URL to the resource.
      returned: success
      type: str
    sourceSnapshotEncryptionKey:
      description:
      - The customer-supplied encryption key of the source snapshot. Required if the
        source snapshot is protected by a customer-supplied encryption key.
      returned: success
      type: complex
      contains:
        rawKey:
          description:
          - Specifies a 256-bit customer-supplied encryption key, encoded in RFC 4648
            base64 to either encrypt or decrypt this resource.
          returned: success
          type: str
        kmsKeyName:
          description:
          - The name of the encryption key that is stored in Google Cloud KMS.
          returned: success
          type: str
        sha256:
          description:
          - The RFC 4648 base64 encoded SHA-256 hash of the customer-supplied encryption
            key that protects this resource.
          returned: success
          type: str
    sourceSnapshotId:
      description:
      - The unique ID of the snapshot used to create this disk. This value identifies
        the exact snapshot that was used to create this persistent disk. For example,
        if you created the persistent disk from a snapshot that was later deleted
        and recreated under the same name, the source snapshot ID would identify the
        exact version of the snapshot that was used.
      returned: success
      type: str
'''

################################################################################
# Imports
################################################################################
from ansible.module_utils.gcp_utils import navigate_hash, GcpSession, GcpModule, GcpRequest
import json

################################################################################
# Main
################################################################################


def main():
    module = GcpModule(argument_spec=dict(filters=dict(type='list', elements='str'), zone=dict(required=True, type='str')))

    if not module.params['scopes']:
        module.params['scopes'] = ['https://www.googleapis.com/auth/compute']

    items = fetch_list(module, collection(module), query_options(module.params['filters']))
    if items.get('items'):
        items = items.get('items')
    else:
        items = []
    return_value = {'items': items}
    module.exit_json(**return_value)


def collection(module):
    return "https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/disks".format(**module.params)


def fetch_list(module, link, query):
    auth = GcpSession(module, 'compute')
    response = auth.get(link, params={'filter': query})
    return return_if_object(module, response)


def query_options(filters):
    if not filters:
        return ''

    if len(filters) == 1:
        return filters[0]
    else:
        queries = []
        for f in filters:
            # For multiple queries, all queries should have ()
            if f[0] != '(' and f[-1] != ')':
                queries.append("(%s)" % ''.join(f))
            else:
                queries.append(f)

        return ' '.join(queries)


def return_if_object(module, response):
    # If not found, return nothing.
    if response.status_code == 404:
        return None

    # If no content, return nothing.
    if response.status_code == 204:
        return None

    try:
        module.raise_for_status(response)
        result = response.json()
    except getattr(json.decoder, 'JSONDecodeError', ValueError) as inst:
        module.fail_json(msg="Invalid JSON response with error: %s" % inst)

    if navigate_hash(result, ['error', 'errors']):
        module.fail_json(msg=navigate_hash(result, ['error', 'errors']))

    return result


if __name__ == "__main__":
    main()
