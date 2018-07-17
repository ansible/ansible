#!powershell

# Copyright: (c) 2014, Timothy Vandenbrande <timothy.vandenbrande@gmail.com>
# Copyright: (c) 2017, Artem Zinenko <zinenkoartem@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

function Parse-ProtocolType {
    param($protocol)

    $protocolNumber = $protocol -as [int]
    if ($protocolNumber -is [int]) {
        return $protocolNumber
    }

    switch -wildcard ($protocol) {
        "tcp" { return [System.Net.Sockets.ProtocolType]::Tcp -as [int] }
        "udp" { return [System.Net.Sockets.ProtocolType]::Udp -as [int] }
        "icmpv4*" { return [System.Net.Sockets.ProtocolType]::Icmp -as [int] }
        "icmpv6*" { return [System.Net.Sockets.ProtocolType]::IcmpV6 -as [int] }
        default { throw "Unknown protocol '$protocol'." }
    }
}

# See 'Direction' constants here: https://msdn.microsoft.com/en-us/library/windows/desktop/aa364724(v=vs.85).aspx
function Parse-Direction {
    param($directionStr)

    switch ($directionStr) {
        "in" { return 1 }
        "out" { return 2 }
        default { throw "Unknown direction '$directionStr'." }
    }
}

# See 'Action' constants here: https://msdn.microsoft.com/en-us/library/windows/desktop/aa364724(v=vs.85).aspx
function Parse-Action {
    param($actionStr)

    switch ($actionStr) {
        "block" { return 0 }
        "allow" { return 1 }
        default { throw "Unknown action '$actionStr'." }
    }
}

# Profile enum values: https://msdn.microsoft.com/en-us/library/windows/desktop/aa366303(v=vs.85).aspx
function Parse-Profiles
{
    param($profilesList)

    $profiles = ($profilesList | Select -uniq | ForEach {
        switch ($_) {
            "domain" { return 1 }
            "private" { return 2 }
            "public" { return 4 }
            default { throw "Unknown profile '$_'." }
        }
    } | Measure-Object -Sum).Sum

    if ($profiles -eq 7) { return 0x7fffffff }
    return $profiles
}

function Parse-InterfaceTypes
{
    param($interfaceTypes)

    return ($interfaceTypes | Select -uniq | ForEach {
        switch ($_) {
            "wireless" { return "Wireless" }
            "lan" { return "Lan" }
            "ras" { return "RemoteAccess" }
            default { throw "Unknown interface type '$_'." }
        }
    }) -Join ","
}

function Parse-EdgeTraversalOptions
{
    param($edgeTraversalOptionsStr)

    switch ($edgeTraversalOptionsStr) {
        "yes" { return 1 }
        "deferapp" { return 2 }
        "deferuser" { return 3 }
        default { throw "Unknown edge traversal options '$edgeTraversalOptionsStr'." }
    }
}

function Parse-SecureFlags
{
    param($secureFlagsStr)

    switch ($secureFlagsStr) {
        "authnoencap" { return 1 }
        "authenticate" { return 2 }
        "authdynenc" { return 3 }
        "authenc" { return 4 }
        default { throw "Unknown secure flags '$secureFlagsStr'." }
    }
}

function New-FWRule
{
    param (
        [string]$name,
        [string]$description,
        [string]$applicationName,
        [string]$serviceName,
        [string]$protocol,
        [string]$localPorts,
        [string]$remotePorts,
        [string]$localAddresses,
        [string]$remoteAddresses,
        [string]$direction,
        [string]$action,
        [bool]$enabled,
        [string[]]$profiles,
        [string[]]$interfaceTypes,
        [string]$edgeTraversalOptions,
        [string]$secureFlags
    )

    # INetFwRule interface description: https://msdn.microsoft.com/en-us/library/windows/desktop/aa365344(v=vs.85).aspx
    $rule = New-Object -ComObject HNetCfg.FWRule
    $rule.Name = $name
    $rule.Enabled = $enabled
    if ($description) { $rule.Description = $description }
    if ($applicationName) { $rule.ApplicationName = $applicationName }
    if ($serviceName) { $rule.ServiceName = $serviceName }
    if ($protocol -and $protocol -ne "any") { $rule.Protocol = Parse-ProtocolType -protocol $protocol }
    if ($localPorts -and $localPorts -ne "any") { $rule.LocalPorts = $localPorts }
    if ($remotePorts -and $remotePorts -ne "any") { $rule.RemotePorts = $remotePorts }
    if ($localAddresses -and $localAddresses -ne "any") { $rule.LocalAddresses = $localAddresses }
    if ($remoteAddresses -and $remoteAddresses -ne "any") { $rule.RemoteAddresses = $remoteAddresses }
    if ($direction) { $rule.Direction = Parse-Direction -directionStr $direction }
    if ($action) { $rule.Action = Parse-Action -actionStr $action }
    # Profiles value cannot be a uint32, but the "all profiles" value (0x7FFFFFFF) will often become a uint32, so must cast to [int]
    if ($profiles) { $rule.Profiles = [int](Parse-Profiles -profilesList $profiles) }
    if ($interfaceTypes -and @(Compare-Object $interfaceTypes @("any")).Count -ne 0) { $rule.InterfaceTypes = Parse-InterfaceTypes -interfaceTypes $interfaceTypes }
    if ($edgeTraversalOptions -and $edgeTraversalOptions -ne "no") {
        # EdgeTraversalOptions property exists only from Windows 7/Windows Server 2008 R2: https://msdn.microsoft.com/en-us/library/windows/desktop/dd607256(v=vs.85).aspx
        if ($rule | Get-Member -Name 'EdgeTraversalOptions') {
            $rule.EdgeTraversalOptions = Parse-EdgeTraversalOptions -edgeTraversalOptionsStr $edgeTraversalOptions
        }
    }
    if ($secureFlags -and $secureFlags -ne "notrequired") {
        # SecureFlags property exists only from Windows 8/Windows Server 2012: https://msdn.microsoft.com/en-us/library/windows/desktop/hh447465(v=vs.85).aspx
        if ($rule | Get-Member -Name 'SecureFlags') {
            $rule.SecureFlags = Parse-SecureFlags -secureFlagsStr $secureFlags
        }
    }

    return $rule
}

$ErrorActionPreference = "Stop"

$result = @{
    changed = $false
}

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$diff_support = Get-AnsibleParam -obj $params -name "_ansible_diff" -type "bool" -default $false

$name = Get-AnsibleParam -obj $params -name "name" -failifempty $true
$description = Get-AnsibleParam -obj $params -name "description" -type "str"
$direction = Get-AnsibleParam -obj $params -name "direction" -type "str" -failifempty $true -validateset "in","out"
$action = Get-AnsibleParam -obj $params -name "action" -type "str" -failifempty $true -validateset "allow","block","bypass"
$program = Get-AnsibleParam -obj $params -name "program" -type "str"
$service = Get-AnsibleParam -obj $params -name "service" -type "str"
$enabled = Get-AnsibleParam -obj $params -name "enabled" -type "bool" -default $true -aliases "enable"
$profiles = Get-AnsibleParam -obj $params -name "profiles" -type "list" -default @("domain", "private", "public") -aliases "profile"
$localip = Get-AnsibleParam -obj $params -name "localip" -type "str" -default "any"
$remoteip = Get-AnsibleParam -obj $params -name "remoteip" -type "str" -default "any"
$localport = Get-AnsibleParam -obj $params -name "localport" -type "str"
$remoteport = Get-AnsibleParam -obj $params -name "remoteport" -type "str"
$protocol = Get-AnsibleParam -obj $params -name "protocol" -type "str" -default "any"
$interfacetypes = Get-AnsibleParam -obj $params -name "interfacetypes" -type "list" -default @("any")
$edge = Get-AnsibleParam -obj $params -name "edge" -type "str" -default "no" -validateset "no","yes","deferapp","deferuser"
$security = Get-AnsibleParam -obj $params -name "security" -type "str" -default "notrequired" -validateset "notrequired","authnoencap","authenticate","authdynenc","authenc"

$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present","absent"

$force = Get-AnsibleParam -obj $params -name "force" -type "bool" -default $false
if ($force) {
    Add-DeprecationWarning -obj $result -message "'force' isn't required anymore" -version 2.9
}

if ($diff_support) {
    $result.diff = @{}
    $result.diff.prepared = ""
}

try {
    $fw = New-Object -ComObject HNetCfg.FwPolicy2

    $existingRule = $fw.Rules | Where { $_.Name -eq $name }

    if ($existingRule -is [System.Array]) {
        Fail-Json $result "Multiple firewall rules with name '$name' found."
    }

    $rule = New-FWRule -name $name `
                       -description $description `
                       -direction $direction `
                       -action $action `
                       -applicationName $program `
                       -serviceName $service `
                       -enabled $enabled `
                       -profiles $profiles `
                       -localAddresses $localip `
                       -remoteAddresses $remoteip `
                       -localPorts $localport `
                       -remotePorts $remoteport `
                       -protocol $protocol `
                       -interfaceTypes $interfacetypes `
                       -edgeTraversalOptions $edge `
                       -secureFlags $security

    $fwPropertiesToCompare = @('Name','Description','Direction','Action','ApplicationName','ServiceName','Enabled','Profiles','LocalAddresses','RemoteAddresses','LocalPorts','RemotePorts','Protocol','InterfaceTypes', 'EdgeTraversalOptions', 'SecureFlags')

    if ($state -eq "absent") {
        if ($existingRule -eq $null) {
            $result.msg = "Firewall rule '$name' does not exist."
        } else {
            if ($diff_support) {
                foreach ($prop in $fwPropertiesToCompare) {
                    $result.diff.prepared += "-[$($prop)='$($existingRule.$prop)']`n"
                }
            }

            if (-not $check_mode) {
                $fw.Rules.Remove($existingRule.Name)
            }
            $result.changed = $true
            $result.msg = "Firewall rule '$name' removed."
        }
    } elseif ($state -eq "present") {
        if ($existingRule -eq $null) {
            if ($diff_support) {
                foreach ($prop in $fwPropertiesToCompare) {
                    $result.diff.prepared += "+[$($prop)='$($existingRule.$prop)']`n"
                }
            }

            if (-not $check_mode) {
                $fw.Rules.Add($rule)
            }
            $result.changed = $true
            $result.msg = "Firewall rule '$name' created."
        } else {
            foreach ($prop in $fwPropertiesToCompare) {
                if ($existingRule.$prop -ne $rule.$prop) {
                    if ($diff_support) {
                        $result.diff.prepared += "-[$($prop)='$($existingRule.$prop)']`n"
                        $result.diff.prepared += "+[$($prop)='$($rule.$prop)']`n"
                    }

                    if (-not $check_mode) {
                        # Profiles value cannot be a uint32, but the "all profiles" value (0x7FFFFFFF) will often become a uint32, so must cast to [int]
                        # to prevent InvalidCastException under PS5+
                        If($prop -eq 'Profiles') {
                            $existingRule.Profiles = [int] $rule.$prop
                        }
                        Else {
                            $existingRule.$prop = $rule.$prop
                        }
                    }
                    $result.changed = $true
                }
            }

            if ($result.changed) {
                $result.msg = "Firewall rule '$name' changed."
            } else {
                $result.msg = "Firewall rule '$name' already exists."
            }
        }
    }
} catch [Exception] {
    $ex = $_
    $result['exception'] = $($ex | Out-String)
    Fail-Json $result $ex.Exception.Message
}

Exit-Json $result
