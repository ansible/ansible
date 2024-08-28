try { [Console]::InputEncoding = [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding } catch { $null = $_ }

if ($PSVersionTable.PSVersion -lt [Version]"3.0") {
    '{"failed":true,"msg":"Ansible requires PowerShell v3.0 or newer"}'
    exit 1
}

$exec_wrapper_str = $input | Out-String
$split_parts = $exec_wrapper_str.Split(@("`0`0`0`0"), 2, [StringSplitOptions]::RemoveEmptyEntries)
If (-not $split_parts.Length -eq 2) { throw "invalid payload" }
Set-Variable -Name json_raw -Value $split_parts[1]
& ([ScriptBlock]::Create($split_parts[0]))
