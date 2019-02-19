.. _process_plugins:

Process Model Plugins
=====================

.. contents::
   :local:
   :depth: 2

Process plugins control the way Ansible creates workers to run tasks on hosts. Currently, the specified process model is global and cannot be changed once Ansible starts.

By default, Ansible ships with two process models: :ref:`forking<forking_process>` and :ref:`threading<threading_process>`.

.. _adding_process_models:

Adding Process Model Plugins
----------------------------

You can extend Ansible to support other process models by dropping a custom plugin into the ``process_plugins`` directory.

.. _using_process_models:

Using Process Model Plugins
---------------------------

You can set the process model plugin globally via :ref:`configuration settings<ansible_configuration_settings>`.

.. _process_model_plugin_list:

Plugin List
-----------

You can use ``ansible-doc -t process -l`` to see the list of available plugins.
Use ``ansible-doc -t process <plugin name>`` to see detailed documentation and examples.


.. toctree:: :maxdepth: 1
    :glob:

    process/*


.. seealso::

   :ref:`Working with Playbooks<working_with_playbooks>`
       An introduction to playbooks
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
