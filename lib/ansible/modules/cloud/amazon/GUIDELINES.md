# Guidelines for AWS modules

The Ansible AWS modules and these guidelines are maintained by the Ansible AWS Working Group.  For
further information see
[the AWS working group community page](https://github.com/ansible/community/tree/master/group-aws).
If you are planning to contribute AWS modules to Ansible then getting in touch with the the working
group will be a good way to start, especially because a similar module may already be under
development.

## Choose Boto3 not Boto

Starting from Ansible 2.0, it has been required that all new AWS modules are written to use boto3.
Please do not add new dependencies on the old boto library.

Prior to 2.0, modules may have been written in boto or boto3. The effort to port all modules to
boto3 has begun.  From Ansible 2.4 it is permissible for modules which previously required boto to
start to migrate to boto3 in order to deliver the functionality previously supported with boto and the
boto dependency can be deleted.

From 2.6, all new modules should use AnsibleAWSModule as a base, or have a documented reason not
to. Using AnsibleAWSModule greatly simplifies exception handling and library management, reducing
the amount of boilerplate code.

## Porting code to AnsibleAWSModule

Change

```
from ansible.module_utils.basic import AnsibleModule
...
module = AnsibleModule(...)
```

to

```
from ansible.module_utils.aws.core import AnsibleAWSModule
...
module = AnsibleAWSModule(...)
```

Few other changes are required. One possible issue that you might encounter is that AnsibleAWSModule
does not inherit methods from AnsibleModule by default, but most useful methods
are included. If you do find an issue, please raise a bug report.

When porting, keep in mind that AnsibleAWSModule also will add the default ec2
argument spec by default. In pre-port modules, you should see common arguments
specfied with:

```
def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state=dict(default='present', choices=['present', 'absent', 'enabled', 'disabled']),
        name=dict(default='default'),
        # ... and so on ...
    ))
    module = AnsibleModule(argument_spec=argument_spec, ...)

# can be replaced with
def main():
    argument_spec = dict(
        state=dict(default='present', choices=['present', 'absent', 'enabled', 'disabled']),
        name=dict(default='default'),
        # ... and so on ...
    )
    module = AnsibleAWSModule(argument_spec=argument_spec, ...)
```

## Bug fixing

Bug fixes to code that relies on boto will still be accepted. When possible, the code should be
ported to use boto3.

## Naming your module

Base the name of the module on the part of AWS that you actually use. (A good rule of thumb is to
take whatever module you use with boto as a starting point).  Don't further abbreviate names - if
something is a well known abbreviation due to it being a major component of AWS, that's fine, but
don't create new ones independently (e.g. VPC, ELB, and similar abbreviations are fine).

Unless the name of your service is quite unique, please consider using "aws_" as a prefix.  For
example "aws_lambda".

## Adding new features

Try to keep backward compatibility with relatively recent versions of boto3. That means that if you
want to implement some functionality that uses a new feature of boto3, it should only fail if that
feature actually needs to be run, with a message stating the missing feature and minimum required
version of boto3.

Use feature testing (e.g. `hasattr('boto3.module', 'shiny_new_method')`) to check whether boto3
supports a feature rather than version checking

e.g. from the `ec2` module:
```python
if boto_supports_profile_name_arg(ec2):
    params['instance_profile_name'] = instance_profile_name
else:
    if instance_profile_name is not None:
        module.fail_json(msg="instance_profile_name parameter requires boto version 2.5.0 or higher")
```

## Using botocore and boto3

### Importing

The `ansible.module_utils.ec2` module and `ansible.module_utils.core.aws` modules will both
automatically import boto3 and botocore.  If boto3 is missing from the system then the variable
`HAS_BOTO3` will be set to false.  Normally, this means that modules don't need to import
boto3 directly. There is no need to check `HAS_BOTO3` when using AnsibleAWSModule
as the module does that check.

```python
from ansible.module_utils.aws.core import AnsibleAWSModule

try:
    import botocore
except ImportError:
    pass  # handled by AnsibleAWSModule
```

or

```python
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import HAS_BOTO3

try:
    import botocore
except ImportError:
    pass  # handled by imported HAS_BOTO3

def main():

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 and botocore are required for this module')
```

#### boto and boto3 combined

Modules should be ported to use boto3 rather than use both boto and boto3.


### Connecting to AWS

AnsibleAWSModule provides the `resource` and `client` helper methods for obtaining boto3 connections.
These handle some of the more esoteric connection options, such as security tokens and boto profiles.

If using the basic AnsibleModule then you should use `get_aws_connection_info` and then `boto3_conn`
to connect to AWS as these handle the same range of connection options.

These helpers also for missing profiles or a region not set when it needs to be, so you don't have to.

An example of connecting to ec2 is shown below. Note that unlike boto there is no `NoAuthHandlerFound`
exception handling like in boto. Instead, an `AuthFailure` exception will be thrown when you use the
connection. To ensure that authorization, parameter validation and permissions errors are all caught,
you should catch `ClientError` and `BotoCoreError` exceptions with every boto3 connection call.
See exception handling.

```python
module.client('ec2')
```

or for the higher level ec2 resource:

```python
module.resource('ec2')
```

An example of the older style connection used for modules based on AnsibleModule rather than AnsibleAWSModule:

```python
region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)
connection = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_params)
```

```python
region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)
connection = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_params)
```

### Common Documentation Fragments for Connection Parameters

There are two [common documentation fragments](https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_documenting.html#documentation-fragments)
that should be included into almost all AWS modules:

* `aws` - contains the common boto connection parameters
* `ec2` - contains the common region parameter required for many AWS modules

These fragments should be used rather than re-documenting these properties to ensure consistency
and that the more esoteric connection options are documented. e.g.

```python
DOCUMENTATION = '''
module: my_module
...
requirements: [ 'botocore', 'boto3' ]
extends_documentation_fragment:
    - aws
    - ec2
'''
```

### Exception Handling

You should wrap any boto3 or botocore call in a try block. If an exception is thrown, then there
are a number of possibilities for handling it.

* Catch the general `ClientError` or look for a specific error code with
    `is_boto3_error_code`.
* Use aws_module.fail_json_aws() to report the module failure in a standard way
* Retry using AWSRetry
* Use fail_json() to report the failure without using `ansible.module_utils.aws.core`
* Do something custom in the case where you know how to handle the exception

For more information on botocore exception handling see [the botocore error documentation](https://botocore.readthedocs.io/en/latest/client_upgrades.html#error-handling).

### Using is_boto3_error_code

To use `ansible.module_utils.aws.core.is_boto3_error_code` to catch a single
AWS error code, call it in place of `ClientError` in your except clauses. In
this case, *only* the `InvalidGroup.NotFound` error code will be caught here,
and any other error will be raised for handling elsewhere in the program.

```python
try:
    return connection.describe_security_groups(**kwargs)
except is_boto3_error_code('InvalidGroup.NotFound'):
    return {'SecurityGroups': []}
```

#### Using fail_json_aws()

In the AnsibleAWSModule there is a special method, `module.fail_json_aws()` for nice reporting of
exceptions.  Call this on your exception and it will report the error together with a traceback for
use in Ansible verbose mode.

You should use the AnsibleAWSModule for all new modules, unless not possible. If adding significant
amounts of exception handling to existing modules, we recommend migrating the module to use AnsibleAWSModule
(there are very few changes required to do this)

```python
from ansible.module_utils.aws.core import AnsibleAWSModule

# Set up module parameters
...

# Connect to AWS
...

# Make a call to AWS
name = module.params.get['name']
try:
    result = connection.describe_frooble(FroobleName=name)
except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
    module.fail_json_aws(e, msg="Couldn't obtain frooble %s" % name)
```

Note that it should normally be acceptable to catch all normal exceptions here, however if you
expect anything other than botocore exceptions you should test everything works as expected.

If you need to perform an action based on the error boto3 returned, use the error code.

```python
# Make a call to AWS
name = module.params.get['name']
try:
    result = connection.describe_frooble(FroobleName=name)
except botocore.exceptions.ClientError as e:
    if e.response['Error']['Code'] == 'FroobleNotFound':
        return None
    else:
        module.fail_json_aws(e, msg="Couldn't obtain frooble %s" % name)
except botocore.exceptions.BotoCoreError as e:
    module.fail_json_aws(e, msg="Couldn't obtain frooble %s" % name)
```

#### using fail_json() and avoiding ansible.module_utils.aws.core

Boto3 provides lots of useful information when an exception is thrown so pass this to the user
along with the message.

```python
from ansible.module_utils.ec2 import HAS_BOTO3

try:
    import botocore
except ImportError:
    pass  # caught by imported HAS_BOTO3

# Connect to AWS
...

# Make a call to AWS
name = module.params.get['name']
try:
    result = connection.describe_frooble(FroobleName=name)
except botocore.exceptions.ClientError as e:
    module.fail_json(msg="Couldn't obtain frooble %s: %s" % (name, str(e)),
                     exception=traceback.format_exc(),
                     **camel_dict_to_snake_dict(e.response))
```

Note: we use `str(e)` rather than `e.message` as the latter doesn't
work with python3

If you need to perform an action based on the error boto3 returned, use the error code.

```python
# Make a call to AWS
name = module.params.get['name']
try:
    result = connection.describe_frooble(FroobleName=name)
except botocore.exceptions.ClientError as e:
    if e.response['Error']['Code'] == 'FroobleNotFound':
        return None
    else:
        module.fail_json(msg="Couldn't obtain frooble %s: %s" % (name, str(e)),
                         exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))
except botocore.exceptions.BotoCoreError as e:
    module.fail_json_aws(e, msg="Couldn't obtain frooble %s" % name)
```

### API throttling and pagination

For methods that return a lot of results, boto3 often provides
[paginators](http://boto3.readthedocs.io/en/latest/guide/paginators.html). If the method
you're calling has `NextToken` or `Marker` parameters, you should probably
check whether a paginator exists (the top of each boto3 service reference page has a link
to Paginators, if the service has any). To use paginators, obtain a paginator object,
call `paginator.paginate` with the appropriate arguments and then call `build_full_result`.

Any time that you are calling the AWS API a lot, you may experience API throttling,
and there is an `AWSRetry` decorator that can be used to ensure backoff. Because
exception handling could interfere with the retry working properly (as AWSRetry needs to
catch throttling exceptions to work correctly), you'd need to provide a backoff function
and then put exception handling around the backoff function.

You can use `exponential_backoff` or `jittered_backoff` strategies - see
the [cloud module_utils](/lib/ansible/module_utils/cloud.py)
and [AWS Architecture blog](https://www.awsarchitectureblog.com/2015/03/backoff.html)
for more details.

The combination of these two approaches is then

```
@AWSRetry.exponential_backoff(retries=5, delay=5)
def describe_some_resource_with_backoff(client, **kwargs):
     paginator = client.get_paginator('describe_some_resource')
     return paginator.paginate(**kwargs).build_full_result()['SomeResource']


def describe_some_resource(client, module):
    filters = ansible_dict_to_boto3_filter_list(module.params['filters'])
    try:
        return describe_some_resource_with_backoff(client, Filters=filters)
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e, msg="Could not describe some resource")
```

If the underlying `describe_some_resources` API call throws a `ResourceNotFound`
exception, `AWSRetry` takes this as a cue to retry until it's not thrown (this
is so that when creating a resource, we can just retry until it exists).

To handle authorization failures or parameter validation errors in
`describe_some_resource_with_backoff`, where we just want to return `None` if
the resource doesn't exist and not retry, we need:

```
@AWSRetry.exponential_backoff(retries=5, delay=5)
def describe_some_resource_with_backoff(client, **kwargs):
     try:
         return client.describe_some_resource(ResourceName=kwargs['name'])['Resources']
     except botocore.exceptions.ClientError as e:
         if e.response['Error']['Code'] == 'ResourceNotFound':
             return None
         else:
             raise
     except BotoCoreError as e:
         raise


def describe_some_resource(client, module):
    name = module.params.get['name']
    try:
        return describe_some_resource_with_backoff(client, name=name)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Could not describe resource %s" % name)
```

To make use of AWSRetry easier, it can now be wrapped around a client returned
by `AnsibleAWSModule`. any call from a client. To add retries to a client,
create a client:

```
module.client('ec2', retry_decorator=AWSRetry.jittered_backoff(retries=10))
```

Any calls from that client can be made to use the decorator passed at call-time
using the `aws_retry` argument. By default, no retries are used.

```
ec2 = module.client('ec2', retry_decorator=AWSRetry.jittered_backoff(retries=10))
ec2.describe_instances(InstanceIds=['i-123456789'], aws_retry=True)

# equivalent with normal AWSRetry
@AWSRetry.jittered_backoff(retries=10)
def describe_instances(client, **kwargs):
    return ec2.describe_instances(**kwargs)

describe_instances(module.client('ec2'), InstanceIds=['i-123456789'])
```

The call will be retried the specified number of times, so the calling functions
don't need to be wrapped in the backoff decorator.

### Returning Values

When you make a call using boto3, you will probably get back some useful information that you
should return in the module.  As well as information related to the call itself, you will also have
some response metadata.  It is OK to return this to the user as well as they may find it useful.

Boto3 returns all values CamelCased.  Ansible follows Python standards for variable names and uses
snake_case. There is a helper function in module_utils/ec2.py called `camel_dict_to_snake_dict`
that allows you to easily convert the boto3 response to snake_case.

You should use this helper function and avoid changing the names of values returned by Boto3.
E.g. if boto3 returns a value called 'SecretAccessKey' do not change it to 'AccessKey'.

```python
# Make a call to AWS
result = connection.aws_call()

# Return the result to the user
module.exit_json(changed=True, **camel_dict_to_snake_dict(result))
```

### Dealing with IAM JSON policy

If your module accepts IAM JSON policies then set the type to 'json' in the module spec. For
example:

```python
argument_spec.update(
    dict(
        policy=dict(required=False, default=None, type='json'),
    )
)
```

Note that AWS is unlikely to return the policy in the same order that is was submitted. Therefore,
use the `compare_policies` helper function which handles this variance.

`compare_policies` takes two dictionaries, recursively sorts and makes them hashable for comparison
and returns True if they are different.

```python
from ansible.module_utils.ec2 import compare_policies

import json

......

# Get the policy from AWS
current_policy = json.loads(aws_object.get_policy())
user_policy = json.loads(module.params.get('policy'))

# Compare the user submitted policy to the current policy ignoring order
if compare_policies(user_policy, current_policy):
    # Update the policy
    aws_object.set_policy(user_policy)
else:
    # Nothing to do
    pass
```

### Dealing with tags

AWS has a concept of resource tags. Usually the boto3 API has separate calls for tagging and
untagging a resource.  For example, the ec2 API has a create_tags and delete_tags call.

It is common practice in Ansible AWS modules to have a `purge_tags` parameter that defaults to
true.

The `purge_tags` parameter means that existing tags will be deleted if they are not specified by
the Ansible task.

There is a helper function `compare_aws_tags` to ease dealing with tags. It can compare two dicts
and return the tags to set and the tags to delete.  See the Helper function section below for more
detail.

### Helper functions

Along with the connection functions in Ansible ec2.py module_utils, there are some other useful
functions detailed below.

#### camel_dict_to_snake_dict

boto3 returns results in a dict.  The keys of the dict are in CamelCase format. In keeping with
Ansible format, this function will convert the keys to snake_case.

`camel_dict_to_snake_dict` takes an optional parameter called `ignore_list` which is a list of
keys not to convert (this is usually useful for the `tags` dict, whose child keys should remain with
case preserved)

Another optional parameter is `reversible`. By default, `HTTPEndpoint` is converted to `http_endpoint`,
which would then be converted by `snake_dict_to_camel_dict` to `HttpEndpoint`.
Passing `reversible=True` converts HTTPEndpoint to `h_t_t_p_endpoint` which converts back to `HTTPEndpoint`.

#### snake_dict_to_camel_dict

`snake_dict_to_camel_dict` converts snake cased keys to camel case. By default, because it was
first introduced for ECS purposes, this converts to dromedaryCase. An optional
parameter called `capitalize_first`, which defaults to `False`, can be used to convert to CamelCase.

#### ansible_dict_to_boto3_filter_list

Converts a an Ansible list of filters to a boto3 friendly list of dicts.  This is useful for any
boto3 `_facts` modules.

### boto_exception

Pass an exception returned from boto or boto3, and this function will consistently get the message from the exception.

Deprecated: use `AnsibleAWSModule`'s `fail_json_aws` instead.


#### boto3_tag_list_to_ansible_dict

Converts a boto3 tag list to an Ansible dict. Boto3 returns tags as a list of dicts containing keys
called 'Key' and 'Value' by default.  This key names can be overridden when calling the function.
For example, if you have already camel_cased your list of tags you may want to pass lowercase key
names instead i.e. 'key' and 'value'.

This function converts the list in to a single dict where the dict key is the tag key and the dict
value is the tag value.

#### ansible_dict_to_boto3_tag_list

Opposite of above. Converts an Ansible dict to a boto3 tag list of dicts. You can again override
the key names used if 'Key' and 'Value' is not suitable.

#### get_ec2_security_group_ids_from_names

Pass this function a list of security group names or combination of security group names and IDs
and this function will return a list of IDs.  You should also pass the VPC ID if known because
security group names are not necessarily unique across VPCs.

#### compare_policies

Pass two dicts of policies to check if there are any meaningful differences and returns true
if there are. This recursively sorts the dicts and makes them hashable before comparison.

This method should be used any time policies are being compared so that a change in order
doesn't result in unnecessary changes.

#### sort_json_policy_dict

Pass any JSON policy dict to this function in order to sort any list contained therein. This is
useful because AWS rarely return lists in the same order that they were submitted so without this
function, comparison of identical policies returns false.

Note if your goal is to check if two policies are the same you're better to use the `compare_policies`
helper which sorts recursively.

#### compare_aws_tags

Pass two dicts of tags and an optional purge parameter and this function will return a dict
containing key pairs you need to modify and a list of tag key names that you need to remove.  Purge
is True by default.  If purge is False then any existing tags will not be modified.

This function is useful when using boto3 'add_tags' and 'remove_tags' functions. Be sure to use the
other helper function `boto3_tag_list_to_ansible_dict` to get an appropriate tag dict before
calling this function. Since the AWS APIs are not uniform (e.g. EC2 versus Lambda) this will work
without modification for some (Lambda) and others may need modification before using these values
(such as EC2, with requires the tags to unset to be in the form `[{'Key': key1}, {'Key': key2}]`).

## Integration Tests for AWS Modules

All new AWS modules should include integration tests to ensure that any changes in AWS APIs that
affect the module are detected. At a minimum this should cover the key API calls and check the
documented return values are present in the module result.

For general information on running the integration tests see the [Integration Tests page of the
Module Development Guide](https://docs.ansible.com/ansible/latest/dev_guide/testing_integration.html).
Particularly the [cloud test configuration section](https://docs.ansible.com/ansible/latest/dev_guide/testing_integration.html#other-configuration-for-cloud-tests)

The integration tests for your module should be added in `test/integration/targets/MODULE_NAME`.

You must also have a aliases file in `test/integration/targets/MODULE_NAME/aliases`. This file serves
two purposes. First indicates it's in an AWS test causing the test framework to make AWS credentials
available during the test run. Second putting the test in a test group causing it to be run in the
continuous integration build.

Tests for new modules should be added to the same group as existing AWS tests. In general just copy
an existing aliases file such as the [aws_s3 tests aliases file](/test/integration/targets/aws_s3/aliases).

### AWS Credentials for Integration Tests

The testing framework handles running the test with appropriate AWS credentials, these are made available
to your test in the following variables:

* `aws_region`
* `aws_access_key`
* `aws_secret_key`
* `security_token`

So all invocations of AWS modules in the test should set these parameters. To avoid duplication these
for every call, it's preferrable to use [YAML Anchors](http://blog.daemonl.com/2016/02/yaml.html) E.g.

```yaml
- name: set connection information for all tasks
  set_fact:
    aws_connection_info: &aws_connection_info
      aws_access_key: "{{ aws_access_key }}"
      aws_secret_key: "{{ aws_secret_key }}"
      security_token: "{{ security_token }}"
      region: "{{ aws_region }}"
  no_log: yes

- name: Do Something
  ec2_instance:
    ... params ...
    <<: *aws_connection_info

- name: Do Something Else
  ec2_instance:
    ... params ...
    <<: *aws_connection_info
```

### AWS Permissions for Integration Tests

As explained in the [Integration Test guide](https://docs.ansible.com/ansible/latest/dev_guide/testing_integration.html#iam-policies-for-aws)
there are defined IAM policies in `hacking/aws_config/testing_policies/` that contain the necessary permissions
to run the AWS integration test.

If your module is interacting with a new service or otherwise requires new permissions you must update the
appropriate policy file to grant the permissions needed to run your integration test.

There is no process for automatically granting additional permissions to the roles used by the continuous
integration builds, so the tests will initially fail when you submit a pull request and the
[Ansibullbot](https://github.com/ansible/ansibullbot/blob/master/ISSUE_HELP.md) will tag it as needing revision.

Once you're certain the failure is only due to the missing permissions, add a comment with the `ready_for_review`
tag and explain that it's due to missing permissions.
