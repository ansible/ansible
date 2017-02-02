#!powershell

# (c) 2017, Anatoliy Ivashina <tivrobo@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

# WANT_JSON
# POWERSHELL_COMMON

$params = Parse-Args $args;

$result = @{
    win_git = @{
        name              = $null
        dest              = $null
        replace_dest      = $false
        accept_hostkey    = $false
    }
    msg = $null
    changed = $false
}

$name = Get-AnsibleParam -obj $params -name "name" -failifempty $true -type "str"
$dest = Get-AnsibleParam -obj $params -name "dest" -failifempty $true -type "path"
$replace_dest = Get-AnsibleParam -obj $params -name "replace_dest" -default $false -type "bool"
$accept_hostkey = Get-AnsibleParam -obj $params -name "accept_hostkey" -default $false -type "bool"
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -default $false -type "bool"

# Add Git to PATH variable
$env:Path += ";" + "C:\Program Files\Git\usr\bin"
$env:Path += ";" + "C:\Program Files (x86)\Git\usr\bin"

# Functions
Function Find-Command
{
    [CmdletBinding()]
    param(
      [Parameter(Mandatory=$true, Position=0)] [string] $command
    )
    $installed = get-command $command -erroraction Ignore
    write-verbose "$installed"
    if ($installed)
    {
        return $installed
    }
    return $null
}

Function FindGit
{
    [CmdletBinding()]
    param()
    $p = Find-Command "git.exe"
    if ($p -ne $null)
    {
        return $p
    }
    $a = Find-Command "C:\Program Files\Git\bin\git.exe"
    if ($a -ne $null)
    {
        return $a
    }
    Throw "git.exe is not installed. It must be installed (use chocolatey)"
}

# Check destination folder, create if not exist
function PrepareDestination
{
    [CmdletBinding()]
    param()
    if (Test-Path $dest) {
        $directoryInfo = Get-ChildItem $dest -Force | Measure-Object
        if ($directoryInfo.Count -ne 0) {
            if ($replace_dest) {
                # Clean destination
                Remove-Item $dest -Force -Recurse | Out-Null
            }
            else {
                Throw "Destination folder not empty!"
            }
        }
    }
    else {
        # Create destination folder
        New-Item $dest -ItemType Directory -Force | Out-Null
    }
}

# SSH Keys
function CheckSshKnownHosts
{
    [CmdletBinding()]
    param()
    # Get the Git Hostname
    $gitServer = $($name -replace "^(\w+)\@([\w-_\.]+)\:(.*)$", '$2')
    & cmd /c ssh-keygen.exe -F $gitServer | Out-Null
    $rc = $LASTEXITCODE
    
    if ($rc -ne 0)
    {
        # Host is unknown
        if ($accept_hostkey)
        {
            & cmd /c ssh-keyscan.exe -t ecdsa-sha2-nistp256 $gitServer | Out-File -Append "$env:Userprofile\.ssh\known_hosts"
        }
        else
        {
            Trow "Host is not known!"
        }
    }
}

function CheckSshIdentity
{
    [CmdletBinding()]
    param()

    & cmd /c git.exe ls-remote $name | Out-Null
    $rc = $LASTEXITCODE
    if ($rc -ne 0) {
        Trow "Something wrong with connection!"
    }
}

# Build Arguments
$git_opts = @()

$git_opts += "clone"

if ($name -eq ($null -or "")) {
    Fail-Json $result "Repository cannot be empty or `$null"
}
$git_opts += $name
$result.win_git.name = $name

$git_opts += $dest
$result.win_git.dest = $dest

$result.win_git.replace_dest = $replace_dest
$result.win_git.accept_hostkey = $accept_hostkey

$git_output = ""
$rc = 0

If ($check_mode) {
    $git_output = "Would have copied the contents of $name to $dest"
    $rc = 0
}
Else {
    Try {

        FindGit
        PrepareDestination
        CheckSshKnownHosts
        CheckSshIdentity

        &git $git_opts | Tee-Object -Variable git_output | Out-Null
        $rc = $LASTEXITCODE
    }
    Catch {
        $ErrorMessage = $_.Exception.Message
        Fail-Json $result "Error cloning $name to $dest! Msg: $ErrorMessage"
    }
}

$result.win_git.return_code = $rc
$result.win_git.output = $git_output

$cmd_msg = "Success"
If ($rc -eq 0) {
    $cmd_msg = "Successfully cloned $name into $dest."
    $changed = $true
}
Else {
    $error_msg = SearchForError $git_output "Fatal Error!"
    Fail-Json $result $error_msg
}

$result.msg = $cmd_msg
$result.changed = $changed

Exit-Json $result