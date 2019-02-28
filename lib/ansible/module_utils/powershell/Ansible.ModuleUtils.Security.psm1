<#
    .SYNOPSIS
    Save the username and the encrypted password as PSCredential object
    .Parameter username
    Username of the user which will use for the action
    .Parameter password
    Password of the user which is used for the action
#>
function Create-Credential {
    [CmdletBinding()] param([Parameter(Mandatory = $true)][string] $username, [Parameter(Mandatory = $true)][string] $password)   
    Write-DebugLog "Preparing credentials..."
    $passwordEncrypted = ConvertTo-SecureString -String $password -AsPlainText -Force
    $credentials = New-Object System.Management.Automation.PSCredential($username, $passwordEncrypted)
    Write-DebugLog "Prepared credentials"
    return $credentials
}