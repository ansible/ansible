#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Patrick Chauncey <pchauncey@gmail.com>
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}

DOCUMENTATION = r'''
---
module: couchbase_bucket
version_added: '2.4'
short_description: Create and manipulate Couchbase buckets
description:
  - The C(couchbase_bucket) module creates or manipulates Couchbase buckets.
options:
  login_user:
    description:
      - The username used to authenticate with
    default: Administrator
  login_password:
    description:
      - The password used to authenticate with
    default: null
  login_host:
    description:
      - The couchbase host to authenticate to
    default: localhost
    aliases:
      - host
  login_port:
    description:
      - The port to connect to
    default: 8091
  name:
    description:
      - The bucket name to create or manipulate
    required: true
    aliases:
      - bucket_name
  bucket_type:
    description:
      - One of couchbase, memcached, ephemeral
    default: couchbase
    choices: [ 'couchbase', 'memcached', 'ephemeral' ]
  bucket_password:
    description:
      - The bucket password. Bucket authentication will be disabled if not supplied
    default: null
  replicas:
    description:
      - Number of replicas to use for a bucket
    default: 1
  ram_quota:
    description:
      - The maximum amount of memory (per node) that this bucket may use, in megabytes. The minimum for this value is 100
  flush_enabled:
    description:
      - Whether the flush API is enabled for the bucket. Not recommended in production
    default: False
  state:
    description:
      - The bucket state
    default: 'present'
    choices: [ 'present', 'absent' ]
requirements:
  - C(libcouchbase)
  - Couchbase Python SDK U(https://developer.couchbase.com/documentation/server/current/sdk/python/start-using-sdk.html)
author:
  - Patrick Chauncey (@pchauncey)
todo:
  - test with 5.0 (currently beta)
notes:
  - tested with Couchbase Enterprise 4.6.2 I(docker pull couchbase)
  - memcached buckets require an updated SDK, see U(https://github.com/pchauncey/couchbase-python-client/commit/1f437384fa4ab784ca61b4e94a47207ebe3237c8)
'''

EXAMPLES = r'''
- name: Create a couchbase bucket with 2 replicas and a 1024MB quota per node
  couchbase_bucket:
    login_username: Administrator
    login_password: abc123
    name: mybucket
    replicas: 2
    state: present
    ram_quota: 1024

- name: Manipulate existing bucket down to 1 replica
  couchbase_bucket:
    bucket_name: mybucket
    login_username: Administrator
    login_password: abc123
    replicas: 1

- name: Require bucket authentication
  couchbase_bucket:
    login_username: Administrator
    login_password: abc123
    bucket_name: mybucket
    bucket_password: zyx321

- name: Destroy an existing bucket
  couchbase_bucket:
    name: mybucket
    login_username: Administrator
    login_password: abc123
    state: absent
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import traceback

try:
    from couchbase.admin import Admin
    from couchbase.exceptions import HTTPError, ConnectError, NetworkError
    has_couchbase = True
except ImportError:
    has_couchbase = False


# ===========================================
# Couchbase module specific support methods.
#

def bucket_info(module, cbadmin, name):
    try:
        result = cbadmin.bucket_info(name)
        return result

    except HTTPError as err:
        if err.objextra.http_status == 404:
            return False
        elif err.objextra.http_status == 401:
            module.fail_json(msg="Unable to authenticate: try login_username and login_password")
        elif err.objextra.http_status == 401:
            module.fail_json(msg="HTTP error received: %s" % to_native(err.objextra.http_status), exception=traceback.format_exc())
    except (NetworkError, ConnectError) as e:
        module.fail_json(msg="Unable to connect to host: %s" % to_native(e), exception=traceback.format_exc())


def bucket_create(module, cbadmin, name, bucket_type, bucket_password='', replicas, ram_quota, flush_enabled):
    try:

        result = cbadmin.bucket_create(name=name,
                                       bucket_type=bucket_type,
                                       bucket_password=bucket_password,
                                       replicas=replicas,
                                       ram_quota=ram_quota,
                                       flush_enabled=flush_enabled)
        return True
    except Exception as e:
        module.fail_json(msg="exception caught during bucket creation: %s" % to_native(e), exception=traceback.format_exc())


def bucket_update(module, cbadmin, name, state, bucket_password='', replicas, ram_quota, flush_enabled):
    try:
        result = cbadmin.bucket_update(name=name,
                                       current=state,
                                       bucket_password=bucket_password,
                                       replicas=replicas,
                                       ram_quota=ram_quota,
                                       flush_enabled=flush_enabled)
        return True
    except Exception as e:
        module.fail_json(msg="exception caught during bucket update: %s" % to_native(e), exception=traceback.format_exc())


def bucket_delete(module, cbadmin, name):
    try:
        cbadmin.bucket_delete(name=name)
        return True
    except HTTPError as err:
        if err.objextra.http_status == 404:
            return False
        elif err.objextra.http_status == 401:
            module.fail_json(msg="Unable to authenticate: try login_username and login_password")
        elif err.objextra.http_status == 401:
            module.fail_json(msg="HTTP error received: %s" % to_native(err.objextra.http_status), exception=traceback.format_exc())
    except (NetworkError, ConnectError) as e:
        module.fail_json(msg="Unable to connect to host: %s" % to_native(e), exception=traceback.format_exc())
    except Exception as e:
        module.fail_json(msg="exception caught during bucket delete: %s" % to_native(e), exception=traceback.format_exc())


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_user=dict(default="Administrator"),
            login_password=dict(default="", no_log=True),
            login_host=dict(default="localhost", aliases=['host']),
            login_port=dict(default=8091, type='int'),
            name=dict(required=True, aliases=['bucket_name']),
            bucket_type=dict(default="couchbase", choices=["couchbase", "memcached", "ephemeral"]),
            bucket_password=dict(default=None, no_log=True),
            replicas=dict(default=1, type='int'),
            ram_quota=dict(default=512, type='int'),
            flush_enabled=dict(default=False, type='bool'),
            state=dict(default="present", choices=["present", "absent", "update"])
        ),
        supports_check_mode=True,
    )

    if not has_couchbase:
        module.fail_json(msg="The couchbase python module is required")

    login_user = module.params["login_user"]
    login_password = module.params["login_password"]
    login_host = module.params["login_host"]
    login_port = module.params["login_port"]
    if login_port < 0 or login_port > 65535:
        module.fail_json(msg="login_port must be a valid unix port number (0-65535)")
    name = module.params["name"]
    bucket_type = module.params["bucket_type"]
    bucket_password = module.params["bucket_password"]
    replicas = module.params["replicas"]
    ram_quota = module.params["ram_quota"]
    if ram_quota and ram_quota < 100:
        module.fail_json(msg='ram_quota minimum is 100')
    flush_enabled = module.params["flush_enabled"]
    state = module.params["state"]

    admin_params = {
        "username": login_user,
        "password": login_password,
        "host": login_host,
        "port": int(login_port),
    }

    changed = False

    cbadmin = Admin(**admin_params)
    info = bucket_info(module, cbadmin, name)

    if info:

        if state == "absent":

            # delete bucket
            if module.check_mode:
                module.exit_json(changed=True, name=name)
            else:
                try:
                    changed = bucket_delete(module, cbadmin, name)
                except Exception as e:
                    module.fail_json(msg="error deleting bucket: %s" % to_native(e))

                module.exit_json(changed=changed, name=name)

        else:

            curr_ram = info.value.get('quota').get('ram')
            curr_replicas = info.value.get('vBucketServerMap').get('numReplicas')
            curr_flush = info.value.get('controllers').get('flush')

            if curr_flush:
                curr_flush = True
            else:
                curr_flush = False

            if (curr_ram != (ram_quota * 1024 ** 2)) or (replicas != curr_replicas) or (curr_flush != flush_enabled) or bucket_password:

                if module.check_mode:
                    module.exit_json(changed=True, name=name)
                else:
                    try:
                        changed = bucket_update(module, cbadmin, name, info, bucket_password, replicas, ram_quota, flush_enabled)
                    except Exception as e:
                        module.fail_json(msg="error updating bucket: %s" % to_native(e))

    else:

        # bucket creation
        if state == "present":
            if module.check_mode:
                module.exit_json(changed=True, name=name)
            else:
                try:
                    changed = bucket_create(module, cbadmin, name, bucket_type, bucket_password, replicas, ram_quota, flush_enabled)
                except Exception as e:
                    module.fail_json(msg="error creating bucket: %s" % to_native(e))

                module.exit_json(changed=changed, name=name)

    module.exit_json(changed=changed, name=name)

if __name__ == '__main__':
    main()
