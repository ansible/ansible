:orphan:

.. _module_defaults_config:

*****************************
Module Defaults Configuration
*****************************

Ansible 2.7 adds a preview-status feature to group together modules that share common sets of parameters. This makes
it easier to author playbooks making heavy use of API-based modules such as cloud modules. By default Ansible ships
with groups for AWS and GCP modules that share parameters.

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
