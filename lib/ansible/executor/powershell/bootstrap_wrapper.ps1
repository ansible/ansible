param([string]$InputFile)

if ($PSVersionTable.PSVersion -lt [Version]"5.1") {
    '{"failed":true,"msg":"Ansible requires PowerShell v5.1"}'
    exit 1
}

$isClm = $ExecutionContext.SessionState.LanguageMode -ne 'FullLanguage'

# Input is either from stdin or a separate file for non-pipelining scenarios.
if ($InputFile) {
    if ($isClm) {
        # While this reads it all in memory there is no other way to avoid this
        # if running in CLM. Only way to avoid this is to have the caller start
        # the process with the content's piped but that is hard to do cross
        # platform.
        Get-Content -LiteralPath $InputFile -Encoding UTF8 |
            & $MyInvocation.MyCommand.ScriptBlock
        return
    }
    else {
        # .GetEnumerator() is important to ensure we stream the lines rather
        # than read it all here.
        $inputData = [System.IO.File]::ReadLines(
            $InputFile,
            [System.Text.Encoding]::UTF8).GetEnumerator()
    }
}
else {
    $inputData = $input
}

# First input is a JSON string with name/script/params of what to run. This
# ends with a line of 4 null bytes and subsequent input is piped to the code
# provided.
$codeJson = foreach ($in in $inputData) {
    if ([string]::Equals($in, "`0`0`0`0")) {
        break
    }
    $in
}
$code = $codeJson | ConvertFrom-Json
$splat = @{}
foreach ($obj in $code.params.PSObject.Properties) {
    $splat[$obj.Name] = $obj.Value
}

$filePath = $null
try {
    $cmd = if ($isClm) {
        # CLM needs to execute code from a file for it to run in FLM when trusted.
        # Set-Item on 5.1 doesn't have a way to use UTF-8 without a BOM but luckily
        # New-Item does that by default for both 5.1 and 7. We need to ensure we
        # use UTF-8 without BOM so the signature is correct.
        $filePath = Join-Path -Path $env:TEMP -ChildPath "$($code.name)-$(New-Guid).ps1"
        $null = New-Item -Path $filePath -Value $code.script -ItemType File -Force

        $filePath
    }
    else {
        # In FLM we can just invoke the code as a scriptblock without touching the
        # disk.
        [System.Management.Automation.Language.Parser]::ParseInput(
            $code.script,
            "$($code.name).ps1", # Name is used in stack traces.
            [ref]$null,
            [ref]$null).GetScriptBlock()
    }

    $inputData | & $cmd @splat
}
finally {
    if ($filePath -and (Test-Path -LiteralPath $filePath)) {
        Remove-Item -LiteralPath $filePath -Force
    }
}
