# (c) 2025 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

using namespace System.IO

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]
    $Path,

    [Parameter(Mandatory)]
    [int]
    $BufferSize
)

if (Test-Path -LiteralPath $Path -PathType Leaf) {
    "[FILE]"

    $fs = [FileStream]::new(
        $path,
        [FileMode]::Open,
        [FileAccess]::Read,
        [FileShare]::Read)

    try {
        $buffer = [byte[]]::new($BufferSize)
        while ($read = $fs.Read($buffer, 0, $buffer.Length)) {
            [Convert]::ToBase64String($buffer, 0, $read)
        }
    }
    finally {
        $fs.Dispose()
    }
}
elseif (Test-Path -LiteralPath $Path -PathType Container) {
    "[DIR]"
}
else {
    Write-Error -Message "$Path does not exist"
}
