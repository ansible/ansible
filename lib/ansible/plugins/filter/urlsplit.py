# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


from urlparse import urlsplit
from ansible.errors import AnsibleFilterError


def split_url(value, query='', alias='urlsplit'):
    ''' Check if string is an URI and filter it '''

    results = urlsplit(value)

    split_url = dict(
        fragment=results.fragment,
        hostname=results.hostname,
        password=results.password,
        path=results.path,
        port=results.port,
        query=results.query,
        scheme=results.scheme,
        username=results.username
    )

    if query:
        if query not in split_url:
            raise AnsibleFilterError(alias + ': unknown URL component: %s' % query)
        return split_url[query]
    return split_url


# ---- Ansible filters ----
class FilterModule(object):
    ''' URI filter '''

    def filters(self):
        return {
            'urlsplit': split_url
        }
