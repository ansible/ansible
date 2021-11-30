.. _test_plugins:

Test plugins
=============

.. contents::
   :local:
   :depth: 2

Test plugins evaluate template expressions and return True or False. With test plugins you can create :ref:`conditionals <playbooks_conditionals>` to implement the logic of your tasks, blocks, plays, playbooks, and roles. Ansible uses the `standard tests `_ shipped as part of Jinja, and adds some specialized test plugins. You can :ref:`create custom Ansible test plugins <developing_test_plugins>`.

.. _standard tests: https://jinja.palletsprojects.com/en/latest/templates/#builtin-tests

.. _enabling_test:

Enabling test plugins
----------------------

You can add a custom test plugin by dropping it into a ``test_plugins`` directory adjacent to your play, inside a role, or by putting it in one of the test plugin directory sources configured in :ref:`ansible.cfg <ansible_configuration_settings>`.


.. _using_test:

Using test plugins
-------------------

The User Guide offers detailed documentation on :ref:`using test plugins <playbooks_tests>`.

.. seealso::

   :ref:`about_playbooks`
       An introduction to playbooks
   :ref:`playbooks_tests`
       Using tests
   :ref:`playbooks_conditionals`
       Using conditional statements
   :ref:`filter_plugins`
       Filter plugins
   :ref:`playbooks_filters`
       Using filters
   :ref:`lookup_plugins`
       Lookup plugins
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   :ref:`communication_irc`
       How to join Ansible chat channels
