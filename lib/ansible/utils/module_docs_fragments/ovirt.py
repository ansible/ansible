# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Red Hat, Inc.
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
#


class ModuleDocFragment(object):

    # Standard oVirt documentation fragment
    DOCUMENTATION = '''
options:
    wait:
        description:
            - "I(True) if the module should wait for the entity to get into desired state."
    fetch_nested:
        description:
            - "If I(True) the module will fetch additional data from the API."
            - "It will fetch IDs of the VMs disks, snapshots, etc. User can configure to fetch other
               attributes of the nested entities by specifying C(nested_attributes)."
        version_added: "2.3"
    nested_attributes:
        description:
            - "Specifies list of the attributes which should be fetched from the API."
            - "This parameter apply only when C(fetch_nested) is I(true)."
        version_added: "2.3"
    auth:
        required: True
        description:
            - "Dictionary with values needed to create HTTP/HTTPS connection to oVirt:"
            - C(username)[I(required)] - The name of the user, something like I(admin@internal).
              Default value is set by I(OVIRT_USERNAME) environment variable.
            - "C(password)[I(required)] - The password of the user. Default value is set by I(OVIRT_PASSWORD) environment variable."
            - "C(url) - A string containing the API URL of the server, usually
            something like `I(https://server.example.com/ovirt-engine/api)`. Default value is set by I(OVIRT_URL) environment variable.
            Either C(url) or C(hostname) is required."
            - "C(hostname) - A string containing the hostname of the server, usually
            something like `I(server.example.com)`. Default value is set by I(OVIRT_HOSTNAME) environment variable.
            Either C(url) or C(hostname) is required."
            - "C(token) - Token to be used instead of login with username/password. Default value is set by I(OVIRT_TOKEN) environment variable."
            - "C(insecure) - A boolean flag that indicates if the server TLS
            certificate and host name should be checked."
            - "C(ca_file) - A PEM file containing the trusted CA certificates. The
            certificate presented by the server will be verified using these CA
            certificates. If `C(ca_file)` parameter is not set, system wide
            CA certificate store is used. Default value is set by I(OVIRT_CAFILE) environment variable."
            - "C(kerberos) - A boolean flag indicating if Kerberos authentication
            should be used instead of the default basic authentication."
            - "C(headers) - Dictionary of HTTP headers to be added to each API call."
    timeout:
        description:
            - "The amount of time in seconds the module should wait for the instance to
               get into desired state."
        default: 180
    poll_interval:
        description:
            - "Number of the seconds the module waits until another poll request on entity status is sent."
        default: 3
requirements:
  - python >= 2.7
  - ovirt-engine-sdk-python >= 4.2.4
notes:
  - "In order to use this module you have to install oVirt Python SDK.
     To ensure it's installed with correct version you can create the following task:
     I(pip: name=ovirt-engine-sdk-python version=4.2.4)"
'''
