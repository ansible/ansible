& {
    $ErrorActionPreference = 'Stop'

    $codeJson = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{{ MANIFEST }}'))
    $code = $codeJson | ConvertFrom-Json
    $splat = @{}

    foreach ($obj in $code.params.PSObject.Properties) {
        $splat[$obj.Name] = $obj.Value
    }

    $errors = @()
    $ast = [System.Management.Automation.Language.Parser]::ParseInput($code.script, $code.path, [ref]$null, [ref]$errors)

    if ($errors) {
        throw "Failed to parse PowerShell script: $errors"
    }

    $cmd = $ast.GetScriptBlock()

    & $cmd @splat
}
