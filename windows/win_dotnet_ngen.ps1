#!powershell
# This file is part of Ansible
#
# Copyright 2015, Peter Mounce <public@neverrunwithscissors.com>
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

$ErrorActionPreference = "Stop"

# WANT_JSON
# POWERSHELL_COMMON

$params = Parse-Args $args;
$result = New-Object PSObject;
Set-Attr $result "changed" $false;

function Invoke-NGen
{
    [CmdletBinding()]

    param
    (
       [Parameter(Mandatory=$false, Position=0)] [string] $arity = ""
    )

    if ($arity -eq $null)
    {
        $arity = ""
    }
    $cmd = "$($env:windir)\microsoft.net\framework$($arity)\v4.0.30319\ngen.exe"
    if (test-path $cmd)
    {
        $update = Invoke-Expression "$cmd update /force";
        Set-Attr $result "dotnet_ngen$($arity)_update_exit_code" $lastexitcode
        Set-Attr $result "dotnet_ngen$($arity)_update_output" $update
        $eqi = Invoke-Expression "$cmd executequeueditems";
        Set-Attr $result "dotnet_ngen$($arity)_eqi_exit_code" $lastexitcode
        Set-Attr $result "dotnet_ngen$($arity)_eqi_output" $eqi

        $result.changed = $true
    }
    else
    {
        Write-Host "Not found: $cmd"
    }
}

Try
{
    Invoke-NGen
    Invoke-NGen -arity "64"

    Exit-Json $result;
}
Catch
{
    Fail-Json $result $_.Exception.Message
}
