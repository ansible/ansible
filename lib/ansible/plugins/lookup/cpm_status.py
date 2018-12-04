# (c) 2018, Western Telematic Inc. <kenp@wti.com>
# (c) 2012-18 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = """
lookup: cpm_status
author: "Western Telematic Inc. (@wtinetworkgear)"
version_added: "2.7"
short_description: Get status and parameters from WTI OOB and PDU devices.
description:
    - "Get various status and parameters from WTI OOB and PDU devices."
options:
  _terms:
    description:
      - This is the Action to send the module.
    required: true
    choices: [ "temperature", "firmware", "status", "alarms" ]
  cpm_url:
    description:
      - This is the URL of the WTI device to send the module.
    required: true
  cpm_username:
    description:
      - This is the Basic Authentication Username of the WTI device to send the module.
    required: true
  cpm_password:
    description:
      - This is the Basic Authentication Password of the WTI device to send the module.
    required: true
  use_https:
    description:
      - Designates to use an https connection or http connection.
    required: false
    type: bool
    default: true
  validate_certs:
    description:
      - If false, SSL certificates will not be validated. This should only be used
        on personally controlled sites using self-signed certificates.
    required: false
    type: bool
    default: true
  use_proxy:
    description: Flag to control if the lookup will observe HTTP proxy environment variables when present.
    type: boolean
    default: True
"""

EXAMPLES = """
# Get temperature
  - name: run Get Device Temperature
  - debug:
        var: lookup('cpm_status',
                'temperature',
                validate_certs=true,
                use_https=true,
                cpm_url='rest.wti.com',
                cpm_username='rest',
                cpm_password='restfulpassword')

# Get firmware version
  - name: Get the firmware version of a given WTI device
  - debug:
        var: lookup('cpm_status',
                'firmware',
                validate_certs=false,
                use_https=true,
                cpm_url="192.168.0.158",
                cpm_username="super",
                cpm_password="super")

# Get status output
  - name: Get the status output from a given WTI device
  - debug:
        var: lookup('cpm_status',
                'status',
                validate_certs=true,
                use_https=true,
                cpm_url="rest.wti.com",
                cpm_username="rest",
                cpm_password="restfulpassword")

# Get Alarm output
  - name: Get the alarms status of a given WTI device
  - debug:
        var: lookup('cpm_status',
                'alarms',
                validate_certs=false,
                use_https=false,
                cpm_url="192.168.0.158",
                cpm_username="super",
                cpm_password="super")
"""

RETURN = """
  _list:
    description: The output JSON returned from the commands sent
    returned: always
    type: str
"""

import base64

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils._text import to_text, to_bytes, to_native
from ansible.module_utils.six.moves.urllib.error import HTTPError, URLError
from ansible.module_utils.urls import open_url, ConnectionError, SSLValidationError


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        self.set_options(direct=kwargs)

        ret = []

        for term in terms:
            auth = to_text(base64.b64encode(to_bytes('{0}:{1}'.format(self.get_option('cpm_username'), self.get_option('cpm_password')),
                           errors='surrogate_or_strict')))

            if self.get_option('use_https') is True:
                protocol = "https://"
            else:
                protocol = "http://"

            if (term == 'temperature'):
                fullurl = ("%s%s/api/v2/status/temperature" % (protocol, self.get_option('cpm_url')))
            elif (term == 'firmware'):
                fullurl = ("%s%s/api/v2/status/firmware" % (protocol, self.get_option('cpm_url')))
            elif (term == 'status'):
                fullurl = ("%s%s/api/v2/status/status" % (protocol, self.get_option('cpm_url')))
            elif (term == 'alarms'):
                fullurl = ("%s%s/api/v2/status/alarms" % (protocol, self.get_option('cpm_url')))
            else:
                raise AnsibleError("Status command not recognized %s " % (term))

            try:
                response = open_url(fullurl, validate_certs=self.get_option('validate_certs'), use_proxy=self.get_option('use_proxy'),
                                    headers={'Content-Type': 'application/json', 'Authorization': "Basic %s" % auth})
            except HTTPError as e:
                raise AnsibleError("Received HTTP error for %s : %s" % (fullurl, to_native(e)))
            except URLError as e:
                raise AnsibleError("Failed lookup url for %s : %s" % (fullurl, to_native(e)))
            except SSLValidationError as e:
                raise AnsibleError("Error validating the server's certificate for %s: %s" % (fullurl, to_native(e)))
            except ConnectionError as e:
                raise AnsibleError("Error connecting to %s: %s" % (fullurl, to_native(e)))

            ret.append(to_text(response.read()))

        return ret
