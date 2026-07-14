# (c) 2025 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

[CmdletBinding()]
param (
    [Parameter(Mandatory)]
    [string]
    $Directory,

    [Parameter(Mandatory)]
    [string]
    $Name
)

$path = [Environment]::ExpandEnvironmentVariables($Directory)
$tmp = New-Item -Path $path -Name $Name -ItemType Directory
$tmp.FullName
