if ($PSVersionTable.PSVersion -lt [Version]"5.1") {
    '{"failed":true,"msg":"Ansible requires PowerShell v5.1"}'
    exit 1
}

# First input is a JSON string with name/script/params of what to run. This
# ends with a line of 4 null bytes and subsequent input is piped to the code
# provided.
$codeJson = foreach ($in in $input) {
    if ([string]::Equals($in, "`0`0`0`0")) {
        break
    }
    $in
}
$code = ConvertFrom-Json -InputObject $codeJson
$splat = @{}
foreach ($obj in $code.params.PSObject.Properties) {
    $splat[$obj.Name] = $obj.Value
}

$cmd = [System.Management.Automation.Language.Parser]::ParseInput(
    $code.script,
    "$($code.name).ps1", # Name is used in stack traces.
    [ref]$null,
    [ref]$null).GetScriptBlock()

$input | & $cmd @splat
