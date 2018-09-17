#!powershell

# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

Set-StrictMode -Version 2

#region functions


    function Confirm-RotationPeriod {
        param(
            $ConfigurationPath,
            $RotationPeriod,
            $TruncateSize,
            [bool]$WhatIf = $false
        )

        
        
        if (-not [String]::IsNullOrEmpty($RotationPeriod)) {
            $validValues = @("Hourly","Daily","Weekly","Monthly","MaxSize","Disabled")
            if ($validValues -notcontains $RotationPeriod)
            {
                Fail-json $result "invalid value supplied for 'rotation_period': must be one of: $($validValues -join ',')"
            }
            if ($RotationPeriod -eq "Disabled"){
                $RotationPeriod = "MaxSize"
                $TruncateSize = 4294967295
            }
            $ConfigurationPath = "$ConfigurationPath/logFile"
            $LogProperties = $(Get-WebConfiguration -Filter $ConfigurationPath)
            
            $changed = $false
            if($LogProperties.period -ne $RotationPeriod ){
                if(-not $WhatIf) {
                    Set-WebConfigurationProperty -Filter $ConfigurationPath -Name period -Value $RotationPeriod
                }
                $changed =  $true
            }
            if($RotationPeriod -eq "MaxSize" -and $LogProperties.truncateSize -ne $TruncateSize){
                if(-not $WhatIf) {
                    Set-WebConfigurationProperty -Filter $ConfigurationPath -Name truncateSize -Value $TruncateSize
                }
                $changed =  $true
            }
            return  $changed
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

       

        $loggedFieldsProperty = $(Get-WebConfigurationProperty -Filter $ConfigurationPath  -Name logExtFileFlags)
       
        if ($loggedFieldsProperty -is [Microsoft.IIs.PowerShell.Framework.ConfigurationAttribute])
        {
            $loggedFields = @()
        }
        else {
            $loggedFields =  $loggedFieldsProperty -split ','
        }

        $fieldsToAdd = @()
        $fieldsToRemove = @()
        $changed = $false
        
        foreach ($ExtFileFlag in $ExtFileFlags) {
            # First ensure this list member has the properties we expect
            if (-not (
                [bool]($ExtFileFlag.PSobject.Properties.name -match "field_name") -and
                [bool]($ExtFileFlag.PSobject.Properties.name -match "state"))
                ){
                Fail-Json $result "Ojects in log_ext_file_flags must have 'field_name', and 'state' property"
            }

            # Check if the field exists and shouldn't
            if ($ExtFileFlag.state -eq 'present' -and -not ($loggedFields -contains $ExtFileFlag.field_name))
            {
               
                if ($allowedFields -notcontains ($ExtFileFlag.field_name)) {
                    Fail-Json $result "Cannot add field $($ExtFileFlag.field_name) because it is not recogized by IIS"
                }
                $changed=$true
                $fieldsToAdd += ($ExtFileFlag.field_name)
                
            }
            elseif ($ExtFileFlag.state -eq 'absent') {
                if ($allowedFields -notcontains ($ExtFileFlag.field_name)) {
                    Add-Warning -obj $result -message "Field $($ExtFileFlag.field_name) selected for removal, but is not recognized by IIS"
                    #Fail-Json $result "Cannot remove field $($ExtFileFlag.field_name) because it is not recogized by IIS"
                }
                elseif ($loggedFields -contains $ExtFileFlag.field_name) {
                   
                    $changed=$true
                    $fieldsToRemove += ($ExtFileFlag.field_name)
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
                
                Set-WebConfigurationProperty -Filter $ConfigurationPath -Name logExtFileFlags -Value $newString
                return $true
            }
        }
    }

    function Confirm-CustomFields {
        param(
            $ConfigurationPath,
            $CustomFields,
            [bool]$WhatIf = $false
        )

        if ($CustomFields.count -gt 0 ) {
            $LogFileMode = $(Get-WebConfiguration -Filter "/system.applicationHost/log").centralLogFileMode
            if ($LogFileMode -ne "Site"){
                Fail-Json $result "Custom Fields are not availabe when configured to one log per server. Hint: set central_log_file_mode to 'Site'"
            }
        }
        $ConfigurationPath = "$ConfigurationPath/customFields"
        $CurrentCustomFields = $(Get-WebConfiguration -Filter $ConfigurationPath).Collection

       

        $fieldsToAdd = @()
        $fieldsToUpdate = @()
        $fieldsToRemove = @()
        $CustomFieldsChanged = $false

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
                $CustomFieldsChanged=$true
                $fieldsToRemove += ($CustomField)
            }
            elseif ($CustomField.state -eq 'present' -and -not ($CurrentCustomFields | Where-Object {$_.logFieldName -eq $CustomField.field_name}))
            {
                $CustomFieldsChanged=$true
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
                    $CustomFieldsChanged=$true
                    $fieldsToUpdate += ($CustomField)
                }
                
            }
        }

        if ($CustomFieldsChanged)
            {
                if ($WhatIf)
                {
                   return $true
                }
               
                else {

                    $fieldsToAdd | Foreach-Object {
                        Add-WebConfigurationProperty -filter  $ConfigurationPath -name "." -value @{logFieldName=$_.field_name;sourceName=$_.source_name;sourceType=$_.source_type}
                    }

                    $fieldsToUpdate | Foreach-Object {
                        Set-WebConfigurationProperty -filter  $ConfigurationPath -name "."  -AtElement @{logFieldName=$_.field_name} -value @{sourceName=$_.source_name;sourceType=$_.source_type}
                    }

                    $fieldsToRemove | Foreach-Object {
                        Remove-WebConfigurationProperty  -filter $ConfigurationPath -name "."  -AtElement @{logFieldName=$_.field_name}
                    }
                    
                    return $true
                }
            }
    }

    Function Test-ParameterSet {
        Param(
            $ValidParameters,
            $Parameters
        )
        $str = ''
        $Parameters.Keys | Foreach-Object {
            
            if ($_ -notlike "_ansible*"){
                if ($ValidParameters -notcontains $_) {
                    Fail-Json $result "Unexpected parameter: $_ not valid for this configuration context"
                }
            }
        }   
    }

    Function Confirm-WebConfigurationProperty {
        Param(
            $Filter,
            $Name,
            $Value,
            [bool]$WhatIf = $false
        )
        if (-not [String]::IsNullOrEmpty($Value)) {
            $CurrentValue = $(Get-WebConfigurationProperty -Filter $Filter -Name $Name)
            if($CurrentValue -ne $Value){
                if(-not $WhatIf) {
                    Set-WebConfigurationProperty -Filter $Filter -Name $Name -Value $Value
                }
                return $true
            }
        }
    }


#end region



$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$configuration = Get-AnsibleParam $params "configuration" -type "str" -default "server"
$site_name = Get-AnsibleParam $params "site_name" -type "str" -default "System"
$log_directory = Get-AnsibleParam $params "log_directory" -type "path" -default $null
$site_log_format = Get-AnsibleParam $params "site_log_format" -type "str" -default $null
$log_ext_file_flags = Get-AnsibleParam $params "log_ext_file_flags" -type "list" 
$log_custom_fields = Get-AnsibleParam $params "log_custom_fields" -type "list"
$use_local_time =  Get-AnsibleParam $params "use_local_time" -type "bool"  -default $null
$rotation_period = Get-AnsibleParam $params "rotation_period" -type "str" -default $null
$truncate_size = Get-AnsibleParam $params "truncate_size" -type "str" -default $null
$central_log_file_mode = Get-AnsibleParam $params "central_log_file_mode" -type "str" -default $null
$log_in_utf8 = Get-AnsibleParam $params "log_in_utf8" -type "bool" -default $null

$result = @{
    changed = $false
}
[bool]$changed = $false
$messages = @()
$shared_params = @()

if ($check_mode)
{
    $shared_params = @{'WhatIf'=$true}
}

if ($rotation_period -ne "MaxSize" -and $truncate_size -ne $null)
{
    Add-Warning -obj $result -message "truncate_size is of no effect when rotation_period is not 'MaxSize'"
}


if ($configuration -eq "server")
{   
    
    $validParameters = @("configuration","central_log_file_mode","log_in_utf8","log_directory","log_ext_file_flags","use_local_time","rotation_period","truncate_size")
    Test-ParameterSet -ValidParameters $validParameters -Parameters $params
    $ConfigurationPath ="/system.applicationHost/log"
    If ($central_log_file_mode -eq "CentralBinary") {
        $LogConfigurationPath = "/system.applicationHost/log/centralBinaryLogFile"
    }
    elseif ($central_log_file_mode -eq "CentralW3C") {
        $LogConfigurationPath = "/system.applicationHost/log/centralW3CLogFile"
    }
    $PropertiesToConfirm = @(
        [PSCustomObject]@{
            Filter = $ConfigurationPath;
            Name = "logInUTF8";
            Value = $log_in_utf8
        },
        [PSCustomObject]@{
            Filter = $ConfigurationPath;
            Name = "centralLogFileMode";
            Value = $central_log_file_mode
        })
    if (-not [String]::IsNullOrEmpty($LogConfigurationPath)) {
        $PropertiesToConfirm += @(
            [PSCustomObject]@{
                Filter = $LogConfigurationPath;
                Name = "localTimeRollover";
                Value = $use_local_time
            },
            
            [PSCustomObject]@{
                Filter = $LogConfigurationPath;
                Name = "directory";
                Value = $log_directory
            },
            [PSCustomObject]@{
                Filter = $LogConfigurationPath;
                Name = "period";
                Value = $rotation_period
            },
            [PSCustomObject]@{
                Filter = $LogConfigurationPath;
                Name = "truncateSize";
                Value = $truncate_size
            })
    }

    
    $PropertiesToConfirm | Foreach-Object {
        if ($(Confirm-WebConfigurationProperty -Name $_.Name -Filter $_.Filter -Value $_.Value))
        {
            $changed = $true
            $messages += $_.Name
        }
    }
}
elseif ( $configuration -eq "siteDefaults"){
    $validParameters = @("configuration","site_log_format","log_directory","log_ext_file_flags","log_custom_fields","use_local_time","rotation_period","truncate_size")
    Test-ParameterSet -ValidParameters $validParameters -Parmaeters $params
    $ConfigurationPath = '/system.applicationHost/sites/siteDefaults/logFile'
    $PropertiesToConfirm =@(
        [PSCustomObject]@{
            Filter = $ConfigurationPath;
            Name = "logFormat";
            Value = $site_log_format
        },
        [PSCustomObject]@{
            Filter = $ConfigurationPath;
            Name = "directory";
            Value = $log_directory
        },
        [PSCustomObject]@{
            Filter = $ConfigurationPath;
            Name = "localTimeRollover";
            Value = $use_local_time
        },
        [PSCustomObject]@{
            Filter = $ConfigurationPath;
            Name = "period";
            Value = $rotation_period
        },
        [PSCustomObject]@{
            Filter = $ConfigurationPath;
            Name = "truncateSize";
            Value = $truncate_size
        })

        $PropertiesToConfirm | Foreach-Object {
            if (Confirm-WebConfigurationProperty -Name $_.Name -Filter $_.Filter -Value $_.Value)
            {
                $changed = $true
                $messages += $_.Name
            }
        }

        if ($(Confirm-CustomFields -CustomFields $log_custom_fields -ConfigurationPath $ConfigurationPath)) {
            $changed = $true
            $messages += "Custom Fields"
        }

        if ($(Confirm-ExtFileFlags -ExtFileFlags $log_ext_file_flags -ConfigurationPath $ConfigurationPath)) {
            $changed = $true
            $messages += "Built-In Fields"
        }

        

    
}
elseif ($configuration -eq "site")
{
    $validParameters = @("configuration","site_name","site_log_format","log_directory","log_ext_file_flags","log_custom_fields","use_local_time","rotation_period","truncate_size")
    Test-ParameterSet -ValidParameters $validParameters -Parmaeters $params
    $ConfigurationPath = "/system.applicationHost/sites/site[@name='$site_name']"
}
else {
    Fail-Json $result "Invalid value specified for configuration.  Must be server, siteDefaults, or site"
}



if ($check_mode) {
    $result.msg = "check mode: "
}

if ($changed) {
    $result.msg = "$($result.msg)$($messages -join ';') changed"
    $result.changed = $true
}

Exit-Json $result