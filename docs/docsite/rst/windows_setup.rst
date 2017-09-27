Ansible Windows Setup
=====================
Before Ansible can communicate with a Windows host, there may be some setup
required on the host to enable this.

..contents:: Topics

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
requirement. The script update powershell.ps1_ can be used to install whatever
powershell version that is set along with the required .NET Framework alongside
it.

This is an example of how to run this script from powershell:

.. code-block:: powershell

    $url = "https://raw.githubusercontent.com/ansible/ansible/devel/examples/scripts/update_powershell.ps1"
    $file = "$env:SystemDrive\temp\update_powershell.ps1"
    $username = "Administrator"
    $password = "Password"

    (New-Object -TypeName System.Net.WebClient).DownloadFile($url, $file)
    Set-ExecutionPolicy -ExecutionPolicy Unrestricted -Force

    # target_version can be 3.0, 4.0 or 5.1
    &$file -target_version 5.1 -username $username -password $password -Verbose

Once complete, the following commands should be run to remove the auto logon
and set the execution policy from powershell:

.. code-block:: powershell

    # this isn't needed but is a good security practice to complete
    Set-ExecutionPolicy -ExecutionPolicy Restricted -Force
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

.. _upgrade powershell.ps1: https://github.com/ansible/ansible/blob/devel/examples/scripts/update_powershell.ps1

WinRM Memory Hotfix
-------------------
When running on Powershell v3.0, there is a bug with the WinRM service on
Windows Server 2008, 2008 R2, 2012, and Windows 7 that limits the amount of
memory available to the service. Without this hotfix installed, Ansible will
fail to execute certain commands on the Windows host. It is highly recommended
these hotfixes are installed as part of the system bootstapping or imaging
process. The script winrm hotfix.ps1_ can be used to install the hotfix on
affected hosts.

The following powershell command will install the hotfix:

.. code-block:: powershell

    $url = "https://raw.githubusercontent.com/ansible/ansible/devel/examples/scripts/winrm_hotfix.ps1"
    $file = "$env:SystemDrive\temp\winrm_hotfix.ps1"

    (New-Object -TypeName System.Net.WebClient).DownloadFile($url, $file)
    powershell.exe -ExecutionPolicy ByPass -File $file -Verbose

.. _winrm hotfix.ps1: https://github.com/ansible/ansible/blob/devel/examples/scripts/winrm_hotfix.ps1

WinRM Host Setup
````````````````
Once powershell has been upgraded to at least 3.0, the final step is for the
WinRM service to be configured so that Ansible can connect to it. Before

Setup WinRM Listener
--------------------
TODO

WinRM Configuration Options
---------------------------
TODO
