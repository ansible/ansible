
.. _migrating_roles:

***************************************
Migrating Roles to Roles in Collections
***************************************

Collections can contain roles, modules, plugins, and playbooks. See :ref:`developing_collections` for details.
You can migrate an existing standalone role into a collection-based role.

.. contents::
   :local:
   :depth: 2

.. _roles_in_collections:

Comparing standalone roles to collection roles
===============================================

:ref:`Standalone roles <playbooks_reuse_roles>` have the following directory structure:

.. code-block:: bash
  :emphasize-lines: 5,7
  
    role/
    ├── defaults
    ├── files
    ├── handlers
    ├── library
    ├── meta
    ├── [*_plugins]
    ├── tasks
    ├── templates
    ├── tests
    └── vars


The collection directory structure includes a :file:`roles/` directory:

.. code-block:: bash

    namespace/
    └── name/
      ├── docs/
      ├── galaxy.yml
      ├── plugins/
      │   ├── modules/
      │   │   └── module1.py
      │   ├── inventory/
      │   └── .../
      ├── README.md
      ├── roles/
      │   ├── role1/
      │   ├── role2/
      │   └── .../
      ├── playbooks/
      │   ├── files/
      │   ├── vars/
      │   ├── templates/
      │   └── tasks/
      └── tests/

A collection can contain one or more roles in the :file:`roles/` directory and these are almost identical to standalone roles with the following exceptions:

- Collection roles cannot contain a :file:`library/` directory with custom modules. Move modules to the :file:`plugins/modules/` directory of the collection. You can reference these collection modules in any of the roles contained within a collection, or externally using the fully qualified collection name (:abbr:`FQCN (Fully Qualified Collection Name)`).
- Modules inside a collection need :abbr:`FQCN (Fully Qualified Collection Name)` paths for their Python imports. See :ref:`migrating_plugins_collection`.
- Standalone roles can optionally encapsulate any plugin in a :file:`PLUGINTYPE_plugins/` directory (such as :file:`filters_plugin/`). For roles in a collection, these plugins go into their respective :file:`plugins/PLUGINTYPE/` directory (such as :file:`plugins/filter/`) in an collection. You reference these plugins with their :abbr:`FQCN (Fully Qualified Collection Name)`.

.. note::

	 In standalone roles, some of the plugin directories referenced their plugin types in the plural sense; this is not the case in collections.

Migrating a role to a collection
================================

In order to migrate from a standalone role to a collection role, create a collection with the ``ansible-galaxy collection`` CLI command. You need a `Galaxy namespace <https://galaxy.ansible.com/docs/contributing/namespaces.html>`_ to import this collection to Galaxy.

.. code-block:: bash

  $ ansible-galaxy collection init mynamespace.mycollection

This creates the collection directory structure. The :file:`mynamespace/mycollection/plugins/` directory contains a :file:`README.md` file that explains the various types of plugins that the collection can contain within optionally created subdirectories.

Migrating a standalone role without plugins or modules
------------------------------------------------------

If you have a standalone role that does not contain any custom modules or plugins, copy the entire standalone role directory into the :file:`roles/` subdirectory of the collection. You can then reference the role with the :abbr:`FQCN (Fully Qualified Collection Name)`.

.. code-block:: bash

  $ mkdir mynamespace/mycollection/roles/my_role/
  $ cp -r /path/to/standalone/role/mynamespace/my_role/\* mynamespace/mycollection/roles/my_role/

The following example uses this collection role in a playbook:

.. code-block:: yaml

  ---
  - name: example role by FQCN
    hosts: some_host_pattern
    tasks:
      - name: import FQCN role from a collection
        import_role:
          name: mynamespace.mycollection.my_role

Note in this example that the type of content from inside a collection is inferred contextually. See :ref:`collections_using_playbook` for more details.


.. _migrating_plugins_collection:

Migrating plugins and modules
-----------------------------

Migrating plugins and modules from a standalone role to a collection requires a few more steps.

Custom module_utils
^^^^^^^^^^^^^^^^^^^

If you have a module that uses a custom ``module_utils``, you could previously address it in the top level ``ansible.module_utils`` Python namespace. This is no longer the case. The top level Python namespace no longer merges the Ansible internal Python namespace with external content and merging external content from collections into the Ansible internal Python namespace is not supported. This is explained below but see :ref:`collection_module_utils` for more details.

When coding with ``module_utils`` in a collection, the Python import statement needs to take into account the :abbr:`FQCN (Fully Qualified Collection Name)` along with the ``ansible_collections`` convention. The resulting Python import looks similar to the following example:

.. code-block:: python

  from ansible_collections.{namespace}.{collectionname}.plugins.module_utils.{util} import {something}

The following example code snippets show a Python and a PowerShell module using both default Ansible ``module_utils`` and those provided by a collection. In this example the namespace is ``ansible_example`` and the collection is ``community``.

In the Python example the ``module_util`` is ``helper`` and the :abbr:`FQCN (Fully Qualified Collection Name)` is ``ansible_example.community.plugins.module_utils.helper``:

.. code-block:: python

  from ansible.module_utils.basic import AnsibleModule
  from ansible.module_utils._text import to_text
  from ansible.module_utils.six.moves.urllib.parse import urlencode
  from ansible.module_utils.six.moves.urllib.error import HTTPError
  from ansible_collections.ansible_example.community.plugins.module_utils.helper import HelperRequest

  argspec = dict(
	  name=dict(required=True, type='str'),
	  state=dict(choices=['present', 'absent'], required=True),
  )

  module = AnsibleModule(
	  argument_spec=argspec,
	  supports_check_mode=True
  )

  _request = HelperRequest(
  	module,
	  headers={"Content-Type": "application/json"},
       data=data
 )

In the PowerShell example the ``module_utils`` is ``hyperv`` and the :abbr:`FQCN (Fully Qualified Collection Name)` is ``ansible_example.community.plugins.module_utils.hyperv``:

.. code-block:: powershell

  #!powershell
  #AnsibleRequires -CSharpUtil Ansible.Basic
  #AnsibleRequires -PowerShell ansible_collections.ansible_example.community.plugins.module_utils.hyperv

  $spec = @{
	  name = @{ required = $true; type = "str" }
  	state = @{ required = $true; choices = @("present", "absent") }
  }
  $module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

  Invoke-HyperVFunction -Name $module.Params.name

  $module.ExitJson()

Importing from __init__.py
^^^^^^^^^^^^^^^^^^^^^^^^^^

Because of the way that the CPython interpreter does imports, combined with the way the Ansible plugin loader works, if your custom embedded module or plugin requires importing something from an :file:`__init__.py` file, that also becomes part of your collection. You can either originate the content inside a standalone role or use the file name in the Python import statement. The following example is an :file:`__init__.py` file that is part of a callback plugin found inside a collection named ``ansible_example.community``.

.. code-block:: python

  from ansible_collections.ansible_example.community.plugins.callback.__init__ import CustomBaseClass


Example: Migrating a standalone role with modules to a collection
=================================================================

In this example we have a standalone role called ``my-standalone-role.webapp`` to emulate a standalone role that contains dashes in the name (which is not valid in collections). This standalone role contains a custom module in the ``library/`` directory called ``manage_webserver``.

.. code-block:: bash

  my-standalone-role.webapp
  ├── defaults
  ├── files
  ├── handlers
  ├── library
  ├── meta
  ├── tasks
  ├── templates
  ├── tests
  └── vars

1. Create a new collection, for example,``acme.webserver``:

.. code-block:: bash

  $ ansible-galaxy collection init acme.webserver
  - Collection acme.webserver was created successfully
  $ tree acme -d 1
  acme
  └── webserver
	 ├── docs
	 ├── plugins
	 └── roles

2. Create the ``webapp`` role inside the collection and copy all contents from the standalone role:

.. code-block:: bash

  $ mkdir acme/webserver/roles/webapp
  $ cp my-standalone-role.webapp/* acme/webserver/roles/webapp/

3. Move the ``manage_webserver`` module to its new home in ``acme/webserver/plugins/modules/``:

.. code-block:: bash

  $ cp my-standalone-role.webapp/library/manage_webserver.py acme/webserver/plugins/modules/manage.py

.. note::

  This example changed the original source file ``manage_webserver.py`` to the destination file ``manage.py``. This is optional but the :abbr:`FQCN (Fully Qualified Collection Name)` provides the ``webserver`` context as ``acme.webserver.manage``.

4. Change ``manage_webserver`` to ``acme.webserver.manage`` in :file:`tasks/` files in the role ( for example, ``my-standalone-role.webapp/tasks/main.yml``) and any use of the original module name.

.. note::

  This name change is only required if you changed the original module name, but illustrates content referenced by :abbr:`FQCN (Fully Qualified Collection Name)` can offer context and in turn can make module and plugin names shorter. If you anticipate using these modules independent of the role, keep the original naming conventions. Users can add the  :ref:`collections keyword <collections_using_playbook>` in their playbooks. Typically roles are an abstraction layer and users won't use components of the role independently.


Supporting standalone roles and migrated collection roles in a downstream RPM
=============================================================================

A standalone role can co-exist with its collection role counterpart (for example, as part of a support lifecycle of a product). This should only be done for a transition period, but these two can exist in downstream in packages such as RPMs. For example, the the RHEL system roles co-exit with the  `RHEL system roles collection <https://github.com/maxamillion/collection-rhel-system-roles>`_ and providing existing backwards compatibility with the downstream RPM.

This section walks through an example creating this coexistence in a downstream RPM and requires Ansible 2.9.0 or later.

To deliver a role as both a standalone role and a collection role:

#. Place the collection in  :file:`/usr/share/ansible/collections/ansible_collections/`.
#. Copy the contents of the role inside the collection into a directory named after the standalone role and place the standalone role in  :file:`/usr/share/ansible/roles/`.

All previously bundled modules and plugins used in the standalone role are now referenced by :abbr:`FQCN (Fully Qualified Collection Name)` so even though they are no longer embedded, they can be found from the collection contents.This is an example of how the content inside the collection is a unique entity and does not have to be bound to a role or otherwise. You could alternately create two separate collections: one for the modules and plugins and another for the standalone role to migrate to. The role must use the modules and plugins as :abbr:`FQCN (Fully Qualified Collection Name)`.

The following is an example RPM spec file that accomplishes this using this example content:

.. code-block:: text

  Name: acme-ansible-content
  Summary: Ansible Collection for deploying and configuring ACME webapp
  Version: 1.0.0
  Release: 1%{?dist}
  License: GPLv3+
  Source0: amce-webserver-1.0.0.tar.gz

  Url: https://github.com/acme/webserver-ansible-collection
  BuildArch: noarch

  %global roleprefix my-standalone-role.
  %global collection_namespace acme
  %global collection_name webserver

  %global collection_dir %{_datadir}/ansible/collections/ansible_collections/%{collection_namespace}/%{collection_name}

  %description
  Ansible Collection and standalone role (for backward compatibility and migration) to deploy, configure, and manage the ACME webapp software.

  %prep
  %setup -qc

  %build

  %install

  mkdir -p %{buildroot}/%{collection_dir}
  cp -r ./* %{buildroot}/%{collection_dir}/

  mkdir -p %{buildroot}/%{_datadir}/ansible/roles
  for role in %{buildroot}/%{collection_dir}/roles/*
    do
	   cp -pR ${role} %{buildroot}/%{_datadir}/ansible/roles/%{roleprefix}$(basename ${role})

	   mkdir -p %{buildroot}/%{_pkgdocdir}/$(basename ${role})
	   for docfile in README.md COPYING LICENSE
	    do
      	if [ -f ${role}/${docfile} ]
    	    then
          	cp -p ${role}/${docfile} %{buildroot}/%{_pkgdocdir}/$(basename ${role})/${docfile}
      	fi
	   done
  done


  %files
  %dir %{_datadir}/ansible
  %dir %{_datadir}/ansible/roles
  %dir %{_datadir}/ansible/collections
  %dir %{_datadir}/ansible/collections/ansible_collections
  %{_datadir}/ansible/roles/
  %doc %{_pkgdocdir}/*/README.md
  %doc %{_datadir}/ansible/roles/%{roleprefix}*/README.md
  %{collection_dir}
  %doc %{collection_dir}/roles/*/README.md
  %license %{_pkgdocdir}/*/COPYING
  %license %{_pkgdocdir}/*/LICENSE
