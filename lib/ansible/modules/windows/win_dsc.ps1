#!powershell

# Copyright: (c) 2015, Trond Hindenes <trond@hindenes.com>, and others
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Version 5

Function ConvertTo-ArgSpecType {
    <#
    .SYNOPSIS
    Converts the DSC parameter type to the arg spec type required for Ansible.
    #>
    param(
        [Parameter(Mandatory=$true)][String]$CimType
    )

    $arg_type = switch($CimType) {
        Boolean { "bool" }
        Char16 { [Func[[Object], [Char]]]{ [System.Char]::Parse($args[0].ToString()) } }
        DateTime { [Func[[Object], [DateTime]]]{ [System.DateTime]($args[0].ToString()) } }
        Instance { "dict" }
        Real32 { "float" }
        Real64 { [Func[[Object], [Double]]]{ [System.Double]::Parse($args[0].ToString()) } }
        Reference { "dict" }
        SInt16 { [Func[[Object], [Int16]]]{ [System.Int16]::Parse($args[0].ToString()) } }
        SInt32 { "int" }
        SInt64 { [Func[[Object], [Int64]]]{ [System.Int64]::Parse($args[0].ToString()) } }
        SInt8 { [Func[[Object], [SByte]]]{ [System.SByte]::Parse($args[0].ToString()) } }
        String { "str" }
        UInt16 { [Func[[Object], [UInt16]]]{ [System.UInt16]::Parse($args[0].ToString()) } }
        UInt32 { [Func[[Object], [UInt32]]]{ [System.UInt32]::Parse($args[0].ToString()) } }
        UInt64 { [Func[[Object], [UInt64]]]{ [System.UInt64]::Parse($args[0].ToString()) } }
        UInt8 { [Func[[Object], [Byte]]]{ [System.Byte]::Parse($args[0].ToString()) } }
        Unknown { "raw" }
        default { "raw" }
    }
    return $arg_type
}

Function Get-DscCimClassProperties {
    <#
    .SYNOPSIS
    Get's a list of CimProperties of a CIM Class. It filters out any magic or
    read only properties that we don't need to know about.
    #>
    param([Parameter(Mandatory=$true)][String]$ClassName)

    $resource = Get-CimClass -ClassName $ClassName -Namespace root\Microsoft\Windows\DesiredStateConfiguration

    # Filter out any magic properties that are used internally on an OMI_BaseResource
    # https://github.com/PowerShell/PowerShell/blob/master/src/System.Management.Automation/DscSupport/CimDSCParser.cs#L1203
    $magic_properties = @("ResourceId", "SourceInfo", "ModuleName", "ModuleVersion", "ConfigurationName")
    $properties = $resource.CimClassProperties | Where-Object {

        ($resource.CimSuperClassName -ne "OMI_BaseResource" -or $_.Name -notin $magic_properties) -and
        -not $_.Flags.HasFlag([Microsoft.Management.Infrastructure.CimFlags]::ReadOnly)
    }

    return ,$properties
}

Function Add-PropertyOption {
    <#
    .SYNOPSIS
    Adds the spec for the property type to the existing module specification.
    #>
    param(
        [Parameter(Mandatory=$true)][Hashtable]$Spec,
        [Parameter(Mandatory=$true)]
        [Microsoft.Management.Infrastructure.CimPropertyDeclaration]$Property
    )

    $option = @{
        required = $false
    }
    $property_name = $Property.Name
    $property_type = $Property.CimType.ToString()

    if ($Property.Flags.HasFlag([Microsoft.Management.Infrastructure.CimFlags]::Key) -or
        $Property.Flags.HasFlag([Microsoft.Management.Infrastructure.CimFlags]::Required)) {
        $option.required = $true
    }

    if ($null -ne $Property.Qualifiers['Values']) {
        $option.choices = [System.Collections.Generic.List`1[Object]]$Property.Qualifiers['Values'].Value
    }

    if ($property_name -eq "Name") {
        # For backwards compatibility we support specifying the Name DSC property as item_name
        $option.aliases = @("item_name")
    } elseif ($property_name -ceq "key") {
        # There seems to be a bug in the CIM property parsing when the property name is 'Key'. The CIM instance will
        # think the name is 'key' when the MOF actually defines it as 'Key'. We set the proper casing so the module arg
        # validator won't fire a case sensitive warning
        $property_name = "Key"
    }

    if ($Property.ReferenceClassName -eq "MSFT_Credential") {
        # Special handling for the MSFT_Credential type (PSCredential), we handle this with having 2 options that
        # have the suffix _username and _password.
        $option_spec_pass = @{
            type = "str"
            required = $option.required
            no_log = $true
        }
        $Spec.options."$($property_name)_password" = $option_spec_pass
        $Spec.required_together.Add(@("$($property_name)_username", "$($property_name)_password")) > $null

        $property_name = "$($property_name)_username"
        $option.type = "str"
    } elseif ($Property.ReferenceClassName -eq "MSFT_KeyValuePair") {
        $option.type = "dict"
    } elseif ($property_type.EndsWith("Array")) {
        $option.type = "list"
        $option.elements = ConvertTo-ArgSpecType -CimType $property_type.Substring(0, $property_type.Length - 5)
    } else {
        $option.type = ConvertTo-ArgSpecType -CimType $property_type
    }

    if (($option.type -eq "dict" -or ($option.type -eq "list" -and $option.elements -eq "dict")) -and
            $Property.ReferenceClassName -ne "MSFT_KeyValuePair") {
        # Get the sub spec if the type is a Instance (CimInstance/dict)
        $sub_option_spec = Get-OptionSpec -ClassName $Property.ReferenceClassName
        $option += $sub_option_spec
    }

    $Spec.options.$property_name = $option
}

Function Get-OptionSpec {
    <#
    .SYNOPSIS
    Generates the specifiec used in AnsibleModule for a CIM MOF resource name.

    .NOTES
    This won't be able to retrieve the default values for an option as that is not defined in the MOF for a resource.
    Default values are still preserved in the DSC engine if we don't pass in the property at all, we just can't report
    on what they are automatically.
    #>
    param(
        [Parameter(Mandatory=$true)][String]$ClassName
    )

    $spec = @{
        options = @{}
        required_together = [System.Collections.ArrayList]@()
    }
    $properties = Get-DscCimClassProperties -ClassName $ClassName
    foreach ($property in $properties) {
        Add-PropertyOption -Spec $spec -Property $property
    }

    return $spec
}

Function ConvertTo-CimInstance {
    <#
    .SYNOPSIS
    Converts a dict to a CimInstance of the specified Class. Also provides a
    better error message if this fails that contains the option name that failed.
    #>
    param(
        [Parameter(Mandatory=$true)][String]$Name,
        [Parameter(Mandatory=$true)][String]$ClassName,
        [Parameter(Mandatory=$true)][System.Collections.IDictionary]$Value,
        [Parameter(Mandatory=$true)][Ansible.Basic.AnsibleModule]$Module,
        [Switch]$Recurse
    )

    $properties = @{}
    foreach ($value_info in $Value.GetEnumerator()) {
        # Need to remove all null values from existing dict so the conversion works
        if ($null -eq $value_info.Value) {
            continue
        }
        $properties.($value_info.Key) = $value_info.Value
    }

    if ($Recurse) {
        # We want to validate and convert and values to what's required by DSC
        $properties = ConvertTo-DscProperty -ClassName $ClassName -Params $properties -Module $Module
    }

    try {
        return (New-CimInstance -ClassName $ClassName -Property $properties -ClientOnly)
    } catch {
        # New-CimInstance raises a poor error message, make sure we mention what option it is for
        $Module.FailJson("Failed to cast dict value for option '$Name' to a CimInstance: $($_.Exception.Message)", $_)
    }
}

Function ConvertTo-DscProperty {
    <#
    .SYNOPSIS
    Converts the input module parameters that have been validated and casted
    into the types expected by the DSC engine. This is mostly done to deal with
    types like PSCredential and Dictionaries.
    #>
    param(
        [Parameter(Mandatory=$true)][String]$ClassName,
        [Parameter(Mandatory=$true)][System.Collections.IDictionary]$Params,
        [Parameter(Mandatory=$true)][Ansible.Basic.AnsibleModule]$Module
    )
    $properties = Get-DscCimClassProperties -ClassName $ClassName

    $dsc_properties = @{}
    foreach ($property in $properties) {
        $property_name = $property.Name
        $property_type = $property.CimType.ToString()

        if ($property.ReferenceClassName -eq "MSFT_Credential") {
            $username = $Params."$($property_name)_username"
            $password = $Params."$($property_name)_password"

            # No user set == No option set in playbook, skip this property
            if ($null -eq $username) {
                continue
            }
            $sec_password = ConvertTo-SecureString -String $password -AsPlainText -Force
            $value = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $username, $sec_password
        } else {
            $value = $Params.$property_name

            # The actual value wasn't set, skip adding this property
            if ($null -eq $value) {
                continue
            }

            if ($property.ReferenceClassName -eq "MSFT_KeyValuePair") {
                $key_value_pairs = [System.Collections.Generic.List`1[CimInstance]]@()
                foreach ($value_info in $value.GetEnumerator()) {
                    $kvp = @{Key = $value_info.Key; Value = $value_info.Value.ToString()}
                    $cim_instance = ConvertTo-CimInstance -Name $property_name -ClassName MSFT_KeyValuePair `
                        -Value $kvp -Module $Module
                    $key_value_pairs.Add($cim_instance) > $null
                }
                $value = $key_value_pairs.ToArray()
            } elseif ($null -ne $property.ReferenceClassName) {
                # Convert the dict to a CimInstance (or list of CimInstances)
                $convert_args = @{
                    ClassName = $property.ReferenceClassName
                    Module = $Module
                    Name = $property_name
                    Recurse = $true
                }
                if ($property_type.EndsWith("Array")) {
                    $value = [System.Collections.Generic.List`1[CimInstance]]@()
                    foreach ($raw in $Params.$property_name.GetEnumerator()) {
                        $cim_instance = ConvertTo-CimInstance -Value $raw @convert_args
                        $value.Add($cim_instance) > $null
                    }
                    $value = $value.ToArray()  # Need to make sure we are dealing with an Array not a List
                } else {
                    $value = ConvertTo-CimInstance -Value $value @convert_args
                }
            }
        }
        $dsc_properties.$property_name = $value
    }

    return $dsc_properties
}

Function Invoke-DscMethod {
    <#
    .SYNOPSIS
    Invokes the DSC Resource Method specified in another PS pipeline. This is
    done so we can retrieve the Verbose stream and return it back to the user
    for futher debugging.
    #>
    param(
        [Parameter(Mandatory=$true)][Ansible.Basic.AnsibleModule]$Module,
        [Parameter(Mandatory=$true)][String]$Method,
        [Parameter(Mandatory=$true)][Hashtable]$Arguments
    )

    # Invoke the DSC resource in a separate runspace so we can capture the Verbose output
    $ps = [PowerShell]::Create()
    $ps.AddCommand("Invoke-DscResource").AddParameter("Method", $Method) > $null
    $ps.AddParameters($Arguments) > $null

    $result = $ps.Invoke()

    # Pass the warnings through to the AnsibleModule return result
    foreach ($warning in $ps.Streams.Warning) {
        $Module.Warn($warning.Message)
    }

    # If running at a high enough verbosity, add the verbose output to the AnsibleModule return result
    if ($Module.Verbosity -ge 3) {
        $verbose_logs = [System.Collections.Generic.List`1[String]]@()
        foreach ($verbosity in $ps.Streams.Verbose) {
            $verbose_logs.Add($verbosity.Message) > $null
        }
        $Module.Result."verbose_$($Method.ToLower())" = $verbose_logs
    }

    if ($ps.HadErrors) {
        # Cannot pass in the ErrorRecord as it's a RemotingErrorRecord and doesn't contain the ScriptStackTrace
        # or other info that would be useful
        $Module.FailJson("Failed to invoke DSC $Method method: $($ps.Streams.Error[0].Exception.Message)")
    }

    return $result
}

# win_dsc is unique in that is builds the arg spec based on DSC Resource input. To get this info
# we need to read the resource_name and module_version value which is done outside of Ansible.Basic
if ($args.Length -gt 0) {
    $params = Get-Content -Path $args[0] | ConvertFrom-Json
} else {
    $params = $complex_args
}
if (-not $params.ContainsKey("resource_name")) {
    $res = @{
        msg = "missing required argument: resource_name"
        failed = $true
    }
    Write-Output -InputObject (ConvertTo-Json -Compress -InputObject $res)
    exit 1
}
$resource_name = $params.resource_name

if ($params.ContainsKey("module_version")) {
    $module_version = $params.module_version
} else {
    $module_version = "latest"
}

$module_versions = (Get-DscResource -Name $resource_name -ErrorAction SilentlyContinue | Sort-Object -Property Version)
$resource = $null
if ($module_version -eq "latest" -and $null -ne $module_versions) {
    $resource = $module_versions[-1]
} elseif ($module_version -ne "latest") {
    $resource = $module_versions | Where-Object { $_.Version -eq $module_version }
}

if (-not $resource) {
    if ($module_version -eq "latest") {
        $msg = "Resource '$resource_name' not found."
    } else {
        $msg = "Resource '$resource_name' with version '$module_version' not found."
        $msg += " Versions installed: '$($module_versions.Version -join "', '")'."
    }

    Write-Output -InputObject (ConvertTo-Json -Compress -InputObject @{ failed = $true; msg = $msg })
    exit 1
}

# Build the base args for the DSC Invocation based on the resource selected
$dsc_args = @{
    Name = $resource.Name
}

# Binary resources are not working very well with that approach - need to guesstimate module name/version
$module_version = $null
if ($resource.Module) {
    $dsc_args.ModuleName = @{
        ModuleName = $resource.Module.Name
        ModuleVersion = $resource.Module.Version
    }
    $module_version = $resource.Module.Version.ToString()
} else {
    $dsc_args.ModuleName = "PSDesiredStateConfiguration"
}

# To ensure the class registered with CIM is the one based on our version, we want to run the Get method so the DSC
# engine updates the metadata propery. We don't care about any errors here
try {
    Invoke-DscResource -Method Get -Property @{Fake="Fake"} @dsc_args > $null
} catch {}

# Dynamically build the option spec based on the resource_name specified and create the module object
$spec = Get-OptionSpec -ClassName $resource.ResourceType
$spec.supports_check_mode = $true
$spec.options.module_version = @{ type = "str"; default = "latest" }
$spec.options.resource_name = @{ type = "str"; required = $true }

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)
$module.Result.reboot_required = $false
$module.Result.module_version = $module_version

# Build the DSC invocation arguments and invoke the resource
$dsc_args.Property = ConvertTo-DscProperty -ClassName $resource.ResourceType -Module $module -Params $Module.Params
$dsc_args.Verbose = $true

$test_result = Invoke-DscMethod -Module $module -Method Test -Arguments $dsc_args
if ($test_result.InDesiredState -ne $true) {
    if (-not $module.CheckMode) {
        $result = Invoke-DscMethod -Module $module -Method Set -Arguments $dsc_args
        $module.Result.reboot_required = $result.RebootRequired
    }
    $module.Result.changed = $true
}

$module.ExitJson()
