#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Cambridge Semantics Inc.
#
# This file is part of Ansible.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: gcdataproc
short_description: Module for Google Cloud Dataproc clusters.
description:
  - Creates or destroys Google Cloud Dataproc clusters on Google Cloud.
    For more information on Dataproc, see "https://cloud.google.com/dataproc/".
version_added: "2.3"
author: "John Baublitz @jbaublitz"
requirements:
  - "python >= 2.6"
  - "google-api-python-client >= 1.5.4"
  - "oauth2client >= 3.0.0"
options:
  name:
    description:
      - Name of the dataproc cluster from which to generate node names.
    required: true
  state:
    description:
      - Desired state of the dataproc cluster.
    default: present
    choices: ['present', 'active', 'absent', 'deleted']
  network:
    description:
      - Network on which to provision the dataproc cluster. Cannot be
        specified with subnetwork.
  subnetwork:
    description:
      - Subnetwork on which to provision the dataproc cluster. Cannot be
        specified with network.
  region:
    description:
      - Specifies the region of resources like network and subnetwork
        in which to provision the cluster.
    default: us-central1
  zone:
    description:
      - Specifies the zone of the dataproc cluster configuration.
    default: us-central1-a
  sync:
    description:
      - Wait for completion of dataproc provisioning to return.
    default: true
    choices: [true, false]
  poll_interval:
    description:
      - Poll interval for checking job completion when 'sync' is true.
    default: 1
  image_version:
    description:
      - Cluster software image version.
  service_account_scopes:
    description:
      - See "https://developers.google.com/identity/protocols/googlescopes#dataprocv1"
        for more information on OAuth2 scopes available for dataproc.
  metadata:
    description:
      - Unvalidated dict of metadata passed to dataproc clusters on creation.
        See "https://cloud.google.com/dataproc/docs/reference/rest/v1/projects.regions.clusters#gceclusterconfig"
        and the metadata field in this object for more information.
  init_actions:
    description:
      - Unvalidated list of initialization actions passed to dataproc clusters on creation.
        Each object in the list is defined by the following object -
        "https://cloud.google.com/dataproc/docs/reference/rest/v1/projects.regions.clusters#nodeinitializationaction".
  master_config:
    description:
      - Unvalidated dict specifying the master configuration for the cluster.
        "https://cloud.google.com/dataproc/docs/reference/rest/v1/projects.regions.clusters#instancegroupconfig".
  worker_config:
    description:
      - Unvalidated dict specifying the master configuration for the cluster.
        "https://cloud.google.com/dataproc/docs/reference/rest/v1/projects.regions.clusters#instancegroupconfig".
  second_worker_config:
    description:
      - Unvalidated dict specifying the master configuration for the cluster.
        "https://cloud.google.com/dataproc/docs/reference/rest/v1/projects.regions.clusters#instancegroupconfig".
  bucket:
    description:
      - A Google Cloud Storage staging bucket used for sharing generated SSH keys and config. If you do not
        specify a staging bucket, Cloud Dataproc will determine an appropriate Cloud Storage location
        (US, ASIA, or EU) for your cluster's staging bucket according to the Google Compute Engine zone where
        your cluster is deployed, and then it will create and manage this project-level, per-location bucket for you.
        (from "https://cloud.google.com/dataproc/docs/reference/rest/v1/projects.regions.clusters#clusterconfig")
notes:
  - Because this module deals directly with a highly variable JSON REST API, much of the input is unvalidated.
    Check the documentation for Google Cloud for defaults on the cloud side. If input is improperly formatted,
    ansible will pass back the Google error as opposed to throwing an error on the ansible side.
'''

EXAMPLES = '''
# Creating a dataproc cluster with default paramters
- gcdataproc:
    name: test

# Creating a dataproc cluster with defaults, fire and forget
- gcdataproc:
    name: test
    sync: false
'''

RETURN = '''
name:
  description:
    - The server-assigned name, which is only unique within the same service that originally returns it. If
      you use the default HTTP mapping, the name should have the format of operations/some/unique/name.
metadata:
  description:
    - Service-specific metadata associated with the operation. It typically contains progress information
      and common metadata such as create time. Some services might not provide such metadata. Any method
      that returns a long-running operation should document the metadata type, if any.
      An object containing fields of an arbitrary type. An additional field "@type" contains a URI
      identifying the type.
done:
  description:
    - If the value is false, it means the operation is still in progress. If true, the operation is completed,
      and either error or response is available.
error:
  description:
    - The error result of the operation in case of failure. 
response:
  description:
    - The normal response of the operation in case of success. If the original method returns no data on
      success, such as Delete, the response is google.protobuf.Empty. If the original method is standard
      Get/Create/Update, the response should be the resource. For other methods, the response should have
      the type XxxResponse, where Xxx is the original method name. For example, if the original method
      name is TakeSnapshot(), the inferred response type is TakeSnapshotResponse.
      An object containing fields of an arbitrary type. An additional field "@type" contains a URI
      identifying the type.
'''

import os
import time

try:
    from oauth2client.service_account import ServiceAccountCredentials
    from apiclient.discovery import build
    from googleapiclient.errors import HttpError
    HAS_GOOGLE_API_LIB = True
except ImportError:
    HAS_GOOGLE_API_LIB = False

def google_auth(module, cred_path):
    scopes = ['https://www.googleapis.com/auth/cloud-platform']
    credentials = None
    try:
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
                          cred_path,
                          scopes=scopes
                      )
    except Exception as e:
        module.fail_json(msg=e, changed=False)

    return credentials

def generate_resource_uri(project, *args):
    google_base_uri = \
            'https://www.googleapis.com/compute/v1/projects/%s/' % project
    return google_base_uri + '/'.join(args)

def populate_request_body(module, name, project, region, zone):
    image_version = module.params.get('image_version')
    bucket = module.params.get('bucket')
    network = module.params.get('network')
    subnetwork = module.params.get('subnetwork')
    tags = module.params.get('tags')
    service_account_scopes = module.params.get('service_account_scopes')
    metadata = module.params.get('metadata')
    init_actions = module.params.get('init_actions')
    master_config = module.params.get('master_config')
    worker_config = module.params.get('worker_config')
    second_worker_config = module.params.get('second_worker_config')

    body = {
        'clusterName': name,
        'projectId': project,
        'config': {
            'gceClusterConfig': {
                'zoneUri': generate_resource_uri(
                    project,
                    'zones',
                    zone
                )
            }
        }
    }

    if image_version:
        body['config']['softwareConfig'] = {}
        body['config']['softwareConfig']['imageVersion'] = image_version
    if bucket:
        body['config']['configBucket'] = bucket
    if tags:
        body['config']['gceClusterConfig']['tags'] = tags.split(',')
    if network:
        body['config']['gceClusterConfig']['networkUri'] = \
            generate_resource_uri(
                project,
                'regions',   
                region,
                network
            )
    if subnetwork:
        body['config']['gceClusterConfig']['subnetworkUri'] = \
            generate_resource_uri(
                project,
                'regions',
                region,
                subnetwork
            )
    if service_account_scopes:
        body['config']['gceConfigCluster']['serviceAccountScopes'] = \
            ['https://www.googleapis.com/auth/' + scope \
             for scope in service_account_scopes]
    if metadata:
        body['config']['gceConfigCluster']['metadata'] = metadata
    if init_actions:
        body['config']['initializationActions'] = init_actions
    if master_config:
        body['config']['masterConfig'] = master_config
    if worker_config:
        body['config']['workerConfig'] = worker_config
    if second_worker_config:
        body['config']['secondaryWorkerConfig'] = second_worker_config

    return body

def main():
    module = AnsibleModule(
        argument_spec = dict(
            name = dict(required=True),
            state = dict(default='present'),
            network = dict(),
            subnetwork = dict(),
            region = dict(default='us-central1'),
            zone = dict(default='us-central1-a'),
            sync = dict(type='bool', default=True),
            poll_interval = dict(type='int', default=1),
            image_version = dict(),
            service_account_scopes = dict(type='list'),
            metadata = dict(type='dict'),
            init_actions = dict(type='list'),
            master_config = dict(type='dict'),
            worker_config = dict(type='dict'),
            second_worker_config = dict(type='dict'),
            bucket = dict()
        ),
        mutually_exclusive = [
            ('network', 'subnetwork')
        ]
    )

    if not HAS_GOOGLE_API_LIB:
        module.fail_json(msg="Please install google-api-python-client library")

    name = module.params.get('name')
    state = module.params.get('state')
    region = module.params.get('region')
    zone = module.params.get('zone')
    sync = module.params.get('sync')
    poll_interval = module.params.get('poll_interval')

    if not zone.startswith(region):
        module.fail_json(msg="Region %s must contain zone %s" % (region, zone))

    gce_email = os.environ.get('GCE_EMAIL', None)
    gce_project = os.environ.get('GCE_PROJECT', None)
    gce_credentials = os.environ.get('GCE_CREDENTIALS_FILE_PATH', None)
    if not gce_email or not gce_project or not gce_credentials:
        module.fail_json(msg="Please define Google auth environment " \
                             "variables GCE_EMAIL, GCE_PROJECT and " \
                             "GCE_CREDENTIALS_FILE_PATH",
                             changed=False)

    credentials = google_auth(module, gce_credentials)
    dataproc = build('dataproc', 'v1', credentials=credentials)
    json = {}
    changed = False
    if state in ['present', 'active']:
        try:
            json = dataproc.projects().regions().clusters() \
                   .get(projectId=gce_project,
                        region='global',
                        clusterName=name).execute()
        except HttpError:
            body = populate_request_body(module, name, gce_project, region, zone)
            json = dataproc.projects().regions().clusters() \
                    .create(projectId=gce_project,
                            region='global',
                            body=body
                    ).execute()
            if sync:
                while 'status' not in json or \
                        json['status']['state'] != 'RUNNING':
                    json = dataproc.projects().regions().clusters() \
                           .get(projectId=gce_project,
                                region='global',
                                clusterName=name).execute();
                    time.sleep(poll_interval)
            changed = True
        except Exception as e:
            module.fail_json(changed=changed, msg=str(e))
    elif state in ['absent', 'deleted']:
        try:
            json = dataproc.projects().regions().clusters() \
                   .get(projectId=gce_project,
                        region='global',
                        clusterName=name).execute()
        except HttpError as e:
            pass
        except Exception as e:
            module.fail_json(changed=changed, msg=str(e))
        else:
            json = dataproc.projects().regions().clusters() \
                   .delete(projectId=gce_project,
                           region='global',
                           clusterName=name
                   ).execute()
            changed = True

    module.exit_json(changed=changed, **json)

from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
