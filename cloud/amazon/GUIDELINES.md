Guidelines for AWS modules
--------------------------

Naming your module
==================

Base the name of the module on the part of AWS that
you actually use. (A good rule of thumb is to take
whatever module you use with boto as a starting point).

Don't further abbreviate names - if something is a well
known abbreviation due to it being a major component of
AWS, that's fine, but don't create new ones independently
(e.g. VPC, ELB, etc. are fine)

Using boto
==========

Wrap the `import` statements in a try block and fail the
module later on if the import fails

```
try:
    import boto
    import boto.module.that.you.use
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

<lots of code here>

def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            module_specific_parameter=dict(),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )
    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')
```


Try and keep backward compatibility with relatively recent
versions of boto. That means that if want to implement some
functionality that uses a new feature of boto, it should only 
fail if that feature actually needs to be run, with a message
saying which version of boto is needed.

Use feature testing (e.g. `hasattr('boto.module', 'shiny_new_method')`)
to check whether boto supports a feature rather than version checking

e.g. from the `ec2` module:
```
if boto_supports_profile_name_arg(ec2):
    params['instance_profile_name'] = instance_profile_name
else:
    if instance_profile_name is not None:
        module.fail_json(
            msg="instance_profile_name parameter requires Boto version 2.5.0 or higher")
```


Connecting to AWS
=================

For EC2 you can just use

```
ec2 = ec2_connect(module)
```

For other modules, you should use `get_aws_connection_info` and then
`connect_to_aws`. To connect to an example `xyz` service:

```
region, ec2_url, aws_connect_params = get_aws_connection_info(module)
xyz = connect_to_aws(boto.xyz, region, **aws_connect_params)
```

The reason for using `get_aws_connection_info` and `connect_to_aws`
(and even `ec2_connect` uses those under the hood) rather than doing it
yourself is that they handle some of the more esoteric connection
options such as security tokens and boto profiles.
