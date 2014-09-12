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

if ($params.package)
{
    $package = $params.package
}
else
{
    Fail-Json $result "missing required argument: package"
}

if ($params.force)
{
    $force = $params.force | ConvertTo-Bool
}
else
{
    $force = $false
}

if ($params.version)
{
    $version = $params.version
}
else
{
    $version = $null
}

if ($params.showlog)
{
    $showlog = $params.showlog | ConvertTo-Bool
}
else
{
    $showlog = $null
}

if ($params.state)
{
    $state = $params.state.ToString().ToLower()
    if (($state -ne "present") -and ($state -ne "absent"))
    {
        Fail-Json $result "state is $state; must be present or absent"
    }
}
else
{
    $state = "present"
}

$ChocoAlreadyInstalled = get-command choco -ErrorAction 0
if ($ChocoAlreadyInstalled -eq $null)
{
    #We need to install chocolatey
    $install_choco_result = iex ((new-object net.webclient).DownloadString("https://chocolatey.org/install.ps1"))
    $result.changed = $true
    $executable = "C:\ProgramData\chocolatey\bin\choco.exe"
}
else
{
    $executable = "choco.exe"
}

if ($params.source)
{
    $source = $params.source.ToString().ToLower()
    if (($source -ne "chocolatey") -and ($source -ne "webpi") -and ($source -ne "windowsfeatures"))
    {
        Fail-Json $result "source is $source - must be one of chocolatey, webpi or windowsfeatures."
    }
}
elseif (!$params.source)
{
    $source = "chocolatey"
}

if ($source -eq "webpi")
{
    # check whether 'webpi' installation source is available; if it isn't, install it
    $webpi_check_cmd = "$executable list webpicmd -localonly"
    $webpi_check_result = invoke-expression $webpi_check_cmd
    Set-Attr $result "chocolatey_bootstrap_webpi_check_cmd" $webpi_check_cmd
    Set-Attr $result "chocolatey_bootstrap_webpi_check_log" $webpi_check_result
    if (
        (
            ($webpi_check_result.GetType().Name -eq "String") -and
            ($webpi_check_result -match "No packages found")
        ) -or
        ($webpi_check_result -contains "No packages found.")
    )
    {
        #lessmsi is a webpicmd dependency, but dependency resolution fails unless it's installed separately
        $lessmsi_install_cmd = "$executable install lessmsi"
        $lessmsi_install_result = invoke-expression $lessmsi_install_cmd
        Set-Attr $result "chocolatey_bootstrap_lessmsi_install_cmd" $lessmsi_install_cmd
        Set-Attr $result "chocolatey_bootstrap_lessmsi_install_log" $lessmsi_install_result

        $webpi_install_cmd = "$executable install webpicmd"
        $webpi_install_result = invoke-expression $webpi_install_cmd
        Set-Attr $result "chocolatey_bootstrap_webpi_install_cmd" $webpi_install_cmd
        Set-Attr $result "chocolatey_bootstrap_webpi_install_log" $webpi_install_result

        if (($webpi_install_result | select-string "already installed").length -gt 0)
        {
            #no change
        }
        elseif (($webpi_install_result | select-string "webpicmd has finished successfully").length -gt 0)
        {
            $result.changed = $true
        }
        else
        {
            Fail-Json $result "WebPI install error: $webpi_install_result"
        }
    }
}
$expression = $executable
if ($state -eq "present")
{
    $expression += " install $package"
}
elseif ($state -eq "absent")
{
    $expression += " uninstall $package"
}
if ($force)
{
    if ($state -eq "present")
    {
        $expression += " -force"
    }
}
if ($version)
{
    $expression += " -version $version"
}
if ($source -eq "chocolatey")
{
    $expression += " -source https://chocolatey.org/api/v2/"
}
elseif (($source -eq "windowsfeatures") -or ($source -eq "webpi"))
{
    $expression += " -source $source"
}

Set-Attr $result "chocolatey command" $expression
$op_result = invoke-expression $expression
if ($state -eq "present")
{
    if (
        (($op_result | select-string "already installed").length -gt 0) -or
        # webpi has different text output, and that doesn't include the package name but instead the human-friendly name
        (($op_result | select-string "No products to be installed").length -gt 0)
    )
    {
        #no change
    }
    elseif (
        (($op_result | select-string "has finished successfully").length -gt 0) -or
        # webpi has different text output, and that doesn't include the package name but instead the human-friendly name
        (($op_result | select-string "Install of Products: SUCCESS").length -gt 0)
    )
    {
        $result.changed = $true
    }
    else
    {
        Fail-Json $result "Install error: $op_result"
    }
}
elseif ($state -eq "absent")
{
    $op_result = invoke-expression "$executable uninstall $package"
    # HACK: Misleading - 'Uninstalling from folder' appears in output even when package is not installed, hence order of checks this way
    if (
        (($op_result | select-string "not installed").length -gt 0) -or
        (($op_result | select-string "Cannot find path").length -gt 0)
    )
    {
        #no change
    }
    elseif (($op_result | select-string "Uninstalling from folder").length -gt 0)
    {
        $result.changed = $true
    }
    else
    {
        Fail-Json $result "Uninstall error: $op_result"
    }
}

if ($showlog)
{
    Set-Attr $result "chocolatey_log" $op_result
}
Set-Attr $result "chocolatey_success" "true"

Exit-Json $result;
