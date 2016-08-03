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

function getFirewallRule ($fwsettings) {
    try {

        #$output = Get-NetFirewallRule -name $($fwsettings.'Rule Name');
        $rawoutput=@(netsh advfirewall firewall show rule name="$($fwsettings.'Rule Name')" verbose)
        if (!($rawoutput -eq 'No rules match the specified criteria.')){
            $rawoutput | Where {$_ -match '^([^:]+):\s*(\S.*)$'} | Foreach -Begin {
                    $FirstRun = $true;
                    $HashProps = @{};
                } -Process {
                    if (($Matches[1] -eq 'Rule Name') -and (!($FirstRun))) {
                        #$output=New-Object -TypeName PSCustomObject -Property $HashProps;
                        $output=$HashProps;
                        $HashProps = @{};
                    };
                    $HashProps.$($Matches[1]) = $Matches[2];
                    $FirstRun = $false;
                } -End {
                #$output=New-Object -TypeName PSCustomObject -Property $HashProps;
                $output=$HashProps;
                }
        }
        $exists=$false;
        $correct=$true;
        $diff=$false;
        $multi=$false;
        $correct=$false;
        $difference=@();
        $msg=@();
        if ($($output|measure).count -gt 0) {
            $exists=$true;
            $msg += @("The rule '" + $fwsettings.'Rule Name' + "' exists.");
            if ($($output|measure).count -gt 1) {
                $multi=$true
                $msg += @("The rule '" + $fwsettings.'Rule Name' + "' has multiple entries.");
                ForEach($rule in $output.GetEnumerator()) {
                    ForEach($fwsetting in $fwsettings.GetEnumerator()) {
                        if ( $rule.$fwsetting -ne $fwsettings.$fwsetting) {
                            $diff=$true;
                            #$difference+=@($fwsettings.$($fwsetting.Key));
                            $difference+=@("output:$rule.$fwsetting,fwsetting:$fwsettings.$fwsetting");
                        };
                    };
                    if ($diff -eq $false) {
                        $correct=$true
                    };
                };
            } else {
                ForEach($fwsetting in $fwsettings.GetEnumerator()) {
                    if ( $output.$($fwsetting.Key) -ne $fwsettings.$($fwsetting.Key)) {

                        if (($fwsetting.Key -eq 'RemoteIP') -and ($output.$($fwsetting.Key) -eq ($fwsettings.$($fwsetting.Key)+'-'+$fwsettings.$($fwsetting.Key)))) {
                            $donothing=$false
                        } elseif (($fwsetting.Key -eq 'DisplayName') -and ($output."Rule Name" -eq $fwsettings.$($fwsetting.Key))) {
                            $donothing=$false
                        } else {
                            $diff=$true;
                            $difference+=@($fwsettings.$($fwsetting.Key));
                        };
                    };
                };
                if ($diff -eq $false) {
                    $correct=$true
                };
            };
            if ($correct) {
                $msg += @("An identical rule exists");
            } else {
                $msg += @("The rule exists but has different values");
            }
        } else {
            $msg += @("No rule could be found");
        };
        $result = @{
            failed = $false
            exists = $exists
            identical = $correct
            multiple = $multi
            difference = $difference
            msg = $msg
        }
    } catch [Exception]{
        $result = @{
            failed = $true
            error = $_.Exception.Message
            msg = $msg
        }
    };
    return $result
};

function createFireWallRule ($fwsettings) {
    $msg=@()
    $execString="netsh advfirewall firewall add rule"

    ForEach ($fwsetting in $fwsettings.GetEnumerator()) {
        if ($fwsetting.key -eq 'Direction') {
            $key='dir'
        } elseif ($fwsetting.key -eq 'Rule Name') {
            $key='name'
        } elseif ($fwsetting.key -eq 'Enabled') {
            $key='enable'
        } elseif ($fwsetting.key -eq 'Profiles') {
            $key='profile'
        } else {
            $key=$($fwsetting.key).ToLower()
        };
        $execString+=" ";
        $execString+=$key;
        $execString+="=";
        $execString+='"';
        $execString+=$fwsetting.value;
        $execString+='"';
    };
    try {
        #$msg+=@($execString);
        $output=$(Invoke-Expression $execString| ? {$_});
        $msg+=@("Created firewall rule $name");

        $result=@{
            failed = $false
            output=$output
            changed=$true
            msg=$msg
        };

    } catch [Exception]{
        $msg=@("Failed to create the rule")
        $result=@{
            output=$output
            failed=$true
            error=$_.Exception.Message
            msg=$msg
        };
    };
    return $result
};

function removeFireWallRule ($fwsettings) {
    $msg=@()
    try {
        $rawoutput=@(netsh advfirewall firewall delete rule name="$($fwsettings.'Rule Name')")
        $rawoutput | Where {$_ -match '^([^:]+):\s*(\S.*)$'} | Foreach -Begin {
                $FirstRun = $true;
                $HashProps = @{};
            } -Process {
                if (($Matches[1] -eq 'Rule Name') -and (!($FirstRun))) {
                    $output=$HashProps;
                    $HashProps = @{};
                };
                $HashProps.$($Matches[1]) = $Matches[2];
                $FirstRun = $false;
            } -End {
                $output=$HashProps;
            };
        $msg+=@("Removed the rule")
        $result=@{
            failed=$false
            changed=$true
            msg=$msg
            output=$output
        };
    } catch [Exception]{
        $msg+=@("Failed to remove the rule")
        $result=@{
            failed=$true
            error=$_.Exception.Message
            msg=$msg
        }
    };
    return $result
}

# Mount Drives
$change=$false;
$fail=$false;
$msg=@();
$fwsettings=@{}

# Variabelise the arguments
$params=Parse-Args $args;

$name = Get-AnsibleParam -obj $params -name "name" -failifempty $true
$direction = Get-AnsibleParam -obj $params -name "direction" -failifempty $true -validateSet "in","out"
$action = Get-AnsibleParam -obj $params -name "action" -failifempty $true -validateSet "allow","block","bypass"
$program = Get-AnsibleParam -obj $params -name "program"
$service = Get-AnsibleParam -obj $params -name "service" -default "any"
$description = Get-AnsibleParam -obj $params -name "description"
$enable = ConvertTo-Bool (Get-AnsibleParam -obj $params -name "enable" -default "true")
$winprofile = Get-AnsibleParam -obj $params -name "profile" -default "any"
$localip = Get-AnsibleParam -obj $params -name "localip" -default "any"
$remoteip = Get-AnsibleParam -obj $params -name "remoteip" -default "any"
$localport = Get-AnsibleParam -obj $params -name "localport" -default "any"
$remoteport = Get-AnsibleParam -obj $params -name "remoteport" -default "any"
$protocol = Get-AnsibleParam -obj $params -name "protocol" -default "any"

$state = Get-AnsibleParam -obj $params -name "state" -failifempty $true -validateSet "present","absent"
$force = ConvertTo-Bool (Get-AnsibleParam -obj $params -name "force" -default "false")

# Check the arguments
If ($enable -eq $true) {
    $fwsettings.Add("Enabled", "yes");
} Else {
    $fwsettings.Add("Enabled", "no");
};

$fwsettings.Add("Rule Name", $name)
#$fwsettings.Add("displayname", $name)

$state = $state.ToString().ToLower()
If ($state -eq "present"){
    $fwsettings.Add("Direction", $direction)
    $fwsettings.Add("Action", $action)
};

If ($description) {
    $fwsettings.Add("Description", $description);
}

If ($program) {
    $fwsettings.Add("Program", $program);
}

$fwsettings.Add("LocalIP", $localip);
$fwsettings.Add("RemoteIP", $remoteip);
$fwsettings.Add("LocalPort", $localport);
$fwsettings.Add("RemotePort", $remoteport);
$fwsettings.Add("Service", $service);
$fwsettings.Add("Protocol", $protocol);
$fwsettings.Add("Profiles", $winprofile)

$output=@()
$capture=getFirewallRule ($fwsettings);
if ($capture.failed -eq $true) {
    $msg+=$capture.msg;
    $result=New-Object psobject @{
        changed=$false
        failed=$true
        error=$capture.error
        msg=$msg
    };
    Exit-Json $result;
} else {
    $diff=$capture.difference
    $msg+=$capture.msg;
    $identical=$capture.identical;
    $multiple=$capture.multiple;
}


switch ($state){
    "present" {
        if ($capture.exists -eq $false) {
            $capture=createFireWallRule($fwsettings);
            $msg+=$capture.msg;
            $change=$true;
            if ($capture.failed -eq $true){
                $result=New-Object psobject @{
                    failed=$capture.failed
                    error=$capture.error
                    output=$capture.output
                    changed=$change
                    msg=$msg
                    difference=$diff
                    fwsettings=$fwsettings
                };
                Exit-Json $result;
            }
        } elseif ($capture.identical -eq $false) {
            if ($force -eq $true) {
                $capture=removeFirewallRule($fwsettings);
                $msg+=$capture.msg;
                $change=$true;
                if ($capture.failed -eq $true){
                    $result=New-Object psobject @{
                        failed=$capture.failed
                        error=$capture.error
                        changed=$change
                        msg=$msg
                        output=$capture.output
                        fwsettings=$fwsettings
                    };
                    Exit-Json $result;
                }
                $capture=createFireWallRule($fwsettings);
                $msg+=$capture.msg;
                $change=$true;
                if ($capture.failed -eq $true){
                    $result=New-Object psobject @{
                        failed=$capture.failed
                        error=$capture.error
                        changed=$change
                        msg=$msg
                        difference=$diff
                        fwsettings=$fwsettings
                    };
                    Exit-Json $result;
                }

            } else {
                $fail=$true
                $msg+=@("There was already a rule $name with different values, use force=True to overwrite it");
            }
        } elseif ($capture.identical -eq $true) {
            $msg+=@("Firewall rule $name was already created");
        };
    }
    "absent" {
        if ($capture.exists -eq $true) {
            $capture=removeFirewallRule($fwsettings);
            $msg+=$capture.msg;
            $change=$true;
            if ($capture.failed -eq $true){
                $result=New-Object psobject @{
                    failed=$capture.failed
                    error=$capture.error
                    changed=$change
                    msg=$msg
                    output=$capture.output
                    fwsettings=$fwsettings
                };
                Exit-Json $result;
            }
        } else {
            $msg+=@("Firewall rule $name did not exist");
        };
    }
};


$result=New-Object psobject @{
    failed=$fail
    changed=$change
    msg=$msg
    difference=$diff
    fwsettings=$fwsettings
};


Exit-Json $result;
