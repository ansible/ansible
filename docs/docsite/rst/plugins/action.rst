Action Plugins
---------------

These plugins act in conjunction with :doc:`modules ../modules` to execute the actions required by playbook tasks.
They mostly execute automatically in the background doing prerequisite work for the modules of the same to be able to execute.

The 'normal' action plugin takes care of modules that do not already have an action plugin.

Enabling Vars Plugins
+++++++++++++++++++++

You can activate a custom action plugins by either dropping it into a `action_plugins` directory adjacent to your play or inside a role
or by putting it in one of the action plugin directory sources configured in `ansible.cfg`.



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
