#!powershell

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.CamelConversion

$ErrorActionPreference = 'Stop'

Function Assert-Equal($actual, $expected) {
    if ($actual -cne $expected) {
        Fail-Json @{} "actual != expected`nActual: $actual`nExpected: $expected"
    }
}

$input_dict = @{
    alllower = 'alllower'
    ALLUPPER = 'allupper'
    camelCase = 'camel_case'
    mixedCase_withCamel = 'mixed_case_with_camel'
    TwoWords = 'two_words'
    AllUpperAtEND = 'all_upper_at_end'
    AllUpperButPLURALs = 'all_upper_but_plurals'
    TargetGroupARNs = 'target_group_arns'
    HTTPEndpoints = 'http_endpoints'
    PLURALs = 'plurals'
    listDict = @(
        @{ entry1 = 'entry1'; entryTwo = 'entry_two' },
        'stringTwo',
        0
    )
    INNERHashTable = @{
        ID = 'id'
        IEnumerable = 'i_enumerable'
    }
    emptyList = @()
    singleList = @("a")
}

$output_dict = Convert-DictToSnakeCase -dict $input_dict
foreach ($entry in $output_dict.GetEnumerator()) {
    $key = $entry.Name
    $value = $entry.Value

    if ($value -is [Hashtable]) {
        Assert-Equal -actual $key -expected "inner_hash_table"
        foreach ($inner_hash in $value.GetEnumerator()) {
            Assert-Equal -actual $inner_hash.Name -expected $inner_hash.Value
        }
    }
    elseif ($value -is [Array] -or $value -is [System.Collections.ArrayList]) {
        if ($key -eq "list_dict") {
            foreach ($inner_list in $value) {
                if ($inner_list -is [Hashtable]) {
                    foreach ($inner_list_hash in $inner_list.GetEnumerator()) {
                        Assert-Equal -actual $inner_list_hash.Name -expected $inner_list_hash.Value
                    }
                }
                elseif ($inner_list -is [String]) {
                    # this is not a string key so we need to keep it the same
                    Assert-Equal -actual $inner_list -expected "stringTwo"
                }
                else {
                    Assert-Equal -actual $inner_list -expected 0
                }
            }
        }
        elseif ($key -eq "empty_list") {
            Assert-Equal -actual $value.Count -expected 0
        }
        elseif ($key -eq "single_list") {
            Assert-Equal -actual $value.Count -expected 1
        }
        else {
            Fail-Json -obj $result -message "invalid key found for list $key"
        }
    }
    else {
        Assert-Equal -actual $key -expected $value
    }
}

Exit-Json @{ data = 'success' }
