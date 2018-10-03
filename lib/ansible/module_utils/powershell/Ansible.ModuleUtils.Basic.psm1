# Copyright (c) 2018 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

#AnsibleRequires -CSharpUtil Ansible.Basic

Function ConvertTo-SpecifiedList {
    <#
    .SYNOPSIS
    Special cmdlet used in Get-AnsibleModule to cast a PowerShell array to
    the type required by the C# module utils.
    #>
    param(
        [AllowEmptyCollection()][Object[]]$List,
        [String]$SubType = "String"
    )

    $list_type = "System.Collections.Generic.List``1[$SubType]"
    $new_list = New-Object -TypeName "System.Collections.Generic.List``1[$list_type]"
    foreach ($entry in $List) {
        $new_entry = New-Object -TypeName $list_type
        foreach ($sub_entry in $entry) {
            # RequiredIf may contain an Array and we need to convert it
            if ($sub_entry -is [Array]) {
                $new_entry.Add([System.Collections.Generic.List`1[String]]$sub_entry) > $null
            } else {
                $new_entry.Add($sub_entry) > $null
            }
        }
        $new_list.Add($new_entry) > $null
    }

    return ,$new_list
}


Function Get-AnsibleModule {
    <#
    .SYNOPSIS
    Helper cmdlet used by PowerShell modules to initialise a new AnsibleModule
    class. This class is used to parse the input arguments and control module
    actions.

    .PARAMETER Arguments
    [String[]] Process arguments where the first entry may point to a json file
    containing the module arguments. If not set then the value $complex_args is
    used as the module argments.

    .PARAMETER ArgumentSpec
    [Hashtable] The module argument spec that is used to validate the input
    arguments as well as cast the values to the request types.

    .PARAMETER MutuallyExclusive
    [Object[]] A collection of [String[]] where each array contains module
    options that cannot be set together.

    .PARAMETER RequiredTogether
    [Object[]] A collection of [String[]] where each array contains module
    options that must be set together.

    .PARAMETER RequiredOneOf
    [Object[]] A collection of [String[]] where each array contains module
    options where at least one of them must be set.

    .PARAMETER RequiredIf
    [Object[]] A collection of [Object[]] where each array contains;
        0: The option name that the value is checked against
        1: The value for the option where if matched means the options in 2 must be set
        2: A list of options where if option[0] == 1, must be set
        3: A bool that states whether only 1 option in 2 must be set, default is $false

    .PARAMETER ExtraTypes
    [Hashtable] Extra option types that can be used as part of the argument
    validation but are not part of Ansible.Basic.cs. The key is the type name
    and the value is a Func that does the conversion. For example to have a type
    that casts the value as a UInt64 value, you can do;
    $extra_types = @{
        uint64 = [Func`2[[Object], [UInt64]]]{ [UInt64]::Parse($args[0]) }
    }

    .PARAMETER SupportsCheckMode
    [Switch]
    States whether the module supports check mode or not.

    .PARAMETER NoLog
    States whether the modules stops any event logging. Like basic.py, this does
    not stop the module from returning the invocation args.
    #>
    param(
        [Parameter(Mandatory=$true)][AllowEmptyCollection()][String[]]$Arguments,
        [Parameter(Mandatory=$true)][Hashtable]$ArgumentSpec,
        [AllowEmptyCollection()][Object[]]$MutuallyExclusive = @(),
        [AllowEmptyCollection()][Object[]]$RequiredTogether = @(),
        [AllowEmptyCollection()][Object[]]$RequiredOneOf = @(),
        [AllowEmptyCollection()][Object[]]$RequiredIf = @(),
        [AllowEmptyCollection()][Hashtable]$ExtraTypes = @{},
        [Switch]$SupportsCheckMode,
        [Switch]$NoLog
    )
    # TODO: do we want this?
    Set-StrictMode -Version latest

    # cast the array params to the format expected by the c# code
    $mutually_exclusive = ConvertTo-SpecifiedList -List $MutuallyExclusive -SubType "String"
    $required_together = ConvertTo-SpecifiedList -List $RequiredTogether -SubType "String"
    $required_one_of = ConvertTo-SpecifiedList -List $RequiredOneOf -SubType "String"
    $required_if = ConvertTo-SpecifiedList -List $RequiredIf -SubType "Object"
    $extra_types = New-Object -TypeName 'System.Collections.Generic.Dictionary`2[[String], [Delegate]]'
    foreach ($type in $ExtraTypes.GetEnumerator()) {
        $extra_types.Add($type.Key, $type.Value)
    }

    # Activator is faster than New-Object and it allows us to reference the
    # actual exception thrown and not just MethodInvocationException which
    # hides whether the constructor exited (FailJson) or threw an uncaught
    # exception. If it's the latter then we build a prettier message to help
    # with debugging.
    # PSObject -> .NET type marshalling errors, we cast the type here to help
    $ctor_args = [Object[]]@(
        [String[]]$Arguments,
        [Hashtable]$ArgumentSpec,
        [bool]$SupportsCheckMode.IsPresent,
        [bool]$NoLog.IsPresent,
        [System.Collections.Generic.List`1[System.Collections.Generic.List`1[String]]]$mutually_exclusive,
        [System.Collections.Generic.List`1[System.Collections.Generic.List`1[String]]]$required_together,
        [System.Collections.Generic.List`1[System.Collections.Generic.List`1[String]]]$required_one_of,
        [System.Collections.Generic.List`1[System.Collections.Generic.List`1[Object]]]$required_if,
        [System.Collections.Generic.Dictionary`2[[String], [Delegate]]]$extra_types
    )

    try {
        $module = [System.Activator]::CreateInstance([Ansible.Basic.AnsibleModule], $ctor_args)
    } catch {
        # calling exit throws ExitException, we know this is done by Exit()
        # which already wrote the output and we skip that case
        if ($_.FullyQualifiedErrorId -ne "System.Management.Automation.ExitException") {
            $res = @{
                msg = "error while initialising AnsibleModule: $($_.Exception.Message)"
                exception = $_.Exception.ToString()
                failed = $true
            }
            Write-Output -InputObject (ConvertTo-Json -InputObject $res -Depth 99 -Compress)
        }
        exit 1
    }

    return ,$module
}

Export-ModuleMember -Function Get-AnsibleModule
