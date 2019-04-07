#!powershell

#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = "Stop"

Function Assert-Equals($actual, $expected) {
    if ($actual -cne $expected) {
        $call_stack = (Get-PSCallStack)[1]
        $error_msg = "AssertionError:`r`nActual: `"$actual`" != Expected: `"$expected`"`r`nLine: $($call_stack.ScriptLineNumber), Method: $($call_stack.Position.Text)"
        Fail-Json -obj $result -message $error_msg
    }
}

$result = @{
    changed = $false
}

#ConvertFrom-AnsibleJso
$input_json  = '{"string":"string","float":3.1415926,"dict":{"string":"string","int":1},"list":["entry 1","entry 2"],"null":null,"int":1}'
$actual = ConvertFrom-AnsibleJson -InputObject $input_json
Assert-Equals -actual $actual.GetType() -expected ([Hashtable])
Assert-Equals -actual $actual.string.GetType() -expected ([String])
Assert-Equals -actual $actual.string -expected "string"
Assert-Equals -actual $actual.int.GetType() -expected ([Int32])
Assert-Equals -actual $actual.int -expected 1
Assert-Equals -actual $actual.null -expected $null
Assert-Equals -actual $actual.float.GetType() -expected ([Decimal])
Assert-Equals -actual $actual.float -expected 3.1415926
Assert-Equals -actual $actual.list.GetType() -expected ([Object[]])
Assert-Equals -actual $actual.list.Count -expected 2
Assert-Equals -actual $actual.list[0] -expected "entry 1"
Assert-Equals -actual $actual.list[1] -expected "entry 2"
Assert-Equals -actual $actual.GetType() -expected ([Hashtable])
Assert-Equals -actual $actual.dict.string -expected "string"
Assert-Equals -actual $actual.dict.int -expected 1

$result.msg = "good"
Exit-Json -obj $result

