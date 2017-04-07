
# Powershell script to upgrade Server Win 7 SP1, 2008 R2, Win 8.1, Server 2012,  or Server 2012R2 to PowerShell 5.1
# Not needed on Windows 10 or Server 2016 as these windows versions
# are supplied with Powershell 5.1

# For versions before win 8.1 or server 2012,
# you will need to
#  Ensure latest service pack installed
#  Install .net 4.5.2
#  REMOVE Windows Management Framework 3.0 (WMF).

#  If any of the logic/information is wrong in this script
# please read https://msdn.microsoft.com/en-us/powershell/wmf/5.1/install-configure which is Microsoft's own guide to installing this update.

# At the time of writing, Ansible modules are expected to work on Powershell 3.0 or later. To make use of DSC resources and other powershell improvements, use
# this script to upgrade powershell (and Windows Managment Framework).
# This may be used by a sample playbook.  Refer to the windows
# documentation on docs.ansible.com for details.
#
# - hosts: windows
#   tasks:
#     - script: upgrade_to_ps51.ps1

# Get version of OS

# 6.0 is 2008 (sorry, too old for ps 5.1)
# 6.1 is 2008 R2 / Win 7 SP1
# 6.2 is 2012
# 6.3 is 2012 R2 / Win 8.1
# 10 is Win 10 / S2016

#Requires -version 3.0

function Expand-ZIPFile($file, $destination)
{
    $shell = New-Object -com shell.application
    $zip = $shell.NameSpace($file)
    foreach($item in $zip.items())
    {
        $shell.Namespace($destination).copyhere($item)
    }
}

function Download-File
{
    param ([string]$path, [string]$local)
    $client = new-object system.net.WebClient
    $client.Headers.Add("user-agent", "PowerShell")
    $client.downloadfile($path, $local)
}

$powershell_version = $PSVersionTable.psversion.ToString()
$os_version = [Environment]::OSVersion.Version.ToString()
$osmajor = [Environment]::OSVersion.Version.Major
$osminor = [Environment]::OSVersion.Version.Minor
$proc_architecture = $ENV:PROCESSOR_ARCHITECTURE
$ps51_url_base = "http://download.microsoft.com/download/6/F/5/6F5FF66C-6775-42B0-86C4-47D41F2DA187/"

$psmodulepath_before = $ENV:PSModulePath

# checks to make sure script is needed
if ($powershell_version -gt "5.1")
{
    write-host "Powershell 5.1 or later Installed already; You don't need this"
    Exit
}

# If the Operating System is above 6.2, then you already have PowerShell Version > 3
if ($osmajor -ge 10) # S2016 / Win 10
{
    Write-Host "OS is new; upgrade not needed."
    Exit
}
# If you are running s2008 you can't upgrade to ps 5.1.  Powershell 4 is still an option though.
if ($os_version -lt "6.1") # 2008
{
    Write-Host "It looks like you are running Windows Server 2008 or earlier version of Windows.  Sorry, only Server 2008 R2 and later can install powershell 5.1"
    Exit
}

# Script will attempt changes if it gets past this point.
# ensure download location
$powershellpath = $ENV:TEMP + "\ps51install"
if (!(Test-Path $powershellpath))
{
    New-Item -ItemType directory -Path $powershellpath
}

# Ensure we have .net 4.5.2 or later installed

# .net 4.5.2 installation instructions
# https://www.microsoft.com/en-ca/download/details.aspx?id=42642

# .net 4.5.2 installer
# https://download.microsoft.com/download/E/2/1/E21644B5-2DF2-47C2-91BD-63C560427900/NDP452-KB2901907-x86-x64-AllOS-ENU.exe

# logic for detecting .net version from https://exchangemaster.wordpress.com/2016/03/16/quick-method-to-determine-installed-version-of-net-framework/
# .NET Framework 4.5.2 release=379893

if ( (Get-ItemProperty HKLM:\SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full -Name Release).Release -lt 379893 )
{
    $download_url = "https://download.microsoft.com/download/E/2/1/E21644B5-2DF2-47C2-91BD-63C560427900/NDP452-KB2901907-x86-x64-AllOS-ENU.exe"
    $filename = $download_url.Split('/')[-1]
    Download-File $download_url "$powershellpath\$filename"
    ."$powershellpath\$filename" /quiet /norestart
}
#You may need to reboot after the .NET install if so just run the script again.

# determine processor architecture
if ($proc_architecture -eq "AMD64")
{
    $architecture = "x64"
}
else
{
    $architecture = "x86"
}

# work out which file to download
if ($osmajor -eq 6 -and $osminor -eq 1 -and $architecture -eq "x64" ) # 2008 R2 / Win 7 64 bit
{
    $filename = "Win7AndW2K8R2-KB3191566-x64.zip"
    $download_url = $ps51_url_base  + $filename
    $install_mode="zip"
}
elseif ($osmajor -eq 6 -and $osminor -eq 1 -and $architecture -eq "x86" ) #  Win 7 32 bit (there was no 32 bit version of S2008R2)
{
    $filename = "Win7-KB3191566-x86.zip"
    $download_url = $ps51_url_base  + $filename
    $install_mode="zip"
}
elseif ($osmajor -eq 6 -and $osminor -eq 2) # 2012
{
    $filename = "W2K12-KB3191564-" + $architecture + ".msu"
    $download_url = $ps51_url_base  + $filename
    $install_mode="msu"
}
elseif ($osmajor -eq 6 -and $osminor -eq 3) # 2012 R2 / 8.1
{
    $download_url = "http://download.microsoft.com/download/6/F/5/6F5FF66C-6775-42B0-86C4-47D41F2DA187/Win8.1AndW2K12R2-KB3191564-" + $architecture + ".msu"
    $install_mode="msu"
}
else
{
    # Nothing to do; In theory this point will never be reached.
    Exit
}

# do the download
#$filename = $download_url.Split('/')[-1]
download-file $download_url "$powershellpath\$filename"

# run msu to install (later windows versions)
If ($install_mode -eq "msu")
{
   Start-Process -FilePath "$powershellpath\$filename" -ArgumentList /quiet
   #Write-Host "Reboot machine to complete installation of Powershell 5.1"
   Write-Host "Waiting for msu installation to complete" # again I think this is asynchronous
   Start-Sleep -seconds 30
}
elseif ($install_mode -eq "zip") # unpack zip and run powershell script (earlier windows versions)
{
   # extract
   Try
   {
       Expand-ZipFile ("$powershellpath\$filename", "$powershellpath")
       # Generous pause added here as the unzip method used is asynchronous
       Start-Sleep -seconds 30
   }
   Catch
   {
       Write-Error  "Error unzipping $powershellpath\$filename to $powershellpath!"
       Exit(1)
   }

   # run the .ps1
   Invoke-Expression -Command $powershellpath\Install-Wmf5.1.ps1 -AcceptEula
   # This will fail unless you have

      # latest service pack installed
      # WMF 3.0 NOT installed
      # .NET Framework 4.5.2 installed  (should be handled above)
   # reboot
   Write-Host "You may need to run ConfigureRemotingForAnsible.ps1 as WinRM is not automatically enabled on older Windows versions"
   Write-Host "If you had ps module path customisations it may be useful to konw that your psmodule path was previously: $psmodulepath_before ."
   Write-Host "You may need to edit your profiles as this script will not change your psmodule path.  "
   Write-Host "For more information see the installation documentation at https://msdn.microsoft.com/en-us/powershell/wmf/5.1/install-configure "
}

# clean up
Remove-Item -Force $powershellpath

Write-Host "Reboot machine to complete installation of Powershell 5.1"
