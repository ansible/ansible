#!powershell

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$params = Parse-Args $args -supports_check_mode $true;
$src = Get-AnsibleParam -obj $params -name "src" -type "path" -aliases "path" -failifempty $true;

$result = @{
    changed = $false;
}

If (Test-Path -Path $src -PathType Leaf)
{
    $bytes = [System.IO.File]::ReadAllBytes($src);
    $result.content = [System.Convert]::ToBase64String($bytes);
    $result.encoding = "base64";
    Exit-Json $result;
}
ElseIf (Test-Path -Path $src -PathType Container)
{
    Fail-Json $result "Path $src is a directory";
}
Else
{
    Fail-Json $result "Path $src is not found";
}
