# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

Function Find-AnsibleModule {
    <#
    .SYNOPSIS
    Find the full path to the Ansible module specified.

    .PARAMETER Name
    [System.String] The name of the module to find.

    .EXAMPLE
    Find-AnsibleModule -Name win_ping

    Find-AnsibleModule -Name win_ping.ps1

    .OUTPUTS
    [System.String] The full path to the module specified
    #>
    [CmdletBinding()]
    [OutputType([System.String])]
    param (
        [Parameter(Mandatory=$true)][System.String]$Name
    )

    # Ensure the module name has an extension
    if ([System.IO.Path]::GetExtension($Name) -eq "") {
        $Name = "$($Name).ps1"
    }

    # Get the full path of the windows modules directory relative to this script
    $modules_path = [System.IO.Path]::GetFullPath(
        [System.IO.Path]::Combine($PSScriptRoot, "..", "..", "lib", "ansible", "modules", "windows")
    )
    $module = Get-ChildItem -LiteralPath $modules_path -Filter $Name -Recurse

    if ($null -eq $module) {
        Write-Error -Message "Failed to find Windows module '$Name' in '$modules_path'" -Category ObjectNotFound
    } else {
        return $module.FullName
    }
}
