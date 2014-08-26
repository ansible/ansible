#!powershell
# This file is part of Ansible
#
# Copyright 2014, Trond Hindenes <trond@hindenes.com>
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

# WANT_JSON
# POWERSHELL_COMMON

$params = Parse-Args $args;
$result = New-Object PSObject;
Set-Attr $result "changed" $false;

If ($params.package) {
    $package = $params.package
}
Else {
    Fail-Json $result "missing required argument: package"
}

If ($params.force) {
    $force = $params.force | ConvertTo-Bool
}
Else
{
    $force = $false
}


If ($params.version) {
    $version = $params.version
}
Else
{
    $version = $null
}

If ($params.showlog) {
    $showlog = $params.showlog | ConvertTo-Bool
}
Else
{
    $showlog = $null
}


$ChocoAlreadyInstalled = get-command choco -ErrorAction 0
if ($ChocoAlreadyInstalled -eq $null)
{
    #We need to install chocolatey
    iex ((new-object net.webclient).DownloadString('https://chocolatey.org/install.ps1'))
    $result.changed -eq $true
    $executable = "C:\ProgramData\chocolatey\bin\choco.exe"
}
Else
{
    $executable = "choco.exe"
}

If ($params.source) {
    $source = $params.source.ToString().ToLower()
    If (($source -ne 'chocolatey') -and ($source -ne 'webpi') -and ($source -ne 'windowsfeatures')) {
        Fail-Json $result "source is '$source'; must be one of 'default', 'webpi' or 'windowsfeatures'."
    }
    If ($source -eq 'chocolatey') {
        $source = "https://chocolatey.org/api/v2/"
    }
}
Elseif (!$params.source)
{
    $source = "https://chocolatey.org/api/v2/"
}

if ($params.source -eq "webpi")
{
    # check whether webpi source is available; if it isn't, install it
    $local = & executable list webpicmd -localonly
    $ll = ($local.count) - 1
    if ($local[0] -like "No packages found") {
      & $executable install webpicmd
    }
}

####### Install
if (($force) -and ($version))
{
    $installresult = & $executable install $package -version $version -force
}
Elseif (($force) -and (!$version))
{
    $installresult = & $executable install $package -force
}
Elseif (!($force) -and ($version))
{
    $installresult = & $executable install $package -version $version
}
Else
{
    $installresult = & $executable install $package
}

$lastline = ($installresult.count) - 1
if ($installresult[1] -match "already installed")
{
    #no change
}
elseif ($installresult[$lastline] -like "finished installing*")
{
    $result.changed = $true
}
Else
{
    Fail-Json $result "something bad happened: $installresult"
}

Set-Attr $result "chocolatey_success" "true"
if ($showlog)
{
    Set-Attr $result "chocolatey_log" $installresult
}

Exit-Json $result;
