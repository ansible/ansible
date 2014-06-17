Windows Support
===============

.. contents:: Topics

.. _windows_how_does_it_work:

Windows: How Does It Work
``````````````````````````

Ansible manages Linux/Unix machines using SSH by default.  

Starting in version 1.7, Ansible also contains support for managing Windows machines.

Ansible will still run from a Linux guest, and uses the "winrm" Python module to talk to remote hosts.

.. _windows_installing:

Installing
``````````

On a Linux control machine::

   pip install http://github.com/diyan/pywinrm/archive/master.zip#egg=pywinrm

.. _windows_inventory:

Inventory
`````````

Ansible's windows support will rely on a few standard variables to indicate the username, password, and connection type (windows)
of the remote hosts::


    [windows]
    winserver1.example.com
    winserver2.example.com 

In group_vars/windows.yml, define the following inventory variables::

    ansible-vault edit group_vars/windows.yml

    ansible_ssh_user: Administrator 
    ansible_ssh_pass: SekritPasswordGoesHere
    ansible_ssh_port: 5986
    ansible_connection: winrm
    
When using your playbook, don't forget to specify --ask-vault-pass to provide the password to unlock the file.

Test your configuration like so, by trying to contact your Windows nodes.  Note this is not an ICMP ping, but tests the Ansible
communication channel that leverages Windows remoting::

    ansible windows [-i inventory] -m ping --ask-vault-pass

.. _windows_what_modules_are_available:

What modules are available
``````````````````````````

Most of the Ansible modules in core Ansible are written for a combination of Linux/Unix machines and arbitrary web services, though there are various
Windows modules as listed in the "windows" subcategory of the Ansible module index.  

Browse this index to see what is available.

In many cases, it may not be neccessary to even write or use an Ansible module.

In particular, the "win_script" module can be used to run arbitrary powershell scripts, allowing Windows administrators familiar with powershell a very
native way to do things, as in the following playbook:

    - hosts: windows
      tasks:
        - win_script: foo.ps1 --argument --other-argument

.. _windows_developers_developers_developers:

Developers: Supported modules and how it works
``````````````````````````````````````````````

Developing ansible modules are covered in a later section, with a focus on Linux/Unix.

For Windows, ansible modules are implemented in Powershell.  Skim the module development chapters before proceeding.

Windows modules live in a "windows/" subfolder in the Ansible "library/" subtree.  For example, if a module is named
"library/windows/win_ping", there will be embedded documentation in the "win_ping" file, and the actual powershell code will
live in a "win_ping.ps1" file.

Modules (ps1 files) should start as follows::

    #!powershell
    # WANT_JSON
    # POWERSHELL_COMMON

    # <license>
    # code goes here, reading in stdin as JSON and outputting JSON

The above magic is neccessary to tell Ansible to mix in some common code and also know how to push modules out.

Taking a look at the sources for win_ping and the equivalent will make it easier to understand how things work by following
the existing patterns.

Additional modules may be submitted as pull requests to github.

.. _windows_system_prep:

System Prep
```````````

In order for Ansible to manage your windows machines you will have to enable powershell remoting first::

   How to do it goes here

.. _windows_and_linux_control_machine:

You Must Have a Linux Control Machine
`````````````````````````````````````

Note running Ansible from a Windows control machine is NOT a goal of the project.  Refrain from asking for this feature,
as it limits what technologies, features, and code we can use in the main project in the future.  A Linux control machine
will be required to manage Windows hosts.
  
Cygwin is not supported, so please do not ask questions about Ansible running from Cygwin.

.. seealso::

   :doc:`developing_modules`
       How to write modules
   :doc:`playbooks`
       Learning ansible's configuration management language
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel

