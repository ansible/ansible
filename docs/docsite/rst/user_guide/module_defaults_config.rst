.. _module_defaults_config:

Module Defaults Configuration
=============================

Ansible 2.7 adds a preview-status feature to group together modules that share common sets of parameters. This makes
it easier to author playbooks making heavy use of API-based modules such as cloud modules. By default Ansible ships
with groups for AWS and GCP modules that share parameters. Using the I(module_defaults_cfg) option users can create
custom groups or remove modules from the builtin groups.

In a playbook, you can set module defaults for whole groups of modules, such as setting a common AWS region.

.. code-block:: YAML

    # example_play.yml
    - hosts: localhost
      module_defaults:
        group/aws:
          region: us-west-2
      tasks:
      - aws_s3_bucket_facts:
      # now the region is shared between both facts modules
      - ec2_ami_facts:
          filters:
            name: 'RHEL*7.5*'

Users can also add their own custom groups. The version 1.0 file format has two keys: version, and groupings.
Modules can be in multiple groups, and can be removed from groups by prefixing the name with '-', such as '-aws'.

.. code-block:: YAML

    ---
    version: '1.0'
    groupings:
      # add your custom module for the new AWS FrobNozzle Scaling service to the `aws` group
      aws_elastic_frobnozzle_scale:
        - aws
      # remove S3 modules from the default `aws` group and move them to a group called `s3`
      aws_s3_bucket_facts:
        - -aws
        - s3
      aws_s3_bucket:
        - -aws
        - s3

To add these custom groupings to the module defaults, in ansible.cfg the user would need to add the file path:

.. code-block:: INI

    [defaults]
    module_defaults_cfg = my_custom_defaults.yml
