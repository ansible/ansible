#!powershell

# Copyright: (c) 2019, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Module Ansible.ModuleUtils.Backup

$module = [Ansible.Basic.AnsibleModule]::Create($args, @{})

Function Assert-Equals {
    param(
        [Parameter(Mandatory=$true, ValueFromPipeline=$true)][AllowNull()]$Actual,
        [Parameter(Mandatory=$true, Position=0)][AllowNull()]$Expected
    )

    $matched = $false
    if ($Actual -is [System.Collections.ArrayList] -or $Actual -is [Array]) {
        $Actual.Count | Assert-Equals -Expected $Expected.Count
        for ($i = 0; $i -lt $Actual.Count; $i++) {
            $actual_value = $Actual[$i]
            $expected_value = $Expected[$i]
            Assert-Equals -Actual $actual_value -Expected $expected_value
        }
        $matched = $true
    } else {
        $matched = $Actual -ceq $Expected
    }

    if (-not $matched) {
        if ($Actual -is [PSObject]) {
            $Actual = $Actual.ToString()
        }

        $call_stack = (Get-PSCallStack)[1]
        $module.Result.test = $test
        $module.Result.actual = $Actual
        $module.Result.expected = $Expected
        $module.Result.line = $call_stack.ScriptLineNumber
        $module.Result.method = $call_stack.Position.Text
        $module.FailJson("AssertionError: actual != expected")
    }
}

$tmp_dir = $module.Tmpdir

$tests = @{
    "Test backup file with missing file" = {
        $actual = Backup-File -path (Join-Path -Path $tmp_dir -ChildPath "missing")
        $actual | Assert-Equals -Expected $null
    }

    "Test backup file in check mode" = {
        $orig_file = Join-Path -Path $tmp_dir -ChildPath "file-check.txt"
        Set-Content -LiteralPath $orig_file -Value "abc"
        $actual = Backup-File -path $orig_file -WhatIf

        (Test-Path -LiteralPath $actual) | Assert-Equals -Expected $false

        $parent_dir = Split-Path -LiteralPath $actual
        $backup_file = Split-Path -Path $actual -Leaf
        $parent_dir | Assert-Equals -Expected $tmp_dir
        ($backup_file -match "^file-check\.txt\.$pid\.\d{8}-\d{6}\.bak$") | Assert-Equals -Expected $true
    }

    "Test backup file" = {
        $content = "abc"
        $orig_file = Join-Path -Path $tmp_dir -ChildPath "file.txt"
        Set-Content -LiteralPath $orig_file -Value $content
        $actual = Backup-File -path $orig_file

        (Test-Path -LiteralPath $actual) | Assert-Equals -Expected $true

        $parent_dir = Split-Path -LiteralPath $actual
        $backup_file = Split-Path -Path $actual -Leaf
        $parent_dir | Assert-Equals -Expected $tmp_dir
        ($backup_file -match "^file\.txt\.$pid\.\d{8}-\d{6}\.bak$") | Assert-Equals -Expected $true
        (Get-Content -LiteralPath $actual -Raw) | Assert-Equals -Expected "$content`r`n"
    }
}

foreach ($test_impl in $tests.GetEnumerator()) {
    $test = $test_impl.Key
    &$test_impl.Value
}

$module.Result.res = 'success'

$module.ExitJson()
