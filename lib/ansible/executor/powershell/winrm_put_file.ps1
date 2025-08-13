# (c) 2025 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

using namespace System.IO
using namespace System.Security.Cryptography

[CmdletBinding()]
param (
    [Parameter(Mandatory)]
    [string]
    $Path,

    [Parameter(ValueFromPipeline)]
    [string]
    $InputObject
)

begin {
    $fd = [File]::Create($Path)
    $sha1 = [SHA1]::Create()
    $bytes = @() #initialize for empty file case
}

process {
    $bytes = [Convert]::FromBase64String($InputObject)
    $null = $sha1.TransformBlock($bytes, 0, $bytes.Length, $bytes, 0)
    $fd.Write($bytes, 0, $bytes.Length)
}

end {
    $fd.Dispose()
    $null = $sha1.TransformFinalBlock($bytes, 0, 0)
    $hash = [BitConverter]::ToString($sha1.Hash).Replace("-", "").ToLowerInvariant()

    '{{"sha1":"{0}"}}' -f $hash
}
