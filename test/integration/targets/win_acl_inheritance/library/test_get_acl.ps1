#!powershell

# WANT_JSON
# POWERSHELL_COMMON

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$params = Parse-Args $args -supports_check_mode $false
$path = Get-AnsibleParam -obj $params "path" -type "path" -failifempty $true

$result = @{
    changed = $false
}

$acl = Get-Acl -LiteralPath $path

$result.inherited = $acl.AreAccessRulesProtected -eq $false

$user_details = @{}
$acl.Access | ForEach-Object {
    $user = $_.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value
    if ($user_details.ContainsKey($user)) {
        $details = $user_details.$user
    } else {
        $details = @{
            isinherited = $false
        }
    }
    $details.isinherited = $_.IsInherited
    $user_details.$user = $details
}

$result.user_details = $user_details

Exit-Json $result
