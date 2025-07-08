# (c) 2025 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

using namespace System.IO

[CmdletBinding()]
param (
    [Parameter(Mandatory)]
    [string]
    $Path,

    [Parameter(Mandatory)]
    [int]
    $BufferSize,

    [Parameter(Mandatory)]
    [long]
    $Offset
)

if (Test-Path -LiteralPath $Path -PathType Leaf) {
    $stream = [FileStream]::new(
        $Path,
        [FileMode]::Open,
        [FileAccess]::Read,
        [FileShare]::ReadWrite)

    try {
        $null = $stream.Seek($Offset, [SeekOrigin]::Begin)
        $buffer = [byte[]]::new($BufferSize)
        $read = $stream.Read($buffer, 0, $buffer.Length)
        if ($read) {
            [Convert]::ToBase64String($buffer, 0, $read)
        }
    }
    finally {
        $stream.Dispose()
    }
}
elseif (Test-Path -LiteralPath $Path -PathType Container) {
    "[DIR]"
}
else {
    $host.UI.WriteErrorLine("$Path does not exist")
    exit 1
}
