# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


from ansible.errors import AnsibleFilterError
from ansible.module_utils.six.moves.urllib.parse import urlsplit
from ansible.utils import helpers


def split_url(value, query='', alias='urlsplit'):

    results = helpers.object_to_dict(urlsplit(value))

    # Filter out keys we don't want in the results
    filter_keys = [x for x in results if x.startswith(('count', 'geturl', 'index', '_'))]
    [results.pop(x, None) for x in filter_keys]

    # If a query is supplied, make sure it's valid then return it.
    # Otherwise, return the entire dictionary.
    if query:
        if query not in results:
            raise AnsibleFilterError(alias + ': unknown URL component: %s' % query)
        return results[query]
    else:
        return results


# ---- Ansible filters ----
class FilterModule(object):
    ''' URI filter '''

    def filters(self):
        return {
            'urlsplit': split_url
        }
