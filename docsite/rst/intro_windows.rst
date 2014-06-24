Windows Support
===============

.. contents:: Topics

.. _windows_how_does_it_work:

Windows: How Does It Work
`````````````````````````

As you may have already read, Ansible manages Linux/Unix machines using SSH by default.  

Starting in version 1.7, Ansible also contains support for managing Windows machines.  This uses
native powershell remoting, rather than SSH.

Ansible will still be run from a Linux control machine, and uses the "winrm" Python module to talk to remote hosts.

No additional software needs to be installed on the remote machines for Ansible to manage them, it still maintains the agentless properties that make it popular on Linux/Unix.

Note that it is expected you have a basic understanding of Ansible prior to jumping into this section, so if you haven't written a Linux playbook first, it might be worthwhile to dig in there first.

.. _windows_installing:

Installing on the Control Machine
``````````````````````````````````

On a Linux control machine::

   pip install http://github.com/diyan/pywinrm/archive/master.zip#egg=pywinrm

.. _windows_inventory:

Inventory
`````````

Ansible's windows support relies on a few standard variables to indicate the username, password, and connection type (windows) of the remote hosts.  These variables are most easily set up in inventory.  This is used instead of SSH-keys or passwords as normally fed into Ansible::

    [windows]
    winserver1.example.com
    winserver2.example.com

In group_vars/windows.yml, define the following inventory variables::

    # it is suggested that these be encrypted with ansible-vault:
    # ansible-vault edit group_vars/windows.yml

    ansible_ssh_user: Administrator
    ansible_ssh_pass: SekritPasswordGoesHere
    ansible_ssh_port: 5986
    ansible_connection: winrm

Notice that the ssh_port is not actually for SSH, but this is a holdover variable name from how Ansible is mostly an SSH-oriented system.  Again, Windows management will not happen over SSH.

When using your playbook, don't forget to specify --ask-vault-pass to provide the password to unlock the file.

Test your configuration like so, by trying to contact your Windows nodes.  Note this is not an ICMP ping, but tests the Ansible
communication channel that leverages Windows remoting::

    ansible windows [-i inventory] -m win_ping --ask-vault-pass

If you haven't done anything to prep your systems yet, this won't work yet.  This is covered in a later
section about how to enable powershell remoting - and if neccessary - how to upgrade powershell to
a version that is 3 or higher.

You'll run this command again later though, to make sure everything is working.

.. _windows_system_prep:

Windows System Prep
```````````````````

In order for Ansible to manage your windows machines, you will have to enable Powershell remoting first, which also enables WinRM.

From the Windows host, launch the Powershell Client. For information on Powershell, visit `Microsoft's Using Powershell article <http://technet.microsoft.com/en-us/library/dn425048.aspx>`_.

In the powershell session, run the following to enable PS Remoting and set the execution policy

.. code-block:: bash

    $  Enable-PSRemoting -Force
    $  Set-ExecutionPolicy RemoteSigned

If your Windows firewall is enabled, you must also run the following command to allow firewall access to the public firewall profile:

.. code-block:: bash

    #  Windows 2012 / 2012R2
    $  Set-NetFirewallRule -Name "WINRM-HTTP-In-TCP-PUBLIC" -RemoteAddress Any

    #  Windows 2008 / 2008R2
    $  NetSH ADVFirewall Set AllProfiles Settings remotemanagement Enable

By default, Powershell remoting enables an HTTP listener. The following commands enable an HTTPS listener, which secures communication between the Control Machine and windows.

An SSL certificate for server authentication is required to create the HTTPS listener. The existence of an existing certificate in the computer account can be verified by using the MMC snap-in.

A best practice for SSL certificates is generating them from an internal or external certificate authority. An existing certificate could be located in the computer account certificate store `using the following article <http://technet.microsoft.com/en-us/library/cc754431.aspx#BKMK_computer>`_.

Alternatively, a self-signed SSL certificate can be generated in powershell using `the following technet article <http://social.technet.microsoft.com/wiki/contents/articles/4714.how-to-generate-a-self-signed-certificate-using-powershell.aspx>`_. At a minimum, the subject name should match the hostname, and Server Authentication is required. Once the self signed certificate is obtained, the certificate thumbprint can be identified using `How to: Retrieve the Thumbprint of a Certificate <http://msdn.microsoft.com/en-us/library/ms734695%28v=vs.110%29.aspx>`_.

.. code-block:: bash

    #  Create the https listener
    $  winrm create winrm/config/Listener?Address=*+Transport=HTTPS  @{Hostname="host_name";CertificateThumbprint="certificate_thumbprint"}

    #  Delete the http listener
    $  WinRM delete winrm/config/listener?Address=*+Transport=HTTP

Again, if your Windows firewall is enabled, the following command to allow firewall access to the HTTPS listener:

.. code-block:: bash

    #  Windows 2008 / 2008R2 / 2012 / 2012R2
    $  netsh advfirewall firewall add rule Profile=public name="Allow WinRM HTTPS" dir=in localport=5986 protocol=TCP action=allow

It's time to verify things are working::

    ansible windows [-i inventory] -m win_ping --ask-vault-pass

However, if you are still running Powershell 2.0 on remote systems, it's time to use Ansible to upgrade powershell
before proceeding further, as some of the Ansible modules will require Powershell 3.0.  

In the future, Ansible may provide a shortcut installer that automates these steps for prepping a Windows machine.

.. _getting_to_powershell_three_or_higher:

Getting to Powershell 3.0 or higher
```````````````````````````````````

Powershell 3.0 or higher is needed for most provided Ansible modules for Windows.

Looking at an ansible checkout, copy the `examples/scripts/upgrade_to_ps3.ps1 <https://github.com/cchurch/ansible/blob/devel/examples/scripts/upgrade_to_ps3.ps1>`_ script onto the remote host and run a powershell console as an administrator.  You will now be running Powershell 3 and can try connectivity again using the win_ping technique referenced above.

.. _what_windows_modules_are_available:

What modules are available
``````````````````````````

Most of the Ansible modules in core Ansible are written for a combination of Linux/Unix machines and arbitrary web services, though there are various 
Windows modules as listed in the `"windows" subcategory of the Ansible module index <http://docs.ansible.com/list_of_windows_modules.html>`_.  

Browse this index to see what is available.

In many cases, it may not be neccessary to even write or use an Ansible module.

In particular, the "script" module can be used to run arbitrary powershell scripts, allowing Windows administrators familiar with powershell a very native way to do things, as in the following playbook::

    - hosts: windows
      tasks:
        - script: foo.ps1 --argument --other-argument

Note there are a few other Ansible modules that don't start with "win" that also function, including "slurp", "raw", and "setup" (which is how fact gathering works).

.. _developers_developers_developers:

Developers: Supported modules and how it works
``````````````````````````````````````````````

Developing ansible modules are covered in a `later section of the documentation <http://developing_modules.html>`_, with a focus on Linux/Unix.
What if you want to write Windows modules for ansible though?

For Windows, ansible modules are implemented in Powershell.  Skim those Linux/Unix module development chapters before proceeding.

Windows modules live in a "windows/" subfolder in the Ansible "library/" subtree.  For example, if a module is named
"library/windows/win_ping", there will be embedded documentation in the "win_ping" file, and the actual powershell code will live in a "win_ping.ps1" file.  Take a look at the sources and this will make more sense.

Modules (ps1 files) should start as follows::

    #!powershell
    # <license>

    # WANT_JSON
    # POWERSHELL_COMMON

    # code goes here, reading in stdin as JSON and outputting JSON

The above magic is neccessary to tell Ansible to mix in some common code and also know how to push modules out.  The common code contains some nice wrappers around working with hash data structures and emitting JSON results, and possibly a few mpmore useful things.  Regular Ansible has this same concept for reusing Python code - this is just the windows equivalent.

What modules you see in windows/ are just a start.  Additional modules may be submitted as pull requests to github.

.. _windows_and_linux_control_machine:

Reminder: You Must Have a Linux Control Machine
```````````````````````````````````````````````

Note running Ansible from a Windows control machine is NOT a goal of the project.  Refrain from asking for this feature,
as it limits what technologies, features, and code we can use in the main project in the future.  A Linux control machine
will be required to manage Windows hosts.

Cygwin is not supported, so please do not ask questions about Ansible running from Cygwin.

.. _windows_facts:

Windows Facts
`````````````

Just as with Linux/Unix, facts can be gathered for windows hosts, which will return things such as the operating system version.  To see what variables are available about a windows host, run the following::

    ansible winhost.example.com -m setup

Note that this command invocation is exactly the same as the Linux/Unix equivalent.

.. _windows_playbook_example:

Windows Playbook Examples
`````````````````````````

Look to the list of windows modules for most of what is possible, though also some modules like "raw" and "script" also work on Windows, as do "fetch" and "slurp".

Here is an example of pushing and running a powershell script::

    - name: test script module
      hosts: windows
      tasks:
        - name: run test script
          script: files/test_script.ps1

Running individual commands uses the 'raw' module, as opposed to the shell or command module as is common on Linux/Unix operating systems::

    - name: test raw module
      hosts: windows
      tasks:
        - name: run ipconfig
          raw: ipconfig
          register: ipconfig
        - debug: var=ipconfig

And for a final example, here's how to use the win_stat module to test for file existance.  Note that the data returned byt he win_stat module is slightly different than what is provided by the Linux equivalent::

    - name: test stat module
      hosts: windows
      tasks:
        - name: test stat module on file
          win_stat: path="C:/Windows/win.ini"
          register: stat_file

        - debug: var=stat_file

        - name: check stat_file result
          assert:
              that:
                 - "stat_file.stat.exists"
                 - "not stat_file.stat.isdir"
                 - "stat_file.stat.size > 0"
                 - "stat_file.stat.md5"

Again, recall that the Windows modules are all listed in the Windows category of modules, with the exception that the "raw", "script", and "fetch" modules are also available.  These modules do not start with a "win" prefix.

.. _windows_contributions:

Windows Contributions
`````````````````````

Windows support in Ansible is still very new, and contributions are quite welcome, whether this is in the
form of new modules, tweaks to existing modules, documentation, or something else.  Please stop by the ansible-devel mailing list if you would like to get involved and say hi.

.. seealso::

   :doc:`developing_modules`
       How to write modules
   :doc:`playbooks`
       Learning ansible's configuration management language
   `List of Windows Modules <http://docs.ansible.com/list_of_windows_modules.html>`_
       Windows specific module list, all implemented in powershell
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel


