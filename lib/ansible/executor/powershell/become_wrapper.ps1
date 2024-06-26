# (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

param(
    [Parameter(Mandatory = $true)][System.Collections.IDictionary]$Payload
)

#Requires -Module Ansible.ModuleUtils.AddType
#AnsibleRequires -CSharpUtil Ansible.AccessToken
#AnsibleRequires -CSharpUtil Ansible.Become

$ErrorActionPreference = "Stop"

Write-AnsibleLog "INFO - starting become_wrapper" "become_wrapper"

Function Get-EnumValue($enum, $flag_type, $value) {
    $raw_enum_value = $value.Replace('_', '')
    try {
        $enum_value = [Enum]::Parse($enum, $raw_enum_value, $true)
    }
    catch [System.ArgumentException] {
        $valid_options = [Enum]::GetNames($enum) | ForEach-Object -Process {
            (($_ -creplace "(.)([A-Z][a-z]+)", '$1_$2') -creplace "([a-z0-9])([A-Z])", '$1_$2').ToString().ToLower()
        }
        throw "become_flags $flag_type value '$value' is not valid, valid values are: $($valid_options -join ", ")"
    }
    return $enum_value
}

Function Get-BecomeFlag($flags) {
    $logon_type = [Ansible.AccessToken.LogonType]::Interactive
    $logon_flags = [Ansible.Become.LogonFlags]::WithProfile

    if ($null -eq $flags -or $flags -eq "") {
        $flag_split = @()
    }
    elseif ($flags -is [string]) {
        $flag_split = $flags.Split(" ")
    }
    else {
        throw "become_flags must be a string, was $($flags.GetType())"
    }

    foreach ($flag in $flag_split) {
        $split = $flag.Split("=")
        if ($split.Count -ne 2) {
            throw "become_flags entry '$flag' is in an invalid format, must be a key=value pair"
        }
        $flag_key = $split[0]
        $flag_value = $split[1]
        if ($flag_key -eq "logon_type") {
            $enum_details = @{
                enum = [Ansible.AccessToken.LogonType]
                flag_type = $flag_key
                value = $flag_value
            }
            $logon_type = Get-EnumValue @enum_details
        }
        elseif ($flag_key -eq "logon_flags") {
            $logon_flag_values = $flag_value.Split(",")
            $logon_flags = 0 -as [Ansible.Become.LogonFlags]
            foreach ($logon_flag_value in $logon_flag_values) {
                if ($logon_flag_value -eq "") {
                    continue
                }
                $enum_details = @{
                    enum = [Ansible.Become.LogonFlags]
                    flag_type = $flag_key
                    value = $logon_flag_value
                }
                $logon_flag = Get-EnumValue @enum_details
                $logon_flags = $logon_flags -bor $logon_flag
            }
        }
        else {
            throw "become_flags key '$flag_key' is not a valid runas flag, must be 'logon_type' or 'logon_flags'"
        }
    }

    return $logon_type, [Ansible.Become.LogonFlags]$logon_flags
}

Write-AnsibleLog "INFO - loading C# become code" "become_wrapper"
$add_type_b64 = $Payload.powershell_modules["Ansible.ModuleUtils.AddType"]
$add_type = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($add_type_b64))
New-Module -Name Ansible.ModuleUtils.AddType -ScriptBlock ([ScriptBlock]::Create($add_type)) | Import-Module > $null

$new_tmp = [System.Environment]::ExpandEnvironmentVariables($Payload.module_args["_ansible_remote_tmp"])
$access_def = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($Payload.csharp_utils["Ansible.AccessToken"]))
$become_def = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($Payload.csharp_utils["Ansible.Become"]))
$process_def = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($Payload.csharp_utils["Ansible.Process"]))
Add-CSharpType -References $access_def, $become_def, $process_def -TempPath $new_tmp -IncludeDebugInfo

$username = $Payload.become_user
$password = $Payload.become_password
# We need to set password to the value of NullString so a null password is preserved when crossing the .NET
# boundary. If we pass $null it will automatically be converted to "" and we need to keep the distinction for
# accounts that don't have a password and when someone wants to become without knowing the password.
if ($null -eq $password) {
    $password = [NullString]::Value
}

try {
    $logon_type, $logon_flags = Get-BecomeFlag -flags $Payload.become_flags
}
catch {
    Write-AnsibleError -Message "internal error: failed to parse become_flags '$($Payload.become_flags)'" -ErrorRecord $_
    $host.SetShouldExit(1)
    return
}
Write-AnsibleLog "INFO - parsed become input, user: '$username', type: '$logon_type', flags: '$logon_flags'" "become_wrapper"

# NB: CreateProcessWithTokenW commandline maxes out at 1024 chars, must
# bootstrap via small wrapper which contains the exec_wrapper passed through the
# stdin pipe. Cannot use 'powershell -' as the $ErrorActionPreference is always
# set to Stop and cannot be changed. Also need to split the payload from the wrapper to prevent potentially
# sensitive content from being logged by the scriptblock logger.
$bootstrap_wrapper = {
    &chcp.com 65001 > $null
    $exec_wrapper_str = [System.Console]::In.ReadToEnd()
    $split_parts = $exec_wrapper_str.Split(@("`0`0`0`0"), 2, [StringSplitOptions]::RemoveEmptyEntries)
    Set-Variable -Name json_raw -Value $split_parts[1]
    $exec_wrapper = [ScriptBlock]::Create($split_parts[0])
    &$exec_wrapper
}
$exec_command = [System.Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($bootstrap_wrapper.ToString()))
$lp_command_line = "powershell.exe -NonInteractive -NoProfile -ExecutionPolicy Bypass -EncodedCommand $exec_command"
$lp_current_directory = $env:SystemRoot  # TODO: should this be set to the become user's profile dir?

# pop the become_wrapper action so we don't get stuck in a loop
$Payload.actions = $Payload.actions[1..99]
# we want the output from the exec_wrapper to be base64 encoded to preserve unicode chars
$Payload.encoded_output = $true

$payload_json = ConvertTo-Json -InputObject $Payload -Depth 99 -Compress
# delimit the payload JSON from the wrapper to keep sensitive contents out of scriptblocks (which can be logged)
$exec_wrapper = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($Payload.exec_wrapper))
$exec_wrapper += "`0`0`0`0" + $payload_json

try {
    Write-AnsibleLog "INFO - starting become process '$lp_command_line'" "become_wrapper"
    $result = [Ansible.Become.BecomeUtil]::CreateProcessAsUser($username, $password, $logon_flags, $logon_type,
        $null, $lp_command_line, $lp_current_directory, $null, $exec_wrapper)
    Write-AnsibleLog "INFO - become process complete with rc: $($result.ExitCode)" "become_wrapper"
    $stdout = $result.StandardOut
    try {
        $stdout = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($stdout))
    }
    catch [FormatException] {
        # output wasn't Base64, ignore as it may contain an error message we want to pass to Ansible
        Write-AnsibleLog "WARN - become process stdout was not base64 encoded as expected: $stdout"
    }

    $host.UI.WriteLine($stdout)
    $host.UI.WriteErrorLine($result.StandardError.Trim())
    $host.SetShouldExit($result.ExitCode)
}
catch {
    Write-AnsibleError -Message "internal error: failed to become user '$username'" -ErrorRecord $_
    $host.SetShouldExit(1)
}

Write-AnsibleLog "INFO - ending become_wrapper" "become_wrapper"
