.. _modules_support:

****************************
Module Maintenance & Support
****************************

.. contents::
  :depth: 2
  :local:

Maintenance
===========

Modules are maintained by the owners of the collection with which they ship.

Core
----

Core Maintained modules are maintained by the Ansible Engineering Team.  These modules are integral
to the basic foundations of the Ansible distribution.  They are shipped with Ansible itself.

Network
-------

The Ansible Content Team maintains a set of collections for customers of Ansible.


Partner Vendors
---------------

Individual vendors maintain a large number of modules in collections hosted on Ansible Automation
Hub.  These collections replace the `List of Ansible Certified Modules <https://access.redhat.com/articles/3642632>`_ as the canonical list of what vendors are maintaining which content.

Ansible Community
-----------------

Modules in the Ansible Community collection are maintained by a group of volunteers who are committed to providing modules that make Ansible usable in a large number of different situations.

Issue Reporting
===============

If you believe you have found a bug in a module and are already running the latest stable or development version of Ansible, first look at the `issue tracker in the Ansible repo <https://github.com/ansible/ansible/issues>`_ to see if an issue has already been filed. If not, please file one.

Should you have a question rather than a bug report, inquiries are welcome on the `ansible-project Google group <https://groups.google.com/forum/#%21forum/ansible-project>`_ or on Ansible's "#ansible" channel, located on irc.freenode.net.

For development-oriented topics, use the `ansible-devel Google group <https://groups.google.com/forum/#%21forum/ansible-devel>`_ or Ansible's #ansible and #ansible-devel channels, located on irc.freenode.net. You should also read the :ref:`Community Guide <ansible_community_guide>`, :ref:`Testing Ansible <developing_testing>`, and the :ref:`Developer Guide <developer_guide>`.

The modules are hosted on GitHub in a subdirectory of the `Ansible <https://github.com/ansible/ansible/tree/devel/lib/ansible/modules>`_ repo.

NOTE: If you have a Red Hat Ansible Automation product subscription, please follow the standard issue reporting process via the `Red Hat Customer Portal <https://access.redhat.com/>`_.

Support
=======

For more information on how included Ansible modules are supported by Red Hat,
please refer to the following `knowledge base article <https://access.redhat.com/articles/3166901>`_ as well as other resources on the `Red Hat Customer Portal. <https://access.redhat.com/>`_

.. seealso::

   :ref:`Module index<modules_by_category>`
       A complete list of all available modules.
   :ref:`intro_adhoc`
       Examples of using modules in /usr/bin/ansible
   :ref:`working_with_playbooks`
       Examples of using modules with /usr/bin/ansible-playbook
   :ref:`developing_modules`
       How to write your own modules
   `Mailing List <https://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
