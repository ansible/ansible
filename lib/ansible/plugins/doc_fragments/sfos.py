#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Rubén del Campo Gómez <yo@rubendelcampo.es>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

class ModuleDocFragment(object):
    DOCUMENTATION = r'''
options:
    sfos_host:
        description:
          - The Sophos XG endpoint IP address or FQDN. If not set then the value of the SFOS_HOST environment variable is used.
        type: str
        required: true
    sfos_port:
        description:
          - Port you mention in above URL should be same as the port you have configured as Admin Console HTTPS Port from System > Administration > Settings. If not set then the value of the SFOS_PORT environment variable is used.
        type: int
        default: 4444
    sfos_protocol:
        description:
          - The protocol used to communicate with the API endpoint. If not set then the value of the SFOS_PROTOCOL environment variable is used.
        choices: [ http, https ]
        type: str
        default: https
    sfos_username:
        description:
          - The username used to login and who has permission to send API requests. If not set then the value of the SFOS_USERNAME environment variable is used.
        choices: [ http, https ]
        type: str
        required: true
    sfos_password:
        description:
          - The password for the username used to login and who has permission to send API requests. If not set then the value of the SFOS_PASSWORD environment variable is used.
        choices: [ http, https ]
        type: str
        required: true
    validate_certs:
        description:
          - Whether the API interface's ssl certificate should be verified or not. If not set then the value of the SFOS_VALIDATECERTS environment variable is used.
        type: bool
        default: yes
    state:
        description:
          - The desired state of the object.
          - C(present) will create or update an object
          - C(absent) will delete an object if it was present
        type: str
        choices: [ absent, present ]
        default: present
notes:
  - This module requires xmltodict python library.
    Use 'pip install xmltodict' in order to get xmltodict.
  - API access must be enabled in Sophos XG. See U(https://community.sophos.com/kb/en-us/132560)
requirements:
  - xmltodict
'''