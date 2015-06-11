
# Powershell script to upgrade a PowerShell 2.0 system to PowerShell 3.0
# based on http://occasionalutility.blogspot.com/2013/11/everyday-powershell-part-7-powershell.html
#
# some Ansible modules that may use Powershell 3 features, so systems may need
# to be upgraded.  This may be used by a sample playbook.  Refer to the windows
# documentation on docs.ansible.com for details.
# 
# - hosts: windows
#   tasks:
#     - script: upgrade_to_ps3.ps1

# Get version of OS

# 6.0 is 2008
# 6.1 is 2008 R2
# 6.2 is 2012
# 6.3 is 2012 R2


if ($PSVersionTable.psversion.Major -ge 3)
{
    write-host "Powershell 3 Installed already; You don't need this"
    Exit
}

$powershellpath = "C:\powershell"

function download-file
{
    param ([string]$path, [string]$local)
    $client = new-object system.net.WebClient
    $client.Headers.Add("user-agent", "PowerShell")
    $client.downloadfile($path, $local)
}

if (!(test-path $powershellpath))
{
    New-Item -ItemType directory -Path $powershellpath
}


# .NET Framework 4.0 is necessary.

#if (($PSVersionTable.CLRVersion.Major) -lt 2)
#{
#    $DownloadUrl = "http://download.microsoft.com/download/B/A/4/BA4A7E71-2906-4B2D-A0E1-80CF16844F5F/dotNetFx45_Full_x86_x64.exe"
#    $FileName = $DownLoadUrl.Split('/')[-1]
#    download-file $downloadurl "$powershellpath\$filename"
#    ."$powershellpath\$filename" /quiet /norestart
#}

#You may need to reboot after the .NET install if so just run the script again.

# If the Operating System is above 6.2, then you already have PowerShell Version > 3
if ([Environment]::OSVersion.Version.Major -gt 6)
{
    write-host "OS is new; upgrade not needed."
    Exit
}


$osminor = [environment]::OSVersion.Version.Minor

$architecture = $ENV:PROCESSOR_ARCHITECTURE

if ($architecture -eq "AMD64")
{
    $architecture = "x64"
}  
else
{
    $architecture = "x86" 
} 

if ($osminor -eq 1)
{
    $DownloadUrl = "http://download.microsoft.com/download/E/7/6/E76850B8-DA6E-4FF5-8CCE-A24FC513FD16/Windows6.1-KB2506143-" + $architecture + ".msu"
}
elseif ($osminor -eq 0)
{
    $DownloadUrl = "http://download.microsoft.com/download/E/7/6/E76850B8-DA6E-4FF5-8CCE-A24FC513FD16/Windows6.0-KB2506146-" + $architecture + ".msu"
}
else
{
    # Nothing to do; In theory this point will never be reached.
    Exit
}

$FileName = $DownLoadUrl.Split('/')[-1]
download-file $downloadurl "$powershellpath\$filename"

Start-Process -FilePath "$powershellpath\$filename" -ArgumentList /quiet
