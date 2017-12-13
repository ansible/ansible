# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Michael DeHaan <michael.dehaan@gmail.com>, 2012-2013
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
import re

from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.cloud import CloudRetry
from ansible.module_utils.six import string_types, binary_type, text_type

try:
    import boto
    import boto.ec2  # boto does weird import stuff
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

try:
    import boto3
    import botocore
    HAS_BOTO3 = True
except:
    HAS_BOTO3 = False

try:
    # Although this is to allow Python 3 the ability to use the custom comparison as a key, Python 2.7 also
    # uses this (and it works as expected). Python 2.6 will trigger the ImportError.
    from functools import cmp_to_key
    PY3_COMPARISON = True
except ImportError:
    PY3_COMPARISON = False


class AnsibleAWSError(Exception):
    pass


def _botocore_exception_maybe():
    """
    Allow for boto3 not being installed when using these utils by wrapping
    botocore.exceptions instead of assigning from it directly.
    """
    if HAS_BOTO3:
        return botocore.exceptions.ClientError
    return type(None)


class AWSRetry(CloudRetry):
    base_class = _botocore_exception_maybe()

    @staticmethod
    def status_code_from_exception(error):
        return error.response['Error']['Code']

    @staticmethod
    def found(response_code, catch_extra_error_codes=None):
        # This list of failures is based on this API Reference
        # http://docs.aws.amazon.com/AWSEC2/latest/APIReference/errors-overview.html
        #
        # TooManyRequestsException comes from inside botocore when it
        # does retrys, unfortunately however it does not try long
        # enough to allow some services such as API Gateway to
        # complete configuration.  At the moment of writing there is a
        # botocore/boto3 bug open to fix this.
        #
        # https://github.com/boto/boto3/issues/876 (and linked PRs etc)
        retry_on = [
            'RequestLimitExceeded', 'Unavailable', 'ServiceUnavailable',
            'InternalFailure', 'InternalError', 'TooManyRequestsException',
            'Throttling'
        ]
        if catch_extra_error_codes:
            retry_on.extend(catch_extra_error_codes)

        not_found = re.compile(r'^\w+.NotFound')
        return response_code in retry_on or not_found.search(response_code)


def boto3_conn(module, conn_type=None, resource=None, region=None, endpoint=None, **params):
    try:
        return _boto3_conn(conn_type=conn_type, resource=resource, region=region, endpoint=endpoint, **params)
    except ValueError as e:
        module.fail_json(msg="Couldn't connect to AWS: %s" % to_native(e))
    except (botocore.exceptions.ProfileNotFound, botocore.exceptions.PartialCredentialsError) as e:
        module.fail_json(msg=to_native(e))
    except botocore.exceptions.NoRegionError as e:
        module.fail_json(msg="The %s module requires a region and none was found in configuration, "
                         "environment variables or module parameters" % module._name)


def _boto3_conn(conn_type=None, resource=None, region=None, endpoint=None, **params):
    profile = params.pop('profile_name', None)

    if conn_type not in ['both', 'resource', 'client']:
        raise ValueError('There is an issue in the calling code. You '
                         'must specify either both, resource, or client to '
                         'the conn_type parameter in the boto3_conn function '
                         'call')

    if conn_type == 'resource':
        resource = boto3.session.Session(profile_name=profile).resource(resource, region_name=region, endpoint_url=endpoint, **params)
        return resource
    elif conn_type == 'client':
        client = boto3.session.Session(profile_name=profile).client(resource, region_name=region, endpoint_url=endpoint, **params)
        return client
    else:
        client = boto3.session.Session(profile_name=profile).client(resource, region_name=region, endpoint_url=endpoint, **params)
        resource = boto3.session.Session(profile_name=profile).resource(resource, region_name=region, endpoint_url=endpoint, **params)
        return client, resource


boto3_inventory_conn = _boto3_conn


def boto_exception(err):
    """
    Extracts the error message from a boto exception.

    :param err: Exception from boto
    :return: Error message
    """
    if hasattr(err, 'error_message'):
        error = err.error_message
    elif hasattr(err, 'message'):
        error = str(err.message) + ' ' + str(err) + ' - ' + str(type(err))
    else:
        error = '%s: %s' % (Exception, err)

    return error


def aws_common_argument_spec():
    return dict(
        ec2_url=dict(),
        aws_secret_key=dict(aliases=['ec2_secret_key', 'secret_key'], no_log=True),
        aws_access_key=dict(aliases=['ec2_access_key', 'access_key']),
        validate_certs=dict(default=True, type='bool'),
        security_token=dict(aliases=['access_token'], no_log=True),
        profile=dict(),
    )


def ec2_argument_spec():
    spec = aws_common_argument_spec()
    spec.update(
        dict(
            region=dict(aliases=['aws_region', 'ec2_region']),
        )
    )
    return spec


def get_aws_connection_info(module, boto3=False):

    # Check module args for credentials, then check environment vars
    # access_key

    ec2_url = module.params.get('ec2_url')
    access_key = module.params.get('aws_access_key')
    secret_key = module.params.get('aws_secret_key')
    security_token = module.params.get('security_token')
    region = module.params.get('region')
    profile_name = module.params.get('profile')
    validate_certs = module.params.get('validate_certs')

    if not ec2_url:
        if 'AWS_URL' in os.environ:
            ec2_url = os.environ['AWS_URL']
        elif 'EC2_URL' in os.environ:
            ec2_url = os.environ['EC2_URL']

    if not access_key:
        if os.environ.get('AWS_ACCESS_KEY_ID'):
            access_key = os.environ['AWS_ACCESS_KEY_ID']
        elif os.environ.get('AWS_ACCESS_KEY'):
            access_key = os.environ['AWS_ACCESS_KEY']
        elif os.environ.get('EC2_ACCESS_KEY'):
            access_key = os.environ['EC2_ACCESS_KEY']
        elif HAS_BOTO and boto.config.get('Credentials', 'aws_access_key_id'):
            access_key = boto.config.get('Credentials', 'aws_access_key_id')
        elif HAS_BOTO and boto.config.get('default', 'aws_access_key_id'):
            access_key = boto.config.get('default', 'aws_access_key_id')
        else:
            # in case access_key came in as empty string
            access_key = None

    if not secret_key:
        if os.environ.get('AWS_SECRET_ACCESS_KEY'):
            secret_key = os.environ['AWS_SECRET_ACCESS_KEY']
        elif os.environ.get('AWS_SECRET_KEY'):
            secret_key = os.environ['AWS_SECRET_KEY']
        elif os.environ.get('EC2_SECRET_KEY'):
            secret_key = os.environ['EC2_SECRET_KEY']
        elif HAS_BOTO and boto.config.get('Credentials', 'aws_secret_access_key'):
            secret_key = boto.config.get('Credentials', 'aws_secret_access_key')
        elif HAS_BOTO and boto.config.get('default', 'aws_secret_access_key'):
            secret_key = boto.config.get('default', 'aws_secret_access_key')
        else:
            # in case secret_key came in as empty string
            secret_key = None

    if not region:
        if 'AWS_REGION' in os.environ:
            region = os.environ['AWS_REGION']
        elif 'AWS_DEFAULT_REGION' in os.environ:
            region = os.environ['AWS_DEFAULT_REGION']
        elif 'EC2_REGION' in os.environ:
            region = os.environ['EC2_REGION']
        else:
            if not boto3:
                if HAS_BOTO:
                    # boto.config.get returns None if config not found
                    region = boto.config.get('Boto', 'aws_region')
                    if not region:
                        region = boto.config.get('Boto', 'ec2_region')
                else:
                    module.fail_json(msg="boto is required for this module. Please install boto and try again")
            elif HAS_BOTO3:
                # here we don't need to make an additional call, will default to 'us-east-1' if the below evaluates to None.
                region = botocore.session.Session(profile=profile_name).get_config_variable('region')
            else:
                module.fail_json(msg="Boto3 is required for this module. Please install boto3 and try again")

    if not security_token:
        if os.environ.get('AWS_SECURITY_TOKEN'):
            security_token = os.environ['AWS_SECURITY_TOKEN']
        elif os.environ.get('AWS_SESSION_TOKEN'):
            security_token = os.environ['AWS_SESSION_TOKEN']
        elif os.environ.get('EC2_SECURITY_TOKEN'):
            security_token = os.environ['EC2_SECURITY_TOKEN']
        elif HAS_BOTO and boto.config.get('Credentials', 'aws_security_token'):
            security_token = boto.config.get('Credentials', 'aws_security_token')
        elif HAS_BOTO and boto.config.get('default', 'aws_security_token'):
            security_token = boto.config.get('default', 'aws_security_token')
        else:
            # in case secret_token came in as empty string
            security_token = None

    if HAS_BOTO3 and boto3:
        boto_params = dict(aws_access_key_id=access_key,
                           aws_secret_access_key=secret_key,
                           aws_session_token=security_token)
        boto_params['verify'] = validate_certs

        if profile_name:
            boto_params['profile_name'] = profile_name

    else:
        boto_params = dict(aws_access_key_id=access_key,
                           aws_secret_access_key=secret_key,
                           security_token=security_token)

        # only set profile_name if passed as an argument
        if profile_name:
            boto_params['profile_name'] = profile_name

        boto_params['validate_certs'] = validate_certs

    for param, value in boto_params.items():
        if isinstance(value, binary_type):
            boto_params[param] = text_type(value, 'utf-8', 'strict')

    return region, ec2_url, boto_params


def get_ec2_creds(module):
    ''' for compatibility mode with old modules that don't/can't yet
        use ec2_connect method '''
    region, ec2_url, boto_params = get_aws_connection_info(module)
    return ec2_url, boto_params['aws_access_key_id'], boto_params['aws_secret_access_key'], region


def boto_fix_security_token_in_profile(conn, profile_name):
    ''' monkey patch for boto issue boto/boto#2100 '''
    profile = 'profile ' + profile_name
    if boto.config.has_option(profile, 'aws_security_token'):
        conn.provider.set_security_token(boto.config.get(profile, 'aws_security_token'))
    return conn


def connect_to_aws(aws_module, region, **params):
    try:
        conn = aws_module.connect_to_region(region, **params)
    except(boto.provider.ProfileNotFoundError):
        raise AnsibleAWSError("Profile given for AWS was not found.  Please fix and retry.")
    if not conn:
        if region not in [aws_module_region.name for aws_module_region in aws_module.regions()]:
            raise AnsibleAWSError("Region %s does not seem to be available for aws module %s. If the region definitely exists, you may need to upgrade "
                                  "boto or extend with endpoints_path" % (region, aws_module.__name__))
        else:
            raise AnsibleAWSError("Unknown problem connecting to region %s for aws module %s." % (region, aws_module.__name__))
    if params.get('profile_name'):
        conn = boto_fix_security_token_in_profile(conn, params['profile_name'])
    return conn


def ec2_connect(module):

    """ Return an ec2 connection"""

    region, ec2_url, boto_params = get_aws_connection_info(module)

    # If we have a region specified, connect to its endpoint.
    if region:
        try:
            ec2 = connect_to_aws(boto.ec2, region, **boto_params)
        except (boto.exception.NoAuthHandlerFound, AnsibleAWSError, boto.provider.ProfileNotFoundError) as e:
            module.fail_json(msg=str(e))
    # Otherwise, no region so we fallback to the old connection method
    elif ec2_url:
        try:
            ec2 = boto.connect_ec2_endpoint(ec2_url, **boto_params)
        except (boto.exception.NoAuthHandlerFound, AnsibleAWSError, boto.provider.ProfileNotFoundError) as e:
            module.fail_json(msg=str(e))
    else:
        module.fail_json(msg="Either region or ec2_url must be specified")

    return ec2


def _camel_to_snake(name, reversible=False):

    def prepend_underscore_and_lower(m):
        return '_' + m.group(0).lower()

    import re
    if reversible:
        upper_pattern = r'[A-Z]'
    else:
        # Cope with pluralized abbreviations such as TargetGroupARNs
        # that would otherwise be rendered target_group_ar_ns
        upper_pattern = r'[A-Z]{3,}s$'

    s1 = re.sub(upper_pattern, prepend_underscore_and_lower, name)
    # Handle when there was nothing before the plural_pattern
    if s1.startswith("_") and not name.startswith("_"):
        s1 = s1[1:]
    if reversible:
        return s1

    # Remainder of solution seems to be https://stackoverflow.com/a/1176023
    first_cap_pattern = r'(.)([A-Z][a-z]+)'
    all_cap_pattern = r'([a-z0-9])([A-Z]+)'
    s2 = re.sub(first_cap_pattern, r'\1_\2', s1)
    return re.sub(all_cap_pattern, r'\1_\2', s2).lower()


def camel_dict_to_snake_dict(camel_dict, reversible=False):
    """
    reversible allows two way conversion of a camelized dict
    such that snake_dict_to_camel_dict(camel_dict_to_snake_dict(x)) == x

    This is achieved through mapping e.g. HTTPEndpoint to h_t_t_p_endpoint
    where the default would be simply http_endpoint, which gets turned into
    HttpEndpoint if recamelized.
    """

    def value_is_list(camel_list):

        checked_list = []
        for item in camel_list:
            if isinstance(item, dict):
                checked_list.append(camel_dict_to_snake_dict(item, reversible))
            elif isinstance(item, list):
                checked_list.append(value_is_list(item))
            else:
                checked_list.append(item)

        return checked_list

    snake_dict = {}
    for k, v in camel_dict.items():
        if isinstance(v, dict):
            snake_dict[_camel_to_snake(k, reversible=reversible)] = camel_dict_to_snake_dict(v, reversible)
        elif isinstance(v, list):
            snake_dict[_camel_to_snake(k, reversible=reversible)] = value_is_list(v)
        else:
            snake_dict[_camel_to_snake(k, reversible=reversible)] = v

    return snake_dict


def _snake_to_camel(snake, capitalize_first=False):
    if capitalize_first:
        return ''.join(x.capitalize() or '_' for x in snake.split('_'))
    else:
        return snake.split('_')[0] + ''.join(x.capitalize() or '_' for x in snake.split('_')[1:])


def snake_dict_to_camel_dict(snake_dict, capitalize_first=False):
    """
    Perhaps unexpectedly, snake_dict_to_camel_dict returns dromedaryCase
    rather than true CamelCase. Passing capitalize_first=True returns
    CamelCase. The default remains False as that was the original implementation
    """

    def camelize(complex_type, capitalize_first=False):
        if complex_type is None:
            return
        new_type = type(complex_type)()
        if isinstance(complex_type, dict):
            for key in complex_type:
                new_type[_snake_to_camel(key, capitalize_first)] = camelize(complex_type[key], capitalize_first)
        elif isinstance(complex_type, list):
            for i in range(len(complex_type)):
                new_type.append(camelize(complex_type[i], capitalize_first))
        else:
            return complex_type
        return new_type

    return camelize(snake_dict, capitalize_first)


def ansible_dict_to_boto3_filter_list(filters_dict):

    """ Convert an Ansible dict of filters to list of dicts that boto3 can use
    Args:
        filters_dict (dict): Dict of AWS filters.
    Basic Usage:
        >>> filters = {'some-aws-id', 'i-01234567'}
        >>> ansible_dict_to_boto3_filter_list(filters)
        {
            'some-aws-id': 'i-01234567'
        }
    Returns:
        List: List of AWS filters and their values
        [
            {
                'Name': 'some-aws-id',
                'Values': [
                    'i-01234567',
                ]
            }
        ]
    """

    filters_list = []
    for k, v in filters_dict.items():
        filter_dict = {'Name': k}
        if isinstance(v, string_types):
            filter_dict['Values'] = [v]
        else:
            filter_dict['Values'] = v

        filters_list.append(filter_dict)

    return filters_list


def boto3_tag_list_to_ansible_dict(tags_list, tag_name_key_name=None, tag_value_key_name=None):

    """ Convert a boto3 list of resource tags to a flat dict of key:value pairs
    Args:
        tags_list (list): List of dicts representing AWS tags.
        tag_name_key_name (str): Value to use as the key for all tag keys (useful because boto3 doesn't always use "Key")
        tag_value_key_name (str): Value to use as the key for all tag values (useful because boto3 doesn't always use "Value")
    Basic Usage:
        >>> tags_list = [{'Key': 'MyTagKey', 'Value': 'MyTagValue'}]
        >>> boto3_tag_list_to_ansible_dict(tags_list)
        [
            {
                'Key': 'MyTagKey',
                'Value': 'MyTagValue'
            }
        ]
    Returns:
        Dict: Dict of key:value pairs representing AWS tags
         {
            'MyTagKey': 'MyTagValue',
        }
    """

    if tag_name_key_name and tag_value_key_name:
        tag_candidates = {tag_name_key_name: tag_value_key_name}
    else:
        tag_candidates = {'key': 'value', 'Key': 'Value'}

    if not tags_list:
        return {}
    for k, v in tag_candidates.items():
        if k in tags_list[0] and v in tags_list[0]:
            return dict((tag[k], tag[v]) for tag in tags_list)
    raise ValueError("Couldn't find tag key (candidates %s) in tag list %s" % (str(tag_candidates), str(tags_list)))


def ansible_dict_to_boto3_tag_list(tags_dict, tag_name_key_name='Key', tag_value_key_name='Value'):

    """ Convert a flat dict of key:value pairs representing AWS resource tags to a boto3 list of dicts
    Args:
        tags_dict (dict): Dict representing AWS resource tags.
        tag_name_key_name (str): Value to use as the key for all tag keys (useful because boto3 doesn't always use "Key")
        tag_value_key_name (str): Value to use as the key for all tag values (useful because boto3 doesn't always use "Value")
    Basic Usage:
        >>> tags_dict = {'MyTagKey': 'MyTagValue'}
        >>> ansible_dict_to_boto3_tag_list(tags_dict)
        {
            'MyTagKey': 'MyTagValue'
        }
    Returns:
        List: List of dicts containing tag keys and values
        [
            {
                'Key': 'MyTagKey',
                'Value': 'MyTagValue'
            }
        ]
    """

    tags_list = []
    for k, v in tags_dict.items():
        tags_list.append({tag_name_key_name: k, tag_value_key_name: to_native(v)})

    return tags_list


def get_ec2_security_group_ids_from_names(sec_group_list, ec2_connection, vpc_id=None, boto3=True):

    """ Return list of security group IDs from security group names. Note that security group names are not unique
     across VPCs.  If a name exists across multiple VPCs and no VPC ID is supplied, all matching IDs will be returned. This
     will probably lead to a boto exception if you attempt to assign both IDs to a resource so ensure you wrap the call in
     a try block
     """

    def get_sg_name(sg, boto3):

        if boto3:
            return sg['GroupName']
        else:
            return sg.name

    def get_sg_id(sg, boto3):

        if boto3:
            return sg['GroupId']
        else:
            return sg.id

    sec_group_id_list = []

    if isinstance(sec_group_list, string_types):
        sec_group_list = [sec_group_list]

    # Get all security groups
    if boto3:
        if vpc_id:
            filters = [
                {
                    'Name': 'vpc-id',
                    'Values': [
                        vpc_id,
                    ]
                }
            ]
            all_sec_groups = ec2_connection.describe_security_groups(Filters=filters)['SecurityGroups']
        else:
            all_sec_groups = ec2_connection.describe_security_groups()['SecurityGroups']
    else:
        if vpc_id:
            filters = {'vpc-id': vpc_id}
            all_sec_groups = ec2_connection.get_all_security_groups(filters=filters)
        else:
            all_sec_groups = ec2_connection.get_all_security_groups()

    unmatched = set(sec_group_list).difference(str(get_sg_name(all_sg, boto3)) for all_sg in all_sec_groups)
    sec_group_name_list = list(set(sec_group_list) - set(unmatched))

    if len(unmatched) > 0:
        # If we have unmatched names that look like an ID, assume they are
        import re
        sec_group_id_list[:] = [sg for sg in unmatched if re.match('sg-[a-fA-F0-9]+$', sg)]
        still_unmatched = [sg for sg in unmatched if not re.match('sg-[a-fA-F0-9]+$', sg)]
        if len(still_unmatched) > 0:
            raise ValueError("The following group names are not valid: %s" % ', '.join(still_unmatched))

    sec_group_id_list += [str(get_sg_id(all_sg, boto3)) for all_sg in all_sec_groups if str(get_sg_name(all_sg, boto3)) in sec_group_name_list]

    return sec_group_id_list


def _hashable_policy(policy, policy_list):
    """
        Takes a policy and returns a list, the contents of which are all hashable and sorted.
        Example input policy:
        {'Version': '2012-10-17',
         'Statement': [{'Action': 's3:PutObjectAcl',
                        'Sid': 'AddCannedAcl2',
                        'Resource': 'arn:aws:s3:::test_policy/*',
                        'Effect': 'Allow',
                        'Principal': {'AWS': ['arn:aws:iam::XXXXXXXXXXXX:user/username1', 'arn:aws:iam::XXXXXXXXXXXX:user/username2']}
                       }]}
        Returned value:
        [('Statement',  ((('Action', (u's3:PutObjectAcl',)),
                          ('Effect', (u'Allow',)),
                          ('Principal', ('AWS', ((u'arn:aws:iam::XXXXXXXXXXXX:user/username1',), (u'arn:aws:iam::XXXXXXXXXXXX:user/username2',)))),
                          ('Resource', (u'arn:aws:s3:::test_policy/*',)), ('Sid', (u'AddCannedAcl2',)))),
         ('Version', (u'2012-10-17',)))]

    """
    if isinstance(policy, list):
        for each in policy:
            tupleified = _hashable_policy(each, [])
            if isinstance(tupleified, list):
                tupleified = tuple(tupleified)
            policy_list.append(tupleified)
    elif isinstance(policy, string_types):
        return [(to_text(policy))]
    elif isinstance(policy, dict):
        sorted_keys = list(policy.keys())
        sorted_keys.sort()
        for key in sorted_keys:
            tupleified = _hashable_policy(policy[key], [])
            if isinstance(tupleified, list):
                tupleified = tuple(tupleified)
            policy_list.append((key, tupleified))

    # ensure we aren't returning deeply nested structures of length 1
    if len(policy_list) == 1 and isinstance(policy_list[0], tuple):
        policy_list = policy_list[0]
    if isinstance(policy_list, list):
        if PY3_COMPARISON:
            policy_list.sort(key=cmp_to_key(py3cmp))
        else:
            policy_list.sort()
    return policy_list


def py3cmp(a, b):
    """ Python 2 can sort lists of mixed types. Strings < tuples. Without this function this fails on Python 3."""
    try:
        if a > b:
            return 1
        elif a < b:
            return -1
        else:
            return 0
    except TypeError as e:
        # check to see if they're tuple-string
        # always say strings are less than tuples (to maintain compatibility with python2)
        str_ind = to_text(e).find('str')
        tup_ind = to_text(e).find('tuple')
        if -1 not in (str_ind, tup_ind):
            if str_ind < tup_ind:
                return -1
            elif tup_ind < str_ind:
                return 1
        raise


def compare_policies(current_policy, new_policy):
    """ Compares the existing policy and the updated policy
        Returns True if there is a difference between policies.
    """
    return set(_hashable_policy(new_policy, [])) != set(_hashable_policy(current_policy, []))


def sort_json_policy_dict(policy_dict):

    """ Sort any lists in an IAM JSON policy so that comparison of two policies with identical values but
    different orders will return true
    Args:
        policy_dict (dict): Dict representing IAM JSON policy.
    Basic Usage:
        >>> my_iam_policy = {'Principle': {'AWS':["31","7","14","101"]}
        >>> sort_json_policy_dict(my_iam_policy)
    Returns:
        Dict: Will return a copy of the policy as a Dict but any List will be sorted
        {
            'Principle': {
                'AWS': [ '7', '14', '31', '101' ]
            }
        }
    """

    def value_is_list(my_list):

        checked_list = []
        for item in my_list:
            if isinstance(item, dict):
                checked_list.append(sort_json_policy_dict(item))
            elif isinstance(item, list):
                checked_list.append(value_is_list(item))
            else:
                checked_list.append(item)

        # Sort list. If it's a list of dictionaries, sort by tuple of key-value
        # pairs, since Python 3 doesn't allow comparisons such as `<` between dictionaries.
        checked_list.sort(key=lambda x: sorted(x.items()) if isinstance(x, dict) else x)
        return checked_list

    ordered_policy_dict = {}
    for key, value in policy_dict.items():
        if isinstance(value, dict):
            ordered_policy_dict[key] = sort_json_policy_dict(value)
        elif isinstance(value, list):
            ordered_policy_dict[key] = value_is_list(value)
        else:
            ordered_policy_dict[key] = value

    return ordered_policy_dict


def map_complex_type(complex_type, type_map):
    """
        Allows to cast elements within a dictionary to a specific type
        Example of usage:

        DEPLOYMENT_CONFIGURATION_TYPE_MAP = {
            'maximum_percent': 'int',
            'minimum_healthy_percent': 'int'
        }

        deployment_configuration = map_complex_type(module.params['deployment_configuration'],
                                                    DEPLOYMENT_CONFIGURATION_TYPE_MAP)

        This ensures all keys within the root element are casted and valid integers
    """

    if complex_type is None:
        return
    new_type = type(complex_type)()
    if isinstance(complex_type, dict):
        for key in complex_type:
            if key in type_map:
                if isinstance(type_map[key], list):
                    new_type[key] = map_complex_type(
                        complex_type[key],
                        type_map[key][0])
                else:
                    new_type[key] = map_complex_type(
                        complex_type[key],
                        type_map[key])
            else:
                return complex_type
    elif isinstance(complex_type, list):
        for i in range(len(complex_type)):
            new_type.append(map_complex_type(
                complex_type[i],
                type_map))
    elif type_map:
        return globals()['__builtins__'][type_map](complex_type)
    return new_type


def compare_aws_tags(current_tags_dict, new_tags_dict, purge_tags=True):
    """
    Compare two dicts of AWS tags. Dicts are expected to of been created using 'boto3_tag_list_to_ansible_dict' helper function.
    Two dicts are returned - the first is tags to be set, the second is any tags to remove. Since the AWS APIs differ t
hese may not be able to be used out of the box.

    :param current_tags_dict:
    :param new_tags_dict:
    :param purge_tags:
    :return: tag_key_value_pairs_to_set: a dict of key value pairs that need to be set in AWS. If all tags are identical this dict will be empty
    :return: tag_keys_to_unset: a list of key names (type str) that need to be unset in AWS. If no tags need to be unset this list will be empty
    """

    tag_key_value_pairs_to_set = {}
    tag_keys_to_unset = []

    for key in current_tags_dict.keys():
        if key not in new_tags_dict and purge_tags:
            tag_keys_to_unset.append(key)

    for key in set(new_tags_dict.keys()) - set(tag_keys_to_unset):
        if new_tags_dict[key] != current_tags_dict.get(key):
            tag_key_value_pairs_to_set[key] = new_tags_dict[key]

    return tag_key_value_pairs_to_set, tag_keys_to_unset
