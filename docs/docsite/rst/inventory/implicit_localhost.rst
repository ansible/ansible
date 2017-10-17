.. _implicit_localhost:

Implicit 'localhost'
====================

When you try to use a 'localhost' and you don't have it defined in inventory, Ansible will create an implicit one for you.::

    - hosts: all
      tasks:
        - name: check that i have log file for all hosts on my local machine
          stat: path=/var/log/hosts/{{inventory_hostname}}.log
          delegate_to: localhost

In a case like this (or ``local_action``) Ansible needs to contact a 'localhost' but you did not supply one,
since it is common enough and we 'should know' the settings, we create one for you.
This host is defined with specific connection vars equivalent to this in an inventory::

   ...

   hosts:
     localhost:
      vars:
        ansible_connection: local
        ansible_python_interpreter: "{{ansible_playbook_python}}"

This ensures that the proper connection and Python are used to execute your tasks locally,
you can of course override this and use any specific settings you want by specifying a 'localhost' type host in your inventory.
At that point you are responsible for using the correct connection and/or python for this host, this affects ``delegate_to`` and ``local_action``.

.. note::
  - This host is not part of any group nor will use any group_vars unless explicitly added, however it will use host_vars/.
  - This implicit host also gets triggered by using ``127.0.0.1`` or ``::1`` as they are the IPv4 and IPv6 representations of 'localhost'.
  - Even though there are many ways to create it, there will only ever be ONE implicit localhost, using the name first used to create it.
  - Having ``connection: local`` does NOT trigger an implicit localhost, you are just changing the connection for the inventory_hostname.
