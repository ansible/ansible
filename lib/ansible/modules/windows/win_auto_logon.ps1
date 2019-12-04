#!powershell

# Copyright: (c) 2019, Prasoon Karunan V (@prasoonkarunan) <kvprasoon@Live.in>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


# All helper methods are written in a binary module and has to be loaded for consuming them.
#AnsibleRequires -CSharpUtil Ansible.Basic

Set-StrictMode -Version 2.0

$spec = @{
    options = @{
        password = @{type = "str"; no_log = $true}
        state = @{type = "str"; choices = "absent","present"; default = "present"}
        username = @{type = "str"}
    }
    required_if = @(
        , @("state", "present", @("username", "password"))
    )
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)
$password = $module.params.password
$state = $module.params.state
$username = $module.params.username
$domain = $null

if ($username) {
    # Try and get the Netlogon form of the username specified. Translating to and from a SID gives us an NTAccount
    # in the Netlogon form that we desire.
    $ntAccount = New-Object -TypeName System.Security.Principal.NTAccount -ArgumentList $username
    try {
        $accountSid = $ntAccount.Translate([System.Security.Principal.SecurityIdentifier])
    } catch [System.Security.Principal.IdentityNotMappedException] {
        $module.FailJson("Failed to find a local or domain user with the name '$username'", $_)
    }
    $ntAccount = $accountSid.Translate([System.Security.Principal.NTAccount])

    $domain, $username = $ntAccount.Value -split '\\'
}

#Build ParamHash

$autoAdminLogon = 1
if($state -eq 'absent'){
    $autoadminlogon = 0
}
$autoLogonKeyList   = @{
    DefaultPassword = $password
    DefaultUserName = $username
    DefaultDomain   = $domain
    AutoAdminLogon  = $autoAdminLogon
}
$actionTaken = $null
$autoLogonRegPath   = 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon\'
$autoLogonKeyRegList   = Get-ItemProperty -LiteralPath $autoLogonRegPath -Name $autoLogonKeyList.GetEnumerator().Name -ErrorAction SilentlyContinue

Foreach($key in $autoLogonKeyList.GetEnumerator().Name){
    $currentKeyValue = $autoLogonKeyRegList | Select-Object -ExpandProperty $key -ErrorAction SilentlyContinue
    if (-not [String]::IsNullOrEmpty($currentKeyValue)) {
        $expectedValue = $autoLogonKeyList[$key]
        if(($state -eq 'present') -and ($currentKeyValue -ne $expectedValue)) {
            Set-ItemProperty -LiteralPath $autoLogonRegPath -Name $key -Value $autoLogonKeyList[$key] -Force
            $actionTaken = $true
        }
        elseif($state -eq 'absent') {
            $actionTaken = $true
            Remove-ItemProperty -LiteralPath  $autoLogonRegPath -Name $key -Force
        }
    }
    else {
        if ($state -eq 'present') {
            $actionTaken = $true
            New-ItemProperty -LiteralPath $autoLogonRegPath -Name $key -Value $autoLogonKeyList[$key] -Force | Out-Null
        }
    }
}
if($actionTaken){
    $module.Result.changed = $true
}

$module.ExitJson()
