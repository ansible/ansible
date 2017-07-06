.. _porting_2.4_guide:

*************************
Ansible 2.4 Porting Guide
*************************

This section discusses the behavioral changes between Ansible 2.3 and Ansible 2.4.

It is intended to assist in updating your playbooks, plugins and other parts of your Ansible infrastructure so they will work with this version of Ansible.


We suggest you read this page along with `Ansible Changelog <https://github.com/ansible/ansible/blob/devel/CHANGELOG.md#2.4>`_ to understand what updates you may need to make.

This document is part of a collection on porting. The complete list of porting guides can be found at :ref:`porting_guides <Porting Guides>`.

.. contents:: Topics

Playbook
========


Deprecated
==========



Use of multiple tags
--------------------

Specifying ``--tags`` (or ``--skip-tags``) multiple times on the command line currently leads to the last one overriding all the previous ones. This behavior is deprecated. In the future, if you specify --tags multiple times the tags will be merged together. From now on, using ``--tags`` multiple times on one command line will emit a deprecation warning. Setting the ``merge_multiple_cli_tags`` option to True in the ``ansible.cfg`` file will enable the new behavior.

In 2.4, the default has change to merge the tags. You can enable the old overwriting behavior via the config option.

In 2.5, multiple ``--tags`` options will be merged with no way to go back to the old behavior.

.. Nothing currently in this section so commented out 
   Placeholder left to keep consistent formatting with porting_guide_2.3.rst 

   Other caveats
   -------------

   Modules
   =======

   Major changes in popular modules are detailed here

   Modules removed
   ---------------
   
   The following modules no longer exist:
   
   * None
   
   Deprecation notices
   -------------------
   
   The following modules will be removed in Ansible 2.6. Please update update your    playbooks accordingly.
   
   * :ref:`fixme <fixme>`
   
   Noteworthy module changes
   -------------------------
      
   Plugins
   =======
   
   Porting custom scripts
   ======================



Networking
==========

There have been a number of changes to how Networking Modules operate.

Playbooks should still use ``connection: local``.

The following changes apply to:

* TBD List modules that have been ported to new framework in 2.4 - Link back to 2.3 porting guide
