Vars Plugins
------------

They inject additional variable data into ansible runs that did not come from an inventory source, playbook, or command line.
The :doc:`host_group_vars vars/host_group_vars` plugin shipped with Ansible provides reading variables from :ref:`host_vars` and :ref:`group_vars`.


Enabling Vars Plugins
+++++++++++++++++++++

You can activate a custom vars plugins by either dropping it into a `vars_plugins` directory adjacent to your play or inside a role
or by putting it in one of the directory sources configured in :doc:`ansible.cfg ../config`.


You can use ``ansible-doc -t vars -l`` to see the list of available plugins,
use ``ansible-doc -t vars <plugin name>`` to see specific documents and examples.


.. toctree:: :maxdepth: 1
    :glob:

    vars/*

.. seealso::

   :doc:`action`
       Ansible Action plugins
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
   `User Mailing List <http://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
