using namespace System.Security.Cryptography.X509Certificates
using namespace Invalid.Namespace.That.Does.Not.Exist

$var = 'bar'

Function Test-ScopedUtil {
    <#
    .SYNOPSIS
    Test out module util scoping.
    #>
    [CmdletBinding()]
    param ()

    $missingUsingNamespace = $false
    try {
        # exec_wrapper does 'using namespace System.IO'. This ensures that this
        # hasn't persisted to the module scope and it has it's own set of using
        # types.
        $null = [File]::Exists('test')
    }
    catch {
        $missingUsingNamespace = $true
    }

    [PSCustomObject]@{
        script_var = $script:var
        module_using_namespace = ([X509Certificate2].FullName)
        missing_using_namespace = $missingUsingNamespace
    }
}

Export-ModuleMember -Function Test-ScopedUtil
