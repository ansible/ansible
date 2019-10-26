# -*- coding: utf-8 -*-

# Copyright: (c) 2016, Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # info standard oVirt documentation fragment
    DOCUMENTATION = r'''
options:
    fetch_nested:
        description:
            - If I(yes) the module will fetch additional data from the API.
            - It will fetch only IDs of nested entity. It doesn't fetch multiple levels of nested attributes.
              Only the attributes of the current entity. User can configure to fetch other
              attributes of the nested entities by specifying C(nested_attributes).
        type: bool
        version_added: "2.3"
    nested_attributes:
        description:
            - Specifies list of the attributes which should be fetched from the API.
            - This parameter apply only when C(fetch_nested) is I(true).
        type: list
        version_added: "2.3"
    auth:
        description:
            - "Dictionary with values needed to create HTTP/HTTPS connection to oVirt:"
            - C(username)[I(required)] - The name of the user, something like I(admin@internal).
              Default value is set by I(OVIRT_USERNAME) environment variable.
            - "C(password)[I(required)] - The password of the user. Default value is set by I(OVIRT_PASSWORD) environment variable."
            - "C(url)- A string containing the API URL of the server, usually
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
        type: dict
        required: true
requirements:
  - python >= 2.7
  - ovirt-engine-sdk-python >= 4.3.0
notes:
  - "In order to use this module you have to install oVirt Python SDK.
     To ensure it's installed with correct version you can create the following task:
     pip: name=ovirt-engine-sdk-python version=4.3.0"
'''
