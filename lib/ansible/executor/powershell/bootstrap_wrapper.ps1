&chcp.com 65001 > $null
$exec_wrapper_str = $input | Out-String
$split_parts = $exec_wrapper_str.Split(@("`0`0`0`0"), 2, [StringSplitOptions]::RemoveEmptyEntries)
If (-not $split_parts.Length -eq 2) { throw "invalid payload" }
Set-Variable -Name json_raw -Value $split_parts[1]
$exec_wrapper = [ScriptBlock]::Create($split_parts[0])
&$exec_wrapper
