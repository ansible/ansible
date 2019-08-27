#!powershell

# Copyright: (c) 2015, Peter Mounce <public@neverrunwithscissors.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = "Stop"

Function Find-Command
{
    [CmdletBinding()]
    param(
      [Parameter(Mandatory=$true, Position=0)] [string] $command
    )
    $installed = get-command $command -erroraction Ignore
    write-verbose "$installed"
    if ($installed)
    {
        return $installed
    }
    return $null
}

Function Find-WebPiCmd
{
    [CmdletBinding()]
    param()
    $p = Find-Command "webpicmd.exe"
    if ($null -ne $p)
    {
        return $p
    }
    $a = Find-Command "c:\programdata\chocolatey\bin\webpicmd.exe"
    if ($null -ne $a)
    {
        return $a
    }
    Throw "webpicmd.exe is not installed. It must be installed (use chocolatey)"
}

Function Test-IsInstalledFromWebPI
{
    [CmdletBinding()]

    param(
        [Parameter(Mandatory=$true, Position=0)]
        [string]$package
    )

    $cmd = "$executable /list /listoption:installed"
    $results = invoke-expression $cmd

    if ($LastExitCode -ne 0)
    {
        $result.webpicmd_error_cmd = $cmd
        $result.webpicmd_error_log = "$results"

        Throw "Error checking installation status for $package"
    }
    Write-Verbose "$results"

    if ($results -match "^$package\s+")
    {
        return $true
    }

    return $false
}

Function Install-WithWebPICmd
{
    [CmdletBinding()]

    param(
        [Parameter(Mandatory=$true, Position=0)]
        [string]$package
    )

    $cmd = "$executable /install /products:$package /accepteula /suppressreboot"

    $results = invoke-expression $cmd

    if ($LastExitCode -ne 0)
    {
        $result.webpicmd_error_cmd = $cmd
        $result.webpicmd_error_log = "$results"
        Throw "Error installing $package"
    }

    write-verbose "$results"

    if ($results -match "Install of Products: SUCCESS")
    {
        $result.changed = $true
    }
}

$result = @{
    changed = $false
}

$params = Parse-Args $args

$package = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true

Try {
    $script:executable = Find-WebPiCmd
    if ((Test-IsInstalledFromWebPI -package $package) -eq $false) {
        Install-WithWebPICmd -package $package
    }

    Exit-Json $result
} Catch {
     Fail-Json $result $_.Exception.Message
}
