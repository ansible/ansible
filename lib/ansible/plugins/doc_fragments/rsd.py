# -*- coding: utf-8 -*-

#######################################################
# Copyright (c) 2019 Intel Corporation. All rights reserved.
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Authors:
#   - Marco Chiappero <marco.chiappero@intel.com>
#######################################################


class ModuleDocFragment(object):

    DOCUMENTATION = '''
options:
    id:
        description:
            - Specify the node to act on by specifying 'type' for type
              of identification key and 'value' for its value.
        required: true
        type: dict
        suboptions:
            type:
                description:
                    - Specify type of identification. For best performance
                      it is suggested to use identity as type.
                required: False
                choices:
                    - name
                    - identity
                    - uuid
                default: identity
                type: str
            value:
                description:
                    - Identification signature.
                required: True
                type: str
    podm:
        description:
        - A dictionary containing information for connecting to a remote PODM.
        - A the very least a host has to be provided, but other parameters may
          be optional and/or specified through environment variables.
        required: false
        type: dict
        suboptions:
            host:
                description:
                    - A hostname or IP adress for connecting to PODM.
                    - Alternatively, if not specified, the environment variable
                      C(PODM_HOST) can be used.
                required: true
                type: str
                aliases:
                    - hostname
            port:
                description:
                    - Port for the PODM API service.
                    - The environment variable C(PODM_PORT) can be defined
                      instead.
                default: 8443
                type: int
            protocol:
                description:
                    - Specifies the protocol to be used to connect to PODM
                default: https
                type: str
                choices:
                    - http
                    - https
            validate_cert:
                description:
                    - Whether or not SSL API requests should be verified.
                default: false
                type: bool
                aliases:
                    - verify_cert

    auth:
        description:
            - A dictionary containing PODM access credentials
        type: dict
        suboptions:
            username:
                description:
                    - The username required to interact with PODM API
                    - Especially for security reasons, the environment variable
                      C(PODM_USERNAME) can be provided instead.
                required: true
                type: str
                aliases:
                    - user
            password:
                description:
                    - The password required to interact with PODM API
                    - Especially for security reasons, the environment variable
                      C(PODM_PASSWORD) can be provided instead.
                required: true
                type: str
                aliases:
                    - pass
requirements:
  - rsd-lib > 0.2.2
  - RSD PODM API >= 2.1
  - cachetools
seealso:
    - name: Rack Scale Design documentation
      description: Reference RSD documentation, including the latest PODM API
                   specification containing detailed information on the
                   supported values and options for composition.
      link: https://www.intel.com/content/www/us/en/architecture-and-technology/rack-scale-design/rack-scale-design-resources.html
'''
