:source: galaxy.py

.. _ansible-galaxy:

==============
ansible-galaxy
==============


:strong:`Perform various Role and Collection related operations.`


.. contents::
   :local:
   :depth: 3


.. program:: ansible-galaxy

Synopsis
========

.. code-block:: bash

   usage: ansible-galaxy [-h] [--version] [-v] TYPE ...



Description
===========


command to manage Ansible roles in shared repositories, the default of which is Ansible Galaxy *https://galaxy.ansible.com*.


Common Options
==============




.. option:: --version

   show program's version number, config file location, configured module search path, module location, executable location and exit


.. option:: -h, --help

   show this help message and exit


.. option:: -v, --verbose

   Causes Ansible to print more debug messages. Adding multiple -v will increase the verbosity, the builtin plugins currently evaluate up to -vvvvvv. A reasonable level to start is -vvv, connection debugging might require -vvvv.






Actions
=======



.. program:: ansible-galaxy collection
.. _ansible_galaxy_collection:

collection
----------

Perform the action on an Ansible Galaxy collection. Must be combined with a further action like init/install as
listed below.






.. program:: ansible-galaxy collection download
.. _ansible_galaxy_collection_download:

collection download
+++++++++++++++++++







.. option:: --clear-response-cache 

   Clear the existing server response cache.

.. option:: --no-cache 

   Do not use the server response cache.

.. option:: --pre 

   Include pre-release versions. Semantic versioning pre-releases are ignored by default

.. option:: --timeout  <TIMEOUT>

   The time to wait for operations against the galaxy server, defaults to 60s.

.. option:: --token  <API_KEY>, --api-key  <API_KEY>

   The Ansible Galaxy API key which can be found at https://galaxy.ansible.com/me/preferences.

.. option:: -c , --ignore-certs 

   Ignore SSL certificate validation errors.

.. option:: -n , --no-deps 

   Don't download collection(s) listed as dependencies.

.. option:: -p  <DOWNLOAD_PATH>, --download-path  <DOWNLOAD_PATH>

   The directory to download the collections to.

.. option:: -r  <REQUIREMENTS>, --requirements-file  <REQUIREMENTS>

   A file containing a list of collections to be downloaded.

.. option:: -s  <API_SERVER>, --server  <API_SERVER>

   The Galaxy API server URL






.. program:: ansible-galaxy collection init
.. _ansible_galaxy_collection_init:

collection init
+++++++++++++++

Creates the skeleton framework of a role or collection that complies with the Galaxy metadata format.
Requires a role or collection name. The collection name must be in the format ``<namespace>.<collection>``.





.. option:: --collection-skeleton  <COLLECTION_SKELETON>

   The path to a collection skeleton that the new collection should be based upon.

.. option:: --init-path  <INIT_PATH>

   The path in which the skeleton collection will be created. The default is the current working directory.

.. option:: --timeout  <TIMEOUT>

   The time to wait for operations against the galaxy server, defaults to 60s.

.. option:: --token  <API_KEY>, --api-key  <API_KEY>

   The Ansible Galaxy API key which can be found at https://galaxy.ansible.com/me/preferences.

.. option:: -c , --ignore-certs 

   Ignore SSL certificate validation errors.

.. option:: -f , --force 

   Force overwriting an existing role or collection

.. option:: -s  <API_SERVER>, --server  <API_SERVER>

   The Galaxy API server URL






.. program:: ansible-galaxy collection build
.. _ansible_galaxy_collection_build:

collection build
++++++++++++++++

Build an Ansible Galaxy collection artifact that can be stored in a central repository like Ansible Galaxy.
By default, this command builds from the current working directory. You can optionally pass in the
collection input path (where the ``galaxy.yml`` file is).





.. option:: --output-path  <OUTPUT_PATH>

   The path in which the collection is built to. The default is the current working directory.

.. option:: --timeout  <TIMEOUT>

   The time to wait for operations against the galaxy server, defaults to 60s.

.. option:: --token  <API_KEY>, --api-key  <API_KEY>

   The Ansible Galaxy API key which can be found at https://galaxy.ansible.com/me/preferences.

.. option:: -c , --ignore-certs 

   Ignore SSL certificate validation errors.

.. option:: -f , --force 

   Force overwriting an existing role or collection

.. option:: -s  <API_SERVER>, --server  <API_SERVER>

   The Galaxy API server URL






.. program:: ansible-galaxy collection publish
.. _ansible_galaxy_collection_publish:

collection publish
++++++++++++++++++

Publish a collection into Ansible Galaxy. Requires the path to the collection tarball to publish.





.. option:: --import-timeout  <IMPORT_TIMEOUT>

   The time to wait for the collection import process to finish.

.. option:: --no-wait 

   Don't wait for import validation results.

.. option:: --timeout  <TIMEOUT>

   The time to wait for operations against the galaxy server, defaults to 60s.

.. option:: --token  <API_KEY>, --api-key  <API_KEY>

   The Ansible Galaxy API key which can be found at https://galaxy.ansible.com/me/preferences.

.. option:: -c , --ignore-certs 

   Ignore SSL certificate validation errors.

.. option:: -s  <API_SERVER>, --server  <API_SERVER>

   The Galaxy API server URL






.. program:: ansible-galaxy collection install
.. _ansible_galaxy_collection_install:

collection install
++++++++++++++++++







.. option:: --clear-response-cache 

   Clear the existing server response cache.

.. option:: --disable-gpg-verify 

   Disable GPG signature verification when installing collections from a Galaxy server

.. option:: --force-with-deps 

   Force overwriting an existing collection and its dependencies.

.. option:: --ignore-signature-status-code 

   A status code to ignore during signature verification (for example, NO_PUBKEY). Provide this option multiple times to ignore a list of status codes. Descriptions for the choices can be seen at L(https://github.com/gpg/gnupg/blob/master/doc/DETAILS#general-status-codes).

.. option:: --keyring  <KEYRING>

   The keyring used during signature verification

.. option:: --no-cache 

   Do not use the server response cache.

.. option:: --offline 

   Install collection artifacts (tarballs) without contacting any distribution servers. This does not apply to collections in remote Git repositories or URLs to remote tarballs.

.. option:: --pre 

   Include pre-release versions. Semantic versioning pre-releases are ignored by default

.. option:: --required-valid-signature-count  <REQUIRED_VALID_SIGNATURE_COUNT>

   The number of signatures that must successfully verify the collection. This should be a positive integer or -1 to signify that all signatures must be used to verify the collection. Prepend the value with + to fail if no valid signatures are found for the collection (e.g. +all).

.. option:: --signature 

   An additional signature source to verify the authenticity of the MANIFEST.json before installing the collection from a Galaxy server. Use in conjunction with a positional collection name (mutually exclusive with --requirements-file).

.. option:: --timeout  <TIMEOUT>

   The time to wait for operations against the galaxy server, defaults to 60s.

.. option:: --token  <API_KEY>, --api-key  <API_KEY>

   The Ansible Galaxy API key which can be found at https://galaxy.ansible.com/me/preferences.

.. option:: -U , --upgrade 

   Upgrade installed collection artifacts. This will also update dependencies unless --no-deps is provided

.. option:: -c , --ignore-certs 

   Ignore SSL certificate validation errors.

.. option:: -f , --force 

   Force overwriting an existing role or collection

.. option:: -i , --ignore-errors 

   Ignore errors during installation and continue with the next specified collection. This will not ignore dependency conflict errors.

.. option:: -n , --no-deps 

   Don't download collections listed as dependencies.

.. option:: -p  <COLLECTIONS_PATH>, --collections-path  <COLLECTIONS_PATH>

   The path to the directory containing your collections.

.. option:: -r  <REQUIREMENTS>, --requirements-file  <REQUIREMENTS>

   A file containing a list of collections to be installed.

.. option:: -s  <API_SERVER>, --server  <API_SERVER>

   The Galaxy API server URL






.. program:: ansible-galaxy collection list
.. _ansible_galaxy_collection_list:

collection list
+++++++++++++++

List installed collections or roles





.. option:: --format  <OUTPUT_FORMAT>

   Format to display the list of collections in.

.. option:: --timeout  <TIMEOUT>

   The time to wait for operations against the galaxy server, defaults to 60s.

.. option:: --token  <API_KEY>, --api-key  <API_KEY>

   The Ansible Galaxy API key which can be found at https://galaxy.ansible.com/me/preferences.

.. option:: -c , --ignore-certs 

   Ignore SSL certificate validation errors.

.. option:: -p , --collections-path 

   One or more directories to search for collections in addition to the default COLLECTIONS_PATHS. Separate multiple paths with ':'.

.. option:: -s  <API_SERVER>, --server  <API_SERVER>

   The Galaxy API server URL






.. program:: ansible-galaxy collection verify
.. _ansible_galaxy_collection_verify:

collection verify
+++++++++++++++++







.. option:: --ignore-signature-status-code 

   A status code to ignore during signature verification (for example, NO_PUBKEY). Provide this option multiple times to ignore a list of status codes. Descriptions for the choices can be seen at L(https://github.com/gpg/gnupg/blob/master/doc/DETAILS#general-status-codes).

.. option:: --keyring  <KEYRING>

   The keyring used during signature verification

.. option:: --offline 

   Validate collection integrity locally without contacting server for canonical manifest hash.

.. option:: --required-valid-signature-count  <REQUIRED_VALID_SIGNATURE_COUNT>

   The number of signatures that must successfully verify the collection. This should be a positive integer or all to signify that all signatures must be used to verify the collection. Prepend the value with + to fail if no valid signatures are found for the collection (e.g. +all).

.. option:: --signature 

   An additional signature source to verify the authenticity of the MANIFEST.json before using it to verify the rest of the contents of a collection from a Galaxy server. Use in conjunction with a positional collection name (mutually exclusive with --requirements-file).

.. option:: --timeout  <TIMEOUT>

   The time to wait for operations against the galaxy server, defaults to 60s.

.. option:: --token  <API_KEY>, --api-key  <API_KEY>

   The Ansible Galaxy API key which can be found at https://galaxy.ansible.com/me/preferences.

.. option:: -c , --ignore-certs 

   Ignore SSL certificate validation errors.

.. option:: -i , --ignore-errors 

   Ignore errors during verification and continue with the next specified collection.

.. option:: -p , --collections-path 

   One or more directories to search for collections in addition to the default COLLECTIONS_PATHS. Separate multiple paths with ':'.

.. option:: -r  <REQUIREMENTS>, --requirements-file  <REQUIREMENTS>

   A file containing a list of collections to be verified.

.. option:: -s  <API_SERVER>, --server  <API_SERVER>

   The Galaxy API server URL







.. program:: ansible-galaxy role
.. _ansible_galaxy_role:

role
----

Perform the action on an Ansible Galaxy role. Must be combined with a further action like delete/install/init
as listed below.






.. program:: ansible-galaxy role init
.. _ansible_galaxy_role_init:

role init
+++++++++

Creates the skeleton framework of a role or collection that complies with the Galaxy metadata format.
Requires a role or collection name. The collection name must be in the format ``<namespace>.<collection>``.





.. option:: --init-path  <INIT_PATH>

   The path in which the skeleton role will be created. The default is the current working directory.

.. option:: --offline 

   Don't query the galaxy API when creating roles

.. option:: --role-skeleton  <ROLE_SKELETON>

   The path to a role skeleton that the new role should be based upon.

.. option:: --timeout  <TIMEOUT>

   The time to wait for operations against the galaxy server, defaults to 60s.

.. option:: --token  <API_KEY>, --api-key  <API_KEY>

   The Ansible Galaxy API key which can be found at https://galaxy.ansible.com/me/preferences.

.. option:: --type  <ROLE_TYPE>

   Initialize using an alternate role type. Valid types include: 'container', 'apb' and 'network'.

.. option:: -c , --ignore-certs 

   Ignore SSL certificate validation errors.

.. option:: -f , --force 

   Force overwriting an existing role or collection

.. option:: -s  <API_SERVER>, --server  <API_SERVER>

   The Galaxy API server URL






.. program:: ansible-galaxy role remove
.. _ansible_galaxy_role_remove:

role remove
+++++++++++

removes the list of roles passed as arguments from the local system.





.. option:: --timeout  <TIMEOUT>

   The time to wait for operations against the galaxy server, defaults to 60s.

.. option:: --token  <API_KEY>, --api-key  <API_KEY>

   The Ansible Galaxy API key which can be found at https://galaxy.ansible.com/me/preferences.

.. option:: -c , --ignore-certs 

   Ignore SSL certificate validation errors.

.. option:: -p , --roles-path 

   The path to the directory containing your roles. The default is the first writable one configured via DEFAULT_ROLES_PATH: {{ ANSIBLE_HOME ~ "/roles:/usr/share/ansible/roles:/etc/ansible/roles" }} 

.. option:: -s  <API_SERVER>, --server  <API_SERVER>

   The Galaxy API server URL






.. program:: ansible-galaxy role delete
.. _ansible_galaxy_role_delete:

role delete
+++++++++++

Delete a role from Ansible Galaxy.





.. option:: --timeout  <TIMEOUT>

   The time to wait for operations against the galaxy server, defaults to 60s.

.. option:: --token  <API_KEY>, --api-key  <API_KEY>

   The Ansible Galaxy API key which can be found at https://galaxy.ansible.com/me/preferences.

.. option:: -c , --ignore-certs 

   Ignore SSL certificate validation errors.

.. option:: -s  <API_SERVER>, --server  <API_SERVER>

   The Galaxy API server URL






.. program:: ansible-galaxy role list
.. _ansible_galaxy_role_list:

role list
+++++++++

List installed collections or roles





.. option:: --timeout  <TIMEOUT>

   The time to wait for operations against the galaxy server, defaults to 60s.

.. option:: --token  <API_KEY>, --api-key  <API_KEY>

   The Ansible Galaxy API key which can be found at https://galaxy.ansible.com/me/preferences.

.. option:: -c , --ignore-certs 

   Ignore SSL certificate validation errors.

.. option:: -p , --roles-path 

   The path to the directory containing your roles. The default is the first writable one configured via DEFAULT_ROLES_PATH: {{ ANSIBLE_HOME ~ "/roles:/usr/share/ansible/roles:/etc/ansible/roles" }} 

.. option:: -s  <API_SERVER>, --server  <API_SERVER>

   The Galaxy API server URL






.. program:: ansible-galaxy role search
.. _ansible_galaxy_role_search:

role search
+++++++++++

searches for roles on the Ansible Galaxy server





.. option:: --author  <AUTHOR>

   GitHub username

.. option:: --galaxy-tags  <GALAXY_TAGS>

   list of galaxy tags to filter by

.. option:: --platforms  <PLATFORMS>

   list of OS platforms to filter by

.. option:: --timeout  <TIMEOUT>

   The time to wait for operations against the galaxy server, defaults to 60s.

.. option:: --token  <API_KEY>, --api-key  <API_KEY>

   The Ansible Galaxy API key which can be found at https://galaxy.ansible.com/me/preferences.

.. option:: -c , --ignore-certs 

   Ignore SSL certificate validation errors.

.. option:: -s  <API_SERVER>, --server  <API_SERVER>

   The Galaxy API server URL






.. program:: ansible-galaxy role import
.. _ansible_galaxy_role_import:

role import
+++++++++++

used to import a role into Ansible Galaxy





.. option:: --branch  <REFERENCE>

   The name of a branch to import. Defaults to the repository's default branch (usually master)

.. option:: --no-wait 

   Don't wait for import results.

.. option:: --role-name  <ROLE_NAME>

   The name the role should have, if different than the repo name

.. option:: --status 

   Check the status of the most recent import request for given github_user/github_repo.

.. option:: --timeout  <TIMEOUT>

   The time to wait for operations against the galaxy server, defaults to 60s.

.. option:: --token  <API_KEY>, --api-key  <API_KEY>

   The Ansible Galaxy API key which can be found at https://galaxy.ansible.com/me/preferences.

.. option:: -c , --ignore-certs 

   Ignore SSL certificate validation errors.

.. option:: -s  <API_SERVER>, --server  <API_SERVER>

   The Galaxy API server URL






.. program:: ansible-galaxy role setup
.. _ansible_galaxy_role_setup:

role setup
++++++++++

Setup an integration from Github or Travis for Ansible Galaxy roles





.. option:: --list 

   List all of your integrations.

.. option:: --remove  <REMOVE_ID>

   Remove the integration matching the provided ID value. Use --list to see ID values.

.. option:: --timeout  <TIMEOUT>

   The time to wait for operations against the galaxy server, defaults to 60s.

.. option:: --token  <API_KEY>, --api-key  <API_KEY>

   The Ansible Galaxy API key which can be found at https://galaxy.ansible.com/me/preferences.

.. option:: -c , --ignore-certs 

   Ignore SSL certificate validation errors.

.. option:: -p , --roles-path 

   The path to the directory containing your roles. The default is the first writable one configured via DEFAULT_ROLES_PATH: {{ ANSIBLE_HOME ~ "/roles:/usr/share/ansible/roles:/etc/ansible/roles" }} 

.. option:: -s  <API_SERVER>, --server  <API_SERVER>

   The Galaxy API server URL






.. program:: ansible-galaxy role info
.. _ansible_galaxy_role_info:

role info
+++++++++

prints out detailed information about an installed role as well as info available from the galaxy API.





.. option:: --offline 

   Don't query the galaxy API when creating roles

.. option:: --timeout  <TIMEOUT>

   The time to wait for operations against the galaxy server, defaults to 60s.

.. option:: --token  <API_KEY>, --api-key  <API_KEY>

   The Ansible Galaxy API key which can be found at https://galaxy.ansible.com/me/preferences.

.. option:: -c , --ignore-certs 

   Ignore SSL certificate validation errors.

.. option:: -p , --roles-path 

   The path to the directory containing your roles. The default is the first writable one configured via DEFAULT_ROLES_PATH: {{ ANSIBLE_HOME ~ "/roles:/usr/share/ansible/roles:/etc/ansible/roles" }} 

.. option:: -s  <API_SERVER>, --server  <API_SERVER>

   The Galaxy API server URL






.. program:: ansible-galaxy role install
.. _ansible_galaxy_role_install:

role install
++++++++++++







.. option:: --force-with-deps 

   Force overwriting an existing role and its dependencies.

.. option:: --timeout  <TIMEOUT>

   The time to wait for operations against the galaxy server, defaults to 60s.

.. option:: --token  <API_KEY>, --api-key  <API_KEY>

   The Ansible Galaxy API key which can be found at https://galaxy.ansible.com/me/preferences.

.. option:: -c , --ignore-certs 

   Ignore SSL certificate validation errors.

.. option:: -f , --force 

   Force overwriting an existing role or collection

.. option:: -g , --keep-scm-meta 

   Use tar instead of the scm archive option when packaging the role.

.. option:: -i , --ignore-errors 

   Ignore errors and continue with the next specified role.

.. option:: -n , --no-deps 

   Don't download roles listed as dependencies.

.. option:: -p , --roles-path 

   The path to the directory containing your roles. The default is the first writable one configured via DEFAULT_ROLES_PATH: {{ ANSIBLE_HOME ~ "/roles:/usr/share/ansible/roles:/etc/ansible/roles" }} 

.. option:: -r  <REQUIREMENTS>, --role-file  <REQUIREMENTS>

   A file containing a list of roles to be installed.

.. option:: -s  <API_SERVER>, --server  <API_SERVER>

   The Galaxy API server URL






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


License
=======

Ansible is released under the terms of the GPLv3+ License.

See also
========

:manpage:`ansible(1)`,  :manpage:`ansible-config(1)`,  :manpage:`ansible-console(1)`,  :manpage:`ansible-doc(1)`,  :manpage:`ansible-galaxy(1)`,  :manpage:`ansible-inventory(1)`,  :manpage:`ansible-playbook(1)`,  :manpage:`ansible-pull(1)`,  :manpage:`ansible-vault(1)`,  