.. _porting_2.6_guide:

*************************
Ansible 2.6 Porting Guide
*************************

This section discusses the behavioral changes between Ansible 2.5 and Ansible 2.6.

It is intended to assist in updating your playbooks, plugins and other parts of your Ansible infrastructure so they will work with this version of Ansible.

We suggest you read this page along with `Ansible Changelog for 2.6 <https://github.com/ansible/ansible/blob/stable-2.6/changelogs/CHANGELOG-v2.6.rst>`_ to understand what updates you may need to make.

This document is part of a collection on porting. The complete list of porting guides can be found at :ref:`porting guides <porting_guides>`.

.. contents:: Topics

Playbook
========

* The deprecated task option ``always_run`` has been removed, please use ``check_mode: no`` instead.

Deprecated
==========

* In the :ref:`nxos_igmp_interface module<nxos_igmp_interface_module>`, ``oif_prefix`` and ``oif_source`` properties are deprecated. Use ``ois_ps`` parameter with a dictionary of prefix and source to values instead.

Modules
=======

Major changes in popular modules are detailed here



Modules removed
---------------

The following modules no longer exist:


Deprecation notices
-------------------

The following modules will be removed in Ansible 2.10. Please update your playbooks accordingly.

* ``k8s_raw`` use :ref:`k8s <k8s_module>` instead.
* ``openshift_raw`` use :ref:`k8s <k8s_module>` instead.
* ``openshift_scale`` use :ref:`k8s_scale <k8s_scale_module>` instead.

Noteworthy module changes
-------------------------

* The ``upgrade`` module option for ``win_chocolatey`` has been removed; use ``state: latest`` instead.
* The ``reboot`` module option for ``win_feature`` has been removed; use the ``win_reboot`` action plugin instead
* The ``win_iis_webapppool`` module no longer accepts a string for the ``attributes`` module option; use the free form dictionary value instead
* The ``name`` module option for ``win_package`` has been removed; this is not used anywhere and should just be removed from your playbooks
* The ``win_regedit`` module no longer automatically corrects the hive path ``HCCC`` to ``HKCC``; use ``HKCC`` because this is the correct hive path
* The :ref:`file_module` now emits a deprecation warning when ``src`` is specified with a state
  other than ``hard`` or ``link`` as it is only supposed to be useful with those.  This could have
  an effect on people who were depending on a buggy interaction between src and other state's to
  place files into a subdirectory.  For instance::

    $ ansible localhost -m file -a 'path=/var/lib src=/tmp/ state=directory'

  Would create a directory named ``/tmp/lib``.  Instead of the above, simply spell out the entire
  destination path like this::

    $ ansible localhost -m file -a 'path=/tmp/lib state=directory'
* The ``k8s_raw`` and ``openshift_raw`` modules have been aliased to the new ``k8s`` module.
* The ``k8s`` module supports all Kubernetes resources including those from Custom Resource Definitions and aggregated API servers. This includes all OpenShift resources.
* The ``k8s`` module will not accept resources where subkeys have been snake_cased. This was a workaround that was suggested with the ``k8s_raw`` and ``openshift_raw`` modules.
* The ``k8s`` module may not accept resources where the ``api_version`` has been changed to match the shortened version in the Kubernetes Python client. You should now specify the proper full Kubernetes ``api_version`` for a resource.
* The ``k8s`` module can now process multi-document YAML files if they are passed with the ``src`` parameter. It will process each document as a separate resource. Resources provided inline with the ``resource_definition`` parameter must still be a single document.
* The ``k8s`` module will not automatically change ``Project`` creation requests into ``ProjectRequest`` creation requests as the ``openshift_raw`` module did. You must now specify the ``ProjectRequest`` kind explicitly.
* The ``k8s`` module will not automatically remove secrets from the Ansible return values (and by extension the log). In order to prevent secret values in a task from being logged, specify the ``no_log`` parameter on the task block.
* The ``k8s_scale`` module now supports scalable OpenShift objects, such as ``DeploymentConfig``.


Plugins
=======

Deprecation notices
-------------------

The following modules will be removed in Ansible 2.10. Please update your playbooks accordingly.

* ``openshift`` use ``k8s`` instead.


Noteworthy plugin changes
-------------------------

* The ``k8s`` lookup plugin now supports all Kubernetes resources including those from Custom Resource Definitions and aggregated API servers. This includes all OpenShift resources.
* The ``k8s`` lookup plugin may not accept resources where the ``api_version`` has been changed to match the shortened version in the Kubernetes Python client. You should now specify the proper full Kubernetes ``api_version`` for a resource.
* The ``k8s`` lookup plugin will no longer remove secrets from the Ansible return values (and by extension the log). In order to prevent secret values in a task from being logged, specify the ``no_log`` parameter on the task block.


Porting custom scripts
======================

No notable changes.

Networking
==========

No notable changes.
