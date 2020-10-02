.. _vmware_rest_collect_info:

*************************************************
How to collect information about your environment
*************************************************

.. contents:: Topics

Introduction
============

This guide will show you how to utilize Ansible to collect information about your
environment. These information will be useful later for the other tutorials.

Scenario Requirements
=====================

In this scenario we've got a vCenter with an ESXi host.

Our environment is pre-initialized with the following elements:

- a datacenter called ``my_dc``
- a cluster called ``my_cluser``
- a cluster called ``my_cluser``
- an ESXi host called ``esxi1`` is in the cluster
- two datastores on the ESXi: ``rw_datastore`` and ``ro_datastore``
- a dvswitch based guest network

Finally, we use the environment variables to authenticate ourselves as explain in :ref:`vmware_rest_authentication`. 

How to collect information
==========================

In this examples, we will use the ``vcenter_*_info`` module to collect
information about the associated resources.

All these modules return a ``value`` key. Depending on the context, this ``value`` key will be either a list or a dictionary.

Datacenter
----------

Here we use the ``vcenter_datacenter_info`` module to list all the datacente:

.. literalinclude:: task_outputs/collect_a_list_of_the_datacenters.task.yaml

Result
______

As expected, the ``value`` key of the output is a list.

.. literalinclude:: task_outputs/collect_a_list_of_the_datacenters.result.json

Cluster
-------

Here we do the same with ``vcenter_cluster_info``:

.. literalinclude:: task_outputs/Build_a_list_of_all_the_clusters.task.yaml

Result
______

.. literalinclude:: task_outputs/Build_a_list_of_all_the_clusters.result.json

And we can also fetch the details about a specific cluster, to do so we use
the ``cluster`` parameter:

.. literalinclude:: task_outputs/Retrieve_details_about_the_first_cluster.task.yaml

Result
______

And the the ``value`` key of the output is this time a dictionary.


.. literalinclude:: task_outputs/Retrieve_details_about_the_first_cluster.result.json

Datastore
---------

Here we use ``vcenter_datastore_info`` to get a list of all the datastores:

.. literalinclude:: task_outputs/Retrieve_a_list_of_all_the_datastores.task.yaml

Result
______

.. literalinclude:: task_outputs/Retrieve_a_list_of_all_the_datastores.result.json

Folder
------

And here again, you use the ``vcenter_folder_info`` module to retrieve a list of all the folders.

.. literalinclude:: task_outputs/Build_a_list_of_all_the_folders.task.yaml

Result
______

.. literalinclude:: task_outputs/Build_a_list_of_all_the_folders.result.json

Most of the time, you will just want one type folders, in this case we can use filters to reduce the amount to collect. Most of the ``_info`` modules comes with similar filters.

.. literalinclude:: task_outputs/Build_a_list_of_all_the_folders_with_the_type_VIRTUAL_MACHINE_and_called_vm.task.yaml

Result
______

.. literalinclude:: task_outputs/Build_a_list_of_all_the_folders_with_the_type_VIRTUAL_MACHINE_and_called_vm.result.json
