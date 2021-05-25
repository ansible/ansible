:orphan:

.. _implicit_localhost:

Implicit 'localhost'
====================

When you try to reference a ``localhost`` and you don't have it defined in inventory, Ansible will create an implicit one for you.::

    - hosts: all
      tasks:
        - name: check that i have log file for all hosts on my local machine
          stat: path=/var/log/hosts/{{inventory_hostname}}.log
          delegate_to: localhost

In a case like this (or ``local_action``) when Ansible needs to contact a 'localhost' but you did not supply one, we create one for you. This host is defined with specific connection variables equivalent to this in an inventory::

   ...

   hosts:
     localhost:
      vars:
        ansible_connection: local
        ansible_python_interpreter: "{{ansible_playbook_python}}"

This ensures that the proper connection and Python are used to execute your tasks locally.
You can override the built-in implicit version by creating a ``localhost`` host entry in your inventory. At that point, all implicit behaviors are ignored; the ``localhost`` in inventory is treated just like any other host. Group and host vars will apply, including connection vars, which includes the ``ansible_python_interpreter`` setting. This will also affect ``delegate_to: localhost`` and ``local_action``, the latter being an alias to the former.

.. note::
  - This host is not targetable via any group, however it will use vars from ``host_vars`` and from the 'all' group.
  - Implicit localhost does not appear in the ``hostvars`` magic variable unless demanded, such as by ``"{{ hostvars['localhost'] }}"``.
  - The ``inventory_file`` and ``inventory_dir`` magic variables are not available for the implicit localhost as they are dependent on **each inventory host**.
  - This implicit host also gets triggered by using ``127.0.0.1`` or ``::1`` as they are the IPv4 and IPv6 representations of 'localhost'.
  - Even though there are many ways to create it, there will only ever be ONE implicit localhost, using the name first used to create it.
  - Having ``connection: local`` does NOT trigger an implicit localhost, you are just changing the connection for the ``inventory_hostname``.
