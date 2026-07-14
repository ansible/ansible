Function Test-PwshUnsigned {
    <#
    .SYNOPSIS
    Tests an unsigned collection pwsh util.
    #>
    [CmdletBinding()]
    param ()

    @{
        language_mode = $ExecutionContext.SessionState.LanguageMode.ToString()
    }
}

Export-ModuleMember -Function Test-PwshUnsigned
