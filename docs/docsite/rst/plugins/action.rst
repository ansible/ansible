Action Plugins
---------------

Action plugins act in conjunction with :doc:`modules <../modules>` to execute the actions required by playbook tasks.
They usually execute automatically in the background doing prerequisite work before modules execute.

The 'normal' action plugin is used for modules that do not already have an action plugin.

.. _enabling_action:

Enabling Action Plugins
+++++++++++++++++++++++

You can enable a custom action plugin by either dropping it into the ``action_plugins`` directory adjacent to your play, inside a role, or by putting it in one of the action plugin directory sources configured in :doc:`ansible.cfg <../config>`.

.. _using_action:

Using Action Plugins
+++++++++++++++++++++

No need to do anything, any module that has an associated action plugin will have it executed by default,
you should see a note in the module documentation to this effect.


.. seealso::

   :doc:`cache`
       Ansible Cache plugins
   :doc:`callback`
       Ansible callback plugins
   :doc:`connection`
       Ansible connection plugins
   :doc:`inventory`
       Ansible inventory plugins
   :doc:`shell`
       Ansible Shell plugins
   :doc:`strategy`
       Ansible Strategy plugins
   :doc:`vars`
       Ansible Vars plugins
   `User Mailing List <http://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
