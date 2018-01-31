# (c) 2016, Bill Wang <ozbillwang(at)gmail.com>
# (c) 2017, Marat Bakeev <hawara(at)gmail.com>
# (c) 2018, Michael De La Rue <siblemitcom.mddlr(at)spamgourmet.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    lookup: aws_ssm
    author:
      - Bill Wang <ozbillwang(at)gmail.com>
      - Marat Bakeev <hawara(at)gmail.com>
      - Michael De La Rue <siblemitcom.mddlr@spamgourmet.com>
    version_added: 2.5
    short_description: Get the value for a SSM parameter.
    description:
      - Get the value for an Amazon Simple Systems Manager parameter or a heirarchy of parameters. The first
        argument you pass the lookup can either be a parameter name or a hierarchy of parameters. Hierarchies start
        with a forward slash and end with the parameter name. Up to 5 layers may be specified.
    options:
      region:
        description: The region to use. You may use environment variables ar the default profile's region as an alternative.
      aws_profile:
        description: The boto profile to use. You may use environment variables or the default profile as an alternative.

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
  debug: msg="{{ lookup('aws_ssm', 'Hello', region=us-east-2 ) }}"

- name: lookup ssm parameter store without decrypted
  debug: msg="{{ lookup('aws_ssm', 'Hello', decrypt=False ) }}"

- name: lookup ssm parameter store in nominated aws profile
  debug: msg="{{ lookup('aws_ssm', 'Hello', aws_profile=myprofile ) }}"

- name: lookup ssm parameter store with all options.
  debug: msg="{{ lookup('aws_ssm', 'Hello', decrypt=false, region=us-east-2, aws_profile=myprofile') }}"

- name: return a dictionary of ssm parameters from a hierarchy path
  debug: msg="{{ lookup('aws_ssm', '/PATH/to/params', region=ap-southeast-2, bypath=true, recursive=true' ) }}"

- name: return a dictionary of ssm parameters from a hierarchy path with shortened names (param instead of /PATH/to/param)
  debug: msg="{{ lookup('aws_ssm', '/PATH/to/params', region=ap-southeast-2, shortnames, bypath=true, recursive=true ) }}"

- name: Iterate over a parameter hierarchy
  debug: msg='key contains {{item.Name }} with value {{item.Value}} '
  with_aws_ssm:
    - '/TEST/test-list region=ap-southeast-2, bypath'
'''
# FIXME the last one is probably not true yet.

from ansible.module_utils.ec2 import HAS_BOTO3, boto3_tag_list_to_ansible_dict
from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

try:
    from botocore.exceptions import ClientError
    import botocore
    import boto3
except ImportError:
    pass  # will be captured by imported HAS_BOTO3


def _boto3_conn(region, credentials):
    if 'boto_profile' in credentials:
        boto_profile = credentials.pop('boto_profile')
    else:
        boto_profile = None

    try:
        connection = boto3.session.Session(profile_name=boto_profile).client('ssm', region, **credentials)
    except (botocore.exceptions.ProfileNotFound, botocore.exceptions.PartialCredentialsError) as e:
        if boto_profile:
            try:
                connection = boto3.session.Session(profile_name=boto_profile).client('ssm', region)
            except (botocore.exceptions.ProfileNotFound, botocore.exceptions.PartialCredentialsError) as e:
                raise AnsibleError("Insufficient credentials found.")
        else:
            raise AnsibleError("Insufficient credentials found.")
    return connection


class LookupModule(LookupBase):
    def run(self, terms, variables, boto_profile=None, aws_secret_key=None, aws_access_key=None,
            aws_security_token=None, region=None, bypath=False, shortnames=False, recursive=False,
            decrypt=True):
        '''
            :param terms: a list of lookups to run
                e.g. ['parameter_name', 'parameter_name_too' ]
            :param variables: ansible variables active at the time of the lookup
            :keyword args: keyword arguments used for configuring the lookup
                - aws_secret_key / aws_access_key / aws_security_token - AWS credentials
                - region - the AWS region in which to do the lookup
                - bypath - set to true to do a lookup of variables under a path
                - recursive - set to true to do a recurse to paths below the path (needs bypath)
            :return A list of parameter values or a list of dictionaries if doing a bypath lookup
        '''

        if not HAS_BOTO3:
            raise AnsibleError('botocore and boto3 are required for aws_ssm lookup.')

        ret = []
        response = {}
        ssm_dict = {}

        credentials = {}
        credentials['boto_profile'] = boto_profile
        credentials['aws_secret_access_key'] = aws_secret_key
        credentials['aws_access_key_id'] = aws_access_key
        credentials['aws_session_token'] = aws_security_token

        client = _boto3_conn(region, credentials)

        ssm_dict['WithDecryption'] = decrypt

        # Lookup by path
        if bypath:
            for term in terms:
                ssm_dict["Path"] = term
                display.vvv("AWS_ssm path lookup term: %s in region: %s" % (term, region))
                try:
                    response = client.get_parameters_by_path(**ssm_dict)
                except ClientError as e:
                    raise AnsibleError("SSM lookup exception: {0}".format(e))
                paramlist = list()
                paramlist.extend(response['Parameters'])

                # Manual pagination, since boto doesn't support it yet for get_parameters_by_path
                while 'NextToken' in response:
                    response = client.get_parameters_by_path(NextToken=response['NextToken'], **ssm_dict)
                    paramlist.extend(response['Parameters'])

                # shorten parameter names. yes, this will return duplicate names with different values.
                if shortnames:
                    for x in paramlist:
                        x['Name'] = x['Name'][x['Name'].rfind('/') + 1:]

                display.vvvv("AWS_ssm path lookup returned: %s" % str(paramlist))
                if len(paramlist):
                    ret.append(boto3_tag_list_to_ansible_dict(paramlist,
                                                              tag_name_key_name="Name",
                                                              tag_value_key_name="Value"))
                else:
                    return None
            # Lookup by parameter name - always returns a list with one or no entry.
        else:
            display.vvv("AWS_ssm name lookup term: %s" % terms)
            ssm_dict["Names"] = terms
            try:
                response = client.get_parameters(**ssm_dict)
            except ClientError as e:
                raise AnsibleError("SSM lookup exception: {0}".format(e))
            if len(response['Parameters']) == len(terms):
                ret = [p['Value'] for p in response['Parameters']]
            else:
                raise AnsibleError('Undefined AWS SSM parameter: %s ' % str(response['InvalidParameters']))

        return ret
