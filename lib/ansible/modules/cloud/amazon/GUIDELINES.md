# Guidelines for AWS modules

## Getting Started

Since Ansible 2.0, it is required that all new AWS modules are written to use boto3.

Prior to 2.0, modules may have been written in boto or boto3. The effort to port all modules to boto3 has begun.

## Bug fixing

Bug fixes to code that relies on boto will still be accepted. When possible, the code should be ported to use boto3. 

## Naming your module

Base the name of the module on the part of AWS that
you actually use. (A good rule of thumb is to take
whatever module you use with boto as a starting point).

Don't further abbreviate names - if something is a well
known abbreviation due to it being a major component of
AWS, that's fine, but don't create new ones independently
(e.g. VPC, ELB, etc. are fine)

## Adding new features

Try to keep backward compatibility with relatively recent
versions of boto3. That means that if you want to implement some
functionality that uses a new feature of boto3, it should only
fail if that feature actually needs to be run, with a message
saying which version of boto3 is needed.

Use feature testing (e.g. `hasattr('boto3.module', 'shiny_new_method')`)
to check whether boto3 supports a feature rather than version checking

e.g. from the `ec2` module:
```python
if boto_supports_profile_name_arg(ec2):
    params['instance_profile_name'] = instance_profile_name
else:
    if instance_profile_name is not None:
        module.fail_json(msg="instance_profile_name parameter requires boto version 2.5.0 or higher")
```

## Using boto and boto3

### Importing

Wrap import statements in a try block and fail the module later if the import fails

#### boto

```python
try:
    import boto.ec2
    from boto.exception import BotoServerError
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

def main():

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')
```

#### boto3

```python
try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

def main():

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')
```

#### boto and boto3 combined

Ensure that you clearly document if a new parameter requires requires a specific version. Import boto3 at the top of the
module as normal and then use the HAS_BOTO3 bool when necessary, before the new feature.

```python
try:
    import boto
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

if my_new_feauture_Parameter_is_set:
    if HAS_BOTO3:
        # do feature
    else:
        module.fail_json(msg="boto3 is required for this feature")
```

### Connecting to AWS

To connect to AWS, you should use `get_aws_connection_info` and then `boto3_conn`.

These functions handle some of the more esoteric connection options, such as security tokens and boto profiles.

Some boto services require that the region is specified. You should check for the region parameter if required.

#### boto

An example of connecting to ec2:

```python
region, ec2_url, aws_connect_params = get_aws_connection_info(module)
if region:
    try:
        connection = connect_to_aws(boto.ec2, region, **aws_connect_params)
    except (boto.exception.NoAuthHandlerFound, AnsibleAWSError) as e:
        module.fail_json(msg=str(e))
else:
    module.fail_json(msg="region must be specified")
```

#### boto3

An example of connecting to ec2 is shown below.  Note that there is no 'NoAuthHandlerFound' exception handling like in boto.
Instead, an AuthFailure exception will be thrown when you use 'connection'. See exception handling.

```python
region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)
if region:
    connection = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_params)
else:
    module.fail_json(msg="region must be specified")
```

### Exception Handling

You should wrap any boto call in a try block. If an exception is thrown, it is up to you decide how to handle it
but usually calling fail_json with the error or helpful message and traceback will suffice.

#### boto

```python
# Import BotoServerError
try:
    import boto.ec2
    from boto.exception import BotoServerError
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

# Connect to AWS
...

# Make a call to AWS
try:
    result = connection.aws_call()
except BotoServerError as e:
    module.fail_json(msg="helpful message here", exception=traceback.format_exc(),
                     **camel_dict_to_snake_dict(e.message))
```

#### boto3

For more information on botocore exception handling see [http://botocore.readthedocs.org/en/latest/client_upgrades.html#error-handling]

Boto3 provides lots of useful info when an exception is thrown so pass this to the user along with the message.

```python
# Import ClientError from botocore
try:
    from botocore.exceptions import ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

# Connect to AWS
...

# Make a call to AWS
try:
    result = connection.aws_call()
except ClientError as e:
    module.fail_json(msg=e.message, exception=traceback.format_exc(),
                     **camel_dict_to_snake_dict(e.response))
```

If you need to perform an action based on the error boto3 returned, use the error code.

```python
# Make a call to AWS
try:
    result = connection.aws_call()
except ClientError as e:
    if e.response['Error']['Code'] == 'NoSuchEntity':
        return None
    else:
        module.fail_json(msg=e.message, exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))
```

### Returning Values

When you make a call using boto3, you will probably get back some useful information that you should return in the module.

As well as information related to the call itself, you will also have some response metadata.  It is OK to return this to
the user as well as they may find it useful.

Boto3 returns all values CamelCased.  Ansible follows Python standards for variable names and uses snake_case. There is a
helper function in module_utils/ec2.py called `camel_dict_to_snake_dict` that allows you to easily convert the boto3
response to snake_case.

You should use this helper function and avoid changing the names of values returned by Boto3.  E.g. if boto3 returns a
value called 'SecretAccessKey' do not change it to 'AccessKey'.

```python
# Make a call to AWS
result = connection.aws_call()

# Return the result to the user
module.exit_json(changed=True, **camel_dict_to_snake_dict(result))
```

### Dealing with IAM JSON policy

If your module accepts IAM JSON policies then set the type to 'json' in the module spec. For example"

```python
argument_spec.update(
    dict(
        policy=dict(required=False, default=None, type='json'),
    )
)
```

Note that AWS is unlikely to return the policy in the same order that is was submitted. Therefore, a helper
function has been created to order policies before comparison.

```python
# Get the policy from AWS
current_policy = aws_object.get_policy()

# Compare the user submitted policy to the current policy but sort them first
if sort_json_policy_dict(user_policy) == sort_json_policy_dict(current_policy):
    # Nothing to do
    pass
else:
    # Update the policy
    aws_object.set_policy(user_policy)
```

### Dealing with tags

AWS has a concept of resource tags. Usually the boto3 API has separate calls for tagging and
untagging a resource.  For example, the ec2 API has a create_tags and delete_tags call.

It is common practice in Ansible AWS modules to have a 'purge_tags' parameter that defaults to true.

The purge_tags parameter means that existing tags will be deleted if they are not specified in
by the Ansible playbook.

There is a helper function 'compare_aws_tags' to ease dealing with tags. It can compare two dicts and
return the tags to set and the tags to delete.  See the Helper function section below for more detail.

### Helper functions

Along with the connection functions in Ansible ec2.py module_utils, there are some other useful functions detailed below.

#### camel_dict_to_snake_dict

boto3 returns results in a dict.  The keys of the dict are in CamelCase format. In keeping
with Ansible format, this function will convert the keys to snake_case.

#### ansible_dict_to_boto3_filter_list

Converts a an Ansible list of filters to a boto3 friendly list of dicts.  This is useful for
any boto3 _facts modules.

#### boto3_tag_list_to_ansible_dict

Converts a boto3 tag list to an Ansible dict. Boto3 returns tags as a list of dicts containing keys called
'Key' and 'Value' by default.  This key names can be overriden when calling the function.  For example, if you have already
camel_cased your list of tags you may want to pass lowercase key names instead i.e. 'key' and 'value'.

This function converts the list in to a single dict where the dict key is the tag key and the dict value is the tag value.

#### ansible_dict_to_boto3_tag_list

Opposite of above. Converts an Ansible dict to a boto3 tag list of dicts. You can again override the key names used if 'Key'
and 'Value' is not suitable.

#### get_ec2_security_group_ids_from_names

Pass this function a list of security group names or combination of security group names and IDs and this function will
return a list of IDs.  You should also pass the VPC ID if known because security group names are not necessarily unique
across VPCs.

#### sort_json_policy_dict

Pass any JSON policy dict to this function in order to sort any list contained therein. This is useful
because AWS rarely return lists in the same order that they were submitted so without this function, comparison
of identical policies returns false.

### compare_aws_tags

Pass two dicts of tags and an optional purge parameter and this function will return a dict containing key pairs you need
to modify and a list of tag key names that you need to remove.  Purge is True by default.  If purge is False then any
existing tags will not be modified.

This function is useful when using boto3 'add_tags' and 'remove_tags' functions. Be sure to use the other helper function
'boto3_tag_list_to_ansible_dict' to get an appropriate tag dict before calling this function. Since the AWS APIs are not
uniform (e.g. EC2 versus Lambda) this will work without modification for some (Lambda) and others may need modification
before using these values (such as EC2, with requires the tags to unset to be in the form [{'Key': key1}, {'Key': key2}]).
