.. _windows_setup:

Setting up a Windows Host
=========================
This document discusses the setup that is required before Ansible can communicate with a Microsoft Windows host.

.. contents::
   :local:

Host Requirements
`````````````````
For Ansible to communicate to a Windows host and use Windows modules, the
Windows host must meet these base requirements for connectivity:

* With Ansible you can generally manage Windows versions under the current and extended support from Microsoft. You can also manage desktop OSs including Windows 8.1, and 10, and server OSs including Windows Server 2012, 2012 R2, 2016, 2019, and 2022.

* You need to install PowerShell 3.0 or newer and at least .NET 4.0 on the Windows host.

* You need to create and activate a WinRM listener. More details, see `WinRM Setup <https://docs.ansible.com/ansible/latest//user_guide/windows_setup.html#winrm-listener>`_.

.. Note:: Some Ansible modules have additional requirements, such as a newer OS or PowerShell version. Consult the module documentation page to determine whether a host meets those requirements.

Upgrading PowerShell and .NET Framework
---------------------------------------
Ansible requires PowerShell version 3.0 and .NET Framework 4.0 or newer to function on older operating systems like Server 2008 and Windows 7. The base image does not meet this
requirement. You can use the `Upgrade-PowerShell.ps1 <https://github.com/jborean93/ansible-windows/blob/master/scripts/Upgrade-PowerShell.ps1>`_ script to update these.

This is an example of how to run this script from PowerShell:

.. code-block:: powershell

    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $url = "https://raw.githubusercontent.com/jborean93/ansible-windows/master/scripts/Upgrade-PowerShell.ps1"
    $file = "$env:temp\Upgrade-PowerShell.ps1"
    $username = "Administrator"
    $password = "Password"

    (New-Object -TypeName System.Net.WebClient).DownloadFile($url, $file)
    Set-ExecutionPolicy -ExecutionPolicy Unrestricted -Force

    &$file -Version 5.1 -Username $username -Password $password -Verbose

In the script, the ``file`` value can be the PowerShell version 3.0, 4.0, or 5.1.

Once completed, you need to run the following PowerShell commands:

1. As an optional but good security practice, you can set the execution policy back to the default.
   
.. code-block:: powershell

    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Force

Use the ``RemoteSigned`` value for Windows servers, or ``Restricted`` for Windows clients.

2. Remove the auto logon.
   
.. code-block:: powershell

    $reg_winlogon_path = "HKLM:\Software\Microsoft\Windows NT\CurrentVersion\Winlogon"
    Set-ItemProperty -Path $reg_winlogon_path -Name AutoAdminLogon -Value 0
    Remove-ItemProperty -Path $reg_winlogon_path -Name DefaultUserName -ErrorAction SilentlyContinue
    Remove-ItemProperty -Path $reg_winlogon_path -Name DefaultPassword -ErrorAction SilentlyContinue

The script determines what programs you need to install (such as .NET Framework 4.5.2) and what PowerShell version needs to be present. If a reboot is needed and the ``username`` and ``password`` parameters are set, the script will automatically reboot the machine and then logon. If the ``username`` and ``password`` parameters are not set, the script will prompt the user to manually reboot and logon when required. When the user is next logged in, the script will continue where it left off and the process continues until no more
actions are required.

.. Note:: If you run the script on Server 2008, then you need to install SP2. For Server 2008 R2 or Windows 7 you need SP1.

    On Windows Server 2008 you can install only PowerShell 3.0. A newer version will result in the script failure.

    The ``username`` and ``password`` parameters are stored in plain text in the registry. Run the cleanup commands after the script finishes to ensure no credentials are stored on the host.


WinRM Memory Hotfix
-------------------
On PowerShell v3.0, there is a bug that limits the amount of memory available to the WinRM service. Use the `Install-WMF3Hotfix.ps1 <https://github.com/jborean93/ansible-windows/blob/master/scripts/Install-WMF3Hotfix.ps1>`_ script to install a hotfix on affected hosts as part of the system bootstrapping or imaging process. Without this hotfix, Ansible fails to execute certain commands on the Windows host.

To install the hotfix:

.. code-block:: powershell

    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $url = "https://raw.githubusercontent.com/jborean93/ansible-windows/master/scripts/Install-WMF3Hotfix.ps1"
    $file = "$env:temp\Install-WMF3Hotfix.ps1"

    (New-Object -TypeName System.Net.WebClient).DownloadFile($url, $file)
    powershell.exe -ExecutionPolicy ByPass -File $file -Verbose

For more details, refer to the `"Out of memory" error on a computer that has a customized MaxMemoryPerShellMB quota set and has WMF 3.0 installed <https://support.microsoft.com/en-us/help/2842230/out-of-memory-error-on-a-computer-that-has-a-customized-maxmemorypersh>`_ article.

WinRM Setup
```````````
You need to configure the WinRM service so that Ansible can connect to it. There are two main components of the WinRM service that governs how Ansible can interface with the Windows host: the ``listener`` and the ``service`` configuration settings.

WinRM Listener
--------------
The WinRM services listen for requests on one or more ports. Each of these ports must have a listener created and configured.

To view the current listeners that are running on the WinRM service:

.. code-block:: powershell

    winrm enumerate winrm/config/Listener

This will output something like:

.. code-block:: powershell

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

In the example above there are two listeners activated. One is listening on port 5985 over HTTP and the other is listening on port 5986 over HTTPS. Some of the key options that are useful to understand are:

* ``Transport``: Whether the listener is run over HTTP or HTTPS. We recommend you use a listener over HTTPS because the data is encrypted without any further changes required.

* ``Port``: The port the listener runs on. By default it is ``5985`` for HTTP and ``5986`` for HTTPS. This port can be changed to whatever is required and corresponds to the host var ``ansible_port``.

* ``URLPrefix``: The URL prefix to listen on. By default it is ``wsman``. If you change this option, you need to set the host var ``ansible_winrm_path`` to the same value.

* ``CertificateThumbprint``: If you use an HTTPS listener, this is the thumbprint of the certificate in the Windows Certificate Store that is used in the connection. To get the details of the certificate itself, run this command with the relevant certificate thumbprint in PowerShell:

.. code-block:: powershell

    $thumbprint = "E6CDAA82EEAF2ECE8546E05DB7F3E01AA47D76CE"
    Get-ChildItem -Path cert:\LocalMachine\My -Recurse | Where-Object { $_.Thumbprint -eq $thumbprint } | Select-Object *

Setup WinRM Listener
++++++++++++++++++++
There are three ways to set up a WinRM listener:

* Using ``winrm quickconfig`` for HTTP or ``winrm quickconfig -transport:https`` for HTTPS. This is the easiest option to use when running outside of a domain environment and a simple listener is required. Unlike the other options, this process also has the added benefit of opening up the firewall for the ports required and starts the WinRM service.

* Using Group Policy Objects (GPO). This is the best way to create a listener when the host is a member of a domain because the configuration is done automatically without any user input. For more information on group policy objects, see the `Group Policy Objects documentation <https://msdn.microsoft.com/en-us/library/aa374162(v=vs.85).aspx>`_.

* Using PowerShell to create a listener with a specific configuration. This can be done by running the following PowerShell commands:

  .. code-block:: powershell

      $selector_set = @{
          Address = "*"
          Transport = "HTTPS"
      }
      $value_set = @{
          CertificateThumbprint = "E6CDAA82EEAF2ECE8546E05DB7F3E01AA47D76CE"
      }

      New-WSManInstance -ResourceURI "winrm/config/Listener" -SelectorSet $selector_set -ValueSet $value_set

  To see the other options with this PowerShell command, refer to the
  `New-WSManInstance <https://docs.microsoft.com/en-us/powershell/module/microsoft.wsman.management/new-wsmaninstance?view=powershell-5.1>`_ documentation.

.. Note:: When creating an HTTPS listener, you must create and store a certificate in the ``LocalMachine\My`` certificate store.

Delete WinRM Listener
+++++++++++++++++++++
* To remove all WinRM listeners:

.. code-block:: powershell

    Remove-Item -Path WSMan:\localhost\Listener\* -Recurse -Force

* To remove only those listeners that run over HTTPS:

.. code-block:: powershell

    Get-ChildItem -Path WSMan:\localhost\Listener | Where-Object { $_.Keys -contains "Transport=HTTPS" } | Remove-Item -Recurse -Force

.. Note:: The ``Keys`` object is an array of strings, so it can contain different values. By default, it contains a key for ``Transport=`` and ``Address=`` which correspond to the values from the ``winrm enumerate winrm/config/Listeners`` command.

WinRM Service Options
---------------------
You can control the behavior of the WinRM service component, including authentication options and memory settings.

To get an output of the current service configuration options, run the following command:

.. code-block:: powershell

    winrm get winrm/config/Service
    winrm get winrm/config/Winrs

This will output something like:

.. code-block:: powershell

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

You do not need to change the majority of these options. However, some of the important ones to know about are:

* ``Service\AllowUnencrypted`` - specifies whether WinRM will allow HTTP traffic without message encryption. Message level encryption is only possible when the ``ansible_winrm_transport`` variable is ``ntlm``, ``kerberos`` or ``credssp``. By default, this is ``false`` and you should only set it to ``true`` when debugging WinRM messages.

* ``Service\Auth\*`` - defines what authentication options you can use with the WinRM service. By default, ``Negotiate (NTLM)`` and ``Kerberos`` are enabled.

* ``Service\Auth\CbtHardeningLevel`` - specifies whether channel binding tokens are not verified (None), verified but not required (Relaxed), or verified and required (Strict). CBT is only used when connecting with NT LAN Manager (NTLM) or Kerberos over HTTPS.

* ``Service\CertificateThumbprint`` - thumbprint of the certificate for encrypting the TLS channel used with CredSSP authentication. By default, this is empty. A self-signed certificate is generated when the WinRM service starts and is used in the TLS process.

* ``Winrs\MaxShellRunTime`` - maximum time, in milliseconds, that a remote command is allowed to execute.

* ``Winrs\MaxMemoryPerShellMB`` - maximum amount of memory allocated per shell, including its child processes.

To modify a setting under the ``Service`` key in PowerShell, you need to provide a path to the option after ``winrm/config/Service``:

.. code-block:: powershell

    Set-Item -Path WSMan:\localhost\Service\{path} -Value {some_value}

For example, to change ``Service\Auth\CbtHardeningLevel``:

.. code-block:: powershell

    Set-Item -Path WSMan:\localhost\Service\Auth\CbtHardeningLevel -Value Strict

To modify a setting under the ``Winrs`` key in PowerShell, you need to provide a path to the option after ``winrm/config/Winrs``:

.. code-block:: powershell

    Set-Item -Path WSMan:\localhost\Shell\{path} -Value {some_value}

For example, to change ``Winrs\MaxShellRunTime``:

.. code-block:: powershell

    Set-Item -Path WSMan:\localhost\Shell\MaxShellRunTime -Value 2147483647

.. Note:: If you run the command in a domain environment, some of these options are set by
    GPO and cannot be changed on the host itself. When you configured a key with GPO, it contains the text ``[Source="GPO"]`` next to the value.

Common WinRM Issues
-------------------
WinRM has a wide range of configuration options, which makes its configuration complex. As a result, errors that Ansible displays could in fact be problems with the host setup instead.

To identify a host issue, run the following command from another Windows host to connect to the target Windows host.

* To test HTTP:

.. code-block:: powershell

    winrs -r:http://server:5985/wsman -u:Username -p:Password ipconfig

* To test HTTPS:

.. code-block:: powershell

    winrs -r:https://server:5986/wsman -u:Username -p:Password -ssl ipconfig

The command will fail if the certificate is not verifiable.
   
* To test HTTPS ignoring certificate verification:

.. code-block:: powershell

    $username = "Username"
    $password = ConvertTo-SecureString -String "Password" -AsPlainText -Force
    $cred = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $username, $password

    $session_option = New-PSSessionOption -SkipCACheck -SkipCNCheck -SkipRevocationCheck
    Invoke-Command -ComputerName server -UseSSL -ScriptBlock { ipconfig } -Credential $cred -SessionOption $session_option

If any of the above commands fail, the issue is probably related to the WinRM setup.

HTTP 401/Credentials Rejected
+++++++++++++++++++++++++++++
An HTTP 401 error indicates the authentication process failed during the initial
connection. You can check the following to troubleshoot:

* The credentials are correct and set properly in your inventory with the ``ansible_user`` and ``ansible_password`` variables.

* The user is a member of the local Administrators group, or has been explicitly granted access. You can perform a connection test with the ``winrs`` command to rule this out.

* The authentication option set by the ``ansible_winrm_transport`` variable is enabled under ``Service\Auth\*``.

* If running over HTTP and not HTTPS, use ``ntlm``, ``kerberos`` or ``credssp`` with the ``ansible_winrm_message_encryption: auto`` custom inventory variable to enable message encryption. If you use another authentication option, or if it is not possible to upgrade the installed ``pywinrm`` package, you can set ``Service\AllowUnencrypted`` to ``true``. This is recommended only for troubleshooting.

* The downstream packages ``pywinrm``, ``requests-ntlm``, ``requests-kerberos``, and/or ``requests-credssp`` are up to date using ``pip``.

* For Kerberos authentication, ensure that ``Service\Auth\CbtHardeningLevel`` is not set to ``Strict``.

* For Basic or Certificate authentication, make sure that the user is a local account. Domain accounts do not work with Basic and Certificate authentication.

HTTP 500 Error
++++++++++++++
An HTTP 500 error indicates a problem with the WinRM service. You can check the following to troubleshoot:

* The number of your currently open shells has not exceeded either ``WinRsMaxShellsPerUser``. Alternatively, you did not exceed any of the other Winrs quotas.

Timeout Errors
+++++++++++++++
Sometimes Ansible is unable to reach the host. These instances usually indicate a problem with the network connection. You can check the following to troubleshoot:

* The firewall is not set to block the configured WinRM listener ports.
* A WinRM listener is enabled on the port and path set by the host vars.
* The ``winrm`` service is running on the Windows host and is configured for the automatic start.

Connection Refused Errors
+++++++++++++++++++++++++
When you communicate with the WinRM service on the host you can encounter some problems. Check the following to help the troubleshooting:

* The WinRM service is up and running on the host. Use the ``(Get-Service -Name winrm).Status`` command to get the status of the service.
* The host firewall is allowing traffic over the WinRM port. By default this is ``5985`` for HTTP and ``5986`` for HTTPS.

Sometimes an installer may restart the WinRM or HTTP service and cause this error. The best way to deal with this is to use the ``win_psexec`` module from another Windows host.

Failure to Load Builtin Modules
+++++++++++++++++++++++++++++++
Sometimes PowerShell fails with an error message similar to:

.. code-block:: powershell

    The 'Out-String' command was found in the module 'Microsoft.PowerShell.Utility', but the module could not be loaded.

In that case, there could be a problem when trying to access all the paths specified by the ``PSModulePath`` environment variable.

A common cause of this issue is that ``PSModulePath`` contains a Universal Naming Convention (UNC) path to a file share. Additionally, the double hop/credential delegation issue causes that the Ansible process cannot access these folders. To work around this problem is to either:

* Remove the UNC path from ``PSModulePath``.
  
or

* Use an authentication option that supports credential delegation like ``credssp`` or ``kerberos``. You need to have the credential delegation enabled.

See `KB4076842 <https://support.microsoft.com/en-us/help/4076842>`_ for more information on this problem.

Windows SSH Setup
`````````````````
Ansible 2.8 has added an experimental SSH connection for Windows managed nodes.

.. warning::
    Use this feature at your own risk! Using SSH with Windows is experimental. This implementation may make
    backwards incompatible changes in future releases. The server-side components can be unreliable depending on your installed version.

Installing OpenSSH using Windows Settings
-----------------------------------------
You can use OpenSSH to connect Window 10 clients to Windows Server 2019. OpenSSH Client is available to install on Windows 10 build 1809 and later. OpenSSH Server is available to install on Windows Server 2019 and later.

For more information, refer to `Get started with OpenSSH for Windows <https://docs.microsoft.com/en-us/windows-server/administration/openssh/openssh_install_firstuse>`_.

Installing Win32-OpenSSH
------------------------
To install the `Win32-OpenSSH <https://github.com/PowerShell/Win32-OpenSSH>`_ service for use with
Ansible, select one of these installation options:

* Manually install ``Win32-OpenSSH``, following the `install instructions <https://github.com/PowerShell/Win32-OpenSSH/wiki/Install-Win32-OpenSSH>`_ from Microsoft.

* Use Chocolatey:

.. code-block:: powershell

    choco install --package-parameters=/SSHServerFeature openssh

* Use the ``win_chocolatey`` Ansible module:

.. code-block:: yaml

    - name: install the Win32-OpenSSH service
      win_chocolatey:
        name: openssh
        package_params: /SSHServerFeature
        state: present

* Install an Ansible Galaxy role for example `jborean93.win_openssh <https://galaxy.ansible.com/jborean93/win_openssh>`_:

.. code-block:: powershell

    ansible-galaxy install jborean93.win_openssh

* Use the role in your playbook:

.. code-block:: yaml

    - name: install Win32-OpenSSH service
      hosts: windows
      gather_facts: false
      roles:
      - role: jborean93.win_openssh
        opt_openssh_setup_service: True

.. note:: ``Win32-OpenSSH`` is still a beta product and is constantly being updated to include new features and bugfixes. If you use SSH as a connection option for Windows, we highly recommend you install the latest version.

Configuring the Win32-OpenSSH shell
-----------------------------------

By default ``Win32-OpenSSH`` uses ``cmd.exe`` as a shell.

* To configure a different shell, use an Ansible playbook with a task to define the registry setting:

.. code-block:: yaml

    - name: set the default shell to PowerShell
      win_regedit:
        path: HKLM:\SOFTWARE\OpenSSH
        name: DefaultShell
        data: C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe
        type: string
        state: present

* To revert the settings back to the default shell:

.. code-block:: yaml

    - name: set the default shell to cmd
      win_regedit:
        path: HKLM:\SOFTWARE\OpenSSH
        name: DefaultShell
        state: absent

Win32-OpenSSH Authentication
----------------------------
Win32-OpenSSH authentication with Windows is similar to SSH authentication on Unix/Linux hosts. You can use a plaintext password or SSH public key authentication.

For the key-based authentication:

* Add your public keys to an ``authorized_key`` file in the ``.ssh`` folder of the user's profile directory.

* Configure the SSH service using the ``sshd_config`` file.

When using SSH key authentication with Ansible, the remote session will not have access to user credentials and will fail when attempting to access a network resource. This is also known as the double-hop or credential delegation issue. To work around this problem:

* Use plaintext password authentication by setting the ``ansible_password`` variable.
* Use the ``become`` directive on the task with the credentials of the user that needs access to the remote resource.

Configuring Ansible for SSH on Windows
--------------------------------------
To configure Ansible to use SSH for Windows hosts, you must set two connection variables:

* set ``ansible_connection`` to ``ssh``
* set ``ansible_shell_type`` to ``cmd`` or ``powershell``

The ``ansible_shell_type`` variable should reflect the ``DefaultShell`` configured on the Windows host. Set ``ansible_shell_type`` to ``cmd`` for the default shell. Alternatively, set ``ansible_shell_type`` to ``powershell`` if you changed ``DefaultShell`` to PowerShell.

Known issues with SSH on Windows
--------------------------------
Using SSH with Windows is experimental. Currently existing issues are:

* Win32-OpenSSH versions older than ``v7.9.0.0p1-Beta`` do not work when ``powershell`` is the shell type.
* While Secure Copy Protocol (SCP) should work, SSH File Transfer Protocol (SFTP) is the recommended mechanism to use when copying or fetching a file.

.. seealso::

    :ref:`about_playbooks`
       An introduction to playbooks
    :ref:`playbooks_best_practices`
       Tips and tricks for playbooks
    :ref:`List of Windows Modules <windows_modules>`
       Windows specific module list, all implemented in PowerShell
    `User Mailing List <https://groups.google.com/group/ansible-project>`_
       Have a question?  Stop by the google group!
    :ref:`communication_irc`
       How to join Ansible chat channels
