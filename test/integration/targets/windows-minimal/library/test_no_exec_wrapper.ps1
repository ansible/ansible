#!powershell

$res = @{
    changed = $false
    msg = "test msg"
    path = $PSCommandPath
    args = $args
    arg0 = [string](Get-Content -LiteralPath $args[0] -Raw)
}

ConvertTo-Json $res
