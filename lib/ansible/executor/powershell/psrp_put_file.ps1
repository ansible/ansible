# (c) 2025 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

using namespace System.IO
using namespace System.Reflection
using namespace System.Security.Cryptography

[CmdletBinding()]
param (
    [Parameter(Mandatory = $true)]
    [string]
    $Path,

    [Parameter(Mandatory, ValueFromPipeline)]
    [AllowEmptyString()]
    [string]
    $InputObject
)

begin {
    $fd = [File]::Create($Path)
    $algo = [SHA1]::Create()
    $bytes = @()

    $bindingFlags = [BindingFlags]'NonPublic, Instance'
    Function Get-Property {
        <#
        .SYNOPSIS
        Gets the private/internal property specified of the object passed in.
        #>
        Param (
            [Parameter(Mandatory = $true, ValueFromPipeline = $true)]
            [Object]
            $Object,

            [Parameter(Mandatory = $true, Position = 1)]
            [String]
            $Name
        )

        process {
            $Object.GetType().GetProperty($Name, $bindingFlags).GetValue($Object, $null)
        }
    }

    Function Set-Property {
        <#
        .SYNOPSIS
        Sets the private/internal property specified on the object passed in.
        #>
        Param (
            [Parameter(Mandatory = $true, ValueFromPipeline = $true)]
            [Object]
            $Object,

            [Parameter(Mandatory = $true, Position = 1)]
            [String]
            $Name,

            [Parameter(Mandatory = $true, Position = 2)]
            [AllowNull()]
            [Object]
            $Value
        )

        process {
            $Object.GetType().GetProperty($Name, $bindingFlags).SetValue($Object, $Value, $null)
        }
    }

    Function Get-Field {
        <#
        .SYNOPSIS
        Gets the private/internal field specified of the object passed in.
        #>
        Param (
            [Parameter(Mandatory = $true, ValueFromPipeline = $true)]
            [Object]
            $Object,

            [Parameter(Mandatory = $true, Position = 1)]
            [String]
            $Name
        )

        process {
            $Object.GetType().GetField($Name, $bindingFlags).GetValue($Object)
        }
    }

    # MaximumAllowedMemory is required to be set to so we can send input data that exceeds the limit on a PS
    # Runspace. We use reflection to access/set this property as it is not accessible publicly. This is not ideal
    # but works on all PowerShell versions I've tested with. We originally used WinRS to send the raw bytes to the
    # host but this falls flat if someone is using a custom PS configuration name so this is a workaround. This
    # isn't required for smaller files so if it fails we ignore the error and hope it wasn't needed.
    # https://github.com/PowerShell/PowerShell/blob/c8e72d1e664b1ee04a14f226adf655cced24e5f0/src/System.Management.Automation/engine/serialization.cs#L325
    try {
        $Host | Get-Property 'ExternalHost' |
            Get-Field '_transportManager' |
            Get-Property 'Fragmentor' |
            Get-Property 'DeserializationContext' |
            Set-Property 'MaximumAllowedMemory' $null
    }
    catch {
        # Satisfy pslint, we purposefully ignore this error as it is not critical it works.
        $null = $null
    }
}
process {
    if ($InputObject) {
        $bytes = [Convert]::FromBase64String($InputObject)
        $algo.TransformBlock($bytes, 0, $bytes.Length, $bytes, 0) > $null
        $fd.Write($bytes, 0, $bytes.Length)
    }
}
end {
    $fd.Close()

    $algo.TransformFinalBlock($bytes, 0, 0) > $null
    $hash = [BitConverter]::ToString($algo.Hash).Replace('-', '').ToLowerInvariant()
    "{`"sha1`":`"$hash`"}"
}
