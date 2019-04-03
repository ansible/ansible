# -*- coding: utf-8 -*-

# Copyright: (c) 2016, Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard oVirt documentation fragment
    DOCUMENTATION = r'''
options:
    wait:
        description:
            - "C(yes) if the module should wait for the entity to get into desired state."
        type: bool
        default: yes
    fetch_nested:
        description:
            - "If I(True) the module will fetch additional data from the API."
            - "It will fetch IDs of the VMs disks, snapshots, etc. User can configure to fetch other
               attributes of the nested entities by specifying C(nested_attributes)."
        type: bool
        version_added: "2.3"
    nested_attributes:
        description:
            - "Specifies list of the attributes which should be fetched from the API."
            - "This parameter apply only when C(fetch_nested) is I(true)."
        type: list
        version_added: "2.3"
    auth:
        description:
            - "Dictionary with values needed to create HTTP/HTTPS connection to oVirt:"
        suboptions:
            username:
                description:
                    - The name of the user, something like I(admin@internal).
                    - Default value is set by C(OVIRT_USERNAME) environment variable.
                type: str
                required: true
            password:
                description:
                    - The password of the user.
                    - Default value is set by C(OVIRT_PASSWORD) environment variable.
                type: str
                required: true
            url:
                description:
                    - A string containing the API URL of the server, usually something like `I(https://server.example.com/ovirt-engine/api)`.
                    - Default value is set by C(OVIRT_URL) environment variable.
                    - Either C(url) or C(hostname) is required.
                type: str
            hostname:
                description:
                    - A string containing the hostname of the server, usually something like `I(server.example.com)`.
                    - Default value is set by C(OVIRT_HOSTNAME) environment variable.
                    - Either C(url) or C(hostname) is required.
                type: str
            token:
                description:
                    - Token to be used instead of login with username/password.
                    - Default value is set by C(OVIRT_TOKEN) environment variable.
                type: str
            insecure:
                description:
                    - A boolean flag that indicates if the server TLS certificate and host name should be checked.
                type: bool
            ca_file:
                description:
                    - A PEM file containing the trusted CA certificates.
                    - The certificate presented by the server will be verified using these CA certificates.
                    - If C(ca_file) parameter is not set, system wide CA certificate store is used.
                    - Default value is set by C(OVIRT_CAFILE) environment variable.
                type: str
            kerberos:
                description:
                    -  A boolean flag indicating if Kerberos authentication should be used instead of the default basic authentication.
                type: bool
            headers:
                description:
                    - Dictionary of HTTP headers to be added to each API call.
                type: dict
        type: dict
        required: true
    timeout:
        description:
            - "The amount of time in seconds the module should wait for the instance to
               get into desired state."
        type: int
        default: 180
    poll_interval:
        description:
            - "Number of the seconds the module waits until another poll request on entity status is sent."
        type: int
        default: 3
requirements:
  - python >= 2.7
  - ovirt-engine-sdk-python >= 4.3.0
notes:
  - "In order to use this module you have to install oVirt Python SDK.
     To ensure it's installed with correct version you can create the following task:
     I(pip: name=ovirt-engine-sdk-python version=4.3.0)"
'''
