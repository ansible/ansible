#!powershell

# Copyright: (c) 2015, Peter Mounce <public@neverrunwithscissors.com>
# Copyright: (c) 2015, Michael Perzel <michaelperzel@gmail.com>
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.SID

$ErrorActionPreference = "Stop"

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$diff_mode = Get-AnsibleParam -obj $params -name "_ansible_diff" -type "bool" -default $false
$_remote_tmp = Get-AnsibleParam $params "_ansible_remote_tmp" -type "path" -default $env:TMP

$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$path = Get-AnsibleParam -obj $params -name "path" -type "str" -default "\"
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "absent", "present"

# task actions, list of dicts [{path, arguments, working_directory}]
$actions = Get-AnsibleParam -obj $params -name "actions" -type "list"

# task triggers, list of dicts [{ type, ... }]
$triggers = Get-AnsibleParam -obj $params -name "triggers" -type "list"

# task Principal properties
$display_name = Get-AnsibleParam -obj $params -name "display_name" -type "str"
$group = Get-AnsibleParam -obj $params -name "group" -type "str"
$logon_type = Get-AnsibleParam -obj $params -name "logon_type" -type "str" -validateset "none","password","s4u","interactive_token","group","service_account","interactive_token_or_password"
$run_level = Get-AnsibleParam -obj $params -name "run_level" -type "str" -validateset "limited", "highest" -aliases "runlevel"
$username = Get-AnsibleParam -obj $params -name "username" -type "str" -aliases "user"
$password = Get-AnsibleParam -obj $params -name "password" -type "str"
$update_password = Get-AnsibleParam -obj $params -name "update_password" -type "bool" -default $true

# task RegistrationInfo properties
$author = Get-AnsibleParam -obj $params -name "author" -type "str"
$date = Get-AnsibleParam -obj $params -name "date" -type "str"
$description = Get-AnsibleParam -obj $params -name "description" -type "str"
$source = Get-AnsibleParam -obj $params -name "source" -type "str"
$version = Get-AnsibleParam -obj $params -name "version" -type "str"

# task Settings properties
$allow_demand_start = Get-AnsibleParam -obj $params -name "allow_demand_start" -type "bool"
$allow_hard_terminate = Get-AnsibleParam -obj $params -name "allow_hard_terminate" -type "bool"
$compatibility =  Get-AnsibleParam -obj $params -name "compatibility" -type "int" # https://msdn.microsoft.com/en-us/library/windows/desktop/aa383486(v=vs.85).aspx
$delete_expired_task_after = Get-AnsibleParam -obj $params -name "delete_expired_task_after" -type "str" # time string PT...
$disallow_start_if_on_batteries = Get-AnsibleParam -obj $params -name "disallow_start_if_on_batteries" -type "bool"
$enabled = Get-AnsibleParam -obj $params -name "enabled" -type "bool"
$execution_time_limit = Get-AnsibleParam -obj $params -name "execution_time_limit" -type "str" # PT72H
$hidden = Get-AnsibleParam -obj $params -name "hidden" -type "bool"
# TODO: support for $idle_settings, needs to be created as a COM object
$multiple_instances = Get-AnsibleParam -obj $params -name "multiple_instances" -type "int" # https://msdn.microsoft.com/en-us/library/windows/desktop/aa383507(v=vs.85).aspx
# TODO: support for  $network_settings, needs to be created as a COM object
$priority = Get-AnsibleParam -obj $params -name "priority" -type "int" # https://msdn.microsoft.com/en-us/library/windows/desktop/aa383512(v=vs.85).aspx
$restart_count = Get-AnsibleParam -obj $params -name "restart_count" -type "int"
$restart_interval = Get-AnsibleParam -obj $params -name "restart_interval" -type "str" # time string PT..
$run_only_if_idle = Get-AnsibleParam -obj $params -name "run_only_if_idle" -type "bool"
$run_only_if_network_available = Get-AnsibleParam -obj $params -name "run_only_if_network_available" -type "bool"
$start_when_available = Get-AnsibleParam -obj $params -name "start_when_available" -type "bool"
$stop_if_going_on_batteries = Get-AnsibleParam -obj $params -name "stop_if_going_on_batteries" -type "bool"
$wake_to_run = Get-AnsibleParam -obj $params -name "wake_to_run" -type "bool"

$result = @{
    changed = $false
}

if ($diff_mode) {
    $result.diff = @{}
}

$task_enums = @"
public enum TASK_ACTION_TYPE // https://msdn.microsoft.com/en-us/library/windows/desktop/aa383553(v=vs.85).aspx
{
    TASK_ACTION_EXEC          = 0,
    // The below are not supported and are only kept for documentation purposes
    TASK_ACTION_COM_HANDLER   = 5,
    TASK_ACTION_SEND_EMAIL    = 6,
    TASK_ACTION_SHOW_MESSAGE  = 7
}

public enum TASK_CREATION // https://msdn.microsoft.com/en-us/library/windows/desktop/aa382538(v=vs.85).aspx
{
    TASK_VALIDATE_ONLY                 = 0x1,
    TASK_CREATE                        = 0x2,
    TASK_UPDATE                        = 0x4,
    TASK_CREATE_OR_UPDATE              = 0x6,
    TASK_DISABLE                       = 0x8,
    TASK_DONT_ADD_PRINCIPAL_ACE        = 0x10,
    TASK_IGNORE_REGISTRATION_TRIGGERS  = 0x20
}

public enum TASK_LOGON_TYPE // https://msdn.microsoft.com/en-us/library/windows/desktop/aa383566(v=vs.85).aspx
{
    TASK_LOGON_NONE                           = 0,
    TASK_LOGON_PASSWORD                       = 1,
    TASK_LOGON_S4U                            = 2,
    TASK_LOGON_INTERACTIVE_TOKEN              = 3,
    TASK_LOGON_GROUP                          = 4,
    TASK_LOGON_SERVICE_ACCOUNT                = 5,
    TASK_LOGON_INTERACTIVE_TOKEN_OR_PASSWORD  = 6
}

public enum TASK_RUN_LEVEL // https://msdn.microsoft.com/en-us/library/windows/desktop/aa380747(v=vs.85).aspx
{
    TASK_RUNLEVEL_LUA      = 0,
    TASK_RUNLEVEL_HIGHEST  = 1
}

public enum TASK_TRIGGER_TYPE2 // https://msdn.microsoft.com/en-us/library/windows/desktop/aa383915(v=vs.85).aspx
{
    TASK_TRIGGER_EVENT                 = 0,
    TASK_TRIGGER_TIME                  = 1,
    TASK_TRIGGER_DAILY                 = 2,
    TASK_TRIGGER_WEEKLY                = 3,
    TASK_TRIGGER_MONTHLY               = 4,
    TASK_TRIGGER_MONTHLYDOW            = 5,
    TASK_TRIGGER_IDLE                  = 6,
    TASK_TRIGGER_REGISTRATION          = 7,
    TASK_TRIGGER_BOOT                  = 8,
    TASK_TRIGGER_LOGON                 = 9,
    TASK_TRIGGER_SESSION_STATE_CHANGE  = 11
}
"@

$original_tmp = $env:TMP
$env:TMP = $_remote_tmp
Add-Type -TypeDefinition $task_enums
$env:TMP = $original_tmp

########################
### HELPER FUNCTIONS ###
########################
Function ConvertTo-HashtableFromPsCustomObject($object) {
    if ($object -is [Hashtable]) {
        return ,$object
    }

    $hashtable = @{}
    $object | Get-Member -MemberType *Property | % {
        $value = $object.$($_.Name)
        if ($value -is [PSObject]) {
            $value = ConvertTo-HashtableFromPsCustomObject -object $value
        }
        $hashtable.$($_.Name) = $value
    }

    return ,$hashtable
}

Function Convert-SnakeToPascalCase($snake) {
    # very basic function to convert snake_case to PascalCase for use in COM
    # objects
    [regex]$regex = "_(\w)"
    $pascal_case = $regex.Replace($snake, { $args[0].Value.Substring(1).ToUpper() })
    $capitalised = $pascal_case.Substring(0, 1).ToUpper() + $pascal_case.Substring(1)

    return $capitalised
}

Function Compare-Properties($property_name, $parent_property, $map, $enum_map=$null) {
    $changes = [System.Collections.ArrayList]@()

    # loop through the passed in map and compare values
    # Name = The name of property in the COM object
    # Value = The new value to compare the existing value with
    foreach ($entry in $map.GetEnumerator()) {
        $new_value = $entry.Value

        if ($new_value -ne $null) {
            $property_name = $entry.Name
            $existing_value = $parent_property.$property_name
            if ($existing_value -cne $new_value) {
                try {
                    $parent_property.$property_name = $new_value
                } catch {
                    Fail-Json -obj $result -message "failed to set $property_name property '$property_name' to '$new_value': $($_.Exception.Message)"
                }

                if ($enum_map -ne $null -and $enum_map.ContainsKey($property_name)) {
                    $enum = [type]$enum_map.$property_name
                    $existing_value = [Enum]::ToObject($enum, $existing_value)
                    $new_value = [Enum]::ToObject($enum, $new_value)
                }
                [void]$changes.Add("-$property_name=$existing_value`n+$property_name=$new_value")
            }
        }
    }

    return ,$changes
}

Function Set-PropertyForComObject($com_object, $name, $arg, $value) {
    $com_name = Convert-SnakeToPascalCase -snake $arg
    try {
        $com_object.$com_name = $value
    } catch {
        Fail-Json -obj $result -message "failed to set $name property '$com_name' to '$value': $($_.Exception.Message)"
    }
}

Function Compare-PropertyList {
    Param(
        $collection, # the collection COM object to manipulate, this must contains the Create method
        [string]$property_name, # human friendly name of the property object, e.g. action/trigger
        [Array]$new, # a list of new properties, passed in by Ansible
        [Array]$existing, # a list of existing properties from the COM object collection
        [Hashtable]$map, # metadata for the collection, see below for the structure
        [string]$enum # the parent enum name for type value
    )
    <## map metadata structure
    {
        collection type [TASK_ACTION_TYPE] for Actions or [TASK_TRIGGER_TYPE2] for Triggers {
            mandatory = list of mandatory properties for this type, ansible input name not the COM name
            optional = list of optional properties that could be set for this type
            # maps the ansible input object name to the COM name, e.g. working_directory = WorkingDirectory
            map = {
                ansible input name = COM name
            }
        }
    }##>
    # used by both Actions and Triggers to compare the collections of that property

    $enum = [type]$enum
    $changes = [System.Collections.ArrayList]@()
    $new_count = $new.Count
    $existing_count = $existing.Count

    for ($i = 0; $i -lt $new_count; $i++) {
        if ($i -lt $existing_count) {
            $existing_property = $existing[$i]
        } else {
            $existing_property = $null
        }
        $new_property = $new[$i]

        # get the type of the property, for action this is set automatically
        if (-not $new_property.ContainsKey("type")) {
            Fail-Json -obj $result -message "entry for $property_name must contain a type key"
        }
        $type = $new_property.type
        $valid_types = $map.Keys
        $property_map = $map.$type

        # now let's validate the args for the property
        $mandatory_args = $property_map.mandatory
        $optional_args = $property_map.optional
        $total_args = $mandatory_args + $optional_args

        # validate the mandatory arguments
        foreach ($mandatory_arg in $mandatory_args) {
            if (-not $new_property.ContainsKey($mandatory_arg)) {
                Fail-Json -obj $result -message "mandatory key '$mandatory_arg' for $($property_name) is not set, mandatory keys are '$($mandatory_args -join "', '")'"
            }
        }
        # throw a warning if in invalid key was set
        foreach ($entry in $new_property.GetEnumerator()) {
            $key = $entry.Name
            if ($key -notin $total_args -and $key -ne "type") {
                Add-Warning -obj $result -message "key '$key' for $($property_name) entry is not valid and will be ignored, valid keys are '$($total_args -join "', '")'"
            }
        }

        # now we have validated the input and have gotten the metadata, let's
        # get the diff string
        if ($existing_property -eq $null) {
            # we have more properties than before,just add to the new
            # properties list
            $diff_list = [System.Collections.ArrayList]@()

            foreach ($property_arg in $total_args) {
                if ($new_property.ContainsKey($property_arg)) {
                    $com_name = Convert-SnakeToPascalCase -snake $property_arg
                    $property_value = $new_property.$property_arg

                    if ($property_value -is [Hashtable]) {
                        foreach ($sub_property_arg in $property_value.Keys) {
                            $sub_com_name = Convert-SnakeToPascalCase -snake $sub_property_arg
                            $sub_property_value = $property_value.$sub_property_arg
                            [void]$diff_list.Add("+$com_name.$sub_com_name=$sub_property_value")
                        }
                    } else {
                        [void]$diff_list.Add("+$com_name=$property_value")
                    }
                }
            }

            [void]$changes.Add("+$property_name[$i] = {`n  +Type=$type`n  $($diff_list -join ",`n  ")`n+}")
        } elseif ([Enum]::ToObject($enum, $existing_property.Type) -ne $type) {
            # the types are different so we need to change
            $diff_list = [System.Collections.ArrayList]@()

            if ($existing_property.Type -notin $valid_types) {
                [void]$diff_list.Add("-UNKNOWN TYPE $($existing_property.Type)")
                foreach ($property_args in $total_args) {
                    if ($new_property.ContainsKey($property_arg)) {
                        $com_name = Convert-SnakeToPascalCase -snake $property_arg
                        $property_value = $new_property.$property_arg

                        if ($property_value -is [Hashtable]) {
                            foreach ($sub_property_arg in $property_value.Keys) {
                                $sub_com_name = Convert-SnakeToPascalCase -snake $sub_property_arg
                                $sub_property_value = $property_value.$sub_property_arg
                                [void]$diff_list.Add("+$com_name.$sub_com_name=$sub_property_value")
                            }
                        } else {
                            [void]$diff_list.Add("+$com_name=$property_value")
                        }
                    }
                }
            } else {
                # we know the types of the existing property
                $existing_type = [Enum]::ToObject([TASK_TRIGGER_TYPE2], $existing_property.Type)
                [void]$diff_list.Add("-Type=$existing_type")
                [void]$diff_list.Add("+Type=$type")
                foreach ($property_arg in $total_args) {
                    $com_name = Convert-SnakeToPascalCase -snake $property_arg
                    $property_value = $new_property.$property_arg
                    $existing_value = $existing_property.$com_name

                    if ($property_value -is [Hashtable]) {
                        foreach ($sub_property_arg in $property_value.Keys) {
                            $sub_property_value = $property_value.$sub_property_arg
                            $sub_com_name = Convert-SnakeToPascalCase -snake $sub_property_arg
                            $sub_existing_value = $existing_property.$com_name.$sub_com_name

                            if ($sub_property_value -ne $null) {
                                [void]$diff_list.Add("+$com_name.$sub_com_name=$sub_property_value")
                            }

                            if ($sub_existing_value -ne $null) {
                                [void]$diff_list.Add("-$com_name.$sub_com_name=$sub_existing_value")
                            }
                        }
                    } else {
                        if ($property_value -ne $null) {
                            [void]$diff_list.Add("+$com_name=$property_value")
                        }

                        if ($existing_value -ne $null) {
                            [void]$diff_list.Add("-$com_name=$existing_value")
                        }
                    }
                }
            }

            [void]$changes.Add("$property_name[$i] = {`n  $($diff_list -join ",`n  ")`n}")
        } else {
            # compare the properties of existing and new
            $diff_list = [System.Collections.ArrayList]@()

            foreach ($property_arg in $total_args) {
                $com_name = Convert-SnakeToPascalCase -snake $property_arg
                $property_value = $new_property.$property_arg
                $existing_value = $existing_property.$com_name
                
                if ($property_value -is [Hashtable]) {
                    foreach ($sub_property_arg in $property_value.Keys) {
                        $sub_property_value = $property_value.$sub_property_arg
                        
                        if ($sub_property_value -ne $null) {
                            $sub_com_name = Convert-SnakeToPascalCase -snake $sub_property_arg
                            $sub_existing_value = $existing_property.$com_name.$sub_com_name

                            if ($sub_property_value -cne $sub_existing_value) {
                                [void]$diff_list.Add("-$com_name.$sub_com_name=$sub_existing_value")
                                [void]$diff_list.Add("+$com_name.$sub_com_name=$sub_property_value")
                            }
                        }
                    }
                } elseif ($property_value -ne $null -and $property_value -cne $existing_value) {
                    [void]$diff_list.Add("-$com_name=$existing_value")
                    [void]$diff_list.Add("+$com_name=$property_value")
                }
            }

            if ($diff_list.Count -gt 0) {
                [void]$changes.Add("$property_name[$i] = {`n  $($diff_list -join ",`n  ")`n}")
            }
        }

        # finally rebuild the new property collection
        $new_object = $collection.Create($type)
        foreach ($property_arg in $total_args) {
            $new_value = $new_property.$property_arg
            if ($new_value -is [Hashtable]) {
                $com_name = Convert-SnakeToPascalCase -snake $property_arg
                $new_object_property = $new_object.$com_name
    
                foreach ($key in $new_value.Keys) {
                    $value = $new_value.$key
                    if ($value -ne $null) {
                        Set-PropertyForComObject -com_object $new_object_property -name $property_name -arg $key -value $value
                    }
                }
            } elseif ($new_value -ne $null) {
                Set-PropertyForComObject -com_object $new_object -name $property_name -arg $property_arg -value $new_value
            }
        }
    }

    # if there were any extra properties not in the new list, create diff str
    if ($existing_count -gt $new_count) {
        for ($i = $new_count; $i -lt $existing_count; $i++) {
            $diff_list = [System.Collections.ArrayList]@()
            $existing_property = $existing[$i]
            $existing_type = [Enum]::ToObject($enum, $existing_property.Type)

            if ($map.ContainsKey($existing_type)) {
                $property_map = $map.$existing_type
                $property_args = $property_map.mandatory + $property_map.optional

                foreach ($property_arg in $property_args) {
                    $com_name = Convert-SnakeToPascalCase -snake $property_arg
                    $existing_value = $existing_property.$com_name
                    if ($existing_value -ne $null) {
                        [void]$diff_list.Add("-$com_name=$existing_value")
                    }
                }
            } else {
                [void]$diff_list.Add("-UNKNOWN TYPE $existing_type")
            }

            [void]$changes.Add("-$property_name[$i] = {`n  $($diff_list -join ",`n  ")`n-}")
        }
    }

    return ,$changes
}

Function Compare-Actions($task_definition) {
    # compares the Actions property and returns a list of list of changed
    # actions for use in a diff string
    # ActionCollection - https://msdn.microsoft.com/en-us/library/windows/desktop/aa446804(v=vs.85).aspx
    # Action - https://msdn.microsoft.com/en-us/library/windows/desktop/aa446803(v=vs.85).aspx
    if ($actions -eq $null) {
        return ,[System.Collections.ArrayList]@()
    }

    $task_actions = $task_definition.Actions
    $existing_count = $task_actions.Count

    # because we clear the actions and re-add them to keep the order, we need
    # to convert the existing actions to a new list.
    # The Item property in actions starts at 1
    $existing_actions = [System.Collections.ArrayList]@()
    for ($i = 1; $i -le $existing_count; $i++) {
        [void]$existing_actions.Add($task_actions.Item($i))
    }
    if ($existing_count -gt 0) {
        $task_actions.Clear()
    }

    $map = @{
        [TASK_ACTION_TYPE]::TASK_ACTION_EXEC = @{
            mandatory = @('path')
            optional = @('arguments', 'working_directory')
        }
    }
    $changes = Compare-PropertyList -collection $task_actions -property_name "action" -new $actions -existing $existing_actions -map $map -enum TASK_ACTION_TYPE

    return ,$changes
}

Function Compare-Principal($task_definition, $task_definition_xml) {
    # compares the Principal property and returns a list of changed objects for
    # use in a diff string
    # https://msdn.microsoft.com/en-us/library/windows/desktop/aa382071(v=vs.85).aspx
    $principal_map = @{
        DisplayName = $display_name
        LogonType = $logon_type
        RunLevel = $run_level
    }
    $enum_map = @{
        LogonType = "TASK_LOGON_TYPE"
        RunLevel = "TASK_RUN_LEVEL"
    }
    $task_principal = $task_definition.Principal
    $changes = Compare-Properties -property_name "Principal" -parent_property $task_principal -map $principal_map -enum_map $enum_map

    # Principal.UserId and GroupId only returns the username portion of the
    # username, skipping the domain or server name. This makes the
    # comparison process useless so we need to parse the task XML to get
    # the actual sid/username. Depending on OS version this could be the SID
    # or it could be the username, we need to handle that accordingly
    $principal_username_sid = $task_definition_xml.Task.Principals.Principal.UserId
    if ($principal_username_sid -ne $null -and $principal_username_sid -notmatch "^S-\d-\d+(-\d+){1,14}(-\d+){0,1}$") {
        $principal_username_sid = Convert-ToSID -account_name $principal_username_sid
    }
    $principal_group_sid = $task_definition_xml.Task.Principals.Principal.GroupId
    if ($principal_group_sid -ne $null -and $principal_group_sid -notmatch "^S-\d-\d+(-\d+){1,14}(-\d+){0,1}$") {
        $principal_group_sid = Convert-ToSID -account_name $principal_group_sid
    }
    
    if ($username_sid -ne $null) {
        $new_user_name = Convert-FromSid -sid $username_sid
        if ($principal_group_sid -ne $null) {
            $existing_account_name = Convert-FromSid -sid $principal_group_sid
            [void]$changes.Add("-GroupId=$existing_account_name`n+UserId=$new_user_name")
            $task_principal.UserId = $new_user_name
            $task_principal.GroupId = $null
        } elseif ($principal_username_sid -eq $null) {
            [void]$changes.Add("+UserId=$new_user_name")
            $task_principal.UserId = $new_user_name
        } elseif ($principal_username_sid -ne $username_sid) {
            $existing_account_name = Convert-FromSid -sid $principal_username_sid
            [void]$changes.Add("-UserId=$existing_account_name`n+UserId=$new_user_name")
            $task_principal.UserId = $new_user_name
        }
    }
    if ($group_sid -ne $null) {
        $new_group_name = Convert-FromSid -sid $group_sid
        if ($principal_username_sid -ne $null) {
            $existing_account_name = Convert-FromSid -sid $principal_username_sid
            [void]$changes.Add("-UserId=$existing_account_name`n+GroupId=$new_group_name")
            $task_principal.UserId = $null
            $task_principal.GroupId = $new_group_name
        } elseif ($principal_group_sid -eq $null) {
            [void]$changes.Add("+GroupId=$new_group_name")
            $task_principal.GroupId = $new_group_name
        } elseif ($principal_group_sid -ne $group_sid) {
            $existing_account_name = Convert-FromSid -sid $principal_group_sid
            [void]$changes.Add("-GroupId=$existing_account_name`n+GroupId=$new_group_name")
            $task_principal.GroupId = $new_group_name
        }
    }
    
    return ,$changes
}

Function Compare-RegistrationInfo($task_definition) {
    # compares the RegistrationInfo property and returns a list of changed
    # objects for use in a diff string
    # https://msdn.microsoft.com/en-us/library/windows/desktop/aa382100(v=vs.85).aspx
    $reg_info_map = @{
        Author = $author
        Date = $date
        Description = $description
        Source = $source
        Version = $version
    }
    $changes = Compare-Properties -property_name "RegistrationInfo" -parent_property $task_definition.RegistrationInfo -map $reg_info_map

    return ,$changes
}

Function Compare-Settings($task_definition) {
    # compares the task Settings property and returns a list of changed objects
    # for use in a diff string
    # https://msdn.microsoft.com/en-us/library/windows/desktop/aa383480(v=vs.85).aspx
    $settings_map = @{
        AllowDemandStart = $allow_demand_start
        AllowHardTerminate = $allow_hard_terminate
        Compatibility = $compatibility
        DeleteExpiredTaskAfter = $delete_expired_task_after
        DisallowStartIfOnBatteries = $disallow_start_if_on_batteries
        ExecutionTimeLimit = $execution_time_limit
        Enabled = $enabled
        Hidden = $hidden
        # IdleSettings = $idle_settings # TODO: this takes in a COM object
        MultipleInstances = $multiple_instances
        # NetworkSettings = $network_settings # TODO: this takes in a COM object
        Priority = $priority
        RestartCount = $restart_count
        RestartInterval = $restart_interval
        RunOnlyIfIdle = $run_only_if_idle
        RunOnlyIfNetworkAvailable = $run_only_if_network_available
        StartWhenAvailable = $start_when_available
        StopIfGoingOnBatteries = $stop_if_going_on_batteries
        WakeToRun = $wake_to_run
    }
    $changes = Compare-Properties -property_name "Settings" -parent_property $task_definition.Settings -map $settings_map

    return ,$changes
}

Function Compare-Triggers($task_definition) {
    # compares the task Triggers property and returns a list of changed objects
    # for use in a diff string
    # TriggerCollection - https://msdn.microsoft.com/en-us/library/windows/desktop/aa383875(v=vs.85).aspx
    # Trigger - https://msdn.microsoft.com/en-us/library/windows/desktop/aa383868(v=vs.85).aspx
    if ($triggers -eq $null) {
        return ,[System.Collections.ArrayList]@()
    }

    $task_triggers = $task_definition.Triggers
    $existing_count = $task_triggers.Count

    # because we clear the actions and re-add them to keep the order, we need
    # to convert the existing actions to a new list.
    # The Item property in actions starts at 1
    $existing_triggers = [System.Collections.ArrayList]@()
    for ($i = 1; $i -le $existing_count; $i++) {
        [void]$existing_triggers.Add($task_triggers.Item($i))
    }
    if ($existing_count -gt 0) {
        $task_triggers.Clear()
    }

    $map = @{
        [TASK_TRIGGER_TYPE2]::TASK_TRIGGER_BOOT = @{
            mandatory = @()
            optional = @('delay', 'enabled', 'end_boundary', 'execution_time_limit', 'start_boundary', 'repetition')
        }
        [TASK_TRIGGER_TYPE2]::TASK_TRIGGER_DAILY = @{
            mandatory = @('start_boundary')
            optional = @('days_interval', 'enabled', 'end_boundary', 'execution_time_limit', 'random_delay', 'repetition')
        }
        [TASK_TRIGGER_TYPE2]::TASK_TRIGGER_EVENT = @{
            mandatory = @('subscription')
            # TODO: ValueQueries is a COM object
            optional = @('delay', 'enabled', 'end_boundary', 'execution_time_limit', 'start_boundary', 'repetition')
        }
        [TASK_TRIGGER_TYPE2]::TASK_TRIGGER_IDLE = @{
            mandatory = @()
            optional = @('enabled', 'end_boundary', 'execution_time_limit', 'start_boundary', 'repetition')
        }
        [TASK_TRIGGER_TYPE2]::TASK_TRIGGER_LOGON = @{
            mandatory = @()
            optional = @('delay', 'enabled', 'end_boundary', 'execution_time_limit', 'start_boundary', 'user_id', 'repetition')
        }
        [TASK_TRIGGER_TYPE2]::TASK_TRIGGER_MONTHLYDOW = @{
            mandatory = @('start_boundary')
            optional = @('days_of_week', 'enabled', 'end_boundary', 'execution_time_limit', 'months_of_year', 'random_delay', 'run_on_last_week_of_month', 'weeks_of_month', 'repetition')
        }
        [TASK_TRIGGER_TYPE2]::TASK_TRIGGER_MONTHLY = @{
            mandatory = @('days_of_month', 'start_boundary')
            optional = @('enabled', 'end_boundary', 'execution_time_limit', 'months_of_year', 'random_delay', 'run_on_last_day_of_month', 'start_boundary', 'repetition')
        }
        [TASK_TRIGGER_TYPE2]::TASK_TRIGGER_REGISTRATION = @{
            mandatory = @()
            optional = @('delay', 'enabled', 'end_boundary', 'execution_time_limit', 'start_boundary', 'repetition')
        }
        [TASK_TRIGGER_TYPE2]::TASK_TRIGGER_TIME = @{
            mandatory = @('start_boundary')
            optional = @('enabled', 'end_boundary', 'execution_time_limit', 'random_delay', 'repetition')
        }
        [TASK_TRIGGER_TYPE2]::TASK_TRIGGER_WEEKLY = @{
            mandatory = @('days_of_week', 'start_boundary')
            optional = @('enabled', 'end_boundary', 'execution_time_limit', 'random_delay', 'weeks_interval', 'repetition')
        }
        [TASK_TRIGGER_TYPE2]::TASK_TRIGGER_SESSION_STATE_CHANGE = @{
            mandatory = @('days_of_week', 'start_boundary')
            optional = @('delay', 'enabled', 'end_boundary', 'execution_time_limit', 'state_change', 'user_id', 'repetition')
        }
    }
    $changes = Compare-PropertyList -collection $task_triggers -property_name "trigger" -new $triggers -existing $existing_triggers -map $map -enum TASK_TRIGGER_TYPE2

    return ,$changes
}

Function Test-TaskExists($task_folder, $name) {
    # checks if a task exists in the TaskFolder COM object, returns null if the
    # task does not exist, otherwise returns the RegisteredTask object
    $task = $null
    if ($task_folder) {
        $raw_tasks = $task_folder.GetTasks(1) # 1 = TASK_ENUM_HIDDEN
        
        for ($i = 1; $i -le $raw_tasks.Count; $i++) {
            if ($raw_tasks.Item($i).Name -eq $name) {
                $task = $raw_tasks.Item($i)
                break
            }
        }
    }

    return $task
}

Function Test-XmlDurationFormat($key, $value) {
    # validate value is in the Duration Data Type format
    # PnYnMnDTnHnMnS
    try {
        $time_span = [System.Xml.XmlConvert]::ToTimeSpan($value)
        return $time_span
    } catch [System.FormatException] {
        Fail-Json -obj $result -message "trigger option '$key' must be in the XML duration format but was '$value'"
    }
}

######################################
### VALIDATION/BUILDING OF OPTIONS ###
######################################
# convert username and group to SID if set
$username_sid = $null
if ($username) {
    $username_sid = Convert-ToSID -account_name $username
}
$group_sid = $null
if ($group) {
    $group_sid = Convert-ToSID -account_name $group
}

# validate store_password and logon_type
if ($logon_type -ne $null) {
    $full_enum_name = "TASK_LOGON_$($logon_type.ToUpper())"
    $logon_type = [TASK_LOGON_TYPE]::$full_enum_name
}

# now validate the logon_type option with the other parameters
if ($username -ne $null -and $group -ne $null) {
    Fail-Json -obj $result -message "username and group can not be set at the same time"
}
if ($logon_type -ne $null) {
    if ($logon_type -eq [TASK_LOGON_TYPE]::TASK_LOGON_PASSWORD -and $password -eq $null) {
        Fail-Json -obj $result -message "password must be set when logon_type=password"
    }
    if ($logon_type -eq [TASK_LOGON_TYPE]::TASK_LOGON_S4U -and $password -eq $null) {
        Fail-Json -obj $result -message "password must be set when logon_type=s4u"
    }

    if ($logon_type -eq [TASK_LOGON_TYPE]::TASK_LOGON_GROUP -and $group -eq $null) {
        Fail-Json -obj $result -message "group must be set when logon_type=group"
    }

    # SIDs == Local System, Local Service and Network Service
    if ($logon_type -eq [TASK_LOGON_TYPE]::TASK_LOGON_SERVICE_ACCOUNT -and $username_sid -notin @("S-1-5-18", "S-1-5-19", "S-1-5-20")) {
        Fail-Json -obj $result -message "username must be SYSTEM, LOCAL SERVICE or NETWORK SERVICE when logon_type=service_account"
    }
}

# convert the run_level to enum value
if ($run_level -ne $null) {
    if ($run_level -eq "limited") {
        $run_level = [TASK_RUN_LEVEL]::TASK_RUNLEVEL_LUA
    } else {
        $run_level = [TASK_RUN_LEVEL]::TASK_RUNLEVEL_HIGHEST
    }
}

# manually add the only support action type for each action - also convert PSCustomObject to Hashtable
for ($i = 0; $i -lt $actions.Count; $i++) {
    $action = ConvertTo-HashtableFromPsCustomObject -object $actions[$i]
    $action.type = [TASK_ACTION_TYPE]::TASK_ACTION_EXEC
    if (-not $action.ContainsKey("path")) {
        Fail-Json -obj $result -message "action entry must contain the key 'path'"
    }
    $actions[$i] = $action
}

# convert and validate the triggers - and convert PSCustomObject to Hashtable
for ($i = 0; $i -lt $triggers.Count; $i++) {
    $trigger = ConvertTo-HashtableFromPsCustomObject -object $triggers[$i]
    $valid_trigger_types = @('event', 'time', 'daily', 'weekly', 'monthly', 'monthlydow', 'idle', 'registration', 'boot', 'logon', 'session_state_change')
    if (-not $trigger.ContainsKey("type")) {
        Fail-Json -obj $result -message "a trigger entry must contain a key 'type' with a value of '$($valid_trigger_types -join "', '")'"
    }

    $trigger_type = $trigger.type
    if ($trigger_type -notin $valid_trigger_types) {
        Fail-Json -obj $result -message "the specified trigger type '$trigger_type' is not valid, type must be a value of '$($valid_trigger_types -join "', '")'"
    }

    $full_enum_name = "TASK_TRIGGER_$($trigger_type.ToUpper())"
    $trigger_type = [TASK_TRIGGER_TYPE2]::$full_enum_name
    $trigger.type = $trigger_type

    $date_properties = @('start_boundary', 'end_boundary')
    foreach ($property_name in $date_properties) {
        # validate the date is in the DateTime format
        # yyyy-mm-ddThh:mm:ss
        if ($trigger.ContainsKey($property_name)) {
            $date_value = $trigger.$property_name
            try {
                $date = Get-Date -Date $date_value -Format s
                # make sure we convert it to the full string format
                $trigger.$property_name = $date.ToString()
            } catch [System.Management.Automation.ParameterBindingException] {
                Fail-Json -obj $result -message "trigger option '$property_name' must be in the format 'YYYY-MM-DDThh:mm:ss' format but was '$date_value'"
            }
        }
    }

    $time_properties = @('execution_time_limit', 'delay', 'random_delay')
    foreach ($property_name in $time_properties) {
        if ($trigger.ContainsKey($property_name)) {
            $time_span = $trigger.$property_name
            Test-XmlDurationFormat -key $property_name -value $time_span
        }
    }

    if ($trigger.ContainsKey("repetition")) {
        $trigger.repetition = ConvertTo-HashtableFromPsCustomObject -object $trigger.repetition

        $interval_timespan = $null
        if ($trigger.repetition.ContainsKey("interval") -and $trigger.repetition.interval -ne $null) {
            $interval_timespan = Test-XmlDurationFormat -key "interval" -value $trigger.repetition.interval
        }

        $duration_timespan = $null
        if ($trigger.repetition.ContainsKey("duration") -and $trigger.repetition.duration -ne $null) {
            $duration_timespan = Test-XmlDurationFormat -key "duration" -value $trigger.repetition.duration
        }

        if ($interval_timespan -ne $null -and $duration_timespan -ne $null -and $interval_timespan -gt $duration_timespan) {
            Fail-Json -obj $result -message "trigger repetition option 'interval' value '$($trigger.repetition.interval)' must be less than or equal to 'duration' value '$($trigger.repetition.duration)'"
        }
    }

    # convert out human readble text to the hex values for these properties
    if ($trigger.ContainsKey("days_of_week")) {
        $days = $trigger.days_of_week
        if ($days -is [String]) {
            $days = $days.Split(",").Trim()
        } elseif ($days -isnot [Array]) {
            $days = @($days)
        }
        
        $day_value = 0
        foreach ($day in $days) {
            # https://msdn.microsoft.com/en-us/library/windows/desktop/aa382057(v=vs.85).aspx
            switch ($day) {
                sunday { $day_value = $day_value -bor 0x01 }
                monday { $day_value = $day_value -bor 0x02 }
                tuesday { $day_value = $day_value -bor 0x04 }
                wednesday { $day_value = $day_value -bor 0x08 }
                thursday { $day_value = $day_value -bor 0x10 }
                friday { $day_value = $day_value -bor 0x20 }
                saturday { $day_value = $day_value -bor 0x40 }
                default { Fail-Json -obj $result -message "invalid day of week '$day', check the spelling matches the full day name" }
            }
        }
        if ($day_value -eq 0) {
            $day_value = $null
        }

        $trigger.days_of_week = $day_value
    }
    if ($trigger.ContainsKey("days_of_month")) {
        $days = $trigger.days_of_month
        if ($days -is [String]) {
            $days = $days.Split(",").Trim()
        } elseif ($days -isnot [Array]) {
            $days = @($days)
        }

        $day_value = 0
        foreach ($day in $days) {
            # https://msdn.microsoft.com/en-us/library/windows/desktop/aa382063(v=vs.85).aspx
            switch ($day) {
                1 { $day_value = $day_value -bor 0x01 }
                2 { $day_value = $day_value -bor 0x02 }
                3 { $day_value = $day_value -bor 0x04 }
                4 { $day_value = $day_value -bor 0x08 }
                5 { $day_value = $day_value -bor 0x10 }
                6 { $day_value = $day_value -bor 0x20 }
                7 { $day_value = $day_value -bor 0x40 }
                8 { $day_value = $day_value -bor 0x80 }
                9 { $day_value = $day_value -bor 0x100 }
                10 { $day_value = $day_value -bor 0x200 }
                11 { $day_value = $day_value -bor 0x400 }
                12 { $day_value = $day_value -bor 0x800 }
                13 { $day_value = $day_value -bor 0x1000 }
                14 { $day_value = $day_value -bor 0x2000 }
                15 { $day_value = $day_value -bor 0x4000 }
                16 { $day_value = $day_value -bor 0x8000 }
                17 { $day_value = $day_value -bor 0x10000 }
                18 { $day_value = $day_value -bor 0x20000 }
                19 { $day_value = $day_value -bor 0x40000 }
                20 { $day_value = $day_value -bor 0x80000 }
                21 { $day_value = $day_value -bor 0x100000 }
                22 { $day_value = $day_value -bor 0x200000 }
                23 { $day_value = $day_value -bor 0x400000 }
                24 { $day_value = $day_value -bor 0x800000 }
                25 { $day_value = $day_value -bor 0x1000000 }
                26 { $day_value = $day_value -bor 0x2000000 }
                27 { $day_value = $day_value -bor 0x4000000 }
                28 { $day_value = $day_value -bor 0x8000000 }
                29 { $day_value = $day_value -bor 0x10000000 }
                30 { $day_value = $day_value -bor 0x20000000 }
                31 { $day_value = $day_value -bor 0x40000000 }
                default { Fail-Json -obj $result -message "invalid day of month '$day', please specify numbers from 1-31" }
            }
        }
        if ($day_value -eq 0) {
            $day_value = $null
        }
        $trigger.days_of_month = $day_value
    }
    if ($trigger.ContainsKey("weeks_of_month")) {
        $weeks = $trigger.weeks_of_month
        if ($weeks -is [String]) {
            $weeks = $weeks.Split(",").Trim()
        } elseif ($weeks -isnot [Array]) {
            $weeks = @($weeks)
        }

        $week_value = 0
        foreach ($week in $weeks) {
            # https://msdn.microsoft.com/en-us/library/windows/desktop/aa382061(v=vs.85).aspx
            switch ($week) {
                1 { $week_value = $week_value -bor 0x01 }
                2 { $week_value = $week_value -bor 0x02 }
                3 { $week_value = $week_value -bor 0x04 }
                4 { $week_value = $week_value -bor 0x08 }
                default { Fail-Json -obj $result -message "invalid week of month '$week', please specify weeks from 1-4" }
            }

        }
        if ($week_value -eq 0) {
            $week_value = $null
        }
        $trigger.weeks_of_month = $week_value
    }
    if ($trigger.ContainsKey("months_of_year")) {
        $months = $trigger.months_of_year
        if ($months -is [String]) {
            $months = $months.Split(",").Trim()
        } elseif ($months -isnot [Array]) {
            $months = @($months)
        }

        $month_value = 0
        foreach ($month in $months) {
            # https://msdn.microsoft.com/en-us/library/windows/desktop/aa382064(v=vs.85).aspx
            switch ($month) {
                january { $month_value = $month_value -bor 0x01 }
                february { $month_value = $month_value -bor 0x02 }
                march { $month_value = $month_value -bor 0x04 }
                april { $month_value = $month_value -bor 0x08 }
                may { $month_value = $month_value -bor 0x10 }
                june { $month_value = $month_value -bor 0x20 }
                july { $month_value = $month_value -bor 0x40 }
                august { $month_value = $month_value -bor 0x80 }
                september { $month_value = $month_value -bor 0x100 }
                october { $month_value = $month_value -bor 0x200 }
                november { $month_value = $month_value -bor 0x400 }
                december { $month_value = $month_value -bor 0x800 }
                default { Fail-Json -obj $result -message "invalid month name '$month', please specify full month name" }
            }
        }
        if ($month_value -eq 0) {
            $month_value = $null
        }
        $trigger.months_of_year = $month_value
    }
    $triggers[$i] = $trigger
}

# add \ to start of path if it is not already there
if (-not $path.StartsWith("\")) {
    $path = "\$path"
}
# ensure path does not end with \ if more than 1 char
if ($path.EndsWith("\") -and $path.Length -ne 1) {
    $path = $path.Substring(0, $path.Length - 1)
}

########################
### START CODE BLOCK ###
########################
$service = New-Object -ComObject Schedule.Service
try {
    $service.Connect()
} catch {
    Fail-Json -obj $result -message "failed to connect to the task scheduler service: $($_.Exception.Message)"
}

# check that the path for the task set exists, create if need be
try {
    $task_folder = $service.GetFolder($path)
} catch {
    $task_folder = $null
}

# try and get the task at the path
$task = Test-TaskExists -task_folder $task_folder -name $name
$task_path = Join-Path -Path $path -ChildPath $name

if ($state -eq "absent") {
    if ($task -ne $null) {
        if (-not $check_mode) {
            try {
                $task_folder.DeleteTask($name, 0)
            } catch {
                Fail-Json -obj $result -message "failed to delete task '$name' at path '$path': $($_.Exception.Message)"
            }
        }
        if ($diff_mode) {
            $result.diff.prepared = "-[Task]`n-$task_path`n"
        }
        $result.changed = $true

        # check if current folder has any more tasks
        $other_tasks = $task_folder.GetTasks(1) # 1 = TASK_ENUM_HIDDEN
        if ($other_tasks.Count -eq 0 -and $task_folder.Name -ne "\") {
            try {
                $task_folder.DeleteFolder($null, $null)
            } catch {
                Fail-Json -obj $result -message "failed to delete empty task folder '$path' after task deletion: $($_.Exception.Message)"
            }
        }
    }
} else {
    if ($task -eq $null) {
        $create_diff_string = "+[Task]`n+$task_path`n`n"
        # to create a bare minimum task we need 1 action
        if ($actions -eq $null -or $actions.Count -eq 0) {
            Fail-Json -obj $result -message "cannot create a task with no actions, set at least one action with a path to an executable"
        }

        # Create a bare minimum task here, further properties will be set later on
        $task_definition = $service.NewTask(0)

        # Set Actions info
        # https://msdn.microsoft.com/en-us/library/windows/desktop/aa446803(v=vs.85).aspx
        $create_diff_string += "[Actions]`n"
        $task_actions = $task_definition.Actions
        foreach ($action in $actions) {
            $create_diff_string += "+action[0] = {`n  +Type=$([TASK_ACTION_TYPE]::TASK_ACTION_EXEC),`n  +Path=$($action.path)`n"
            $task_action = $task_actions.Create([TASK_ACTION_TYPE]::TASK_ACTION_EXEC)
            $task_action.Path = $action.path
            if ($action.arguments -ne $null) {
                $create_diff_string += "  +Arguments=$($action.arguments)`n"
                $task_action.Arguments = $action.arguments
            }
            if ($action.working_directory -ne $null) {
                $create_diff_string += "  +WorkingDirectory=$($action.working_directory)`n"
                $task_action.WorkingDirectory = $action.working_directory
            }
            $create_diff_string += "+}`n"
        }

        # Register the new task
        # https://msdn.microsoft.com/en-us/library/windows/desktop/aa382577(v=vs.85).aspx
        if ($check_mode) {
            # Only validate the task in check mode
            $task_creation_flags = [TASK_CREATION]::TASK_VALIDATE_ONLY
        } else {
            # Create the task but do not fire it as we still need to configure it further below
            $task_creation_flags = [TASK_CREATION]::TASK_CREATE -bor [TASK_CREATION]::TASK_IGNORE_REGISTRATION_TRIGGERS
        }

        # folder doesn't exist, need to create
        if ($task_folder -eq $null) {
            $task_folder = $service.GetFolder("\")
            try {
                if (-not $check_mode) {
                    $task_folder = $task_folder.CreateFolder($path)
                }                
            } catch {
                Fail-Json -obj $result -message "failed to create new folder at path '$path': $($_.Exception.Message)"
            }
        }

        try {
            $task = $task_folder.RegisterTaskDefinition($name, $task_definition, $task_creation_flags, $null, $null, $null)
        } catch {
            Fail-Json -obj $result -message "failed to register new task definition: $($_.Exception.Message)"
        }
        if ($diff_mode) {
            $result.diff.prepared = $create_diff_string
        }

        $result.changed = $true
    }

    # we cannot configure a task that was created above in check mode as it
    # won't actually exist
    if ($task) {
        $task_definition = $task.Definition
        $task_definition_xml = [xml]$task_definition.XmlText

        $action_changes = Compare-Actions -task_definition $task_definition
        $principal_changed = Compare-Principal -task_definition $task_definition -task_definition_xml $task_definition_xml
        $reg_info_changed = Compare-RegistrationInfo -task_definition $task_definition
        $settings_changed = Compare-Settings -task_definition $task_definition
        $trigger_changes = Compare-Triggers -task_definition $task_definition

        # compile the diffs into one list with headers
        $task_diff = [System.Collections.ArrayList]@()        
        if ($action_changes.Count -gt 0) {
            [void]$task_diff.Add("[Actions]")
            foreach ($action_change in $action_changes) {
                [void]$task_diff.Add($action_change)
            }
            [void]$task_diff.Add("`n")
        }
        if ($principal_changed.Count -gt 0) {
            [void]$task_diff.Add("[Principal]")
            foreach ($principal_change in $principal_changed) {
                [void]$task_diff.Add($principal_change)
            }
            [void]$task_diff.Add("`n")
        }
        if ($reg_info_changed.Count -gt 0) {
            [void]$task_diff.Add("[Registration Info]")
            foreach ($reg_info_change in $reg_info_changed) {
                [void]$task_diff.Add($reg_info_change)
            }
            [void]$task_diff.Add("`n")
        }
        if ($settings_changed.Count -gt 0) {
            [void]$task_diff.Add("[Settings]")
            foreach ($settings_change in $settings_changed) {
                [void]$task_diff.add($settings_change)
            }
            [void]$task_diff.Add("`n")
        }
        if ($trigger_changes.Count -gt 0) {
            [void]$task_diff.Add("[Triggers]")
            foreach ($trigger_change in $trigger_changes) {
                [void]$task_diff.Add("$trigger_change")
            }
            [void]$task_diff.Add("`n")
        }

        if ($password -ne $null -and (($update_password -eq $true) -or ($task_diff.Count -gt 0))) {
            # because we can't compare the passwords we just need to reset it
            $register_username = $username
            $register_password = $password
            $register_logon_type = $task_principal.LogonType
        } else {
            # will inherit from the Principal property values
            $register_username = $null
            $register_password = $null
            $register_logon_type = $null
        }
        
        if ($task_diff.Count -gt 0 -or $register_password -ne $null) {
            if ($check_mode) {
                # Only validate the task in check mode
                $task_creation_flags = [TASK_CREATION]::TASK_VALIDATE_ONLY
            } else {
                # Create the task
                $task_creation_flags = [TASK_CREATION]::TASK_CREATE_OR_UPDATE
            }
            try {
                $task_folder.RegisterTaskDefinition($name, $task_definition, $task_creation_flags, $register_username, $register_password, $register_logon_type) | Out-Null
            } catch {
                Fail-Json -obj $result -message "failed to modify scheduled task: $($_.Exception.Message)"
            }
            
            $result.changed = $true

            if ($diff_mode) {
                $changed_diff_text = $task_diff -join "`n"
                if ($result.diff.prepared -ne $null) {
                    $diff_text = "$($result.diff.prepared)`n$changed_diff_text"
                } else {
                    $diff_text = $changed_diff_text
                }
                $result.diff.prepared = $diff_text.Trim()
            }
        }
    }
}

Exit-Json -obj $result
