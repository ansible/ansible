******************
Networking Support
******************


.. contents:: Topics

.. _working_with_networking_devices:

Working with Networking Devices
====================================

Starting with Ansible version 2.1, you can now use the familiar Ansible models of playbook authoring and module development to manage heterogenous networking devices.  Ansible supports a growing number of network devices using both CLI over SSH and API (when available) transports.

.. _networking_installation:

Network Automation Installation
================================================

* Install the `latest Ansible release <http://docs.ansible.com/ansible/intro_installation.html>`_.

.. _networking_module_index:

Available Networking Modules
====================================

Most standard Ansible modules are designed to work with Linux/Unix or Windows machines and will not work with networking devices. Some modules (including "slurp", "raw", and "setup") are platform-agnostic and will work with networking devices.

To see what modules are available for networking devices, please browse the `"networking" section of the Ansible module index <https://docs.ansible.com/ansible/list_of_network_modules.html#>`_.


Persistent Connections
======================
Before diving into the technical detail of how to troubleshoot it can be useful to understand how Ansible communicates with the remote network device.

As of version 2.3, Ansible includes support for `persistent connections`. Persistent connections are useful for playbooks with multiple tasks that require multiple SSH connections. In previous releases, these SSH connections had to be established and destroyed each time a task was run, which was inefficient. Persistent connections allows an SSH connection to stay active across multiple Ansible tasks and plays, elimintating the need to spend time establishing and destroying the connection. This is done by keeping a Linux socket open, via a daemon process called ``ansible-connection``.

Persistent Connection had been enable for the following groups of modules:

 * dellos6
 * dellos9
 * dellos10
 * eos
 * ios
 * iosxr
 * junos
 * nxos (some)
 * vyos
 * sros (from 2.3 RC2)


.. notes: Future support

   The list of network platforms that support Persistent Connection will grow with each release.

.. notes: Persistent Connections is for `cli` (ssh), not for API transports.

   The Persistent Connection work added in Ansible 2.3 only applies to `cli transport`. It doesn't apply to APIs such as eos's eapi, or nxos's nxapi. Starting with Ansible 2.3, using CLI should be faster in most cases than using the API transport. Using CLI also allows you be benefit from using SSH Keys.

Playbook Structure from 2.1 to 2.3
==================================

Ansible 2.3 makes it easier to write playbooks by simplifying how connections are handled. This means that you no longer need to define the connection details in every task (via ``host:`` or ``provider:``); instead you can utilize ssh keys and write shortened playbooks.


Ansible 2.3 maintains backwards with playbooks created in Ansible 2.2, so you are not forced to upgrade your playbooks when you upgrade to Ansible 2.3.

Why is this changing
--------------------

As of Ansible 2.FIXME specifying credentials directly under the task or under provider will no longer be supported in network modules. This is to make the network modules work in the same way as normal Linux and Windows modules. This has the following advantages:

* Easier to understand
* Consistent with the rest of Ansible
* Simplified module code
* Fewer code paths doing similar things


Recap of different connection methods
-------------------------------------
This section demonstrates the different ways to write connect to network devices.

The following examples are all equivalent.

.. note: Which playbook style should I use?

   If you are starting Networking in Ansible 2.3 we recommend using FIXME name for 2.3 style FIXME. As that is the format that will be supported long term.
   Where ever possible we suggest using `cli` with SSH keys.

Playbook with provider dict
```````````````````````````

**Version:** Ansible 2.2 - 2.3

``group_vars/eos.yml``

.. code-block:: yaml

   ---
   cli:
     host: "{{ ansible_host }}"
     username: "{{ eos_cli_user | default('admin') }}"
     password: "{{ eos_cli_pass | default('admin') }}"
     transport: cli


.. code-block:: yaml

   - name: Gather facts
     - eos_facts:
         gather_subset: all
         provider: "{{ cli }}"


Note, that if you use this form in Ansible 2.3 you will get the following deprecation messages. This is a reminder that you need to move to the new 2.3 connection framework, or use ``provider:``.

.. code-block:: yaml

   [WARNING]: argument username has been deprecated and will be removed in a future version
   [WARNING]: argument host has been deprecated and will be removed in a future version
   [WARNING]: argument password has been deprecated and will be removed in a future version

2.2 Playbook with provider
``````````````````````````

**Version:** Ansible 2.2 - 2.3

.. code-block:: yaml

   - name: Gather facts
     - eos_facts:
         gather_subset: all
         provider:
           username: myuser
           password: "{{ networkpassword }}"
           transport: cli
           host: "{{ ansible_host }}"

2.3 Playbook
````````````

**Version:** Ansible 2.3


.. code-block:: yaml

   - name: Gather facts
     - eos_facts:
         gather_subset: all


By default eos and nxos module use cli (ssh). If you wish to use the API, use the ``transport:`` option. For example:

.. code-block:: yaml

   - name: Gather facts
     - eos_facts:
         gather_subset: all
         transport: eapi

For details on how how to pass in authentication details, see `Specifying Credentials`.






















The rest of this file needs review


.. _understanding_provider_arguments:

Connecting to Networking Devices
================================================

All core networking modules implement a *provider* argument, which is a collection of arguments used to define the characteristics of how to connect to the device.  This section will assist in understanding how the provider argument is used.


Each core network module supports an underlying operating system and transport.  The operating system is a one-to-one match with the module, and the transport maintains a one-to-many relationship to the operating system as appropriate. Some network operating systems only have a single transport option.


Each core network module supports some basic arguments for configuring the transport:

* host - defines the hostname or IP address of the remote host
* port - defines the port to connect to
* username - defines the username to use to authenticate the connection
* password - defines the password to use to authenticate the connection
* transport - defines the type of connection transport to build
* authorize - enables privilege escalation for devices that require it
* auth_pass  - defines the password, if needed, for privilege escalation

Individual modules can set defaults for these arguments to common values that match device default configuration settings.  For instance, the default value for transport is universally 'cli'.  Some modules support other values such as EOS (eapi) and NXOS (nxapi), while some only support 'cli'.  All arguments are fully documented for each module.

By allowing individual tasks to set the transport arguments independently, modules that use different transport mechanisms and authentication credentials can be combined as necessary.

One downside to this approach is that every task needs to include the required arguments.  This is where the provider argument comes into play. The provider argument accepts keyword arguments and passes them through to the task to assign connection and authentication parameters.

The following two config modules are essentially identical (using nxos_config) as an example but it applies to all core networking modules::


    ---
    nxos_config:
       src: config.j2
       host: "{{ inventory_hostname }}"
       username: "{{ ansible_ssh_user }}"
       password: "{{ ansible_ssh_pass }}"
       transport: cli

    ---
    vars:
       cli:
          host: "{{ inventory_hostname }}"
          username: "{{ ansible_ssh_user }}"
          password: "{{ ansible_ssh_pass }} "
          transport: cli


    nxos_config:
       src: config.j2
       provider: "{{ cli }}"

Given the above two examples that are equivalent, the arguments can also be used to establish precedence and defaults.  Consider the following example::

    ---
    vars:
        cli:
           host: "{{ inventory_hostname }}"
           username: operator
           password: secret
           transport: cli

    tasks:
    - nxos_config:
       src: config.j2
       provider: "{{ cli }}"
       username: admin
       password: admin


In this example, the values of admin for username and admin for password will override the values of operator in cli['username'] and secret in cli['password'])

This is true for all values in the provider including transport.  So you could have a singular task that is now supported over CLI or NXAPI (assuming the configuration is value). ::


    ---
    vars:
        cli:
           host: "{{ inventory_hostname }}"
           username: operator
           password: secret
           transport: cli

    tasks:
      - nxos_config:
          src: config.j2
          provider: "{{ cli }}"
          transport: nxapi

If all values are provided via the provider argument, the rules for requirements are still honored for the module.   For instance, take the following scenario::

    ---
    vars:
      conn:
         password: cisco_pass
         transport: cli

    tasks:
    - nxos_config:
      src: config.j2
      provider: "{{ conn }}"

Running the above task will cause an error to be generated with a message that required parameters are missing.  ::

    "msg": "missing required arguments: username,host"

Overall, this provides a very granular level of control over how credentials are used with modules.  It provides the playbook designer maximum control for changing context during a playbook run as needed.

.. _networking_environment_variables:

Networking Environment Variables
====================================

The following environment variables are available to Ansible networking modules:

username ANSIBLE_NET_USERNAME
password ANSIBLE_NET_PASSWORD
ssh_keyfile ANSIBLE_NET_SSH_KEYFILE
authorize ANSIBLE_NET_AUTHORIZE
auth_pass ANSIBLE_NET_AUTH_PASS

Variables are evaulated in the following order, listed from lowest to highest priority:

* Default
* Environment
* Provider
* Task arguments

.. _networking_module_conditionals:

Conditionals in Networking Modules
====================================

Ansible allows you to use conditionals to control the flow of your playbooks. Ansible networking command modules use the following unique conditional statements.

* eq - Equal
* neq - Not equal
* gt - Greater than
* ge - Greater than or equal
* lt - Less than
* le - Less than or equal
* contains - Object contains specified item


Conditional statements evalute the results from the commands that are
executed remotely on the device.  Once the task executes the command
set, the waitfor argument can be used to evalute the results before
returning control to the Ansible playbook.

For example::

    ---
    - name: wait for interface to be admin enabled
      eos_command:
          commands:
              - show interface Ethernet4 | json
          waitfor:
              - "result[0].interfaces.Ethernet4.interfaceStatus eq connected"

In the above example task, the command :code:`show interface Ethernet4 | json`
is executed on the remote device and the results are evaluated.  If
the path
:code:`(result[0].interfaces.Ethernet4.interfaceStatus)` is not equal to
"connected", then the command is retried.  This process continues
until either the condition is satisfied or the number of retries has
expired (by default, this is 10 retries at 1 second intervals).

The commands module can also evaluate more than one set of command
results in an interface.  For instance::

    ---
    - name: wait for interfaces to be admin enabled
      eos_command:
          commands:
              - show interface Ethernet4 | json
              - show interface Ethernet5 | json
          waitfor:
              - "result[0].interfaces.Ethernet4.interfaceStatus eq connected"
              - "result[1].interfaces.Ethernet4.interfaceStatus eq connected"

In the above example, two commands are executed on the
remote device, and the results are evaluated.  By specifying the result
index value (0 or 1), the correct result output is checked against the
conditional.

The waitfor argument must always start with result and then the
command index in [], where 0 is the first command in the commands list,
1 is the second command, 2 is the third and so on.

