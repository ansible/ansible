# (c) 2016, Bill Wang <ozbillwang(at)gmail.com>
# (c) 2017, Marat Bakeev <hawara(at)gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    lookup: aws_ssm
    author:
      - Bill Wang <ozbillwang(at)gmail.com>
      - Marat Bakeev <hawara(at)gmail.com>
    version_added: 2.5
    short_description: Get the value for a SSM parameter.
    description:
      - Get the value for an Amazon Simple Systems Manager parameter or a heirarchy of parameters. The first
        argument you pass the lookup can either be a parameter name or a hierarchy of parameters. Hierarchies start
        with a forward slash and end with the parameter name. Up to 5 layers may be specified.
    options:
      aws_profile:
        description: The boto profile to use. You may use environment variables or the default profile as an alternative.
      region:
        description: The region to use. You may use environment variables ar the default profile's region as an alternative.
      decrypt:
        description: A boolean to indicate whether to decrypt the parameter.
        default: false
      bypath:
        description: A boolean to indicate whether the parameter is provided as a hierarchy.
        default: false
      recursive:
        description: A boolean to indicate whether to retrieve all parameters within a hierarchy.
        default: false
      shortnames:
        description: Indicates whether to return the shortened name if using a parameter hierarchy.
        default: false
'''

EXAMPLES = '''
# lookup sample:
- name: lookup ssm parameter store in the current region
  debug: msg="{{ lookup('aws_ssm', 'Hello' ) }}"

- name: lookup a key which doesn't exist, returns ""
  debug: msg="{{ lookup('aws_ssm', 'NoKey') }}"

- name: lookup ssm parameter store in nominated region
  debug: msg="{{ lookup('aws_ssm', 'Hello', 'region=us-east-2' ) }}"

- name: lookup ssm parameter store without decrypted
  debug: msg="{{ lookup('aws_ssm', 'Hello', 'decrypt=False' ) }}"

- name: lookup ssm parameter store in nominated aws profile
  debug: msg="{{ lookup('aws_ssm', 'Hello', 'aws_profile=myprofile' ) }}"

- name: lookup ssm parameter store with all options.
  debug: msg="{{ lookup('aws_ssm', 'Hello', 'decrypt=false', 'region=us-east-2', 'aws_profile=myprofile') }}"

- name: return a dictionary of ssm parameters from a hierarchy path
  debug: msg="{{ lookup('aws_ssm', '/PATH/to/params', 'region=ap-southeast-2', 'bypath', 'recursive=true' ) }}"

- name: return a dictionary of ssm parameters from a hierarchy path with shortened names (param instead of /PATH/to/param)
  debug: msg="{{ lookup('aws_ssm', '/PATH/to/params', 'region=ap-southeast-2', 'shortnames', 'bypath', 'recursive=true' ) }}"

- name: Iterate over a parameter hierarchy
  debug: msg='key contains {{item.Name }} with value {{item.Value}} '
  with_aws_ssm:
    - '/TEST/test-list'
    - 'region=ap-southeast-2'
    - 'bypath'
'''

from ansible.module_utils.ec2 import HAS_BOTO3
from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils.parsing.convert_bool import boolean

try:
    from botocore.exceptions import ClientError
    import boto3
except ImportError:
    pass  # will be captured by imported HAS_BOTO3


class LookupModule(LookupBase):
    def run(self, terms, variables, **kwargs):
        '''
            :param terms: a list of plugin options
                          e.g. ['parameter_name', 'region=us-east-1', 'aws_profile=profile', 'decrypt=false']
            :param variables: config variables
            :return The value of the SSM parameter or None
        '''

        ret = {}
        response = {}
        session = {}
        ssm_dict = {}
        lparams = {}

        if not HAS_BOTO3:
            raise AnsibleError('botocore and boto3 are required.')

        ssm_dict['WithDecryption'] = True

        # check if option 'bypath' is specified, while still allowing to have a parameter with the same name
        if 'bypath' in terms[1:]:
            ssm_dict['Path'] = terms[0]
            del terms[terms[1:].index('bypath') + 1]
        else:
            ssm_dict['Names'] = [terms[0]]

        # Option to return short parameter names in by path lookups
        if 'shortnames' in terms[1:]:
            lparams['shortnames'] = True
            del terms[terms[1:].index('shortnames') + 1]

        if len(terms) > 1:
            for param in terms[1:]:
                if "=" in param:
                    key, value = param.split('=')
                else:
                    raise AnsibleError("ssm parameter store plugin needs key=value pairs, but received %s" % param)

                if key == "region" or key == "aws_profile":
                    session[key] = value

                # recurse or not
                if key == "recursive" and boolean(value):
                    ssm_dict['Recursive'] = True

                # decrypt the value or not
                if key == "decrypt" and boolean(value):
                    ssm_dict['WithDecryption'] = False

        if "aws_profile" in session:
            boto3.setup_default_session(profile_name=session['aws_profile'])

        if "region" in session:
            client = boto3.client('ssm', region_name=session['region'])
        else:
            client = boto3.client('ssm')

        try:
            # Lookup by path
            if 'Path' in ssm_dict:
                response = client.get_parameters_by_path(**ssm_dict)
                paramlist = list()
                paramlist.extend(response['Parameters'])

                # Manual pagination, since boto doesnt support it yet for get_parameters_by_path
                while 'NextToken' in response:
                    response = client.get_parameters_by_path(NextToken=response['NextToken'], **ssm_dict)
                    paramlist.extend(response['Parameters'])

                # shorten parameter names. yes, this will return duplicate names with different values.
                if 'shortnames' in lparams:
                    for x in paramlist:
                        x['Name'] = x['Name'][x['Name'].rfind('/') + 1:]

                if len(paramlist):
                    return paramlist
                else:
                    return None
            # Lookup by parameter name
            else:
                response = client.get_parameters(**ssm_dict)
                ret.update(response)
                if ret['Parameters']:
                    return [ret['Parameters'][0]['Value']]
                else:
                    return None

        except ClientError as e:
            raise AnsibleError("SSM lookup exception: {0}".format(e))
