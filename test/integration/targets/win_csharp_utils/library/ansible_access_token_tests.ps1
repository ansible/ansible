# End of the setup code and start of the module code
#!powershell

#AnsibleRequires -CSharpUtil Ansible.AccessToken
#AnsibleRequires -CSharpUtil Ansible.Basic

$spec = @{
    options = @{
        test_username = @{ type = "str"; required = $true }
        test_password = @{ type = "str"; required = $true; no_log = $true }
    }
}
$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$test_username = $module.Params.test_username
$test_password = $module.Params.test_password

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

$current_user = [System.Security.Principal.WindowsIdentity]::GetCurrent().User

$tests = [Ordered]@{
    "Open process token" = {
        $h_process = [Ansible.AccessToken.TokenUtil]::OpenProcess()

        $h_token = [Ansible.AccessToken.TokenUtil]::OpenProcessToken($h_process, "Query")
        try {
            $h_token.IsClosed | Assert-Equals -Expected $false
            $h_token.IsInvalid | Assert-Equals -Expected $false

            $actual_user = [Ansible.AccessToken.TokenUtil]::GetTokenUser($h_token)
            $actual_user | Assert-Equals -Expected $current_user
        } finally {
            $h_token.Dispose()
        }
        $h_token.IsClosed | Assert-Equals -Expected $true
    }

    "Open process token of another process" = {
        $proc_info = Start-Process -FilePath "powershell.exe" -ArgumentList "-Command Start-Sleep -Seconds 60" -WindowStyle Hidden -PassThru
        try {
            $h_process = [Ansible.AccessToken.TokenUtil]::OpenProcess($proc_info.Id, "QueryInformation", $false)
            try {
                $h_process.IsClosed | Assert-Equals -Expected $false
                $h_process.IsInvalid | Assert-Equals -Expected $false

                $h_token = [Ansible.AccessToken.TokenUtil]::OpenProcessToken($h_process, "Query")
                try {
                    $actual_user = [Ansible.AccessToken.TokenUtil]::GetTokenUser($h_token)
                    $actual_user | Assert-Equals -Expected $current_user
                } finally {
                    $h_token.Dispose()
                }
            } finally {
                $h_process.Dispose()
            }
            $h_process.IsClosed | Assert-Equals -Expected $true
        } finally {
            $proc_info | Stop-Process
        }
    }

    "Failed to open process token" = {
        $failed = $false
        try {
            $h_process = [Ansible.AccessToken.TokenUtil]::OpenProcess(4, "QueryInformation", $false)
            $h_process.Dispose()  # Incase this doesn't fail, make sure we still dispose of it
        } catch [Ansible.AccessToken.Win32Exception] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "Failed to open process 4 with access QueryInformation (Access is denied, Win32ErrorCode 5 - 0x00000005)"
        }
        $failed | Assert-Equals -Expected $true
    }

    "Duplicate access token primary" = {
        $h_process = [Ansible.AccessToken.TokenUtil]::OpenProcess()
        $h_token = [Ansible.AccessToken.TokenUtil]::OpenProcessToken($h_process, "Duplicate")
        try {
            $dup_token = [Ansible.AccessToken.TokenUtil]::DuplicateToken($h_token, "Query", "Anonymous", "Primary")
            try {
                $dup_token.IsClosed | Assert-Equals -Expected $false
                $dup_token.IsInvalid | Assert-Equals -Expected $false

                $actual_user = [Ansible.AccessToken.TokenUtil]::GetTokenUser($dup_token)

                $actual_user | Assert-Equals -Expected $current_user
                $actual_stat = [Ansible.AccessToken.TokenUtil]::GetTokenStatistics($dup_token)

                $actual_stat.TokenType | Assert-Equals -Expected ([Ansible.AccessToken.TokenType]::Primary)
                $actual_stat.ImpersonationLevel | Assert-Equals -Expected ([Ansible.AccessToken.SecurityImpersonationLevel]::Anonymous)
            } finally {
                $dup_token.Dispose()
            }

            $dup_token.IsClosed | Assert-Equals -Expected $true
        } finally {
            $h_token.Dispose()
        }
    }

    "Duplicate access token impersonation" = {
        $h_process = [Ansible.AccessToken.TokenUtil]::OpenProcess()
        $h_token = [Ansible.AccessToken.TokenUtil]::OpenProcessToken($h_process, "Duplicate")
        try {
            "Anonymous", "Identification", "Impersonation", "Delegation" | ForEach-Object -Process {
                $dup_token = [Ansible.AccessToken.TokenUtil]::DuplicateToken($h_token, "Query", $_, "Impersonation")
                try {
                    $actual_user = [Ansible.AccessToken.TokenUtil]::GetTokenUser($dup_token)

                    $actual_user | Assert-Equals -Expected $current_user
                    $actual_stat = [Ansible.AccessToken.TokenUtil]::GetTokenStatistics($dup_token)

                    $actual_stat.TokenType | Assert-Equals -Expected ([Ansible.AccessToken.TokenType]::Impersonation)
                    $actual_stat.ImpersonationLevel | Assert-Equals -Expected ([Ansible.AccessToken.SecurityImpersonationLevel]"$_")
                } finally {
                    $dup_token.Dispose()
                }
            }
        } finally {
            $h_token.Dispose()
        }
    }

    "Impersonate SYSTEM token" = {
        $system_sid = New-Object -TypeName System.Security.Principal.SecurityIdentifier -ArgumentList @(
            [System.Security.Principal.WellKnownSidType]::LocalSystemSid,
            $null
        )
        $tested = $false
        foreach ($h_token in [Ansible.AccessToken.TokenUtil]::EnumerateUserTokens($system_sid, "Duplicate, Impersonate, Query")) {
            $actual_user = [Ansible.AccessToken.TokenUtil]::GetTokenUser($h_token)
            $actual_user | Assert-Equals -Expected $system_sid

            [Ansible.AccessToken.TokenUtil]::ImpersonateToken($h_token)
            try {
                $current_sid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
                $current_sid | Assert-Equals -Expected $system_sid
            } finally {
                [Ansible.AccessToken.TokenUtil]::RevertToSelf()
            }

            $current_sid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
            $current_sid | Assert-Equals -Expected $current_user

            # Will keep on looping for each SYSTEM token it can retrieve, we only want to test 1
            $tested = $true
            break
        }

        $tested | Assert-Equals -Expected $true
    }

    "Get token privileges" = {
        $h_process = [Ansible.AccessToken.TokenUtil]::OpenProcess()
        $h_token = [Ansible.AccessToken.TokenUtil]::OpenProcessToken($h_process, "Query")
        try {
            $priv_info = &whoami.exe /priv | Where-Object { $_.StartsWith("Se") }
            $actual_privs = [Ansible.AccessToken.Tokenutil]::GetTokenPrivileges($h_token)
            $actual_stat = [Ansible.AccessToken.TokenUtil]::GetTokenStatistics($h_token)

            $actual_privs.Count | Assert-Equals -Expected $priv_info.Count
            $actual_privs.Count | Assert-Equals -Expected $actual_stat.PrivilegeCount

            foreach ($info in $priv_info) {
                $info_split = $info.Split(" ", [System.StringSplitOptions]::RemoveEmptyEntries)
                $priv_name = $info_split[0]
                $priv_enabled = $info_split[-1] -eq "Enabled"
                $actual_priv = $actual_privs | Where-Object { $_.Name -eq $priv_name }

                $actual_priv -eq $null | Assert-Equals -Expected $false
                if ($priv_enabled) {
                    $actual_priv.Attributes.HasFlag([Ansible.AccessToken.PrivilegeAttributes]::Enabled) | Assert-Equals -Expected $true
                } else {
                    $actual_priv.Attributes.HasFlag([Ansible.AccessToken.PrivilegeAttributes]::Disabled) | Assert-Equals -Expected $true
                }
            }
        } finally {
            $h_token.Dispose()
        }
    }

    "Get token statistics" = {
        $h_process = [Ansible.AccessToken.TokenUtil]::OpenProcess()
        $h_token = [Ansible.AccessToken.TokenUtil]::OpenProcessToken($h_process, "Query")
        try {
            $actual_priv = [Ansible.AccessToken.Tokenutil]::GetTokenPrivileges($h_token)
            $actual_stat = [Ansible.AccessToken.TokenUtil]::GetTokenStatistics($h_token)

            $actual_stat.TokenId.GetType().FullName | Assert-Equals -Expected "Ansible.AccessToken.Luid"
            $actual_stat.AuthenticationId.GetType().FullName | Assert-Equals -Expected "Ansible.AccessToken.Luid"
            $actual_stat.ExpirationTime.GetType().FullName | Assert-Equals -Expected "System.Int64"

            $actual_stat.TokenType | Assert-Equals -Expected ([Ansible.AccessToken.TokenType]::Primary)

            $os_version = [Version](Get-Item -LiteralPath $env:SystemRoot\System32\kernel32.dll).VersionInfo.ProductVersion
            if ($os_version -lt [Version]"6.1") {
                # While the token is a primary token, Server 2008 reports the SecurityImpersonationLevel for a primary token as Impersonation
                $actual_stat.ImpersonationLevel | Assert-Equals -Expected ([Ansible.AccessToken.SecurityImpersonationLevel]::Impersonation)
            } else {
                $actual_stat.ImpersonationLevel | Assert-Equals -Expected ([Ansible.AccessToken.SecurityImpersonationLevel]::Anonymous)
            }
            $actual_stat.DynamicCharged.GetType().FullName | Assert-Equals -Expected "System.UInt32"
            $actual_stat.DynamicAvailable.GetType().FullName | Assert-Equals -Expected "System.UInt32"
            $actual_stat.GroupCount.GetType().FullName | Assert-Equals -Expected "System.UInt32"
            $actual_stat.PrivilegeCount | Assert-Equals -Expected $actual_priv.Count
            $actual_stat.ModifiedId.GetType().FullName | Assert-Equals -Expected "Ansible.AccessToken.Luid"
        } finally {
            $h_token.Dispose()
        }
    }

    "Get token linked token impersonation" = {
        $h_token = [Ansible.AccessToken.TokenUtil]::LogonUser($test_username, $null, $test_password, "Interactive", "Default")
        try {
            $actual_elevation_type = [Ansible.AccessToken.TokenUtil]::GetTokenElevationType($h_token)
            $actual_elevation_type | Assert-Equals -Expected ([Ansible.AccessToken.TokenElevationType]::Limited)

            $actual_linked = [Ansible.AccessToken.TokenUtil]::GetTokenLinkedToken($h_token)
            try {
                $actual_linked.IsClosed | Assert-Equals -Expected $false
                $actual_linked.IsInvalid | Assert-Equals -Expected $false

                $actual_elevation_type = [Ansible.AccessToken.TokenUtil]::GetTokenElevationType($actual_linked)
                $actual_elevation_type | Assert-Equals -Expected ([Ansible.AccessToken.TokenElevationType]::Full)

                $actual_stat = [Ansible.AccessToken.TokenUtil]::GetTokenStatistics($actual_linked)
                $actual_stat.TokenType | Assert-Equals -Expected ([Ansible.AccessToken.TokenType]::Impersonation)
            } finally {
                $actual_linked.Dispose()
            }
            $actual_linked.IsClosed | Assert-Equals -Expected $true
        } finally {
            $h_token.Dispose()
        }
    }

    "Get token linked token primary" = {
        # We need a token with the SeTcbPrivilege for this to work.
        $system_sid = New-Object -TypeName System.Security.Principal.SecurityIdentifier -ArgumentList @(
            [System.Security.Principal.WellKnownSidType]::LocalSystemSid,
            $null
        )
        $tested = $false
        foreach ($system_token in [Ansible.AccessToken.TokenUtil]::EnumerateUserTokens($system_sid, "Duplicate, Impersonate, Query")) {
            $privileges = [Ansible.AccessToken.TokenUtil]::GetTokenPrivileges($system_token)
            if ($null -eq ($privileges | Where-Object { $_.Name -eq "SeTcbPrivilege" })) {
                continue
            }

            $h_token = [Ansible.AccessToken.TokenUtil]::LogonUser($test_username, $null, $test_password, "Interactive", "Default")
            try {
                [Ansible.AccessToken.TokenUtil]::ImpersonateToken($system_token)
                try {
                    $actual_linked = [Ansible.AccessToken.TokenUtil]::GetTokenLinkedToken($h_token)
                    try {
                        $actual_linked.IsClosed | Assert-Equals -Expected $false
                        $actual_linked.IsInvalid | Assert-Equals -Expected $false

                        $actual_elevation_type = [Ansible.AccessToken.TokenUtil]::GetTokenElevationType($actual_linked)
                        $actual_elevation_type | Assert-Equals -Expected ([Ansible.AccessToken.TokenElevationType]::Full)

                        $actual_stat = [Ansible.AccessToken.TokenUtil]::GetTokenStatistics($actual_linked)
                        $actual_stat.TokenType | Assert-Equals -Expected ([Ansible.AccessToken.TokenType]::Primary)
                    } finally {
                        $actual_linked.Dispose()
                    }
                    $actual_linked.IsClosed | Assert-Equals -Expected $true
                } finally {
                    [Ansible.AccessToken.TokenUtil]::RevertToSelf()
                }
            } finally {
                $h_token.Dispose()
            }

            $tested = $true
            break
        }
        $tested | Assert-Equals -Expected $true
    }

    "Failed to get token information" = {
        $h_process = [Ansible.AccessToken.TokenUtil]::OpenProcess()
        $h_token = [Ansible.AccessToken.TokenUtil]::OpenProcessToken($h_process, 'Duplicate')  # Without Query the below will fail

        $failed = $false
        try {
            [Ansible.AccessToken.TokenUtil]::GetTokenUser($h_token)
        } catch [Ansible.AccessToken.Win32Exception] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "GetTokenInformation(TokenUser) failed to get buffer length (Access is denied, Win32ErrorCode 5 - 0x00000005)"
        } finally {
            $h_token.Dispose()
        }
        $failed | Assert-Equals -Expected $true
    }

    "Logon with valid credentials" = {
        $expected_user = New-Object -TypeName System.Security.Principal.NTAccount -ArgumentList $test_username
        $expected_sid = $expected_user.Translate([System.Security.Principal.SecurityIdentifier])

        $h_token = [Ansible.AccessToken.TokenUtil]::LogonUser($test_username, $null, $test_password, "Network", "Default")
        try {
            $h_token.IsClosed | Assert-Equals -Expected $false
            $h_token.IsInvalid | Assert-Equals -Expected $false

            $actual_user = [Ansible.AccessToken.TokenUtil]::GetTokenUser($h_token)
            $actual_user | Assert-Equals -Expected $expected_sid
        } finally {
            $h_token.Dispose()
        }
        $h_token.IsClosed | Assert-Equals -Expected $true
    }

    "Logon with invalid credentials" = {
        $failed = $false
        try {
            [Ansible.AccessToken.TokenUtil]::LogonUser("fake-user", $null, "fake-pass", "Network", "Default")
        } catch [Ansible.AccessToken.Win32Exception] {
            $failed = $true
            $_.Exception.Message.Contains("Failed to logon fake-user") | Assert-Equals -Expected $true
            $_.Exception.Message.Contains("Win32ErrorCode 1326 - 0x0000052E)") | Assert-Equals -Expected $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Logon with invalid credential with domain account" = {
        $failed = $false
        try {
            [Ansible.AccessToken.TokenUtil]::LogonUser("fake-user", "fake-domain", "fake-pass", "Network", "Default")
        } catch [Ansible.AccessToken.Win32Exception] {
            $failed = $true
            $_.Exception.Message.Contains("Failed to logon fake-domain\fake-user") | Assert-Equals -Expected $true
            $_.Exception.Message.Contains("Win32ErrorCode 1326 - 0x0000052E)") | Assert-Equals -Expected $true
        }
        $failed | Assert-Equals -Expected $true
    }
}

foreach ($test_impl in $tests.GetEnumerator()) {
    $test = $test_impl.Key
    &$test_impl.Value
}

$module.Result.data = "success"
$module.ExitJson()
