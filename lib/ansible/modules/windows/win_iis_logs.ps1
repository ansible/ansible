#!powershell

# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

Set-StrictMode -Version 2

#region functions

    function Confirm-LocalTime {
        param(
            $ConfigurationPath,
            [Nullable[boolean]]$UseLocalTime,
            [bool]$WhatIf = $false
        )
        
        if (-not [String]::IsNullOrEmpty($UseLocalTime)) {
            $ConfigurationPath = '/system.applicationHost/sites/siteDefaults/logFile'
            $LogProperties = $(Get-WebConfiguration -Filter $ConfigurationPath)
            
            if($LogProperties.localTimeRollover -ne $UseLocalTime){
                if(-not $WhatIf) {
                    Set-WebConfigurationProperty -Filter '/system.applicationHost/sites/siteDefaults' -Name logfile.localTimeRollover -Value $UseLocalTime
                }
                return $true
            }
        }
    }
    function Confirm-LogDirectory {
        param(
            $ConfigurationPath,
            $LogDirectory,
            [bool]$WhatIf = $false
        )
        if (-not [String]::IsNullOrEmpty($LogDirectory)) {
            
            $LogProperties = Get-WebConfigurationProperty -Filter $ConfigurationPath  -Name logfile
            
            if($LogProperties.directory -ne $LogDirectory){
                if(-not $WhatIf) {
                    Set-WebConfigurationProperty -Filter '/system.applicationHost/sites/siteDefaults' -Name logfile.directory -Value $LogDirectory
                }
                return $true
            }
        }
    }

    function Confirm-ExtFileFlags {
        param(
            $ConfigurationPath,
            $ExtFileFlags,
            [bool]$WhatIf = $false
        )

        $allowedFields = @("Date","Time","ClientIP","UserName","SiteName","ComputerName","ServerIP","Method","UriStem","UriQuery","HttpStatus","Win32Status","BytesSent","BytesRecv","TimeTaken","ServerPort","UserAgent","Cookie","Referer","ProtocolVersion","Host","HttpSubStatus")


        if (-not ($ExtFileFlags -is [array])) {
            if ($ExtFileFlags -eq "all" ) {
                $ExtFileFlags = $allowedFields | ForEach-Object {
                    [PSCustomObject]@{
                        field_name=$_;
                        state="present"
                    }
                }
            }
            elseif ($ExtFileFlags -eq "none") {
                $ExtFileFlags = $allowedFields | ForEach-Object {
                    [PSCustomObject]@{
                        field_name=$_;
                        state="absent"
                    }
                }
            }
            else {
                Fail-Json $result "invalid value supplied for log_ext_file_flags: $log_ext_file_flags"
            }
        }
            
        $LogProperties = Get-WebConfigurationProperty -Filter $ConfigurationPath  -Name logfile
        $loggedFields = $LogProperties.logExtFileFlags -split ','
        

        $fieldsToAdd = @()
        $fieldsToRemove = @()
        $changed = $false
        
        foreach ($ExtFileFlag in $ExtFileFlags) {
            # First ensure this list member has the properties we expect
            if (-not ([bool]($ExtFileFlag.PSobject.Properties.name -match "field_name") -and
            [bool]($ExtFileFlag.PSobject.Properties.name -match "state"))){
                Fail-Json $result "Ojects in log_ext_file_flags must have 'field_name' and 'state' property"
            }

            # Check if the field exists and shouldn't
            if ($ExtFileFlag.state -eq 'present' -and -not ($loggedFields -contains $ExtFileFlag.field_name))
            {
                $changed=$true
                if ($allowedFields -notcontains ($ExtFileFlag.field_name)) {
                    Fail-Json $result "Cannot add field $($ExtFileFlag.field_name) because it is not recogized by IIS"
                }
                $fieldsToAdd += ($ExtFileFlag.field_name)
            }
            elseif ($ExtFileFlag.state -eq 'absent' -and ($loggedFields -contains $ExtFileFlag.field_name)) {
                $changed=$true
                $fieldsToRemove += ($ExtFileFlag.field_name)
            }
        }

        if ($changed)
        {
            if ($WhatIf)
            {
                return $true
            }
            
            else {
                $newLoggedFields = @()
                $loggedFields |
                    Where-Object { $fieldsToRemove -notcontains $_ } | 
                    Foreach-Object { 
                        $newLoggedFields += $_
                    }
                $fieldsToAdd | Foreach-Object {
                    $newLoggedFields += $_
                }
            
                $newString = $( $newLoggedFields | Where-Object {$_}) -join ','
                Set-WebConfigurationProperty -Filter '/system.applicationHost/sites/siteDefaults' -Name  logfile.logExtFileFlags -Value $newString
                return $true
            }
        }
    }

    function Confirm-CustomFields {
        param(
            $CustomFields,
            [bool]$WhatIf = $false
        )
        $ConfigurationPath = '/system.applicationHost/sites/siteDefaults/logFile/customFields'
        $CurrentCustomFields = $(Get-WebConfiguration -Filter $ConfigurationPath).Collection

        $fieldsToAdd = @()
        $fieldsToUpdate = @()
        $fieldsToRemove = @()
        $changed = $false

        foreach ($CustomField in $CustomFields) {
            # First ensure this list member has the properties we expect
            if (-not (
                    [bool]($CustomField.PSobject.Properties.name -match "field_name") -and
                    [bool]($CustomField.PSobject.Properties.name -match "source_type") -and
                    [bool]($CustomField.PSobject.Properties.name -match "source_name") -and
                    [bool]($CustomField.PSobject.Properties.name -match "state"))

                )
            {
                Fail-Json $result "Ojects in log_custom_fields must have 'field_name', 'source_type', 'source_name', and 'state' properties"
            }

            if ($CustomField.state -eq 'absent' -and ($CurrentCustomFields | Where-Object {$_.logFieldName -eq $CustomField.field_name})) {
                $changed=$true
                $fieldsToRemove += ($CustomField)
            }
            elseif ($CustomField.state -eq 'present' -and -not ($CurrentCustomFields | Where-Object {$_.logFieldName -eq $CustomField.field_name}))
            {
                $changed=$true
                $fieldsToAdd += ($CustomField)
            }
            elseif ($CustomField.state -eq 'present')
            {
                $CurrentCustomField = $CurrentCustomFields | Where-Object {$_.logFieldName -eq $CustomField.field_name}
                if (
                    ($CurrentCustomField.logFieldName -eq $CustomField.field_name) -and
                    ($CurrentCustomField.sourceName -eq $CustomField.source_name) -and
                    ($CurrentCustomField.sourceType -eq $CustomField.source_type)
                ) {

                }
                else {
                    $changed=$true
                    $fieldsToUpdate += ($CustomField)
                }
                
            }
        }

        if ($changed)
            {
                if ($WhatIf)
                {
                   return $true
                }
               
                else {

                    $fieldsToAdd | Foreach-Object {
                        Add-WebConfigurationProperty -pspath 'MACHINE/WEBROOT/APPHOST'  -filter "system.applicationHost/sites/siteDefaults/logFile/customFields" -name "." -value @{logFieldName=$_.field_name;sourceName=$_.source_name;sourceType=$_.source_type}
                    }

                    $fieldsToUpdate | Foreach-Object {
                        Set-WebConfigurationProperty -pspath 'MACHINE/WEBROOT/APPHOST' -filter "system.applicationHost/sites/siteDefaults/logFile/customFields" -name "."  -AtElement @{logFieldName=$_.field_name} -value @{sourceName=$_.source_name;sourceType=$_.source_type}
                    }

                    $fieldsToRemove | Foreach-Object {
                        Remove-WebConfigurationProperty -pspath 'MACHINE/WEBROOT/APPHOST' -filter "system.applicationHost/sites/siteDefaults/logFile/customFields" -name "."  -AtElement @{logFieldName=$_.field_name}
                    }
                    
                    return $true
                }
            } 
    }
#end region



$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$debug_level = Get-AnsibleParam -obj $params -name "_ansible_verbosity" -type "int"
$debug = $debug_level -gt 2

$site_name = Get-AnsibleParam $params "site_name" -type "str" -default "System" -aliases "dest", "file"
$log_directory = Get-AnsibleParam $params "log_directory" -type "path" -default $null
$log_format = Get-AnsibleParam $params "log_format" -type "path" -default "W3C"
$log_ext_file_flags = Get-AnsibleParam $params "log_ext_file_flags" -type "list" 
$log_custom_fields = Get-AnsibleParam $params "log_custom_fields" -type "list"
$use_local_time =  Get-AnsibleParam $params "use_local_time" -type "bool"  -default $null

$result = @{
    changed = $false
}
[bool]$changed = $false
$messages = @()
$shared_params = @()

if ($site_name -eq "System") {
    
    $ConfigurationPath = '/system.applicationHost/sites/siteDefaults'
    if ($check_mode)
    {
        $shared_params = @{'WhatIf'=$true}
    }
    
    if($(Confirm-LogDirectory -ConfigurationPath $ConfigurationPath -LogDirectory $log_directory @shared_params))
    {
        $changed = $true
        $messages += "LogDirectory"
    }

    if($(Confirm-ExtFileFlags -ConfigurationPath $ConfigurationPath -ExtFileFlags $log_ext_file_flags @shared_params))
    {
        $changed = $true
        $messages += "Log Fields"
    }

    if($(Confirm-CustomFields -CustomFields $log_custom_fields @shared_params))
    {
        $changed = $true
        $messages += "Custom Fields"
    }

    if($(Confirm-LocalTime -UseLocalTime $use_local_time @shared_params)){
        $changed = $true
        $messages += "Use Local Time"
    }

    if ($check_mode) {
        $result.msg = "check mode: "
    }
    
    if ($changed) {
        $result.msg = "$($result.msg)$($messages -join ';') changed"
        $result.changed = $true
    }
}
else {
    Fail-Json $result "Site does not exist"
}

Exit-Json $result