#!powershell

# Copyright: (c) 2015, Trond Hindenes <trond@hindenes.com>, and others
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Version 5

$ErrorActionPreference = "Stop"

$params = Parse-Args $args -supports_check_mode $true
$result = @{
    changed = $false
}

Function ConvertTo-HashtableFromPsCustomObject($psObject)
{
    $hashtable = @{}
    $psObject | Get-Member -MemberType *Property | ForEach-Object {
        $value = $psObject.($_.Name)
        if ($value -is [PSObject])
        {
            $value = ConvertTo-HashtableFromPsCustomObject -myPsObject $value
        }
        $hashtable.($_.Name) = $value
    }

    return ,$hashtable
}

Function Cast-ToCimInstance($name, $value, $className)
{
    # this converts a hashtable to a CimInstance
    if ($value -is [PSObject])
    {
        # convert to hashtable
        $value = ConvertTo-HashtableFromPsCustomObject -psObject $value
    }

    $valueType = $value.GetType()
    if ($valueType -ne [hashtable])
    {
        Fail-Json -obj $result -message "CimInstance value for property $name must be a hashtable, was $($valueType.FullName)"
    }

    try
    {
        $cim = New-CimInstance -ClassName $className -Property $value -ClientOnly        
    }
    catch
    {
        Fail-Json -obj $result -message "Failed to convert hashtable to CimInstance of $($className): $($_.Exception.Message)"
    }

    return ,$cim
}

Function Cast-Value($value, $type, $typeString, $name)
{
    if ($type -eq [CimInstance])
    {
        $newValue = Cast-ToCimInstance -name $name -value $value -className $typeString
    }
    ElseIf ($type -eq [CimInstance[]])
    {
        if ($value -isnot [array])
        {
            $value = @($value)
        }
        [CimInstance[]]$newValue = @()
        $baseTypeString = $typeString.Substring(0, $typeString.Length - 2)
        foreach ($cim in $value)
        {
            $newValue += Cast-ToCimInstance -name $name -value $cim -className $baseTypeString
        }
    }
    Else
    {
        $originalType = $value.GetType()
        if ($originalType -eq $type)
        {
            $newValue = $value
        }
        Else
        {
            $newValue = $value -as $type   
            if ($newValue -eq $null)
            {
                Add-Warning -obj $result -message "failed to cast property $name from '$value' of type $($originalType.FullName) to type $($type.FullName), the DSC engine may ignore this property with an invalid cast"
                $newValue = $value
            }
        }
    }

    return ,$newValue
}

Function Parse-DscProperty($name, $value, $resourceProp)
{
    $propertyTypeString = $resourceProp.PropertyType
    if ($propertyTypeString.StartsWith("["))
    {
        $propertyTypeString = $propertyTypeString.Substring(1, $propertyTypeString.Length - 2)
    }
    $propertyType = $propertyTypeString -as [type]

    # CimInstance and CimInstance[] are reperesented as the actual Cim
    # ClassName and the above returns a $null. We need to manually set the
    # type in these cases
    if ($propertyType -eq $null)
    {
        if ($propertyTypeString.EndsWith("[]"))
        {
            $propertyType = [CimInstance[]]
        }
        Else
        {
            $propertyType = [CimInstance]
        }
    }

    if ($propertyType.IsArray)
    {
        # convert the value to a list for later conversion
        if ($value -is [string])
        {
            $value = $value.Split(",").Trim()
        }
        ElseIf ($value -isnot [array])
        {
            $value = @($value)
        }
    }
    $newValue = Cast-Value -value $value -type $propertyType -typeString $propertyTypeString -name $name

    return ,$newValue
}

$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$resourcename = Get-AnsibleParam -obj $params -name "resource_name" -type "str" -failifempty $true
$module_version = Get-AnsibleParam -obj $params -name "module_version" -type "str" -default "latest"

#From Ansible 2.3 onwards, params is now a Hash Array
$Attributes = @{}
foreach ($param in $params.GetEnumerator())
{
    if ($param.Name -notin @("resource_name", "module_version") -and $param.Name -notlike "_ansible_*")
    {
        $Attributes[$param.Name] = $param.Value
    }
}

if ($Attributes.Count -eq 0)
{
    Fail-Json -obj $result -message "No attributes specified"
}

#Always return some basic info
$result["reboot_required"] = $false

$Config = @{
   Name = ($resourcename)
   Property = @{}
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
foreach ($attribute in $Attributes.GetEnumerator())
{
    $key = $attribute.Name.Replace("item_name", "name")
    $value = $attribute.Value
    $prop = $resource.Properties | Where-Object {$_.Name -eq $key}
    if (!$prop)
    {
        #If its a credential specified as "credential", Ansible will support credential_username and credential_password. Need to check for that
        $prop = $resource.Properties | Where-Object {$_.Name -eq $key.Replace("_username","")}
        if ($prop)
        {
            #We need to construct a cred object. At this point keyvalue is the username, so grab the password
            $PropUserNameValue = $value
            $PropPassword = $key.Replace("_username","_password")
            $PropPasswordValue = $Attributes.$PropPassword

            $KeyValue = New-Object System.Management.Automation.PSCredential ($PropUserNameValue, ($PropPasswordValue | ConvertTo-SecureString -AsPlainText -Force))
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
    Else
    {
        if ($value -eq $null)
        {
            $keyValue = $null
        }
        Else
        {
            $keyValue = Parse-DscProperty -name $key -value $value -resourceProp $prop
        }
        
        $config.Property.Add($key, $keyValue)
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

Exit-Json -obj $result
