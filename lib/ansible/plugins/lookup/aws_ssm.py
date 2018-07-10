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
requirements:
  - boto3
  - botocore
short_description: Get the value for a SSM parameter or all parameters under a path.
description:
  - Get the value for an Amazon Simple Systems Manager parameter or a hierarchy of parameters.
    The first argument you pass the lookup can either be a parameter name or a hierarchy of
    parameters. Hierarchies start with a forward slash and end with the parameter name. Up to
    5 layers may be specified.
  - If looking up an explicitly listed parameter by name which does not exist then the lookup will
    return a None value which will be interpreted by Jinja2 as an empty string.  You can use the
    ```default``` filter to give a default value in this case but must set the second parameter to
    true (see examples below)
  - When looking up a path for parameters under it a dictionary will be returned for each path.
    If there is no parameter under that path then the return will be successful but the
    dictionary will be empty.
  - If the lookup fails due to lack of permissions or due to an AWS client error then the aws_ssm
    will generate an error, normally crashing the current ansible task.  This is normally the right
    thing since ignoring a value that IAM isn't giving access to could cause bigger problems and
    wrong behavour or loss of data.  If you want to continue in this case then you will have to set
    up two ansible tasks, one which sets a variable and ignores failures one which uses the value
    of that variable with a default.  See the examples below.

options:
  decrypt:
    description: A boolean to indicate whether to decrypt the parameter.
    default: false
    type: boolean
  bypath:
    description: A boolean to indicate whether the parameter is provided as a hierarchy.
    default: false
    type: boolean
  recursive:
    description: A boolean to indicate whether to retrieve all parameters within a hierarchy.
    default: false
    type: boolean
  shortnames:
    description: Indicates whether to return the name only without path if using a parameter hierarchy.
    default: false
    type: boolean
'''

EXAMPLES = '''
# lookup sample:
- name: lookup ssm parameter store in the current region
  debug: msg="{{ lookup('aws_ssm', 'Hello' ) }}"

- name: lookup ssm parameter store in nominated region
  debug: msg="{{ lookup('aws_ssm', 'Hello', region='us-east-2' ) }}"

- name: lookup ssm parameter store without decrypted
  debug: msg="{{ lookup('aws_ssm', 'Hello', decrypt=False ) }}"

- name: lookup ssm parameter store in nominated aws profile
  debug: msg="{{ lookup('aws_ssm', 'Hello', aws_profile='myprofile' ) }}"

- name: lookup ssm parameter store with all options.
  debug: msg="{{ lookup('aws_ssm', 'Hello', decrypt=false, region='us-east-2', aws_profile='myprofile') }}"

- name: lookup a key which doesn't exist, returns ""
  debug: msg="{{ lookup('aws_ssm', 'NoKey') }}"

- name: lookup a key which doesn't exist, returning a default ('root')
  debug: msg="{{ lookup('aws_ssm', 'AdminID') | default('root', true) }}"

- name: lookup a key which doesn't exist failing to store it in a fact
  set_fact:
    temp_secret: "{{ lookup('aws_ssm', '/NoAccess/hiddensecret') }}"
  ignore_errors: true

- name: show fact default to "access failed" if we don't have access
  debug: msg="{{ "the secret was:" ~ temp_secret | default('couldn\'t access secret') }}"

- name: return a dictionary of ssm parameters from a hierarchy path
  debug: msg="{{ lookup('aws_ssm', '/PATH/to/params', region='ap-southeast-2', bypath=true, recursive=true ) }}"

- name: return a dictionary of ssm parameters from a hierarchy path with shortened names (param instead of /PATH/to/param)
  debug: msg="{{ lookup('aws_ssm', '/PATH/to/params', region='ap-southeast-2', shortnames=true, bypath=true, recursive=true ) }}"

- name: Iterate over a parameter hierarchy
  debug: msg='key contains {{item.Name}} with value {{item.Value}} '
  loop: '{{ query("aws_ssm", "/TEST/test-list", region="ap-southeast-2", bypath=true) }}'

'''

from ansible.module_utils._text import to_native
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
    except (botocore.exceptions.ProfileNotFound, botocore.exceptions.PartialCredentialsError):
        if boto_profile:
            try:
                connection = boto3.session.Session(profile_name=boto_profile).client('ssm', region)
            # FIXME: we should probably do better passing on of the error information
            except (botocore.exceptions.ProfileNotFound, botocore.exceptions.PartialCredentialsError):
                raise AnsibleError("Insufficient credentials found.")
        else:
            raise AnsibleError("Insufficient credentials found.")
    return connection


class LookupModule(LookupBase):
    def run(self, terms, variables=None, boto_profile=None, aws_profile=None,
            aws_secret_key=None, aws_access_key=None, aws_security_token=None, region=None,
            bypath=False, shortnames=False, recursive=False, decrypt=True):
        '''
            :arg terms: a list of lookups to run.
                e.g. ['parameter_name', 'parameter_name_too' ]
            :kwarg variables: ansible variables active at the time of the lookup
            :kwarg aws_secret_key: identity of the AWS key to use
            :kwarg aws_access_key: AWS seret key (matching identity)
            :kwarg aws_security_token: AWS session key if using STS
            :kwarg decrypt: Set to True to get decrypted parameters
            :kwarg region: AWS region in which to do the lookup
            :kwarg bypath: Set to True to do a lookup of variables under a path
            :kwarg recursive: Set to True to recurse below the path (requires bypath=True)
            :returns: A list of parameter values or a list of dictionaries if bypath=True.
        '''

        if not HAS_BOTO3:
            raise AnsibleError('botocore and boto3 are required for aws_ssm lookup.')

        ret = []
        response = {}
        ssm_dict = {}

        credentials = {}
        if aws_profile:
            credentials['boto_profile'] = aws_profile
        else:
            credentials['boto_profile'] = boto_profile
        credentials['aws_secret_access_key'] = aws_secret_key
        credentials['aws_access_key_id'] = aws_access_key
        credentials['aws_session_token'] = aws_security_token

        client = _boto3_conn(region, credentials)

        ssm_dict['WithDecryption'] = decrypt

        # Lookup by path
        if bypath:
            ssm_dict['Recursive'] = recursive
            for term in terms:
                ssm_dict["Path"] = term
                display.vvv("AWS_ssm path lookup term: %s in region: %s" % (term, region))
                try:
                    response = client.get_parameters_by_path(**ssm_dict)
                except ClientError as e:
                    raise AnsibleError("SSM lookup exception: {0}".format(to_native(e)))
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
                    ret.append({})
            # Lookup by parameter name - always returns a list with one or no entry.
        else:
            display.vvv("AWS_ssm name lookup term: %s" % terms)
            ssm_dict["Names"] = terms
            try:
                response = client.get_parameters(**ssm_dict)
            except ClientError as e:
                raise AnsibleError("SSM lookup exception: {0}".format(to_native(e)))
            params = boto3_tag_list_to_ansible_dict(response['Parameters'], tag_name_key_name="Name",
                                                    tag_value_key_name="Value")
            for i in terms:
                if i in params:
                    ret.append(params[i])
                elif i in response['InvalidParameters']:
                    ret.append(None)
                else:
                    raise AnsibleError("Ansible internal error: aws_ssm lookup failed to understand boto3 return value: {0}".format(str(response)))
            return ret

        display.vvvv("AWS_ssm path lookup returning: %s " % str(ret))
        return ret
