Ansible Galaxy
++++++++++++++

"Ansible Galaxy" can either refer to a website for sharing and downloading Ansible roles, or a command line tool that helps work with roles.

.. contents:: Topics

The Website
```````````

The website `Ansible Galaxy <https://galaxy.ansible.com>`_, is a free site for finding, downloading, rating, and reviewing all kinds of community developed Ansible roles and can be a great way to get a jumpstart on your automation projects.

You can sign up with social auth and use the download client 'ansible-galaxy' which is included in Ansible 1.4.2 and later.

Read the "About" page on the Galaxy site for more information.

The ansible-galaxy command line tool
````````````````````````````````````

The command line ansible-galaxy has many different subcommands.

Installing Roles
----------------

The most obvious is downloading roles from the Ansible Galaxy website::

   ansible-galaxy install username.rolename

.. _roles_path:

roles_path
===============

You can specify a particular directory where you want the downloaded roles to be placed::

   ansible-galaxy install username.role -p ~/Code/ansible_roles/
   
This can be useful if you have a master folder that contains ansible galaxy roles shared across several projects. The default is the roles_path configured in your ansible.cfg file (/etc/ansible/roles if not configured).

Building out Role Scaffolding
-----------------------------

It can also be used to initialize the base structure of a new role, saving time on creating the various directories and main.yml files a role requires::

   ansible-galaxy init rolename

Installing Multiple Roles From A File
-------------------------------------

To install multiple roles, the ansible-galaxy CLI can be fed a requirements file.  All versions of ansible allow the following syntax for installing roles from the Ansible Galaxy website::

   ansible-galaxy install -r requirements.txt

Where the requirements.txt looks like::

   username1.foo_role
   username2.bar_role

To request specific versions (tags) of a role, use this syntax in the roles file::

   username1.foo_role,version
   username2.bar_role,version

Available versions will be listed on the Ansible Galaxy webpage for that role.

Advanced Control over Role Requirements Files
---------------------------------------------

For more advanced control over where to download roles from, including support for remote repositories, Ansible 1.8 and later support a new YAML format for the role requirements file, which must end in a 'yml' extension.  It works like this::

    ansible-galaxy install -r requirements.yml

The extension is important. If the .yml extension is left off, the ansible-galaxy CLI will assume the file is in the "basic" format and will be confused.

And here's an example showing some specific version downloads from multiple sources.  In one of the examples we also override the name of the role and download it as something different::

    # from galaxy
    - src: yatesr.timezone

    # from github
    - src: https://github.com/bennojoy/nginx

    # from github installing to a relative path
    - src: https://github.com/bennojoy/nginx
      path: vagrant/roles/

    # from github, overriding the name and specifying a specific tag
    - src: https://github.com/bennojoy/nginx
      version: master
      name: nginx_role
    
    # from a webserver, where the role is packaged in a tar.gz
    - src: https://some.webserver.example.com/files/master.tar.gz
      name: http-role

    # from bitbucket, if bitbucket happens to be operational right now :)
    - src: git+http://bitbucket.org/willthames/git-ansible-galaxy
      version: v1.4

    # from bitbucket, alternative syntax and caveats
    - src: http://bitbucket.org/willthames/hg-ansible-galaxy
      scm: hg

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

