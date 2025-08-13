# (c) 2025 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

[CmdletBinding()]
param (
    [Parameter(Mandatory)]
    [string]
    $Path
)

$userProfile = [Environment]::GetFolderPath([Environment+SpecialFolder]::UserProfile)
if ($Path -eq '~') {
    $userProfile
}
elseif ($Path.StartsWith(('~\'))) {
    Join-Path -Path $userProfile -ChildPath $Path.Substring(2)
}
else {
    $Path
}
