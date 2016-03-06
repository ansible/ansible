Ansible Galaxy
++++++++++++++

"Ansible Galaxy" can either refer to a website for sharing and downloading Ansible roles, or a command line tool for managing and creating roles.

.. contents:: Topics

The Website
```````````

The website `Ansible Galaxy <https://galaxy.ansible.com>`_, is a free site for finding, downloading, and sharing community developed Ansible roles. Downloading roles from Galaxy is a great way to jumpstart your automation projects.

Access the Galaxy web site using GitHub OAuth, and to install roles use the 'ansible-galaxy' command line tool included in Ansible 1.4.2 and later.

Read the "About" page on the Galaxy site for more information.

The ansible-galaxy command line tool
````````````````````````````````````

The ansible-galaxy command has many different sub-commands for managing roles both locally and at `galaxy.ansible.com <https://galaxy.ansible.com>`_.

.. note::

    The search, login, import, delete, and setup commands in the Ansible 2.0 version of ansible-galaxy require access to the 
    2.0 Beta release of the Galaxy web site available at `https://galaxy-qa.ansible.com <https://galaxy-qa.ansible.com>`_.

    Use the ``--server`` option to access the beta site. For example::

        $ ansible-galaxy search --server https://galaxy-qa.ansible.com mysql --author geerlingguy

    Additionally, you can define a server in ansible.cfg::

        [galaxy]
        server=https://galaxy-qa.ansible.com

Installing Roles
----------------

The most obvious use of the ansible-galaxy command is downloading roles from `the Ansible Galaxy website <https://galaxy.ansible.com>`_::

   $ ansible-galaxy install username.rolename

roles_path
==========

You can specify a particular directory where you want the downloaded roles to be placed::

   $ ansible-galaxy install username.role -p ~/Code/ansible_roles/
   
This can be useful if you have a master folder that contains ansible galaxy roles shared across several projects. The default is the roles_path configured in your ansible.cfg file (/etc/ansible/roles if not configured).

Installing Multiple Roles From A File
=====================================

To install multiple roles, the ansible-galaxy CLI can be fed a requirements file.  All versions of ansible allow the following syntax for installing roles from the Ansible Galaxy website::

   $ ansible-galaxy install -r requirements.txt

Where the requirements.txt looks like::

   username1.foo_role
   username2.bar_role

To request specific versions (tags) of a role, use this syntax in the roles file::

   username1.foo_role,version
   username2.bar_role,version

Available versions will be listed on the Ansible Galaxy webpage for that role.

Advanced Control over Role Requirements Files
=============================================

For more advanced control over where to download roles from, including support for remote repositories, Ansible 1.8 and later support a new YAML format for the role requirements file, which must end in a 'yml' extension.  It works like this::

    ansible-galaxy install -r requirements.yml

The extension is important. If the .yml extension is left off, the ansible-galaxy CLI will assume the file is in the "basic" format and will be confused.

And here's an example showing some specific version downloads from multiple sources.  In one of the examples we also override the name of the role and download it as something different::

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
      version: 0.1.0

As you can see in the above, there are a large amount of controls available
to customize where roles can be pulled from, and what to save roles as.     

Roles pulled from galaxy work as with other SCM sourced roles above. To download a role with dependencies, and automatically install those dependencies, the role must be uploaded to the Ansible Galaxy website.

.. seealso::

   :doc:`playbooks_roles`
       All about ansible roles
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel

Building Role Scaffolding
-------------------------

Use the init command to initialize the base structure of a new role, saving time on creating the various directories and main.yml files a role requires::

   $ ansible-galaxy init rolename

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

.. note::

    .travis.yml and tests/ are new in Ansible 2.0

If a directory matching the name of the role already exists in the current working directory, the init command will result in an error. To ignore the error use the --force option. Force will create the above subdirectories and files, replacing anything that matches.

Search for Roles
----------------

The search command provides for querying the Galaxy database, allowing for searching by tags, platforms, author and multiple keywords. For example:

::

    $ ansible-galaxy search elasticsearch --author geerlingguy

The search command will return a list of the first 1000 results matching your search:

::
    
    Found 2 roles matching your search:

    Name                              Description
    ----                              -----------
    geerlingguy.elasticsearch         Elasticsearch for Linux.
    geerlingguy.elasticsearch-curator Elasticsearch curator for Linux.

.. note::

   The format of results pictured here is new in Ansible 2.0.

Get More Information About a Role
---------------------------------

Use the info command To view more detail about a specific role:

::

    $ ansible-galaxy info username.role_name

This returns everything found in Galaxy for the role:

::

    Role: username.rolename
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


List Installed Roles
--------------------

The list command shows the name and version of each role installed in roles_path.

::

    $ ansible-galaxy list

    - chouseknecht.role-install_mongod, master
    - chouseknecht.test-role-1, v1.0.2
    - chrismeyersfsu.role-iptables, master
    - chrismeyersfsu.role-required_vars, master

Remove an Installed Role
------------------------

The remove command will delete a role from roles_path:

::

    $ ansible-galaxy remove username.rolename

Authenticate with Galaxy
------------------------

To use the import, delete and setup commands authentication with Galaxy is required. The login command will authenticate the user,retrieve a token from Galaxy, and store it in the user's home directory.

::

    $ ansible-galaxy login

    We need your Github login to identify you.
    This information will not be sent to Galaxy, only to api.github.com.
    The password will not be displayed.

    Use --github-token if you do not want to enter your password.

    Github Username: dsmith
    Password for dsmith:
    Succesfully logged into Galaxy as dsmith

As depicted above, the login command prompts for a GitHub username and password. It does NOT send your password to Galaxy. It actually authenticates with GitHub and creates a personal access token. It then sends the personal access token to Galaxy, which in turn verifies that you are you and returns a Galaxy access token. After authentication completes the GitHub personal access token is destroyed. 

If you do not wish to use your GitHub password, or if you have two-factor authentication enabled with GitHub, use the --github-token option to pass a personal access token that you create. Log into GitHub, go to Settings and click on Personal Access Token to create a token.

.. note::

    The login command in Ansible 2.0 requires using the Galaxy 2.0 Beta site. Use the ``--server`` option to access 
    `https://galaxy-qa.ansible.com <https://galaxy-qa.ansible.com>`_. You can also add a *server* definition in the [galaxy] 
    section of your ansible.cfg file.

Import a Role
-------------

Roles can be imported using ansible-galaxy. The import command expects that the user previously authenticated with Galaxy using the login command.

Import any GitHub repo you have access to:

::

    $ ansible-galaxy import github_user github_repo

By default the command will wait for the role to be imported by Galaxy, displaying the results as the import progresses:

::

    Successfully submitted import request 41
    Starting import 41: role_name=myrole repo=githubuser/ansible-role-repo ref=
    Retrieving Github repo githubuser/ansible-role-repo
    Accessing branch: master
    Parsing and validating meta/main.yml
    Parsing galaxy_tags
    Parsing platforms
    Adding dependencies
    Parsing and validating README.md
    Adding repo tags as role versions
    Import completed
    Status SUCCESS : warnings=0 errors=0

Use the --branch option to import a specific branch. If not specified, the default branch for the repo will be used.

If the --no-wait option is present, the command will not wait for results. Results of the most recent import for any of your roles is available on the Galaxy web site under My Imports.

.. note::

    The import command in Ansible 2.0 requires using the Galaxy 2.0 Beta site. Use the ``--server`` option to access 
    `https://galaxy-qa.ansible.com <https://galaxy-qa.ansible.com>`_. You can also add a *server* definition in the [galaxy] 
    section of your ansible.cfg file.

Delete a Role
-------------

Remove a role from the Galaxy web site using the delete command.  You can delete any role that you have access to in GitHub. The delete command expects that the user previously authenticated with Galaxy using the login command.

::

    $ ansible-galaxy delete github_user github_repo

This only removes the role from Galaxy. It does not impact the actual GitHub repo.

.. note::

    The delete command in Ansible 2.0 requires using the Galaxy 2.0 Beta site. Use the ``--server`` option to access 
    `https://galaxy-qa.ansible.com <https://galaxy-qa.ansible.com>`_. You can also add a *server* definition in the [galaxy] 
    section of your ansible.cfg file.

Setup Travis Integrations
--------------------------

Using the setup command you can enable notifications from `travis <http://travis-ci.org>`_. The setup command expects that the user previously authenticated with Galaxy using the login command.

::

    $ ansible-galaxy setup travis github_user github_repo xxxtravistokenxxx

    Added integration for travis github_user/github_repo 

The setup command requires your Travis token. The Travis token is not stored in Galaxy. It is used along with the GitHub username and repo to create a hash as described in `the Travis documentation <https://docs.travis-ci.com/user/notifications/>`_. The calculated hash is stored in Galaxy and used to verify notifications received from Travis.

The setup command enables Galaxy to respond to notifications. Follow the `Travis getting started guide <https://docs.travis-ci.com/user/getting-started/>`_ to enable the Travis build process for the role repository.

When you create your .travis.yml file add the following to cause Travis to notify Galaxy when a build completes:

::

    notifications:
        webhooks: https://galaxy.ansible.com/api/v1/notifications/

.. note::

    The setup command in Ansible 2.0 requires using the Galaxy 2.0 Beta site. Use the ``--server`` option to access 
    `https://galaxy-qa.ansible.com <https://galaxy-qa.ansible.com>`_. You can also add a *server* definition in the [galaxy] 
    section of your ansible.cfg file.


List Travis Integrations
========================

Use the --list option to display your Travis integrations:

::

    $ ansible-galaxy setup --list


    ID         Source     Repo
    ---------- ---------- ----------
    2          travis     github_user/github_repo
    1          travis     github_user/github_repo


Remove Travis Integrations
==========================

Use the --remove option to disable and remove a Travis integration:

::

    $ ansible-galaxy setup --remove ID

Provide the ID of the integration you want disabled. Use the --list option to get the ID.











 






