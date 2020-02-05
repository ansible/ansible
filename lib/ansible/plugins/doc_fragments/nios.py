# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Peter Sprygada <psprygada@ansible.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = r'''
options:
  provider:
    description:
      - A dict object containing connection details.
    type: dict
    suboptions:
      host:
        description:
          - Specifies the DNS host name or address for connecting to the remote
            instance of NIOS WAPI over REST
          - Value can also be specified using C(INFOBLOX_HOST) environment
            variable.
        type: str
        required: true
      username:
        description:
          - Configures the username to use to authenticate the connection to
            the remote instance of NIOS.
          - Value can also be specified using C(INFOBLOX_USERNAME) environment
            variable.
        type: str
      password:
        description:
          - Specifies the password to use to authenticate the connection to
            the remote instance of NIOS.
          - Value can also be specified using C(INFOBLOX_PASSWORD) environment
            variable.
        type: str
      validate_certs:
        description:
          - Boolean value to enable or disable verifying SSL certificates
          - Value can also be specified using C(INFOBLOX_SSL_VERIFY) environment
            variable.
        type: bool
        default: no
        aliases: [ ssl_verify ]
      http_request_timeout:
        description:
          - The amount of time before to wait before receiving a response
          - Value can also be specified using C(INFOBLOX_HTTP_REQUEST_TIMEOUT) environment
            variable.
        type: int
        default: 10
      max_retries:
        description:
          - Configures the number of attempted retries before the connection
            is declared usable
          - Value can also be specified using C(INFOBLOX_MAX_RETRIES) environment
            variable.
        type: int
        default: 3
      wapi_version:
        description:
          - Specifies the version of WAPI to use
          - Value can also be specified using C(INFOBLOX_WAP_VERSION) environment
            variable.
          - Until ansible 2.8 the default WAPI was 1.4
        type: str
        default: '2.1'
      max_results:
        description:
          - Specifies the maximum number of objects to be returned,
            if set to a negative number the appliance will return an error when the
            number of returned objects would exceed the setting.
          - Value can also be specified using C(INFOBLOX_MAX_RESULTS) environment
            variable.
        type: int
        default: 1000
notes:
  - "This module must be run locally, which can be achieved by specifying C(connection: local)."
  - Please read the :ref:`nios_guide` for more detailed information on how to use Infoblox with Ansible.

'''
