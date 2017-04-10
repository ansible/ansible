# (c) 2016, Bill Wang <ozbillwang(at)gmail.com>
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

from ansible.module_utils.ec2 import HAS_BOTO3
from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase

try:
    from botocore.exceptions import ClientError
    import boto3
except ImportError:
    pass  # will be captured by imported HAS_BOTO3


class LookupModule(LookupBase):
    def run(self, terms, variables, **kwargs):
        '''
        # lookup sample:
        - name: lookup ssm parameter store in the current region
          debug: msg="{{ lookup('ssm', 'Hello' ) }}"

        - name: lookup a key which doesn't exist, return ""
          debug: msg="{{ lookup('ssm', 'NoKey') }}"

        - name: lookup ssm parameter store in nominated region
          debug: msg="{{ lookup('ssm', 'Hello', 'region=us-east-2' ) }}"

        - name: lookup ssm parameter store without decrypted
          debug: msg="{{ lookup('ssm', 'Hello', 'decrypt=False' ) }}"

        - name: lookup ssm parameter store in nominated aws profile
          debug: msg="{{ lookup('ssm', 'Hello', 'aws_profile=myprofile' ) }}"

        - name: lookup ssm parameter store with all options.
          debug: msg="{{ lookup('ssm', 'Hello', 'decrypt=false', 'region=us-east-2', 'aws_profile=myprofile') }}"
        '''

        ret = {}
        response = {}
        session = {}
        ssm_dict = {}

        if not HAS_BOTO3:
            raise AnsibleError('botocore and boto3 are required.')

        ssm_dict['WithDecryption'] = True
        ssm_dict['Names'] = [terms[0]]

        if len(terms) > 1:
            for param in terms[1:]:
                if "=" in param:
                    key, value = param.split('=')
                else:
                    raise AnsibleError("ssm parameter store plugin needs key=value pairs, but received %s" % param)

                if key == "region" or key == "aws_profile":
                    session[key] = value

                # decrypt the value or not
                if key == "decrypt" and value.lower() == "false":
                    ssm_dict['WithDecryption'] = False

        if "aws_profile" in session:
            boto3.setup_default_session(profile_name=session['aws_profile'])

        if "region" in session:
            client = boto3.client('ssm', region_name=session['region'])
        else:
            client = boto3.client('ssm')

        try:
            response = client.get_parameters(**ssm_dict)
        except ClientError:
            raise AnsibleError("ssm parameter store plugin can't get parameters, is AWS access key correct and not expired?")

        ret.update(response)

        if ret['Parameters']:
            return [ret['Parameters'][0]['Value']]
        else:
            return None
