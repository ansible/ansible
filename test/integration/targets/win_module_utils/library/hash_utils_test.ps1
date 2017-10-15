#!powershell

#Requires -Module Ansible.ModuleUtils.HashUtils

Function Assert-Equals($actual, $expected) {
    if ($actual -ne $expected) {
        Fail-Json @{} "actual != expected`nActual: $actual`nExpected: $expected"
    }
}

Function Assert-EqualsHash($actual, $expected) {
    if ($actual.Count -ne $expected.Count) {
        Write-Output "Number of hash keys do not match`nActual: $actual.Keys.Count`nExpected: $expected.Keys.Count"
    }

    foreach ($key in $actual.Keys) {
        if (!$expected[$key]) {
            Write-Output "Hash keys do not match`nActual: $actual.Keys`nExpected: $expected.Keys"
        }

        if ($actual[$key] -ne $expected[$key]) {
            Write-Output "Hash value does not match`nActual: $actual[$key]`nExpected: $expected[$key]"
        }
    }
}

$test_hash1 = @{
    key1 = "value1";
    key2 = "value2"
}

$test_array1 = @(
    1, "key1=value1", "key2=value2"
)

$expected_string = "key1=value1 key2=value2"

$test_hash1_string = Convert-HashToString $test_hash1
$test_array1_hash = Convert-ArrayToHash $test_array1

Assert-Equals $test_hash1_string $expected_string
Assert-EqualsHash $test_array1_hash $test_hash1

Exit-Json @{ data = "success" }
