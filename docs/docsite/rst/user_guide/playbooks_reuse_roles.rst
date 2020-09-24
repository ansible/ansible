.. _playbooks_reuse_roles:

*****
Roles
*****

Roles let you automatically load related vars_files, tasks, handlers, and other Ansible artifacts based on a known file structure. Once you group your content in roles, you can easily reuse them and share them with other users.

.. contents::
   :local:

Role directory structure
========================

An Ansible role has a defined directory structure with seven main standard directories. You must include at least one of these directories in each role. You can omit any directories the role does not use. For example:

.. code-block:: text

    # playbooks
    site.yml
    webservers.yml
    fooservers.yml
    roles/
        common/
            tasks/
            handlers/
            library/
            files/
            templates/
            vars/
            defaults/
            meta/
        webservers/
            tasks/
            defaults/
            meta/

By default Ansible will look in each directory within a role for a ``main.yml`` file for relevant content (also ``main.yaml`` and ``main``):

- ``tasks/main.yml`` - the main list of tasks that the role executes.
- ``handlers/main.yml`` - handlers, which may be used within or outside this role.
- ``library/my_module.py`` - modules, which may be used within this role (see :ref:`embedding_modules_and_plugins_in_roles` for more information).
- ``defaults/main.yml`` - default variables for the role (see :ref:`playbooks_variables` for more information). These variables have the lowest priority of any variables available, and can be easily overridden by any other variable, including inventory variables.
- ``vars/main.yml`` - other variables for the role (see :ref:`playbooks_variables` for more information).
- ``files/main.yml`` - files that the role deploys.
- ``templates/main.yml`` - templates that the role deploys.
- ``meta/main.yml`` - metadata for the role, including role dependencies.

You can add other YAML files in some directories. For example, you can place platform-specific tasks in separate files and refer to them in the ``tasks/main.yml`` file:

.. code-block:: yaml

    # roles/example/tasks/main.yml
    - name: Install the correct web server for RHEL
      import_tasks: redhat.yml
      when: ansible_facts['os_family']|lower == 'redhat'

    - name: Install the correct web server for Debian
      import_tasks: debian.yml
      when: ansible_facts['os_family']|lower == 'debian'

    # roles/example/tasks/redhat.yml
    - name: Install web server
      ansible.builtin.yum:
        name: "httpd"
        state: present

    # roles/example/tasks/debian.yml
    - name: Install web server
      ansible.builtin.apt:
        name: "apache2"
        state: present

Roles may also include modules and other plugin types in a directory called ``library``. For more information, please refer to :ref:`embedding_modules_and_plugins_in_roles` below.

.. _role_search_path:

Storing and finding roles
=========================

By default, Ansible looks for roles in two locations:

- in a directory called ``roles/``, relative to the playbook file
- in ``/etc/ansible/roles``

If you store your roles in a different location, set the :ref:`roles_path <DEFAULT_ROLES_PATH>` configuration option so Ansible can find your roles. Checking shared roles into a single location makes them easier to use in multiple playbooks. See :ref:`intro_configuration` for details about managing settings in ansible.cfg.

Alternatively, you can call a role with a fully qualified path:

.. code-block:: yaml

    ---
    - hosts: webservers
      roles:
        - role: '/path/to/my/roles/common'

Using roles
===========

You can use roles in three ways:

- at the play level with the ``roles`` option: This is the classic way of using roles in a play.
- at the tasks level with ``include_role``: You can reuse roles dynamically anywhere in the ``tasks`` section of a play using ``include_role``.
- at the tasks level with ``import_role``: You can reuse roles statically anywhere in the ``tasks`` section of a play using ``import_role``.

.. _roles_keyword:

Using roles at the play level
-----------------------------

The classic (original) way to use roles is with the ``roles`` option for a given play:

.. code-block:: yaml

    ---
    - hosts: webservers
      roles:
        - common
        - webservers

When you use the ``roles`` option at the play level, for each role 'x':

- If roles/x/tasks/main.yml exists, Ansible adds the tasks in that file to the play.
- If roles/x/handlers/main.yml exists, Ansible adds the handlers in that file to the play.
- If roles/x/vars/main.yml exists, Ansible adds the variables in that file to the play.
- If roles/x/defaults/main.yml exists, Ansible adds the variables in that file to the play.
- If roles/x/meta/main.yml exists, Ansible adds any role dependencies in that file to the list of roles.
- Any copy, script, template or include tasks (in the role) can reference files in roles/x/{files,templates,tasks}/ (dir depends on task) without having to path them relatively or absolutely.

When you use the ``roles`` option at the play level, Ansible treats the roles as static imports and processes them during playbook parsing. Ansible executes your playbook in this order:

- Any ``pre_tasks`` defined in the play.
- Any handlers triggered by pre_tasks.
- Each role listed in ``roles:``, in the order listed. Any role dependencies defined in the role's ``meta/main.yml`` run first, subject to tag filtering and conditionals. See :ref:`role_dependencies` for more details.
- Any ``tasks`` defined in the play.
- Any handlers triggered by the roles or tasks.
- Any ``post_tasks`` defined in the play.
- Any handlers triggered by post_tasks.

.. note::
   If using tags with tasks in a role, be sure to also tag your pre_tasks, post_tasks, and role dependencies and pass those along as well, especially if the pre/post tasks and role dependencies are used for monitoring outage window control or load balancing. See :ref:`tags` for details on adding and using tags.

You can pass other keywords to the ``roles`` option:

.. code-block:: yaml

    ---
    - hosts: webservers
      roles:
        - common
        - role: foo_app_instance
          vars:
            dir: '/opt/a'
            app_port: 5000
          tags: typeA
        - role: foo_app_instance
          vars:
            dir: '/opt/b'
            app_port: 5001
          tags: typeB

When you add a tag to the ``role`` option, Ansible applies the tag to ALL tasks within the role.

When using ``vars:`` within the ``roles:`` section of a playbook, the variables are added to the play variables, making them available to all tasks within the play before and after the role. This behavior can be changed by :ref:`DEFAULT_PRIVATE_ROLE_VARS`.

Including roles: dynamic reuse
------------------------------

You can reuse roles dynamically anywhere in the ``tasks`` section of a play using ``include_role``. While roles added in a ``roles`` section run before any other tasks in a playbook, included roles run in the order they are defined. If there are other tasks before an ``include_role`` task, the other tasks will run first.

To include a role:

.. code-block:: yaml

    ---
    - hosts: webservers
      tasks:
        - name: Print a message
          ansible.builtin.debug:
            msg: "this task runs before the example role"

        - name: Include the example role
          include_role:
            name: example

        - name: Print a message
          ansible.builtin.debug:
            msg: "this task runs after the example role"

You can pass other keywords, including variables and tags, when including roles:

.. code-block:: yaml

    ---
    - hosts: webservers
      tasks:
        - name: Include the foo_app_instance role
          include_role:
            name: foo_app_instance
          vars:
            dir: '/opt/a'
            app_port: 5000
          tags: typeA
      ...

When you add a :ref:`tag <tags>` to an ``include_role`` task, Ansible applies the tag `only` to the include itself. This means you can pass ``--tags`` to run only selected tasks from the role, if those tasks themselves have the same tag as the include statement. See :ref:`selective_reuse` for details.

You can conditionally include a role:

.. code-block:: yaml

    ---
    - hosts: webservers
      tasks:
        - name: Include the some_role role
          include_role:
            name: some_role
          when: "ansible_facts['os_family'] == 'RedHat'"

Importing roles: static reuse
-----------------------------

You can reuse roles statically anywhere in the ``tasks`` section of a play using ``import_role``. The behavior is the same as using the ``roles`` keyword. For example:

.. code-block:: yaml

    ---
    - hosts: webservers
      tasks:
        - name: Print a message
          ansible.builtin.debug:
            msg: "before we run our role"

        - name: Import the example role
          import_role:
            name: example

        - name: Print a message
          ansible.builtin.debug:
            msg: "after we ran our role"

You can pass other keywords, including variables and tags, when importing roles:

.. code-block:: yaml

    ---
    - hosts: webservers
      tasks:
        - name: Import the foo_app_instance role
          import_role:
            name: foo_app_instance
          vars:
            dir: '/opt/a'
            app_port: 5000
      ...

When you add a tag to an ``import_role`` statement, Ansible applies the tag to `all` tasks within the role. See :ref:`tag_inheritance` for details.

.. _run_role_twice:

Running a role multiple times in one playbook
=============================================

Ansible only executes each role once, even if you define it multiple times, unless the parameters defined on the role are different for each definition. For example, Ansible only runs the role ``foo`` once in a play like this:

.. code-block:: yaml

    ---
    - hosts: webservers
      roles:
        - foo
        - bar
        - foo

You have two options to force Ansible to run a role more than once.

Passing different parameters
----------------------------

You can pass different parameters in each role definition as:

.. code-block:: yaml

    ---
    - hosts: webservers
      roles:
        - { role: foo, vars: { message: "first" } }
        - { role: foo, vars: { message: "second" } }

or

.. code-block:: yaml

    ---
    - hosts: webservers
      roles:
        - role: foo
          vars:
            message: "first"
        - role: foo
          vars:
            message: "second"

In this example, because each role definition has different parameters, Ansible runs ``foo`` twice.

Using ``allow_duplicates: true``
--------------------------------

Add ``allow_duplicates: true`` to the ``meta/main.yml`` file for the role:

.. code-block:: yaml

    # playbook.yml
    ---
    - hosts: webservers
      roles:
        - foo
        - foo

    # roles/foo/meta/main.yml
    ---
    allow_duplicates: true

In this example, Ansible runs ``foo`` twice because we have explicitly enabled it to do so.

.. _role_dependencies:

Using role dependencies
=======================

Role dependencies let you automatically pull in other roles when using a role. Ansible does not execute role dependencies when you include or import a role. You must use the ``roles`` keyword if you want Ansible to execute role dependencies.

Role dependencies are stored in the ``meta/main.yml`` file within the role directory. This file should contain a list of roles and parameters to insert before the specified role. For example:

.. code-block:: yaml

    # roles/myapp/meta/main.yml
    ---
    dependencies:
      - role: common
        vars:
          some_parameter: 3
      - role: apache
        vars:
          apache_port: 80
      - role: postgres
        vars:
          dbname: blarg
          other_parameter: 12

Ansible always executes role dependencies before the role that includes them. Ansible executes recursive role dependencies as well. If one role depends on a second role, and the second role depends on a third role, Ansible executes the third role, then the second role, then the first role.

Running role dependencies multiple times in one playbook
--------------------------------------------------------

Ansible treats duplicate role dependencies like duplicate roles listed under ``roles:``: Ansible only executes role dependencies once, even if defined multiple times, unless the parameters, tags, or when clause defined on the role are different for each definition. If two roles in a playbook both list a third role as a dependency, Ansible only runs that role dependency once, unless you pass different parameters, tags, when clause, or use ``allow_duplicates: true`` in the dependent (third) role. See :ref:`Galaxy role dependencies <galaxy_dependencies>` for more details.

For example, a role named ``car`` depends on a role named ``wheel`` as follows:

.. code-block:: yaml

    ---
    dependencies:
      - role: wheel
        vars:
          n: 1
      - role: wheel
        vars:
          n: 2
      - role: wheel
        vars:
          n: 3
      - role: wheel
        vars:
          n: 4

And the ``wheel`` role depends on two roles: ``tire`` and ``brake``. The ``meta/main.yml`` for wheel would then contain the following:

.. code-block:: yaml

    ---
    dependencies:
      - role: tire
      - role: brake

And the ``meta/main.yml`` for ``tire`` and ``brake`` would contain the following:

.. code-block:: yaml

    ---
    allow_duplicates: true

The resulting order of execution would be as follows:

.. code-block:: text

    tire(n=1)
    brake(n=1)
    wheel(n=1)
    tire(n=2)
    brake(n=2)
    wheel(n=2)
    ...
    car

To use ``allow_duplicates: true`` with role dependencies, you must specify it for the dependent role, not for the parent role. In the example above, ``allow_duplicates: true`` appears in the ``meta/main.yml`` of the ``tire`` and ``brake`` roles. The ``wheel`` role does not require ``allow_duplicates: true``, because each instance defined by ``car`` uses different parameter values.

.. note::
   See :ref:`playbooks_variables` for details on how Ansible chooses among variable values defined in different places (variable inheritance and scope).

.. _embedding_modules_and_plugins_in_roles:

Embedding modules and plugins in roles
======================================

If you write a custom module (see :ref:`developing_modules`) or a plugin (see :ref:`developing_plugins`), you might wish to distribute it as part of a role. For example, if you write a module that helps configure your company's internal software, and you want other people in your organization to use this module, but you do not want to tell everyone how to configure their Ansible library path, you can include the module in your internal_config role.

To add a module or a plugin to a role:
Alongside the 'tasks' and 'handlers' structure of a role, add a directory named 'library' and then include the module directly inside the 'library' directory.

Assuming you had this:

.. code-block:: text

    roles/
        my_custom_modules/
            library/
                module1
                module2

The module will be usable in the role itself, as well as any roles that are called *after* this role, as follows:

.. code-block:: yaml

    ---
    - hosts: webservers
      roles:
        - my_custom_modules
        - some_other_role_using_my_custom_modules
        - yet_another_role_using_my_custom_modules

If necessary, you can also embed a module in a role to modify a module in Ansible's core distribution. For example, you can use the development version of a particular module before it is released in production releases by copying the module and embedding the copy in a role. Use this approach with caution, as API signatures may change in core components, and this workaround is not guaranteed to work.

The same mechanism can be used to embed and distribute plugins in a role, using the same schema. For example, for a filter plugin:

.. code-block:: text

    roles/
        my_custom_filter/
            filter_plugins
                filter1
                filter2

These filters can then be used in a Jinja template in any role called after 'my_custom_filter'.

Sharing roles: Ansible Galaxy
=============================

`Ansible Galaxy <https://galaxy.ansible.com>`_ is a free site for finding, downloading, rating, and reviewing all kinds of community-developed Ansible roles and can be a great way to get a jumpstart on your automation projects.

The client ``ansible-galaxy`` is included in Ansible. The Galaxy client allows you to download roles from Ansible Galaxy, and also provides an excellent default framework for creating your own roles.

Read the `Ansible Galaxy documentation <https://galaxy.ansible.com/docs/>`_ page for more information

.. seealso::

   :ref:`ansible_galaxy`
       How to create new roles, share roles on Galaxy, role management
   :ref:`yaml_syntax`
       Learn about YAML syntax
   :ref:`working_with_playbooks`
       Review the basic Playbook language features
   :ref:`playbooks_best_practices`
       Tips and tricks for playbooks
   :ref:`playbooks_variables`
       Variables in playbooks
   :ref:`playbooks_conditionals`
       Conditionals in playbooks
   :ref:`playbooks_loops`
       Loops in playbooks
   :ref:`tags`
       Using tags to select or skip roles/tasks in long playbooks
   :ref:`list_of_collections`
       Browse existing collections, modules, and plugins
   :ref:`developing_modules`
       Extending Ansible by writing your own modules
   `GitHub Ansible examples <https://github.com/ansible/ansible-examples>`_
       Complete playbook files from the GitHub project source
   `Mailing List <https://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
