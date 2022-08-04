.. _developing_collections:

**********************
Developing collections
**********************

Collections are a distribution format for Ansible content. You can package and distribute playbooks, roles, modules, and plugins using collections. A typical collection addresses a set of related use cases. For example, the ``cisco.ios`` collection automates management of Cisco IOS devices.

You can create a collection and publish it to `Ansible Galaxy <https://galaxy.ansible.com>`_ or to a private Automation Hub instance. You can publish certified collections to the Red Hat Automation Hub, part of the Red Hat Ansible Automation Platform.

.. toctree::
   :maxdepth: 2
   :caption: Developing new collections

   developing_collections_creating
   developing_collections_shared
   developing_collections_testing
   developing_collections_distributing
   developing_collections_documenting

.. toctree::
   :maxdepth: 2
   :caption: Working with existing collections

   developing_collections_migrating
   developing_collections_contributing
   developing_collections_changelogs

.. toctree::
   :maxdepth: 2
   :caption: Collections references

   developing_collections_structure
   collections_galaxy_meta

For instructions on developing modules, see :ref:`developing_modules_general`.

.. seealso::

   :ref:`collections`
       Learn how to install and use collections in playbooks and roles
   :ref:`contributing_maintained_collections`
       Guidelines for contributing to selected collections
   `Ansible Collections Overview and FAQ <https://github.com/ansible-collections/overview/blob/main/README.rst>`_
       Current development status of community collections and FAQ
   `Mailing List <https://groups.google.com/group/ansible-devel>`_
       The development mailing list
   :ref:`communication_irc`
       How to join Ansible chat channels
