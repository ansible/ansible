#Requires -Version 6
#Requires -Modules PSScriptAnalyzer, PSSA-PSCustomUseLiteralPath

$ErrorActionPreference = "Stop"
$WarningPreference = "Stop"

Function Convert-OutputObject {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory=$true, ValueFromPipeline=$true)]
        [AllowNull()]
        [object]
        $InputObject,

        [Parameter(Mandatory=$true)]
        [int]
        $Depth
    )

    begin {
        $childDepth = $Depth - 1
    }

    process {
        if ($null -eq $InputObject) {
            $null
        }
        elseif ($InputObject -is [DateTime] -or $InputObject -is [DateTimeOffset]) {
            # Behaviour of ConvertTo-Json with date types differs across versions, just use ISO 8601
            $InputObject.ToString('o')
        }
        elseif ($InputObject -is [Type]) {
            # Type contains lots of properties, some with circular references
            $InputObject.FullName
        }
        elseif ($InputObject -is [switch]) {
            $InputObject.IsPresent
        }
        elseif ($InputObject -is [string]) {
            # A string is not a ValueType but should be handled as one
            $InputObject
        }
        elseif ($InputObject.GetType().IsValueType) {
            # We want to display just this value and not any properties it has (if any).
            $InputObject
        }
        elseif ($Depth -lt 0) {
            # This must occur after the above to ensure ints and other ValueTypes are preserved as is.
            [string]$InputObject
        }
        elseif ($InputObject -is [Collections.IList]) {
            ,@(foreach ($obj in $InputObject) {
                Convert-OutputObject -InputObject $obj -Depth $childDepth
            })
        }
        elseif ($InputObject -is [Collections.IDictionary]) {
            $newObj = @{}

            # Replicate ConvertTo-Json, props are replaced by keys if they share the same name. We only want ETS
            # properties as well.
            foreach ($prop in $InputObject.PSObject.Properties) {
                if ($prop.MemberType -notin @('AliasProperty', 'ScriptProperty', 'NoteProperty')) {
                    continue
                }
                $newObj[$prop.Name] = Convert-OutputObject -InputObject $prop.Value -Depth $childDepth
            }
            foreach ($kvp in $InputObject.GetEnumerator()) {
                $newObj[$kvp.Key] = Convert-OutputObject -InputObject $kvp.Value -Depth $childDepth
            }
            $newObj
        }
        else {
            $newObj = @{}
            foreach ($prop in $InputObject.PSObject.Properties) {
                $newObj[$prop.Name] = Convert-OutputObject -InputObject $prop.Value -Depth $childDepth
            }
            $newObj
        }
    }
}

# Until https://github.com/PowerShell/PSScriptAnalyzer/issues/1217 is fixed we need to import Pester if it's
# available.
if (Get-Module -Name Pester -ListAvailable -ErrorAction SilentlyContinue) {
    Import-Module -Name Pester
}

$LiteralPathRule = Import-Module -Name PSSA-PSCustomUseLiteralPath -PassThru
$LiteralPathRulePath = Join-Path -Path $LiteralPathRule.ModuleBase -ChildPath $LiteralPathRule.RootModule

$PSSAParams = @{
    CustomRulePath = @($LiteralPathRulePath)
    IncludeDefaultRules = $true
    Setting = (Join-Path -Path $PSScriptRoot -ChildPath "settings.psd1")
}

$Results = @(ForEach ($Path in $Args) {
    $Retries = 3

    Do {
        Try {
            Invoke-ScriptAnalyzer -Path $Path @PSSAParams 3> $null
            $Retries = 0
        }
        Catch {
            If (--$Retries -le 0) {
                Throw
            }
        }
    }
    Until ($Retries -le 0)
})

ConvertTo-Json -InputObject (Convert-OutputObject -InputObject $Results -Depth 2) -Depth 2
