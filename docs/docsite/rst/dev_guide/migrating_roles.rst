
.. _migrating_roles:

***************************************
Migrating Roles to Roles in Collections
***************************************

You can migrate an existing standalone role into a role within a collection.

.. contents::
   :local:
   :depth: 2

Standalone role structure
=========================

:ref:`Standalone roles <playbooks_reuse_roles>` have the following directory structure:

.. code-block:: bash

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


- defaults - default variables for the standalone role. See :ref:`Using variables <playbooks-variables>`.
- files - contains files that can be deployed with this standalone role.
- handlers - contains handlers, which may be used by this role or outside this role.
- library - contains custom Ansible Modules encapsulated within this standalone role.
- tasks - contains the main list of tasks executed by the standalone role.
- vars - other variables for the standalone role. See :ref:`Using variables <playbooks-variables>`.
- templates - contains templates which can be deployed with this standalone role.
- meta - defines some metadata for this standalone role such as dependencies and Ansible Galaxy information.

- \*_plugins - optionally any plugin type can be encapsulated inside a standalone role by placing a directory named PLUGINTYPE_plugins (such as ``filters_plugin``)

.. _roles_in_collections:

Roles within an Ansible collection
==================================

Ansible Collections can contain roles, modules, plugins, and playbooks. See :ref:`developing_collections` for details.

The collection directory structure includes a ``roles/`` directory:

.. code-block:: language

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

A collection can contain one or more roles in the :file:`roles/`` directory and these are almost identical to standalone roles with the following exceptions:

- Roles inside collections cannot contain a :file:`library/` directory with custom modules. Keep modules in the :file:`plugins/modules/`` directory of the collection. You can reference these collection modules in any of the roles contained within a collection, or externally using the fully qualified collection name (FQCN).
   - Modules inside a collection need FQCN paths for their Python imports. See :ref:`migrating_plugins_collection`.
- standalone roles can optionally encapsulate any plugin in a ``PLUGINTYPE_plugins/`` directory (such as ``filters_plugin/``), however these plugins will go into their respective ``plugins/PLUGINTYPE/`` directory (such as ``plugins/filter/``) in an Ansible collection. You reference these plugins with their FQCN.
  - NOTE: In standalone roles, some of the plugin directories referenced their plugin types in the plural sense; this is not the case in Collections. The specific plugin directories as expected as covered in the Creating a Collection section of this document.

Migrating a role to a collection
================================

In order to migrate from a standalone role to a Collection, we need to create a Collection. Fortunately, just as with standalone roles the ability to initialize a Collection is provided by the ``ansible-galaxy`` command-line utility.

We will create a Collection using both the namespace and the name in dot notation:
```
    ansible-galaxy collection init namespace.name
```
This will create the directory structure that’s listed at the top of this section of the document and the ``namespace/name/plugins/`` directory contains a ``README.md`` file, which is a markdown format document that explains the various types of Ansible Plugins that can be contained within the optionally created subdirectories.

Migrating a standalone role without plugins or modules
------------------------------------------------------

In the instance of a standalone role that does not contain any custom modules or plugins, the only thing that is necessary is to copy the entire standalone role directory into the ``roles/`` subdirectory of the Collection. At this point the Role may be used as referenced by FQCN.

Example:
```
$ mkdir namespace/name/roles/my_legacy_role/
$ cp -r /path/to/legacy/role/namespace/\* name/roles/my_legacy_role/
```
At this point we can utilize it in a playbook like the following:

```
---
- name: example role by FQCN
  hosts: some_host_pattern
  tasks:
    - name: import FQCN Role from a Collection
      import_role:
        name: namespace.name.my_legacy_role
```

Something to note from this example is that the type of Content from inside a Collection is inferred contextually. More information can be found in the [Ansible Collection User Guide](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html).


.. _migrating_plugins_collection:

Migrating plugins and modules
-----------------------------

Plugins, and Modules which are also plugins, written in Python need some consideration when using Collections. We will cover those situations here.

Custom module_utils
^^^^^^^^^^^^^^^^^^^

In the event you have a module that is written in Python and is using a custom module_utils, it was previously addressable in the top level ``ansible.module_utils`` Python namespace. However, that is no longer the case as the top level Python namespace will no longer merge the Ansible internal Python namespace with external content in the future and merging external content from Collections into the Ansible internal Python namespace is not supported. There is an example of this in the [Ansible Developing Collections Guide](https://docs.ansible.com/ansible/devel/dev_guide/developing_collections.html#module-utils), but we will also cover an example in this document.

When coding with ``module_utils`` in a collection, the Python import statement needs to take into account the _FQCN_ along with the ``ansible_collections`` convention. The resulting Python import will look like the following example:
```
from ansible_collections.{namespace}.{name}.plugins.module_utils.{util} import {something}
```

The following example code snippets show a Python and a PowerShell module using both default Ansible module_utils and those provided by a collection. In this example the namespace is ansible_example, the collection is community. In the Python example the module_util in question is called helper such that the FQCN is ``ansible_example.community.plugins.module_utils.helper``:

```python
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
```

In the PowerShell example the module_utils in question is called hyperv such that the FQCN is ``ansible_example.community.plugins.module_utils.hyperv``:

```
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
```

Importing from __init__.py
----------------------------------

Because of the way that the CPython interpreter does imports, combined with the way the Ansible plugin loader works, if your custom embedded Module or Plugin requires importing something from an ``__init__.py`` file that will also become part of your Collection, either by originating as content inside a standalone role or otherwise, it requires using the file name in the python import statement. The following example is for an ``__init__.py`` file that is part of a Callback Plugin found inside a Collection named ``namespace.name``.

```python
from ansible_collections.namespace.name.plugins.callback.__init__ import CustomBaseClass
```

Deliver Downstream Compatibility (RPMs)
========================================

In the event the content of a standalone role is part of a Support Lifecycle of a product, or there is some other requirement for a standalone role to continue co-existing with its Collection Role counterpart, hopefully as part of a transition period, there are ways to allow Collection Role content be delivered downstream in methods such as RPM packaging that will function like they did as standalone roles. There is a real-world example of “porting” RHEL System Roles to a Collection and providing existing backwards compatibility via downstream RPM [here](https://github.com/maxamillion/collection-rhel-system-roles), but we will walk through a fictional example in this section of the document.
- **NOTE:** This requires Ansible 2.9.0 or newer.


In this example we will have a standalone role called ``my-legacy-role.webapp`` to emulate a standalone role that contains dashes in the name (which is not valid in Collections), this standalone role will contain a custom module in the ``library/`` directory called manage_webserver.

```
mylegacy-role.webapp
├── defaults
├── files
├── handlers
├── library
├── meta
├── tasks
├── templates
├── tests
└── vars
```

The first thing we need to do is create a new Collection, for the sake of example we will use the namespace acme and the name webserver which produces the combination of ``acme.webserve``:r

```
$ ansible-galaxy collection init acme.webserver
- Collection acme.webserver was created successfully
$ tree acme -d 1
acme
└── webserver
	├── docs
	├── plugins
	└── roles
```
Next, we need to create our webapp Role inside the Collection by simply copying over all contents from the standalone role.

```
$ mkdir acme/webserver/roles/webapp
$ cp mylegacy-role.webapp/* acme/webserver/roles/webapp/
```

At this point we need to move the manage_webserver module to its new home in ``acme/webserver/plugins/modules/``:

```
$ cp mylegacy-role.webapp/library/manage_webserver.py acme/webserver/plugins/modules/manage.py
```

You will note that the original source file of ``manage_webserver.py`` and the destination file of ``manage.py`` differ in name. This is optional but I’ve chosen here to change the name of the module since I no longer have to contextualize the module with webserver being in the name, instead because the FQCN provides proper namespacing it can be used as ``acme.webserver.manage``. Next we will need to go through all Tasks files in the Role (in our example there is only one: ``mylegacy-role.webapp/tasks/main.yml``) and change any use of the ``manage_webserver`` module to ``acme.webserver.manage`` in the Tasks list.
- **NOTE:** The renaming that takes place here is not a requirement but simply an illustration of what Content referenced by FQCN can offer in terms of context and in turn can make module and plugin names shorter. Something else to keep in mind is that if there is a need to offer these modules independently of the Role to users, the old naming conventions can be maintained but users will have to add the [collections keyword to their Plays](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html#using-collections-in-a-playbook). Typically Roles are meant to be used as the abstraction layer and users aren’t digging in and using components of the Role independently so this is likely not a concern.

Now that we have a functional Collection what we will need to do is provide it and its roles as parallel Content in a downstream distribution mechanism. I will illustrate how to do this as an RPM.

Downstream RPM
---------------

In order to deliver a Role as both a standalone role and a Collection Role, only a few things need to be done and are outlined here:

- The Collection be placed in ``/usr/share/ansible/collections/ansible_collections/``
- The contents of the Role inside the Collection be copied into a directory named after the standalone role and be placed in ``/usr/share/ansible/roles/``
- All previously bundled modules and plugins that are used in the standalone role are now referenced by FQCN so that even though they are no longer embedded, they can be found from the Collection Contents
  - This is an example of how the content inside an Ansible Collection is a unique entity and doesn’t have to be bound to a Role or otherwise. We could have made two separate Collections: one for the modules and plugins and another for the standalone role to migrate to; and as long as the Role used the modules and plugins as FQCN entities it would work just as it always has.

Here is an example RPM spec file to accomplish this using the example content from above:
```
Name: acme-ansible-content
Summary: Ansible Collection for deploying and configuring ACME webapp
Version: 1.0.0
Release: 1%{?dist}
License: GPLv3+
Source0: amce-webserver-1.0.0.tar.gz

Url: https://github.com/acme/webserver-ansible-collection
BuildArch: noarch

%global roleprefix mylegacy-role.
%global collection_namespace acme
%global collection_name webserver

%global collection_dir %{_datadir}/ansible/collections/ansible_collections/%{collection_namespace}/%{collection_name}

%description
Ansible Collection and standalone role (for legacy compatibility and migration) to deploy, configure, and manage the ACME webapp software.

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
```
