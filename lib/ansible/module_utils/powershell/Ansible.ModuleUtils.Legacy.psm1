# Copyright (c), Michael DeHaan <michael.dehaan@gmail.com>, 2014, and others
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

Function Set-Attr($obj, $name, $value)
{
<#
    .SYNOPSIS
    Helper function to set an "attribute" on a psobject instance in PowerShell.
    This is a convenience to make adding Members to the object easier and
    slightly more pythonic
    .EXAMPLE
    Set-Attr $result "changed" $true
#>

    # If the provided $obj is undefined, define one to be nice
    If (-not $obj.GetType)
    {
        $obj = @{ }
    }

    Try
    {
        $obj.$name = $value
    }
    Catch
    {
        $obj | Add-Member -Force -MemberType NoteProperty -Name $name -Value $value
    }
}

Function Exit-Json($obj)
{
<#
    .SYNOPSIS
    Helper function to convert a PowerShell object to JSON and output it, exiting
    the script
    .EXAMPLE
    Exit-Json $result
#>

    # If the provided $obj is undefined, define one to be nice
    If (-not $obj.GetType)
    {
        $obj = @{ }
    }

    if (-not $obj.ContainsKey('changed')) {
        Set-Attr $obj "changed" $false
    }

    Write-Output $obj | ConvertTo-Json -Compress -Depth 99
    Exit
}

Function Fail-Json($obj, $message = $null)
{
<#
    .SYNOPSIS
    Helper function to add the "msg" property and "failed" property, convert the
    PowerShell Hashtable to JSON and output it, exiting the script
    .EXAMPLE
    Fail-Json $result "This is the failure message"
#>

    if ($obj -is [hashtable] -or $obj -is [psobject]) {
        # Nothing to do
    } elseif ($obj -is [string] -and $null -eq $message) {
        # If we weren't given 2 args, and the only arg was a string,
        # create a new Hashtable and use the arg as the failure message
        $message = $obj
        $obj = @{ }
    } else {
        # If the first argument is undefined or a different type,
        # make it a Hashtable
        $obj = @{ }
    }

    # Still using Set-Attr for PSObject compatibility
    Set-Attr $obj "msg" $message
    Set-Attr $obj "failed" $true

    if (-not $obj.ContainsKey('changed')) {
        Set-Attr $obj "changed" $false
    }

    Write-Output $obj | ConvertTo-Json -Compress -Depth 99
    Exit 1
}

Function Add-Warning($obj, $message)
{
<#
    .SYNOPSIS
    Helper function to add warnings, even if the warnings attribute was
    not already set up. This is a convenience for the module developer
    so they do not have to check for the attribute prior to adding.
#>

    if (-not $obj.ContainsKey("warnings")) {
        $obj.warnings = @()
    } elseif ($obj.warnings -isnot [array]) {
        throw "Add-Warning: warnings attribute is not an array"
    }

    $obj.warnings += $message
}

Function Add-DeprecationWarning($obj, $message, $version = $null)
{
<#
    .SYNOPSIS
    Helper function to add deprecations, even if the deprecations attribute was
    not already set up. This is a convenience for the module developer
    so they do not have to check for the attribute prior to adding.
#>
    if (-not $obj.ContainsKey("deprecations")) {
        $obj.deprecations = @()
    } elseif ($obj.deprecations -isnot [array]) {
        throw "Add-DeprecationWarning: deprecations attribute is not a list"
    }

    $obj.deprecations += @{
        msg = $message
        version = $version
    }
}

Function Expand-Environment($value)
{
<#
    .SYNOPSIS
    Helper function to expand environment variables in values. By default
    it turns any type to a string, but we ensure $null remains $null.
#>
    if ($null -ne $value) {
        [System.Environment]::ExpandEnvironmentVariables($value)
    } else {
        $value
    }
}

Function Get-AnsibleParam($obj, $name, $default = $null, $resultobj = @{}, $failifempty = $false, $emptyattributefailmessage, $ValidateSet, $ValidateSetErrorMessage, $type = $null, $aliases = @())
{
<#
    .SYNOPSIS
    Helper function to get an "attribute" from a psobject instance in PowerShell.
    This is a convenience to make getting Members from an object easier and
    slightly more pythonic
    .EXAMPLE
    $attr = Get-AnsibleParam $response "code" -default "1"
    .EXAMPLE
    Get-AnsibleParam -obj $params -name "State" -default "Present" -ValidateSet "Present","Absent" -resultobj $resultobj -failifempty $true
    Get-AnsibleParam also supports Parameter validation to save you from coding that manually
    Note that if you use the failifempty option, you do need to specify resultobject as well.
#>
    # Check if the provided Member $name or aliases exist in $obj and return it or the default.
    try {

        $found = $null
        # First try to find preferred parameter $name
        $aliases = @($name) + $aliases

        # Iterate over aliases to find acceptable Member $name
        foreach ($alias in $aliases) {
            if ($obj.ContainsKey($alias)) {
                $found = $alias
                break
            }
        }

        if ($null -eq $found) {
            throw
        }
        $name = $found

        if ($ValidateSet) {

            if ($ValidateSet -contains ($obj.$name)) {
                $value = $obj.$name
            } else {
                if ($null -eq $ValidateSetErrorMessage) {
                    #Auto-generated error should be sufficient in most use cases
                    $ValidateSetErrorMessage = "Get-AnsibleParam: Argument $name needs to be one of $($ValidateSet -join ",") but was $($obj.$name)."
                }
                Fail-Json -obj $resultobj -message $ValidateSetErrorMessage
            }
        } else {
            $value = $obj.$name
        }
    } catch {
        if ($failifempty -eq $false) {
            $value = $default
        } else {
            if (-not $emptyattributefailmessage) {
                $emptyattributefailmessage = "Get-AnsibleParam: Missing required argument: $name"
            }
            Fail-Json -obj $resultobj -message $emptyattributefailmessage
        }
    }

    # If $null -eq $value, the parameter was unspecified by the user (deliberately or not)
    # Please leave $null-values intact, modules need to know if a parameter was specified
    if ($null -eq $value) {
        return $null
    }

    if ($type -eq "path") {
        # Expand environment variables on path-type
        $value = Expand-Environment($value)
        # Test if a valid path is provided
        if (-not (Test-Path -IsValid $value)) {
            $path_invalid = $true
            # could still be a valid-shaped path with a nonexistent drive letter
            if ($value -match "^\w:") {
                # rewrite path with a valid drive letter and recheck the shape- this might still fail, eg, a nonexistent non-filesystem PS path
                if (Test-Path -IsValid $(@(Get-PSDrive -PSProvider Filesystem)[0].Name + $value.Substring(1))) {
                    $path_invalid = $false
                }
            }
            if ($path_invalid) {
                Fail-Json -obj $resultobj -message "Get-AnsibleParam: Parameter '$name' has an invalid path '$value' specified."
            }
        }
    } elseif ($type -eq "str") {
        # Convert str types to real Powershell strings
        $value = $value.ToString()
    } elseif ($type -eq "bool") {
        # Convert boolean types to real Powershell booleans
        $value = $value | ConvertTo-Bool
    } elseif ($type -eq "int") {
        # Convert int types to real Powershell integers
        $value = $value -as [int]
    } elseif ($type -eq "float") {
        # Convert float types to real Powershell floats
        $value = $value -as [float]
    } elseif ($type -eq "list") {
        if ($value -is [array]) {
            # Nothing to do
        } elseif ($value -is [string]) {
            # Convert string type to real Powershell array
            $value = $value.Split(",").Trim()
        } elseif ($value -is [int]) {
            $value = @($value)
        } else {
            Fail-Json -obj $resultobj -message "Get-AnsibleParam: Parameter '$name' is not a YAML list."
        }
        # , is not a typo, forces it to return as a list when it is empty or only has 1 entry
        return ,$value
    }

    return $value
}

#Alias Get-attr-->Get-AnsibleParam for backwards compat. Only add when needed to ease debugging of scripts
If (-not(Get-Alias -Name "Get-attr" -ErrorAction SilentlyContinue))
{
    New-Alias -Name Get-attr -Value Get-AnsibleParam
}

Function ConvertTo-Bool
{
<#
    .SYNOPSIS
    Helper filter/pipeline function to convert a value to boolean following current
    Ansible practices
    .EXAMPLE
    $is_true = "true" | ConvertTo-Bool
#>
    param(
        [parameter(valuefrompipeline=$true)]
        $obj
    )

    $boolean_strings = "yes", "on", "1", "true", 1
    $obj_string = [string]$obj

    if (($obj -is [boolean] -and $obj) -or $boolean_strings -contains $obj_string.ToLower()) {
        return $true
    } else {
        return $false
    }
}

Function Parse-Args($arguments, $supports_check_mode = $false)
{
<#
    .SYNOPSIS
    Helper function to parse Ansible JSON arguments from a "file" passed as
    the single argument to the module.
    .EXAMPLE
    $params = Parse-Args $args
#>
    $params = New-Object psobject
    If ($arguments.Length -gt 0)
    {
        $params = Get-Content $arguments[0] | ConvertFrom-Json
    }
    Else {
        $params = $complex_args
    }
    $check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
    If ($check_mode -and -not $supports_check_mode)
    {
        Exit-Json @{
            skipped = $true
            changed = $false
            msg = "remote module does not support check mode"
        }
    }
    return $params
}


Function Get-FileChecksum($path, $algorithm = 'sha1')
{
<#
    .SYNOPSIS
    Helper function to calculate a hash of a file in a way which PowerShell 3
    and above can handle
#>
    If (Test-Path -LiteralPath $path -PathType Leaf)
    {
        switch ($algorithm)
        {
            'md5' { $sp = New-Object -TypeName System.Security.Cryptography.MD5CryptoServiceProvider }
            'sha1' { $sp = New-Object -TypeName System.Security.Cryptography.SHA1CryptoServiceProvider }
            'sha256' { $sp = New-Object -TypeName System.Security.Cryptography.SHA256CryptoServiceProvider }
            'sha384' { $sp = New-Object -TypeName System.Security.Cryptography.SHA384CryptoServiceProvider }
            'sha512' { $sp = New-Object -TypeName System.Security.Cryptography.SHA512CryptoServiceProvider }
            default { Fail-Json @{} "Unsupported hash algorithm supplied '$algorithm'" }
        }

        If ($PSVersionTable.PSVersion.Major -ge 4) {
            $raw_hash = Get-FileHash -LiteralPath $path -Algorithm $algorithm
            $hash = $raw_hash.Hash.ToLower()
        } Else {
            $fp = [System.IO.File]::Open($path, [System.IO.Filemode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite);
            $hash = [System.BitConverter]::ToString($sp.ComputeHash($fp)).Replace("-", "").ToLower();
            $fp.Dispose();
        }
    }
    ElseIf (Test-Path -LiteralPath $path -PathType Container)
    {
        $hash = "3";
    }
    Else
    {
        $hash = "1";
    }
    return $hash
}

Function Get-PendingRebootStatus
{
<#
    .SYNOPSIS
    Check if reboot is required, if so notify CA.
    Function returns true if computer has a pending reboot
#>
    $featureData = Invoke-WmiMethod -EA Ignore -Name GetServerFeature -Namespace root\microsoft\windows\servermanager -Class MSFT_ServerManagerTasks
    $regData = Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager" "PendingFileRenameOperations" -EA Ignore
    $CBSRebootStatus = Get-ChildItem "HKLM:\\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing"  -ErrorAction SilentlyContinue| Where-Object {$_.PSChildName -eq "RebootPending"}
    if(($featureData -and $featureData.RequiresReboot) -or $regData -or $CBSRebootStatus)
    {
        return $True
    }
    else
    {
        return $False
    }
}

# this line must stay at the bottom to ensure all defined module parts are exported
Export-ModuleMember -Alias * -Function * -Cmdlet *

