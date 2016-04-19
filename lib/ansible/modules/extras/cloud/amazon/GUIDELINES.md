# Guidelines for AWS modules

## Getting Started

Since Ansible 2.0, it is a requirement that all new AWS modules are written to use boto3.

Prior to 2.0, modules may of been written in boto or boto3. Modules written using boto can continue to be extended using boto.

Backward compatibility of older modules must be maintained.

## Bug fixing

If you are writing a bugfix for a module that uses boto, you should continue to use boto to maintain backward compatibility.

If you are adding new functionality to an existing module that uses boto but the new functionality requires boto3, you
must maintain backward compatibility of the module and ensure the module still works without boto3.

## Naming your module

Base the name of the module on the part of AWS that
you actually use. (A good rule of thumb is to take
whatever module you use with boto as a starting point).

Don't further abbreviate names - if something is a well
known abbreviation due to it being a major component of
AWS, that's fine, but don't create new ones independently
(e.g. VPC, ELB, etc. are fine)

## Adding new features

Try and keep backward compatibility with relatively recent
versions of boto. That means that if want to implement some
functionality that uses a new feature of boto, it should only
fail if that feature actually needs to be run, with a message
saying which version of boto is needed.

Use feature testing (e.g. `hasattr('boto.module', 'shiny_new_method')`)
to check whether boto supports a feature rather than version checking

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

If you want to add boto3 functionality to a module written using boto, you must maintain backward compatibility.
Ensure that you clearly document if a new parameter requires boto3. Import boto3 at the top of the
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

To connect to AWS, you should use `get_aws_connection_info` and then
`connect_to_aws`.

The reason for using `get_aws_connection_info` and `connect_to_aws` rather than doing it
yourself is that they handle some of the more esoteric connection
options such as security tokens and boto profiles.

Some boto services require region to be specified. You should check for the region parameter if required.

#### boto

An example of connecting to ec2:

```python
region, ec2_url, aws_connect_params = get_aws_connection_info(module)
if region:
    try:
        connection = connect_to_aws(boto.ec2, region, **aws_connect_params)
    except (boto.exception.NoAuthHandlerFound, AnsibleAWSError), e:
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
but usually calling fail_json with the error message will suffice.

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
except BotoServerError, e:
    module.fail_json(msg=e.message)
```

#### boto3

For more information on botocore exception handling see [http://botocore.readthedocs.org/en/latest/client_upgrades.html#error-handling]

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
except ClientError, e:
    module.fail_json(msg=e.message)
```

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
'Key' and 'Value'. This function converts this list in to a single dict where the dict key is the tag
key and the dict value is the tag value.

#### ansible_dict_to_boto3_tag_list

Opposite of above. Converts an Ansible dict to a boto3 tag list of dicts.

