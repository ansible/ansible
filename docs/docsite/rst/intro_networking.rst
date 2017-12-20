Networking Support
==================

.. contents:: Topics

.. _working_with_networking_devices:

Working with Networking Devices
```````````````````````````````

You can use the familiar Ansible models of playbook authoring and module development to manage heterogenous networking devices.  Ansible supports a growing number of network devices using both CLI over SSH and API (when available) transports.

.. _networking_installation:

Network Automation Installation
```````````````````````````````

* Install the `latest Ansible release <http://docs.ansible.com/ansible/intro_installation.html>`_.

.. _networking_module_index:

Available Networking Modules
````````````````````````````

Most standard Ansible modules are designed to work with Linux/Unix or Windows machines and will not work with networking devices. Some modules (including "slurp", "raw", and "setup") are platform-agnostic and will work with networking devices.

To see what modules are available for networking devices, please browse the `"networking" section of the Ansible module index <https://docs.ansible.com/ansible/list_of_network_modules.html#>`_.

.. _understanding_provider_arguments:

Connecting to Networking Devices
````````````````````````````````

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
````````````````````````````````

The following environment variables are available to Ansible networking modules:

username :envvar:`ANSIBLE_NET_USERNAME`

password :envvar:`ANSIBLE_NET_PASSWORD`

ssh_keyfile :envvar:`ANSIBLE_NET_SSH_KEYFILE`

authorize :envvar:`ANSIBLE_NET_AUTHORIZE`

auth_pass :envvar:`ANSIBLE_NET_AUTH_PASS`

Variables are evaulated in the following order, listed from lowest to highest priority:

* Default
* Environment
* Provider
* Task arguments

