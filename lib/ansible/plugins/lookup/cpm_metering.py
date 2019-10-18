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
lookup: cpm_metering
author: "Western Telematic Inc. (@wtinetworkgear)"
version_added: "2.7"
short_description: Get Power and Current data from WTI OOB/Combo and PDU devices
description:
    - "Get Power and Current data from WTI OOB/Combo and PDU devices"
options:
  _terms:
    description:
      - This is the Action to send the module.
    required: true
    choices: [ "getpower", "getcurrent" ]
  cpm_url:
    description:
      - This is the URL of the WTI device  to send the module.
    required: true
  cpm_username:
    description:
      - This is the Username of the WTI device to send the module.
  cpm_password:
    description:
      - This is the Password of the WTI device to send the module.
  use_https:
    description:
      - Designates to use an https connection or http connection.
    required: false
    default: True
    choices: [ True, False ]
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
  startdate:
    description:
      - Start date of the range to look for power data
    required: false
  enddate:
    description:
      - End date of the range to look for power data
    required: false
"""

EXAMPLES = """
# Get Power data
  - name: Get Power data for a given WTI device
  - debug:
        var: lookup('cpm_metering',
                'getpower',
                validate_certs=true,
                use_https=true,
                cpm_url='rest.wti.com',
                cpm_username='restpower',
                cpm_password='restfulpowerpass12')

# Get Current data
  - name: Get Current data for a given WTI device
  - debug:
        var: lookup('cpm_metering',
                'getcurrent',
                validate_certs=true,
                use_https=true,
                cpm_url='rest.wti.com',
                cpm_username='restpower',
                cpm_password='restfulpowerpass12')

# Get Power data for a date range
  - name: Get Power data for a given WTI device given a certain date range
  - debug:
        var: lookup('cpm_metering',
                'getpower',
                validate_certs=true,
                use_https=true,
                cpm_url='rest.wti.com',
                cpm_username='restpower',
                cpm_password='restfulpowerpass12',
                startdate='08-12-2018'
                enddate='08-14-2018')
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
from ansible.utils.display import Display

display = Display()


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        self.set_options(direct=kwargs)

        ret = []
        for term in terms:
            auth = to_text(base64.b64encode(to_bytes('{0}:{1}'.format(self.get_option('cpm_username'), self.get_option('cpm_password')),
                           errors='surrogate_or_strict')))

            additional = ""
            if self.get_option("startdate") is not None and (len(self.get_option("startdate")) > 0):
                if self.get_option("enddate") is not None and (len(self.get_option("enddate")) > 0):
                    additional = "?startdate=" + self.get_option("startdate") + "&enddate=" + self.get_option("enddate")

            if self.get_option('use_https') is True:
                protocol = "https://"
            else:
                protocol = "http://"

            if (term == 'getpower'):
                fullurl = ("%s%s/api/v2/config/power" % (protocol, self.get_option('cpm_url')))
            elif (term == 'getcurrent'):
                fullurl = ("%s%s/api/v2/config/current" % (protocol, self.get_option('cpm_url')))
            else:
                raise AnsibleError("Power command not recognized %s " % (term))

            if (len(additional) > 0):
                fullurl += additional

            display.vvvv("cpm_metering connecting to %s" % fullurl)

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
