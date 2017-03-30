# (c) 2015, Ensighten <infra@ensighten.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase

CREDSTASH_INSTALLED = False

try:
    import credstash
    CREDSTASH_INSTALLED = True
except ImportError:
    CREDSTASH_INSTALLED = False


class LookupModule(LookupBase):
    def run(self, terms, variables, **kwargs):

        if not CREDSTASH_INSTALLED:
            raise AnsibleError('The credstash lookup plugin requires credstash to be installed.')

        ret = []
        for term in terms:
            try:
                version = kwargs.pop('version', '')
                region = kwargs.pop('region', None)
                table = kwargs.pop('table', 'credential-store')
                profile_name = kwargs.pop('profile_name', os.getenv('AWS_PROFILE', None))
                aws_access_key_id = kwargs.pop('aws_access_key_id', os.getenv('AWS_ACCESS_KEY_ID', None))
                aws_secret_access_key = kwargs.pop('aws_secret_access_key', os.getenv('AWS_SECRET_ACCESS_KEY', None))
                aws_session_token = kwargs.pop('aws_session_token', os.getenv('AWS_SESSION_TOKEN', None))
                kwargs_pass = {'profile_name': profile_name, 'aws_access_key_id': aws_access_key_id,
                               'aws_secret_access_key': aws_secret_access_key, 'aws_session_token': aws_session_token}
                val = credstash.getSecret(term, version, region, table,
                                          context=kwargs, **kwargs_pass)
            except credstash.ItemNotFound:
                raise AnsibleError('Key {0} not found'.format(term))
            except Exception as e:
                raise AnsibleError('Encountered exception while fetching {0}: {1}'.format(term, e.message))
            ret.append(val)

        return ret
