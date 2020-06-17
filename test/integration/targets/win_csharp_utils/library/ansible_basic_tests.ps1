#!powershell

#AnsibleRequires -CSharpUtil Ansible.Basic

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

Function Assert-DictionaryEquals {
    param(
        [Parameter(Mandatory=$true, ValueFromPipeline=$true)][AllowNull()]$Actual,
        [Parameter(Mandatory=$true, Position=0)][AllowNull()]$Expected
    )
    $actual_keys = $Actual.Keys
    $expected_keys = $Expected.Keys

    $actual_keys.Count | Assert-Equals -Expected $expected_keys.Count
    foreach ($actual_entry in $Actual.GetEnumerator()) {
        $actual_key = $actual_entry.Key
        ($actual_key -cin $expected_keys) | Assert-Equals -Expected $true
        $actual_value = $actual_entry.Value
        $expected_value = $Expected.$actual_key

        if ($actual_value -is [System.Collections.IDictionary]) {
            $actual_value | Assert-DictionaryEquals -Expected $expected_value
        } elseif ($actual_value -is [System.Collections.ArrayList] -or $actual_value -is [Array]) {
            for ($i = 0; $i -lt $actual_value.Count; $i++) {
                $actual_entry = $actual_value[$i]
                $expected_entry = $expected_value[$i]
                if ($actual_entry -is [System.Collections.IDictionary]) {
                    $actual_entry | Assert-DictionaryEquals -Expected $expected_entry
                } else {
                    Assert-Equals -Actual $actual_entry -Expected $expected_entry
                }
            }
        } else {
            Assert-Equals -Actual $actual_value -Expected $expected_value
        }
    }
    foreach ($expected_key in $expected_keys) {
        ($expected_key -cin $actual_keys) | Assert-Equals -Expected $true
    }
}

Function Exit-Module {
    # Make sure Exit actually calls exit and not our overriden test behaviour
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

        $m.CheckMode | Assert-Equals -Expected $false
        $m.DebugMode | Assert-Equals -Expected $false
        $m.DiffMode | Assert-Equals -Expected $false
        $m.KeepRemoteFiles | Assert-Equals -Expected $false
        $m.ModuleName | Assert-Equals -Expected "undefined win module"
        $m.NoLog | Assert-Equals -Expected $false
        $m.Verbosity | Assert-Equals -Expected 0
        $m.AnsibleVersion | Assert-Equals -Expected $null
    }

    "Empty spec and no options - complex_args" = {
        $complex_args = @{}
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})

        $m.CheckMode | Assert-Equals -Expected $false
        $m.DebugMode | Assert-Equals -Expected $false
        $m.DiffMode | Assert-Equals -Expected $false
        $m.KeepRemoteFiles | Assert-Equals -Expected $false
        $m.ModuleName | Assert-Equals -Expected "undefined win module"
        $m.NoLog | Assert-Equals -Expected $false
        $m.Verbosity | Assert-Equals -Expected 0
        $m.AnsibleVersion | Assert-Equals -Expected $null
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
        "_ansible_tmpdir": "$($m_tmpdir -replace "\\", "\\")",
        "_ansible_verbosity": 3,
        "_ansible_version": "2.8.0"
    }
}
"@)
        $m = [Ansible.Basic.AnsibleModule]::Create(@($args_file), @{supports_check_mode=$true})
        $m.CheckMode | Assert-Equals -Expected $true
        $m.DebugMode | Assert-Equals -Expected $true
        $m.DiffMode | Assert-Equals -Expected $true
        $m.KeepRemoteFiles | Assert-Equals -Expected $true
        $m.ModuleName | Assert-Equals -Expected "ansible_basic_tests"
        $m.NoLog | Assert-Equals -Expected $true
        $m.Verbosity | Assert-Equals -Expected 3
        $m.AnsibleVersion | Assert-Equals -Expected "2.8.0"
        $m.Tmpdir | Assert-Equals -Expected $m_tmpdir
    }

    "Internal param changes - complex_args" = {
        $m_tmpdir = Join-Path -Path $tmpdir -ChildPath "moduletmpdir-$(Get-Random)"
        New-Item -Path $m_tmpdir -ItemType Directory > $null
        $complex_args = @{
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
        $m.CheckMode | Assert-Equals -Expected $true
        $m.DebugMode | Assert-Equals -Expected $true
        $m.DiffMode | Assert-Equals -Expected $true
        $m.KeepRemoteFiles | Assert-Equals -Expected $true
        $m.ModuleName | Assert-Equals -Expected "ansible_basic_tests"
        $m.NoLog | Assert-Equals -Expected $true
        $m.Verbosity | Assert-Equals -Expected 3
        $m.AnsibleVersion | Assert-Equals -Expected "2.8.0"
        $m.Tmpdir | Assert-Equals -Expected $m_tmpdir
    }

    "Parse complex module options" = {
        $spec = @{
            options = @{
                option_default = @{}
                missing_option_default = @{}
                string_option = @{type = "str"}
                required_option = @{required = $true}
                missing_choices = @{choices = "a", "b"}
                choices = @{choices = "a", "b"}
                one_choice = @{choices = ,"b"}
                choice_with_default = @{choices = "a", "b"; default = "b"}
                alias_direct = @{aliases = ,"alias_direct1"}
                alias_as_alias = @{aliases = "alias_as_alias1", "alias_as_alias2"}
                bool_type = @{type = "bool"}
                bool_from_str = @{type = "bool"}
                dict_type = @{
                    type = "dict"
                    options = @{
                        int_type = @{type = "int"}
                        str_type = @{type = "str"; default = "str_sub_type"}
                    }
                }
                dict_type_missing = @{
                    type = "dict"
                    options = @{
                        int_type = @{type = "int"}
                        str_type = @{type = "str"; default = "str_sub_type"}
                    }
                }
                dict_type_defaults = @{
                    type = "dict"
                    apply_defaults = $true
                    options = @{
                        int_type = @{type = "int"}
                        str_type = @{type = "str"; default = "str_sub_type"}
                    }
                }
                dict_type_json = @{type = "dict"}
                dict_type_str = @{type = "dict"}
                float_type = @{type = "float"}
                int_type = @{type = "int"}
                json_type = @{type = "json"}
                json_type_dict = @{type = "json"}
                list_type = @{type = "list"}
                list_type_str = @{type = "list"}
                list_with_int = @{type = "list"; elements = "int"}
                list_type_single = @{type = "list"}
                list_with_dict = @{
                    type = "list"
                    elements = "dict"
                    options = @{
                        int_type = @{type = "int"}
                        str_type = @{type = "str"; default = "str_sub_type"}
                    }
                }
                path_type = @{type = "path"}
                path_type_nt = @{type = "path"}
                path_type_missing = @{type = "path"}
                raw_type_str = @{type = "raw"}
                raw_type_int = @{type = "raw"}
                sid_type = @{type = "sid"}
                sid_from_name = @{type = "sid"}
                str_type = @{type = "str"}
                delegate_type = @{type = [Func[[Object], [UInt64]]]{ [System.UInt64]::Parse($args[0]) }}
            }
        }
        $complex_args = @{
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

        $m.Params.option_default | Assert-Equals -Expected "1"
        $m.Params.option_default.GetType().ToString() | Assert-Equals -Expected "System.String"
        $m.Params.missing_option_default | Assert-Equals -Expected $null
        $m.Params.string_option | Assert-Equals -Expected "1"
        $m.Params.string_option.GetType().ToString() | Assert-Equals -Expected "System.String"
        $m.Params.required_option | Assert-Equals -Expected "required"
        $m.Params.required_option.GetType().ToString() | Assert-Equals -Expected "System.String"
        $m.Params.missing_choices | Assert-Equals -Expected $null
        $m.Params.choices | Assert-Equals -Expected "a"
        $m.Params.choices.GetType().ToString() | Assert-Equals -Expected "System.String"
        $m.Params.one_choice | Assert-Equals -Expected "b"
        $m.Params.one_choice.GetType().ToString() | Assert-Equals -Expected "System.String"
        $m.Params.choice_with_default | Assert-Equals -Expected "b"
        $m.Params.choice_with_default.GetType().ToString() | Assert-Equals -Expected "System.String"
        $m.Params.alias_direct | Assert-Equals -Expected "a"
        $m.Params.alias_direct.GetType().ToString() | Assert-Equals -Expected "System.String"
        $m.Params.alias_as_alias | Assert-Equals -Expected "a"
        $m.Params.alias_as_alias.GetType().ToString() | Assert-Equals -Expected "System.String"
        $m.Params.bool_type | Assert-Equals -Expected $true
        $m.Params.bool_type.GetType().ToString() | Assert-Equals -Expected "System.Boolean"
        $m.Params.bool_from_str | Assert-Equals -Expected $false
        $m.Params.bool_from_str.GetType().ToString() | Assert-Equals -Expected "System.Boolean"
        $m.Params.dict_type | Assert-DictionaryEquals -Expected @{int_type = 10; str_type = "str_sub_type"}
        $m.Params.dict_type.GetType().ToString() | Assert-Equals -Expected "System.Collections.Generic.Dictionary``2[System.String,System.Object]"
        $m.Params.dict_type.int_type.GetType().ToString() | Assert-Equals -Expected "System.Int32"
        $m.Params.dict_type.str_type.GetType().ToString() | Assert-Equals -Expected "System.String"
        $m.Params.dict_type_missing | Assert-Equals -Expected $null
        $m.Params.dict_type_defaults | Assert-DictionaryEquals -Expected @{int_type = $null; str_type = "str_sub_type"}
        $m.Params.dict_type_defaults.GetType().ToString() | Assert-Equals -Expected "System.Collections.Generic.Dictionary``2[System.String,System.Object]"
        $m.Params.dict_type_defaults.str_type.GetType().ToString() | Assert-Equals -Expected "System.String"
        $m.Params.dict_type_json | Assert-DictionaryEquals -Expected @{
            a = "a"
            b = 1
            c = @("a", "b")
        }
        $m.Params.dict_type_json.GetType().ToString() | Assert-Equals -Expected "System.Collections.Generic.Dictionary``2[System.String,System.Object]"
        $m.Params.dict_type_json.a.GetType().ToString() | Assert-Equals -Expected "System.String"
        $m.Params.dict_type_json.b.GetType().ToString() | Assert-Equals -Expected "System.Int32"
        $m.Params.dict_type_json.c.GetType().ToString() | Assert-Equals -Expected "System.Collections.ArrayList"
        $m.Params.dict_type_str | Assert-DictionaryEquals -Expected @{a = "a"; b = "b 2"; c = "c"}
        $m.Params.dict_type_str.GetType().ToString() | Assert-Equals -Expected "System.Collections.Generic.Dictionary``2[System.String,System.Object]"
        $m.Params.dict_type_str.a.GetType().ToString() | Assert-Equals -Expected "System.String"
        $m.Params.dict_type_str.b.GetType().ToString() | Assert-Equals -Expected "System.String"
        $m.Params.dict_type_str.c.GetType().ToString() | Assert-Equals -Expected "System.String"
        $m.Params.float_type | Assert-Equals -Expected ([System.Single]3.14159)
        $m.Params.float_type.GetType().ToString() | Assert-Equals -Expected "System.Single"
        $m.Params.int_type | Assert-Equals -Expected 0
        $m.Params.int_type.GetType().ToString() | Assert-Equals -Expected "System.Int32"
        $m.Params.json_type | Assert-Equals -Expected '{"a":"a","b":1,"c":["a","b"]}'
        $m.Params.json_type.GetType().ToString() | Assert-Equals -Expected "System.String"
        [Ansible.Basic.AnsibleModule]::FromJson($m.Params.json_type_dict) | Assert-DictionaryEquals -Expected ([Ansible.Basic.AnsibleModule]::FromJson('{"a":"a","b":1,"c":["a","b"]}'))
        $m.Params.json_type_dict.GetType().ToString() | Assert-Equals -Expected "System.String"
        $m.Params.list_type.GetType().ToString() | Assert-Equals -Expected "System.Collections.Generic.List``1[System.Object]"
        $m.Params.list_type.Count | Assert-Equals -Expected 4
        $m.Params.list_type[0] | Assert-Equals -Expected "a"
        $m.Params.list_type[0].GetType().FullName | Assert-Equals -Expected "System.String"
        $m.Params.list_type[1] | Assert-Equals -Expected "b"
        $m.Params.list_type[1].GetType().FullName | Assert-Equals -Expected "System.String"
        $m.Params.list_type[2] | Assert-Equals -Expected 1
        $m.Params.list_type[2].GetType().FullName | Assert-Equals -Expected "System.Int32"
        $m.Params.list_type[3] | Assert-Equals -Expected 2
        $m.Params.list_type[3].GetType().FullName | Assert-Equals -Expected "System.Int32"
        $m.Params.list_type_str.GetType().ToString() | Assert-Equals -Expected "System.Collections.Generic.List``1[System.Object]"
        $m.Params.list_type_str.Count | Assert-Equals -Expected 4
        $m.Params.list_type_str[0] | Assert-Equals -Expected "a"
        $m.Params.list_type_str[0].GetType().FullName | Assert-Equals -Expected "System.String"
        $m.Params.list_type_str[1] | Assert-Equals -Expected "b"
        $m.Params.list_type_str[1].GetType().FullName | Assert-Equals -Expected "System.String"
        $m.Params.list_type_str[2] | Assert-Equals -Expected "1"
        $m.Params.list_type_str[2].GetType().FullName | Assert-Equals -Expected "System.String"
        $m.Params.list_type_str[3] | Assert-Equals -Expected "2"
        $m.Params.list_type_str[3].GetType().FullName | Assert-Equals -Expected "System.String"
        $m.Params.list_with_int.GetType().ToString() | Assert-Equals -Expected "System.Collections.Generic.List``1[System.Object]"
        $m.Params.list_with_int.Count | Assert-Equals -Expected 2
        $m.Params.list_with_int[0] | Assert-Equals -Expected 1
        $m.Params.list_with_int[0].GetType().FullName | Assert-Equals -Expected "System.Int32"
        $m.Params.list_with_int[1] | Assert-Equals -Expected 2
        $m.Params.list_with_int[1].GetType().FullName | Assert-Equals -Expected "System.Int32"
        $m.Params.list_type_single.GetType().ToString() | Assert-Equals -Expected "System.Collections.Generic.List``1[System.Object]"
        $m.Params.list_type_single.Count | Assert-Equals -Expected 1
        $m.Params.list_type_single[0] | Assert-Equals -Expected "single"
        $m.Params.list_type_single[0].GetType().FullName | Assert-Equals -Expected "System.String"
        $m.Params.list_with_dict.GetType().FullName.StartsWith("System.Collections.Generic.List``1[[System.Object") | Assert-Equals -Expected $true
        $m.Params.list_with_dict.Count | Assert-Equals -Expected 3
        $m.Params.list_with_dict[0].GetType().FullName.StartsWith("System.Collections.Generic.Dictionary``2[[System.String") | Assert-Equals -Expected $true
        $m.Params.list_with_dict[0] | Assert-DictionaryEquals -Expected @{int_type = 2; str_type = "dict entry"}
        $m.Params.list_with_dict[0].int_type.GetType().FullName.ToString() | Assert-Equals -Expected "System.Int32"
        $m.Params.list_with_dict[0].str_type.GetType().FullName.ToString() | Assert-Equals -Expected "System.String"
        $m.Params.list_with_dict[1].GetType().FullName.StartsWith("System.Collections.Generic.Dictionary``2[[System.String") | Assert-Equals -Expected $true
        $m.Params.list_with_dict[1] | Assert-DictionaryEquals -Expected @{int_type = 1; str_type = "str_sub_type"}
        $m.Params.list_with_dict[1].int_type.GetType().FullName.ToString() | Assert-Equals -Expected "System.Int32"
        $m.Params.list_with_dict[1].str_type.GetType().FullName.ToString() | Assert-Equals -Expected "System.String"
        $m.Params.list_with_dict[2].GetType().FullName.StartsWith("System.Collections.Generic.Dictionary``2[[System.String") | Assert-Equals -Expected $true
        $m.Params.list_with_dict[2] | Assert-DictionaryEquals -Expected @{int_type = $null; str_type = "str_sub_type"}
        $m.Params.list_with_dict[2].str_type.GetType().FullName.ToString() | Assert-Equals -Expected "System.String"
        $m.Params.path_type | Assert-Equals -Expected "$($env:SystemRoot)\System32"
        $m.Params.path_type.GetType().ToString() | Assert-Equals -Expected "System.String"
        $m.Params.path_type_nt | Assert-Equals -Expected "\\?\%SystemRoot%\System32"
        $m.Params.path_type_nt.GetType().ToString() | Assert-Equals -Expected "System.String"
        $m.Params.path_type_missing | Assert-Equals -Expected "T:\missing\path"
        $m.Params.path_type_missing.GetType().ToString() | Assert-Equals -Expected "System.String"
        $m.Params.raw_type_str | Assert-Equals -Expected "str"
        $m.Params.raw_type_str.GetType().FullName | Assert-Equals -Expected "System.String"
        $m.Params.raw_type_int | Assert-Equals -Expected 1
        $m.Params.raw_type_int.GetType().FullName | Assert-Equals -Expected "System.Int32"
        $m.Params.sid_type | Assert-Equals -Expected (New-Object -TypeName System.Security.Principal.SecurityIdentifier -ArgumentList "S-1-5-18")
        $m.Params.sid_type.GetType().ToString() | Assert-Equals -Expected "System.Security.Principal.SecurityIdentifier"
        $m.Params.sid_from_name | Assert-Equals -Expected (New-Object -TypeName System.Security.Principal.SecurityIdentifier -ArgumentList "S-1-5-18")
        $m.Params.sid_from_name.GetType().ToString() | Assert-Equals -Expected "System.Security.Principal.SecurityIdentifier"
        $m.Params.str_type | Assert-Equals -Expected "str"
        $m.Params.str_type.GetType().ToString() | Assert-Equals -Expected "System.String"
        $m.Params.delegate_type | Assert-Equals -Expected 1234
        $m.Params.delegate_type.GetType().ToString() | Assert-Equals -Expected "System.UInt64"

        $failed = $false
        try {
            $m.ExitJson()
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

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
        $actual.Keys.Count | Assert-Equals -Expected 2
        $actual.changed | Assert-Equals -Expected $false
        $actual.invocation | Assert-DictionaryEquals -Expected @{module_args = $expected_module_args}
    }

    "Parse module args with list elements and delegate type" = {
        $spec = @{
            options = @{
                list_delegate_type = @{
                    type = "list"
                    elements = [Func[[Object], [UInt16]]]{ [System.UInt16]::Parse($args[0]) }
                }
            }
        }
        $complex_args = @{
            list_delegate_type = @(
                "1234",
                4321
            )
        }
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        $m.Params.list_delegate_type.GetType().Name | Assert-Equals -Expected 'List`1'
        $m.Params.list_delegate_type[0].GetType().FullName | Assert-Equals -Expected "System.UInt16"
        $m.Params.list_delegate_Type[1].GetType().FullName | Assert-Equals -Expected "System.UInt16"

        $failed = $false
        try {
            $m.ExitJson()
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

        $expected_module_args = @{
            list_delegate_type = @(
                1234,
                4321
            )
        }
        $actual.Keys.Count | Assert-Equals -Expected 2
        $actual.changed | Assert-Equals -Expected $false
        $actual.invocation | Assert-DictionaryEquals -Expected @{module_args = $expected_module_args}
    }

    "Parse module args with case insensitive input" = {
        $spec = @{
            options = @{
                option1 = @{ type = "int"; required = $true }
            }
        }
        $complex_args = @{
            _ansible_module_name = "win_test"
            Option1 = "1"
        }

        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        # Verifies the case of the params key is set to the module spec not actual input
        $m.Params.Keys | Assert-Equals -Expected @("option1")
        $m.Params.option1 | Assert-Equals -Expected 1

        # Verifies the type conversion happens even on a case insensitive match
        $m.Params.option1.GetType().FullName | Assert-Equals -Expected "System.Int32"

        $failed = $false
        try {
            $m.ExitJson()
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

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
        $actual | Assert-DictionaryEquals -Expected $expected
    }

    "No log values" = {
        $spec = @{
            options = @{
                username = @{type = "str"}
                password = @{type = "str"; no_log = $true}
                password2 = @{type = "int"; no_log = $true}
                dict = @{type = "dict"}
            }
        }
        $complex_args = @{
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
        $m.Params.username | Assert-Equals -Expected "user - pass - name"
        $m.Params.password | Assert-Equals -Expected "pass"
        $m.Params.password2 | Assert-Equals -Expected 1234
        $m.Params.dict.custom | Assert-Equals -Expected "pass"

        $failed = $false
        try {
            $m.ExitJson()
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

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
        $actual | Assert-DictionaryEquals -Expected $expected

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
        $actual_event | Assert-DictionaryEquals -Expected $expected_event
    }

    "No log value with an empty string" = {
        $spec = @{
            options = @{
                password1 = @{type = "str"; no_log = $true}
                password2 = @{type = "str"; no_log = $true}
            }
        }
        $complex_args = @{
            _ansible_module_name = "test_no_log"
            password1 = ""
        }

        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        $m.Result.data = $complex_args.dict

        # verify params internally aren't masked
        $m.Params.password1 | Assert-Equals -Expected ""
        $m.Params.password2 | Assert-Equals -Expected $null

        $failed = $false
        try {
            $m.ExitJson()
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_test_out)
        }
        $failed | Assert-Equals -Expected $true

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
        $actual | Assert-DictionaryEquals -Expected $expected
    }

    "Removed in version" = {
        $spec = @{
            options = @{
                removed1 = @{removed_in_version = "2.1"}
                removed2 = @{removed_in_version = "2.2"}
            }
        }
        $complex_args = @{
            removed1 = "value"
        }

        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)

        $failed = $false
        try {
            $m.ExitJson()
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

        $expected = @{
            changed = $false
            invocation = @{
                module_args = @{
                    removed1 = "value"
                    removed2 = $null
                }
            }
            deprecations = @(
                @{
                    msg = "Param 'removed1' is deprecated. See the module docs for more information"
                    version = "2.1"
                }
            )
        }
        $actual | Assert-DictionaryEquals -Expected $expected
    }

    "Required by - single value" = {
        $spec = @{
            options = @{
                option1 = @{type = "str"}
                option2 = @{type = "str"}
                option3 = @{type = "str"}
            }
            required_by = @{
                option1 = "option2"
            }
        }
        $complex_args = @{
            option1 = "option1"
            option2 = "option2"
        }

        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)

        $failed = $false
        try {
            $m.ExitJson()
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

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
        $actual | Assert-DictionaryEquals -Expected $expected
    }

    "Required by - multiple values" = {
        $spec = @{
            options = @{
                option1 = @{type = "str"}
                option2 = @{type = "str"}
                option3 = @{type = "str"}
            }
            required_by = @{
                option1 = "option2", "option3"
            }
        }
        $complex_args = @{
            option1 = "option1"
            option2 = "option2"
            option3 = "option3"
        }

        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)

        $failed = $false
        try {
            $m.ExitJson()
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

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
        $actual | Assert-DictionaryEquals -Expected $expected
    }

    "Required by explicit null" = {
        $spec = @{
            options = @{
                option1 = @{type = "str"}
                option2 = @{type = "str"}
                option3 = @{type = "str"}
            }
            required_by = @{
                option1 = "option2"
            }
        }
        $complex_args = @{
            option1 = "option1"
            option2 = $null
        }

        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)

        $failed = $false
        try {
            $m.ExitJson()
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

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
        $actual | Assert-DictionaryEquals -Expected $expected
    }

    "Required by failed - single value" = {
        $spec = @{
            options = @{
                option1 = @{type = "str"}
                option2 = @{type = "str"}
                option3 = @{type = "str"}
            }
            required_by = @{
                option1 = "option2"
            }
        }
        $complex_args = @{
            option1 = "option1"
        }

        $failed = $false
        try {
            $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

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
        $actual | Assert-DictionaryEquals -Expected $expected
    }

    "Required by failed - multiple values" = {
        $spec = @{
            options = @{
                option1 = @{type = "str"}
                option2 = @{type = "str"}
                option3 = @{type = "str"}
            }
            required_by = @{
                option1 = "option2", "option3"
            }
        }
        $complex_args = @{
            option1 = "option1"
        }

        $failed = $false
        try {
            $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

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
        $actual | Assert-DictionaryEquals -Expected $expected
    }

    "Debug without debug set" = {
        $complex_args = @{
            _ansible_debug = $false
        }
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})
        $m.Debug("debug message")
        $actual_event = (Get-EventLog -LogName Application -Source Ansible -Newest 1).Message
        $actual_event | Assert-Equals -Expected "undefined win module - Invoked with:`r`n  "
    }

    "Debug with debug set" = {
        $complex_args = @{
            _ansible_debug = $true
        }
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})
        $m.Debug("debug message")
        $actual_event = (Get-EventLog -LogName Application -Source Ansible -Newest 1).Message
        $actual_event | Assert-Equals -Expected "undefined win module - [DEBUG] debug message"
    }

    "Deprecate and warn" = {
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})
        $m.Deprecate("message", "2.8")
        $actual_deprecate_event = Get-EventLog -LogName Application -Source Ansible -Newest 1
        $m.Warn("warning")
        $actual_warn_event = Get-EventLog -LogName Application -Source Ansible -Newest 1

        $actual_deprecate_event.Message | Assert-Equals -Expected "undefined win module - [DEPRECATION WARNING] message 2.8"
        $actual_warn_event.EntryType | Assert-Equals -Expected "Warning"
        $actual_warn_event.Message | Assert-Equals -Expected "undefined win module - [WARNING] warning"

        $failed = $false
        try {
            $m.ExitJson()
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

        $expected = @{
            changed = $false
            invocation = @{
                module_args = @{}
            }
            warnings = @("warning")
            deprecations = @(@{msg = "message"; version = "2.8"})
        }
        $actual | Assert-DictionaryEquals -Expected $expected
    }

    "FailJson with message" = {
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})

        $failed = $false
        try {
            $m.FailJson("fail message")
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $failed

        $expected = @{
            changed = $false
            invocation = @{
                module_args = @{}
            }
            failed = $true
            msg = "fail message"
        }
        $actual | Assert-DictionaryEquals -Expected $expected
    }

    "FailJson with Exception" = {
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})

        try {
            [System.IO.Path]::GetFullPath($null)
        } catch {
            $excp = $_.Exception
        }

        $failed = $false
        try {
            $m.FailJson("fail message", $excp)
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $failed

        $expected = @{
            changed = $false
            invocation = @{
                module_args = @{}
            }
            failed = $true
            msg = "fail message"
        }
        $actual | Assert-DictionaryEquals -Expected $expected
    }

    "FailJson with ErrorRecord" = {
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})

        try {
            Get-Item -Path $null
        } catch {
            $error_record = $_
        }

        $failed = $false
        try {
            $m.FailJson("fail message", $error_record)
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $failed

        $expected = @{
            changed = $false
            invocation = @{
                module_args = @{}
            }
            failed = $true
            msg = "fail message"
        }
        $actual | Assert-DictionaryEquals -Expected $expected
    }

    "FailJson with Exception and verbosity 3" = {
        $complex_args = @{
            _ansible_verbosity = 3
        }
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})

        try {
            [System.IO.Path]::GetFullPath($null)
        } catch {
            $excp = $_.Exception
        }

        $failed = $false
        try {
            $m.FailJson("fail message", $excp)
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $failed

        $actual.changed | Assert-Equals -Expected $false
        $actual.invocation | Assert-DictionaryEquals -Expected @{module_args = @{}}
        $actual.failed | Assert-Equals -Expected $true
        $actual.msg | Assert-Equals -Expected "fail message"
        $actual.exception.Contains('System.Management.Automation.MethodInvocationException: Exception calling "GetFullPath" with "1" argument(s)') | Assert-Equals -Expected $true
    }

    "FailJson with ErrorRecord and verbosity 3" = {
        $complex_args = @{
            _ansible_verbosity = 3
        }
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})

        try {
            Get-Item -Path $null
        } catch {
            $error_record = $_
        }

        $failed = $false
        try {
            $m.FailJson("fail message", $error_record)
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $failed

        $actual.changed | Assert-Equals -Expected $false
        $actual.invocation | Assert-DictionaryEquals -Expected @{module_args = @{}}
        $actual.failed | Assert-Equals -Expected $true
        $actual.msg | Assert-Equals -Expected "fail message"
        $actual.exception.Contains("Cannot bind argument to parameter 'Path' because it is null") | Assert-Equals -Expected $true
        $actual.exception.Contains("+             Get-Item -Path `$null") | Assert-Equals -Expected $true
        $actual.exception.Contains("ScriptStackTrace:") | Assert-Equals -Expected $true
    }

    "Diff entry without diff set" = {
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})
        $m.Diff.before = @{a = "a"}
        $m.Diff.after = @{b = "b"}

        $failed = $false
        try {
            $m.ExitJson()
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $failed

        $expected = @{
            changed = $false
            invocation = @{
                module_args = @{}
            }
        }
        $actual | Assert-DictionaryEquals -Expected $expected
    }

    "Diff entry with diff set" = {
        $complex_args = @{
            _ansible_diff = $true
        }
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})
        $m.Diff.before = @{a = "a"}
        $m.Diff.after = @{b = "b"}

        $failed = $false
        try {
            $m.ExitJson()
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $failed

        $expected = @{
            changed = $false
            invocation = @{
                module_args = @{}
            }
            diff = @{
                before = @{a = "a"}
                after = @{b = "b"}
            }
        }
        $actual | Assert-DictionaryEquals -Expected $expected
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
            $actual | Assert-Equals -Expected $expected
            $actual.GetType().FullName | Assert-Equals -Expected "System.Boolean"
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
            } catch {
                $failed = $true
                $_.Exception.Message.Contains("The value '$fail_bool' is not a valid boolean") | Assert-Equals -Expected $true
            }
            $failed | Assert-Equals -Expected $true
        }
    }

    "Unknown internal key" = {
        $complex_args = @{
            _ansible_invalid = "invalid"
        }
        $failed = $false
        try {
            $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 1"

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
            $actual | Assert-DictionaryEquals -Expected $expected
        }
        $failed | Assert-Equals -Expected $true
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
        $complex_args = @{
            _ansible_remote_tmp = $remote_tmp.ToString()
        }
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})
        (Test-Path -Path $remote_tmp -PathType Container) | Assert-Equals -Expected $true

        $actual_tmpdir = $m.Tmpdir
        $parent_tmpdir = Split-Path -Path $actual_tmpdir -Parent
        $tmpdir_name = Split-Path -Path $actual_tmpdir -Leaf

        $parent_tmpdir | Assert-Equals -Expected $remote_tmp
        $tmpdir_name.StartSwith("ansible-moduletmp-") | Assert-Equals -Expected $true
        (Test-Path -Path $actual_tmpdir -PathType Container) | Assert-Equals -Expected $true
        (Test-Path -Path $remote_tmp -PathType Container) | Assert-Equals -Expected $true
        $children = [System.IO.Directory]::EnumerateDirectories($remote_tmp)
        $children.Count | Assert-Equals -Expected 1
        $actual_tmpdir_sd = (Get-Acl -Path $actual_tmpdir).GetSecurityDescriptorSddlForm("Access, Owner")
        $actual_tmpdir_sd | Assert-Equals -Expected $expected_sd

        try {
            $m.ExitJson()
        } catch [System.Management.Automation.RuntimeException] {
            $output = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        (Test-Path -Path $actual_tmpdir -PathType Container) | Assert-Equals -Expected $false
        (Test-Path -Path $remote_tmp -PathType Container) | Assert-Equals -Expected $true
        $output.warnings.Count | Assert-Equals -Expected 0
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
        $complex_args = @{
            _ansible_remote_tmp = $remote_tmp.ToString()
        }
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})
        (Test-Path -Path $remote_tmp -PathType Container) | Assert-Equals -Expected $false

        $actual_tmpdir = $m.Tmpdir
        $parent_tmpdir = Split-Path -Path $actual_tmpdir -Parent
        $tmpdir_name = Split-Path -Path $actual_tmpdir -Leaf

        $parent_tmpdir | Assert-Equals -Expected $remote_tmp
        $tmpdir_name.StartSwith("ansible-moduletmp-") | Assert-Equals -Expected $true
        (Test-Path -Path $actual_tmpdir -PathType Container) | Assert-Equals -Expected $true
        (Test-Path -Path $remote_tmp -PathType Container) | Assert-Equals -Expected $true
        $children = [System.IO.Directory]::EnumerateDirectories($remote_tmp)
        $children.Count | Assert-Equals -Expected 1
        $actual_remote_sd = (Get-Acl -Path $remote_tmp).GetSecurityDescriptorSddlForm("Access, Owner")
        $actual_tmpdir_sd = (Get-Acl -Path $actual_tmpdir).GetSecurityDescriptorSddlForm("Access, Owner")
        $actual_remote_sd | Assert-Equals -Expected $expected_sd
        $actual_tmpdir_sd | Assert-Equals -Expected $expected_sd

        try {
            $m.ExitJson()
        } catch [System.Management.Automation.RuntimeException] {
            $output = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        (Test-Path -Path $actual_tmpdir -PathType Container) | Assert-Equals -Expected $false
        (Test-Path -Path $remote_tmp -PathType Container) | Assert-Equals -Expected $true
        $output.warnings.Count | Assert-Equals -Expected 1
        $nt_account = $current_user.Translate([System.Security.Principal.NTAccount])
        $actual_warning = "Module remote_tmp $remote_tmp did not exist and was created with FullControl to $nt_account, "
        $actual_warning += "this may cause issues when running as another user. To avoid this, "
        $actual_warning += "create the remote_tmp dir with the correct permissions manually"
        $actual_warning | Assert-Equals -Expected $output.warnings[0]
    }

    "Module tmp, keep remote files" = {
        $remote_tmp = Join-Path -Path $tmpdir -ChildPath "moduletmpdir-$(Get-Random)"
        New-Item -Path $remote_tmp -ItemType Directory > $null
        $complex_args = @{
            _ansible_remote_tmp = $remote_tmp.ToString()
            _ansible_keep_remote_files = $true
        }
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})

        $actual_tmpdir = $m.Tmpdir
        $parent_tmpdir = Split-Path -Path $actual_tmpdir -Parent
        $tmpdir_name = Split-Path -Path $actual_tmpdir -Leaf

        $parent_tmpdir | Assert-Equals -Expected $remote_tmp
        $tmpdir_name.StartSwith("ansible-moduletmp-") | Assert-Equals -Expected $true
        (Test-Path -Path $actual_tmpdir -PathType Container) | Assert-Equals -Expected $true
        (Test-Path -Path $remote_tmp -PathType Container) | Assert-Equals -Expected $true

        try {
            $m.ExitJson()
        } catch [System.Management.Automation.RuntimeException] {
            $output = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        (Test-Path -Path $actual_tmpdir -PathType Container) | Assert-Equals -Expected $true
        (Test-Path -Path $remote_tmp -PathType Container) | Assert-Equals -Expected $true
        $output.warnings.Count | Assert-Equals -Expected 0
        Remove-Item -Path $actual_tmpdir -Force -Recurse
    }

    "Invalid argument spec key" = {
        $spec = @{
            invalid = $true
        }
        $failed = $false
        try {
            $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

        $expected_msg = "internal error: argument spec entry contains an invalid key 'invalid', valid keys: apply_defaults, "
        $expected_msg += "aliases, choices, default, elements, mutually_exclusive, no_log, options, removed_in_version, "
        $expected_msg += "removed_at_date, removed_from_collection, required, required_by, required_if, required_one_of, "
        $expected_msg += "required_together, supports_check_mode, type"

        $actual.Keys.Count | Assert-Equals -Expected 3
        $actual.failed | Assert-Equals -Expected $true
        $actual.msg | Assert-Equals -Expected $expected_msg
        ("exception" -cin $actual.Keys) | Assert-Equals -Expected $true
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
            $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

        $expected_msg = "internal error: argument spec entry contains an invalid key 'invalid', valid keys: apply_defaults, "
        $expected_msg += "aliases, choices, default, elements, mutually_exclusive, no_log, options, removed_in_version, "
        $expected_msg += "removed_at_date, removed_from_collection, required, required_by, required_if, required_one_of, "
        $expected_msg += "required_together, supports_check_mode, type - found in option_key -> sub_option_key"

        $actual.Keys.Count | Assert-Equals -Expected 3
        $actual.failed | Assert-Equals -Expected $true
        $actual.msg | Assert-Equals -Expected $expected_msg
        ("exception" -cin $actual.Keys) | Assert-Equals -Expected $true
    }

    "Invalid argument spec value type" = {
        $spec = @{
            apply_defaults = "abc"
        }
        $failed = $false
        try {
            $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

        $expected_msg = "internal error: argument spec for 'apply_defaults' did not match expected "
        $expected_msg += "type System.Boolean: actual type System.String"

        $actual.Keys.Count | Assert-Equals -Expected 3
        $actual.failed | Assert-Equals -Expected $true
        $actual.msg | Assert-Equals -Expected $expected_msg
        ("exception" -cin $actual.Keys) | Assert-Equals -Expected $true
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
            $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

        $expected_msg = "internal error: type 'invalid type' is unsupported - found in option_key. "
        $expected_msg += "Valid types are: bool, dict, float, int, json, list, path, raw, sid, str"

        $actual.Keys.Count | Assert-Equals -Expected 3
        $actual.failed | Assert-Equals -Expected $true
        $actual.msg | Assert-Equals -Expected $expected_msg
        ("exception" -cin $actual.Keys) | Assert-Equals -Expected $true
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
            $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

        $expected_msg = "internal error: elements 'invalid type' is unsupported - found in option_key. "
        $expected_msg += "Valid types are: bool, dict, float, int, json, list, path, raw, sid, str"

        $actual.Keys.Count | Assert-Equals -Expected 3
        $actual.failed | Assert-Equals -Expected $true
        $actual.msg | Assert-Equals -Expected $expected_msg
        ("exception" -cin $actual.Keys) | Assert-Equals -Expected $true
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
            $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

        $expected_msg = "internal error: required and default are mutually exclusive for option_key"

        $actual.Keys.Count | Assert-Equals -Expected 3
        $actual.failed | Assert-Equals -Expected $true
        $actual.msg | Assert-Equals -Expected $expected_msg
        ("exception" -cin $actual.Keys) | Assert-Equals -Expected $true
    }

    "Unsupported options" = {
        $spec = @{
            options = @{
                option_key = @{
                    type = "str"
                }
            }
        }
        $complex_args = @{
            option_key = "abc"
            invalid_key = "def"
            another_key = "ghi"
        }

        $failed = $false
        try {
            $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

        $expected_msg = "Unsupported parameters for (undefined win module) module: another_key, invalid_key. "
        $expected_msg += "Supported parameters include: option_key"

        $actual.Keys.Count | Assert-Equals -Expected 4
        $actual.changed | Assert-Equals -Expected $false
        $actual.failed | Assert-Equals -Expected $true
        $actual.msg | Assert-Equals -Expected $expected_msg
        $actual.invocation | Assert-DictionaryEquals -Expected @{module_args = $complex_args}
    }

    "Check mode and module doesn't support check mode" = {
        $spec = @{
            options = @{
                option_key = @{
                    type = "str"
                }
            }
        }
        $complex_args = @{
            _ansible_check_mode = $true
            option_key = "abc"
        }

        $failed = $false
        try {
            $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

        $expected_msg = "remote module (undefined win module) does not support check mode"

        $actual.Keys.Count | Assert-Equals -Expected 4
        $actual.changed | Assert-Equals -Expected $false
        $actual.skipped | Assert-Equals -Expected $true
        $actual.msg | Assert-Equals -Expected $expected_msg
        $actual.invocation | Assert-DictionaryEquals -Expected @{module_args = @{option_key = "abc"}}
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
        $complex_args = @{
            _ansible_check_mode = $true
        }

        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        $m.CheckMode | Assert-Equals -Expected $true
    }

    "Type conversion error" = {
        $spec = @{
            options = @{
                option_key = @{
                    type = "int"
                }
            }
        }
        $complex_args = @{
            option_key = "a"
        }

        $failed = $false
        try {
            $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

        $expected_msg = "argument for option_key is of type System.String and we were unable to convert to int: "
        $expected_msg += "Input string was not in a correct format."

        $actual.Keys.Count | Assert-Equals -Expected 4
        $actual.changed | Assert-Equals -Expected $false
        $actual.failed | Assert-Equals -Expected $true
        $actual.msg | Assert-Equals -Expected $expected_msg
        $actual.invocation | Assert-DictionaryEquals -Expected @{module_args = $complex_args}
    }

    "Type conversion error - delegate" = {
        $spec = @{
            options = @{
                option_key = @{
                    type = "dict"
                    options = @{
                        sub_option_key = @{
                            type = [Func[[Object], [UInt64]]]{ [System.UInt64]::Parse($args[0]) }
                        }
                    }
                }
            }
        }
        $complex_args = @{
            option_key = @{
                sub_option_key = "a"
            }
        }

        $failed = $false
        try {
            $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

        $expected_msg = "argument for sub_option_key is of type System.String and we were unable to convert to delegate: "
        $expected_msg += "Exception calling `"Parse`" with `"1`" argument(s): `"Input string was not in a correct format.`" "
        $expected_msg += "found in option_key"

        $actual.Keys.Count | Assert-Equals -Expected 4
        $actual.changed | Assert-Equals -Expected $false
        $actual.failed | Assert-Equals -Expected $true
        $actual.msg | Assert-Equals -Expected $expected_msg
        $actual.invocation | Assert-DictionaryEquals -Expected @{module_args = $complex_args}
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
        $complex_args = @{
            option_key = "2"
        }

        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        try {
            $m.ExitJson()
        } catch [System.Management.Automation.RuntimeException] {
            $output = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $output.Keys.Count | Assert-Equals -Expected 2
        $output.changed | Assert-Equals -Expected $false
        $output.invocation | Assert-DictionaryEquals -Expected @{module_args = @{option_key = 2}}
    }

    "Case insensitive choice" = {
        $spec = @{
            options = @{
                option_key = @{
                    choices = "abc", "def"
                }
            }
        }
        $complex_args = @{
            option_key = "ABC"
        }

        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        try {
            $m.ExitJson()
        } catch [System.Management.Automation.RuntimeException] {
            $output = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $expected_warning = "value of option_key was a case insensitive match of one of: abc, def. "
        $expected_warning += "Checking of choices will be case sensitive in a future Ansible release. "
        $expected_warning += "Case insensitive matches were: ABC"

        $output.invocation | Assert-DictionaryEquals -Expected @{module_args = @{option_key = "ABC"}}
        # We have disabled the warnings for now
        #$output.warnings.Count | Assert-Equals -Expected 1
        #$output.warnings[0] | Assert-Equals -Expected $expected_warning
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
        $complex_args = @{
            option_key = "ABC"
        }

        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        try {
            $m.ExitJson()
        } catch [System.Management.Automation.RuntimeException] {
            $output = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $expected_warning = "value of option_key was a case insensitive match of one of: abc, def. "
        $expected_warning += "Checking of choices will be case sensitive in a future Ansible release. "
        $expected_warning += "Case insensitive matches were: VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"

        $output.invocation | Assert-DictionaryEquals -Expected @{module_args = @{option_key = "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"}}
        # We have disabled the warnings for now
        #$output.warnings.Count | Assert-Equals -Expected 1
        #$output.warnings[0] | Assert-Equals -Expected $expected_warning
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
        $complex_args = @{
            option_key = "AbC", "ghi", "jkl"
        }

        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        try {
            $m.ExitJson()
        } catch [System.Management.Automation.RuntimeException] {
            $output = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $expected_warning = "value of option_key was a case insensitive match of one or more of: abc, def, ghi, JKL. "
        $expected_warning += "Checking of choices will be case sensitive in a future Ansible release. "
        $expected_warning += "Case insensitive matches were: AbC, jkl"

        $output.invocation | Assert-DictionaryEquals -Expected @{module_args = $complex_args}
        # We have disabled the warnings for now
        #$output.warnings.Count | Assert-Equals -Expected 1
        #$output.warnings[0] | Assert-Equals -Expected $expected_warning
    }

    "Invalid choice" = {
        $spec = @{
            options = @{
                option_key = @{
                    choices = "a", "b"
                }
            }
        }
        $complex_args = @{
            option_key = "c"
        }

        $failed = $false
        try {
            $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

        $expected_msg = "value of option_key must be one of: a, b. Got no match for: c"

        $actual.Keys.Count | Assert-Equals -Expected 4
        $actual.changed | Assert-Equals -Expected $false
        $actual.failed | Assert-Equals -Expected $true
        $actual.msg | Assert-Equals -Expected $expected_msg
        $actual.invocation | Assert-DictionaryEquals -Expected @{module_args = $complex_args}
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
        $complex_args = @{
            option_key = "abc"
        }

        $failed = $false
        try {
            $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

        $expected_msg = "value of option_key must be one of: a, b. Got no match for: ********"

        $actual.Keys.Count | Assert-Equals -Expected 4
        $actual.changed | Assert-Equals -Expected $false
        $actual.failed | Assert-Equals -Expected $true
        $actual.msg | Assert-Equals -Expected $expected_msg
        $actual.invocation | Assert-DictionaryEquals -Expected @{module_args = @{option_key = "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER"}}
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
        $complex_args = @{
            option_key = "a", "c"
        }

        $failed = $false
        try {
            $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

        $expected_msg = "value of option_key must be one or more of: a, b. Got no match for: c"

        $actual.Keys.Count | Assert-Equals -Expected 4
        $actual.changed | Assert-Equals -Expected $false
        $actual.failed | Assert-Equals -Expected $true
        $actual.msg | Assert-Equals -Expected $expected_msg
        $actual.invocation | Assert-DictionaryEquals -Expected @{module_args = $complex_args}
    }

    "Mutually exclusive options" = {
        $spec = @{
            options = @{
                option1 = @{}
                option2 = @{}
            }
            mutually_exclusive = @(,@("option1", "option2"))
        }
        $complex_args = @{
            option1 = "a"
            option2 = "b"
        }

        $failed = $false
        try {
            $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

        $expected_msg = "parameters are mutually exclusive: option1, option2"

        $actual.Keys.Count | Assert-Equals -Expected 4
        $actual.changed | Assert-Equals -Expected $false
        $actual.failed | Assert-Equals -Expected $true
        $actual.msg | Assert-Equals -Expected $expected_msg
        $actual.invocation | Assert-DictionaryEquals -Expected @{module_args = $complex_args}
    }

    "Missing required argument" = {
        $spec = @{
            options = @{
                option1 = @{}
                option2 = @{required = $true}
            }
        }
        $complex_args = @{
            option1 = "a"
        }

        $failed = $false
        try {
            $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

        $expected_msg = "missing required arguments: option2"

        $actual.Keys.Count | Assert-Equals -Expected 4
        $actual.changed | Assert-Equals -Expected $false
        $actual.failed | Assert-Equals -Expected $true
        $actual.msg | Assert-Equals -Expected $expected_msg
        $actual.invocation | Assert-DictionaryEquals -Expected @{module_args = $complex_args}
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
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

        $actual.Keys.Count | Assert-Equals -Expected 2
        $actual.changed | Assert-Equals -Expected $false
        $actual.invocation | Assert-DictionaryEquals -Expected @{module_args = $complex_args}
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
        $complex_args = @{
            option_key = @{
                another_key = "abc"
            }
        }

        $failed = $false
        try {
            $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

        $expected_msg = "missing required arguments: sub_option_key found in option_key"

        $actual.Keys.Count | Assert-Equals -Expected 4
        $actual.changed | Assert-Equals -Expected $false
        $actual.failed | Assert-Equals -Expected $true
        $actual.msg | Assert-Equals -Expected $expected_msg
        $actual.invocation | Assert-DictionaryEquals -Expected @{module_args = $complex_args}
    }

    "Required together not set" = {
        $spec = @{
            options = @{
                option1 = @{}
                option2 = @{}
            }
            required_together = @(,@("option1", "option2"))
        }
        $complex_args = @{
            option1 = "abc"
        }

        $failed = $false
        try {
            $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

        $expected_msg = "parameters are required together: option1, option2"

        $actual.Keys.Count | Assert-Equals -Expected 4
        $actual.changed | Assert-Equals -Expected $false
        $actual.failed | Assert-Equals -Expected $true
        $actual.msg | Assert-Equals -Expected $expected_msg
        $actual.invocation | Assert-DictionaryEquals -Expected @{module_args = $complex_args}
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
                    required_together = @(,@("option1", "option2"))
                }
                another_option = @{}
            }
            required_together = @(,@("option_key", "another_option"))
        }
        $complex_args = @{
            option_key = @{
                option1 = "abc"
            }
            another_option = "def"
        }

        $failed = $false
        try {
            $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

        $expected_msg = "parameters are required together: option1, option2 found in option_key"

        $actual.Keys.Count | Assert-Equals -Expected 4
        $actual.changed | Assert-Equals -Expected $false
        $actual.failed | Assert-Equals -Expected $true
        $actual.msg | Assert-Equals -Expected $expected_msg
        $actual.invocation | Assert-DictionaryEquals -Expected @{module_args = $complex_args}
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
        $complex_args = @{
            option1 = "abc"
        }

        $failed = $false
        try {
            $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

        $expected_msg = "one of the following is required: option2, option3"

        $actual.Keys.Count | Assert-Equals -Expected 4
        $actual.changed | Assert-Equals -Expected $false
        $actual.failed | Assert-Equals -Expected $true
        $actual.msg | Assert-Equals -Expected $expected_msg
        $actual.invocation | Assert-DictionaryEquals -Expected @{module_args = $complex_args}
    }

    "Required if invalid entries" = {
        $spec = @{
            options = @{
                state = @{choices = "absent", "present"; default = "present"}
                path = @{type = "path"}
            }
            required_if = @(,@("state", "absent"))
        }

        $failed = $false
        try {
            $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

        $expected_msg = "internal error: invalid required_if value count of 2, expecting 3 or 4 entries"

        $actual.Keys.Count | Assert-Equals -Expected 4
        $actual.changed | Assert-Equals -Expected $false
        $actual.failed | Assert-Equals -Expected $true
        $actual.msg | Assert-Equals -Expected $expected_msg
        $actual.invocation | Assert-DictionaryEquals -Expected @{module_args = $complex_args}
    }

    "Required if no missing option" = {
        $spec = @{
            options = @{
                state = @{choices = "absent", "present"; default = "present"}
                name = @{}
                path = @{type = "path"}
            }
            required_if = @(,@("state", "absent", @("name", "path")))
        }
        $complex_args = @{
            name = "abc"
        }
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)

        $failed = $false
        try {
            $m.ExitJson()
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

        $actual.Keys.Count | Assert-Equals -Expected 2
        $actual.changed | Assert-Equals -Expected $false
        $actual.invocation | Assert-DictionaryEquals -Expected @{module_args = $complex_args}
    }

    "Required if missing option" = {
        $spec = @{
            options = @{
                state = @{choices = "absent", "present"; default = "present"}
                name = @{}
                path = @{type = "path"}
            }
            required_if = @(,@("state", "absent", @("name", "path")))
        }
        $complex_args = @{
            state = "absent"
            name = "abc"
        }

        $failed = $false
        try {
            $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

        $expected_msg = "state is absent but all of the following are missing: path"

        $actual.Keys.Count | Assert-Equals -Expected 4
        $actual.changed | Assert-Equals -Expected $false
        $actual.failed | Assert-Equals -Expected $true
        $actual.msg | Assert-Equals -Expected $expected_msg
        $actual.invocation | Assert-DictionaryEquals -Expected @{module_args = $complex_args}
    }

    "Required if missing option and required one is set" = {
        $spec = @{
            options = @{
                state = @{choices = "absent", "present"; default = "present"}
                name = @{}
                path = @{type = "path"}
            }
            required_if = @(,@("state", "absent", @("name", "path"), $true))
        }
        $complex_args = @{
            state = "absent"
        }

        $failed = $false
        try {
            $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 1"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

        $expected_msg = "state is absent but any of the following are missing: name, path"

        $actual.Keys.Count | Assert-Equals -Expected 4
        $actual.changed | Assert-Equals -Expected $false
        $actual.failed | Assert-Equals -Expected $true
        $actual.msg | Assert-Equals -Expected $expected_msg
        $actual.invocation | Assert-DictionaryEquals -Expected @{module_args = $complex_args}
    }

    "Required if missing option but one required set" = {
        $spec = @{
            options = @{
                state = @{choices = "absent", "present"; default = "present"}
                name = @{}
                path = @{type = "path"}
            }
            required_if = @(,@("state", "absent", @("name", "path"), $true))
        }
        $complex_args = @{
            state = "absent"
            name = "abc"
        }
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)

        $failed = $false
        try {
            $m.ExitJson()
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

        $actual.Keys.Count | Assert-Equals -Expected 2
        $actual.changed | Assert-Equals -Expected $false
        $actual.invocation | Assert-DictionaryEquals -Expected @{module_args = $complex_args}
    }

    "PS Object in return result" = {
        $m = [Ansible.Basic.AnsibleModule]::Create(@(), @{})

        # JavaScriptSerializer struggles with PS Object like PSCustomObject due to circular references, this test makes
        # sure we can handle these types of objects without bombing
        $m.Result.output = [PSCustomObject]@{a = "a"; b = "b"}
        $failed = $true
        try {
            $m.ExitJson()
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

        $actual.Keys.Count | Assert-Equals -Expected 3
        $actual.changed | Assert-Equals -Expected $false
        $actual.invocation | Assert-DictionaryEquals -Expected @{module_args = @{}}
        $actual.output | Assert-DictionaryEquals -Expected @{a = "a"; b = "b"}
    }

    "String json array to object" = {
        $input_json = '["abc", "def"]'
        $actual = [Ansible.Basic.AnsibleModule]::FromJson($input_json)
        $actual -is [Array] | Assert-Equals -Expected $true
        $actual.Length | Assert-Equals -Expected 2
        $actual[0] | Assert-Equals -Expected "abc"
        $actual[1] | Assert-Equals -Expected "def"
    }

    "String json array of dictionaries to object" = {
        $input_json = '[{"abc":"def"}]'
        $actual = [Ansible.Basic.AnsibleModule]::FromJson($input_json)
        $actual -is [Array] | Assert-Equals -Expected $true
        $actual.Length | Assert-Equals -Expected 1
        $actual[0] | Assert-DictionaryEquals -Expected @{"abc" = "def"}
    }

    "Ansible 2.10 compatibility" = {
        $spec = @{
            options = @{
                removed1 = @{removed_at_date = [DateTime]"2020-01-01"; removed_from_collection = "foo.bar"}
            }
        }
        $complex_args = @{
            removed1 = "value"
        }

        $m = [Ansible.Basic.AnsibleModule]::Create(@(), $spec)
        $m.Deprecate("version w collection", "2.10", "foo.bar")
        $m.Deprecate("date w/o collection", [DateTime]"2020-01-01")
        $m.Deprecate("date w collection", [DateTime]"2020-01-01", "foo.bar")

        $failed = $false
        try {
            $m.ExitJson()
        } catch [System.Management.Automation.RuntimeException] {
            $failed = $true
            $_.Exception.Message | Assert-Equals -Expected "exit: 0"
            $actual = [Ansible.Basic.AnsibleModule]::FromJson($_.Exception.InnerException.Output)
        }
        $failed | Assert-Equals -Expected $true

        $expected = @{
            changed = $false
            invocation = @{
                module_args = @{
                    removed1 = "value"
                }
            }
            deprecations = @(
                @{
                    msg = "Param 'removed1' is deprecated. See the module docs for more information"
                    version = $null
                },
                @{
                    msg = "version w collection"
                    version = "2.10"
                },
                @{
                    msg = "date w/o collection"
                    version = $null
                },
                @{
                    msg = "date w collection"
                    version = $null
                }
            )
        }
        $actual | Assert-DictionaryEquals -Expected $expected
    }
}

try {
    foreach ($test_impl in $tests.GetEnumerator()) {
        # Reset the variables before each test
        $complex_args = @{}

        $test = $test_impl.Key
        &$test_impl.Value
    }
    $module.Result.data = "success"
} catch [System.Management.Automation.RuntimeException] {
    $module.Result.failed = $true
    $module.Result.test = $test
    $module.Result.line = $_.InvocationInfo.ScriptLineNumber
    $module.Result.method = $_.InvocationInfo.Line.Trim()

    if ($_.Exception.Message.StartSwith("exit: ")) {
        # The exception was caused by an unexpected Exit call, log that on the output
        $module.Result.output = (ConvertFrom-Json -InputObject $_.Exception.InnerException.Output)
        $module.Result.msg = "Uncaught AnsibleModule exit in tests, see output"
    } else {
        # Unrelated exception
        $module.Result.exception = $_.Exception.ToString()
        $module.Result.msg = "Uncaught exception: $(($_ | Out-String).ToString())"
    }
}

Exit-Module

