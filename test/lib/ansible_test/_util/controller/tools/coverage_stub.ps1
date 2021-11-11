<#
.SYNOPSIS
Gets the lines to hit from a sourcefile for coverage stubs.
#>
[CmdletBinding()]
param (
    [Parameter(Mandatory, ValueFromRemainingArguments)]
    [String[]]
    $Path
)

$stubInfo = @(
    foreach ($sourcePath in $Path) {
        # Default is to just no lines for missing files
        [Collections.Generic.HashSet[int]]$lines = @()

        if (Test-Path -LiteralPath $sourcePath) {
            $code = [ScriptBlock]::Create([IO.File]::ReadAllText($sourcePath))

            # We set our breakpoints with this predicate so our stubs should match
            # that logic.
            $predicate = {
                $args[0] -is [System.Management.Automation.Language.CommandBaseAst]
            }
            $cmds = $code.Ast.FindAll($predicate, $true)

            # We only care about unique lines not multiple commands on 1 line.
            $lines = @(foreach ($cmd in $cmds) {
                    $cmd.Extent.StartLineNumber
                })
        }

        [PSCustomObject]@{
            Path = $sourcePath
            Lines = $lines
        }
    }
)

ConvertTo-Json -InputObject $stubInfo -Depth 2 -Compress
