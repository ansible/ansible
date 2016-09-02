# -*- coding: utf-8 -*-

#
# Copyright (c) 2016 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
            - "The amount of time the module should wait for the instance to
               get into desired state."
        default: 180
requirements:
  - python >= 2.7
  - ovirt-engine-sdk-python >= 4.0.0
notes:
  - "In order to use this module you have to install oVirt Python SDK.
     To ensure it's installed with correct version you can create following task:
     pip: name=ovirt-engine-sdk-python version=4.0.0"
'''
