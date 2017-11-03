#!powershell
# (c) 2015, Trond Hindenes <trond@hindenes.com>, and others
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# WANT_JSON
# POWERSHELL_COMMON

#Temporary fix
#Set-StrictMode -Off

$params = Parse-Args $args -supports_check_mode $true
$result = @{
    changed = $false
}

#Check that we're on at least Powershell version 5
if ($PSVersionTable.PSVersion.Major -lt 5)
{
    Fail-Json -obj $Result -message "This module only runs on Powershell version 5 or higher"
}
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$resourcename = Get-AnsibleParam -obj $params -name "resource_name" -type "str" -failifempty $true -resultobj $result
$module_version = Get-AnsibleParam -obj $params -name "module_version" -type "str" -default "latest"

#From Ansible 2.3 onwards, params is now a Hash Array
$Attributes = $params.GetEnumerator() | 
    Where-Object {
        $_.key -ne "resource_name" -and
        $_.key -ne "module_version" -and
        $_.key -notlike "_ansible_*"
    }

if (!($Attributes))
{
    Fail-Json -obj $result -message "No attributes specified"
}

#Always return some basic info
$result["resource_name"] = $resourcename
$result["attributes"] = $Attributes
$result["reboot_required"] = $null


# Build Attributes Hashtable for DSC Resource Propertys
$Attrib = @{}
foreach ($key in $Attributes)
{
    $result[$key.name] = $key.value
    $Attrib.Add($Key.Key,$Key.Value)
}

$result["dsc_attributes"] = $attrib

$Config = @{
   Name = ($resourcename)
   Property = @{
        }
    }

#Get the latest version of the module
if ($module_version -eq "latest")
{
    $Resource = Get-DscResource -Name $resourcename -ErrorAction SilentlyContinue | sort Version | select -Last 1
}
else 
{
    $Resource = Get-DscResource -Name $resourcename -ErrorAction SilentlyContinue | where {$_.Version -eq $module_version}
}

if (!$Resource)
{
    if ($module_version -eq "latest")
    {
        Fail-Json -obj $result -message "Resource $resourcename not found"
    }
    else 
    {
        Fail-Json -obj $result -message "Resource $resourcename with version $module_version not found"
    }
    
}

#Get the Module that provides the resource. Will be used as
#mandatory argument for Invoke-DscResource
$Module =  @{ 
    ModuleName = $Resource.ModuleName
    ModuleVersion = $Resource.Version
}

# Binary resources are not working very well with that approach - need to guesstimate module name/version
if ( -not ($Module.ModuleName -or $Module.ModuleVersion)) {
    $Module = 'PSDesiredStateConfiguration'
}

#grab the module version if we can
try {
    if ($Resource.Module.Version)
    {
        $result["module_version"] = $Resource.Module.Version.ToString()
    }
}
catch {}


#Convert params to correct datatype and inject
$attrib.Keys | foreach-object {
    $Key = $_.replace("item_name", "name")
    $prop = $resource.Properties | where {$_.Name -eq $key}
    if (!$prop)
    {
        #If its a credential specified as "credential", Ansible will support credential_username and credential_password. Need to check for that
        $prop = $resource.Properties | where {$_.Name -eq $key.Replace("_username","")}
        if ($prop)
        {
            #We need to construct a cred object. At this point keyvalue is the username, so grab the password
            $PropUserNameValue = $attrib.Item($_)
            $PropPassword = $key.Replace("_username","_password")
            $PropPasswordValue = $attrib.$PropPassword

            $cred = New-Object System.Management.Automation.PSCredential ($PropUserNameValue, ($PropPasswordValue | ConvertTo-SecureString -AsPlainText -Force))
            [System.Management.Automation.PSCredential]$KeyValue = $cred
            $config.Property.Add($key.Replace("_username",""),$KeyValue)
        }
        ElseIf ($key.Contains("_password"))
        {
            #Do nothing. We suck in the password in the handler for _username, so we can just skip it.
        }
        Else
        {
            Fail-Json -obj $result -message "Property $key in resource $resourcename is not a valid property"
        }

    }
    ElseIf ($prop.PropertyType -eq "[string]")
    {
        [String]$KeyValue = $attrib.Item($_)
        $config.Property.Add($key,$KeyValue)
    }
    ElseIf ($prop.PropertyType -eq "[string[]]")
    {
        #KeyValue is an array of strings
        [String]$TempKeyValue = $attrib.Item($_)
        [String[]]$KeyValue = $TempKeyValue.Split(",").Trim()

        $config.Property.Add($key,$KeyValue)
    }
    ElseIf ($prop.PropertyType -eq "[UInt32[]]")
    {
        #KeyValue is an array of integers
        [String]$TempKeyValue = $attrib.Item($_)
        [UInt32[]]$KeyValue = $attrib.Item($_.split(",").Trim())
        $config.Property.Add($key,$KeyValue)
    }
    ElseIf ($prop.PropertyType -eq "[bool]")
    {
        if ($attrib.Item($_) -like "true")
        {
            [bool]$KeyValue = $true
        }
        ElseIf ($attrib.Item($_) -like "false")
        {
            [bool]$KeyValue = $false
        }
        $config.Property.Add($key,$KeyValue)
    }
    ElseIf ($prop.PropertyType -eq "[int]")
    {
        [int]$KeyValue = $attrib.Item($_)
        $config.Property.Add($key,$KeyValue)
    }
    ElseIf ($prop.PropertyType -eq "[CimInstance[]]")
    {
      #KeyValue is an array of CimInstance
      [CimInstance[]]$KeyVal = @()
      [String]$TempKeyValue = $attrib.Item($_)
      #Need to split on the string }, because some property values have commas in them
      [String[]]$KeyValueStr = $TempKeyValue -split("},")
      #Go through each string of properties and create a hash of them
      foreach($str in $KeyValueStr)
      {
        [string[]]$properties = $str.Split("{")[1].Replace("}","").Trim().Split([environment]::NewLine).Trim()
        $prph = @{}
        foreach($p in $properties)
        {
          $pArr = $p -split "="
          #if the value can be an int we must convert it to an int
          if([bool]($pArr[1] -as [int] -is [int]))
          {
              $prph.Add($pArr[0].Trim(),$pArr[1].Trim() -as [int])
          }
          else
          {
              $prph.Add($pArr[0].Trim(),$pArr[1].Trim())
          }
        }
        #create the new CimInstance
        $cim = New-CimInstance -ClassName $str.Split("{")[0].Trim() -Property $prph -ClientOnly
        #add the new CimInstance to the array
        $KeyVal += $cim
      }
      $config.Property.Add($key,$KeyVal)
    }
    ElseIf ($prop.PropertyType -eq "[Int32]")
    {
        # Add Supoort for Int32
        [int]$KeyValue = $attrib.Item($_)
        $config.Property.Add($key,$KeyValue)
    }
    ElseIf ($prop.PropertyType -eq "[UInt32]")
    {
        # Add Support for [UInt32]
        [UInt32]$KeyValue = $attrib.Item($_)
        $config.Property.Add($key,$KeyValue)
    }

  }

try
{
    #Defined variables in strictmode
    $TestError, $TestError = $null
    $TestResult = Invoke-DscResource @Config -Method Test -ModuleName $Module -ErrorVariable TestError -ErrorAction SilentlyContinue
    if ($TestError)
    {
       throw ($TestError[0].Exception.Message)
    }
    ElseIf (($TestResult.InDesiredState) -ne $true)
    {
        if ($check_mode -eq $False)
        {
            $SetResult = Invoke-DscResource -Method Set @Config -ModuleName $Module -ErrorVariable SetError -ErrorAction SilentlyContinue -WarningAction SilentlyContinue
            if ($SetError -and ($SetResult -eq $null))
            {
                #If SetError was filled, throw to exit out of the try/catch loop
                throw $SetError
            }
            $result["reboot_required"] = $SetResult.RebootRequired
        }
        $result["changed"] = $true
        if ($SetError)
        {
           throw ($SetError[0].Exception.Message)
        }
    }
}
Catch
{
    Fail-Json -obj $result -message $_[0].Exception.Message
}


#set-attr -obj $result -name "property" -value $property
Exit-Json -obj $result
