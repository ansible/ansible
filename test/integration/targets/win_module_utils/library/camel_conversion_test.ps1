#!powershell

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.CamelConversion

$ErrorActionPreference = 'Continue'

Function Assert-Equals($actual, $expected) {
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
}

$output_dict = Convert-DictToSnakeCase -dict $input_dict
foreach ($entry in $output_dict.GetEnumerator()) {
    $key = $entry.Name
    $value = $entry.Value

    if ($value -is [Hashtable]) {
        Assert-Equals -actual $key -expected "inner_hash_table"
        foreach ($inner_hash in $value.GetEnumerator()) {
            Assert-Equals -actual $inner_hash.Name -expected $inner_hash.Value
        }
    } elseif ($value -is [Array]) {
        # there is one array in our original dict, we know the structure
        foreach ($inner_list in $value) {
            if ($inner_list -is [Hashtable]) {
                foreach ($inner_list_hash in $inner_list.GetEnumerator()) {
                    Assert-Equals -actual $inner_list_hash.Name -expected $inner_list_hash.Value
                }
            } elseif ($inner_list -is [String]) {
                Assert-Equals -actual $inner_list -expected "string_two"
            } else {
                Assert-Equals -actual $inner_list -expected 0
            }
        }
    } else {
        Assert-Equals -actual $key -expected $value
    }
}

Exit-Json @{ data = 'success' }
