.. _module_defaults:

Module defaults
===============

If you frequently call the same module with the same arguments, it can be useful to define default arguments for that particular module using the ``module_defaults`` attribute.

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

You can remove any previously established defaults for a module by specifying an empty dict::

    - file:
        state: touch
        path: /tmp/file1
      module_defaults:
        file: {}

.. note::
    Any module defaults set at the play level (and block/task level when using ``include_role`` or ``import_role``) will apply to any roles used, which may cause unexpected behavior in the role.

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
        ec2_instance_info:
          region: '{{ my_region }}'
        ec2_vpc_net_info:
          region: '{{ my_region }}'

.. _module_defaults_groups:

Module defaults groups
----------------------

.. versionadded:: 2.7

Ansible 2.7 adds a preview-status feature to group together modules that share common sets of parameters. Ansible 2.10 adds support for groups to be defined in collections. This makes it easier to author playbooks making heavy use of API-based modules such as cloud modules.

+---------+---------------------------+-----------------+
| Group   | Purpose                   | Ansible Version |
+=========+===========================+=================+
| aws     | Amazon Web Services       | 2.7             |
+---------+---------------------------+-----------------+
| azure   | Azure                     | 2.7             |
+---------+---------------------------+-----------------+
| gcp     | Google Cloud Platform     | 2.7             |
+---------+---------------------------+-----------------+
| k8s     | Kubernetes                | 2.8             |
+---------+---------------------------+-----------------+
| os      | OpenStack                 | 2.8             |
+---------+---------------------------+-----------------+
| acme    | ACME                      | 2.10            |
+---------+---------------------------+-----------------+
| docker* | Docker                    | 2.10            |
+---------+---------------------------+-----------------+
| ovirt   | oVirt                     | 2.10            |
+---------+---------------------------+-----------------+
| vmware  | VMware                    | 2.10            |
+---------+---------------------------+-----------------+

* The `docker_stack <docker_stack_module>`_ module is not included in the ``docker`` defaults group.

Use the groups with ``module_defaults`` by prefixing the group name with ``group/`` - e.g. ``group/aws``.

In a playbook, you can set module defaults for whole groups of modules, such as setting a common AWS region.

.. code-block:: YAML

    # example_play.yml
    - hosts: localhost
      module_defaults:
        group/aws:
          region: us-west-2
      tasks:
      - aws_s3_bucket_info:
      # now the region is shared between both info modules
      - ec2_ami_info:
          filters:
            name: 'RHEL*7.5*'

As of Ansible 2.10, a collection can define ``action_groups`` in its ``meta/runtime.yml`` file to be used with module_defaults.

.. code-block:: YAML

   # collection_namespace/collection_name/meta/runtime.yml
   action_groups:
     group_name:
       - module_name
       - another_module

.. code-block:: YAML

   # example_play.yml
   - hosts: all
     module_defaults:
       group/collection_namespace.collection_name.group_name:
         common_option: value

Allowing content in another collection to share the same group name is supported via the collection's ``action_groups_redirection`` metadata field. This allows playbooks to work without modification when content is relocated.

The ``ansible.builtin`` collection metadata contains the unqualified group names listed above for backwards compatibility and redirects the options to the new fully qualified group name(s).

.. code-block:: YAML

   acme:
     redirect: [community.crypto.acme]
   aws:
     redirect: [amazon.aws.aws, community.aws.aws]
   azure:
     redirect: [azure.azcollection.azure]
   cpm:
     redirect: [wti.remote.cpm]
   docker:
     redirect: [community.general.docker]
   gcp:
     redirect: [google.cloud.gcp]
   k8s:
     redirect: [community.kubernetes.k8s]
   os:
     redirect: [openstack.cloud.os]
   ovirt:
     redirect: [ovirt.ovirt.ovirt]
   vmware:
     redirect: [community.vmware.vmware]

This allows a playbook written using the group ``aws`` to continue working with AWS modules which were moved to the ``amazon.aws`` and ``community.aws`` collections.

.. code-block:: YAML

   hosts: localhost
   gather_facts: no
   module_defaults:
     group/aws:
       ...
   tasks:
     - name: Use group/aws options with a redirected module from ansible.builtin
       aws_s3:

     - name: Use group/aws options with fully qualified module name
       amazon.aws.aws_s3:

     - name: Use group/aws options with collections list shorthand
       aws_s3:
       collections: amazon.aws
