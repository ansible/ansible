#!powershell
# This file is part of Ansible
#
# Copyright 2014, Trond Hindenes <trond@hindenes.com>
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.


# WANT_JSON
# POWERSHELL_COMMON

$params = Parse-Args $args;
$result = New-Object PSObject;
Set-Attr $result "changed" $false;

$package = Get-Attr -obj $params -name name -failifempty $true -emptyattributefailmessage "missing required argument: name"
$force = Get-Attr -obj $params -name force -default "false" | ConvertTo-Bool
$upgrade = Get-Attr -obj $params -name upgrade -default "false" | ConvertTo-Bool
$version = Get-Attr -obj $params -name version -default $null

$source = Get-Attr -obj $params -name source -default $null
if ($source) {$source = $source.Tolower()}

$showlog = Get-Attr -obj $params -name showlog -default "false" | ConvertTo-Bool
$state = Get-Attr -obj $params -name state -default "present"

$installargs = Get-Attr -obj $params -name install_args -default $null
$packageparams = Get-Attr -obj $params -name params -default $null
$ignoredependencies = Get-Attr -obj $params -name ignore_dependencies -default "false" | ConvertTo-Bool

if ("present","absent" -notcontains $state)
{
    Fail-Json $result "state is $state; must be present or absent"
}


Function Chocolatey-Install-Upgrade
{
    [CmdletBinding()]

    param()

    $ChocoAlreadyInstalled = get-command choco -ErrorAction 0
    if ($ChocoAlreadyInstalled -eq $null)
    {
        #We need to install chocolatey
        iex ((new-object net.webclient).DownloadString("https://chocolatey.org/install.ps1"))
        $result.changed = $true
        $script:executable = "C:\ProgramData\chocolatey\bin\choco.exe"
    }
    else
    {
        $script:executable = "choco.exe"

        if ((choco --version) -lt '0.9.9')
        {
            Choco-Upgrade chocolatey 
        }
    }
}


Function Choco-IsInstalled
{
    [CmdletBinding()]
    
    param(
        [Parameter(Mandatory=$true, Position=1)]
        [string]$package
    )

    $cmd = "$executable list --local-only $package"
    $results = invoke-expression $cmd

    if ($LastExitCode -ne 0)
    {
        Set-Attr $result "choco_error_cmd" $cmd
        Set-Attr $result "choco_error_log" "$results"
        
        Throw "Error checking installation status for $package" 
    } 
    
    If ("$results" -match "$package .* (\d+) packages installed.")
    {
        return $matches[1] -gt 0
    }
    
    $false
}

Function Choco-Upgrade 
{
    [CmdletBinding()]
    
    param(
        [Parameter(Mandatory=$true, Position=1)]
        [string]$package,
        [Parameter(Mandatory=$false, Position=2)]
        [string]$version,
        [Parameter(Mandatory=$false, Position=3)]
        [string]$source,
        [Parameter(Mandatory=$false, Position=4)]
        [bool]$force,
        [Parameter(Mandatory=$false, Position=5)]
        [string]$installargs,
        [Parameter(Mandatory=$false, Position=6)]
        [string]$packageparams,
        [Parameter(Mandatory=$false, Position=7)]
        [bool]$ignoredependencies
    )

    if (-not (Choco-IsInstalled $package))
    {
        throw "$package is not installed, you cannot upgrade"
    }

    $cmd = "$executable upgrade -dv -y $package"

    if ($version)
    {
        $cmd += " -version $version"
    }

    if ($source)
    {
        $cmd += " -source $source"
    }

    if ($force)
    {
        $cmd += " -force"
    }

    if ($installargs)
    {
        $cmd += " -installargs '$installargs'"
    }

    if ($packageparams)
    {
        $cmd += " -params '$packageparams'"
    }

    if ($ignoredependencies)
    {
        $cmd += " -ignoredependencies"
    }

    $results = invoke-expression $cmd

    if ($LastExitCode -ne 0)
    {
        Set-Attr $result "choco_error_cmd" $cmd
        Set-Attr $result "choco_error_log" "$results"
        Throw "Error installing $package" 
    }

    if ("$results" -match ' upgraded (\d+)/\d+ package\(s\)\. ')
    {
        if ($matches[1] -gt 0)
        {
            $result.changed = $true
        }
    }
}

Function Choco-Install 
{
    [CmdletBinding()]
    
    param(
        [Parameter(Mandatory=$true, Position=1)]
        [string]$package,
        [Parameter(Mandatory=$false, Position=2)]
        [string]$version,
        [Parameter(Mandatory=$false, Position=3)]
        [string]$source,
        [Parameter(Mandatory=$false, Position=4)]
        [bool]$force,
        [Parameter(Mandatory=$false, Position=5)]
        [bool]$upgrade,
        [Parameter(Mandatory=$false, Position=6)]
        [string]$installargs,
        [Parameter(Mandatory=$false, Position=7)]
        [string]$packageparams,
        [Parameter(Mandatory=$false, Position=8)]
        [bool]$ignoredependencies
    )

    if (Choco-IsInstalled $package)
    {
        if ($upgrade)
        {
            Choco-Upgrade -package $package -version $version -source $source -force $force `
                -installargs $installargs -packageparams $packageparams `
                -ignoredependencies $ignoredependencies
        }

        return
    }

    $cmd = "$executable install -dv -y $package"

    if ($version)
    {
        $cmd += " -version $version"
    }

    if ($source)
    {
        $cmd += " -source $source"
    }

    if ($force)
    {
        $cmd += " -force"
    }

    if ($installargs)
    {
        $cmd += " -installargs '$installargs'"
    }

    if ($packageparams)
    {
        $cmd += " -params '$packageparams'"
    }

    if ($ignoredependencies)
    {
        $cmd += " -ignoredependencies"
    }

    $results = invoke-expression $cmd

    if ($LastExitCode -ne 0)
    {
        Set-Attr $result "choco_error_cmd" $cmd
        Set-Attr $result "choco_error_log" "$results"
        Throw "Error installing $package" 
    }

     $result.changed = $true
}

Function Choco-Uninstall 
{
    [CmdletBinding()]
    
    param(
        [Parameter(Mandatory=$true, Position=1)]
        [string]$package,
        [Parameter(Mandatory=$false, Position=2)]
        [string]$version,
        [Parameter(Mandatory=$false, Position=3)]
        [bool]$force
    )

    if (-not (Choco-IsInstalled $package))
    {
        return
    }

    $cmd = "$executable uninstall -dv -y $package"

    if ($version)
    {
        $cmd += " -version $version"
    }

    if ($force)
    {
        $cmd += " -force"
    }

    $results = invoke-expression $cmd

    if ($LastExitCode -ne 0)
    {
        Set-Attr $result "choco_error_cmd" $cmd
        Set-Attr $result "choco_error_log" "$results"
        Throw "Error uninstalling $package" 
    }

     $result.changed = $true
}
Try
{
    Chocolatey-Install-Upgrade

    if ($state -eq "present")
    {
        Choco-Install -package $package -version $version -source $source `
            -force $force -upgrade $upgrade -installargs $installargs `
            -packageparams $packageparams -ignoredependencies $ignoredependencies
    }
    else
    {
        Choco-Uninstall -package $package -version $version -force $force
    }

    Exit-Json $result;
}
Catch
{
     Fail-Json $result $_.Exception.Message
}

