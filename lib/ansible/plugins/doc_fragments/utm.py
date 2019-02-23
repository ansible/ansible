# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Johannes Brunswicker <johannes.brunswicker@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    DOCUMENTATION = r'''
options:
    headers:
        description:
          - A dictionary of additional headers to be sent to POST and PUT requests.
          - Is needed for some modules
        type: dict
        required: false
    utm_host:
        description:
          - The REST Endpoint of the Sophos UTM.
        type: str
        required: true
    utm_port:
        description:
          - The port of the REST interface.
        type: int
        default: 4444
    utm_token:
        description:
          - "The token used to identify at the REST-API. See U(https://www.sophos.com/en-us/medialibrary/\
            PDFs/documentation/UTMonAWS/Sophos-UTM-RESTful-API.pdf?la=en), Chapter 2.4.2."
        type: str
        required: true
    utm_protocol:
        description:
          - The protocol of the REST Endpoint.
        choices: [ http, https ]
        type: str
        default: https
    validate_certs:
        description:
          - Whether the REST interface's ssl certificate should be verified or not.
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
'''
