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

.. note:: While these are the base requirements some modules have separate
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

    $url = "https://github.com/ansible/ansible/blah.ps1"
    $file = "$env:SystemDrive\temp\upgrade_powershell.ps1"
    $username = "Administrator"
    $password = "Password"

    (New-Object -TypeName System.Net.WebClient).DownloadFile($url, $file)
    Set-ExecutionPolicy -ExecutionPolicy Unrestricted
    &$file -target_version 5.1 -username $username -password $password -Verbose

Once complete, the following commands should be run to remove the auto logon
from powershell:

.. code-block:: powershell

    Set-ItemProperty -Path $reg_winlogon_path -Name AutoAdminLogon -Value 0
    Remove-ItemProperty -Path $reg_winlogon_path -Name DefaultUserName -ErrorAction SilentlyContinue
    Remove-ItemProperty -Path $reg_winlogon_path -Name DefaultPassword -ErrorAction SilentlyContinue

When running the script, the ``-target_version`` parameter set's the version of
powershell to install and it can be from ``3.0``, ``4.0``, or ``5.1``. The
username and password of an admin account of that host must also be set. This
is so the script can reboot the host when required during the install process.
If these parameters are not set then a reboot must be done manually and a user
must log on after the reboot to continue the script if required.

.. Note:: If running on Server 2008, then SP2 must be installed before .NET 4.0
    and Powershell 3.0 can be installed. If running on Server 2008 R2 or
    Windows 7, then SP1 must be installed.

.. Note:: Windows Server 2008 can only install Powershell 3.0, specifying a
    newer version will result in the script failing.

.. _upgrade powershell.ps1: https://github.com/ansible/ansible/blah.ps1

WinRM Memory Hotfix
-------------------
There is a bug with the WinRM service on Windows Server 2008, 2008 R2, 2012, and
Windows 7 that limits the amount of memory available to the service. Without
this hotfix installed, Ansible will fail to execute certain commands on the
Windows host. It is highly recommended these hotfixes are installed as part of
the system bootstapping or imaging process.

The following powershell command will install the hotfix:

.. code-block:: powershell
    $tmp_dir = "$env:SystemDrive\temp"
    $os_version = [Environment]::OSVersion.Version
    $host_string = "$($os_version.Major).$($os_version.Minor)-$($env:PROCESSOR_ARCHITECTURE)"
    switch($host_string) {
        "6.0-x86" {
            $url = "http://hotfixv4.microsoft.com/Windows%20Vista/sp3/Fix467401/6000/free/464091_intl_i386_zip.exe"
        }
        "6.0-AMD64" {
            $url = "http://hotfixv4.microsoft.com/Windows%20Vista/sp3/Fix467401/6000/free/464090_intl_x64_zip.exe"
        }
        "6.1-x86" {
            $url = "http://hotfixv4.microsoft.com/Windows%207/Windows%20Server2008%20R2%20SP1/sp2/Fix467402/7600/free/463983_intl_i386_zip.exe"
        }
        "6.1-AMD64" {
            $url = "http://hotfixv4.microsoft.com/Windows%207/Windows%20Server2008%20R2%20SP1/sp2/Fix467402/7600/free/463984_intl_x64_zip.exe"
        }
        "6.2-x86" {
            $url = "http://hotfixv4.microsoft.com/Windows%208%20RTM/nosp/Fix452763/9200/free/463940_intl_i386_zip.exe"
        }
        "6.2-AMD64" {
            $url = "http://hotfixv4.microsoft.com/Windows%208%20RTM/nosp/Fix452763/9200/free/463941_intl_x64_zip.exe"
        }
    }
    $filename = $hotfix_url.Split("/")[-1]
    $compressed_file = "$tmp_dir\$($filename).zip"
    (New-Object -TypeName System.Net.WebClient).DownloadFile($url, $compressed_file)

    $shell = New-Object -ComObject Shell.Application
    $zip_src = $shell.NameSpace($compressed_file)
    $zip_dest = $shell.NameSpace($tmp_dir)
    foreach ($entry in $zip_src.Items()) {
        $hotfix_filename = "$($entry.Name).msu"
        $zip_dest.CopyHere($entry, 1044)
    }
    $file = "$tmp_dir\$hotfix_filename"
    &$file /quiet /norestart
    $rc = $LASTEXITCODE
    if ($rc -ne 0 -and $rc -ne 3010) {
        throw "failed to install hotfix: exit code $exit_code"
    }
    if ($rc -eq 3010) {
        Write-Host "reboot is required to complete install"
    }

WinRM Host Setup
````````````````
TODO: information about setting up a WinRM listener. The below is a copy from intro_windows.rst

Setup WinRM Listener
--------------------
TODO

WinRM Configuration Options
---------------------------
TODO
