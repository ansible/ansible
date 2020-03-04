#Requires -Version 5.0 -Modules CimCmdlets

Function Get-TargetResource
{
    [CmdletBinding()]
    [OutputType([Hashtable])]
    param(
        [Parameter(Mandatory=$true)]
        [ValidateNotNullOrEmpty()]
        [String]$KeyParam
    )
    return @{Value = [bool]$global:DSCMachineStatus}
}

Function Set-TargetResource
{
    [CmdletBinding()]
    param (
        [Parameter(Mandatory=$true)]
        [ValidateNotNullOrEmpty()]
        [String]$KeyParam,
        [Bool]$Value = $true
    )
    $global:DSCMachineStatus = [int]$Value
}

Function Test-TargetResource
{
    [CmdletBinding()]
    [OutputType([Boolean])]
    param (
        [Parameter(Mandatory=$true)]
        [ValidateNotNullOrEmpty()]
        [String]$KeyParam,
        [Bool]$Value = $true
    )
    $false
}

Export-ModuleMember -Function *-TargetResource

