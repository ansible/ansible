# Copyright 2018, Ansible by Red Hat.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

VERSION = '3.3.0'
# This is the release number for the RPM builds
RELEASE = 1
CUR_API_VERSION = 'v2'

LAUNCH_TYPE_CHOICES = [
    'manual', 'relaunch', 'relaunch', 'callback',
    'scheduled', 'dependency', 'workflow', 'sync', 'scm'
]

STATUS_CHOICES = [
    'new', 'pending', 'waiting', 'running', 'successful',
    'failed', 'error', 'canceled'
]

INVENTORY_SOURCE_CHOICES = [
    '', 'file', 'scm', 'ec2', 'vmware', 'gce', 'azure', 'azure_rm', 'openstack',
    'satellite6', 'cloudforms', 'custom'
]
