.. _nagios:

nagios
``````

Perform common tasks in Nagios related to downtime and notifications.

The Nagios module has two basic functions: scheduling downtime and
toggling alerts for services or hosts.

The following parameters are common to all *actions* in the nagios
module:

+---------------+----------+----------------------------------+------------------------------------------------------------------+
| parameter     | required |           default                | comments                                                         |
+===============+==========+==================================+==================================================================+
| action        | yes      |                                  | one of: 'downtime', 'enable_alerts'/'disable_alerts', or         |
|               |          |                                  | 'silence'/'unsilence'                                            |
+---------------+----------+----------------------------------+------------------------------------------------------------------+
| host          | yes      |                                  | host to operate on in nagios                                     |
+---------------+----------+----------------------------------+------------------------------------------------------------------+
| cmdfile       | no       | /var/spool/nagios/cmd/nagios.cmd | path to the nagios *command file* (FIFO pipe)                    |
+---------------+----------+----------------------------------+------------------------------------------------------------------+

The following parameters may be used with the **downtime** action:

+---------------+----------+----------------------------------+------------------------------------------------------------------+
| parameter     | required |           default                | comments                                                         |
+===============+==========+==================================+==================================================================+
| author        | no       | Ansible                          | author to leave downtime comments as                             |
+---------------+----------+----------------------------------+------------------------------------------------------------------+
| minutes       | no       | 30                               | minutes to schedule downtime for                                 |
+---------------+----------+----------------------------------+------------------------------------------------------------------+
| services      | no       |                                  | what to manage downtime/alerts for. separate multiple services   |
|               |          |                                  | with commas.                                                     |
|               |          |                                  | **service** is as an alias for **services**                      |
+---------------+----------+----------------------------------+------------------------------------------------------------------+

The following parameter must be used with the **enable_alerts** and **disable_alerts** actions:

+---------------+----------+----------------------------------+------------------------------------------------------------------+
| parameter     | required |           default                | comments                                                         |
+===============+==========+==================================+==================================================================+
| services      | no       |                                  | what to manage downtime/alerts for. separate multiple services   |
|               |          |                                  | with commas.                                                     |
|               |          |                                  | **service** is as an alias for **services**                      |
+---------------+----------+----------------------------------+------------------------------------------------------------------+

.. note::
   The **silence** and **unsilence** actions have no additional
   parameters that may be used with them.


All actions require the **host** parameter to be given explicitly. In
playbooks you can use the ``$inventory_hostname`` variable to refer to
the host the playbook is currently running on.

You can specify multiple services at once by separating them with
commas, .e.g., ``services=httpd,nfs,puppet``.

When specifying what service to handle there is a special keyword,
**host**, which will handle alerts/downtime for the **host itself**,
e.g., ``service=host``. This keyword may *not* be given with other
services at the same time. *Handling alerts/downtime for a host does
not affect alerts/downtime for any of the services running on it.*


Examples of Scheduling Downtime in :doc:`playbooks`::

    ---
    - hosts: webservers
      user: root
      tasks:
        - name: set 30 minutes of apache downtime
          action: nagios action=downtime minutes=15 service=httpd host=$inventory_hostname
          delegate_to: nagios.example.com

        - name: schedule an hour of HOST downtime
          action: nagios action=downtime minutes=60 service=host host=$inventory_hostname
          delegate_to: nagios.example.com

        # Use the default of 30 minutes
        # Schedule downtime for three services at once
        - name: schedule downtime for a few services
          action: nagios action=downtime services=frob,foobar,qeuz host=$inventory_hostname
          delegate_to: nagios.example.com

And from the command line:

.. code-block:: bash

   $ ansible nagios.example.com -m nagios -a "action=downtime minutes=15 service=httpd host=server01.example.com"
   $ ansible nagios.example.com -m nagios -a "action=downtime minutes=60 service=host host=server01.example.com"
   $ ansible nagios.example.com -m nagios -a "action=downtime services=frob,foobar,qeuz host=server01.example.com"

Examples of handling specific host/service alerts in :doc:`playbooks`::

    ---
    - hosts: webservers
      user: root
      tasks:
        - name: enable SMART disk alerts
          action: nagios action=enable_alerts service=smart host=$inventory_hostname
          delegate_to: nagios.example.com

        # Note that you can disable multiple at once
        - name: disable httpd alerts
          action: nagios action=disable_alerts service=httpd,nfs host=$inventory_hostname
          delegate_to: nagios.example.com

        # And disabling HOST alerts
        - name: disable HOST alerts
          action: nagios action=disable_alerts service=host host=$inventory_hostname
          delegate_to: nagios.example.com

And from the command line:

.. code-block:: bash

   $ ansible nagios.example.com -m nagios -a "action=enable_alerts service=smart host=server01.example.com"
   $ ansible nagios.example.com -m nagios -a "action=disable_alerts service=httpd,nfs host=server01.example.com"
   $ ansible nagios.example.com -m nagios -a "action=disable_alerts service=host host=server01.example.com"

Examples of Silencing all host/service alerts in :doc:`playbooks`::

    ---
    - hosts: webservers
      user: root
      tasks:
        - name: silence ALL alerts
          action: nagios action=silence host=$inventory_hostname
          delegate_to: nagios.example.com

        - name: unsilence all alerts
          action: nagios action=unsilence host=$inventory_hostname
          delegate_to: nagios.example.com

And from the command line:

.. code-block:: bash

   $ ansible nagios.example.com -m nagios -a "action=silence host=server01.example.com"
   $ ansible nagios.example.com -m nagios -a "action=unsilence host=server01.example.com"


**Optional Configuration**

If your nagios **cmdfile** is not ``/var/spool/nagios/cmd/nagios.cmd``
you can configure ansible (on your nagios server) to use the correct
one by making a file called ``/etc/ansible/modules/nagios.conf`` that
looks like this:

.. code-block:: ini

    [main]
    cmdfile = /path/to/your/nagios.cmd

Or, use the **cmdfile** parameter to set it explicitly.


**Troubleshooting Tips**

The nagios module may not operate for you out of the box. The most
likely problem is with your **cmdfile** permissions/paths. You will
receive this error if that is the case::

    {"msg": "unable to write to nagios command file", "failed": true, "cmdfile": "/var/spool/nagios/cmd/nagios.cmd"}

Steps to correct this:

1. Ensure you are running the nagios module as a user who has
   **write** permissions to the **cmdfile**.

2. Ensure you have **cmdfile** set correctly.
