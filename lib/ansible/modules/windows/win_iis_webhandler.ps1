#!powershell

# Copyright: (c) 2018, id27182
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#AnsibleRequires -OSVersion 6.2

$ErrorActionPreference = "Stop"

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$allowpathinfo = Get-AnsibleParam -obj $params -name "allow_path_info" -type "bool" -default "false"
$modules = Get-AnsibleParam -obj $params -name "modules" -type "str" -default "ManagedPipelineHandler"
$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$path = Get-AnsibleParam -obj $params -name "path" -type "str" -failifempty $true
$precondition = Get-AnsibleParam -obj $params -name "precondition" -type "str" -validateset 'bitness32', 'bitness64', 'integratedMode', 'ISAPIMode', 'runtimeVersionv1.1', 'runtimeVersionv2.0'
$requireaccess = Get-AnsibleParam -obj $params -name "require_access" -type "str" -default "Script" -validateset 'None', 'Read', 'Write', 'Script', 'Execute'
$resourcetype = Get-AnsibleParam -obj $params -name "resource_type" -type "str" -default "Unspecified" -validateset 'Directory', 'Either', 'File', 'Script', 'Unspecified'
$responsebufferlimit = Get-AnsibleParam -obj $params -name "response_buffer_limit" -type "int" -default "4194304"
$scriptprocessor = Get-AnsibleParam -obj $params -name "script_processor" -type "path"
$type = Get-AnsibleParam -obj $params -name "type" -type "str"
$verb = Get-AnsibleParam -obj $params -name "verb" -type "str" -failifempty $true
$applicationname = Get-AnsibleParam -obj $params -name "application_name" -type "str" -default ""
$sitename = Get-AnsibleParam -obj $params -name "site_name" -type "str" -default ""
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "absent","present"

$result = @{
    changed = $false
}

# Ensure WebAdministration PS module is installed
if (!(Get-Module -Name WebAdministration -ListAvailable)) {
    Fail-Json -obj $result -message "win_iis_webhandler requires WebAdministration PS module to be installed."
}
Import-Module -Name WebAdministration

# Define IIS path and Location tag
if (!$sitename -and !$applicationname) {
    $iispath = "IIS:\"
    $location = $null
}
elseif ($sitename -and !$applicationname) {
    if (!(Get-Website -Name $sitename)) {
        Fail-Json -obj $result -message "Specified site '$sitename' does not exist. Check site name and execute module again."
    }

    $iispath = "IIS:\Sites\$sitename"
    $location = $sitename
}
elseif (!$sitename -and $applicationname) {
    Fail-Json -obj $result -message "Application name '$applicationname' was specified without specifying site name. Please, specify both application name and site name and execute module again."
}
else {
    if (!(Get-Website -Name $sitename)) {
        Fail-Json -obj $result -message "Specified site '$sitename' does not exist. Check site name and execute module again."
    }
    else {
        if (!(Get-WebApplication -Site $sitename -Name $applicationname)) {
            Fail-Json -obj $result -message "Specified application '$applicationname' does not exist under site '$sitename'. Check application name and execute module again."
        }
    }

    $iispath = "IIS:\Sites\$sitename\$applicationname"
    $location = "$sitename\$applicationname"
}

# Ensure path to hanlder' scriptprocessor exist
if ($scriptprocessor) {
    if ((Test-Path -Path $scriptprocessor -PathType Leaf) -eq $false) {
        Fail-Json -obj $result -message "Path to handler scriptprocessor '$scriptprocessor' does not exist. Check path to handler' scriptprocessor and run module again."
    }
}

$specified_attributes = @{
    Name                = $name
    Path                = $path
    Verb                = $verb
    Type                = $type
    Modules             = $modules
    ScriptProcessor     = $scriptProcessor
    ResourceType        = $resourcetype
    RequireAccess       = $requireaccess
    AllowPathInfo       = $allowpathinfo
    PreCondition        = $precondition
    ResponseBufferLimit = [uint32]$responsebufferlimit
}

# IIS path to display in messages
if ($iispath -eq "IIS:\" -and !$location) {
    $iispath_for_messages = "root"
}
else {
    $iispath_for_messages = $iispath
}

#Get current status of web handler
try {
    $currentwebhandler = Get-WebHandler -Name $name -PSPath $iispath

}
catch {
    $ErrorMessage = "Failed to get info about webhandler '$name' in IIS on '$iispath_for_messages' path: $($_.Exception.Message)"
    Fail-Json -obj $result -message $ErrorMessage
}

#Check and set desired state
if ($state -eq 'present') {
    if (!$currentwebhandler) {
        #Get rid of $null values
        $attributes_to_set = @{}
        $specified_attributes.GetEnumerator() | ForEach-Object -Process {
            if ($_.Value) {
                $attributes_to_set.add($_.Key, $_.Value)
            }
        }

        try {
            if ($iispath -eq "IIS:\" -and !$location) {
                Add-WebConfigurationProperty -Filter 'system.webServer/handlers' -PSPath $iispath -Name . -Value $attributes_to_set -WhatIf:$check_mode
            }
            else {
                Add-WebConfigurationProperty -Filter 'system.webServer/handlers' -PSPath "IIS:\" -Name . -Value $attributes_to_set -Location $location -WhatIf:$check_mode
            }

            Add-Warning -obj $result -message "New webhandler '$name' was added to IIS on '$iispath_for_messages' path."
            $result.changed = $true
        }
        catch {
            $ErrorMessage = "Failed to create new webhandler '$name' in IIS on '$iispath_for_messages' path: $($_.Exception.Message)"
            Fail-Json -obj $result -message $ErrorMessage
        }
    }
    else {
        $current_webhandler_attributes = @{
            Name                = $currentwebhandler.name
            Path                = $currentwebhandler.path
            Verb                = $currentwebhandler.verb
            Type                = $currentwebhandler.type
            Modules             = $currentwebhandler.modules
            ScriptProcessor     = $currentwebhandler.scriptProcessor
            ResourceType        = $currentwebhandler.resourcetype
            RequireAccess       = $currentwebhandler.requireaccess
            AllowPathInfo       = $currentwebhandler.allowpathinfo
            PreCondition        = $currentwebhandler.precondition
            ResponseBufferLimit = $currentwebhandler.responsebufferlimit
        }

        $filter = "system.webServer/handlers/Add[@Name='$name']"
        $in_desired_state = $true
        foreach ($key in $current_webhandler_attributes.GetEnumerator()) {
            $keyName = $key.Name
            if ($specified_attributes[$keyName] -ne $current_webhandler_attributes[$keyName]) {   
                if (!$specified_attributes[$keyName] -and !$current_webhandler_attributes[$keyName]) {
                    Continue
                }
                elseif (($specified_attributes[$keyName] -and $current_webhandler_attributes[$keyName]) -or ($specified_attributes[$keyName] -and !$current_webhandler_attributes[$keyName])) {
                    $in_desired_state = $false
                    try {
                        if ($iispath -eq "IIS:\" -and !$location) {
                            Set-WebConfigurationProperty -Filter $filter -PSPath $iispath -Name $keyName -Value $specified_attributes[$keyName] -WhatIf:$check_mode
                        }
                        else {
                            Set-WebConfigurationProperty -Filter $filter -PSPath "IIS:\" -Name $keyName -Value $specified_attributes[$keyName] -Location $Location -WhatIf:$check_mode
                        }

                        Add-Warning -obj $result -message "Existing webhandler's '$name' property '$keyName' was edited in IIS on '$iispath_for_messages' path to be in desired state."
                        $result.changed = $true
                    }
                    catch {
                        $ErrorMessage = "Failed to set desired state for existing webhandler's '$name' for property '$keyName' in IIS on '$iispath_for_messages' path: $($_.Exception.Message)"
                        Fail-Json -obj $result -message $ErrorMessage
                    } 
                }
                else {
                    $in_desired_state = $false
                    try {
                        if ($iispath -eq "IIS:\" -and !$location) {
                            Clear-WebConfiguration -Filter "$filter/@$keyName" -PSPath $iispath -WhatIf:$check_mode
                        }
                        else {
                            Clear-WebConfiguration -Filter "$filter/@$keyName" -PSPath "IIS:\" -Location $Location -WhatIf:$check_mode
                        }

                        Add-Warning -obj $result -message "Existing webhandler's '$name' property '$keyName' was cleared in IIS on '$iispath_for_messages' path to be in desired state."
                        $result.changed = $true
                    }
                    catch {
                        $ErrorMessage = "Failed to clear existing webhandler's '$name' property '$keyName' in IIS on '$iispath_for_messages' path: $($_.Exception.Message)"
                        Fail-Json -obj $result -message $ErrorMessage
                    }
                }
            }
        }

        if ($in_desired_state -eq $true) {
            Add-Warning -obj $result -message "Existing webhandler '$name' in IIS on '$iispath_for_messages' path already in desired state."
        }
    }
}
else {
    if ($currentwebhandler) {
        try {
            if ($iispath -eq "IIS:\" -and !$location) {
                Remove-WebHandler -Name $name -PSPath $iispath -Confirm:$false -WhatIf:$check_mode
            }
            else {
                Remove-WebHandler -Name $name -PSPath "IIS:\" -Location $Location -Confirm:$false -WhatIf:$check_mode
            }

            Add-Warning -obj $result -message "Webhandler '$name' was removed from IIS on '$iispath_for_messages' path."
            $result.changed = $true
        }
        catch {
            $ErrorMessage = "Failed to remove webhandler '$name' from IIS on '$iispath_for_messages' path: $($_.Exception.Message)"
            Fail-Json -obj $result -message $ErrorMessage
        }
    }
    else {
        Add-Warning -obj $result -message "Webhandler '$name' is already removed from IIS on '$iispath_for_messages' path."
    }
}

# Result
$webhandler = Get-WebHandler -Name $name -PSPath $iispath

if ($webhandler) {
    $result.name = $webhandler.name
    $result.path = $webhandler.path
    $result.verb = $webhandler.verb
    $result.type = $webhandler.type
    $result.modules = $webhandler.modules
    $result.script_processor = $webhandler.scriptProcessor
    $result.resource_type = $webhandler.resourcetype
    $result.require_access = $webhandler.requireaccess
    $result.allow_path_info = $webhandler.allowpathinfo
    $result.precondition = $webhandler.precondition
    $result.response_buffer_limit = $webhandler.responsebufferlimit
    $result.state = "present"
}
else {
    $result.name = $name
    $result.state = "absent"
}

Exit-Json -obj $result
