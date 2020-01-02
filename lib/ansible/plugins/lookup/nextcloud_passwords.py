from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase

try:
    import requests
except ImportError:
    raise AnsibleError("Please install requests library.")

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = """
lookup: nextcloud_passwords
author:
    - Markus Bergholz <markuman@gmail.com>
version_added: 2.10
short_description: read passwords from nextcloud "passwords" app
description:
    - This lookup returns the password stored in nextcloud passwords app based by label
    - See U(https://apps.nextcloud.com/apps/passwords)
options:
  _terms:
    description: Label of the requested password.
    required: True
  host:
    description: host of the requested nextcloud instance (required https)
    required: True
  user:
    description: username of the requested nextcloud passwords user
    required: True
  api_token:
    description: generated api token of the user on the requested nextcloud passwords user
    required: True

notes:
    - This lookup plugin requires a https connection to the requested nextcloud instance.
"""


EXAMPLES = """
- name: Retrieve Password with label "Stackoverflow"
  debug:
    var: lookup('nextcloud_passwords', 'Stackoverflow' , host='nextcloud.tld', user='ansible', api_token='some-token')
"""


class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):

        # get options
        host = kwargs.get('host')
        user = kwargs.get('user')
        token = kwargs.get('api_token')

        if None in [host, user, token]:
            raise AnsibleLookupError('Unable to perform nextcloud passwords lookup. '
                                     'host, user, api_token and label are required.')

        r = requests.get(
            'https://{HOST}/index.php/apps/passwords/api/1.0/password/list'.format(HOST=host),
            auth=(user, token)
        )

        ret = []
        for term in terms:
            try:
                if r.status_code == 200:
                    for item in r.json():
                        if item['label'] == term:
                            ret.append(item['password'])
                else:
                    raise AnsibleParserError()
            except AnsibleParserError:
                raise AnsibleError("nextcloud responded with status code: %d" % r.status_code)

        return ret
