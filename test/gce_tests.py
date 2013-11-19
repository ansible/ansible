#!/usr/bin/env python
# Copyright 2013 Google Inc.
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

# This is a custom functional test script for the Google Compute Engine
# ansible modules.  In order to run these tests, you must:
# 1) Create a Google Cloud Platform account and enable the Google
#    Compute Engine service and billing
# 2) Download, install, and configure  'gcutil'
#    see [https://developers.google.com/compute/docs/gcutil/]
# 3) Convert your GCE Service Account private key from PKCS12 to PEM format
#    $ openssl pkcs12 -in pkey.pkcs12 -passin pass:notasecret \
#    > -nodes -nocerts | openssl rsa -out pkey.pem 
# 4) Make sure you have libcloud 0.13.3 or later installed.
# 5) Make sure you have a libcloud 'secrets.py' file in your PYTHONPATH
# 6) Set GCE_PARAMS and GCE_KEYWORD_PARMS in your 'secrets.py' file.
# 7) Set up a simple hosts file
#    $ echo 127.0.0.1 > ~/ansible_hosts
#    $ echo "export ANSIBLE_HOSTS='~/ansible_hosts'" >> ~/.bashrc
#    $ . ~/.bashrc
# 8) Set up your ansible 'hacking' environment
#    $ cd ~/ansible
#    $ . hacking/env-setup
#    $ export ANSIBLE_HOST_KEY_CHECKING=no
#    $ ansible all -m ping
# 9) Set your PROJECT variable below
# 10) Run and time the tests and log output, take ~30 minutes to run
#    $ time stdbuf -oL python test/gce_tests.py 2>&1 | tee log
#
# Last update: gcutil-1.11.0 and v1beta16

# Set this to your test Project ID
PROJECT="google.com:erjohnso"

# debugging
DEBUG=False   # lots of debugging output
VERBOSE=True  # on failure, display ansible command and expected/actual result

# location - note that some tests rely on the module's 'default'
# region/zone, which should match the settings below.
REGION="us-central1"
ZONE="%s-a" % REGION

# Peeking is a way to trigger looking at a specified set of resources
# before and/or after a test run.  The 'test_cases' data structure below
# has a few tests with 'peek_before' and 'peek_after'.  When those keys
# are set and PEEKING_ENABLED is True, then these steps will be executed
# to aid in debugging tests.  Normally, this is not needed.
PEEKING_ENABLED=False

# disks
DNAME="aaaaa-ansible-disk"
DNAME2="aaaaa-ansible-disk2"
DNAME6="aaaaa-ansible-inst6"
DNAME7="aaaaa-ansible-inst7"
USE_PD="true"
KERNEL="https://www.googleapis.com/compute/v1beta16/projects/google/global/kernels/gce-no-conn-track-v20130813"

# instances
INAME="aaaaa-ansible-inst"
INAME2="aaaaa-ansible-inst2"
INAME3="aaaaa-ansible-inst3"
INAME4="aaaaa-ansible-inst4"
INAME5="aaaaa-ansible-inst5"
INAME6="aaaaa-ansible-inst6"
INAME7="aaaaa-ansible-inst7"
TYPE="n1-standard-1"
IMAGE="https://www.googleapis.com/compute/v1beta16/projects/debian-cloud/global/images/debian-7-wheezy-v20131014"
NETWORK="default"
SCOPES="https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/compute,https://www.googleapis.com/auth/devstorage.full_control"

# networks / firewalls
NETWK1="ansible-network1"
NETWK2="ansible-network2"
NETWK3="ansible-network3"
CIDR1="10.240.16.0/24"
CIDR2="10.240.32.0/24"
CIDR3="10.240.64.0/24"
GW1="10.240.16.1"
GW2="10.240.32.1"
FW1="ansible-fwrule1"
FW2="ansible-fwrule2"
FW3="ansible-fwrule3"
FW4="ansible-fwrule4"

# load-balancer tests
HC1="ansible-hc1"
HC2="ansible-hc2"
HC3="ansible-hc3"
LB1="ansible-lb1"
LB2="ansible-lb2"

from commands import getstatusoutput as run
import sys

test_cases = [
    {'id': '01', 'desc': 'Detach / Delete disk tests',
     'setup': ['gcutil addinstance "%s" --wait_until_running --zone=%s --machine_type=%s --network=%s --service_account_scopes="%s" --image="%s" --persistent_boot_disk=%s' % (INAME, ZONE, TYPE, NETWORK, SCOPES, IMAGE, USE_PD),
               'gcutil adddisk "%s" --size_gb=2 --zone=%s --wait_until_complete' % (DNAME, ZONE)],

     'tests': [
       {'desc': 'DETACH_ONLY but disk not found [success]',
        'm': 'gce_pd',
        'a': 'name=%s instance_name=%s zone=%s detach_only=yes state=absent' % ("missing-disk", INAME, ZONE),
        'r': '127.0.0.1 | success >> {"changed": false, "detach_only": true, "detached_from_instance": "%s", "name": "missing-disk", "state": "absent", "zone": "%s"}' % (INAME, ZONE),
       },
       {'desc': 'DETACH_ONLY but instance not found [success]',
        'm': 'gce_pd',
        'a': 'name=%s instance_name=%s zone=%s detach_only=yes state=absent' % (DNAME, "missing-instance", ZONE),
        'r': '127.0.0.1 | success >> {"changed": false, "detach_only": true, "detached_from_instance": "missing-instance", "name": "%s", "size_gb": 2, "state": "absent", "zone": "%s"}' % (DNAME, ZONE),
       },
       {'desc': 'DETACH_ONLY but neither disk nor instance exists [success]',
        'm': 'gce_pd',
        'a': 'name=%s instance_name=%s zone=%s detach_only=yes state=absent' % ("missing-disk", "missing-instance", ZONE),
        'r': '127.0.0.1 | success >> {"changed": false, "detach_only": true, "detached_from_instance": "missing-instance", "name": "missing-disk", "state": "absent", "zone": "%s"}' % (ZONE),
       },
       {'desc': 'DETACH_ONLY but disk is not currently attached [success]',
        'm': 'gce_pd',
        'a': 'name=%s instance_name=%s zone=%s detach_only=yes state=absent' % (DNAME, INAME, ZONE),
        'r': '127.0.0.1 | success >> {"changed": false, "detach_only": true, "detached_from_instance": "%s", "name": "%s", "size_gb": 2, "state": "absent", "zone": "%s"}' % (INAME, DNAME, ZONE),
       },
       {'desc': 'DETACH_ONLY disk is attached and should be detached [success]',
        'setup': ['gcutil attachdisk --disk="%s,mode=READ_ONLY" --zone=%s %s' % (DNAME, ZONE, INAME), 'sleep 10'],
        'm': 'gce_pd',
        'a': 'name=%s instance_name=%s zone=%s detach_only=yes state=absent' % (DNAME, INAME, ZONE),
        'r': '127.0.0.1 | success >> {"attached_mode": "READ_ONLY", "attached_to_instance": "%s", "changed": true, "detach_only": true, "detached_from_instance": "%s", "name": "%s", "size_gb": 2, "state": "absent", "zone": "%s"}' % (INAME, INAME, DNAME, ZONE),
        'teardown': ['gcutil detachdisk --zone=%s --device_name=%s %s' % (ZONE, DNAME, INAME)],
       },
       {'desc': 'DETACH_ONLY but not instance specified [FAIL]',
        'm': 'gce_pd',
        'a': 'name=%s zone=%s detach_only=yes state=absent' % (DNAME, ZONE),
        'r': '127.0.0.1 | FAILED >> {"changed": false, "failed": true, "msg": "Must specify an instance name when detaching a disk"}',
       },
       {'desc': 'DELETE but disk not found [success]',
        'm': 'gce_pd',
        'a': 'name=%s zone=%s state=absent' % ("missing-disk", ZONE),
        'r': '127.0.0.1 | success >> {"changed": false, "name": "missing-disk", "state": "absent", "zone": "%s"}' % (ZONE),
       },
       {'desc': 'DELETE but disk is attached [FAIL]',
        'setup': ['gcutil attachdisk --disk="%s,mode=READ_ONLY" --zone=%s %s' % (DNAME, ZONE, INAME), 'sleep 10'],
        'm': 'gce_pd',
        'a': 'name=%s zone=%s state=absent' % (DNAME, ZONE),
        'r': "127.0.0.1 | FAILED >> {\"changed\": false, \"failed\": true, \"msg\": \"The disk resource 'projects/%s/zones/%s/disks/%s' is already being used by 'projects/%s/zones/%s/instances/%s'\"}" % (PROJECT, ZONE, DNAME, PROJECT, ZONE, INAME),
        'teardown': ['gcutil detachdisk --zone=%s --device_name=%s %s' % (ZONE, DNAME, INAME)],
       },
       {'desc': 'DELETE disk [success]',
        'm': 'gce_pd',
        'a': 'name=%s zone=%s state=absent' % (DNAME, ZONE),
        'r': '127.0.0.1 | success >> {"changed": true, "name": "%s", "size_gb": 2, "state": "absent", "zone": "%s"}' % (DNAME, ZONE),
       },
     ],
     'teardown': ['gcutil deleteinstance -f "%s" --zone=%s' % (INAME, ZONE),
                  'sleep 15',
                  'gcutil deletedisk -f "%s" --zone=%s' % (INAME, ZONE),
                  'sleep 10',
                  'gcutil deletedisk -f "%s" --zone=%s' % (DNAME, ZONE),
                  'sleep 10'],
    },

    {'id': '02', 'desc': 'Create disk but do not attach (e.g. no instance_name param)',
     'setup': [],
     'tests': [
       {'desc': 'CREATE_NO_ATTACH "string" for size_gb [FAIL]',
        'm': 'gce_pd',
        'a': 'name=%s size_gb="foo" zone=%s' % (DNAME, ZONE),
        'r': '127.0.0.1 | FAILED >> {"changed": false, "failed": true, "msg": "Must supply a size_gb larger than 1 GB"}',
       },
       {'desc': 'CREATE_NO_ATTACH negative size_gb [FAIL]',
        'm': 'gce_pd',
        'a': 'name=%s size_gb=-2 zone=%s' % (DNAME, ZONE),
        'r': '127.0.0.1 | FAILED >> {"changed": false, "failed": true, "msg": "Must supply a size_gb larger than 1 GB"}',
       },
       {'desc': 'CREATE_NO_ATTACH size_gb exceeds quota [FAIL]',
        'm': 'gce_pd',
        'a': 'name=%s size_gb=9999 zone=%s' % ("big-disk", ZONE),
        'r': '127.0.0.1 | FAILED >> {"changed": false, "failed": true, "msg": "Requested disk size exceeds quota"}',
       },
       {'desc': 'CREATE_NO_ATTACH create the disk [success]',
        'm': 'gce_pd',
        'a': 'name=%s zone=%s' % (DNAME, ZONE),
        'r': '127.0.0.1 | success >> {"changed": true, "name": "%s", "size_gb": 10, "state": "present", "zone": "%s"}' % (DNAME, ZONE),
       },
       {'desc': 'CREATE_NO_ATTACH but disk already exists [success]',
        'm': 'gce_pd',
        'a': 'name=%s zone=%s' % (DNAME, ZONE),
        'r': '127.0.0.1 | success >> {"changed": false, "name": "%s", "size_gb": 10, "state": "present", "zone": "%s"}' % (DNAME, ZONE),
       },
     ],
     'teardown': ['gcutil deletedisk -f "%s" --zone=%s' % (DNAME, ZONE),
                  'sleep 10'],
    },

    {'id': '03', 'desc': 'Create and attach disk',
     'setup': ['gcutil addinstance "%s" --zone=%s --machine_type=%s --network=%s --service_account_scopes="%s" --image="%s" --persistent_boot_disk=%s' % (INAME2, ZONE, TYPE, NETWORK, SCOPES, IMAGE, USE_PD),
               'gcutil addinstance "%s" --zone=%s --machine_type=%s --network=%s --service_account_scopes="%s" --image="%s" --persistent_boot_disk=%s' % (INAME, ZONE, "g1-small", NETWORK, SCOPES, IMAGE, USE_PD),
               'gcutil adddisk "%s" --size_gb=2 --zone=%s' % (DNAME, ZONE),
               'gcutil adddisk "%s" --size_gb=2 --zone=%s --wait_until_complete' % (DNAME2, ZONE),],
     'tests': [
       {'desc': 'CREATE_AND_ATTACH "string" for size_gb [FAIL]',
        'm': 'gce_pd',
        'a': 'name=%s size_gb="foo" instance_name=%s zone=%s' % (DNAME, INAME, ZONE),
        'r': '127.0.0.1 | FAILED >> {"changed": false, "failed": true, "msg": "Must supply a size_gb larger than 1 GB"}',
       },
       {'desc': 'CREATE_AND_ATTACH negative size_gb [FAIL]',
        'm': 'gce_pd',
        'a': 'name=%s size_gb=-2 instance_name=%s zone=%s' % (DNAME, INAME, ZONE),
        'r': '127.0.0.1 | FAILED >> {"changed": false, "failed": true, "msg": "Must supply a size_gb larger than 1 GB"}',
       },
       {'desc': 'CREATE_AND_ATTACH size_gb exceeds quota [FAIL]',
        'm': 'gce_pd',
        'a': 'name=%s size_gb=9999 instance_name=%s zone=%s' % ("big-disk", INAME, ZONE),
        'r': '127.0.0.1 | FAILED >> {"changed": false, "failed": true, "msg": "Requested disk size exceeds quota"}',
       },
       {'desc': 'CREATE_AND_ATTACH missing instance [FAIL]',
        'm': 'gce_pd',
        'a': 'name=%s instance_name=%s zone=%s' % (DNAME, "missing-instance", ZONE),
        'r': '127.0.0.1 | FAILED >> {"changed": false, "failed": true, "msg": "Instance %s does not exist in zone %s"}' % ("missing-instance", ZONE),
       },
       {'desc': 'CREATE_AND_ATTACH disk exists but not attached [success]',
        'peek_before': ["gcutil --format=csv listinstances --zone=%s --filter=\"name eq 'aaaa.*'\"" % (ZONE)],
        'm': 'gce_pd',
        'a': 'name=%s instance_name=%s zone=%s' % (DNAME, INAME, ZONE),
        'r': '127.0.0.1 | success >> {"attached_mode": "READ_ONLY", "attached_to_instance": "%s", "changed": true, "name": "%s", "size_gb": 2, "state": "present", "zone": "%s"}' % (INAME, DNAME, ZONE),
        'peek_after': ["gcutil --format=csv listinstances --zone=%s --filter=\"name eq 'aaaa.*'\"" % (ZONE)],
       },
       {'desc': 'CREATE_AND_ATTACH disk exists already attached [success]',
        'm': 'gce_pd',
        'a': 'name=%s instance_name=%s zone=%s' % (DNAME, INAME, ZONE),
        'r': '127.0.0.1 | success >> {"attached_mode": "READ_ONLY", "attached_to_instance": "%s", "changed": false, "name": "%s", "size_gb": 2, "state": "present", "zone": "%s"}' % (INAME, DNAME, ZONE),
       },
       {'desc': 'CREATE_AND_ATTACH attached RO, attempt RO to 2nd inst [success]',
        'peek_before': ["gcutil --format=csv listinstances --zone=%s --filter=\"name eq 'aaaa.*'\"" % (ZONE)],
        'm': 'gce_pd',
        'a': 'name=%s instance_name=%s zone=%s' % (DNAME, INAME2, ZONE),
        'r': '127.0.0.1 | success >> {"attached_mode": "READ_ONLY", "attached_to_instance": "%s", "changed": true, "name": "%s", "size_gb": 2, "state": "present", "zone": "%s"}' % (INAME2, DNAME, ZONE),
        'peek_after': ["gcutil --format=csv listinstances --zone=%s --filter=\"name eq 'aaaa.*'\"" % (ZONE)],
       },
       {'desc': 'CREATE_AND_ATTACH attached RO, attach RW to self [FAILED no-op]',
        'peek_before': ["gcutil --format=csv listinstances --zone=%s --filter=\"name eq 'aaaa.*'\"" % (ZONE)],
        'm': 'gce_pd',
        'a': 'name=%s instance_name=%s zone=%s mode=READ_WRITE' % (DNAME, INAME, ZONE),
        'r': '127.0.0.1 | success >> {"attached_mode": "READ_ONLY", "attached_to_instance": "%s", "changed": false, "name": "%s", "size_gb": 2, "state": "present", "zone": "%s"}' % (INAME, DNAME, ZONE),
       },
       {'desc': 'CREATE_AND_ATTACH attached RW, attach RW to other [FAIL]',
        'setup': ['gcutil attachdisk --disk=%s,mode=READ_WRITE --zone=%s %s' % (DNAME2, ZONE, INAME), 'sleep 10'],
        'peek_before': ["gcutil --format=csv listinstances --zone=%s --filter=\"name eq 'aaaa.*'\"" % (ZONE)],
        'm': 'gce_pd',
        'a': 'name=%s instance_name=%s zone=%s mode=READ_WRITE' % (DNAME2, INAME2, ZONE),
        'r': "127.0.0.1 | FAILED >> {\"changed\": false, \"failed\": true, \"msg\": \"Unexpected response: HTTP return_code[200], API error code[RESOURCE_IN_USE] and message: The disk resource 'projects/%s/zones/%s/disks/%s' is already being used in read-write mode\"}" % (PROJECT, ZONE, DNAME2),
        'peek_after': ["gcutil --format=csv listinstances --zone=%s --filter=\"name eq 'aaaa.*'\"" % (ZONE)],
       },
       {'desc': 'CREATE_AND_ATTACH attach too many disks to inst [FAIL]',
        'setup': ['gcutil adddisk aa-disk-dummy --size_gb=2 --zone=%s' % (ZONE),
                  'gcutil adddisk aa-disk-dummy2 --size_gb=2 --zone=%s --wait_until_complete' % (ZONE),
                  'gcutil attachdisk --disk=aa-disk-dummy --zone=%s %s' % (ZONE, INAME),
                  'sleep 5'],
        'peek_before': ["gcutil --format=csv listinstances --zone=%s --filter=\"name eq 'aaaa.*'\"" % (ZONE)],
        'm': 'gce_pd',
        'a': 'name=%s instance_name=%s zone=%s' % ("aa-disk-dummy2", INAME, ZONE),
        'r': "127.0.0.1 | FAILED >> {\"changed\": false, \"failed\": true, \"msg\": \"Unexpected response: HTTP return_code[200], API error code[LIMIT_EXCEEDED] and message: Exceeded limit 'maximum_persistent_disks' on resource 'projects/%s/zones/%s/instances/%s'. Limit: 4\"}" % (PROJECT, ZONE, INAME),
        'teardown': ['gcutil detachdisk --device_name=aa-disk-dummy --zone=%s %s' % (ZONE, INAME),
                     'sleep 3',
                     'gcutil deletedisk -f aa-disk-dummy --zone=%s' % (ZONE),
                     'sleep 10',
                     'gcutil deletedisk -f aa-disk-dummy2 --zone=%s' % (ZONE),
                     'sleep 10'],
       },
     ],
     'teardown': ['gcutil deleteinstance -f "%s" --zone=%s' % (INAME2, ZONE),
                  'sleep 15',
                  'gcutil deleteinstance -f "%s" --zone=%s' % (INAME, ZONE),
                  'sleep 15',
                  'gcutil deletedisk -f "%s" --zone=%s' % (INAME, ZONE),
                  'sleep 10',
                  'gcutil deletedisk -f "%s" --zone=%s' % (INAME2, ZONE),
                  'sleep 10',
                  'gcutil deletedisk -f "%s" --zone=%s' % (DNAME, ZONE),
                  'sleep 10',
                  'gcutil deletedisk -f "%s" --zone=%s' % (DNAME2, ZONE),
                  'sleep 10'],
    },

    {'id': '04', 'desc': 'Delete / destroy instances',
     'setup': ['gcutil addinstance "%s" --zone=%s --machine_type=%s --image="%s" --persistent_boot_disk=false' % (INAME, ZONE, TYPE, IMAGE),
               'gcutil addinstance "%s" --zone=%s --machine_type=%s --image="%s" --persistent_boot_disk=false' % (INAME2, ZONE, TYPE, IMAGE),
               'gcutil addinstance "%s" --zone=%s --machine_type=%s --image="%s" --persistent_boot_disk=false' % (INAME3, ZONE, TYPE, IMAGE),
               'gcutil addinstance "%s" --zone=%s --machine_type=%s --image="%s" --persistent_boot_disk=false' % (INAME4, ZONE, TYPE, IMAGE),
               'gcutil addinstance "%s" --wait_until_running --zone=%s --machine_type=%s --image="%s" --persistent_boot_disk=false' % (INAME5, ZONE, TYPE, IMAGE)],
     'tests': [
       {'desc': 'DELETE instance, bad zone param [FAIL]',
        'm': 'gce',
        'a': 'name=missing-inst zone=bogus state=absent',
        'r': '127.0.0.1 | FAILED >> {"failed": true, "msg": "value of zone must be one of: us-central1-a,us-central1-b,us-central2-a,europe-west1-a,europe-west1-b, got: bogus"}',
       },
       {'desc': 'DELETE non-existent instance, no-op [success]',
        'm': 'gce',
        'a': 'name=missing-inst zone=%s state=absent' % (ZONE),
        'r': '127.0.0.1 | success >> {"changed": false, "name": "missing-inst", "state": "absent", "zone": "%s"}' % (ZONE),
       },
       {'desc': 'DELETE an existing named instance [success]',
        'm': 'gce',
        'a': 'name=%s zone=%s state=absent' % (INAME, ZONE),
        'r': '127.0.0.1 | success >> {"changed": true, "name": "%s", "state": "absent", "zone": "%s"}' % (INAME, ZONE),
       },
       {'desc': 'DELETE list of instances with a non-existent one [success]',
        'm': 'gce',
        'a': 'instance_names=%s,missing,%s zone=%s state=absent' % (INAME2,INAME3, ZONE),
        'r': '127.0.0.1 | success >> {"changed": true, "instance_names": ["%s", "%s"], "state": "absent", "zone": "%s"}' % (INAME2, INAME3, ZONE),
       },
       {'desc': 'DELETE list of instances all pre-exist [success]',
        'm': 'gce',
        'a': 'instance_names=%s,%s zone=%s state=absent' % (INAME4,INAME5, ZONE),
        'r': '127.0.0.1 | success >> {"changed": true, "instance_names": ["%s", "%s"], "state": "absent", "zone": "%s"}' % (INAME4, INAME5, ZONE),
       },
     ],
     'teardown': ['gcutil deleteinstance -f "%s" --zone=%s' % (INAME, ZONE),
                  'gcutil deleteinstance -f "%s" --zone=%s' % (INAME2, ZONE),
                  'gcutil deleteinstance -f "%s" --zone=%s' % (INAME3, ZONE),
                  'gcutil deleteinstance -f "%s" --zone=%s' % (INAME4, ZONE),
                  'gcutil deleteinstance -f "%s" --zone=%s' % (INAME5, ZONE),
                  'sleep 10'],
    },

    {'id': '05', 'desc': 'Create instances',
     'setup': ['gcutil adddisk --source_image=%s --zone=%s %s --wait_until_complete' % (IMAGE, ZONE, DNAME7),
              'gcutil addinstance boo --wait_until_running --zone=%s --machine_type=%s --network=%s --disk=%s,mode=READ_WRITE,boot --kernel=%s' % (ZONE,TYPE,NETWORK,DNAME7,KERNEL),
              ],
     'tests': [
       {'desc': 'CREATE_INSTANCE invalid image arg [FAIL]',
        'm': 'gce',
        'a': 'name=foo image=foo',
        'r': '127.0.0.1 | FAILED >> {"changed": false, "failed": true, "msg": "Missing required create instance variable"}',
       },
       {'desc': 'CREATE_INSTANCE metadata a list [FAIL]',
        'strip_numbers': True,
        'm': 'gce',
        'a': 'name=%s zone=%s metadata=\'[\\"foo\\":\\"bar\\",\\"baz\\":1]\'' % (INAME,ZONE),
        'r': '127.0.0.1 | FAILED >> {"failed": true, "msg": "bad metadata syntax"}',
       },
       {'desc': 'CREATE_INSTANCE metadata not a dict [FAIL]',
        'strip_numbers': True,
        'm': 'gce',
        'a': 'name=%s zone=%s metadata=\\"foo\\":\\"bar\\",\\"baz\\":1' % (INAME,ZONE),
        'r': '127.0.0.1 | FAILED >> {"failed": true, "msg": "bad metadata syntax"}',
       },
       {'desc': 'CREATE_INSTANCE with metadata form1 [FAIL]',
        'strip_numbers': True,
        'm': 'gce',
        'a': 'name=%s zone=%s metadata=\'{"foo":"bar","baz":1}\'' % (INAME,ZONE),
        'r': '127.0.0.1 | FAILED >> {"failed": true, "msg": "bad metadata: malformed string"}',
       },
       {'desc': 'CREATE_INSTANCE with metadata form2 [FAIL]',
        'strip_numbers': True,
        'm': 'gce',
        'a': 'name=%s zone=%s metadata={\'foo\':\'bar\',\'baz\':1}' % (INAME,ZONE),
        'r': '127.0.0.1 | FAILED >> {"failed": true, "msg": "bad metadata: malformed string"}',
       },
       {'desc': 'CREATE_INSTANCE with metadata form3 [FAIL]',
        'strip_numbers': True,
        'm': 'gce',
        'a': 'name=%s zone=%s metadata="foo:bar" '% (INAME,ZONE),
        'r': '127.0.0.1 | FAILED >> {"failed": true, "msg": "bad metadata syntax"}',
       },
       {'desc': 'CREATE_INSTANCE with metadata form4 [FAIL]',
        'strip_numbers': True,
        'm': 'gce',
        'a': 'name=%s zone=%s metadata="{\'foo\':\'bar\'}"'% (INAME,ZONE),
        'r': '127.0.0.1 | FAILED >> {"failed": true, "msg": "bad metadata: malformed string"}',
       },
       {'desc': 'CREATE_INSTANCE invalid image arg [FAIL]',
        'm': 'gce',
        'a': 'instance_names=foo,bar image=foo',
        'r': '127.0.0.1 | FAILED >> {"changed": false, "failed": true, "msg": "Missing required create instance variable"}',
       },
       {'desc': 'CREATE_INSTANCE single inst, using defaults [success]',
        'strip_numbers': True,
        'm': 'gce',
        'a': 'name=%s' % (INAME),
        'r': '127.0.0.1 | success >> {"changed": true, "instance_data": [{"image": "debian-7-wheezy-v20130816", "machine_type": "n1-standard-1", "metadata": {}, "name": "%s", "network": "default", "private_ip": "10.240.175.15", "public_ip": "173.255.120.190", "status": "RUNNING", "tags": [], "zone": "%s"}], "name": "%s", "state": "present", "zone": "%s"}' % (INAME, ZONE, INAME, ZONE),
       },
       {'desc': 'CREATE_INSTANCE the same instance again, no-op [success]',
        'strip_numbers': True,
        'm': 'gce',
        'a': 'name=%s' % (INAME),
        'r': '127.0.0.1 | success >> {"changed": false, "instance_data": [{"image": "debian-7-wheezy-v20130816", "machine_type": "n1-standard-1", "metadata": {}, "name": "%s", "network": "default", "private_ip": "10.240.175.15", "public_ip": "173.255.120.190", "status": "RUNNING", "tags": [], "zone": "%s"}], "name": "%s", "state": "present", "zone": "%s"}' % (INAME, ZONE, INAME, ZONE),
       },
       {'desc': 'CREATE_INSTANCE instance with alt type [success]',
        'strip_numbers': True,
        'm': 'gce',
        'a': 'name=%s machine_type=n1-standard-2' % (INAME2),
        'r': '127.0.0.1 | success >> {"changed": true, "instance_data": [{"image": "debian-7-wheezy-v20130816", "machine_type": "n1-standard-2", "metadata": {}, "name": "%s", "network": "default", "private_ip": "10.240.192.227", "public_ip": "173.255.121.233", "status": "RUNNING", "tags": [], "zone": "%s"}], "name": "%s", "state": "present", "zone": "%s"}' % (INAME2, ZONE, INAME2, ZONE),
       },
       {'desc': 'CREATE_INSTANCE instance with root pd [success]',
        'strip_numbers': True,
        'm': 'gce',
        'a': 'name=%s persistent_boot_disk=yes' % (INAME3),
        'r': '127.0.0.1 | success >> {"changed": true, "instance_data": [{"image": null, "machine_type": "n1-standard-1", "metadata": {}, "name": "%s", "network": "default", "private_ip": "10.240.178.140", "public_ip": "173.255.121.176", "status": "RUNNING", "tags": [], "zone": "%s"}], "name": "%s", "state": "present", "zone": "%s"}' % (INAME3, ZONE, INAME3, ZONE),
       },
       {'desc': 'CREATE_INSTANCE instance with root pd, that already exists [success]',
        'setup': ['gcutil adddisk --source_image=%s --zone=%s %s --wait_until_complete' % (IMAGE, ZONE, DNAME6),],
        'strip_numbers': True,
        'm': 'gce',
        'a': 'name=%s zone=%s persistent_boot_disk=yes' % (INAME6, ZONE),
        'r': '127.0.0.1 | success >> {"changed": true, "instance_data": [{"image": null, "machine_type": "n1-standard-1", "metadata": {}, "name": "%s", "network": "default", "private_ip": "10.240.178.140", "public_ip": "173.255.121.176", "status": "RUNNING", "tags": [], "zone": "%s"}], "name": "%s", "state": "present", "zone": "%s"}' % (INAME6, ZONE, INAME6, ZONE),
       },
       {'desc': 'CREATE_INSTANCE instance with root pd attached to other inst [FAIL]',
        'm': 'gce',
        'a': 'name=%s zone=%s persistent_boot_disk=yes' % (INAME7, ZONE),
        'r': '127.0.0.1 | FAILED >> {"failed": true, "msg": "Unexpected error attempting to create instance %s, error: The disk resource \'projects/%s/zones/%s/disks/%s\' is already being used in read-write mode"}' % (INAME7,PROJECT,ZONE,DNAME7),
       },
       {'desc': 'CREATE_INSTANCE use *all* the options! [success]',
        'strip_numbers': True,
        'm': 'gce',
        'a': 'instance_names=%s,%s metadata=\'{\\"foo\\":\\"bar\\", \\"baz\\":1}\' tags=t1,t2,t3 zone=%s image=centos-6-v20130731 persistent_boot_disk=yes' % (INAME4,INAME5,ZONE),
        'r': '127.0.0.1 | success >> {"changed": true, "instance_data": [{"image": null, "machine_type": "n1-standard-1", "metadata": {"baz": "1", "foo": "bar"}, "name": "%s", "network": "default", "private_ip": "10.240.130.4", "public_ip": "173.255.121.97", "status": "RUNNING", "tags": ["t1", "t2", "t3"], "zone": "%s"}, {"image": null, "machine_type": "n1-standard-1", "metadata": {"baz": "1", "foo": "bar"}, "name": "%s", "network": "default", "private_ip": "10.240.207.226", "public_ip": "173.255.121.85", "status": "RUNNING", "tags": ["t1", "t2", "t3"], "zone": "%s"}], "instance_names": ["%s", "%s"], "state": "present", "zone": "%s"}' % (INAME4, ZONE, INAME5, ZONE, INAME4, INAME5, ZONE),
       },
     ],
     'teardown': ['gcutil deleteinstance -f "%s" --zone=%s' % (INAME, ZONE),
                  'gcutil deleteinstance -f "%s" --zone=%s' % (INAME2, ZONE),
                  'gcutil deleteinstance -f "%s" --zone=%s' % (INAME3, ZONE),
                  'gcutil deleteinstance -f "%s" --zone=%s' % (INAME4, ZONE),
                  'gcutil deleteinstance -f "%s" --zone=%s' % (INAME5, ZONE),
                  'gcutil deleteinstance -f "%s" --zone=%s' % (INAME6, ZONE),
                  'gcutil deleteinstance -f "%s" --zone=%s' % (INAME7, ZONE),
                  'gcutil deleteinstance -f boo --zone=%s' % (ZONE),
                  'sleep 10',
                  'gcutil deletedisk -f "%s" --zone=%s' % (INAME3, ZONE),
                  'gcutil deletedisk -f "%s" --zone=%s' % (INAME4, ZONE),
                  'gcutil deletedisk -f "%s" --zone=%s' % (INAME5, ZONE),
                  'gcutil deletedisk -f "%s" --zone=%s' % (INAME6, ZONE),
                  'gcutil deletedisk -f "%s" --zone=%s' % (INAME7, ZONE),
                  'sleep 10'],
    },

    {'id': '06', 'desc': 'Delete / destroy networks and firewall rules',
     'setup': ['gcutil addnetwork --range="%s" --gateway="%s" %s' % (CIDR1, GW1, NETWK1),
               'gcutil addnetwork --range="%s" --gateway="%s" %s' % (CIDR2, GW2, NETWK2),
               'sleep 5',
               'gcutil addfirewall --allowed="tcp:80" --network=%s %s' % (NETWK1, FW1),
               'gcutil addfirewall --allowed="tcp:80" --network=%s %s' % (NETWK2, FW2),
               'sleep 5'],
     'tests': [
       {'desc': 'DELETE bogus named firewall [success]',
        'm': 'gce_net',
        'a': 'fwname=missing-fwrule state=absent',
        'r': '127.0.0.1 | success >> {"changed": false, "fwname": "missing-fwrule", "state": "absent"}',
       },
       {'desc': 'DELETE bogus named network [success]',
        'm': 'gce_net',
        'a': 'name=missing-network state=absent',
        'r': '127.0.0.1 | success >> {"changed": false, "name": "missing-network", "state": "absent"}',
       },
       {'desc': 'DELETE named firewall rule [success]',
        'm': 'gce_net',
        'a': 'fwname=%s state=absent' % (FW1),
        'r': '127.0.0.1 | success >> {"changed": true, "fwname": "%s", "state": "absent"}' % (FW1),
        'teardown': ['sleep 5'], # pause to give GCE time to delete fwrule
       },
       {'desc': 'DELETE unused named network [success]',
        'm': 'gce_net',
        'a': 'name=%s state=absent' % (NETWK1),
        'r': '127.0.0.1 | success >> {"changed": true, "name": "%s", "state": "absent"}' % (NETWK1),
       },
       {'desc': 'DELETE named network *and* fwrule [success]',
        'm': 'gce_net',
        'a': 'name=%s fwname=%s state=absent' % (NETWK2, FW2),
        'r': '127.0.0.1 | success >> {"changed": true, "fwname": "%s", "name": "%s", "state": "absent"}' % (FW2, NETWK2),
       },
     ],
     'teardown': ['gcutil deletenetwork -f %s' % (NETWK1),
                  'gcutil deletenetwork -f %s' % (NETWK2),
                  'sleep 5',
                  'gcutil deletefirewall -f %s' % (FW1),
                  'gcutil deletefirewall -f %s' % (FW2)],
    },

    {'id': '07', 'desc': 'Create networks and firewall rules',
     'setup': ['gcutil addnetwork --range="%s" --gateway="%s" %s' % (CIDR1, GW1, NETWK1),
               'sleep 5',
               'gcutil addfirewall --allowed="tcp:80" --network=%s %s' % (NETWK1, FW1),
               'sleep 5'],
     'tests': [
       {'desc': 'CREATE network without specifying ipv4_range [FAIL]',
        'm': 'gce_net',
        'a': 'name=fail',
        'r': "127.0.0.1 | FAILED >> {\"changed\": false, \"failed\": true, \"msg\": \"Missing required 'ipv4_range' parameter\"}",
       },
       {'desc': 'CREATE network with specifying bad ipv4_range [FAIL]',
        'm': 'gce_net',
        'a': 'name=fail ipv4_range=bad_value',
        'r': "127.0.0.1 | FAILED >> {\"changed\": false, \"failed\": true, \"msg\": \"Unexpected response: HTTP return_code[400], API error code[None] and message: Invalid value for field 'resource.IPv4Range': 'bad_value'.  Must be a CIDR address range that is contained in the RFC1918 private address blocks: [10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16]\"}",
       },
       {'desc': 'CREATE existing network, not changed [success]',
        'm': 'gce_net',
        'a': 'name=%s ipv4_range=%s' % (NETWK1, CIDR1),
        'r': '127.0.0.1 | success >> {"changed": false, "ipv4_range": "%s", "name": "%s", "state": "present"}' % (CIDR1, NETWK1),
       },
       {'desc': 'CREATE new network, changed [success]',
        'm': 'gce_net',
        'a': 'name=%s ipv4_range=%s' % (NETWK2, CIDR2),
        'r': '127.0.0.1 | success >> {"changed": true, "ipv4_range": "10.240.32.0/24", "name": "%s", "state": "present"}' % (NETWK2),
       },
       {'desc': 'CREATE new fw rule missing params [FAIL]',
        'm': 'gce_net',
        'a': 'name=%s fwname=%s' % (NETWK1, FW1),
        'r': '127.0.0.1 | FAILED >> {"changed": false, "failed": true, "msg": "Missing required firewall rule parameter(s)"}',
       },
       {'desc': 'CREATE new fw rule bad params [FAIL]',
        'm': 'gce_net',
        'a': 'name=%s fwname=broken allowed=blah src_tags="one,two"' % (NETWK1),
        'r': "127.0.0.1 | FAILED >> {\"changed\": false, \"failed\": true, \"msg\": \"Unexpected response: HTTP return_code[400], API error code[None] and message: Invalid value for field 'resource.allowed[0].IPProtocol': 'blah'.  Must be one of [\\\"tcp\\\", \\\"udp\\\", \\\"icmp\\\"] or an IP protocol number between 0 and 255\"}",
       },
       {'desc': 'CREATE existing fw rule [success]',
        'm': 'gce_net',
        'a': 'name=%s fwname=%s allowed="tcp:80" src_tags="one,two"' % (NETWK1, FW1),
        'r': '127.0.0.1 | success >> {"allowed": "tcp:80", "changed": false, "fwname": "%s", "ipv4_range": "%s", "name": "%s", "src_range": null, "src_tags": ["one", "two"], "state": "present"}' % (FW1, CIDR1, NETWK1),
       },
       {'desc': 'CREATE new fw rule [success]',
        'm': 'gce_net',
        'a': 'name=%s fwname=%s allowed="tcp:80" src_tags="one,two"' % (NETWK1, FW3),
        'r': '127.0.0.1 | success >> {"allowed": "tcp:80", "changed": true, "fwname": "%s", "ipv4_range": "%s", "name": "%s", "src_range": null, "src_tags": ["one", "two"], "state": "present"}' % (FW3, CIDR1, NETWK1),
       },
       {'desc': 'CREATE new network *and* fw rule [success]',
        'm': 'gce_net',
        'a': 'name=%s ipv4_range=%s fwname=%s allowed="tcp:80" src_tags="one,two"' % (NETWK3, CIDR3, FW4),
        'r': '127.0.0.1 | success >> {"allowed": "tcp:80", "changed": true, "fwname": "%s", "ipv4_range": "%s", "name": "%s", "src_range": null, "src_tags": ["one", "two"], "state": "present"}' % (FW4, CIDR3, NETWK3),
       },
     ],
     'teardown': ['gcutil deletefirewall -f %s' % (FW1),
                  'gcutil deletefirewall -f %s' % (FW2),
                  'gcutil deletefirewall -f %s' % (FW3),
                  'gcutil deletefirewall -f %s' % (FW4),
                  'sleep 5',
                  'gcutil deletenetwork -f %s' % (NETWK1),
                  'gcutil deletenetwork -f %s' % (NETWK2),
                  'gcutil deletenetwork -f %s' % (NETWK3),
                  'sleep 5'],
    },

    {'id': '08', 'desc': 'Create load-balancer resources',
     'setup': ['gcutil addinstance "%s" --zone=%s --machine_type=%s --network=%s --service_account_scopes="%s" --image="%s" --nopersistent_boot_disk' % (INAME, ZONE, TYPE, NETWORK, SCOPES, IMAGE),
               'gcutil addinstance "%s" --wait_until_running --zone=%s --machine_type=%s --network=%s --service_account_scopes="%s" --image="%s" --nopersistent_boot_disk' % (INAME2, ZONE, TYPE, NETWORK, SCOPES, IMAGE),
              ],
     'tests': [
       {'desc': 'Do nothing [FAIL]',
        'm': 'gce_lb',
        'a': 'httphealthcheck_port=7',
        'r': '127.0.0.1 | FAILED >> {"changed": false, "failed": true, "msg": "Nothing to do, please specify a \\\"name\\\" or \\\"httphealthcheck_name\\\" parameter"}',
       },
       {'desc': 'CREATE_HC create basic http healthcheck [success]',
        'm': 'gce_lb',
        'a': 'httphealthcheck_name=%s' % (HC1),
        'r': '127.0.0.1 | success >> {"changed": true, "httphealthcheck_healthy_count": 2, "httphealthcheck_host": null, "httphealthcheck_interval": 5, "httphealthcheck_name": "%s", "httphealthcheck_path": "/", "httphealthcheck_port": 80, "httphealthcheck_timeout": 5, "httphealthcheck_unhealthy_count": 2, "name": null, "state": "present"}' % (HC1),
       },
       {'desc': 'CREATE_HC (repeat, no-op) create basic http healthcheck [success]',
        'm': 'gce_lb',
        'a': 'httphealthcheck_name=%s' % (HC1),
        'r': '127.0.0.1 | success >> {"changed": false, "httphealthcheck_healthy_count": 2, "httphealthcheck_host": null, "httphealthcheck_interval": 5, "httphealthcheck_name": "%s", "httphealthcheck_path": "/", "httphealthcheck_port": 80, "httphealthcheck_timeout": 5, "httphealthcheck_unhealthy_count": 2, "name": null, "state": "present"}' % (HC1),
       },
       {'desc': 'CREATE_HC create custom http healthcheck [success]',
        'm': 'gce_lb',
        'a': 'httphealthcheck_name=%s httphealthcheck_port=1234 httphealthcheck_path="/whatup" httphealthcheck_host="foo" httphealthcheck_interval=300' % (HC2),
        'r': '127.0.0.1 | success >> {"changed": true, "httphealthcheck_healthy_count": 2, "httphealthcheck_host": "foo", "httphealthcheck_interval": 300, "httphealthcheck_name": "%s", "httphealthcheck_path": "/whatup", "httphealthcheck_port": 1234, "httphealthcheck_timeout": 5, "httphealthcheck_unhealthy_count": 2, "name": null, "state": "present"}' % (HC2),
       },
       {'desc': 'CREATE_HC create (broken) custom http healthcheck [FAIL]',
        'm': 'gce_lb',
        'a': 'httphealthcheck_name=%s httphealthcheck_port="string" httphealthcheck_path=7' % (HC3),
        'r': '127.0.0.1 | FAILED >> {"changed": false, "failed": true, "msg": "Unexpected response: HTTP return_code[400], API error code[None] and message: Invalid value for: Expected a signed integer, got \'string\' (class java.lang.String)"}',
       },
       {'desc': 'CREATE_LB create lb, missing region [FAIL]',
        'm': 'gce_lb',
        'a': 'name=%s' % (LB1),
        'r': '127.0.0.1 | FAILED >> {"changed": false, "failed": true, "msg": "Missing required region name"}',
       },
       {'desc': 'CREATE_LB create lb, bogus region [FAIL]',
        'm': 'gce_lb',
        'a': 'name=%s region=bogus' % (LB1),
        'r': '127.0.0.1 | FAILED >> {"changed": false, "failed": true, "msg": "Unexpected response: HTTP return_code[404], API error code[None] and message: The resource \'projects/%s/regions/bogus\' was not found"}' % (PROJECT),
       },
       {'desc': 'CREATE_LB create lb, minimal params [success]',
        'strip_numbers': True,
        'm': 'gce_lb',
        'a': 'name=%s region=%s' % (LB1, REGION),
        'r': '127.0.0.1 | success >> {"changed": true, "external_ip": "173.255.123.245", "httphealthchecks": [], "members": [], "name": "%s", "port_range": "1-65535", "protocol": "tcp", "region": "%s", "state": "present"}' % (LB1, REGION),
       },
       {'desc': 'CREATE_LB create lb full params [success]',
        'strip_numbers': True,
        'm': 'gce_lb',
        'a': 'httphealthcheck_name=%s httphealthcheck_port=5055 httphealthcheck_path="/howami" name=%s port_range=8000-8888 region=%s members=%s/%s,%s/%s' % (HC3,LB2,REGION,ZONE,INAME,ZONE,INAME2),
        'r': '127.0.0.1 | success >> {"changed": true, "external_ip": "173.255.126.81", "httphealthcheck_healthy_count": 2, "httphealthcheck_host": null, "httphealthcheck_interval": 5, "httphealthcheck_name": "%s", "httphealthcheck_path": "/howami", "httphealthcheck_port": 5055, "httphealthcheck_timeout": 5, "httphealthcheck_unhealthy_count": 2, "httphealthchecks": ["%s"], "members": ["%s/%s", "%s/%s"], "name": "%s", "port_range": "8000-8888", "protocol": "tcp", "region": "%s", "state": "present"}' % (HC3,HC3,ZONE,INAME,ZONE,INAME2,LB2,REGION),
       },
      ],
      'teardown': [
        'gcutil deleteinstance --zone=%s -f %s %s' % (ZONE, INAME, INAME2),
        'gcutil deleteforwardingrule --region=%s -f %s %s' % (REGION, LB1, LB2),
        'sleep 10',
        'gcutil deletetargetpool --region=%s -f %s-tp %s-tp' % (REGION, LB1, LB2),
        'sleep 10',
        'gcutil deletehttphealthcheck -f %s %s %s' % (HC1, HC2, HC3),
      ],
    },

    {'id': '09', 'desc': 'Destroy load-balancer resources',
     'setup': ['gcutil addhttphealthcheck %s' % (HC1),
               'sleep 5',
               'gcutil addhttphealthcheck %s' % (HC2),
               'sleep 5',
               'gcutil addtargetpool --health_checks=%s --region=%s %s-tp' % (HC1, REGION, LB1),
               'sleep 5',
               'gcutil addforwardingrule --target=%s-tp --region=%s %s' % (LB1, REGION, LB1),
               'sleep 5',
               'gcutil addtargetpool --region=%s %s-tp' % (REGION, LB2),
               'sleep 5',
               'gcutil addforwardingrule --target=%s-tp --region=%s %s' % (LB2, REGION, LB2),
               'sleep 5',
              ],
     'tests': [
       {'desc': 'DELETE_LB: delete a non-existent LB [success]',
        'm': 'gce_lb',
        'a': 'name=missing state=absent',
        'r': '127.0.0.1 | success >> {"changed": false, "name": "missing", "state": "absent"}',
       },
       {'desc': 'DELETE_LB: delete a non-existent LB+HC [success]',
        'm': 'gce_lb',
        'a': 'name=missing httphealthcheck_name=alsomissing state=absent',
        'r': '127.0.0.1 | success >> {"changed": false, "httphealthcheck_name": "alsomissing", "name": "missing", "state": "absent"}',
       },
       {'desc': 'DELETE_LB: destroy standalone healthcheck [success]',
        'm': 'gce_lb',
        'a': 'httphealthcheck_name=%s state=absent' % (HC2),
        'r': '127.0.0.1 | success >> {"changed": true, "httphealthcheck_name": "%s", "name": null, "state": "absent"}' % (HC2),
       },
       {'desc': 'DELETE_LB: destroy standalone balancer [success]',
        'm': 'gce_lb',
        'a': 'name=%s state=absent' % (LB2),
        'r': '127.0.0.1 | success >> {"changed": true, "name": "%s", "state": "absent"}' % (LB2),
       },
       {'desc': 'DELETE_LB: destroy LB+HC [success]',
        'm': 'gce_lb',
        'a': 'name=%s httphealthcheck_name=%s state=absent' % (LB1, HC1),
        'r': '127.0.0.1 | success >> {"changed": true, "httphealthcheck_name": "%s", "name": "%s", "state": "absent"}' % (HC1,LB1),
       },
     ],
      'teardown': [
        'gcutil deleteforwardingrule --region=%s -f %s %s' % (REGION, LB1, LB2),
        'sleep 10',
        'gcutil deletetargetpool --region=%s -f %s-tp %s-tp' % (REGION, LB1, LB2),
        'sleep 10',
        'gcutil deletehttphealthcheck -f %s %s' % (HC1, HC2),
      ],
    },
]

def main(tests_to_run=[]):
    for test in test_cases:
        if tests_to_run and test['id'] not in tests_to_run:
            continue
        print "=> starting/setup '%s:%s'"% (test['id'], test['desc'])
        if DEBUG: print "=debug>", test['setup']
        for c in test['setup']:
            (s,o) = run(c)
        test_i = 1
        for t in test['tests']:
            if DEBUG: print "=>debug>", test_i, t['desc']
            # run any test-specific setup commands
            if t.has_key('setup'):
                for setup in t['setup']:
                    (status, output) = run(setup)

            # run any 'peek_before' commands
            if t.has_key('peek_before') and PEEKING_ENABLED:
                for setup in t['peek_before']:
                    (status, output) = run(setup)

            # run the ansible test if 'a' exists, otherwise
            # an empty 'a' directive allows test to run
            # setup/teardown for a subsequent test.
            if t['a']:
                if DEBUG: print "=>debug>", t['m'], t['a']
                acmd = "ansible all -o -m %s -a \"%s\"" % (t['m'],t['a'])
                #acmd = "ANSIBLE_KEEP_REMOTE_FILES=1 ansible all -vvv -m %s -a \"%s\"" % (t['m'],t['a'])
                (s,o) = run(acmd)

                # check expected output
                if DEBUG: print "=debug>", o.strip(), "!=", t['r']
                print "=> %s.%02d '%s':" % (test['id'], test_i, t['desc']),
                if t.has_key('strip_numbers'):
                    # strip out all numbers so we don't trip over different
                    # IP addresses
                    is_good = (o.strip().translate(None, "0123456789") == t['r'].translate(None, "0123456789"))
                else:
                    is_good = (o.strip() == t['r'])

                if is_good:
                    print "PASS"
                else:
                    print "FAIL"
                    if VERBOSE:
                        print "=>", acmd
                        print "=> Expected:", t['r']
                        print "=>      Got:", o.strip()

            # run any 'peek_after' commands
            if t.has_key('peek_after') and PEEKING_ENABLED:
                for setup in t['peek_after']:
                    (status, output) = run(setup)

            # run any test-specific teardown commands
            if t.has_key('teardown'):
                for td in t['teardown']:
                    (status, output) = run(td)
            test_i += 1

        print "=> completing/teardown '%s:%s'" % (test['id'], test['desc'])
        if DEBUG: print "=debug>", test['teardown']
        for c in test['teardown']:
            (s,o) = run(c)


if __name__ == '__main__':
    tests_to_run = []
    if len(sys.argv) == 2:
        if sys.argv[1] in ["--help", "--list"]:
            print "usage: %s [id1,id2,...,idN]" % sys.argv[0]
            print "  * An empty argument list will execute all tests"
            print "  * Do not need to specify tests in numerical order"
            print "  * List test categories with --list or --help"
            print ""
            for test in test_cases:
                print "\t%s:%s" % (test['id'], test['desc'])
            sys.exit(0)
        else:
            tests_to_run = sys.argv[1].split(',')
    main(tests_to_run)
