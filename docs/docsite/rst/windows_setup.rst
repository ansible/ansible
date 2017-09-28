Setting up a Windows Host
=========================
Before Ansible can communicate with a Windows host, there may be some setup
required on the host to enable this.

.. contents:: Topics

Host Requirments
````````````````
For Ansible to communicate to a Windows host and use Windows modules, the
Windows host must meet the following requirements:

* The OS versions that are supported under Ansible fall under the same support
  agreement as Microsoft. If running a desktop OS, it must be Windows 7, 8.1,
  or 10. If running a desktop OS it must be Windows Server 2008, 2008 R2,
  2012, 2012 R2, or 2016.

* Ansible requires Powershell 3.0 or newer and at least .NET 4.0 to be
  installed on the Windows host.

* A WinRM listener is created and is activated, more details for this can be
  found below.

.. Note:: While these are the base requirements some modules have separate
    requirements where it may need a newer OS or the latest powershell
    version. Please read the notes section on a module to determine whether
    a host meets those requirements.

Upgrading Powershell and .NET Framework
---------------------------------------
Ansible requires Powershell v3 and .NET Framework 4.0 or newer to function and
on older OS' like Server 2008 and Windows 7, the base image does not meet this
requirement. The script `update_powershell.ps1 <https://github.com/ansible/ansible/blob/devel/examples/scripts/update_powershell.ps1>`_
can be used to install whatever powershell version that is set along with the
required .NET Framework alongside it.

This is an example of how to run this script from powershell:

.. code-block:: powershell

    $url = "https://raw.githubusercontent.com/ansible/ansible/devel/examples/scripts/update_powershell.ps1"
    $file = "$env:SystemDrive\temp\update_powershell.ps1"
    $username = "Administrator"
    $password = "Password"

    (New-Object -TypeName System.Net.WebClient).DownloadFile($url, $file)
    Set-ExecutionPolicy -ExecutionPolicy Unrestricted -Force

    # version can be 3.0, 4.0 or 5.1
    &$file -version 5.1 -username $username -password $password -Verbose

Once complete, the following commands should be run to remove the auto logon
and set the execution policy from powershell:

.. code-block:: powershell

    # this isn't needed but is a good security practice to complete
    Set-ExecutionPolicy -ExecutionPolicy Restricted -Force

    $reg_winlogon_path = "HKLM:\Software\Microsoft\Windows NT\CurrentVersion\Winlogon"
    Set-ItemProperty -Path $reg_winlogon_path -Name AutoAdminLogon -Value 0
    Remove-ItemProperty -Path $reg_winlogon_path -Name DefaultUserName -ErrorAction SilentlyContinue
    Remove-ItemProperty -Path $reg_winlogon_path -Name DefaultPassword -ErrorAction SilentlyContinue

The script works by checking to see what programs need to be installed like
.NET Framework 4.5.2 and then what powershell version is required. If a reboot
is required and the ``username`` and ``password`` parameters are set, the
script will automatically reboot and automatically logon when it comes back up
from the reboot. This continues until no more actions are required and the
powershell version matches the target version. If the ``username`` and
``password`` parameters are not set, the script will prompt the user to
manually reboot and logon when required. When the user is next logged in, the
script will continue where it left off and the process continues until no more
actions are required.

.. Note:: If running on Server 2008, then SP2 must be installed before .NET 4.0
    and Powershell 3.0 can be installed. If running on Server 2008 R2 or
    Windows 7, then SP1 must be installed.

.. Note:: Windows Server 2008 can only install Powershell 3.0, specifying a
    newer version will result in the script failing.

.. Note:: If setting the ``username`` and ``password`` parameter, these values
    are stored in plain text in the registry. Make sure the cleanup commands
    are run after runnning this step to ensure no credentials are still stored
    on the host.

WinRM Memory Hotfix
-------------------
When running on Powershell v3.0, there is a bug with the WinRM service on
Windows Server 2008, 2008 R2, 2012, and Windows 7 that limits the amount of
memory available to the service. Without this hotfix installed, Ansible will
fail to execute certain commands on the Windows host. It is highly recommended
these hotfixes are installed as part of the system bootstapping or imaging
process. The script `winrm_hotfix.ps1 <https://github.com/ansible/ansible/blob/devel/examples/scripts/winrm_hotfix.ps1>`_
can be used to install the hotfix on affected hosts.

The following powershell command will install the hotfix:

.. code-block:: powershell

    $url = "https://raw.githubusercontent.com/ansible/ansible/devel/examples/scripts/winrm_hotfix.ps1"
    $file = "$env:SystemDrive\temp\winrm_hotfix.ps1"

    (New-Object -TypeName System.Net.WebClient).DownloadFile($url, $file)
    powershell.exe -ExecutionPolicy ByPass -File $file -Verbose

WinRM Setup
```````````
Once powershell has been upgraded to at least 3.0, the final step is for the
WinRM service to be configured so that Ansible can connect to it. There are two
main components of the WinRM service that Ansible interfaces with; the
``listener`` and the ``service`` configuration settings.

Further details about each component can be read below but to get a single host
up and running to use with Windows the script `ConfigureRemotingForAnsible.ps1 <https://github.com/ansible/ansible/blob/devel/examples/scripts/ConfigureRemotingForAnsible.ps1>`_
can be used. This script set's up both a HTTP and HTTPS listener with a self
signed certificate as well as enabling the ``Basic`` authentication option on
the service.

To run this script, run the following in powershell:

.. code-block:: powershell

    $url = "https://raw.githubusercontent.com/ansible/ansible/devel/examples/scripts/ConfigureRemotingForAnsible.ps1"
    $file = "$env:SystemDrive\temp\ConfigureRemotingForAnsible.ps1"

    (New-Object -TypeName System.Net.WebClient).DownloadFile($url, $file)

    powershell.exe -ExecutionPolicy ByPass -File $file

There are different switches and parameters, like ``-EnableCredSSP`` and
``-ForceNewSSLCert`` that can be set alongside this script. he documentation
for these options are located at the top of the script itself.

.. Note:: The ConfigureRemotingForAnsible.ps1 script should not be used in a
    production environment. It enables settings that can be inherently insecure
    like ``Basic`` auth. It is only designed for dev work and to help people
    can get started.

WinRM Listener
--------------
WinRM works by having the service listen on a port or ports from requests and
handle them accordingly. For it to listener on a port it must have a listener
created and configured with that port.

To view the current listeners that are running on the WinRM service, run the
following::

    winrm enumerate winrm/config/Listeners

This will output something like the following::

    Listener
        Address = *
        Transport = HTTP
        Port = 5985
        Hostname
        Enabled = true
        URLPrefix = wsman
        CertificateThumbprint
        ListeningOn = 10.0.2.15, 127.0.0.1, 192.168.56.155, ::1, fe80::5efe:10.0.2.15%6, fe80::5efe:192.168.56.155%8, fe80::
    ffff:ffff:fffe%2, fe80::203d:7d97:c2ed:ec78%3, fe80::e8ea:d765:2c69:7756%7

    Listener
        Address = *
        Transport = HTTPS
        Port = 5986
        Hostname = SERVER2016
        Enabled = true
        URLPrefix = wsman
        CertificateThumbprint = E6CDAA82EEAF2ECE8546E05DB7F3E01AA47D76CE
        ListeningOn = 10.0.2.15, 127.0.0.1, 192.168.56.155, ::1, fe80::5efe:10.0.2.15%6, fe80::5efe:192.168.56.155%8, fe80::
    ffff:ffff:fffe%2, fe80::203d:7d97:c2ed:ec78%3, fe80::e8ea:d765:2c69:7756%7

In the example above there are two listeners activated, one is listening on
port 5985 over HTTP and the other is listening on port 5986 over HTTPS. Some of
the key options that are useful to understand are:

* ``Transport``: Whether the listener is run over HTTP or HTTPS, it is
  recommended to use a listener over HTTPS as the data is encrypted without
  any further changes required.

* ``Port``: The port the listener runs on, by default it is ``5985`` for HTTP
  and ``5986`` for HTTPS. This port can be changed to whatever is required and
  corresponds to the host var ``ansible_port``.

* ``URLPrefix``: The URL prefix to listen on, by default it is ``wsman``. If
  this is changed, the host var ``ansible_winrm_path`` must be set to the same
  value.

* ``CertificateThumbprint``: If running over a HTTPS listener, this is the
  thumbprint of the certificate in the Windows Certificate Store that is used
  in the connection. To get the details of the certificate itself, run this
  command in powershell:

  .. code-block:: powershell
    
    $thumbprint = "E6CDAA82EEAF2ECE8546E05DB7F3E01AA47D76CE"
    Get-ChildItem -Path cert:\LocalMachine\My -Recurse | Where-Object { $_.Thumbprint -eq $thumbprint } | Select-Object *

Setup WinRM Listener
++++++++++++++++++++
When setting up a WinRM listener, there are three ways in which they can be
created. The best option to choose from depends on how each environment is
setup, e.g. use GPO when in a domain environment vs quickconfig when spinning
a new host in the cloud not in a domain. The three different ways a listener
can be set up are:

* Using ``winrm quickconfig`` for HTTP or
  ``winrm quickconfig -transport:https`` for HTTPS. This is the simplest option
  to use when running outside of a domain environment and a simple listener is
  required. This process also has the added benefit of opening up the Firewall
  for the ports required and starts the WinRM service unlike the other two
  options where these steps need to be done separately.

* Using Group Policy Objects, this process is outside the scope of this
  document but guides can be found online on how to do this. This is the best
  way to create a listener when the host is a member of a domain as the
  configuration is done automatically without any user input.

* Using powershell to create the listener with a specific configuration. This
  can be done by running the following powershell commands:

  .. code-block:: powershell

      $selector_set = @{
          Address = "*"
          Transport = "HTTPS"
      }
      $value_set = @{
          CertificateThumbprint = "E6CDAA82EEAF2ECE8546E05DB7F3E01AA47D76CE"
      }

      New-WSManInstance -ResourceURI "winrm/config/Listener" -SelectorSet $selector_set -ValueSet $value_set

  To see the other options with this powershell cmdlet, see
  `New-WSManInstance <https://docs.microsoft.com/en-us/powershell/module/microsoft.wsman.management/new-wsmaninstance?view=powershell-5.1>`_.

.. Note:: When creating a HTTPS listener, an existing certificate needs to be
    created and stored in the ``LocalMachine\My`` certificate store. Without a
    certificate being present in this store, most commands will fail.

Delete WinRM Listener
+++++++++++++++++++++
The method to remove a WinRM listener is quite simple, the following commands
can be used to do so:

.. code-block: powershell

    # remove all listeners
    Remove-Item -Path WSMan:\localhost\Listener\* -Recurse -Force

    # only remove listeners that are run over HTTPS
    Get-ChildItem -Path WSMan:\localhost\Listener | Where-Object { $_.Keys -contains "Transport=HTTPS" } | Remove-Item -Recurse -Force

.. Note:: The ``Keys`` object is a ``String[]`` so it can contain different
    values. By default it contains a key for ``Transport=`` and ``Address=``
    which correspond to the values from winrm enumerate winrm/config/Listeners.

WinRM Service Options
---------------------
The WinRM service component is what governs the rules around the WinRM service
such as the authentication options supported, 

To get an output of the service configurations currently set, run the
following::

    winrm get winrm/config/Service
    winrm get winrm/config/Winrs

This will output something like the following::

    Service
        RootSDDL = O:NSG:BAD:P(A;;GA;;;BA)(A;;GR;;;IU)S:P(AU;FA;GA;;;WD)(AU;SA;GXGW;;;WD)
        MaxConcurrentOperations = 4294967295
        MaxConcurrentOperationsPerUser = 1500
        EnumerationTimeoutms = 240000
        MaxConnections = 300
        MaxPacketRetrievalTimeSeconds = 120
        AllowUnencrypted = false
        Auth
            Basic = true
            Kerberos = true
            Negotiate = true
            Certificate = true
            CredSSP = true
            CbtHardeningLevel = Relaxed
        DefaultPorts
            HTTP = 5985
            HTTPS = 5986
        IPv4Filter = *
        IPv6Filter = *
        EnableCompatibilityHttpListener = false
        EnableCompatibilityHttpsListener = false
        CertificateThumbprint
        AllowRemoteAccess = true

    Winrs
        AllowRemoteShellAccess = true
        IdleTimeout = 7200000
        MaxConcurrentUsers = 2147483647
        MaxShellRunTime = 2147483647
        MaxProcessesPerShell = 2147483647
        MaxMemoryPerShellMB = 2147483647
        MaxShellsPerUser = 2147483647

While a lot of these options should rarely be changed, a few can easily impact
the operations over WinRM and are useful to understand. Some of the important
options are:

* ``Service\AllowUnencrypted``: This option states whether the WinRM will allow
  traffic that is run over HTTP without message encryption. Message level
  encryption is only supported when ``ansible_winrm_transport`` is ``ntlm``,
  ``kerberos`` or ``credssp``. By default this is ``false`` and should only be
  set to ``true`` in when debugging WinRM messages.

* ``Service\Auth\*``: These are the flags that states what authentication
  options are allowed with the WinRM service. By default ``Negotiate/NTLM`` and
  ``Kerberos`` are enabled.

* ``Service\Auth\CbtHardeningLevel``: States whether channel binding tokens are
  not verified (None), verified but not required (Relaxed), or verified and
  required (Strict). CBT is only used when connecting with NTLM or Kerberos
  over HTTPS. Currently the downstream libraries Ansible use only support
  passing the CBT with NTLM authentication. Using Kerberos with
  ``CbtHardeningLevel = Strict`` will result in a ``404`` error.

* ``Service\CertificateThumbprint``: This is the thumbprint of the certificate
  used to encrypt the TLS channel used with CredSSP authentication. By default
  this is not set to anything which means a self signed certificate generated
  when the WinRM service starts is used instead.

* ``Winrs\MaxShellRunTime``: This is the maximum time, in milliseconds, that a
  remote command is allowed to execute for.

* ``Winrs\MaxMemoryPerShellMB``: This is the maximum amount of memory allocated
  per shell, including the shell's child processes.

To modify a setting in powershell, the following command can be used:

.. code-block:: powershell

    # substitute {path} with the path to the option after winrm/config
    Set-Item -Path WSMan:\localhost\{path} -Value "value here"

    # e.g. to change Service\Auth\CbtHardeningLevel run
    Set-Item -Path WSMan:\localhost\Service\Auth\CbtHardeningLevel -Value Strict

.. Note:: If running in a domain environment, some of these options are set by
    GPO and cannot be changed on the host itself. When a key has been
    configured with GPO it has the text ``[Source="GPO"]`` next to the value.

Common WinRM Issues
-------------------
WinRM can be a finnicky protocol due to the complexity in it's setup and the
wide range of configuration options that can be used. Because of this
complexity, issues that are shown by Ansible could in fact be issues with the
host setup instead. One easy way to determine whether it is a host issue is by
running the following command from another Windows host::

    # test out HTTP
    winrs -r:http://server:5985/wsman -u:Username -p:Password ipconfig

    # test out HTTPS (will fail if the cert is not verifiable)
    winrs -r:http://server:5985/wsman -u:Username -p:Password -ssl ipconfig

    # test out HTTPS, ignoring certificate verification
    $username = "Username"
    $password = ConvertTo-SecureString -String "Password" -AsPlainText -Force
    $cred = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $username, $password

    $session_option = New-PSSessionOption -SkipCACheck -SkipCNCheck -SkipRevocationCheck
    Invoke-Command -ComputerName server -UseSSL -ScriptBlock { ipconfig } -Credential $cred -SessionOption $session_option

If the above works, then see below for more help but if it fails then the issue
is probably related to the WinRM setup.

HTTP 401/Credentials Rejected
+++++++++++++++++++++++++++++
A HTTP 401 error indicates the authentication process failed during the initial
connection. Some things to check for this are:

* Verify that the credentials are correct and set properly with
  ``ansible_user`` and ``ansible_password``

* The user is a member of the local Administrators group or has been explicitly
  been granted access. The connection test with the ``winrs`` command should
  rule this out

* The authentication option set by ``ansible_winrm_transport`` is enabled under
  ``Service\Auth\*``

* If running over HTTP and not HTTPS, use ``ntlm``, ``kerberos`` or ``credssp``
  with ``ansible_winrm_message_encryption: auto`` to enable message encryption.
  If using another auth option or the installed pywinrm version cannot be
  upgraded the ``Service\AllowUnencrypted`` can be set to ``true`` but this is
  not recommended

* Ensure the downstream packages ``pywinrm``, ``requests-ntlm``,
  ``requests-kerberos``, and/or ``requests-credssp`` are up to date with pip

* If using Kerberos authentication, check ``Service\Auth\CbtHardeningLevel`` is
  not set to ``Strict``

* When using Basic or Certificate auth, check the user set by ``ansible_user``
  is a local account and not a domain account. Domain accounts do not work over
  Basic and Certificate auth.

HTTP 500 Error
++++++++++++++
These errors indicate an error has occured with the WinRM service. Some things
to check for this are:

* Verify that the number of current open shells has not exceeded either
  ``WinRsMaxShellsPerUser`` or any of the other Winrs settings haven't been
  breached.

Time Out Errors
+++++++++++++++
These errors usually indicate an error with the network connection where
Ansible is unable to even reach the host. Some things to check for this are:

* The firewall is not set to block the WinRM port's it is listening on
* There is a WinRM listener enabled on the port and path set by the host vars
* The WinRM service ``winrm`` is started and running on the Windows host

.. seealso::

   :doc:`index`
       The documentation index
   :doc:`playbooks`
       An introduction to playbooks
   :doc:`playbooks_best_practices`
       Best practices advice
   `List of Windows Modules <http://docs.ansible.com/list_of_windows_modules.html>`_
       Windows specific module list, all implemented in PowerShell
   `User Mailing List <http://groups.google.com/group/ansible-project>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
