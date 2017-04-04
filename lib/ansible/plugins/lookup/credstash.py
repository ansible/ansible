
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
                if 'profile' not in kwargs:
                    profile_was_set = True
                else:
                    profile_was_set = False
                profile = kwargs.pop('profile', 'default')
                iam_arn_assume_role = kwargs.pop('iam_arn_assume_role', None)
                # As per docs, if profile is set we ignore arn.  Should probably log this.
                # AWS_PROFILE set in environment WILL be respected.
                if iam_arn_assume_role and not profile_was_set:
                    try: 
                        #creds = botocore.session.Session().get_credentials()
                        session_params = credstash.get_session_params(None, iam_arn_assume_role)
                    except Exception as e:
                        raise AnsibleError('error assuming role {0} in profile {1}: {2}'.format(iam_arn_assume_role, profile, e))
                try:
                    val = credstash.getSecret(term, version, region, table, profile_name=profile,
                                          context=kwargs)
                except Exception as e:
                    raise AnsibleError('credstash.getSecret failed with context {}'.format(kwargs))
            except credstash.ItemNotFound:
                raise AnsibleError('Key {0} not found'.format(term))
            except Exception as e:
                raise AnsibleError('Encountered exception while fetching {0}: {1}'.format(term, e.message))
            ret.append(val)

        return ret
