#!powershell

#AnsibleRequires -CSharpUtil Ansible.Basic
#AnsibleRequires -CSharpUtil Ansible.Process

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

$tests = @{
    "ParseCommandLine empty string" = {
        $expected = @((Get-Process -Id $pid).Path)
        $actual = [Ansible.Process.ProcessUtil]::ParseCommandLine("")
        Assert-Equals -Actual $actual -Expected $expected
    }

    "ParseCommandLine single argument" = {
        $expected = @("powershell.exe")
        $actual = [Ansible.Process.ProcessUtil]::ParseCommandLine("powershell.exe")
        Assert-Equals -Actual $actual -Expected $expected
    }

    "ParseCommandLine multiple arguments" = {
        $expected = @("powershell.exe", "-File", "C:\temp\script.ps1")
        $actual = [Ansible.Process.ProcessUtil]::ParseCommandLine("powershell.exe -File C:\temp\script.ps1")
        Assert-Equals -Actual $actual -Expected $expected
    }

    "ParseCommandLine comples arguments" = {
        $expected = @('abc', 'd', 'ef gh', 'i\j', 'k"l', 'm\n op', 'ADDLOCAL=qr, s', 'tuv\', 'w''x', 'yz')
        $actual = [Ansible.Process.ProcessUtil]::ParseCommandLine('abc d "ef gh" i\j k\"l m\\"n op" ADDLOCAL="qr, s" tuv\ w''x yz')
        Assert-Equals -Actual $actual -Expected $expected
    }

    "SearchPath normal" = {
        $expected = "$($env:SystemRoot)\System32\WindowsPowerShell\v1.0\powershell.exe"
        $actual = [Ansible.Process.ProcessUtil]::SearchPath("powershell.exe")
        $actual | Assert-Equals -Expected $expected
    }

    "SearchPath missing" = {
        $failed = $false
        try {
            [Ansible.Process.ProcessUtil]::SearchPath("fake.exe")
        } catch {
            $failed = $true
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.FileNotFoundException"
            $expected = 'Exception calling "SearchPath" with "1" argument(s): "Could not find file ''fake.exe''."'
            $_.Exception.Message | Assert-Equals -Expected $expected
        }
        $failed | Assert-Equals -Expected $true
    }

    "CreateProcess basic" = {
        $actual = [Ansible.Process.ProcessUtil]::CreateProcess("whoami.exe")
        $actual.GetType().FullName | Assert-Equals -Expected "Ansible.Process.Result"
        $actual.StandardOut | Assert-Equals -Expected "$(&whoami.exe)`r`n"
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0
    }

    "CreateProcess stderr" = {
        $actual = [Ansible.Process.ProcessUtil]::CreateProcess("powershell.exe [System.Console]::Error.WriteLine('hi')")
        $actual.StandardOut | Assert-Equals -Expected ""
        $actual.StandardError | Assert-Equals -Expected "hi`r`n"
        $actual.ExitCode | Assert-Equals -Expected 0
    }

    "CreateProcess exit code" = {
        $actual = [Ansible.Process.ProcessUtil]::CreateProcess("powershell.exe exit 10")
        $actual.StandardOut | Assert-Equals -Expected ""
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 10
    }

    "CreateProcess bad executable" = {
        $failed = $false
        try {
            [Ansible.Process.ProcessUtil]::CreateProcess("fake.exe")
        } catch {
            $failed = $true
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "Ansible.Process.Win32Exception"
            $expected = 'Exception calling "CreateProcess" with "1" argument(s): "CreateProcessW() failed '
            $expected += '(The system cannot find the file specified, Win32ErrorCode 2)"'
            $_.Exception.Message | Assert-Equals -Expected $expected
        }
        $failed | Assert-Equals -Expected $true
    }

    "CreateProcess with unicode" = {
        $actual = [Ansible.Process.ProcessUtil]::CreateProcess("cmd.exe /c echo 💩 café")
        $actual.StandardOut | Assert-Equals -Expected "💩 café`r`n"
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0

        $actual = [Ansible.Process.ProcessUtil]::CreateProcess($null, "cmd.exe /c echo 💩 café", $null, $null)
        $actual.StandardOut | Assert-Equals -Expected "💩 café`r`n"
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0
    }

    "CreateProcess without working dir" = {
        $expected = $pwd.Path + "`r`n"
        $actual = [Ansible.Process.ProcessUtil]::CreateProcess($null, 'powershell.exe $pwd.Path', $null, $null)
        $actual.StandardOut | Assert-Equals -Expected $expected
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0
    }

    "CreateProcess with working dir" = {
        $expected = "C:\Windows`r`n"
        $actual = [Ansible.Process.ProcessUtil]::CreateProcess($null, 'powershell.exe $pwd.Path', "C:\Windows", $null)
        $actual.StandardOut | Assert-Equals -Expected $expected
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0
    }

    "CreateProcess without environment" = {
        $expected = "$($env:USERNAME)`r`n"
        $actual = [Ansible.Process.ProcessUtil]::CreateProcess($null, 'powershell.exe $env:TEST; $env:USERNAME', $null, $null)
        $actual.StandardOut | Assert-Equals -Expected $expected
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0
    }

    "CreateProcess with environment" = {
        $env_vars = @{
            TEST = "tesTing"
            TEST2 = "Testing 2"
        }
        $actual = [Ansible.Process.ProcessUtil]::CreateProcess($null, 'cmd.exe /c set', $null, $env_vars)
        ("TEST=tesTing" -cin $actual.StandardOut.Split("`r`n")) | Assert-Equals -Expected $true
        ("TEST2=Testing 2" -cin $actual.StandardOut.Split("`r`n")) | Assert-Equals -Expected $true
        ("USERNAME=$($env:USERNAME)" -cnotin $actual.StandardOut.Split("`r`n")) | Assert-Equals -Expected $true
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0
    }

    "CreateProcess with string stdin" = {
        $expected = "input value`r`n`r`n"
        $actual = [Ansible.Process.ProcessUtil]::CreateProcess($null, 'powershell.exe [System.Console]::In.ReadToEnd()',
            $null, $null, "input value")
        $actual.StandardOut | Assert-Equals -Expected $expected
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0
    }

    "CreateProcess with string stdin and newline" = {
        $expected = "input value`r`n`r`n"
        $actual = [Ansible.Process.ProcessUtil]::CreateProcess($null, 'powershell.exe [System.Console]::In.ReadToEnd()',
            $null, $null, "input value`r`n")
        $actual.StandardOut | Assert-Equals -Expected $expected
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0
    }

    "CreateProcess with byte stdin" = {
        $expected = "input value`r`n"
        $actual = [Ansible.Process.ProcessUtil]::CreateProcess($null, 'powershell.exe [System.Console]::In.ReadToEnd()',
            $null, $null, [System.Text.Encoding]::UTF8.GetBytes("input value"))
        $actual.StandardOut | Assert-Equals -Expected $expected
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0
    }

    "CreateProcess with byte stdin and newline" = {
        $expected = "input value`r`n`r`n"
        $actual = [Ansible.Process.ProcessUtil]::CreateProcess($null, 'powershell.exe [System.Console]::In.ReadToEnd()',
            $null, $null, [System.Text.Encoding]::UTF8.GetBytes("input value`r`n"))
        $actual.StandardOut | Assert-Equals -Expected $expected
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0
    }

    "CreateProcess with lpApplicationName" = {
        $expected = "abc`r`n"
        $full_path = "$($env:SystemRoot)\System32\WindowsPowerShell\v1.0\powershell.exe"
        $actual = [Ansible.Process.ProcessUtil]::CreateProcess($full_path, "Write-Output 'abc'", $null, $null)
        $actual.StandardOut | Assert-Equals -Expected $expected
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0

        $actual = [Ansible.Process.ProcessUtil]::CreateProcess($full_path, "powershell.exe Write-Output 'abc'", $null, $null)
        $actual.StandardOut | Assert-Equals -Expected $expected
        $actual.StandardError | Assert-Equals -Expected ""
        $actual.ExitCode | Assert-Equals -Expected 0
    }
}

foreach ($test_impl in $tests.GetEnumerator()) {
    $test = $test_impl.Key
    &$test_impl.Value
}

$module.Result.data = "success"
$module.ExitJson()

