#!powershell
#
# (c) 2014, Timothy Vandenbrande <timothy.vandenbrande@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.
#
# WANT_JSON
# POWERSHELL_COMMON

# TODO: Reimplement this using Powershell cmdlets

$ErrorActionPreference = "Stop"

function convertToNetmask($maskLength) {
    [IPAddress] $ip = 0
    $ip.Address = ([UInt32]::MaxValue) -shl (32 - $maskLength) -shr (32 - $maskLength)
    return $ip.IPAddressToString
}

function ConvertTo-TitleCase($string) {
    return (Get-Culture).TextInfo.ToTitleCase($string.ToLower())
}

function ConvertTo-SortedKV($object, $unsupported = @()) {
    $output = ""
    foreach($item in $object.GetEnumerator() | Sort -Property Name) {
        if (($item.Name -notin $unsupported) -and ($item.Value -ne $null)) {
            $output += "$($item.Name): $($item.Value)`n"
        }
    }
    return $output
}

function preprocessAndCompare($key, $outputValue, $fwsettingValue) {
    if ($key -eq 'RemoteIP') {
        if ($outputValue -eq $fwsettingValue) {
            return $true
        }

        if ($outputValue -eq $fwsettingValue+'-'+$fwsettingValue) {
            return $true
        }

        if (($outputValue -eq $fwsettingValue+'/32') -or ($outputValue -eq $fwsettingValue+'/255.255.255.255')) {
            return $true
        }

        if ($outputValue -match '^([\d\.]+)\/(\d+)$') {
            $netmask = convertToNetmask($Matches[2])
            if ($fwsettingValue -eq $Matches[1]+"/"+$netmask) {
                return $true
            }
        }

        if ($fwsettingValue -match '^([\d\.]+)\/(\d+)$') {
            $netmask = convertToNetmask($Matches[2])
            if ($outputValue -eq $Matches[1]+"/"+$netmask) {
                return $true
            }
        }
    }

    return $false
}

function getFirewallRule ($fwsettings) {
    $diff = $false
    $result = @{
        changed = $false
        identical = $false
        exists = $false
        failed = $false
        msg = @()
        multiple = $false
    }

    try {
        $command = "netsh advfirewall firewall show rule name=`"$($fwsettings.'Rule Name')`" verbose"
        #$output = Get-NetFirewallRule -name $($fwsettings.'Rule Name')
        $result.output = Invoke-Expression $command | Where { $_  }
        $rc = $LASTEXITCODE
        if ($rc -eq 1) {
            $result.msg += @("No rule '$name' could be found")
        } elseif ($rc -eq 0) {
            # Process command output
            $result.output | Where {$_ -match '^([^:]+):\s*(\S.*)$'} | ForEach -Begin {
                    $FirstRun = $true
                    $HashProps = @{}
                } -Process {
                    if (($Matches[1] -eq 'Rule Name') -and (-not $FirstRun)) {
                        $output = $HashProps
                        $HashProps = @{}
                    }
                    $HashProps.$($Matches[1]) = $Matches[2]
                    $FirstRun = $false
                } -End {
                    $output = $HashProps
                }
            if ($($output|measure).count -gt 0) {
                $diff = $false
                $result.exists = $true
                #$result.msg += @("The rule '$($fwsettings.'Rule Name')' exists.")
                if ($($output|measure).count -gt 1) {
                    $result.multiple = $true
                    $result.msg += @("The rule '$($fwsettings.'Rule Name')' has multiple entries.")
                    $result.diff = @{}
                    $result.diff.after = ConvertTo-SortedKV $fwsettings
                    $result.diff.before = ConvertTo-SortedKV $rule $unsupported
                    if ($result.diff.after -ne $result.diff.before ) {
                        $diff = $true
                    }
                } else {
                    if ($diff_support) {
                        $result.diff = @{}
                        $result.diff.after = ConvertTo-SortedKV $fwsettings
                        $result.diff.before = ConvertTo-SortedKV $output $unsupported
                    }
                    ForEach($fwsetting in $fwsettings.GetEnumerator()) {
                        if ($output.$($fwsetting.Key) -ne $fwsettings.$($fwsetting.Key)) {
                            if ((preprocessAndCompare -key $fwsetting.Key -outputValue $output.$($fwsetting.Key) -fwsettingValue $fwsettings.$($fwsetting.Key))) {
                                Continue
                            } elseif (($fwsetting.Key -eq 'DisplayName') -and ($output."Rule Name" -eq $fwsettings.$($fwsetting.Key))) {
                                Continue
                            } elseif (($fwsetting.Key -eq 'Program') -and ($output.$($fwsetting.Key) -eq (Expand-Environment($fwsettings.$($fwsetting.Key))))) {
                                # Ignore difference caused by expanded environment variables
                                Continue
                            } else {
                                $diff = $true
                                Break
                            }
                        }
                    }
                }
                if (-not $diff) {
                    $result.identical = $true
                }
                if ($result.identical) {
                    $result.msg += @("The rule '$name' exists and is identical")
                } else {
                    $result.msg += @("The rule '$name' exists but has different values")
                }
            }
        } else {
            $result.failed = $true
        }
    } catch [Exception] {
        $result.failed = $true
        $result.error = $_.Exception.Message
    }
    return $result
}

function createFireWallRule ($fwsettings) {
    $result = @{
        changed = $false
        failed = $false
        msg = @()
    }

    $command = "netsh advfirewall firewall add rule"
    ForEach ($fwsetting in $fwsettings.GetEnumerator()) {
        if ($fwsetting.value -ne $null) {
            switch($fwsetting.key) {
                "Direction" { $option = "dir" }
                "Rule Name" { $option = "name" }
                "Enabled" { $option = "enable" }
                "Profiles" { $option = "profile" }
                "InterfaceTypes" { $option = "interfacetype" }
                "Security" { $option = "security" }
                "Edge traversal" { $option = "edge" }
                default { $option = $($fwsetting.key).ToLower() }
            }
            $command += " $option='$($fwsetting.value)'"
        }
    }

    try {
        $rc = 0
        if (-not $check_mode) {
            $result.output = Invoke-Expression $command | Where { $_ }
            $rc = $LASTEXITCODE
        }
        if ($rc -eq 0) {
            if ($diff_support) {
                $result.diff = @{}
                $result.diff.after = ConvertTo-SortedKV $fwsettings
                $result.diff.before= ""
            }
            $result.changed = $true
            $result.msg += @("Created firewall rule '$name'")
        } else {
            $result.failed = $true
            $result.msg += @("Create command '$command' failed with rc=$rc")
        }
    } catch [Exception]{
        $result.error = $_.Exception.Message
        $result.failed = $true
        $result.msg = @("Failed to create the rule '$name'")
    }
    return $result
}

function removeFireWallRule ($fwsettings) {
    $result = @{
        changed = $false
        failed = $false
        msg = @()
    }

    $command = "netsh advfirewall firewall delete rule name='$($fwsettings.'Rule Name')'"
    try {
        $rc = 0
        if (-not $check_mode) {
            $result.output = Invoke-Expression $command | Where { $_ }
            $rc = $LASTEXITCODE
            $result.output | Where {$_ -match '^([^:]+):\s*(\S.*)$'} | Foreach -Begin {
                    $FirstRun = $true
                    $HashProps = @{}
                } -Process {
                    if (($Matches[1] -eq 'Rule Name') -and (-not $FirstRun)) {
                        $result.output = $HashProps
                        $HashProps = @{}
                    }
                    $HashProps.$($Matches[1]) = $Matches[2]
                    $FirstRun = $false
                } -End {
                    $result.output = $HashProps
                }
        }
        if ($rc -eq 0 -or $rc -eq 1) {
            if ($diff_support) {
                $result.diff = @{}
                $result.diff.after = ""
                $result.diff.before = ConvertTo-SortedKV $fwsettings
            }
            $result.changed = $true
            $result.msg += @("Removed the rule '$name'")
        } else {
            $result.failed = $true
            $result.msg += @("Remove command '$command' failed with rc=$rc")
        }
    } catch [Exception]{
        $result.error = $_.Exception.Message
        $result.failed = $true
        $result.msg += @("Failed to remove the rule '$name'")
    }
    return $result
}

# FIXME: Unsupported keys
#$unsupported = @("Grouping", "Rule source")
$unsupported = @("Rule source")

$result = @{
    changed = $false
    fwsettings = @{}
    msg = @()
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
$profiles = Get-AnsibleParam -obj $params -name "profiles" -type "str" -default "domain,private,public" -aliases "profile"
$localip = Get-AnsibleParam -obj $params -name "localip" -type "str" -default "any"
$remoteip = Get-AnsibleParam -obj $params -name "remoteip" -type "str" -default "any"
$localport = Get-AnsibleParam -obj $params -name "localport" -type "str"
$remoteport = Get-AnsibleParam -obj $params -name "remoteport" -type "str"
$protocol = Get-AnsibleParam -obj $params -name "protocol" -type "str" -default "any"
$edge = Get-AnsibleParam -obj $params -name "edge" -type "str" -default "no" -validateset "no","yes","deferapp","deferuser"
$interfacetypes = Get-AnsibleParam -obj $params -name "interfacetypes" -type "str" -default "any"
$security = Get-AnsibleParam -obj $params -name "security" -type "str" -default "notrequired"

$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present","absent"
$force = Get-AnsibleParam -obj $params -name "force" -type "bool" -default $false

# Check the arguments
if ($enabled) {
    $result.fwsettings.Add("Enabled", "Yes")
} else {
    $result.fwsettings.Add("Enabled", "No")
}

$result.fwsettings.Add("Rule Name", $name)
#$result.fwsettings.Add("displayname", $name)

if ($state -eq "present") {
    $result.fwsettings.Add("Direction", $(ConvertTo-TitleCase($direction)))
    $result.fwsettings.Add("Action", $(ConvertTo-TitleCase $action))
}

if ($description -ne $null) {
    $result.fwsettings.Add("Description", $description)
}

if ($program -ne $null) {
    $result.fwsettings.Add("Program", $program)
}

$result.fwsettings.Add("LocalIP", $localip)
$result.fwsettings.Add("RemoteIP", $remoteip)

if ($localport -ne $null) {
    $result.fwsettings.Add("LocalPort", $localport)
}

if ($remoteport -ne $null) {
    $result.fwsettings.Add("RemotePort", $remoteport)
}

if ($service -ne $null) {
    $result.fwsettings.Add("Service", $(ConvertTo-TitleCase($service)))
}

if ($protocol -eq "Any") {
    $result.fwsettings.Add("Protocol", $protocol)
} else {
    $result.fwsettings.Add("Protocol", $protocol.toupper())
}

if ($profiles -eq "Any") {
    $result.fwsettings.Add("Profiles", "Domain,Private,Public")
} else {
    $result.fwsettings.Add("Profiles", $(ConvertTo-TitleCase($profiles)))
}

$result.fwsettings.Add("Edge traversal", $(ConvertTo-TitleCase($edge)))

if ($interfacetypes -ne $null) {
    $result.fwsettings.Add("InterfaceTypes", $(ConvertTo-TitleCase($interfacetypes)))
}

switch($security) {
    "Authenticate" { $security = "Authenticate" }
    "AuthDynEnc" { $security = "AuthDynEnc" }
    "AuthEnc" { $security = "AuthEnc" }
    "AuthNoEncap" { $security = "AuthNoEncap" }
    "NotRequired" { $security = "NotRequired" }
}
$result.fwsettings.Add("Security", $security)

# FIXME: Define unsupported options
#$result.fwsettings.Add("Grouping", "")
#$result.fwsettings.Add("Rule source", "Local Setting")

$get = getFirewallRule($result.fwsettings)
$result.msg += $get.msg

if ($get.failed) {
    $result.error = $get.error
    $result.output = $get.output
    Fail-Json $result $result.msg
}

$result.diff = $get.diff

if ($state -eq "present") {
    if (-not $get.exists) {

        $create = createFireWallRule($result.fwsettings)
        $result.msg += $create.msg
        $result.diff = $create.diff

        if ($create.failed) {
            $result.error = $create.error
            $result.output = $create.output
            Fail-Json $result $result.msg
        }

        $result.changed = $true

    } elseif (-not $get.identical) {
        # FIXME: This ought to use netsh advfirewall firewall set instead !
        if ($force) {

            $remove = removeFirewallRule($result.fwsettings)
            # NOTE: We retain the diff output from $get.diff here
            $result.msg += $remove.msg

            if ($remove.failed) {
                $result.error = $remove.error
                $result.output = $remove.output
                Fail-Json $result $result.msg
            }

            $create = createFireWallRule($result.fwsettings)
            # NOTE: We retain the diff output from $get.diff here
            $result.msg += $create.msg

            if ($create.failed) {
                $result.error = $create.error
                $result.output = $create.output
                Fail-Json $result $result.msg
            }

            $result.changed = $true

        } else {

            $result.msg += @("There was already a rule '$name' with different values, use the 'force' parameter to overwrite it")
            Fail-Json $result $result.msg

        }
    } else {

        $result.msg += @("Firewall rule '$name' was already created")

    }

} elseif ($state -eq "absent") {

    if ($get.exists) {

        $remove = removeFirewallRule($result.fwsettings)
        $result.diff = $remove.diff
        $result.msg += $remove.msg

        if ($remove.failed) {
            $result.error = $remove.error
            $result.output = $remove.output
            Fail-Json $result $result.msg
        }

        $result.changed = $true

    } else {

        $result.msg += @("Firewall rule '$name' did not exist")

    }
}

Exit-Json $result
