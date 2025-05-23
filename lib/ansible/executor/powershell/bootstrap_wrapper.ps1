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

$filePath = $null
try {
    $cmd = if ($ExecutionContext.SessionState.LanguageMode -eq 'FullLanguage') {
        # In FLM we can just invoke the code as a scriptblock without touching the
        # disk.
        [System.Management.Automation.Language.Parser]::ParseInput(
            $code.script,
            "$($code.name).ps1", # Name is used in stack traces.
            [ref]$null,
            [ref]$null).GetScriptBlock()
    }
    else {
        # CLM needs to execute code from a file for it to run in FLM when trusted.
        # Set-Item on 5.1 doesn't have a way to use UTF-8 without a BOM but luckily
        # New-Item does that by default for both 5.1 and 7. We need to ensure we
        # use UTF-8 without BOM so the signature is correct.
        $filePath = Join-Path -Path $env:TEMP -ChildPath "$($code.name)-$(New-Guid).ps1"
        $null = New-Item -Path $filePath -Value $code.script -ItemType File -Force

        $filePath
    }

    $input | & $cmd @splat
}
finally {
    if ($filePath -and (Test-Path -LiteralPath $filePath)) {
        Remove-Item -LiteralPath $filePath -Force
    }
}
