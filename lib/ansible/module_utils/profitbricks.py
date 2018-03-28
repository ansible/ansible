# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright 2018 ProfitBricks GmbH
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import re
import time


LOCATIONS = ['us/las',
             'us/ewr',
             'de/fra',
             'de/fkb']

CPU_FAMILIES = ['AMD_OPTERON',
                'INTEL_XEON']

DISK_TYPES = ['HDD',
              'SSD']

BUS_TYPES = ['VIRTIO',
             'IDE']

AVAILABILITY_ZONES = ['AUTO',
                      'ZONE_1',
                      'ZONE_2',
                      'ZONE_3']

PROTOCOLS = ['TCP',
             'UDP',
             'ICMP',
             'ANY']

LICENCE_TYPES = ['LINUX',
                 'WINDOWS',
                 'UNKNOWN',
                 'OTHER',
                 'WINDOWS2016']

uuid_match = re.compile(r'[\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12}', re.I)


def wait_for_completion(profitbricks, promise, wait_timeout, msg):
    if not promise:
        return
    wait_timeout = time.time() + wait_timeout
    while wait_timeout > time.time():
        time.sleep(5)
        operation_result = profitbricks.get_request(
            request_id=promise['requestId'],
            status=True)

        if operation_result['metadata']['status'] == "DONE":
            return
        elif operation_result['metadata']['status'] == "FAILED":
            raise Exception(
                'Request failed to complete ' + msg + ' "' + str(
                    promise['requestId']) + '" to complete.')

    raise Exception('Timed out waiting for async operation ' + msg + ' "' +
                    str(promise['requestId']) + '" to complete.')


def get_resource_id(resource_list, identity):
    """
    Fetch and return the UUID of a resource regardless of whether the name or
    UUID is passed.
    """
    for resource in resource_list['items']:
        if identity in (resource['properties']['name'], resource['id']):
            return resource['id']
    return None


def get_user_id(resource_list, identity):
    """
    Return the UUID of a user regardless of whether the email or UUID is passed.
    """
    for resource in resource_list['items']:
        if identity in (resource['properties']['email'], resource['id']):
            return resource['id']
    return None
