.. _module_plugins:

Modules
=======

.. contents::
   :local:
   :depth: 2

Modules are the main building blocks of Ansible playbooks. Although we do not generally speak of "module plugins", a module is a type of plugin. For a developer-focused description of the differences between modules and other plugins, see :ref:`modules_vs_plugins`.

.. _enabling_modules:

Enabling modules
----------------

You can enable a custom module by dropping it into one of these locations:

* any directory added to the ``ANSIBLE_LIBRARY`` environment variable (``$ANSIBLE_LIBRARY`` takes a colon-separated list like ``$PATH``)
* ``~/.ansible/plugins/modules/``
* ``/usr/share/ansible/plugins/modules/``

For more information on using local custom modules, see :ref:`local_modules`. 

.. _using_modules:

Using modules
-------------

For information on using modules in ad hoc tasks, see :ref:`intro_adhoc`. For information on using modules in playbooks, see :ref:`playbooks_intro`.

.. seealso::

   :ref:`about_playbooks`
       An introduction to playbooks
   :ref:`developing_modules_general`
       An introduction to creating Ansible modules
   :ref:`developing_collections`
       An guide to creating Ansible collections
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.libera.chat <https://libera.chat/>`_
       #ansible-devel IRC chat channel
