Installing roles from Galaxy
============================

The ``ansible-galaxy`` command comes bundled with Ansible, and you can use it to install roles from Galaxy or directly from a git based SCM. You can
also use it to create a new role, remove roles, or perform tasks on the Galaxy website.

The command line tool by default communicates with the Galaxy website API using the server address *https://galaxy.ansible.com*. Since the `Galaxy project <https://github.com/ansible/galaxy>`_
is an open source project, you may be running your own internal Galaxy server and wish to override the default server address. You can do this using the *--server* option
or by setting the Galaxy server value in your *ansible.cfg* file. For information on setting the value in *ansible.cfg* see :ref:`galaxy_server`.


Installing Roles
----------------

Use the ``ansible-galaxy`` command to download roles from the `Galaxy website <https://galaxy.ansible.com>`_

.. code-block:: bash

  $ ansible-galaxy install username.role_name

roles_path
^^^^^^^^^^

By default Ansible downloads roles to the first writable directory in the default list of paths ``~/.ansible/roles:/usr/share/ansible/roles:/etc/ansible/roles``. This will install roles in the home directory of the user running ``ansible-galaxy``.

You can override this by setting the environment variable :envvar:`ANSIBLE_ROLES_PATH` in your session, defining ``roles_path`` in an ``ansible.cfg`` file, or by using the ``--roles-path`` option.

The following provides an example of using ``--roles-path`` to install the role into the current working directory:

.. code-block:: bash

    $ ansible-galaxy install --roles-path . geerlingguy.apache

.. seealso::

   :ref:`intro_configuration`
      All about configuration files

Installing a specific version of a role
---------------------------------------

You can install a specific version of a role from Galaxy by appending a comma and the value of a GitHub release tag. For example:

.. code-block:: bash

   $ ansible-galaxy install geerlingguy.apache,v1.0.0

It's also possible to point directly to the git repository and specify a branch name or commit hash as the version. For example, the following will
install a specific commit:

.. code-block:: bash

   $ ansible-galaxy install git+https://github.com/geerlingguy/ansible-role-apache.git,0b7cd353c0250e87a26e0499e59e7fd265cc2f25


Installing multiple roles from a file
-------------------------------------

Beginning with Ansible 1.8 it is possible to install multiple roles by including the roles in a *requirements.yml* file. The format of the file is YAML, and the
file extension must be either *.yml* or *.yaml*.

Use the following command to install roles included in *requirements.yml*:

.. code-block:: bash

    $ ansible-galaxy install -r requirements.yml

Again, the extension is important. If the *.yml* extension is left off, the ``ansible-galaxy`` CLI assumes the file is in an older, now deprecated,
"basic" format.

Each role in the file will have one or more of the following attributes:

   src
     The source of the role. Use the format *username.role_name*, if downloading from Galaxy; otherwise, provide a URL pointing
     to a repository within a git based SCM. See the examples below. This is a required attribute.
   scm
     Specify the SCM. As of this writing only *git* or *hg* are allowed. See the examples below. Defaults to *git*.
   version:
     The version of the role to download. Provide a release tag value, commit hash, or branch name. Defaults to the branch set as a default in the repository, otherwise defaults to the *master*.
   name:
     Download the role to a specific name. Defaults to the Galaxy name when downloading from Galaxy, otherwise it defaults
     to the name of the repository.

Use the following example as a guide for specifying roles in *requirements.yml*:

.. code-block:: text

    # from galaxy
    - src: yatesr.timezone

    # from GitHub
    - src: https://github.com/bennojoy/nginx

    # from GitHub, overriding the name and specifying a specific tag
    - src: https://github.com/bennojoy/nginx
      version: master
      name: nginx_role

    # from a webserver, where the role is packaged in a tar.gz
    - src: https://some.webserver.example.com/files/master.tar.gz
      name: http-role-gz

    # from a webserver, where the role is packaged in a tar.bz2
    - src: https://some.webserver.example.com/files/master.tar.bz2
      name: http-role-bz2

    # from a webserver, where the role is packaged in a tar.xz (Python 3.x only)
    - src: https://some.webserver.example.com/files/master.tar.xz
      name: http-role-xz

    # from Bitbucket
    - src: git+https://bitbucket.org/willthames/git-ansible-galaxy
      version: v1.4

    # from Bitbucket, alternative syntax and caveats
    - src: https://bitbucket.org/willthames/hg-ansible-galaxy
      scm: hg

    # from GitLab or other git-based scm, using git+ssh
    - src: git@gitlab.company.com:mygroup/ansible-base.git
      scm: git
      version: "0.1"  # quoted, so YAML doesn't parse this as a floating-point value

Installing multiple roles from multiple files
---------------------------------------------

At a basic level, including requirements files allows you to break up bits of roles into smaller files. Role includes pull in roles from other files.

Use the following command to install roles includes in *requirements.yml*  + *webserver.yml*

.. code-block:: bash

    ansible-galaxy install -r requirements.yml

Content of the *requirements.yml* file:

.. code-block:: text

    # from galaxy
    - src: yatesr.timezone

    - include: <path_to_requirements>/webserver.yml


Content of the *webserver.yml* file:

.. code-block:: text

    # from github
    - src: https://github.com/bennojoy/nginx

    # from Bitbucket
    - src: git+https://bitbucket.org/willthames/git-ansible-galaxy
      version: v1.4

.. _galaxy_dependencies:

Dependencies
------------

Roles can also be dependent on other roles, and when you install a role that has dependencies, those dependencies will automatically be installed.

You specify role dependencies in the ``meta/main.yml`` file by providing a list of roles. If the source of a role is Galaxy, you can simply specify the role in
the format ``username.role_name``. You can also use the more complex format in ``requirements.yml``, allowing you to provide ``src``, ``scm``, ``version``, and ``name``.

Tags are inherited *down* the dependency chain. In order for tags to be applied to a role and all its dependencies, the tag should be applied to the role, not to all the tasks within a role.

Roles listed as dependencies are subject to conditionals and tag filtering, and may not execute fully depending on
what tags and conditionals are applied.

Dependencies found in Galaxy can be specified as follows:

.. code-block:: text

    dependencies:
      - geerlingguy.apache
      - geerlingguy.ansible


The complex form can also be used as follows:

.. code-block:: text

    dependencies:
      - src: geerlingguy.ansible
      - src: git+https://github.com/geerlingguy/ansible-role-composer.git
        version: 775396299f2da1f519f0d8885022ca2d6ee80ee8
        name: composer

When dependencies are encountered by ``ansible-galaxy``, it will automatically install each dependency to the ``roles_path``. To understand how dependencies are handled during play execution, see :ref:`playbooks_reuse_roles`.

.. note::

    At the time of this writing, the Galaxy website expects all role dependencies to exist in Galaxy, and therefore dependencies to be specified in the
    ``username.role_name`` format. If you import a role with a dependency where the ``src`` value is a URL, the import process will fail.

List installed roles
--------------------

Use ``list`` to show the name and version of each role installed in the *roles_path*.

.. code-block:: bash

    $ ansible-galaxy list

    - chouseknecht.role-install_mongod, master
    - chouseknecht.test-role-1, v1.0.2
    - chrismeyersfsu.role-iptables, master
    - chrismeyersfsu.role-required_vars, master

Remove an installed role
------------------------

Use ``remove`` to delete a role from *roles_path*:

.. code-block:: bash

    $ ansible-galaxy remove username.role_name
