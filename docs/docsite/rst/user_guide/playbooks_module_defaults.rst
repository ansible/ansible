.. _module_defaults:

Module defaults
===============

If you find yourself calling the same module repeatedly with the same arguments, it can be useful to define default arguments for that particular module using the ``module_defaults`` attribute.

Here is a basic example::

    - hosts: localhost
      module_defaults:
        file:
          owner: root
          group: root
          mode: 0755
      tasks:
        - file:
            state: touch
            path: /tmp/file1
        - file:
            state: touch
            path: /tmp/file2
        - file:
            state: touch
            path: /tmp/file3

The ``module_defaults`` attribute can be used at the play, block, and task level. Any module arguments explicitly specified in a task will override any established default for that module argument::

    - block:
        - debug:
            msg: "a different message"
      module_defaults:
        debug:
          msg: "a default message"

It's also possible to remove any previously established defaults for a module by specifying an empty dict (if MODULE_DEFAULTS_MERGE is False)::

    - file:
        state: touch
        path: /tmp/file1
      module_defaults:
        file: {}

.. note::
    Any module defaults set at the play level (and block/task level when using ``include_role`` or ``import_role``) will apply to any roles used, which may cause unexpected behavior in the role.

Ansible 2.8 adds a MODULE_DEFAULTS_MERGE configuration option to allow arguments for a module or group to be merged with arguments for the same module/group in an inner scope::

    - hosts: localhost
      module_defaults:
        group/aws:
          aws_access_key: "{{ access_key }}"
          aws_secret_key: "{{ secret_key }}"
      tasks:
        - name: run tasks in us-east-1
          module_defaults:
            # without MODULE_DEFAULTS_MERGE enabled this would overwrite the previous keys in group/aws
            group/aws:
              region: us-east-1
          block:
            - elb_target_facts:

If the MODULE_DEFAULTS_MERGE option is enabled use the special key __clear__ can be used to remove previous defaults. This allows clearing values and setting new ones within the same scope::

    - hosts: localhost
      module_defaults:
        group/aws:
          profile: dev
      tasks:
        - name: assume a role
          sts_assume_role:
            region: us-east-1
            role_arn: "arn:aws:iam::123456789012:role/someRole"
            role_session_name: "someRoleSession"
          register: assumed_role
        - name: remove the previous group/aws defaults and use new credentials for subsequent tasks
          module_defaults:
            group/aws:
              __clear__: yes
              region: us-east-1
              aws_access_key: "{{ assumed_role.sts_creds.access_key }}"
              aws_secret_key: "{{ assumed_role.sts_creds.secret_key }}"
              security_token: "{{ assumed_role.sts_creds.session_token }}"
          block:
            ...

Here are some more realistic use cases for this feature.

Interacting with an API that requires auth::

    - hosts: localhost
      module_defaults:
        uri:
          force_basic_auth: true
          user: some_user
          password: some_password
      tasks:
        - uri:
            url: http://some.api.host/v1/whatever1
        - uri:
            url: http://some.api.host/v1/whatever2
        - uri:
            url: http://some.api.host/v1/whatever3

Setting a default AWS region for specific EC2-related modules::

    - hosts: localhost
      vars:
        my_region: us-west-2
      module_defaults:
        ec2:
          region: '{{ my_region }}'
        ec2_instance_facts:
          region: '{{ my_region }}'
        ec2_vpc_net_facts:
          region: '{{ my_region }}'

.. _module_defaults_groups:

Module defaults groups
``````````````````````

.. versionadded:: 2.7

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
