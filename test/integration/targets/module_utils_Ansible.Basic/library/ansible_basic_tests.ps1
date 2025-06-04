#!powershell

#AnsibleRequires -CSharpUtil Ansible.Basic

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
            $module.Result.failed = $true
            $module.Result.test = $test
            $module.Result.actual = $Actual
            $module.Result.expected = $Expected
            $module.Result.line = $call_stack.ScriptLineNumber
            $module.Result.method = $call_stack.Position.Text
            $module.Result.msg = "AssertionError: actual != expected"

            Exit-Module
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
            elseif ($actual_value -is [System.Collections.ArrayList] -or $actual_value -is [Array]) {
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

Function Exit-Module {
    # Make sure Exit actually calls exit and not our overridden test behaviour
    [Ansible.Basic.AnsibleModule]::Exit = { param([Int32]$rc) exit $rc }
    Write-Output -InputObject (ConvertTo-Json -InputObject $module.Result -Compress -Depth 99)
    $module.ExitJson()
}

$tmpdir = $module.Tmpdir

# Override the Exit and WriteLine behaviour to throw an exception instead of exiting the module
[Ansible.Basic.AnsibleModule]::Exit = {
    param([Int32]$rc)
    $exp = New-Object -TypeName System.Exception -ArgumentList "exit: $rc"
    $exp | Add-Member -Type NoteProperty -Name Output -Value $_test_out
    throw $exp
}
[Ansible.Basic.AnsibleModule]::WriteLine = {
    param([String]$line)
    Set-Variable -Name _test_out -Scope Global -Value $line
}

$tests = @{
    "Empty spec and no options - args file" = {
        $args_file = Join-Path -Path $tmpdir -ChildPath "args-$(Get-Random).json"
        [System.IO.File]::WriteAllText($args_file, '{ "ANSIBLE_MODULE_ARGS": {} }')
        $m = [Ansible.Basic.AnsibleModule]::Create(@($args_file), @{})

        $m.CheckMode | Assert-Equal -Expected $false
        $m.DebugMode | Assert-Equal -Expected $false
        $m.DiffMode | Assert-Equal -Expected $false
        $m.KeepRemoteFiles | Assert-Equal -Expected $false
        $m.ModuleName | Assert-Equal -Expected "undefined win module"
        $m.NoLog | Assert-Equal -Expected $false
        $m.Verbosity | Assert-Equal -Expected 0
        $m.AnsibleVersion | Assert-Equal -Expected $null
    }

    "Empty spec and no options - complex_args" = {
        Set-Variable -Name complex_args -Scope Global -Value @{}
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})

        $m.CheckMode | Assert-Equal -Expected $false
        $m.DebugMode | Assert-Equal -Expected $false
        $m.DiffMode | Assert-Equal -Expected $false
        $m.KeepRemoteFiles | Assert-Equal -Expected $false
        $m.ModuleName | Assert-Equal -Expected "undefined win module"
        $m.NoLog | Assert-Equal -Expected $false
        $m.Verbosity | Assert-Equal -Expected 0
        $m.AnsibleVersion | Assert-Equal -Expected $null
    }

    "Internal param changes - args file" = {
        $m_tmpdir = Join-Path -Path $tmpdir -ChildPath "moduletmpdir-$(Get-Random)"
        New-Item -Path $m_tmpdir -ItemType Directory > $null
        $args_file = Join-Path -Path $tmpdir -ChildPath "args-$(Get-Random).json"
        [System.IO.File]::WriteAllText($args_file, @"
{
    "ANSIBLE_MODULE_ARGS": {
        "_ansible_check_mode": true,
        "_ansible_debug": true,
        "_ansible_diff": true,
        "_ansible_keep_remote_files": true,
        "_ansible_module_name": "ansible_basic_tests",
        "_ansible_no_log": true,
        "_ansible_remote_tmp": "%TEMP%",
        "_ansible_selinux_special_fs": "ignored",
        "_ansible_shell_executable": "ignored",
        "_ansible_socket": "ignored",
        "_ansible_syslog_facility": "ignored",
        "_ansible_target_log_info": "ignored",
        "_ansible_tmpdir": "$($m_tmpdir -replace "\\", "\\")",
        "_ansible_verbosity": 3,
        "_ansible_version": "2.8.0"
    }
}
"@)
        $m = [Ansible.Basic.AnsibleModule]::Create(@($args_file), @{supports_check_mode = $true })
        $m.CheckMode | Assert-Equal -Expected $true
        $m.DebugMode | Assert-Equal -Expected $true
        $m.DiffMode | Assert-Equal -Expected $true
        $m.KeepRemoteFiles | Assert-Equal -Expected $true
        $m.ModuleName | Assert-Equal -Expected "ansible_basic_tests"
        $m.NoLog | Assert-Equal -Expected $true
        $m.Verbosity | Assert-Equal -Expected 3
        $m.AnsibleVersion | Assert-Equal -Expected "2.8.0"
        $m.Tmpdir | Assert-Equal -Expected $m_tmpdir
    }

    "Internal param changes - complex_args" = {
        $m_tmpdir = Join-Path -Path $tmpdir -ChildPath "moduletmpdir-$(Get-Random)"
        New-Item -Path $m_tmpdir -ItemType Directory > $null
        Set-Variable -Name complex_args -Scope Global -Value @{
            _ansible_check_mode = $true
            _ansible_debug = $true
            _ansible_diff = $true
            _ansible_keep_remote_files = $true
            _ansible_module_name = "ansible_basic_tests"
            _ansible_no_log = $true
            _ansible_remote_tmp = "%TEMP%"
            _ansible_selinux_special_fs = "ignored"
            _ansible_shell_executable = "ignored"
            _ansible_socket = "ignored"
            _ansible_syslog_facility = "ignored"
            _ansible_tmpdir = $m_tmpdir.ToString()
            _ansible_verbosity = 3
            _ansible_version = "2.8.0"
        }
        $spec = @{
            supports_check_mode = $true
        }
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        $m.CheckMode | Assert-Equal -Expected $true
        $m.DebugMode | Assert-Equal -Expected $true
        $m.DiffMode | Assert-Equal -Expected $true
        $m.KeepRemoteFiles | Assert-Equal -Expected $true
        $m.ModuleName | Assert-Equal -Expected "ansible_basic_tests"
        $m.NoLog | Assert-Equal -Expected $true
        $m.Verbosity | Assert-Equal -Expected 3
        $m.AnsibleVersion | Assert-Equal -Expected "2.8.0"
        $m.Tmpdir | Assert-Equal -Expected $m_tmpdir
    }

    "Parse complex module options" = {
        $spec = @{
            options = @{
                option_default = @{}
                missing_option_default = @{}
                string_option = @{type = "str" }
                required_option = @{required = $true }
                missing_choices = @{choices = "a", "b" }
                choices = @{choices = "a", "b" }
                one_choice = @{choices = , "b" }
                choice_with_default = @{choices = "a", "b"; default = "b" }
                alias_direct = @{aliases = , "alias_direct1" }
                alias_as_alias = @{aliases = "alias_as_alias1", "alias_as_alias2" }
                bool_type = @{type = "bool" }
                bool_from_str = @{type = "bool" }
                dict_type = @{
                    type = "dict"
                    options = @{
                        int_type = @{type = "int" }
                        str_type = @{type = "str"; default = "str_sub_type" }
                    }
                }
                dict_type_missing = @{
                    type = "dict"
                    options = @{
                        int_type = @{type = "int" }
                        str_type = @{type = "str"; default = "str_sub_type" }
                    }
                }
                dict_type_defaults = @{
                    type = "dict"
                    apply_defaults = $true
                    options = @{
                        int_type = @{type = "int" }
                        str_type = @{type = "str"; default = "str_sub_type" }
                    }
                }
                dict_type_json = @{type = "dict" }
                dict_type_str = @{type = "dict" }
                float_type = @{type = "float" }
                int_type = @{type = "int" }
                json_type = @{type = "json" }
                json_type_dict = @{type = "json" }
                list_type = @{type = "list" }
                list_type_str = @{type = "list" }
                list_with_int = @{type = "list"; elements = "int" }
                list_type_single = @{type = "list" }
                list_with_dict = @{
                    type = "list"
                    elements = "dict"
                    options = @{
                        int_type = @{type = "int" }
                        str_type = @{type = "str"; default = "str_sub_type" }
                    }
                }
                path_type = @{type = "path" }
                path_type_nt = @{type = "path" }
                path_type_missing = @{type = "path" }
                raw_type_str = @{type = "raw" }
                raw_type_int = @{type = "raw" }
                sid_type = @{type = "sid" }
                sid_from_name = @{type = "sid" }
                str_type = @{type = "str" }
                delegate_type = @{type = [Func[[Object], [UInt64]]] { [System.UInt64]::Parse($args[0]) } }
            }
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            option_default = 1
            string_option = 1
            required_option = "required"
            choices = "a"
            one_choice = "b"
            alias_direct = "a"
            alias_as_alias2 = "a"
            bool_type = $true
            bool_from_str = "false"
            dict_type = @{
                int_type = "10"
            }
            dict_type_json = '{"a":"a","b":1,"c":["a","b"]}'
            dict_type_str = 'a=a b="b 2" c=c'
            float_type = "3.14159"
            int_type = 0
            json_type = '{"a":"a","b":1,"c":["a","b"]}'
            json_type_dict = @{
                a = "a"
                b = 1
                c = @("a", "b")
            }
            list_type = @("a", "b", 1, 2)
            list_type_str = "a, b,1,2 "
            list_with_int = @("1", 2)
            list_type_single = "single"
            list_with_dict = @(
                @{
                    int_type = 2
                    str_type = "dict entry"
                },
                @{ int_type = 1 },
                @{}
            )
            path_type = "%SystemRoot%\System32"
            path_type_nt = "\\?\%SystemRoot%\System32"
            path_type_missing = "T:\missing\path"
            raw_type_str = "str"
            raw_type_int = 1
            sid_type = "S-1-5-18"
            sid_from_name = "SYSTEM"
            str_type = "str"
            delegate_type = "1234"
        }
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)

        $m.Params.option_default | Assert-Equal -Expected "1"
        $m.Params.option_default.GetType().ToString() | Assert-Equal -Expected "System.String"
        $m.Params.missing_option_default | Assert-Equal -Expected $null
        $m.Params.string_option | Assert-Equal -Expected "1"
        $m.Params.string_option.GetType().ToString() | Assert-Equal -Expected "System.String"
        $m.Params.required_option | Assert-Equal -Expected "required"
        $m.Params.required_option.GetType().ToString() | Assert-Equal -Expected "System.String"
        $m.Params.missing_choices | Assert-Equal -Expected $null
        $m.Params.choices | Assert-Equal -Expected "a"
        $m.Params.choices.GetType().ToString() | Assert-Equal -Expected "System.String"
        $m.Params.one_choice | Assert-Equal -Expected "b"
        $m.Params.one_choice.GetType().ToString() | Assert-Equal -Expected "System.String"
        $m.Params.choice_with_default | Assert-Equal -Expected "b"
        $m.Params.choice_with_default.GetType().ToString() | Assert-Equal -Expected "System.String"
        $m.Params.alias_direct | Assert-Equal -Expected "a"
        $m.Params.alias_direct.GetType().ToString() | Assert-Equal -Expected "System.String"
        $m.Params.alias_as_alias | Assert-Equal -Expected "a"
        $m.Params.alias_as_alias.GetType().ToString() | Assert-Equal -Expected "System.String"
        $m.Params.bool_type | Assert-Equal -Expected $true
        $m.Params.bool_type.GetType().ToString() | Assert-Equal -Expected "System.Boolean"
        $m.Params.bool_from_str | Assert-Equal -Expected $false
        $m.Params.bool_from_str.GetType().ToString() | Assert-Equal -Expected "System.Boolean"
        $m.Params.dict_type | Assert-DictionaryEqual -Expected @{int_type = 10; str_type = "str_sub_type" }
        $m.Params.dict_type.GetType().ToString() | Assert-Equal -Expected "System.Collections.Generic.Dictionary``2[System.String,System.Object]"
        $m.Params.dict_type.int_type.GetType().ToString() | Assert-Equal -Expected "System.Int32"
        $m.Params.dict_type.str_type.GetType().ToString() | Assert-Equal -Expected "System.String"
        $m.Params.dict_type_missing | Assert-Equal -Expected $null
        $m.Params.dict_type_defaults | Assert-DictionaryEqual -Expected @{int_type = $null; str_type = "str_sub_type" }
        $m.Params.dict_type_defaults.GetType().ToString() | Assert-Equal -Expected "System.Collections.Generic.Dictionary``2[System.String,System.Object]"
        $m.Params.dict_type_defaults.str_type.GetType().ToString() | Assert-Equal -Expected "System.String"
        $m.Params.dict_type_json | Assert-DictionaryEqual -Expected @{
            a = "a"
            b = 1
            c = @("a", "b")
        }
        $m.Params.dict_type_json.GetType().ToString() | Assert-Equal -Expected "System.Collections.Generic.Dictionary``2[System.String,System.Object]"
        $m.Params.dict_type_json.a.GetType().ToString() | Assert-Equal -Expected "System.String"
        $m.Params.dict_type_json.b.GetType().ToString() | Assert-Equal -Expected "System.Int32"
        $m.Params.dict_type_json.c.GetType().ToString() | Assert-Equal -Expected "System.Collections.ArrayList"
        $m.Params.dict_type_str | Assert-DictionaryEqual -Expected @{a = "a"; b = "b 2"; c = "c" }
        $m.Params.dict_type_str.GetType().ToString() | Assert-Equal -Expected "System.Collections.Generic.Dictionary``2[System.String,System.Object]"
        $m.Params.dict_type_str.a.GetType().ToString() | Assert-Equal -Expected "System.String"
        $m.Params.dict_type_str.b.GetType().ToString() | Assert-Equal -Expected "System.String"
        $m.Params.dict_type_str.c.GetType().ToString() | Assert-Equal -Expected "System.String"
        $m.Params.float_type | Assert-Equal -Expected ([System.Single]3.14159)
        $m.Params.float_type.GetType().ToString() | Assert-Equal -Expected "System.Single"
        $m.Params.int_type | Assert-Equal -Expected 0
        $m.Params.int_type.GetType().ToString() | Assert-Equal -Expected "System.Int32"
        $m.Params.json_type | Assert-Equal -Expected '{"a":"a","b":1,"c":["a","b"]}'
        $m.Params.json_type.GetType().ToString() | Assert-Equal -Expected "System.String"
        $jsonValue = ([Ansible.Basic.AnsibleModule]::FromJson('{"a":"a","b":1,"c":["a","b"]}'))
        [Ansible.Basic.AnsibleModule]::FromJson($m.Params.json_type_dict) | Assert-DictionaryEqual -Expected $jsonValue
        $m.Params.json_type_dict.GetType().ToString() | Assert-Equal -Expected "System.String"
        $m.Params.list_type.GetType().ToString() | Assert-Equal -Expected "System.Collections.Generic.List``1[System.Object]"
        $m.Params.list_type.Count | Assert-Equal -Expected 4
        $m.Params.list_type[0] | Assert-Equal -Expected "a"
        $m.Params.list_type[0].GetType().FullName | Assert-Equal -Expected "System.String"
        $m.Params.list_type[1] | Assert-Equal -Expected "b"
        $m.Params.list_type[1].GetType().FullName | Assert-Equal -Expected "System.String"
        $m.Params.list_type[2] | Assert-Equal -Expected 1
        $m.Params.list_type[2].GetType().FullName | Assert-Equal -Expected "System.Int32"
        $m.Params.list_type[3] | Assert-Equal -Expected 2
        $m.Params.list_type[3].GetType().FullName | Assert-Equal -Expected "System.Int32"
        $m.Params.list_type_str.GetType().ToString() | Assert-Equal -Expected "System.Collections.Generic.List``1[System.Object]"
        $m.Params.list_type_str.Count | Assert-Equal -Expected 4
        $m.Params.list_type_str[0] | Assert-Equal -Expected "a"
        $m.Params.list_type_str[0].GetType().FullName | Assert-Equal -Expected "System.String"
        $m.Params.list_type_str[1] | Assert-Equal -Expected "b"
        $m.Params.list_type_str[1].GetType().FullName | Assert-Equal -Expected "System.String"
        $m.Params.list_type_str[2] | Assert-Equal -Expected "1"
        $m.Params.list_type_str[2].GetType().FullName | Assert-Equal -Expected "System.String"
        $m.Params.list_type_str[3] | Assert-Equal -Expected "2"
        $m.Params.list_type_str[3].GetType().FullName | Assert-Equal -Expected "System.String"
        $m.Params.list_with_int.GetType().ToString() | Assert-Equal -Expected "System.Collections.Generic.List``1[System.Object]"
        $m.Params.list_with_int.Count | Assert-Equal -Expected 2
        $m.Params.list_with_int[0] | Assert-Equal -Expected 1
        $m.Params.list_with_int[0].GetType().FullName | Assert-Equal -Expected "System.Int32"
        $m.Params.list_with_int[1] | Assert-Equal -Expected 2
        $m.Params.list_with_int[1].GetType().FullName | Assert-Equal -Expected "System.Int32"
        $m.Params.list_type_single.GetType().ToString() | Assert-Equal -Expected "System.Collections.Generic.List``1[System.Object]"
        $m.Params.list_type_single.Count | Assert-Equal -Expected 1
        $m.Params.list_type_single[0] | Assert-Equal -Expected "single"
        $m.Params.list_type_single[0].GetType().FullName | Assert-Equal -Expected "System.String"
        $m.Params.list_with_dict.GetType().FullName.StartsWith("System.Collections.Generic.List``1[[System.Object") | Assert-Equal -Expected $true
        $m.Params.list_with_dict.Count | Assert-Equal -Expected 3
        $m.Params.list_with_dict[0].GetType().FullName.StartsWith("System.Collections.Generic.Dictionary``2[[System.String") | Assert-Equal -Expected $true
        $m.Params.list_with_dict[0] | Assert-DictionaryEqual -Expected @{int_type = 2; str_type = "dict entry" }
        $m.Params.list_with_dict[0].int_type.GetType().FullName.ToString() | Assert-Equal -Expected "System.Int32"
        $m.Params.list_with_dict[0].str_type.GetType().FullName.ToString() | Assert-Equal -Expected "System.String"
        $m.Params.list_with_dict[1].GetType().FullName.StartsWith("System.Collections.Generic.Dictionary``2[[System.String") | Assert-Equal -Expected $true
        $m.Params.list_with_dict[1] | Assert-DictionaryEqual -Expected @{int_type = 1; str_type = "str_sub_type" }
        $m.Params.list_with_dict[1].int_type.GetType().FullName.ToString() | Assert-Equal -Expected "System.Int32"
        $m.Params.list_with_dict[1].str_type.GetType().FullName.ToString() | Assert-Equal -Expected "System.String"
        $m.Params.list_with_dict[2].GetType().FullName.StartsWith("System.Collections.Generic.Dictionary``2[[System.String") | Assert-Equal -Expected $true
        $m.Params.list_with_dict[2] | Assert-DictionaryEqual -Expected @{int_type = $null; str_type = "str_sub_type" }
        $m.Params.list_with_dict[2].str_type.GetType().FullName.ToString() | Assert-Equal -Expected "System.String"
        $m.Params.path_type | Assert-Equal -Expected "$($env:SystemRoot)\System32"
        $m.Params.path_type.GetType().ToString() | Assert-Equal -Expected "System.String"
        $m.Params.path_type_nt | Assert-Equal -Expected "\\?\%SystemRoot%\System32"
        $m.Params.path_type_nt.GetType().ToString() | Assert-Equal -Expected "System.String"
        $m.Params.path_type_missing | Assert-Equal -Expected "T:\missing\path"
        $m.Params.path_type_missing.GetType().ToString() | Assert-Equal -Expected "System.String"
        $m.Params.raw_type_str | Assert-Equal -Expected "str"
        $m.Params.raw_type_str.GetType().FullName | Assert-Equal -Expected "System.String"
        $m.Params.raw_type_int | Assert-Equal -Expected 1
        $m.Params.raw_type_int.GetType().FullName | Assert-Equal -Expected "System.Int32"
        $m.Params.sid_type | Assert-Equal -Expected (New-Object -TypeName System.Security.Principal.SecurityIdentifier -ArgumentList "S-1-5-18")
        $m.Params.sid_type.GetType().ToString() | Assert-Equal -Expected "System.Security.Principal.SecurityIdentifier"
        $m.Params.sid_from_name | Assert-Equal -Expected (New-Object -TypeName System.Security.Principal.SecurityIdentifier -ArgumentList "S-1-5-18")
        $m.Params.sid_from_name.GetType().ToString() | Assert-Equal -Expected "System.Security.Principal.SecurityIdentifier"
        $m.Params.str_type | Assert-Equal -Expected "str"
        $m.Params.str_type.GetType().ToString() | Assert-Equal -Expected "System.String"
        $m.Params.delegate_type | Assert-Equal -Expected 1234
        $m.Params.delegate_type.GetType().ToString() | Assert-Equal -Expected "System.UInt64"

        $failed = $false
        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected_module_args = @{
            option_default = "1"
            missing_option_default = $null
            string_option = "1"
            required_option = "required"
            missing_choices = $null
            choices = "a"
            one_choice = "b"
            choice_with_default = "b"
            alias_direct = "a"
            alias_as_alias = "a"
            alias_as_alias2 = "a"
            bool_type = $true
            bool_from_str = $false
            dict_type = @{
                int_type = 10
                str_type = "str_sub_type"
            }
            dict_type_missing = $null
            dict_type_defaults = @{
                int_type = $null
                str_type = "str_sub_type"
            }
            dict_type_json = @{
                a = "a"
                b = 1
                c = @("a", "b")
            }
            dict_type_str = @{
                a = "a"
                b = "b 2"
                c = "c"
            }
            float_type = 3.14159
            int_type = 0
            json_type = $m.Params.json_type.ToString()
            json_type_dict = $m.Params.json_type_dict.ToString()
            list_type = @("a", "b", 1, 2)
            list_type_str = @("a", "b", "1", "2")
            list_with_int = @(1, 2)
            list_type_single = @("single")
            list_with_dict = @(
                @{
                    int_type = 2
                    str_type = "dict entry"
                },
                @{
                    int_type = 1
                    str_type = "str_sub_type"
                },
                @{
                    int_type = $null
                    str_type = "str_sub_type"
                }
            )
            path_type = "$($env:SystemRoot)\System32"
            path_type_nt = "\\?\%SystemRoot%\System32"
            path_type_missing = "T:\missing\path"
            raw_type_str = "str"
            raw_type_int = 1
            sid_type = "S-1-5-18"
            sid_from_name = "S-1-5-18"
            str_type = "str"
            delegate_type = 1234
        }
        $actual.Keys.Count | Assert-Equal -Expected 2
        $actual.changed | Assert-Equal -Expected $false
        $actual.invocation | Assert-DictionaryEqual -Expected @{module_args = $expected_module_args }
    }

    "Parse module args with list elements and delegate type" = {
        $spec = @{
            options = @{
                list_delegate_type = @{
                    type = "list"
                    elements = [Func[[Object], [UInt16]]] { [System.UInt16]::Parse($args[0]) }
                }
            }
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            list_delegate_type = @(
                "1234",
                4321
            )
        }
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        $m.Params.list_delegate_type.GetType().Name | Assert-Equal -Expected 'List`1'
        $m.Params.list_delegate_type[0].GetType().FullName | Assert-Equal -Expected "System.UInt16"
        $m.Params.list_delegate_Type[1].GetType().FullName | Assert-Equal -Expected "System.UInt16"

        $failed = $false
        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected_module_args = @{
            list_delegate_type = @(
                1234,
                4321
            )
        }
        $actual.Keys.Count | Assert-Equal -Expected 2
        $actual.changed | Assert-Equal -Expected $false
        $actual.invocation | Assert-DictionaryEqual -Expected @{module_args = $expected_module_args }
    }

    "Parse module args with case insensitive input" = {
        $spec = @{
            options = @{
                option1 = @{ type = "int"; required = $true }
            }
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            _ansible_module_name = "win_test"
            Option1 = "1"
        }

        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        # Verifies the case of the params key is set to the module spec not actual input
        $m.Params.Keys | Assert-Equal -Expected @("option1")
        $m.Params.option1 | Assert-Equal -Expected 1

        # Verifies the type conversion happens even on a case insensitive match
        $m.Params.option1.GetType().FullName | Assert-Equal -Expected "System.Int32"

        $failed = $false
        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected_warnings = "Parameters for (win_test) was a case insensitive match: Option1. "
        $expected_warnings += "Module options will become case sensitive in a future Ansible release. "
        $expected_warnings += "Supported parameters include: option1"

        $expected = @{
            changed = $false
            invocation = @{
                module_args = @{
                    option1 = 1
                }
            }
            # We have disabled the warning for now
            #warnings = @($expected_warnings)
        }
        $actual | Assert-DictionaryEqual -Expected $expected
    }

    "No log values" = {
        $spec = @{
            options = @{
                username = @{type = "str" }
                password = @{type = "str"; no_log = $true }
                password2 = @{type = "int"; no_log = $true }
                dict = @{type = "dict" }
            }
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            _ansible_module_name = "test_no_log"
            username = "user - pass - name"
            password = "pass"
            password2 = 1234
            dict = @{
                data = "Oops this is secret: pass"
                dict = @{
                    pass = "plain"
                    hide = "pass"
                    sub_hide = "password"
                    int_hide = 123456
                }
                list = @(
                    "pass",
                    "password",
                    1234567,
                    "pa ss",
                    @{
                        pass = "plain"
                        hide = "pass"
                        sub_hide = "password"
                        int_hide = 123456
                    }
                )
                custom = "pass"
            }
        }

        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        $m.Result.data = $complex_args.dict

        # verify params internally aren't masked
        $m.Params.username | Assert-Equal -Expected "user - pass - name"
        $m.Params.password | Assert-Equal -Expected "pass"
        $m.Params.password2 | Assert-Equal -Expected 1234
        $m.Params.dict.custom | Assert-Equal -Expected "pass"

        $failed = $false
        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        # verify no_log params are masked in invocation
        $expected = @{
            invocation = @{
                module_args = @{
                    password2 = "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"
                    dict = @{
                        dict = @{
                            pass = "plain"
                            hide = "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"
                            sub_hide = "********word"
                            int_hide = "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"
                        }
                        custom = "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"
                        list = @(
                            "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER",
                            "********word",
                            "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER",
                            "pa ss",
                            @{
                                pass = "plain"
                                hide = "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"
                                sub_hide = "********word"
                                int_hide = "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"
                            }
                        )
                        data = "Oops this is secret: ********"
                    }
                    username = "user - ******** - name"
                    password = "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"
                }
            }
            changed = $false
            data = $complex_args.dict
        }
        $actual | Assert-DictionaryEqual -Expected $expected

        $expected_event = @'
test_no_log - Invoked with:
  username: user - ******** - name
  dict: dict: sub_hide: ****word
      pass: plain
      int_hide: ********56
      hide: VALUE_SPECIFIED_IN_NO_LOG_PARAMETER
      data: Oops this is secret: ********
      custom: VALUE_SPECIFIED_IN_NO_LOG_PARAMETER
      list:
      - VALUE_SPECIFIED_IN_NO_LOG_PARAMETER
      - ********word
      - ********567
      - pa ss
      - sub_hide: ********word
          pass: plain
          int_hide: ********56
          hide: VALUE_SPECIFIED_IN_NO_LOG_PARAMETER
  password2: VALUE_SPECIFIED_IN_NO_LOG_PARAMETER
  password: VALUE_SPECIFIED_IN_NO_LOG_PARAMETER
'@
        $actual_event = (Get-EventLog -LogName Application -Source Ansible -Newest 1).Message
        $actual_event | Assert-DictionaryEqual -Expected $expected_event
    }

    "No log value with an empty string" = {
        $spec = @{
            options = @{
                password1 = @{type = "str"; no_log = $true }
                password2 = @{type = "str"; no_log = $true }
            }
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            _ansible_module_name = "test_no_log"
            password1 = ""
        }

        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        $m.Result.data = $complex_args.dict

        # verify params internally aren't masked
        $m.Params.password1 | Assert-Equal -Expected ""
        $m.Params.password2 | Assert-Equal -Expected $null

        $failed = $false
        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected = @{
            invocation = @{
                module_args = @{
                    password1 = ""
                    password2 = $null
                }
            }
            changed = $false
            data = $complex_args.dict
        }
        $actual | Assert-DictionaryEqual -Expected $expected
    }

    "Removed in version" = {
        $spec = @{
            options = @{
                removed1 = @{removed_in_version = "2.1" }
                removed2 = @{removed_in_version = "2.2" }
                removed3 = @{removed_in_version = "2.3"; removed_from_collection = "ansible.builtin" }
            }
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            removed1 = "value"
            removed3 = "value"
        }

        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)

        $failed = $false
        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected = @{
            changed = $false
            invocation = @{
                module_args = @{
                    removed1 = "value"
                    removed2 = $null
                    removed3 = "value"
                }
            }
            deprecations = @(
                @{
                    msg = "Param 'removed3' is deprecated. See the module docs for more information"
                    version = "2.3"
                    collection_name = "ansible.builtin"
                },
                @{
                    msg = "Param 'removed1' is deprecated. See the module docs for more information"
                    version = "2.1"
                    collection_name = $null
                }
            )
        }
        $actual | Assert-DictionaryEqual -Expected $expected
    }

    "Removed at date" = {
        $spec = @{
            options = @{
                removed1 = @{removed_at_date = [DateTime]"2020-03-10" }
                removed2 = @{removed_at_date = [DateTime]"2020-03-11" }
                removed3 = @{removed_at_date = [DateTime]"2020-06-07"; removed_from_collection = "ansible.builtin" }
            }
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            removed1 = "value"
            removed3 = "value"
        }

        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)

        $failed = $false
        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected = @{
            changed = $false
            invocation = @{
                module_args = @{
                    removed1 = "value"
                    removed2 = $null
                    removed3 = "value"
                }
            }
            deprecations = @(
                @{
                    msg = "Param 'removed3' is deprecated. See the module docs for more information"
                    date = "2020-06-07"
                    collection_name = "ansible.builtin"
                },
                @{
                    msg = "Param 'removed1' is deprecated. See the module docs for more information"
                    date = "2020-03-10"
                    collection_name = $null
                }
            )
        }
        $actual | Assert-DictionaryEqual -Expected $expected
    }

    "Deprecated aliases" = {
        $spec = @{
            options = @{
                option1 = @{ type = "str"; aliases = "alias1"; deprecated_aliases = @(@{name = "alias1"; version = "2.10" }) }
                option2 = @{ type = "str"; aliases = "alias2"; deprecated_aliases = @(@{name = "alias2"; version = "2.11" }) }
                option3 = @{
                    type = "dict"
                    options = @{
                        option1 = @{ type = "str"; aliases = "alias1"; deprecated_aliases = @(@{name = "alias1"; version = "2.10" }) }
                        option2 = @{ type = "str"; aliases = "alias2"; deprecated_aliases = @(@{name = "alias2"; version = "2.11" }) }
                        option3 = @{
                            type = "str"
                            aliases = "alias3"
                            deprecated_aliases = @(
                                @{name = "alias3"; version = "2.12"; collection_name = "ansible.builtin" }
                            )
                        }
                        option4 = @{ type = "str"; aliases = "alias4"; deprecated_aliases = @(@{name = "alias4"; date = [DateTime]"2020-03-11" }) }
                        option5 = @{ type = "str"; aliases = "alias5"; deprecated_aliases = @(@{name = "alias5"; date = [DateTime]"2020-03-09" }) }
                        option6 = @{
                            type = "str"
                            aliases = "alias6"
                            deprecated_aliases = @(
                                @{name = "alias6"; date = [DateTime]"2020-06-01"; collection_name = "ansible.builtin" }
                            )
                        }
                    }
                }
                option4 = @{ type = "str"; aliases = "alias4"; deprecated_aliases = @(@{name = "alias4"; date = [DateTime]"2020-03-10" }) }
                option5 = @{ type = "str"; aliases = "alias5"; deprecated_aliases = @(@{name = "alias5"; date = [DateTime]"2020-03-12" }) }
                option6 = @{
                    type = "str"
                    aliases = "alias6"
                    deprecated_aliases = @(
                        @{name = "alias6"; version = "2.12"; collection_name = "ansible.builtin" }
                    )
                }
                option7 = @{
                    type = "str"
                    aliases = "alias7"
                    deprecated_aliases = @(
                        @{name = "alias7"; date = [DateTime]"2020-06-07"; collection_name = "ansible.builtin" }
                    )
                }
            }
        }

        Set-Variable -Name complex_args -Scope Global -Value @{
            alias1 = "alias1"
            option2 = "option2"
            option3 = @{
                option1 = "option1"
                alias2 = "alias2"
                alias3 = "alias3"
                option4 = "option4"
                alias5 = "alias5"
                alias6 = "alias6"
            }
            option4 = "option4"
            alias5 = "alias5"
            alias6 = "alias6"
            alias7 = "alias7"
        }

        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        $failed = $false
        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected = @{
            changed = $false
            invocation = @{
                module_args = @{
                    alias1 = "alias1"
                    option1 = "alias1"
                    option2 = "option2"
                    option3 = @{
                        option1 = "option1"
                        option2 = "alias2"
                        alias2 = "alias2"
                        option3 = "alias3"
                        alias3 = "alias3"
                        option4 = "option4"
                        option5 = "alias5"
                        alias5 = "alias5"
                        option6 = "alias6"
                        alias6 = "alias6"
                    }
                    option4 = "option4"
                    option5 = "alias5"
                    alias5 = "alias5"
                    option6 = "alias6"
                    alias6 = "alias6"
                    option7 = "alias7"
                    alias7 = "alias7"
                }
            }
            deprecations = @(
                @{
                    msg = "Alias 'alias7' is deprecated. See the module docs for more information"
                    date = "2020-06-07"
                    collection_name = "ansible.builtin"
                },
                @{
                    msg = "Alias 'alias1' is deprecated. See the module docs for more information"
                    version = "2.10"
                    collection_name = $null
                },
                @{
                    msg = "Alias 'alias5' is deprecated. See the module docs for more information"
                    date = "2020-03-12"
                    collection_name = $null
                },
                @{
                    msg = "Alias 'alias6' is deprecated. See the module docs for more information"
                    version = "2.12"
                    collection_name = "ansible.builtin"
                },
                @{
                    msg = "Alias 'alias2' is deprecated. See the module docs for more information - found in option3"
                    version = "2.11"
                    collection_name = $null
                },
                @{
                    msg = "Alias 'alias5' is deprecated. See the module docs for more information - found in option3"
                    date = "2020-03-09"
                    collection_name = $null
                },
                @{
                    msg = "Alias 'alias3' is deprecated. See the module docs for more information - found in option3"
                    version = "2.12"
                    collection_name = "ansible.builtin"
                },
                @{
                    msg = "Alias 'alias6' is deprecated. See the module docs for more information - found in option3"
                    date = "2020-06-01"
                    collection_name = "ansible.builtin"
                }
            )
        }
        $actual | Assert-DictionaryEqual -Expected $expected
    }

    "Required by - single value" = {
        $spec = @{
            options = @{
                option1 = @{type = "str" }
                option2 = @{type = "str" }
                option3 = @{type = "str" }
            }
            required_by = @{
                option1 = "option2"
            }
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            option1 = "option1"
            option2 = "option2"
        }

        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)

        $failed = $false
        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected = @{
            changed = $false
            invocation = @{
                module_args = @{
                    option1 = "option1"
                    option2 = "option2"
                    option3 = $null
                }
            }
        }
        $actual | Assert-DictionaryEqual -Expected $expected
    }

    "Required by - multiple values" = {
        $spec = @{
            options = @{
                option1 = @{type = "str" }
                option2 = @{type = "str" }
                option3 = @{type = "str" }
            }
            required_by = @{
                option1 = "option2", "option3"
            }
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            option1 = "option1"
            option2 = "option2"
            option3 = "option3"
        }

        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)

        $failed = $false
        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected = @{
            changed = $false
            invocation = @{
                module_args = @{
                    option1 = "option1"
                    option2 = "option2"
                    option3 = "option3"
                }
            }
        }
        $actual | Assert-DictionaryEqual -Expected $expected
    }

    "Required by explicit null" = {
        $spec = @{
            options = @{
                option1 = @{type = "str" }
                option2 = @{type = "str" }
                option3 = @{type = "str" }
            }
            required_by = @{
                option1 = "option2"
            }
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            option1 = "option1"
            option2 = $null
        }

        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)

        $failed = $false
        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected = @{
            changed = $false
            invocation = @{
                module_args = @{
                    option1 = "option1"
                    option2 = $null
                    option3 = $null
                }
            }
        }
        $actual | Assert-DictionaryEqual -Expected $expected
    }

    "Required by failed - single value" = {
        $spec = @{
            options = @{
                option1 = @{type = "str" }
                option2 = @{type = "str" }
                option3 = @{type = "str" }
            }
            required_by = @{
                option1 = "option2"
            }
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            option1 = "option1"
        }

        $failed = $false
        try {
            $null = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected = @{
            changed = $false
            failed = $true
            invocation = @{
                module_args = @{
                    option1 = "option1"
                }
            }
            msg = "missing parameter(s) required by 'option1': option2"
        }
        $actual | Assert-DictionaryEqual -Expected $expected
    }

    "Required by failed - multiple values" = {
        $spec = @{
            options = @{
                option1 = @{type = "str" }
                option2 = @{type = "str" }
                option3 = @{type = "str" }
            }
            required_by = @{
                option1 = "option2", "option3"
            }
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            option1 = "option1"
        }

        $failed = $false
        try {
            $null = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected = @{
            changed = $false
            failed = $true
            invocation = @{
                module_args = @{
                    option1 = "option1"
                }
            }
            msg = "missing parameter(s) required by 'option1': option2, option3"
        }
        $actual | Assert-DictionaryEqual -Expected $expected
    }

    "Debug without debug set" = {
        Set-Variable -Name complex_args -Scope Global -Value @{
            _ansible_debug = $false
        }
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})
        $m.Debug("debug message")
        $actual_event = (Get-EventLog -LogName Application -Source Ansible -Newest 1).Message
        $actual_event | Assert-Equal -Expected "undefined win module - Invoked with:`r`n  "
    }

    "Debug with debug set" = {
        Set-Variable -Name complex_args -Scope Global -Value @{
            _ansible_debug = $true
        }
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})
        $m.Debug("debug message")
        $actual_event = (Get-EventLog -LogName Application -Source Ansible -Newest 1).Message
        $actual_event | Assert-Equal -Expected "undefined win module - [DEBUG] debug message"
    }

    "Deprecate and warn with version" = {
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})
        $m.Deprecate("message", "2.7")
        $actual_deprecate_event_1 = Get-EventLog -LogName Application -Source Ansible -Newest 1
        $m.Deprecate("message w collection", "2.8", "ansible.builtin")
        $actual_deprecate_event_2 = Get-EventLog -LogName Application -Source Ansible -Newest 1
        $m.Warn("warning")
        $actual_warn_event = Get-EventLog -LogName Application -Source Ansible -Newest 1

        $actual_deprecate_event_1.Message | Assert-Equal -Expected "undefined win module - [DEPRECATION WARNING] message 2.7"
        $actual_deprecate_event_2.Message | Assert-Equal -Expected "undefined win module - [DEPRECATION WARNING] message w collection 2.8"
        $actual_warn_event.EntryType | Assert-Equal -Expected "Warning"
        $actual_warn_event.Message | Assert-Equal -Expected "undefined win module - [WARNING] warning"

        $failed = $false
        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected = @{
            changed = $false
            invocation = @{
                module_args = @{}
            }
            warnings = @("warning")
            deprecations = @(
                @{msg = "message"; version = "2.7"; collection_name = $null },
                @{msg = "message w collection"; version = "2.8"; collection_name = "ansible.builtin" }
            )
        }
        $actual | Assert-DictionaryEqual -Expected $expected
    }

    "Deprecate and warn with date" = {
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})
        $m.Deprecate("message", [DateTime]"2020-01-01")
        $actual_deprecate_event_1 = Get-EventLog -LogName Application -Source Ansible -Newest 1
        $m.Deprecate("message w collection", [DateTime]"2020-01-02", "ansible.builtin")
        $actual_deprecate_event_2 = Get-EventLog -LogName Application -Source Ansible -Newest 1
        $m.Warn("warning")
        $actual_warn_event = Get-EventLog -LogName Application -Source Ansible -Newest 1

        $actual_deprecate_event_1.Message | Assert-Equal -Expected "undefined win module - [DEPRECATION WARNING] message 2020-01-01"
        $actual_deprecate_event_2.Message | Assert-Equal -Expected "undefined win module - [DEPRECATION WARNING] message w collection 2020-01-02"
        $actual_warn_event.EntryType | Assert-Equal -Expected "Warning"
        $actual_warn_event.Message | Assert-Equal -Expected "undefined win module - [WARNING] warning"

        $failed = $false
        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected = @{
            changed = $false
            invocation = @{
                module_args = @{}
            }
            warnings = @("warning")
            deprecations = @(
                @{msg = "message"; date = "2020-01-01"; collection_name = $null },
                @{msg = "message w collection"; date = "2020-01-02"; collection_name = "ansible.builtin" }
            )
        }
        $actual | Assert-DictionaryEqual -Expected $expected
    }

    "Run with exec wrapper warnings" = {
        [Ansible.Basic.AnsibleModule]::_WrapperWarnings = [System.Collections.Generic.List[string]]@('Warning 1', 'Warning 2')
        try {
            $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})
            $m.Warn("Warning 3")

            $failed = $false
            try {
                $m.ExitJson()
            }
            catch [System.Management.Automation.RuntimeException] {
                $failed = $true
                $_.Exception.Message | Assert-Equal -Expected "exit: 0"
                $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
            }
            $failed | Assert-Equal -Expected $true
        }
        finally {
            [Ansible.Basic.AnsibleModule]::_WrapperWarnings = $null
        }

        $expected = @{
            changed = $false
            invocation = @{
                module_args = @{}
            }
            warnings = @("Warning 3", "Warning 1", "Warning 2")
        }
        $actual | Assert-DictionaryEqual -Expected $expected
    }

    "FailJson with message" = {
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})

        $failed = $false
        try {
            $m.FailJson("fail message")
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $failed

        $expected = @{
            changed = $false
            invocation = @{
                module_args = @{}
            }
            failed = $true
            msg = "fail message"
        }
        $actual | Assert-DictionaryEqual -Expected $expected
    }

    "FailJson with Exception" = {
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})

        try {
            [System.IO.Path]::GetFullPath($null)
        }
        catch {
            $excp = $_.Exception
        }

        $failed = $false
        try {
            $m.FailJson("fail message", $excp)
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $failed

        $expected = @{
            changed = $false
            invocation = @{
                module_args = @{}
            }
            failed = $true
            msg = "fail message"
        }
        $actual | Assert-DictionaryEqual -Expected $expected
    }

    "FailJson with ErrorRecord" = {
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})

        try {
            Get-Item -LiteralPath $null
        }
        catch {
            $error_record = $_
        }

        $failed = $false
        try {
            $m.FailJson("fail message", $error_record)
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $failed

        $expected = @{
            changed = $false
            invocation = @{
                module_args = @{}
            }
            failed = $true
            msg = "fail message"
        }
        $actual | Assert-DictionaryEqual -Expected $expected
    }

    "FailJson with Exception and verbosity 3" = {
        Set-Variable -Name complex_args -Scope Global -Value @{
            _ansible_verbosity = 3
        }
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})

        try {
            [System.IO.Path]::GetFullPath($null)
        }
        catch {
            $excp = $_.Exception
        }

        $failed = $false
        try {
            $m.FailJson("fail message", $excp)
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $failed

        $actual.changed | Assert-Equal -Expected $false
        $actual.invocation | Assert-DictionaryEqual -Expected @{module_args = @{} }
        $actual.failed | Assert-Equal -Expected $true
        $actual.msg | Assert-Equal -Expected "fail message"
        $expected = 'System.Management.Automation.MethodInvocationException: Exception calling "GetFullPath" with "1" argument(s)'
        $actual.exception.Contains($expected) | Assert-Equal -Expected $true
    }

    "FailJson with ErrorRecord and verbosity 3" = {
        Set-Variable -Name complex_args -Scope Global -Value @{
            _ansible_verbosity = 3
        }
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})

        try {
            Get-Item -LiteralPath $null
        }
        catch {
            $error_record = $_
        }

        $failed = $false
        try {
            $m.FailJson("fail message", $error_record)
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $failed

        $actual.changed | Assert-Equal -Expected $false
        $actual.invocation | Assert-DictionaryEqual -Expected @{module_args = @{} }
        $actual.failed | Assert-Equal -Expected $true
        $actual.msg | Assert-Equal -Expected "fail message"
        $actual.exception.Contains("Cannot bind argument to parameter 'LiteralPath' because it is null") | Assert-Equal -Expected $true
        $actual.exception.Contains("+             Get-Item -LiteralPath `$null") | Assert-Equal -Expected $true
        $actual.exception.Contains("ScriptStackTrace:") | Assert-Equal -Expected $true
    }

    "Diff entry without diff set" = {
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})
        $m.Diff.before = @{a = "a" }
        $m.Diff.after = @{b = "b" }

        $failed = $false
        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $failed

        $expected = @{
            changed = $false
            invocation = @{
                module_args = @{}
            }
        }
        $actual | Assert-DictionaryEqual -Expected $expected
    }

    "Diff entry with diff set" = {
        Set-Variable -Name complex_args -Scope Global -Value @{
            _ansible_diff = $true
        }
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})
        $m.Diff.before = @{a = "a" }
        $m.Diff.after = @{b = "b" }

        $failed = $false
        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $failed

        $expected = @{
            changed = $false
            invocation = @{
                module_args = @{}
            }
            diff = @{
                before = @{a = "a" }
                after = @{b = "b" }
            }
        }
        $actual | Assert-DictionaryEqual -Expected $expected
    }

    "ParseBool tests" = {
        $mapping = New-Object -TypeName 'System.Collections.Generic.Dictionary`2[[Object], [Bool]]'
        $mapping.Add("y", $true)
        $mapping.Add("Y", $true)
        $mapping.Add("yes", $true)
        $mapping.Add("Yes", $true)
        $mapping.Add("on", $true)
        $mapping.Add("On", $true)
        $mapping.Add("1", $true)
        $mapping.Add(1, $true)
        $mapping.Add("true", $true)
        $mapping.Add("True", $true)
        $mapping.Add("t", $true)
        $mapping.Add("T", $true)
        $mapping.Add("1.0", $true)
        $mapping.Add(1.0, $true)
        $mapping.Add($true, $true)
        $mapping.Add("n", $false)
        $mapping.Add("N", $false)
        $mapping.Add("no", $false)
        $mapping.Add("No", $false)
        $mapping.Add("off", $false)
        $mapping.Add("Off", $false)
        $mapping.Add("0", $false)
        $mapping.Add(0, $false)
        $mapping.Add("false", $false)
        $mapping.Add("False", $false)
        $mapping.Add("f", $false)
        $mapping.Add("F", $false)
        $mapping.Add("0.0", $false)
        $mapping.Add(0.0, $false)
        $mapping.Add($false, $false)

        foreach ($map in $mapping.GetEnumerator()) {
            $expected = $map.Value
            $actual = [Ansible.Basic.AnsibleModule]::ParseBool($map.Key)
            $actual | Assert-Equal -Expected $expected
            $actual.GetType().FullName | Assert-Equal -Expected "System.Boolean"
        }

        $fail_bools = @(
            "falsey",
            "abc",
            2,
            "2",
            -1
        )
        foreach ($fail_bool in $fail_bools) {
            $failed = $false
            try {
                [Ansible.Basic.AnsibleModule]::ParseBool($fail_bool)
            }
            catch {
                $failed = $true
                $_.Exception.Message.Contains("The value '$fail_bool' is not a valid boolean") | Assert-Equal -Expected $true
            }
            $failed | Assert-Equal -Expected $true
        }
    }

    "Unknown internal key" = {
        Set-Variable -Name complex_args -Scope Global -Value @{
            _ansible_invalid = "invalid"
        }
        $failed = $false
        try {
            $null = [Ansible.Basic.AnsibleModule]::Create(@(), @{})
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"

            $expected = @{
                invocation = @{
                    module_args = @{
                        _ansible_invalid = "invalid"
                    }
                }
                changed = $false
                failed = $true
                msg = "Unsupported parameters for (undefined win module) module: _ansible_invalid. Supported parameters include: "
            }
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
            $actual | Assert-DictionaryEqual -Expected $expected
        }
        $failed | Assert-Equal -Expected $true
    }

    "Module tmpdir with present remote tmp" = {
        $current_user = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
        $dir_security = New-Object -TypeName System.Security.AccessControl.DirectorySecurity
        $dir_security.SetOwner($current_user)
        $dir_security.SetAccessRuleProtection($true, $false)
        $ace = New-Object -TypeName System.Security.AccessControl.FileSystemAccessRule -ArgumentList @(
            $current_user, [System.Security.AccessControl.FileSystemRights]::FullControl,
            [System.Security.AccessControl.InheritanceFlags]"ContainerInherit, ObjectInherit",
            [System.Security.AccessControl.PropagationFlags]::None, [System.Security.AccessControl.AccessControlType]::Allow
        )
        $dir_security.AddAccessRule($ace)
        $expected_sd = $dir_security.GetSecurityDescriptorSddlForm("Access, Owner")

        $remote_tmp = Join-Path -Path $tmpdir -ChildPath "moduletmpdir-$(Get-Random)"
        New-Item -Path $remote_tmp -ItemType Directory > $null
        Set-Variable -Name complex_args -Scope Global -Value @{
            _ansible_remote_tmp = $remote_tmp.ToString()
        }
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})
        (Test-Path -LiteralPath $remote_tmp -PathType Container) | Assert-Equal -Expected $true

        $actual_tmpdir = $m.Tmpdir
        $parent_tmpdir = Split-Path -Path $actual_tmpdir -Parent
        $tmpdir_name = Split-Path -Path $actual_tmpdir -Leaf

        $parent_tmpdir | Assert-Equal -Expected $remote_tmp
        $tmpdir_name.StartSwith("ansible-moduletmp-") | Assert-Equal -Expected $true
        (Test-Path -LiteralPath $actual_tmpdir -PathType Container) | Assert-Equal -Expected $true
        (Test-Path -LiteralPath $remote_tmp -PathType Container) | Assert-Equal -Expected $true
        $children = [System.IO.Directory]::EnumerateDirectories($remote_tmp)
        $children.Count | Assert-Equal -Expected 1
        $actual_tmpdir_sd = (Get-Acl -Path $actual_tmpdir).GetSecurityDescriptorSddlForm("Access, Owner")
        $actual_tmpdir_sd | Assert-Equal -Expected $expected_sd

        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $output = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        (Test-Path -LiteralPath $actual_tmpdir -PathType Container) | Assert-Equal -Expected $false
        (Test-Path -LiteralPath $remote_tmp -PathType Container) | Assert-Equal -Expected $true
        $output.warnings.Count | Assert-Equal -Expected 0
    }

    "Module tmpdir with missing remote_tmp" = {
        $current_user = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
        $dir_security = New-Object -TypeName System.Security.AccessControl.DirectorySecurity
        $dir_security.SetOwner($current_user)
        $dir_security.SetAccessRuleProtection($true, $false)
        $ace = New-Object -TypeName System.Security.AccessControl.FileSystemAccessRule -ArgumentList @(
            $current_user, [System.Security.AccessControl.FileSystemRights]::FullControl,
            [System.Security.AccessControl.InheritanceFlags]"ContainerInherit, ObjectInherit",
            [System.Security.AccessControl.PropagationFlags]::None, [System.Security.AccessControl.AccessControlType]::Allow
        )
        $dir_security.AddAccessRule($ace)
        $expected_sd = $dir_security.GetSecurityDescriptorSddlForm("Access, Owner")

        $remote_tmp = Join-Path -Path $tmpdir -ChildPath "moduletmpdir-$(Get-Random)"
        Set-Variable -Name complex_args -Scope Global -Value @{
            _ansible_remote_tmp = $remote_tmp.ToString()
        }
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})
        (Test-Path -LiteralPath $remote_tmp -PathType Container) | Assert-Equal -Expected $false

        $actual_tmpdir = $m.Tmpdir
        $parent_tmpdir = Split-Path -Path $actual_tmpdir -Parent
        $tmpdir_name = Split-Path -Path $actual_tmpdir -Leaf

        $parent_tmpdir | Assert-Equal -Expected $remote_tmp
        $tmpdir_name.StartSwith("ansible-moduletmp-") | Assert-Equal -Expected $true
        (Test-Path -LiteralPath $actual_tmpdir -PathType Container) | Assert-Equal -Expected $true
        (Test-Path -LiteralPath $remote_tmp -PathType Container) | Assert-Equal -Expected $true
        $children = [System.IO.Directory]::EnumerateDirectories($remote_tmp)
        $children.Count | Assert-Equal -Expected 1
        $actual_remote_sd = (Get-Acl -Path $remote_tmp).GetSecurityDescriptorSddlForm("Access, Owner")
        $actual_tmpdir_sd = (Get-Acl -Path $actual_tmpdir).GetSecurityDescriptorSddlForm("Access, Owner")
        $actual_remote_sd | Assert-Equal -Expected $expected_sd
        $actual_tmpdir_sd | Assert-Equal -Expected $expected_sd

        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $output = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        (Test-Path -LiteralPath $actual_tmpdir -PathType Container) | Assert-Equal -Expected $false
        (Test-Path -LiteralPath $remote_tmp -PathType Container) | Assert-Equal -Expected $true
        $output.warnings.Count | Assert-Equal -Expected 1
        $nt_account = $current_user.Translate([System.Security.Principal.NTAccount])
        $actual_warning = "Module remote_tmp $remote_tmp did not exist and was created with FullControl to $nt_account, "
        $actual_warning += "this may cause issues when running as another user. To avoid this, "
        $actual_warning += "create the remote_tmp dir with the correct permissions manually"
        $actual_warning | Assert-Equal -Expected $output.warnings[0]
    }

    "Module tmp, keep remote files" = {
        $remote_tmp = Join-Path -Path $tmpdir -ChildPath "moduletmpdir-$(Get-Random)"
        New-Item -Path $remote_tmp -ItemType Directory > $null
        Set-Variable -Name complex_args -Scope Global -Value @{
            _ansible_remote_tmp = $remote_tmp.ToString()
            _ansible_keep_remote_files = $true
        }
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})

        $actual_tmpdir = $m.Tmpdir
        $parent_tmpdir = Split-Path -Path $actual_tmpdir -Parent
        $tmpdir_name = Split-Path -Path $actual_tmpdir -Leaf

        $parent_tmpdir | Assert-Equal -Expected $remote_tmp
        $tmpdir_name.StartSwith("ansible-moduletmp-") | Assert-Equal -Expected $true
        (Test-Path -LiteralPath $actual_tmpdir -PathType Container) | Assert-Equal -Expected $true
        (Test-Path -LiteralPath $remote_tmp -PathType Container) | Assert-Equal -Expected $true

        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $output = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        (Test-Path -LiteralPath $actual_tmpdir -PathType Container) | Assert-Equal -Expected $true
        (Test-Path -LiteralPath $remote_tmp -PathType Container) | Assert-Equal -Expected $true
        $output.warnings.Count | Assert-Equal -Expected 0
        Remove-Item -LiteralPath $actual_tmpdir -Force -Recurse
    }

    "Module tmpdir with symlinks" = {
        $remote_tmp = Join-Path -Path $tmpdir -ChildPath "moduletmpdir-$(Get-Random)"
        New-Item -Path $remote_tmp -ItemType Directory > $null
        Set-Variable -Name complex_args -Scope Global -Value @{
            _ansible_remote_tmp = $remote_tmp.ToString()
        }
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})

        $actual_tmpdir = $m.Tmpdir

        $dir1 = Join-Path $actual_tmpdir Dir1
        $dir2 = Join-Path $actual_tmpdir Dir2
        $dir1, $dir2 | New-Item -Path { $_ } -ItemType Directory > $null

        $file1 = Join-Path $dir1 test.txt
        $file2 = Join-Path $dir2 test.txt
        $file3 = Join-Path $actual_tmpdir test.txt
        Set-Content -LiteralPath $file1 ''
        Set-Content -LiteralPath $file2 ''
        Set-Content -LiteralPath $file3 ''

        $outside_target = Join-Path -Path $tmpdir -ChildPath "moduleoutsidedir-$(Get-Random)"
        $outside_file = Join-Path -Path $outside_target -ChildPath "file"
        New-Item -Path $outside_target -ItemType Directory > $null
        Set-Content -LiteralPath $outside_file ''

        cmd.exe /c mklink /d "$dir1\missing-dir-link" "$actual_tmpdir\fake"
        cmd.exe /c mklink /d "$dir1\good-dir-link" "$dir2"
        cmd.exe /c mklink /d "$dir1\recursive-target-link" "$dir1"
        cmd.exe /c mklink "$dir1\missing-file-link" "$actual_tmpdir\fake"
        cmd.exe /c mklink "$dir1\good-file-link" "$dir2\test.txt"
        cmd.exe /c mklink /d "$actual_tmpdir\outside-dir" $outside_target
        cmd.exe /c mklink "$actual_tmpdir\outside-file" $outside_file

        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $output = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }

        $output.warnings.Count | Assert-Equal -Expected 0
        (Test-Path -LiteralPath $actual_tmpdir -PathType Container) | Assert-Equal -Expected $false
        (Test-Path -LiteralPath $outside_target -PathType Container) | Assert-Equal -Expected $true
        (Test-Path -LiteralPath $outside_file -PathType Leaf) | Assert-Equal -Expected $true

        Remove-Item -LiteralPath $remote_tmp -Force -Recurse
    }

    "Module tmpdir with undeletable file" = {
        $remote_tmp = Join-Path -Path $tmpdir -ChildPath "moduletmpdir-$(Get-Random)"
        New-Item -Path $remote_tmp -ItemType Directory > $null
        Set-Variable -Name complex_args -Scope Global -Value @{
            _ansible_remote_tmp = $remote_tmp.ToString()
        }
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})

        $actual_tmpdir = $m.Tmpdir

        $dir1 = Join-Path $actual_tmpdir Dir1
        $dir2 = Join-Path $actual_tmpdir Dir2
        $dir1, $dir2 | New-Item -Path { $_ } -ItemType Directory > $null

        $file1 = Join-Path $dir1 test.txt
        $file2 = Join-Path $dir2 test.txt
        $file3 = Join-Path $actual_tmpdir test.txt
        Set-Content -LiteralPath $file1 ''
        Set-Content -LiteralPath $file2 ''
        Set-Content -LiteralPath $file3 ''

        $fs = [System.IO.File]::Open($file1, "Open", "Read", "None")
        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $output = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }

        $expected_msg = "Failure cleaning temp path '$actual_tmpdir': IOException Directory contains files still open by other processes"
        $output.warnings.Count | Assert-Equal -Expected 1
        $output.warnings[0] | Assert-Equal -Expected $expected_msg

        (Test-Path -LiteralPath $actual_tmpdir -PathType Container) | Assert-Equal -Expected $true
        (Test-Path -LiteralPath $dir1 -PathType Container) | Assert-Equal -Expected $true
        # Test-Path tries to open the file in a way that fails if it's marked as deleted
        (Get-ChildItem -LiteralPath $dir1 -File).Count | Assert-Equal -Expected 1
        (Test-Path -LiteralPath $dir2 -PathType Container) | Assert-Equal -Expected $false
        (Test-Path -LiteralPath $file3 -PathType Leaf) | Assert-Equal -Expected $false

        # Releasing the file handle releases the lock on the file but as the
        # cleanup couldn't access the file to mark as delete on close it is
        # still going to be present.
        $fs.Dispose()
        (Test-Path -LiteralPath $dir1 -PathType Container) | Assert-Equal -Expected $true
        (Test-Path -LiteralPath $file1 -PathType Leaf) | Assert-Equal -Expected $true

        Remove-Item -LiteralPath $remote_tmp -Force -Recurse
    }

    "Module tmpdir delete with locked handle" = {
        $remote_tmp = Join-Path -Path $tmpdir -ChildPath "moduletmpdir-$(Get-Random)"
        New-Item -Path $remote_tmp -ItemType Directory > $null
        Set-Variable -Name complex_args -Scope Global -Value @{
            _ansible_remote_tmp = $remote_tmp.ToString()
        }
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})

        $actual_tmpdir = $m.Tmpdir

        $dir1 = Join-Path $actual_tmpdir Dir1
        $dir2 = Join-Path $actual_tmpdir Dir2
        $dir1, $dir2 | New-Item -Path { $_ } -ItemType Directory > $null

        $file1 = Join-Path $dir1 test.txt
        $file2 = Join-Path $dir2 test.txt
        $file3 = Join-Path $actual_tmpdir test.txt
        Set-Content -LiteralPath $file1 ''
        Set-Content -LiteralPath $file2 ''
        Set-Content -LiteralPath $file3 ''

        [System.IO.File]::SetAttributes($file1, "ReadOnly")
        [System.IO.File]::SetAttributes($file2, "ReadOnly")
        [System.IO.File]::SetAttributes($file3, "ReadOnly")
        $fs = [System.IO.File]::Open($file1, "Open", "Read", "Delete")
        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $output = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }

        if ([System.Environment]::OSVersion.Version -lt [Version]'10.0') {
            # Older hosts can only do delete on close. This means Dir1 and its
            # file will still be present but Dir2 should be deleted.
            $expected_msg = "Failure cleaning temp path '$actual_tmpdir': IOException Directory contains files still open by other processes"
            $output.warnings.Count | Assert-Equal -Expected 1
            $output.warnings[0] | Assert-Equal -Expected $expected_msg

            (Test-Path -LiteralPath $actual_tmpdir -PathType Container) | Assert-Equal -Expected $true
            (Test-Path -LiteralPath $dir1 -PathType Container) | Assert-Equal -Expected $true
            # Test-Path tries to open the file in a way that fails if it's marked as deleted
            (Get-ChildItem -LiteralPath $dir1 -File).Count | Assert-Equal -Expected 1
            (Test-Path -LiteralPath $dir2 -PathType Container) | Assert-Equal -Expected $false
            (Test-Path -LiteralPath $file3 -PathType Leaf) | Assert-Equal -Expected $false

            # Releasing the file handle releases the lock on the file deleting
            # it. Unfortunately the parent dir will still be present
            $fs.Dispose()
            (Test-Path -LiteralPath $dir1 -PathType Container) | Assert-Equal -Expected $true
            (Test-Path -LiteralPath $file1 -PathType Leaf) | Assert-Equal -Expected $false
        }
        else {
            # Server 2016+ can use the POSIX APIs which will delete it straight away
            (Test-Path -LiteralPath $actual_tmpdir -PathType Container) | Assert-Equal -Expected $false
            $output.warnings.Count | Assert-Equal -Expected 0

            $fs.Dispose()
        }

        Remove-Item -LiteralPath $remote_tmp -Force -Recurse
    }

    "Invalid argument spec key" = {
        $spec = @{
            invalid = $true
        }
        $failed = $false
        try {
            $null = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected_msg = "internal error: argument spec entry contains an invalid key 'invalid', valid keys: apply_defaults, "
        $expected_msg += "aliases, choices, default, deprecated_aliases, elements, mutually_exclusive, no_log, options, "
        $expected_msg += "removed_in_version, removed_at_date, removed_from_collection, required, required_by, required_if, "
        $expected_msg += "required_one_of, required_together, supports_check_mode, type"

        $actual.Keys.Count | Assert-Equal -Expected 3
        $actual.failed | Assert-Equal -Expected $true
        $actual.msg | Assert-Equal -Expected $expected_msg
        ("exception" -cin $actual.Keys) | Assert-Equal -Expected $true
    }

    "Invalid argument spec key - nested" = {
        $spec = @{
            options = @{
                option_key = @{
                    options = @{
                        sub_option_key = @{
                            invalid = $true
                        }
                    }
                }
            }
        }
        $failed = $false
        try {
            $null = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected_msg = "internal error: argument spec entry contains an invalid key 'invalid', valid keys: apply_defaults, "
        $expected_msg += "aliases, choices, default, deprecated_aliases, elements, mutually_exclusive, no_log, options, "
        $expected_msg += "removed_in_version, removed_at_date, removed_from_collection, required, required_by, required_if, "
        $expected_msg += "required_one_of, required_together, supports_check_mode, type - found in option_key -> sub_option_key"

        $actual.Keys.Count | Assert-Equal -Expected 3
        $actual.failed | Assert-Equal -Expected $true
        $actual.msg | Assert-Equal -Expected $expected_msg
        ("exception" -cin $actual.Keys) | Assert-Equal -Expected $true
    }

    "Invalid argument spec value type" = {
        $spec = @{
            apply_defaults = "abc"
        }
        $failed = $false
        try {
            $null = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected_msg = "internal error: argument spec for 'apply_defaults' did not match expected "
        $expected_msg += "type System.Boolean: actual type System.String"

        $actual.Keys.Count | Assert-Equal -Expected 3
        $actual.failed | Assert-Equal -Expected $true
        $actual.msg | Assert-Equal -Expected $expected_msg
        ("exception" -cin $actual.Keys) | Assert-Equal -Expected $true
    }

    "Invalid argument spec option type" = {
        $spec = @{
            options = @{
                option_key = @{
                    type = "invalid type"
                }
            }
        }
        $failed = $false
        try {
            $null = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected_msg = "internal error: type 'invalid type' is unsupported - found in option_key. "
        $expected_msg += "Valid types are: bool, dict, float, int, json, list, path, raw, sid, str"

        $actual.Keys.Count | Assert-Equal -Expected 3
        $actual.failed | Assert-Equal -Expected $true
        $actual.msg | Assert-Equal -Expected $expected_msg
        ("exception" -cin $actual.Keys) | Assert-Equal -Expected $true
    }

    "Invalid argument spec option element type" = {
        $spec = @{
            options = @{
                option_key = @{
                    type = "list"
                    elements = "invalid type"
                }
            }
        }
        $failed = $false
        try {
            $null = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected_msg = "internal error: elements 'invalid type' is unsupported - found in option_key. "
        $expected_msg += "Valid types are: bool, dict, float, int, json, list, path, raw, sid, str"

        $actual.Keys.Count | Assert-Equal -Expected 3
        $actual.failed | Assert-Equal -Expected $true
        $actual.msg | Assert-Equal -Expected $expected_msg
        ("exception" -cin $actual.Keys) | Assert-Equal -Expected $true
    }

    "Invalid deprecated aliases entry - no version and date" = {
        $spec = @{
            options = @{
                option_key = @{
                    type = "str"
                    aliases = , "alias_name"
                    deprecated_aliases = @(
                        @{name = "alias_name" }
                    )
                }
            }
        }

        $failed = $false
        try {
            $null = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected_msg = "internal error: One of version or date is required in a deprecated_aliases entry"

        $actual.Keys.Count | Assert-Equal -Expected 3
        $actual.failed | Assert-Equal -Expected $true
        $actual.msg | Assert-Equal -Expected $expected_msg
        ("exception" -cin $actual.Keys) | Assert-Equal -Expected $true
    }

    "Invalid deprecated aliases entry - no name (nested)" = {
        $spec = @{
            options = @{
                option_key = @{
                    type = "dict"
                    options = @{
                        sub_option_key = @{
                            type = "str"
                            aliases = , "alias_name"
                            deprecated_aliases = @(
                                @{version = "2.10" }
                            )
                        }
                    }
                }
            }
        }

        Set-Variable -Name complex_args -Scope Global -Value @{
            option_key = @{
                sub_option_key = "a"
            }
        }

        $failed = $false
        try {
            $null = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        }
        catch [System.ArgumentException] {
            $failed = $true
            $expected_msg = "name is required in a deprecated_aliases entry - found in option_key"
            $_.Exception.Message | Assert-Equal -Expected $expected_msg
        }
        $failed | Assert-Equal -Expected $true
    }

    "Invalid deprecated aliases entry - both version and date" = {
        $spec = @{
            options = @{
                option_key = @{
                    type = "str"
                    aliases = , "alias_name"
                    deprecated_aliases = @(
                        @{
                            name = "alias_name"
                            date = [DateTime]"2020-03-10"
                            version = "2.11"
                        }
                    )
                }
            }
        }

        $failed = $false
        try {
            $null = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected_msg = "internal error: Only one of version or date is allowed in a deprecated_aliases entry"

        $actual.Keys.Count | Assert-Equal -Expected 3
        $actual.failed | Assert-Equal -Expected $true
        $actual.msg | Assert-Equal -Expected $expected_msg
        ("exception" -cin $actual.Keys) | Assert-Equal -Expected $true
    }

    "Invalid deprecated aliases entry - wrong date type" = {
        $spec = @{
            options = @{
                option_key = @{
                    type = "str"
                    aliases = , "alias_name"
                    deprecated_aliases = @(
                        @{
                            name = "alias_name"
                            date = "2020-03-10"
                        }
                    )
                }
            }
        }

        $failed = $false
        try {
            $null = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected_msg = "internal error: A deprecated_aliases date must be a DateTime object"

        $actual.Keys.Count | Assert-Equal -Expected 3
        $actual.failed | Assert-Equal -Expected $true
        $actual.msg | Assert-Equal -Expected $expected_msg
        ("exception" -cin $actual.Keys) | Assert-Equal -Expected $true
    }

    "Spec required and default set at the same time" = {
        $spec = @{
            options = @{
                option_key = @{
                    required = $true
                    default = "default value"
                }
            }
        }

        $failed = $false
        try {
            $null = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected_msg = "internal error: required and default are mutually exclusive for option_key"

        $actual.Keys.Count | Assert-Equal -Expected 3
        $actual.failed | Assert-Equal -Expected $true
        $actual.msg | Assert-Equal -Expected $expected_msg
        ("exception" -cin $actual.Keys) | Assert-Equal -Expected $true
    }

    "Unsupported options" = {
        $spec = @{
            options = @{
                option_key = @{
                    type = "str"
                }
            }
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            option_key = "abc"
            invalid_key = "def"
            another_key = "ghi"
        }

        $failed = $false
        try {
            $null = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected_msg = "Unsupported parameters for (undefined win module) module: another_key, invalid_key. "
        $expected_msg += "Supported parameters include: option_key"

        $actual.Keys.Count | Assert-Equal -Expected 4
        $actual.changed | Assert-Equal -Expected $false
        $actual.failed | Assert-Equal -Expected $true
        $actual.msg | Assert-Equal -Expected $expected_msg
        $actual.invocation | Assert-DictionaryEqual -Expected @{module_args = $complex_args }
    }

    "Unsupported options with ignore" = {
        $spec = @{
            options = @{
                option_key = @{
                    type = "str"
                }
            }
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            option_key = "abc"
            invalid_key = "def"
            another_key = "ghi"
            _ansible_ignore_unknown_opts = $true
        }

        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        $m.Params | Assert-DictionaryEqual -Expected @{ option_key = "abc"; invalid_key = "def"; another_key = "ghi" }
        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $output = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $output.Keys.Count | Assert-Equal -Expected 2
        $output.changed | Assert-Equal -Expected $false
        $output.invocation | Assert-DictionaryEqual -Expected @{module_args = @{option_key = "abc"; invalid_key = "def"; another_key = "ghi" } }
    }

    "Check mode and module doesn't support check mode" = {
        $spec = @{
            options = @{
                option_key = @{
                    type = "str"
                }
            }
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            _ansible_check_mode = $true
            option_key = "abc"
        }

        $failed = $false
        try {
            $null = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected_msg = "remote module (undefined win module) does not support check mode"

        $actual.Keys.Count | Assert-Equal -Expected 4
        $actual.changed | Assert-Equal -Expected $false
        $actual.skipped | Assert-Equal -Expected $true
        $actual.msg | Assert-Equal -Expected $expected_msg
        $actual.invocation | Assert-DictionaryEqual -Expected @{module_args = @{option_key = "abc" } }
    }

    "Check mode with suboption without supports_check_mode" = {
        $spec = @{
            options = @{
                sub_options = @{
                    # This tests the situation where a sub key doesn't set supports_check_mode, the logic in
                    # Ansible.Basic automatically sets that to $false and we want it to ignore it for a nested check
                    type = "dict"
                    options = @{
                        sub_option = @{ type = "str"; default = "value" }
                    }
                }
            }
            supports_check_mode = $true
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            _ansible_check_mode = $true
        }

        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        $m.CheckMode | Assert-Equal -Expected $true
    }

    "Type conversion error" = {
        $spec = @{
            options = @{
                option_key = @{
                    type = "int"
                }
            }
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            option_key = "a"
        }

        $failed = $false
        try {
            $null = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected_msg = "argument for option_key is of type System.String and we were unable to convert to int: "
        $expected_msg += "Input string was not in a correct format."

        $actual.Keys.Count | Assert-Equal -Expected 4
        $actual.changed | Assert-Equal -Expected $false
        $actual.failed | Assert-Equal -Expected $true
        $actual.msg | Assert-Equal -Expected $expected_msg
        $actual.invocation | Assert-DictionaryEqual -Expected @{module_args = $complex_args }
    }

    "Type conversion error - delegate" = {
        $spec = @{
            options = @{
                option_key = @{
                    type = "dict"
                    options = @{
                        sub_option_key = @{
                            type = [Func[[Object], [UInt64]]] { [System.UInt64]::Parse($args[0]) }
                        }
                    }
                }
            }
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            option_key = @{
                sub_option_key = "a"
            }
        }

        $failed = $false
        try {
            $null = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected_msg = "argument for sub_option_key is of type System.String and we were unable to convert to delegate: "
        $expected_msg += "Exception calling `"Parse`" with `"1`" argument(s): `"Input string was not in a correct format.`" "
        $expected_msg += "found in option_key"

        $actual.Keys.Count | Assert-Equal -Expected 4
        $actual.changed | Assert-Equal -Expected $false
        $actual.failed | Assert-Equal -Expected $true
        $actual.msg | Assert-Equal -Expected $expected_msg
        $actual.invocation | Assert-DictionaryEqual -Expected @{module_args = $complex_args }
    }

    "Numeric choices" = {
        $spec = @{
            options = @{
                option_key = @{
                    choices = 1, 2, 3
                    type = "int"
                }
            }
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            option_key = "2"
        }

        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $output = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $output.Keys.Count | Assert-Equal -Expected 2
        $output.changed | Assert-Equal -Expected $false
        $output.invocation | Assert-DictionaryEqual -Expected @{module_args = @{option_key = 2 } }
    }

    "Case insensitive choice" = {
        $spec = @{
            options = @{
                option_key = @{
                    choices = "abc", "def"
                }
            }
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            option_key = "ABC"
        }

        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $output = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $expected_warning = "value of option_key was a case insensitive match of one of: abc, def. "
        $expected_warning += "Checking of choices will be case sensitive in a future Ansible release. "
        $expected_warning += "Case insensitive matches were: ABC"

        $output.invocation | Assert-DictionaryEqual -Expected @{module_args = @{option_key = "ABC" } }
        # We have disabled the warnings for now
        #$output.warnings.Count | Assert-Equal -Expected 1
        #$output.warnings[0] | Assert-Equal -Expected $expected_warning
    }

    "Case insensitive choice no_log" = {
        $spec = @{
            options = @{
                option_key = @{
                    choices = "abc", "def"
                    no_log = $true
                }
            }
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            option_key = "ABC"
        }

        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $output = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $expected_warning = "value of option_key was a case insensitive match of one of: abc, def. "
        $expected_warning += "Checking of choices will be case sensitive in a future Ansible release. "
        $expected_warning += "Case insensitive matches were: VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"

        $output.invocation | Assert-DictionaryEqual -Expected @{module_args = @{option_key = "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER" } }
        # We have disabled the warnings for now
        #$output.warnings.Count | Assert-Equal -Expected 1
        #$output.warnings[0] | Assert-Equal -Expected $expected_warning
    }

    "Case insentitive choice as list" = {
        $spec = @{
            options = @{
                option_key = @{
                    choices = "abc", "def", "ghi", "JKL"
                    type = "list"
                    elements = "str"
                }
            }
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            option_key = "AbC", "ghi", "jkl"
        }

        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $output = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $expected_warning = "value of option_key was a case insensitive match of one or more of: abc, def, ghi, JKL. "
        $expected_warning += "Checking of choices will be case sensitive in a future Ansible release. "
        $expected_warning += "Case insensitive matches were: AbC, jkl"

        $output.invocation | Assert-DictionaryEqual -Expected @{module_args = $complex_args }
        # We have disabled the warnings for now
        #$output.warnings.Count | Assert-Equal -Expected 1
        #$output.warnings[0] | Assert-Equal -Expected $expected_warning
    }

    "Invalid choice" = {
        $spec = @{
            options = @{
                option_key = @{
                    choices = "a", "b"
                }
            }
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            option_key = "c"
        }

        $failed = $false
        try {
            $null = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected_msg = "value of option_key must be one of: a, b. Got no match for: c"

        $actual.Keys.Count | Assert-Equal -Expected 4
        $actual.changed | Assert-Equal -Expected $false
        $actual.failed | Assert-Equal -Expected $true
        $actual.msg | Assert-Equal -Expected $expected_msg
        $actual.invocation | Assert-DictionaryEqual -Expected @{module_args = $complex_args }
    }

    "Invalid choice with no_log" = {
        $spec = @{
            options = @{
                option_key = @{
                    choices = "a", "b"
                    no_log = $true
                }
            }
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            option_key = "abc"
        }

        $failed = $false
        try {
            $null = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected_msg = "value of option_key must be one of: a, b. Got no match for: ********"

        $actual.Keys.Count | Assert-Equal -Expected 4
        $actual.changed | Assert-Equal -Expected $false
        $actual.failed | Assert-Equal -Expected $true
        $actual.msg | Assert-Equal -Expected $expected_msg
        $actual.invocation | Assert-DictionaryEqual -Expected @{module_args = @{option_key = "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER" } }
    }

    "Invalid choice in list" = {
        $spec = @{
            options = @{
                option_key = @{
                    choices = "a", "b"
                    type = "list"
                }
            }
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            option_key = "a", "c"
        }

        $failed = $false
        try {
            $null = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected_msg = "value of option_key must be one or more of: a, b. Got no match for: c"

        $actual.Keys.Count | Assert-Equal -Expected 4
        $actual.changed | Assert-Equal -Expected $false
        $actual.failed | Assert-Equal -Expected $true
        $actual.msg | Assert-Equal -Expected $expected_msg
        $actual.invocation | Assert-DictionaryEqual -Expected @{module_args = $complex_args }
    }

    "Mutually exclusive options" = {
        $spec = @{
            options = @{
                option1 = @{}
                option2 = @{}
            }
            mutually_exclusive = @(, @("option1", "option2"))
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            option1 = "a"
            option2 = "b"
        }

        $failed = $false
        try {
            $null = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected_msg = "parameters are mutually exclusive: option1, option2"

        $actual.Keys.Count | Assert-Equal -Expected 4
        $actual.changed | Assert-Equal -Expected $false
        $actual.failed | Assert-Equal -Expected $true
        $actual.msg | Assert-Equal -Expected $expected_msg
        $actual.invocation | Assert-DictionaryEqual -Expected @{module_args = $complex_args }
    }

    "Missing required argument" = {
        $spec = @{
            options = @{
                option1 = @{}
                option2 = @{required = $true }
            }
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            option1 = "a"
        }

        $failed = $false
        try {
            $null = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected_msg = "missing required arguments: option2"

        $actual.Keys.Count | Assert-Equal -Expected 4
        $actual.changed | Assert-Equal -Expected $false
        $actual.failed | Assert-Equal -Expected $true
        $actual.msg | Assert-Equal -Expected $expected_msg
        $actual.invocation | Assert-DictionaryEqual -Expected @{module_args = $complex_args }
    }

    "Missing required argument subspec - no value defined" = {
        $spec = @{
            options = @{
                option_key = @{
                    type = "dict"
                    options = @{
                        sub_option_key = @{
                            required = $true
                        }
                    }
                }
            }
        }

        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        $failed = $false
        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $actual.Keys.Count | Assert-Equal -Expected 2
        $actual.changed | Assert-Equal -Expected $false
        $actual.invocation | Assert-DictionaryEqual -Expected @{module_args = $complex_args }
    }

    "Missing required argument subspec" = {
        $spec = @{
            options = @{
                option_key = @{
                    type = "dict"
                    options = @{
                        sub_option_key = @{
                            required = $true
                        }
                        another_key = @{}
                    }
                }
            }
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            option_key = @{
                another_key = "abc"
            }
        }

        $failed = $false
        try {
            $null = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected_msg = "missing required arguments: sub_option_key found in option_key"

        $actual.Keys.Count | Assert-Equal -Expected 4
        $actual.changed | Assert-Equal -Expected $false
        $actual.failed | Assert-Equal -Expected $true
        $actual.msg | Assert-Equal -Expected $expected_msg
        $actual.invocation | Assert-DictionaryEqual -Expected @{module_args = $complex_args }
    }

    "Required together not set" = {
        $spec = @{
            options = @{
                option1 = @{}
                option2 = @{}
            }
            required_together = @(, @("option1", "option2"))
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            option1 = "abc"
        }

        $failed = $false
        try {
            $null = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected_msg = "parameters are required together: option1, option2"

        $actual.Keys.Count | Assert-Equal -Expected 4
        $actual.changed | Assert-Equal -Expected $false
        $actual.failed | Assert-Equal -Expected $true
        $actual.msg | Assert-Equal -Expected $expected_msg
        $actual.invocation | Assert-DictionaryEqual -Expected @{module_args = $complex_args }
    }

    "Required together not set - subspec" = {
        $spec = @{
            options = @{
                option_key = @{
                    type = "dict"
                    options = @{
                        option1 = @{}
                        option2 = @{}
                    }
                    required_together = @(, @("option1", "option2"))
                }
                another_option = @{}
            }
            required_together = @(, @("option_key", "another_option"))
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            option_key = @{
                option1 = "abc"
            }
            another_option = "def"
        }

        $failed = $false
        try {
            $null = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected_msg = "parameters are required together: option1, option2 found in option_key"

        $actual.Keys.Count | Assert-Equal -Expected 4
        $actual.changed | Assert-Equal -Expected $false
        $actual.failed | Assert-Equal -Expected $true
        $actual.msg | Assert-Equal -Expected $expected_msg
        $actual.invocation | Assert-DictionaryEqual -Expected @{module_args = $complex_args }
    }

    "Required one of not set" = {
        $spec = @{
            options = @{
                option1 = @{}
                option2 = @{}
                option3 = @{}
            }
            required_one_of = @(@("option1", "option2"), @("option2", "option3"))
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            option1 = "abc"
        }

        $failed = $false
        try {
            $null = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected_msg = "one of the following is required: option2, option3"

        $actual.Keys.Count | Assert-Equal -Expected 4
        $actual.changed | Assert-Equal -Expected $false
        $actual.failed | Assert-Equal -Expected $true
        $actual.msg | Assert-Equal -Expected $expected_msg
        $actual.invocation | Assert-DictionaryEqual -Expected @{module_args = $complex_args }
    }

    "Required if invalid entries" = {
        $spec = @{
            options = @{
                state = @{choices = "absent", "present"; default = "present" }
                path = @{type = "path" }
            }
            required_if = @(, @("state", "absent"))
        }

        $failed = $false
        try {
            $null = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected_msg = "internal error: invalid required_if value count of 2, expecting 3 or 4 entries"

        $actual.Keys.Count | Assert-Equal -Expected 4
        $actual.changed | Assert-Equal -Expected $false
        $actual.failed | Assert-Equal -Expected $true
        $actual.msg | Assert-Equal -Expected $expected_msg
        $actual.invocation | Assert-DictionaryEqual -Expected @{module_args = $complex_args }
    }

    "Required if no missing option" = {
        $spec = @{
            options = @{
                state = @{choices = "absent", "present"; default = "present" }
                name = @{}
                path = @{type = "path" }
            }
            required_if = @(, @("state", "absent", @("name", "path")))
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            name = "abc"
        }
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)

        $failed = $false
        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $actual.Keys.Count | Assert-Equal -Expected 2
        $actual.changed | Assert-Equal -Expected $false
        $actual.invocation | Assert-DictionaryEqual -Expected @{module_args = $complex_args }
    }

    "Required if missing option" = {
        $spec = @{
            options = @{
                state = @{choices = "absent", "present"; default = "present" }
                name = @{}
                path = @{type = "path" }
            }
            required_if = @(, @("state", "absent", @("name", "path")))
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            state = "absent"
            name = "abc"
        }

        $failed = $false
        try {
            $null = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected_msg = "state is absent but all of the following are missing: path"

        $actual.Keys.Count | Assert-Equal -Expected 4
        $actual.changed | Assert-Equal -Expected $false
        $actual.failed | Assert-Equal -Expected $true
        $actual.msg | Assert-Equal -Expected $expected_msg
        $actual.invocation | Assert-DictionaryEqual -Expected @{module_args = $complex_args }
    }

    "Required if missing option and required one is set" = {
        $spec = @{
            options = @{
                state = @{choices = "absent", "present"; default = "present" }
                name = @{}
                path = @{type = "path" }
            }
            required_if = @(, @("state", "absent", @("name", "path"), $true))
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            state = "absent"
        }

        $failed = $false
        try {
            $null = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $expected_msg = "state is absent but any of the following are missing: name, path"

        $actual.Keys.Count | Assert-Equal -Expected 4
        $actual.changed | Assert-Equal -Expected $false
        $actual.failed | Assert-Equal -Expected $true
        $actual.msg | Assert-Equal -Expected $expected_msg
        $actual.invocation | Assert-DictionaryEqual -Expected @{module_args = $complex_args }
    }

    "Required if missing option but one required set" = {
        $spec = @{
            options = @{
                state = @{choices = "absent", "present"; default = "present" }
                name = @{}
                path = @{type = "path" }
            }
            required_if = @(, @("state", "absent", @("name", "path"), $true))
        }
        Set-Variable -Name complex_args -Scope Global -Value @{
            state = "absent"
            name = "abc"
        }
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)

        $failed = $false
        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $actual.Keys.Count | Assert-Equal -Expected 2
        $actual.changed | Assert-Equal -Expected $false
        $actual.invocation | Assert-DictionaryEqual -Expected @{module_args = $complex_args }
    }

    "Required if for unset option" = {
        $spec = @{
            options = @{
                state = @{ choices = "absent", "present" }
                name = @{}
                path = @{}
            }
            required_if = @(, @("state", "absent", @("name", "path")))
        }
        Set-Variable -Name complex_args -Scope Global -Value @{}
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)

        $failed = $false
        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $actual.Keys.Count | Assert-Equal -Expected 2
        $actual.changed | Assert-Equal -Expected $false
        $actual.invocation | Assert-DictionaryEqual -Expected @{ module_args = $complex_args }
    }

    "PS Object in return result" = {
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})

        # JavaScriptSerializer struggles with PS Object like PSCustomObject due to circular references, this test makes
        # sure we can handle these types of objects without bombing
        $m.Result.output = [PSCustomObject]@{a = "a"; b = "b" }
        $failed = $true
        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $actual.Keys.Count | Assert-Equal -Expected 3
        $actual.changed | Assert-Equal -Expected $false
        $actual.invocation | Assert-DictionaryEqual -Expected @{module_args = @{} }
        $actual.output | Assert-DictionaryEqual -Expected @{a = "a"; b = "b" }
    }

    "String json array to object" = {
        $input_json = '["abc", "def"]'
        $actual = [Ansible.Basic.AnsibleModule]::FromJson($input_json)
        $actual -is [Array] | Assert-Equal -Expected $true
        $actual.Length | Assert-Equal -Expected 2
        $actual[0] | Assert-Equal -Expected "abc"
        $actual[1] | Assert-Equal -Expected "def"
    }

    "String json array of dictionaries to object" = {
        $input_json = '[{"abc":"def"}]'
        $actual = [Ansible.Basic.AnsibleModule]::FromJson($input_json)
        $actual -is [Array] | Assert-Equal -Expected $true
        $actual.Length | Assert-Equal -Expected 1
        $actual[0] | Assert-DictionaryEqual -Expected @{"abc" = "def" }
    }

    "Spec with fragments" = {
        $spec = @{
            options = @{
                option1 = @{ type = "str" }
            }
        }
        $fragment1 = @{
            options = @{
                option2 = @{ type = "str" }
            }
        }

        Set-Variable -Name complex_args -Scope Global -Value @{
            option1 = "option1"
            option2 = "option2"
        }
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec, @($fragment1))

        $failed = $false
        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $actual.changed | Assert-Equal -Expected $false
        $actual.invocation | Assert-DictionaryEqual -Expected @{module_args = $complex_args }
    }

    "Fragment spec that with a deprecated alias" = {
        $spec = @{
            options = @{
                option1 = @{
                    aliases = @("alias1_spec")
                    type = "str"
                    deprecated_aliases = @(
                        @{name = "alias1_spec"; version = "2.0" }
                    )
                }
                option2 = @{
                    aliases = @("alias2_spec")
                    deprecated_aliases = @(
                        @{name = "alias2_spec"; version = "2.0"; collection_name = "ansible.builtin" }
                    )
                }
            }
        }
        $fragment1 = @{
            options = @{
                option1 = @{
                    aliases = @("alias1")
                    deprecated_aliases = @()  # Makes sure it doesn't overwrite the spec, just adds to it.
                }
                option2 = @{
                    aliases = @("alias2")
                    deprecated_aliases = @(
                        @{name = "alias2"; version = "2.0"; collection_name = "foo.bar" }
                    )
                    type = "str"
                }
            }
        }

        Set-Variable -Name complex_args -Scope Global -Value @{
            alias1_spec = "option1"
            alias2 = "option2"
        }
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec, @($fragment1))

        $failed = $false
        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $actual.deprecations.Count | Assert-Equal -Expected 2
        $actual.deprecations[0] | Assert-DictionaryEqual -Expected @{
            msg = "Alias 'alias1_spec' is deprecated. See the module docs for more information"; version = "2.0"; collection_name = $null
        }
        $actual.deprecations[1] | Assert-DictionaryEqual -Expected @{
            msg = "Alias 'alias2' is deprecated. See the module docs for more information"; version = "2.0"; collection_name = "foo.bar"
        }
        $actual.changed | Assert-Equal -Expected $false
        $actual.invocation | Assert-DictionaryEqual -Expected @{
            module_args = @{
                option1 = "option1"
                alias1_spec = "option1"
                option2 = "option2"
                alias2 = "option2"
            }
        }
    }

    "Fragment spec with mutual args" = {
        $spec = @{
            options = @{
                option1 = @{ type = "str" }
                option2 = @{ type = "str" }
            }
            mutually_exclusive = @(
                , @('option1', 'option2')
            )
        }
        $fragment1 = @{
            options = @{
                fragment1_1 = @{ type = "str" }
                fragment1_2 = @{ type = "str" }
            }
            mutually_exclusive = @(
                , @('fragment1_1', 'fragment1_2')
            )
        }
        $fragment2 = @{
            options = @{
                fragment2 = @{ type = "str" }
            }
        }

        Set-Variable -Name complex_args -Scope Global -Value @{
            option1 = "option1"
            fragment1_1 = "fragment1_1"
            fragment1_2 = "fragment1_2"
            fragment2 = "fragment2"
        }

        $failed = $false
        try {
            [Ansible.Basic.AnsibleModule]::Create(@(), $spec, @($fragment1, $fragment2))
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $actual.changed | Assert-Equal -Expected $false
        $actual.failed | Assert-Equal -Expected $true
        $actual.msg | Assert-Equal -Expected "parameters are mutually exclusive: fragment1_1, fragment1_2"
        $actual.invocation | Assert-DictionaryEqual -Expected @{ module_args = $complex_args }
    }

    "Fragment spec with no_log" = {
        $spec = @{
            options = @{
                option1 = @{
                    aliases = @("alias")
                }
            }
        }
        $fragment1 = @{
            options = @{
                option1 = @{
                    no_log = $true  # Makes sure that a value set in the fragment but not in the spec is respected.
                    type = "str"
                }
            }
        }

        Set-Variable -Name complex_args -Scope Global -Value @{
            alias = "option1"
        }
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec, @($fragment1))

        $failed = $false
        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $actual.changed | Assert-Equal -Expected $false
        $actual.invocation | Assert-DictionaryEqual -Expected @{
            module_args = @{
                option1 = "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"
                alias = "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"
            }
        }
    }

    "Catch invalid fragment spec format" = {
        $spec = @{
            options = @{
                option1 = @{ type = "str" }
            }
        }
        $fragment = @{
            options = @{}
            invalid = "will fail"
        }

        Set-Variable -Name complex_args -Scope Global -Value @{
            option1 = "option1"
        }

        $failed = $false
        try {
            [Ansible.Basic.AnsibleModule]::Create(@(), $spec, @($fragment))
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $actual.failed | Assert-Equal -Expected $true
        $actual.msg.StartsWith("internal error: argument spec entry contains an invalid key 'invalid', valid keys: ") | Assert-Equal -Expected $true
    }

    "Spec with different list types" = {
        $spec = @{
            options = @{
                # Single element of the same list type not in a list
                option1 = @{
                    aliases = "alias1"
                    deprecated_aliases = @{name = "alias1"; version = "2.0"; collection_name = "foo.bar" }
                }

                # Arrays
                option2 = @{
                    aliases = , "alias2"
                    deprecated_aliases = , @{name = "alias2"; version = "2.0"; collection_name = "foo.bar" }
                }

                # ArrayList
                option3 = @{
                    aliases = [System.Collections.ArrayList]@("alias3")
                    deprecated_aliases = [System.Collections.ArrayList]@(@{name = "alias3"; version = "2.0"; collection_name = "foo.bar" })
                }

                # Generic.List[Object]
                option4 = @{
                    aliases = [System.Collections.Generic.List[Object]]@("alias4")
                    deprecated_aliases = [System.Collections.Generic.List[Object]]@(@{name = "alias4"; version = "2.0"; collection_name = "foo.bar" })
                }

                # Generic.List[T]
                option5 = @{
                    aliases = [System.Collections.Generic.List[String]]@("alias5")
                    deprecated_aliases = [System.Collections.Generic.List[Hashtable]]@()
                }
            }
        }
        $spec.options.option5.deprecated_aliases.Add(@{name = "alias5"; version = "2.0"; collection_name = "foo.bar" })

        Set-Variable -Name complex_args -Scope Global -Value @{
            alias1 = "option1"
            alias2 = "option2"
            alias3 = "option3"
            alias4 = "option4"
            alias5 = "option5"
        }
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)

        $failed = $false
        try {
            $m.ExitJson()
        }
        catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equal -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equal -Expected $true

        $actual.changed | Assert-Equal -Expected $false
        $actual.deprecations.Count | Assert-Equal -Expected 5
        foreach ($dep in $actual.deprecations) {
            $dep.msg -like "Alias 'alias?' is deprecated. See the module docs for more information" | Assert-Equal -Expected $true
            $dep.version | Assert-Equal -Expected '2.0'
            $dep.collection_name | Assert-Equal -Expected 'foo.bar'
        }
        $actual.invocation | Assert-DictionaryEqual -Expected @{
            module_args = @{
                alias1 = "option1"
                option1 = "option1"
                alias2 = "option2"
                option2 = "option2"
                alias3 = "option3"
                option3 = "option3"
                alias4 = "option4"
                option4 = "option4"
                alias5 = "option5"
                option5 = "option5"
            }
        }
    }
}

try {
    foreach ($test_impl in $tests.GetEnumerator()) {
        # Reset the variables before each test
        Set-Variable -Name complex_args -Value @{} -Scope Global

        $test = $test_impl.Key
        &$test_impl.Value
    }
    $module.Result.data = "success"
}
catch [System.Management.Automation.RuntimeException] {
    $module.Result.failed = $true
    $module.Result.test = $test
    $module.Result.line = $_.InvocationInfo.ScriptLineNumber
    $module.Result.method = $_.InvocationInfo.Line.Trim()

    if ($_.Exception.Message.StartSwith("exit: ")) {
        # The exception was caused by an unexpected Exit call, log that on the output
        $module.Result.output = (ConvertFrom-Json -InputObject $_.Exception.InnerException.Output)
        $module.Result.msg = "Uncaught AnsibleModule exit in tests, see output"
    }
    else {
        # Unrelated exception
        $module.Result.exception = $_.Exception.ToString()
        $module.Result.msg = "Uncaught exception: $(($_ | Out-String).ToString())"
    }
}

Exit-Module
