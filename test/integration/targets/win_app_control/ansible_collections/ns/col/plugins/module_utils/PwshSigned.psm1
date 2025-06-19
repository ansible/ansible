Function Test-PwshSigned {
    <#
    .SYNOPSIS
    Tests a signed collection pwsh util.
    #>
    [CmdletBinding()]
    param ()

    @{
        language_mode = $ExecutionContext.SessionState.LanguageMode.ToString()
    }
}

Export-ModuleMember -Function Test-PwshSigned
