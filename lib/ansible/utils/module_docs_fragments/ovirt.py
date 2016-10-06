#!/usr/bin/python
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
            - "True if the module should wait for the entity to get into desired state."
    auth:
        required: True
        description:
            - "Dictionary with values needed to create HTTP/HTTPS connection to oVirt:"
            - "C(username)[I(required)] - The name of the user, something like `I(admin@internal)`."
            - "C(password)[I(required)] - The password of the user."
            - "C(url)[I(required)] - A string containing the base URL of the server, usually
            something like `I(https://server.example.com/ovirt-engine/api)`."
            - "C(token) - Token to be used instead of login with username/password."
            - "C(insecure) - A boolean flag that indicates if the server TLS
            certificate and host name should be checked."
            - "C(ca_file) - A PEM file containing the trusted CA certificates. The
            certificate presented by the server will be verified using these CA
            certificates. If `C(ca_file)` parameter is not set, system wide
            CA certificate store is used."
            - "C(kerberos) - A boolean flag indicating if Kerberos authentication
            should be used instead of the default basic authentication."
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
  - ovirt-engine-sdk-python >= 4.0.0
notes:
  - "In order to use this module you have to install oVirt Python SDK.
     To ensure it's installed with correct version you can create the following task:
     pip: name=ovirt-engine-sdk-python version=4.0.0"
'''
