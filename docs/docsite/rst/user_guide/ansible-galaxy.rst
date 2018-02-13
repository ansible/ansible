.. _ansible-galaxy:

==============
ansible-galaxy
==============


:strong:`None`


.. contents::
   :local:
   :depth: 2


.. program:: ansible-galaxy

Synopsis
========

.. code-block:: bash

   ansible-galaxy [delete|import|info|init|install|list|login|remove|search|setup] [--help] [options] ...


Description
===========


command to manage Ansible roles in shared repostories, the default of which is Ansible Galaxy *https://galaxy.ansible.com*.


Common Options
==============




.. option:: --list

   List all of your integrations.


.. option:: --remove <REMOVE_ID>

   Remove the integration matching the provided ID value. Use --list to see ID values.


.. option:: --version

   show program's version number and exit


.. option:: -c, --ignore-certs

   Ignore SSL certificate validation errors.


.. option:: -h, --help

   show this help message and exit


.. option:: -s <API_SERVER>, --server <API_SERVER>

   The API server destination


.. option:: -v, --verbose

   verbose mode (-vvv for more, -vvvv to enable connection debugging)






Actions
=======



.. program:: ansible-galaxy info
.. _ansible_galaxy_info:

info
----

prints out detailed information about an installed role as well as info available from the galaxy API.





.. option:: --offline 

   Don't query the galaxy API when creating roles

.. option:: -p , --roles-path 

   The path to the directory containing your roles. The default is the roles_path configured in your ansible.cfgfile (/etc/ansible/roles if not configured)





.. program:: ansible-galaxy search
.. _ansible_galaxy_search:

search
------

searches for roles on the Ansible Galaxy server





.. option:: --author  <AUTHOR>

   GitHub username

.. option:: --galaxy-tags  <GALAXY_TAGS>

   list of galaxy tags to filter by

.. option:: --platforms  <PLATFORMS>

   list of OS platforms to filter by

.. option:: -p , --roles-path 

   The path to the directory containing your roles. The default is the roles_path configured in your ansible.cfgfile (/etc/ansible/roles if not configured)





.. program:: ansible-galaxy setup
.. _ansible_galaxy_setup:

setup
-----

Setup an integration from Github or Travis for Ansible Galaxy roles





.. option:: --list 

   List all of your integrations.

.. option:: --remove  <REMOVE_ID>

   Remove the integration matching the provided ID value. Use --list to see ID values.





.. program:: ansible-galaxy list
.. _ansible_galaxy_list:

list
----

lists the roles installed on the local system or matches a single role passed as an argument.





.. option:: -p , --roles-path 

   The path to the directory containing your roles. The default is the roles_path configured in your ansible.cfgfile (/etc/ansible/roles if not configured)





.. program:: ansible-galaxy remove
.. _ansible_galaxy_remove:

remove
------

removes the list of roles passed as arguments from the local system.





.. option:: -p , --roles-path 

   The path to the directory containing your roles. The default is the roles_path configured in your ansible.cfgfile (/etc/ansible/roles if not configured)





.. program:: ansible-galaxy init
.. _ansible_galaxy_init:

init
----

creates the skeleton framework of a role that complies with the galaxy metadata format.





.. option:: --container-enabled 

   Initialize the skeleton role with default contents for a Container Enabled role.

.. option:: --init-path  <INIT_PATH>

   The path in which the skeleton role will be created. The default is the current working directory.

.. option:: --offline 

   Don't query the galaxy API when creating roles

.. option:: --role-skeleton  <ROLE_SKELETON>

   The path to a role skeleton that the new role should be based upon.

.. option:: -f , --force 

   Force overwriting an existing role





.. program:: ansible-galaxy install
.. _ansible_galaxy_install:

install
-------

uses the args list of roles to be installed, unless -f was specified. The list of roles
can be a name (which will be downloaded via the galaxy API and github), or it can be a local .tar.gz file.





.. option:: -f , --force 

   Force overwriting an existing role

.. option:: -i , --ignore-errors 

   Ignore errors and continue with the next specified role.

.. option:: -n , --no-deps 

   Don't download roles listed as dependencies

.. option:: -p , --roles-path 

   The path to the directory containing your roles. The default is the roles_path configured in your ansible.cfgfile (/etc/ansible/roles if not configured)

.. option:: -r  <ROLE_FILE>, --role-file  <ROLE_FILE>

   A file containing a list of roles to be imported





.. program:: ansible-galaxy import
.. _ansible_galaxy_import:

import
------

used to import a role into Ansible Galaxy





.. option:: --branch  <REFERENCE>

   The name of a branch to import. Defaults to the repository's default branch (usually master)

.. option:: --no-wait 

   Don't wait for import results.

.. option:: --role-name  <ROLE_NAME>

   The name the role should have, if different than the repo name

.. option:: --status 

   Check the status of the most recent import request for given github_user/github_repo.





.. program:: ansible-galaxy login
.. _ansible_galaxy_login:

login
-----

verify user's identify via Github and retrieve an auth token from Ansible Galaxy.





.. option:: --github-token  <TOKEN>

   Identify with github token rather than username and password.





.. program:: ansible-galaxy delete
.. _ansible_galaxy_delete:

delete
------

Delete a role from Ansible Galaxy.




.. program:: ansible-galaxy


Environment
===========

The following environment variables may be specified.



:envvar:`ANSIBLE_CONFIG` -- Override the default ansible config file

Many more are available for most options in ansible.cfg


Files
=====


:file:`/etc/ansible/ansible.cfg` -- Config file, used if present

:file:`~/.ansible.cfg` -- User config file, overrides the default config if present

Author
======

Ansible was originally written by Michael DeHaan.

See the `AUTHORS` file for a complete list of contributors.


Copyright
=========

Copyright © 2017 Red Hat, Inc | Ansible.

Ansible is released under the terms of the GPLv3 License.

See also
========

:manpage:`ansible(1)`,  :manpage:`ansible-config(1)`,  :manpage:`ansible-console(1)`,  :manpage:`ansible-doc(1)`,  :manpage:`ansible-galaxy(1)`,  :manpage:`ansible-inventory(1)`,  :manpage:`ansible-playbook(1)`,  :manpage:`ansible-pull(1)`,  :manpage:`ansible-vault(1)`,  
