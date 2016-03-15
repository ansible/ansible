Windows Support
===============

.. contents:: Topics

.. _windows_how_does_it_work:

Windows: How Does It Work
`````````````````````````

As you may have already read, Ansible manages Linux/Unix machines using SSH by default.

Starting in version 1.7, Ansible also contains support for managing Windows machines.  This uses
native PowerShell remoting, rather than SSH.

Ansible will still be run from a Linux control machine, and uses the "winrm" Python module to talk to remote hosts.

No additional software needs to be installed on the remote machines for Ansible to manage them, it still maintains the agentless properties that make it popular on Linux/Unix.

Note that it is expected you have a basic understanding of Ansible prior to jumping into this section, so if you haven't written a Linux playbook first, it might be worthwhile to dig in there first.

.. _windows_installing:

Installing on the Control Machine
`````````````````````````````````

On a Linux control machine::

   pip install "pywinrm>=0.1.1"

Note:: on distributions with multiple python versions, use pip2 or pip2.x, where x matches the python minor version Ansible is running under.

Active Directory Support
++++++++++++++++++++++++

If you wish to connect to domain accounts published through Active Directory (as opposed to local accounts created on the remote host), you will need to install the "python-kerberos" module on the Ansible control host (and the MIT krb5 libraries it depends on). The Ansible control host also requires a properly configured computer account in Active Directory.

Installing python-kerberos dependencies
---------------------------------------

.. code-block:: bash

   # Via Yum
   yum -y install python-devel krb5-devel krb5-libs krb5-workstation

   # Via Apt (Ubuntu)
   sudo apt-get install python-dev libkrb5-dev

   # Via Portage (Gentoo)
   emerge -av app-crypt/mit-krb5
   emerge -av dev-python/setuptools

   # Via pkg (FreeBSD)
   sudo pkg install security/krb5

   # Via OpenCSW (Solaris)
   pkgadd -d http://get.opencsw.org/now
   /opt/csw/bin/pkgutil -U
   /opt/csw/bin/pkgutil -y -i libkrb5_3

   # Via Pacman (Arch Linux)
   pacman -S krb5

Installing python-kerberos
--------------------------

Once you've installed the necessary dependencies, the python-kerberos wrapper can be installed via pip:

.. code-block:: bash

   pip install kerberos

Kerberos is installed and configured by default on OS X and many Linux distributions. If your control machine has not already done this for you, you will need to.

Configuring Kerberos
--------------------

Edit your /etc/krb5.conf (which should be installed as a result of installing packages above) and add the following information for each domain you need to connect to:

In the section that starts with

.. code-block:: bash

   [realms]

add the full domain name and the fully qualified domain names of your primary and secondary Active Directory domain controllers.  It should look something like this:

.. code-block:: bash

   [realms]
   
    MY.DOMAIN.COM = {
     kdc = domain-controller1.my.domain.com
     kdc = domain-controller2.my.domain.com
    }


and in the [domain_realm] section add a line like the following for each domain you want to access:

.. code-block:: bash

    [domain_realm]
        .my.domain.com = MY.DOMAIN.COM

You may wish to configure other settings here, such as the default domain.

Testing a kerberos connection
-----------------------------

If you have installed krb5-workstation (yum) or krb5-user (apt-get) you can use the following command to test that you can be authorised by your domain controller.

.. code-block:: bash

   kinit user@MY.DOMAIN.COM

Note that the domain part has to be fully qualified and must be in upper case.

To see what tickets if any you have acquired, use the command klist

.. code-block:: bash

   klist


Troubleshooting kerberos connections
------------------------------------

If you unable to connect using kerberos, check the following:

Ensure that forward and reverse DNS lookups are working properly on your domain.

To test this, ping the windows host you want to control by name then use the ip address returned with nslookup.  You should get the same name back from DNS when you use nslookup on the ip address.  

If you get different hostnames back than the name you originally pinged, speak to your active directory administrator and get them to check that DNS Scavenging is enabled and that DNS and DHCP are updating each other.

Ensure that the Ansible controller has a properly configured computer account in the domain.

Check your Ansible controller's clock is synchronised with your domain controller.  Kerberos is time sensitive and a little clock drift can cause tickets not be granted.

Check you are using the real fully qualified domain name for the domain.  Sometimes domains are commonly known to users by aliases.  To check this run:


.. code-block:: bash

   kinit -C user@MY.DOMAIN.COM
   klist

If the domain name returned by klist is different from the domain name you requested, you are requesting using an alias, and you need to update your krb5.conf so you are using the fully qualified domain name, not its alias.

.. _windows_inventory:

Inventory
`````````

Ansible's windows support relies on a few standard variables to indicate the username, password, and connection type (windows) of the remote hosts.  These variables are most easily set up in inventory.  This is used instead of SSH-keys or passwords as normally fed into Ansible::

    [windows]
    winserver1.example.com
    winserver2.example.com

.. include:: ansible_ssh_changes_note.rst

In group_vars/windows.yml, define the following inventory variables::

    # it is suggested that these be encrypted with ansible-vault:
    # ansible-vault edit group_vars/windows.yml

    ansible_user: Administrator
    ansible_password: SecretPasswordGoesHere
    ansible_port: 5986
    ansible_connection: winrm
    # The following is necessary for Python 2.7.9+ when using default WinRM self-signed certificates:
    ansible_winrm_server_cert_validation: ignore

Although Ansible is mostly an SSH-oriented system, Windows management will not happen over SSH (`yet <http://blogs.msdn.com/b/powershell/archive/2015/06/03/looking-forward-microsoft-support-for-secure-shell-ssh.aspx>`).

If you have installed the ``kerberos`` module and ``ansible_user`` contains ``@`` (e.g. ``username@realm``), Ansible will first attempt Kerberos authentication. *This method uses the principal you are authenticated to Kerberos with on the control machine and not ``ansible_user``*. If that fails, either because you are not signed into Kerberos on the control machine or because the corresponding domain account on the remote host is not available, then Ansible will fall back to "plain" username/password authentication.

When using your playbook, don't forget to specify --ask-vault-pass to provide the password to unlock the file.

Test your configuration like so, by trying to contact your Windows nodes.  Note this is not an ICMP ping, but tests the Ansible
communication channel that leverages Windows remoting::

    ansible windows [-i inventory] -m win_ping --ask-vault-pass

If you haven't done anything to prep your systems yet, this won't work yet.  This is covered in a later
section about how to enable PowerShell remoting - and if necessary - how to upgrade PowerShell to
a version that is 3 or higher.

You'll run this command again later though, to make sure everything is working.

Since 2.0, the following custom inventory variables are also supported for additional configuration of WinRM connections::

* ``ansible_winrm_scheme``: Specify the connection scheme (``http`` or ``https``) to use for the WinRM connection.  Ansible uses ``https`` by default unless the port is 5985.
* ``ansible_winrm_path``: Specify an alternate path to the WinRM endpoint.  Ansible uses ``/wsman`` by default.
* ``ansible_winrm_realm``: Specify the realm to use for Kerberos authentication.  If the username contains ``@``, Ansible will use the part of the username after ``@`` by default.
* ``ansible_winrm_transport``: Specify one or more transports as a comma-separated list.  By default, Ansible will use ``kerberos,plaintext`` if the ``kerberos`` module is installed and a realm is defined, otherwise ``plaintext``.
* ``ansible_winrm_server_cert_validation``: Specify the server certificate validation mode (``ignore`` or ``validate``). Ansible defaults to ``validate`` on Python 2.7.9 and higher, which will result in certificate validation errors against the Windows self-signed certificates. Unless verifiable certificates have been configured on the WinRM listeners, this should be set to ``ignore``
* ``ansible_winrm_*``: Any additional keyword arguments supported by ``winrm.Protocol`` may be provided.

.. _windows_system_prep:

Windows System Prep
```````````````````

In order for Ansible to manage your windows machines, you will have to enable PowerShell remoting configured.

To automate setup of WinRM, you can run `this PowerShell script <https://github.com/ansible/ansible/blob/devel/examples/scripts/ConfigureRemotingForAnsible.ps1>`_ on the remote machine.

The example script accepts a few arguments which Admins may choose to use to modify the default setup slightly, which might be appropriate in some cases.

Pass the -CertValidityDays option to customize the expiration date of the generated certificate.
  powershell.exe -File ConfigureRemotingForAnsible.ps1 -CertValidityDays 100

Pass the -SkipNetworkProfileCheck switch to configure winrm to listen on PUBLIC zone interfaces.  (Without this option, the script will fail if any network interface on device is in PUBLIC zone)
  powershell.exe -File ConfigureRemotingForAnsible.ps1 -SkipNetworkProfileCheck

.. note::
   On Windows 7 and Server 2008 R2 machines, due to a bug in Windows
   Management Framework 3.0, it may be necessary to install this
   hotfix http://support.microsoft.com/kb/2842230 to avoid receiving
   out of memory and stack overflow exceptions.  Newly-installed Server 2008
   R2 systems which are not fully up to date with windows updates are known
   to have this issue.

   Windows 8.1 and Server 2012 R2 are not affected by this issue as they
   come with Windows Management Framework 4.0.

.. _getting_to_powershell_three_or_higher:

Getting to PowerShell 3.0 or higher
```````````````````````````````````

PowerShell 3.0 or higher is needed for most provided Ansible modules for Windows, and is also required to run the above setup script. Note that PowerShell 3.0 is only supported on Windows 7 SP1, Windows Server 2008 SP1, and later releases of Windows.

Looking at an Ansible checkout, copy the `examples/scripts/upgrade_to_ps3.ps1 <https://github.com/cchurch/ansible/blob/devel/examples/scripts/upgrade_to_ps3.ps1>`_ script onto the remote host and run a PowerShell console as an administrator.  You will now be running PowerShell 3 and can try connectivity again using the win_ping technique referenced above.

.. _what_windows_modules_are_available:

What modules are available
``````````````````````````

Most of the Ansible modules in core Ansible are written for a combination of Linux/Unix machines and arbitrary web services, though there are various
Windows modules as listed in the `"windows" subcategory of the Ansible module index <http://docs.ansible.com/list_of_windows_modules.html>`_.

Browse this index to see what is available.

In many cases, it may not be necessary to even write or use an Ansible module.

In particular, the "script" module can be used to run arbitrary PowerShell scripts, allowing Windows administrators familiar with PowerShell a very native way to do things, as in the following playbook::

    - hosts: windows
      tasks:
        - script: foo.ps1 --argument --other-argument

Note there are a few other Ansible modules that don't start with "win" that also function, including "slurp", "raw", and "setup" (which is how fact gathering works).

.. _developers_developers_developers:

Developers: Supported modules and how it works
``````````````````````````````````````````````

Developing Ansible modules are covered in a `later section of the documentation <http://docs.ansible.com/developing_modules.html>`_, with a focus on Linux/Unix.
What if you want to write Windows modules for Ansible though?

For Windows, Ansible modules are implemented in PowerShell.  Skim those Linux/Unix module development chapters before proceeding. Windows modules in the core and extras repo live in a "windows/" subdir. Custom modules can go directly into the Ansible "library/" directories or those added in ansible.cfg. Documentation lives in a `.py` file with the same name. For example, if a module is named "win_ping", there will be embedded documentation in the "win_ping.py" file, and the actual PowerShell code will live in a "win_ping.ps1" file. Take a look at the sources and this will make more sense.

Modules (ps1 files) should start as follows::

    #!powershell
    # <license>

    # WANT_JSON
    # POWERSHELL_COMMON

    # code goes here, reading in stdin as JSON and outputting JSON

The above magic is necessary to tell Ansible to mix in some common code and also know how to push modules out.  The common code contains some nice wrappers around working with hash data structures and emitting JSON results, and possibly a few more useful things.  Regular Ansible has this same concept for reusing Python code - this is just the windows equivalent.

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

Here is an example of pushing and running a PowerShell script::

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

Running common DOS commands like 'del", 'move', or 'copy" is unlikely to work on a remote Windows Server using Powershell, but they can work by prefacing the commands with "CMD /C" and enclosing the command in double quotes as in this example::

    - name: another raw module example
      hosts: windows
      tasks:
         - name: Move file on remote Windows Server from one location to another
           raw: CMD /C "MOVE /Y C:\teststuff\myfile.conf C:\builds\smtp.conf"

And for a final example, here's how to use the win_stat module to test for file existence.  Note that the data returned by the win_stat module is slightly different than what is provided by the Linux equivalent::

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
       Learning Ansible's configuration management language
   `List of Windows Modules <http://docs.ansible.com/list_of_windows_modules.html>`_
       Windows specific module list, all implemented in PowerShell
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
