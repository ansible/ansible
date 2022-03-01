#!powershell

#AnsibleRequires -CSharpUtil Ansible.Basic
#Ansiblerequires -CSharpUtil Ansible.Privilege

$module = [Ansible.Basic.AnsibleModule]::Create($args, @{})

Function Assert-Equal {
    param(
        [Parameter(Mandatory = $true, ValueFromPipeline = $true)][AllowNull()]$Actual,
        [Parameter(Mandatory = $true, Position = 0)][AllowNull()]$Expected
    )

    process {
        $matched = $false
        if ($Actual -is [System.Collections.ArrayList] -or $Actual -is [Array]) {
            $Actual.Count | Assert-Equal -Expected $Expected.Count
            for ($i = 0; $i -lt $Actual.Count; $i++) {
                $actual_value = $Actual[$i]
                $expected_value = $Expected[$i]
                Assert-Equal -Actual $actual_value -Expected $expected_value
            }
            $matched = $true
        }
        else {
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
}

Function Assert-DictionaryEqual {
    param(
        [Parameter(Mandatory = $true, ValueFromPipeline = $true)][AllowNull()]$Actual,
        [Parameter(Mandatory = $true, Position = 0)][AllowNull()]$Expected
    )

    process {
        $actual_keys = $Actual.Keys
        $expected_keys = $Expected.Keys

        $actual_keys.Count | Assert-Equal -Expected $expected_keys.Count
        foreach ($actual_entry in $Actual.GetEnumerator()) {
            $actual_key = $actual_entry.Key
            ($actual_key -cin $expected_keys) | Assert-Equal -Expected $true
            $actual_value = $actual_entry.Value
            $expected_value = $Expected.$actual_key

            if ($actual_value -is [System.Collections.IDictionary]) {
                $actual_value | Assert-DictionaryEqual -Expected $expected_value
            }
            elseif ($actual_value -is [System.Collections.ArrayList]) {
                for ($i = 0; $i -lt $actual_value.Count; $i++) {
                    $actual_entry = $actual_value[$i]
                    $expected_entry = $expected_value[$i]
                    if ($actual_entry -is [System.Collections.IDictionary]) {
                        $actual_entry | Assert-DictionaryEqual -Expected $expected_entry
                    }
                    else {
                        Assert-Equal -Actual $actual_entry -Expected $expected_entry
                    }
                }
            }
            else {
                Assert-Equal -Actual $actual_value -Expected $expected_value
            }
        }
        foreach ($expected_key in $expected_keys) {
            ($expected_key -cin $actual_keys) | Assert-Equal -Expected $true
        }
    }
}

$process = [Ansible.Privilege.PrivilegeUtil]::GetCurrentProcess()

$tests = @{
    "Check valid privilege name" = {
        $actual = [Ansible.Privilege.PrivilegeUtil]::CheckPrivilegeName("SeTcbPrivilege")
        $actual | Assert-Equal -Expected $true
    }

    "Check invalid privilege name" = {
        $actual = [Ansible.Privilege.PrivilegeUtil]::CheckPrivilegeName("SeFake")
        $actual | Assert-Equal -Expected $false
    }

    "Disable a privilege" = {
        # Ensure the privilege is enabled at the start
        [Ansible.Privilege.PrivilegeUtil]::EnablePrivilege($process, "SeTimeZonePrivilege") > $null

        $actual = [Ansible.Privilege.PrivilegeUtil]::DisablePrivilege($process, "SeTimeZonePrivilege")
        $actual.GetType().Name | Assert-Equal -Expected 'Dictionary`2'
        $actual.Count | Assert-Equal -Expected 1
        $actual.SeTimeZonePrivilege | Assert-Equal -Expected $true

        # Disable again
        $actual = [Ansible.Privilege.PrivilegeUtil]::DisablePrivilege($process, "SeTimeZonePrivilege")
        $actual.GetType().Name | Assert-Equal -Expected 'Dictionary`2'
        $actual.Count | Assert-Equal -Expected 0
    }

    "Enable a privilege" = {
        # Ensure the privilege is disabled at the start
        [Ansible.Privilege.PrivilegeUtil]::DisablePrivilege($process, "SeTimeZonePrivilege") > $null

        $actual = [Ansible.Privilege.PrivilegeUtil]::EnablePrivilege($process, "SeTimeZonePrivilege")
        $actual.GetType().Name | Assert-Equal -Expected 'Dictionary`2'
        $actual.Count | Assert-Equal -Expected 1
        $actual.SeTimeZonePrivilege | Assert-Equal -Expected $false

        # Disable again
        $actual = [Ansible.Privilege.PrivilegeUtil]::EnablePrivilege($process, "SeTimeZonePrivilege")
        $actual.GetType().Name | Assert-Equal -Expected 'Dictionary`2'
        $actual.Count | Assert-Equal -Expected 0
    }

    "Disable and revert privileges" = {
        $current_state = [Ansible.Privilege.PrivilegeUtil]::GetAllPrivilegeInfo($process)

        $previous_state = [Ansible.Privilege.PrivilegeUtil]::DisableAllPrivileges($process)
        $previous_state.GetType().Name | Assert-Equal -Expected 'Dictionary`2'
        foreach ($previous_state_entry in $previous_state.GetEnumerator()) {
            $previous_state_entry.Value | Assert-Equal -Expected $true
        }

        # Disable again
        $previous_state2 = [Ansible.Privilege.PrivilegeUtil]::DisableAllPrivileges($process)
        $previous_state2.Count | Assert-Equal -Expected 0

        $actual = [Ansible.Privilege.PrivilegeUtil]::GetAllPrivilegeInfo($process)
        foreach ($actual_entry in $actual.GetEnumerator()) {
            $actual_entry.Value -band [Ansible.Privilege.PrivilegeAttributes]::Enabled | Assert-Equal -Expected 0
        }

        [Ansible.Privilege.PrivilegeUtil]::SetTokenPrivileges($process, $previous_state) > $null
        $actual = [Ansible.Privilege.PrivilegeUtil]::GetAllPrivilegeInfo($process)
        $actual | Assert-DictionaryEqual -Expected $current_state
    }

    "Remove a privilege" = {
        [Ansible.Privilege.PrivilegeUtil]::RemovePrivilege($process, "SeUndockPrivilege") > $null
        $actual = [Ansible.Privilege.PrivilegeUtil]::GetAllPrivilegeInfo($process)
        $actual.ContainsKey("SeUndockPrivilege") | Assert-Equal -Expected $false
    }

    "Test Enabler" = {
        # Disable privilege at the start
        $new_state = @{
            SeTimeZonePrivilege = $false
            SeShutdownPrivilege = $false
            SeIncreaseWorkingSetPrivilege = $false
        }
        [Ansible.Privilege.PrivilegeUtil]::SetTokenPrivileges($process, $new_state) > $null
        $check_state = [Ansible.Privilege.PrivilegeUtil]::GetAllPrivilegeInfo($process)
        $check_state.SeTimeZonePrivilege -band [Ansible.Privilege.PrivilegeAttributes]::Enabled | Assert-Equal -Expected 0
        $check_state.SeShutdownPrivilege -band [Ansible.Privilege.PrivilegeAttributes]::Enabled | Assert-Equal -Expected 0
        $check_state.SeIncreaseWorkingSetPrivilege -band [Ansible.Privilege.PrivilegeAttributes]::Enabled | Assert-Equal -Expected 0

        # Check that strict = false won't validate privileges not held but activates the ones we want
        $enabler = New-Object -TypeName Ansible.Privilege.PrivilegeEnabler -ArgumentList $false, "SeTimeZonePrivilege", "SeShutdownPrivilege", "SeTcbPrivilege"
        $actual = [Ansible.Privilege.PrivilegeUtil]::GetAllPrivilegeInfo($process)
        $actual.SeTimeZonePrivilege -band [Ansible.Privilege.PrivilegeAttributes]::Enabled |
            Assert-Equal -Expected ([Ansible.Privilege.PrivilegeAttributes]::Enabled)
        $actual.SeShutdownPrivilege -band [Ansible.Privilege.PrivilegeAttributes]::Enabled |
            Assert-Equal -Expected ([Ansible.Privilege.PrivilegeAttributes]::Enabled)
        $actual.SeIncreaseWorkingSetPrivilege -band [Ansible.Privilege.PrivilegeAttributes]::Enabled | Assert-Equal -Expected 0
        $actual.ContainsKey("SeTcbPrivilege") | Assert-Equal -Expected $false

        # Now verify a no-op enabler will not rever back to disabled
        $enabler2 = New-Object -TypeName Ansible.Privilege.PrivilegeEnabler -ArgumentList $false, "SeTimeZonePrivilege", "SeShutdownPrivilege", "SeTcbPrivilege"
        $enabler2.Dispose()
        $actual = [Ansible.Privilege.PrivilegeUtil]::GetAllPrivilegeInfo($process)
        $actual.SeTimeZonePrivilege -band [Ansible.Privilege.PrivilegeAttributes]::Enabled |
            Assert-Equal -Expected ([Ansible.Privilege.PrivilegeAttributes]::Enabled)
        $actual.SeShutdownPrivilege -band [Ansible.Privilege.PrivilegeAttributes]::Enabled |
            Assert-Equal -Expected ([Ansible.Privilege.PrivilegeAttributes]::Enabled)

        # Verify that when disposing the object the privileges are reverted
        $enabler.Dispose()
        $actual = [Ansible.Privilege.PrivilegeUtil]::GetAllPrivilegeInfo($process)
        $actual.SeTimeZonePrivilege -band [Ansible.Privilege.PrivilegeAttributes]::Enabled | Assert-Equal -Expected 0
        $actual.SeShutdownPrivilege -band [Ansible.Privilege.PrivilegeAttributes]::Enabled | Assert-Equal -Expected 0
    }

    "Test Enabler strict" = {
        # Disable privilege at the start
        $new_state = @{
            SeTimeZonePrivilege = $false
            SeShutdownPrivilege = $false
            SeIncreaseWorkingSetPrivilege = $false
        }
        [Ansible.Privilege.PrivilegeUtil]::SetTokenPrivileges($process, $new_state) > $null
        $check_state = [Ansible.Privilege.PrivilegeUtil]::GetAllPrivilegeInfo($process)
        $check_state.SeTimeZonePrivilege -band [Ansible.Privilege.PrivilegeAttributes]::Enabled | Assert-Equal -Expected 0
        $check_state.SeShutdownPrivilege -band [Ansible.Privilege.PrivilegeAttributes]::Enabled | Assert-Equal -Expected 0
        $check_state.SeIncreaseWorkingSetPrivilege -band [Ansible.Privilege.PrivilegeAttributes]::Enabled | Assert-Equal -Expected 0

        # Check that strict = false won't validate privileges not held but activates the ones we want
        $enabler = New-Object -TypeName Ansible.Privilege.PrivilegeEnabler -ArgumentList $true, "SeTimeZonePrivilege", "SeShutdownPrivilege"
        $actual = [Ansible.Privilege.PrivilegeUtil]::GetAllPrivilegeInfo($process)
        $actual.SeTimeZonePrivilege -band [Ansible.Privilege.PrivilegeAttributes]::Enabled |
            Assert-Equal -Expected ([Ansible.Privilege.PrivilegeAttributes]::Enabled)
        $actual.SeShutdownPrivilege -band [Ansible.Privilege.PrivilegeAttributes]::Enabled |
            Assert-Equal -Expected ([Ansible.Privilege.PrivilegeAttributes]::Enabled)
        $actual.SeIncreaseWorkingSetPrivilege -band [Ansible.Privilege.PrivilegeAttributes]::Enabled | Assert-Equal -Expected 0

        # Now verify a no-op enabler will not rever back to disabled
        $enabler2 = New-Object -TypeName Ansible.Privilege.PrivilegeEnabler -ArgumentList $true, "SeTimeZonePrivilege", "SeShutdownPrivilege"
        $enabler2.Dispose()
        $actual = [Ansible.Privilege.PrivilegeUtil]::GetAllPrivilegeInfo($process)
        $actual.SeTimeZonePrivilege -band [Ansible.Privilege.PrivilegeAttributes]::Enabled |
            Assert-Equal -Expected ([Ansible.Privilege.PrivilegeAttributes]::Enabled)
        $actual.SeShutdownPrivilege -band [Ansible.Privilege.PrivilegeAttributes]::Enabled |
            Assert-Equal -Expected ([Ansible.Privilege.PrivilegeAttributes]::Enabled)

        # Verify that when disposing the object the privileges are reverted
        $enabler.Dispose()
        $actual = [Ansible.Privilege.PrivilegeUtil]::GetAllPrivilegeInfo($process)
        $actual.SeTimeZonePrivilege -band [Ansible.Privilege.PrivilegeAttributes]::Enabled | Assert-Equal -Expected 0
        $actual.SeShutdownPrivilege -band [Ansible.Privilege.PrivilegeAttributes]::Enabled | Assert-Equal -Expected 0
    }

    "Test Enabler invalid privilege" = {
        $failed = $false
        try {
            New-Object -TypeName Ansible.Privilege.PrivilegeEnabler -ArgumentList $false, "SeTimeZonePrivilege", "SeFake"
        }
        catch {
            $failed = $true
            $expected = "Failed to enable privilege(s) SeTimeZonePrivilege, SeFake (A specified privilege does not exist, Win32ErrorCode 1313)"
            $_.Exception.InnerException.Message | Assert-Equal -Expected $expected
        }
        $failed | Assert-Equal -Expected $true
    }

    "Test Enabler strict failure" = {
        # Start disabled
        [Ansible.Privilege.PrivilegeUtil]::DisablePrivilege($process, "SeTimeZonePrivilege") > $null
        $check_state = [Ansible.Privilege.PrivilegeUtil]::GetAllPrivilegeInfo($process)
        $check_state.SeTimeZonePrivilege -band [Ansible.Privilege.PrivilegeAttributes]::Enabled | Assert-Equal -Expected 0

        $failed = $false
        try {
            New-Object -TypeName Ansible.Privilege.PrivilegeEnabler -ArgumentList $true, "SeTimeZonePrivilege", "SeTcbPrivilege"
        }
        catch {
            $failed = $true
            $expected = -join @(
                "Failed to enable privilege(s) SeTimeZonePrivilege, SeTcbPrivilege "
                "(Not all privileges or groups referenced are assigned to the caller, Win32ErrorCode 1300)"
            )
            $_.Exception.InnerException.Message | Assert-Equal -Expected $expected
        }
        $failed | Assert-Equal -Expected $true
    }
}

foreach ($test_impl in $tests.GetEnumerator()) {
    $test = $test_impl.Key
    &$test_impl.Value
}

$module.Result.data = "success"
$module.ExitJson()

