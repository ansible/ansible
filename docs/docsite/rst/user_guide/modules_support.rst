.. _modules_support:

Module Maintenance & Support
----------------------------

.. toctree:: :maxdepth: 1

To help identify maintainers and understand how the included modules are officially supported, each module now has associated metadata that provides additional clarity for maintenance and support.

Core
````

:ref:`Core Maintained<core_supported>` modules are maintained by the Ansible Engineering Team.
These modules are integral to the basic foundations of the Ansible distribution.

Network
```````

:ref:`Network Maintained<network_supported>` modules are are maintained by the Ansible Network Team. Please note there are additional networking modules that are categorized as Certified or Community not maintained by Ansible.


Certified
`````````

Certified modules are part of a future planned program currently in development.

Community
`````````

:ref:`Community Maintained<community_supported>` modules are submitted and maintained by the Ansible community.  These modules are not maintained by Ansible, and are included as a convenience.

Issue Reporting
```````````````

If you believe you have found a bug in a module and are already running the latest stable or development version of Ansible, first look at the `issue tracker in the Ansible repo <https://github.com/ansible/ansible/issues>`_ to see if an issue has already been filed. If not, please file one.

Should you have a question rather than a bug report, inquiries are welcome on the `ansible-project Google group <https://groups.google.com/forum/#%21forum/ansible-project>`_ or on Ansible's "#ansible" channel, located on irc.freenode.net.

For development-oriented topics, use the `ansible-devel Google group <https://groups.google.com/forum/#%21forum/ansible-devel>`_ or Ansible's #ansible and #ansible-devel channels, located on irc.freenode.net. You should also read :doc:`Community Information & Contributing <../community/index>`, :doc:`Testing Ansible <../dev_guide/testing>`, and :doc:`Developing Modules <../dev_guide/developing_modules>`.

The modules are hosted on GitHub in a subdirectory of the `Ansible <https://github.com/ansible/ansible/tree/devel/lib/ansible/modules>`_ repo.

NOTE: If you have a Red Hat Ansible Engine product subscription, please follow the standard issue reporting process via the Red Hat Customer Portal.

Support
```````

For more information on how included Ansible modules are supported by Red Hat,
please refer to the following `knowledgebase article <https://access.redhat.com/articles/3166901>`_ as well as other resources on the `Red Hat Customer Portal. <https://access.redhat.com/>`_

.. seealso::

   :doc:`../modules/modules_by_category`
       A complete list of all available modules.
   :doc:`intro_adhoc`
       Examples of using modules in /usr/bin/ansible
   :doc:`playbooks`
       Examples of using modules with /usr/bin/ansible-playbook
   :doc:`../dev_guide/developing_modules`
       How to write your own modules
   :doc:`../dev_guide/developing_api`
       Examples of using modules with the Python API
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
