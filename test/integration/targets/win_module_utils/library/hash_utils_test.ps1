#!powershell

#Requires -Module Ansible.ModuleUtils.HashUtils

Function Assert-Equals($actual, $expected) {
    if ($actual -ne $expected) {
        Fail-Json @{} "actual != expected`nActual: $actual`nExpected: $expected"
    }
}

$test_hash1 = @{
    key1 = "value1",
    key2 = "value2"
}

$test_hash1_string = Convert-HashToString $test_hash1
$expected_string = "key1=value1 key2=value2"
Assert-Equals $test_hash1_string $expected_string

Exit-Json @{ data = "success" }
