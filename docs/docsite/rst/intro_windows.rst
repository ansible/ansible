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
While not supported by Microsoft or Ansible, this Linux control machine can be a Windows Subsystem for Linux (WSL) bash shell.

No additional software needs to be installed on the remote machines for Ansible to manage them, it still maintains the agentless properties that make it popular on Linux/Unix.

Note that it is expected you have a basic understanding of Ansible prior to jumping into this section, so if you haven't written a Linux playbook first, it might be worthwhile to dig in there first.

.. _windows_installing:

Installing on the Control Machine
`````````````````````````````````

On a Linux control machine::

   pip install "pywinrm>=0.2.2"

.. Note:: on distributions with multiple python versions, use pip2 or pip2.x, where x matches the python minor version Ansible is running under.


.. _windows_control_machine:

Using a Windows control machine
```````````````````````````````
A Linux control machine is required to manage Windows hosts. This Linux control machine can be a Windows Subsystem for Linux (WSL) bash shell.


.. Note:: Running Ansible from a Windows control machine directly is not a goal of the project.  Refrain from asking for this feature, as it limits what technologies, features, and code we can use in the main project in the future.  

.. Note:: The Windows Subsystem for Linux (Beta) is not supported by Microsoft or Ansible and should not be used for production systems. 

If you would like to experiment with the Windows Subsystem for Linux (WSL), first enable the Windows Subsystem for Linux using
`these instructions <https://www.jeffgeerling.com/blog/2017/using-ansible-through-windows-10s-subsystem-linux>`_.
This requires a reboot.

Once WSL is enabled, you can open the Bash terminal. At the prompt, you can quickly start using the latest Ansible release by running the following commands::

    sudo apt-get update
    sudo apt-get install python-pip git libffi-dev libssl-dev -y
    pip install ansible pywinrm

    # this step is only necessary for Windows builds earlier than 16188, and must be repeated each time bash is launched,
    # unless bash is launched as ``bash --login``
    # see https://github.com/Microsoft/BashOnWindows/issues/2148 and
    # https://github.com/Microsoft/BashOnWindows/issues/816#issuecomment-301216901 for details
    source ~/.profile

After you've successfully run these commands, you can start to create your inventory, write example playbooks and start targeting systems using the plethora of available Windows modules.

If you want to run Ansible from source for development purposes, simply uninstall the pip-installed version (which will leave all the necessary dependencies behind), then clone the Ansible source, and run the hacking script to configure it to run from source::

    pip uninstall ansible -y
    git clone https://github.com/ansible/ansible.git
    source ansible/hacking/env-setup

.. Note:: Ansible is also reported to "work" on Cygwin, but installation is more cumbersome, and will incur sporadic failures due to Cygwin's implementation of ``fork()``.


Authentication Options
``````````````````````

When connecting to a Windows host there are different authentication options that can be used. The options and the features they support are:

+-------------+----------------+---------------------------+-----------------------+
| Option      | Local Accounts | Active Directory Accounts | Credential Delegation |
+=============+================+===========================+=======================+
| Basic       | Yes            | No                        | No                    |
+-------------+----------------+---------------------------+-----------------------+
| Certificate | Yes            | No                        | No                    |
+-------------+----------------+---------------------------+-----------------------+
| Kerberos    | No             | Yes                       | Yes                   |
+-------------+----------------+---------------------------+-----------------------+
| NTLM        | Yes            | Yes                       | No                    |
+-------------+----------------+---------------------------+-----------------------+
| CredSSP     | Yes            | Yes                       | Yes                   |
+-------------+----------------+---------------------------+-----------------------+

You can specify which authentication option you wish to use by setting it to the ``ansible_winrm_transport`` variable.

Certificate
+++++++++++

Certificate authentication is similar to SSH where a certificate is assigned to a local user and instead of using a password to authenticate a certificate is used instead.


Kerberos
++++++++

Kerberos is the preferred option compared to NTLM to use when using an Active Directory account but it requires a few extra steps to set up on the Ansible control host. You will need to install the "python-kerberos" module on the Ansible control host (and the MIT krb5 libraries it depends on). The Ansible control host also requires a properly configured computer account in Active Directory.

Installing python-kerberos dependencies
---------------------------------------

.. code-block:: bash

   # Via Yum
   yum -y install python-devel krb5-devel krb5-libs krb5-workstation

   # Via Apt (Ubuntu)
   sudo apt-get install python-dev libkrb5-dev krb5-user

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

   pip install pywinrm[kerberos]

Kerberos is installed and configured by default on OS X and many Linux distributions. If your control machine has not already done this for you, you will need to.

Configuring Kerberos
--------------------

Edit your /etc/krb5.conf (which should be installed as a result of installing packages above) and add the following information for each domain you need to connect to:

In the section that starts with

.. code-block:: ini

   [realms]

add the full domain name and the fully qualified domain names of your primary and secondary Active Directory domain controllers.  It should look something like this:

.. code-block:: ini

   [realms]
   
    MY.DOMAIN.COM = {
     kdc = domain-controller1.my.domain.com
     kdc = domain-controller2.my.domain.com
    }


and in the [domain_realm] section add a line like the following for each domain you want to access:

.. code-block:: ini

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

Automatic kerberos ticket management
------------------------------------

Ansible defaults to automatically managing kerberos tickets (as of Ansible 2.3) when both username and password are specified for a host that's configured for kerberos. A new ticket is created in a temporary credential cache for each host, before each task executes (to minimize the chance of ticket expiration). The temporary credential caches are deleted after each task, and will not interfere with the default credential cache.

To disable automatic ticket management (e.g., to use an existing SSO ticket or call ``kinit`` manually to populate the default credential cache), set ``ansible_winrm_kinit_mode=manual`` via inventory.

Automatic ticket management requires a standard ``kinit`` binary on the control host system path. To specify a different location or binary name, set the ``ansible_winrm_kinit_cmd`` inventory var to the fully-qualified path to an MIT krbv5 ``kinit``-compatible binary.

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


CredSSP
+++++++

CredSSP authentication can be used to authenticate with both domain and local accounts. It allows credential delegation to do second hop authentication on a remote host by sending an encrypted form of the credentials to the remote host using the CredSSP protocol.

Installing requests-credssp
---------------------------

To install credssp you can use pip to install the requests-credssp library:

.. code-block:: bash

   pip install pywinrm[credssp]

CredSSP and TLS 1.2
-------------------

CredSSP requires the remote host to have TLS 1.2 configured or else the connection will fail. TLS 1.2 is installed by default from Server 2012 and Windows 8 onwards. For Server 2008, 2008 R2 and Windows 7 you can add TLS 1.2 support by:

* Installing the `TLS 1.2 update from Microsoft <https://support.microsoft.com/en-us/help/3080079/update-to-add-rds-support-for-tls-1.1-and-tls-1.2-in-windows-7-or-windows-server-2008-r2>`_
* Adding the TLS 1.2 registry keys as shown on this `page <https://technet.microsoft.com/en-us/library/dn786418.aspx#BKMK_SchannelTR_TLS12>`_

Credential Delegation
+++++++++++++++++++++

If you need to interact with a remote resource or run a process that requires the credentials to be stored in the current session like a certreq.exe then an authentication protocol that supports credential delegation needs to be used.

Inventory
`````````

Ansible's windows support relies on a few standard variables to indicate the username, password, and connection type (windows) of the remote hosts.  These variables are most easily set up in inventory.  This is used instead of SSH-keys or passwords as normally fed into Ansible::

    [windows]
    winserver1.example.com
    winserver2.example.com

.. include:: ../rst_common/ansible_ssh_changes_note.rst

In ``group_vars/windows.yml``, define the following inventory variables::

    # it is suggested that these be encrypted with ansible-vault:
    # ansible-vault edit group_vars/windows.yml

    ansible_user: Administrator
    ansible_password: SecretPasswordGoesHere
    ansible_port: 5986
    ansible_connection: winrm
    # The following is necessary for Python 2.7.9+ (or any older Python that has backported SSLContext, eg, Python 2.7.5 on RHEL7) when using default WinRM self-signed certificates:
    ansible_winrm_server_cert_validation: ignore

Attention for the older style variables (``ansible_ssh_*``): ansible_ssh_password doesn't exist, should be ansible_ssh_pass.

Although Ansible is mostly an SSH-oriented system, Windows management will not happen over SSH (`yet <http://blogs.msdn.com/b/powershell/archive/2015/06/03/looking-forward-microsoft-support-for-secure-shell-ssh.aspx>`_).

If you have installed the ``kerberos`` module and ``ansible_user`` contains ``@`` (e.g. ``username@realm``), Ansible will first attempt Kerberos authentication. *This method uses the principal you are authenticated to Kerberos with on the control machine and not* ``ansible_user``. If that fails, either because you are not signed into Kerberos on the control machine or because the corresponding domain account on the remote host is not available, then Ansible will fall back to "plain" username/password authentication.

When using your playbook, don't forget to specify ``--ask-vault-pass`` to provide the password to unlock the file.

Test your configuration like so, by trying to contact your Windows nodes.  Note this is not an ICMP ping, but tests the Ansible
communication channel that leverages Windows remoting::

    ansible windows [-i inventory] -m win_ping --ask-vault-pass

If you haven't done anything to prep your systems yet, this won't work yet.  This is covered in a later
section about how to enable PowerShell remoting - and if necessary - how to upgrade PowerShell to
a version that is 3 or higher.

You'll run this command again later though, to make sure everything is working.

Since 2.0, the following custom inventory variables are also supported for additional configuration of WinRM connections

* ``ansible_winrm_scheme``: Specify the connection scheme (``http`` or ``https``) to use for the WinRM connection.  Ansible uses ``https`` by default unless the port is 5985.
* ``ansible_winrm_path``: Specify an alternate path to the WinRM endpoint.  Ansible uses ``/wsman`` by default.
* ``ansible_winrm_realm``: Specify the realm to use for Kerberos authentication.  If the username contains ``@``, Ansible will use the part of the username after ``@`` by default.
* ``ansible_winrm_transport``: Specify one or more transports as a comma-separated list.  By default, Ansible will use ``kerberos,plaintext`` if the ``kerberos`` module is installed and a realm is defined, otherwise ``plaintext``.
* ``ansible_winrm_server_cert_validation``: Specify the server certificate validation mode (``ignore`` or ``validate``). Ansible defaults to ``validate`` on Python 2.7.9 and higher, which will result in certificate validation errors against the Windows self-signed certificates. Unless verifiable certificates have been configured on the WinRM listeners, this should be set to ``ignore``.
* ``ansible_winrm_kerberos_delegation``: Set to ``true`` to enable delegation of commands on the remote host when using kerberos.
* ``ansible_winrm_operation_timeout_sec``: Increase the default timeout for WinRM operations (default: ``20``).
* ``ansible_winrm_read_timeout_sec``: Increase the WinRM read timeout if you experience read timeout errors (default: ``30``), e.g. intermittent network issues.
* ``ansible_winrm_*``: Any additional keyword arguments supported by ``winrm.Protocol`` may be provided.

.. _windows_system_prep:

Windows System Prep
```````````````````

In order for Ansible to manage your windows machines, you will have to enable and configure PowerShell remoting.

To automate the setup of WinRM, you can run the `examples/scripts/ConfigureRemotingForAnsible.ps1 <https://github.com/ansible/ansible/blob/devel/examples/scripts/ConfigureRemotingForAnsible.ps1>`_ script on the remote machine in a PowerShell console as an administrator.

The example script accepts a few arguments which Admins may choose to use to modify the default setup slightly, which might be appropriate in some cases.

Pass the ``-CertValidityDays`` option to customize the expiration date of the generated certificate::

    powershell.exe -File ConfigureRemotingForAnsible.ps1 -CertValidityDays 100

Pass the ``-EnableCredSSP`` switch to enable CredSSP as an authentication option::

    powershell.exe -File ConfigureRemotingForAnsible.ps1 -EnableCredSSP

Pass the ``-ForceNewSSLCert`` switch to force a new SSL certificate to be attached to an already existing winrm listener. (Avoids SSL winrm errors on syspreped Windows images after the CN changes)::

    powershell.exe -File ConfigureRemotingForAnsible.ps1 -ForceNewSSLCert

Pass the ``-SkipNetworkProfileCheck`` switch to configure winrm to listen on PUBLIC zone interfaces.  (Without this option, the script will fail if any network interface on device is in PUBLIC zone)::

    powershell.exe -File ConfigureRemotingForAnsible.ps1 -SkipNetworkProfileCheck

To troubleshoot the ``ConfigureRemotingForAnsible.ps1`` writes every change it makes to the Windows EventLog (useful when run unattendedly). Additionally the ``-Verbose`` option can be used to get more information on screen about what it is doing.

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

Looking at an Ansible checkout, copy the `examples/scripts/upgrade_to_ps3.ps1 <https://github.com/ansible/ansible/blob/devel/examples/scripts/upgrade_to_ps3.ps1>`_ script onto the remote host and run a PowerShell console as an administrator.  You will now be running PowerShell 3 and can try connectivity again using the ``win_ping`` technique referenced above.

.. _what_windows_modules_are_available:

What modules are available
``````````````````````````

Most of the Ansible modules in core Ansible are written for a combination of Linux/Unix machines and arbitrary web services, though there are various
Windows-only modules. These are listed in the `"windows" subcategory of the Ansible module index <http://docs.ansible.com/list_of_windows_modules.html>`_.

In addition, the following core modules/action-plugins work with Windows:

* add_host
* assert
* async_status
* debug
* fail
* fetch
* group_by
* include
* include_role
* include_vars
* meta
* pause
* raw
* script
* set_fact
* set_stats
* setup
* slurp
* template (also: win_template)
* wait_for_connection

Some modules can be utilised in playbooks that target windows by delegating to localhost, depending on what you are
attempting to achieve.  For example, ``assemble`` can be used to create a file on your ansible controller that is then 
sent to your windows targets using ``win_copy``.

In many cases, there is no need to use or write an Ansible module. In particular, the ``script`` module can be used to run arbitrary PowerShell scripts, allowing Windows administrators familiar with PowerShell a very native way to do things, as in the following playbook::

    - hosts: windows
      tasks:
        - script: foo.ps1 --argument --other-argument

But also the ``win_shell`` module allows for running Powershell snippets inline::

    - hosts: windows
      tasks:
        - name: Remove Appx packages (and their hindering file assocations)
          win_shell: |
            Get-AppxPackage -name "Microsoft.ZuneMusic" | Remove-AppxPackage
            Get-AppxPackage -name "Microsoft.ZuneVideo" | Remove-AppxPackage

.. _developers_developers_developers:

Developers: Supported modules and how it works
``````````````````````````````````````````````

Developing Ansible modules are covered in a `later section of the documentation <http://docs.ansible.com/developing_modules.html>`_, with a focus on Linux/Unix.
What if you want to write Windows modules for Ansible though?

For Windows, Ansible modules are implemented in PowerShell.  Skim those Linux/Unix module development chapters before proceeding. Windows modules in the core and extras repo live in a ``windows/`` subdir. Custom modules can go directly into the Ansible ``library/`` directories or those added in ansible.cfg. Documentation lives in a ``.py`` file with the same name. For example, if a module is named ``win_ping``, there will be embedded documentation in the ``win_ping.py`` file, and the actual PowerShell code will live in a ``win_ping.ps1`` file. Take a look at the sources and this will make more sense.

Modules (ps1 files) should start as follows::

    #!powershell
    # <license>

    # WANT_JSON
    # POWERSHELL_COMMON

    # code goes here, reading in stdin as JSON and outputting JSON

The above magic is necessary to tell Ansible to mix in some common code and also know how to push modules out.  The common code contains some nice wrappers around working with hash data structures and emitting JSON results, and possibly a few more useful things.  Regular Ansible has this same concept for reusing Python code - this is just the windows equivalent.

What modules you see in ``windows/`` are just a start.  Additional modules may be submitted as pull requests to github.

.. _windows_facts:

Windows Facts
`````````````

Just as with Linux/Unix, facts can be gathered for windows hosts, which will return things such as the operating system version.  To see what variables are available about a windows host, run the following::

    ansible winhost.example.com -m setup

Note that this command invocation is exactly the same as the Linux/Unix equivalent.

.. _windows_playbook_example:

Windows Playbook Examples
`````````````````````````

Here is an example of pushing and running a PowerShell script::

    - name: test script module
      hosts: windows
      tasks:
        - name: run test script
          script: files/test_script.ps1

Running individual commands uses the ``win_command <https://docs.ansible.com/ansible/win_command_module.html>`` or ``win_shell <https://docs.ansible.com/ansible/win_shell_module.html>`` module, as opposed to the shell or command module as is common on Linux/Unix operating systems::

    - name: test raw module
      hosts: windows
      tasks:
        - name: run ipconfig
          win_command: ipconfig
          register: ipconfig
        - debug: var=ipconfig

Running common DOS commands like ``del``, ``move``, or ``copy`` is unlikely to work on a remote Windows Server using Powershell, but they can work by prefacing the commands with ``CMD /C`` and enclosing the command in double quotes as in this example::

    - name: another raw module example
      hosts: windows
      tasks:
         - name: Move file on remote Windows Server from one location to another
           win_command: CMD /C "MOVE /Y C:\teststuff\myfile.conf C:\builds\smtp.conf"

You may wind up with a more readable playbook by using the PowerShell equivalents of DOS commands.  For example, to achieve the same effect as the example above, you could use::

    - name: another raw module example demonstrating powershell one liner
      hosts: windows
      tasks:
         - name: Move file on remote Windows Server from one location to another
           win_command: Powershell.exe "Move-Item C:\teststuff\myfile.conf C:\builds\smtp.conf"

Bear in mind that using ``win_command`` or ``win_shell`` will always report ``changed``, and it is your responsibility to ensure PowerShell will need to handle idempotency as appropriate (the move examples above are inherently not idempotent), so where possible use (or write) a module.

Here's an example of how to use the ``win_stat`` module to test for file existence. Note that the data returned by the ``win_stat`` module is slightly different than what is provided by the Linux equivalent::

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

.. _windows_contributions:

Windows Contributions
`````````````````````

Windows support in Ansible is still relatively new, and contributions are quite welcome, whether this is in the
form of new modules, tweaks to existing modules, documentation, or something else.  Please stop by the ansible-devel mailing list if you would like to get involved and say hi.

.. seealso::

   :doc:`dev_guide/developing_modules`
       How to write modules
   :doc:`playbooks`
       Learning Ansible's configuration management language
   `List of Windows Modules <http://docs.ansible.com/list_of_windows_modules.html>`_
       Windows specific module list, all implemented in PowerShell
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
