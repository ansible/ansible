.. _ansible_galaxy:

Ansible Galaxy
++++++++++++++

*Ansible Galaxy* refers to the `Galaxy <https://galaxy.ansible.com>`_  website where users can share roles, and to a command line tool for installing,
creating and managing roles.

.. contents:: Topics

The Website
```````````

`Galaxy <https://galaxy.ansible.com>`_, is a free site for finding, downloading, and sharing community developed roles. Downloading roles from Galaxy is
a great way to jumpstart your automation projects.

You can also use the site to share roles that you create. By authenticating with the site using your GitHub account, you're able to *import* roles, making
them available to the Ansible community. Imported roles become available in the Galaxy search index and visible on the site, allowing users to
discover and download them.

Learn more by viewing `the About page <https://galaxy.ansible.com/intro>`_.

The command line tool
`````````````````````

The ``ansible-galaxy`` command comes bundled with Ansible, and you can use it to install roles from Galaxy or directly from a git based SCM. You can
also use it to create a new role, remove roles, or perform tasks on the Galaxy website.

The command line tool by default communicates with the Galaxy website API using the server address *https://galaxy.ansible.com*. Since the `Galaxy project <https://github.com/ansible/galaxy>`_
is an open source project, you may be running your own internal Galaxy server and wish to override the default server address. You can do this using the *--server* option
or by setting the Galaxy server value in your *ansible.cfg* file. For information on setting the value in *ansible.cfg* visit `Galaxy Settings <./intro_configuration.html#galaxy-settings>`_.


Installing Roles
----------------

Use the ``ansible-galaxy`` command to download roles from the `Galaxy website <https://galaxy.ansible.com>`_

::

    $ ansible-galaxy install username.role_name

roles_path
==========

Be aware that by default Ansible downloads roles to the path specified by the environment variable :envvar:`ANSIBLE_ROLES_PATH`. This can be set to a series of
directories (i.e. */etc/ansible/roles:~/.ansible/roles*), in which case the first writable path will be used. When Ansible is first installed it defaults
to */etc/ansible/roles*, which requires *root* privileges.

You can override this by setting the environment variable in your session, defining *roles_path* in an *ansible.cfg* file, or by using the *--roles-path* option.
The following provides an example of using *--roles-path* to install the role into the current working directory:

::

    $ ansible-galaxy install --roles-path . geerlingguy.apache

.. seealso::

   :ref:`intro_configuration`
      All about configuration files

version
=======

You can install a specific version of a role from Galaxy by appending a comma and the value of a GitHub release tag. For example:

::

   $ ansible-galaxy install geerlingguy.apache,v1.0.0

It's also possible to point directly to the git repository and specify a branch name or commit hash as the version. For example, the following will
install a specific commit:

::

   $ ansible-galaxy install git+https://github.com/geerlingguy/ansible-role-apache.git,0b7cd353c0250e87a26e0499e59e7fd265cc2f25


Installing multiple roles from a file
=====================================

Beginning with Ansible 1.8 it is possible to install multiple roles by including the roles in a *requirements.yml* file. The format of the file is YAML, and the
file extension must be either *.yml* or *.yaml*.

Use the following command to install roles included in *requirements.yml*:

::

    $ ansible-galaxy install -r requirements.yml

Again, the extension is important. If the *.yml* extension is left off, the ``ansible-galaxy`` CLI assumes the file is in an older, now deprecated,
"basic" format.

Each role in the file will have one or more of the following attributes:

   src
     The source of the role. Use the format *username.role_name*, if downloading from Galaxy; otherwise, provide a URL pointing
     to a repository within a git based SCM. See the examples below. This is a required attribute.
   scm
     Specify the SCM. As of this writing only *git* or *hg* are supported. See the examples below. Defaults to *git*.
   version:
     The version of the role to download. Provide a release tag value, commit hash, or branch name. Defaults to *master*.
   name:
     Download the role to a specific name. Defaults to the Galaxy name when downloading from Galaxy, otherwise it defaults
     to the name of the repository.

Use the following example as a guide for specifying roles in *requirements.yml*:

::

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
      name: http-role

    # from Bitbucket
    - src: git+http://bitbucket.org/willthames/git-ansible-galaxy
      version: v1.4

    # from Bitbucket, alternative syntax and caveats
    - src: http://bitbucket.org/willthames/hg-ansible-galaxy
      scm: hg

    # from GitLab or other git-based scm
    - src: git@gitlab.company.com:mygroup/ansible-base.git
      scm: git
      version: "0.1"  # quoted, so YAML doesn't parse this as a floating-point value

Installing multiple roles from multiple files
=============================================

At a basic level, including requirements files allows you to break up bits of roles into smaller files. Role includes pull in roles from other files.

Use the following command to install roles includes in *requirements.yml*  + *webserver.yml*

::

    ansible-galaxy install -r requirements.yml

Content of the *requirements.yml* file:

::

    # from galaxy
    - src: yatesr.timezone

    - include: <path_to_requirements>/webserver.yml


Content of the *webserver.yml* file:

::

    # from github
    - src: https://github.com/bennojoy/nginx

    # from Bitbucket
    - src: git+http://bitbucket.org/willthames/git-ansible-galaxy
      version: v1.4

Dependencies
============

Roles can also be dependent on other roles, and when you install a role that has dependencies, those dependencies will automatically be installed.

You specify role dependencies in the ``meta/main.yml`` file by providing a list of roles. If the source of a role is Galaxy, you can simply specify the role in
the format ``username.role_name``. The more complex format used in ``requirements.yml`` is also supported, allowing you to provide ``src``, ``scm``, ``version``, and ``name``.

Tags are inherited *down* the dependency chain. In order for tags to be applied to a role and all its dependencies, the tag should be applied to the role, not to all the tasks within a role.

Roles listed as dependencies are subject to conditionals and tag filtering, and may not execute fully depending on
what tags and conditionals are applied.

Dependencies found in Galaxy can be specified as follows:

::

    dependencies:
      - geerlingguy.apache
      - geerlingguy.ansible


The complex form can also be used as follows:

::

    dependencies:
      - src: geerlingguy.ansible
      - src: git+https://github.com/geerlingguy/ansible-role-composer.git
        version: 775396299f2da1f519f0d8885022ca2d6ee80ee8
        name: composer

When dependencies are encountered by ``ansible-galaxy``, it will automatically install each dependency to the ``roles_path``. To understand how dependencies are handled during play execution, see :ref:`playbooks_reuse_roles`.

.. note::

    At the time of this writing, the Galaxy website expects all role dependencies to exist in Galaxy, and therefore dependencies to be specified in the
    ``username.role_name`` format. If you import a role with a dependency where the ``src`` value is a URL, the import process will fail.

Create roles
------------

Use the ``init`` command to initialize the base structure of a new role, saving time on creating the various directories and main.yml files a role requires

::

   $ ansible-galaxy init role_name

The above will create the following directory structure in the current working directory:

::

   README.md
   .travis.yml
   defaults/
       main.yml
   files/
   handlers/
       main.yml
   meta/
       main.yml
   templates/
   tests/
       inventory
       test.yml
   vars/
       main.yml

Force
=====

If a directory matching the name of the role already exists in the current working directory, the init command will result in an error. To ignore the error
use the *--force* option. Force will create the above subdirectories and files, replacing anything that matches.

Container Enabled
=================

If you are creating a Container Enabled role, use the *--container-enabled* option. This will create the same directory structure as above, but populate it
with default files appropriate for a Container Enabled role. For instance, the README.md has a slightly different structure, the *.travis.yml* file tests
the role using `Ansible Container <https://github.com/ansible/ansible-container>`_, and the meta directory includes a *container.yml* file.

Using a Custom Role Skeleton
============================

A custom role skeleton directory can be supplied as follows:

::

   $ ansible-galaxy init --role-skeleton=/path/to/skeleton role_name

When a skeleton is provided, init will:

- copy all files and directories from the skeleton to the new role
- any .j2 files found outside of a templates folder will be rendered as templates. The only useful variable at the moment is role_name
- The .git folder and any .git_keep files will not be copied

Alternatively, the role_skeleton and ignoring of files can be configured via ansible.cfg

::

  [galaxy]
  role_skeleton = /path/to/skeleton
  role_skeleton_ignore = ^.git$,^.*/.git_keep$


Search for Roles
----------------

Search the Galaxy database by tags, platforms, author and multiple keywords. For example:

::

    $ ansible-galaxy search elasticsearch --author geerlingguy

The search command will return a list of the first 1000 results matching your search:

::

    Found 2 roles matching your search:

    Name                              Description
    ----                              -----------
    geerlingguy.elasticsearch         Elasticsearch for Linux.
    geerlingguy.elasticsearch-curator Elasticsearch curator for Linux.


Get more information about a role
---------------------------------

Use the ``info`` command to view more detail about a specific role:

::

    $ ansible-galaxy info username.role_name

This returns everything found in Galaxy for the role:

::

    Role: username.role_name
        description: Installs and configures a thing, a distributed, highly available NoSQL thing.
        active: True
        commit: c01947b7bc89ebc0b8a2e298b87ab416aed9dd57
        commit_message: Adding travis
        commit_url: https://github.com/username/repo_name/commit/c01947b7bc89ebc0b8a2e298b87ab
        company: My Company, Inc.
        created: 2015-12-08T14:17:52.773Z
        download_count: 1
        forks_count: 0
        github_branch:
        github_repo: repo_name
        github_user: username
        id: 6381
        is_valid: True
        issue_tracker_url:
        license: Apache
        min_ansible_version: 1.4
        modified: 2015-12-08T18:43:49.085Z
        namespace: username
        open_issues_count: 0
        path: /Users/username/projects/roles
        scm: None
        src: username.repo_name
        stargazers_count: 0
        travis_status_url: https://travis-ci.org/username/repo_name.svg?branch=master
        version:
        watchers_count: 1


List installed roles
--------------------

Use ``list`` to show the name and version of each role installed in the *roles_path*.

::

    $ ansible-galaxy list

    - chouseknecht.role-install_mongod, master
    - chouseknecht.test-role-1, v1.0.2
    - chrismeyersfsu.role-iptables, master
    - chrismeyersfsu.role-required_vars, master

Remove an installed role
------------------------

Use ``remove`` to delete a role from *roles_path*:

::

    $ ansible-galaxy remove username.role_name

Authenticate with Galaxy
------------------------

Using the ``import``, ``delete`` and ``setup`` commands to manage your roles on the Galaxy website requires authentication, and the ``login`` command
can be used to do just that. Before you can use the ``login`` command, you must create an account on the Galaxy website.

The ``login`` command requires using your GitHub credentials. You can use your username and password, or you can create a `personal access token <https://help.github.com/articles/creating-an-access-token-for-command-line-use/>`_. If you choose to create a token, grant minimal access to the token, as it is used just to verify identify.

The following shows authenticating with the Galaxy website using a GitHub username and password:

::

    $ ansible-galaxy login

    We need your GitHub login to identify you.
    This information will not be sent to Galaxy, only to api.github.com.
    The password will not be displayed.

    Use --github-token if you do not want to enter your password.

    Github Username: dsmith
    Password for dsmith:
    Successfully logged into Galaxy as dsmith

When you choose to use your username and password, your password is not sent to Galaxy. It is used to authenticates with GitHub and create a personal access token.
It then sends the token to Galaxy, which in turn verifies that your identity and returns a Galaxy access token. After authentication completes the GitHub token is
destroyed.

If you do not wish to use your GitHub password, or if you have two-factor authentication enabled with GitHub, use the *--github-token* option to pass a personal access token
that you create.


Import a role
-------------

The ``import`` command requires that you first authenticate using the ``login`` command. Once authenticated you can import any GitHub repository that you own or have
been granted access.

Use the following to import to role:

::

    $ ansible-galaxy import github_user github_repo

By default the command will wait for Galaxy to complete the import process, displaying the results as the import progresses:

::

    Successfully submitted import request 41
    Starting import 41: role_name=myrole repo=githubuser/ansible-role-repo ref=
    Retrieving GitHub repo githubuser/ansible-role-repo
    Accessing branch: master
    Parsing and validating meta/main.yml
    Parsing galaxy_tags
    Parsing platforms
    Adding dependencies
    Parsing and validating README.md
    Adding repo tags as role versions
    Import completed
    Status SUCCESS : warnings=0 errors=0

Branch
======

Use the *--branch* option to import a specific branch. If not specified, the default branch for the repo will be used.

Role name
=========

By default the name given to the role will be derived from the GitHub repository name. However, you can use the *--role-name* option to override this and set the name.

No wait
=======

If the *--no-wait* option is present, the command will not wait for results. Results of the most recent import for any of your roles is available on the Galaxy web site
by visiting *My Imports*.

Delete a role
-------------

The ``delete`` command requires that you first authenticate using the ``login`` command. Once authenticated you can remove a role from the Galaxy web site. You are only allowed
to remove roles where you have access to the repository in GitHub.

Use the following to delete a role:

::

    $ ansible-galaxy delete github_user github_repo

This only removes the role from Galaxy. It does not remove or alter the actual GitHub repository.


Travis integrations
-------------------

You can create an integration or connection between a role in Galaxy and `Travis <http://travis-ci.org>`_. Once the connection is established, a build in Travis will
automatically trigger an import in Galaxy, updating the search index with the latest information about the role.

You create the integration using the ``setup`` command, but before an integration can be created, you must first authenticate using the ``login`` command; you will
also need an account in Travis, and your Travis token. Once you're ready, use the following command to create the integration:

::

    $ ansible-galaxy setup travis github_user github_repo xxx-travis-token-xxx

The setup command requires your Travis token, however the token is not stored in Galaxy. It is used along with the GitHub username and repo to create a hash as described
in `the Travis documentation <https://docs.travis-ci.com/user/notifications/>`_. The hash is stored in Galaxy and used to verify notifications received from Travis.

The setup command enables Galaxy to respond to notifications. To configure Travis to run a build on your repository and send a notification, follow the
`Travis getting started guide <https://docs.travis-ci.com/user/getting-started/>`_.

To instruct Travis to notify Galaxy when a build completes, add the following to your .travis.yml file:

::

    notifications:
        webhooks: https://galaxy.ansible.com/api/v1/notifications/


List Travis integrations
========================

Use the *--list* option to display your Travis integrations:

::

    $ ansible-galaxy setup --list


    ID         Source     Repo
    ---------- ---------- ----------
    2          travis     github_user/github_repo
    1          travis     github_user/github_repo


Remove Travis integrations
==========================

Use the *--remove* option to disable and remove a Travis integration:

::

    $ ansible-galaxy setup --remove ID

Provide the ID of the integration to be disabled. You can find the ID by using the *--list* option.


.. seealso::

   :ref:`playbooks_reuse_roles`
       All about ansible roles
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
