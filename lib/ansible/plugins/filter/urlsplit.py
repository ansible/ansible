# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


from ansible.module_utils.six.moves.urllib.parse import urlsplit
from ansible.utils import helpers


def split_url(value, query='', alias='urlsplit'):

    results = helpers.object_to_dict(urlsplit(value))

    return results


# ---- Ansible filters ----
class FilterModule(object):
    ''' URI filter '''

    def filters(self):
        return {
            'urlsplit': split_url
        }
