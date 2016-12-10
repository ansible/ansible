#!/usr/bin/python
#
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This Ansible library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: s3_bucket_sync
short_description: Sync the contents of two s3 buckets
description:
     - This module reads the filelist of the source bucket in batches a 1000 file and creates a syncing queue which is processed by multiple workers.
version_added: 2.2
author: "Georg Rabenstein @raben2"
options:
   bucket_from:
      description:
           - Source bucket for sync
      required: true
      default: null
   bucket_to:
      description:
          - Destination bucket for sync
      required: true
      default: null
   max_processes:
      description:
          - Worker processes to be spawned on the sync queue.
      required: false
      default: 10
   log:
      description:
           - Creates a s3_sync.log in the current working directory
      required: false
      default: false
'''

EXAMPLES = '''
# sync contents of bucket a to bucket b
tasks:
- name: sync my pictures
  s3_bucket_sync:
    bucket_from: my-picture-dump
    bucket_to: my-backup
    log: true
    max_processes: 20
# sync without waiting for the result
- name: sync my videos
  s3_bucket_sync:
     bucket_from: video-bucket
     bucket_to: private-bucket
     log: false
     max_processes: 20
  async: true
'''

RETURN = '''
bucket_from:
  description: a s3 bucket object
bucket_to: 
  description: a s3 bucket object
log:
  description: a complete logfile of the sync process in your working directory
max_processes:
  description: number of sync threads to spawn as subprocesses
''' 

import sys, argparse, logging
import threading
from multiprocessing import Manager, Queue
try:
   import boto.ec2
   from boto.s3.connection import S3Connection, OrdinaryCallingFormat, Location
   from boto.exception import BotoServerError, S3CreateError, S3ResponseError
   HAS_BOTO = True
except ImportError:
   HAS_BOTO = False

def upload_to_s3(sync, bucket_from, bucket_to, connection, module):
    log = module.params.get("log")
    bucket_right = connection.get_bucket(bucket_to)
    missing_key = sync.get()
    try:
          bucket_right.copy_key(new_key_name=missing_key, src_bucket_name=bucket_from, src_key_name=missing_key, preserve_acl=True)
          logging.info("syncing object %s" % missing_key)

    except S3ResponseError, e:
          logging.info("key not found %s %s" % missing_key, e.message)
    return


def sync_diff(connection, module):
    #module params
    bucket_from = module.params.get("bucket_from")
    bucket_to = module.params.get("bucket_to")
    num_threads = module.params.get("max_processes")
    log = module.params.get("log")
    # s3 buckets as object
    bucket_right = connection.get_bucket(bucket_to)
    bucket_left = connection.get_bucket(bucket_from)

    changed = False
    mgr = Manager()
    job  = mgr.Queue(maxsize=0)
    mark = mgr.Queue(maxsize=0)
    sync = mgr.Queue(maxsize=0)
    job.put("start")
    mark.put('')

    while not mark.empty():
        p = threading.Thread(target=producer, args=(sync, job, mark, bucket_left, bucket_right))
        p.start()
        while True:
            if not sync.empty():
              threads = []
              for i in range(num_threads):
                u = threading.Thread(target=upload_to_s3, args=(sync, bucket_from, bucket_to, connection, module))
                u.start()
                threads.append(u)
            else:
               module.exit_json(changed=changed)
               break

        j = job.get()
        if (j == "final"):
            changed = True
            mark.task_done()
            continue
        p.join()

def producer(sync, job, mark, bucket_left, bucket_right):
    num = 1000 # max for get_all_keys
    retag  = []
    marker = mark.get()
    try:
       left = bucket_left.get_all_keys(max_keys=num, marker=marker)
       right = bucket_right.get_all_keys(max_keys=num, marker=marker)
       next = left[-1].name # set last found key for marker on next run
       mark.put(next)
       logging.info("next marker at %s" % next)
    except S3ResponseError, e:
          module.fail_json(msg=e.message)
    for rkey in right:
          retag.append(rkey.etag)
    for lkey in left:
        if not lkey.etag in retag:
              sync.put(lkey.name)

    # less items than num found start final run
    if len(left) < num:
        job.put("final")
        logging.info("##################################")
        logging.info("final run reached %s" % len(left))
        mark.task_done()
    else:
        job.put("continue")

def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            bucket_from   = dict(required=True),
            bucket_to     = dict(required=True),
            max_processes = dict(required=False, type='int', default='10'),
            log           = dict(required=False, type='bool', default='false')
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)

    try:
        connection = boto.s3.connect_to_region(Location, is_secure=True, calling_format=OrdinaryCallingFormat(), **aws_connect_params)
        if connection is None:
            connection = boto.connect_s3(**aws_connect_params)
    except Exception, e:
        module.fail_json(msg='Failed to connect to S3: %s' % str(e))

    if connection is None: # this should never happen
        module.fail_json(msg ='Unknown error, failed to create s3 connection, no information from boto.')

    max_processes = module.params.get("max_processes")
    log = module.params.get("log")
    if log:
       logging.basicConfig(filename='s3_sync.log',level=logging.INFO)
    else:
       logging.basicConfig(filename='/dev/null', level=logging.INFO)
    sync_diff(connection, module)

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
