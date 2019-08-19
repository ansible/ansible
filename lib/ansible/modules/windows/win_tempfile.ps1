#!powershell

# Copyright: (c) 2017, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic

Function New-TempFile {
    Param ([string]$path, [string]$prefix, [string]$suffix, [string]$type, [bool]$checkmode)
    $temppath = $null
    $curerror = $null
    $attempt = 0

    # Since we don't know if the file already exists, we try 5 times with a random name
    do {
        $attempt += 1
        $randomname = [System.IO.Path]::GetRandomFileName()
        $temppath = (Join-Path -Path $path -ChildPath "$prefix$randomname$suffix")
        Try {
            $file = New-Item -Path $temppath -ItemType $type -WhatIf:$checkmode
            # Makes sure we get the full absolute path of the created temp file and not a relative or DOS 8.3 dir
            if (-not $checkmode) {
                $temppath = $file.FullName
            } else {
                # Just rely on GetFulLpath for check mode
                $temppath = [System.IO.Path]::GetFullPath($temppath)
            }
        } Catch {
            $temppath = $null
            $curerror = $_
        }
    } until (($null -ne $temppath) -or ($attempt -ge 5))

    # If it fails 5 times, something is wrong and we have to report the details
    if ($null -eq $temppath) {
        $module.FailJson("No random temporary file worked in $attempt attempts. Error: $($curerror.Exception.Message)", $curerror)
    }

    return $temppath.ToString()
}

$spec = @{
    options = @{
        path = @{ type='path'; default='%TEMP%'; aliases=@( 'dest' ) }
        state = @{ type='str'; default='file'; choices=@( 'directory', 'file') }
        prefix = @{ type='str'; default='ansible.' }
        suffix = @{ type='str' }
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$path = $module.Params.path
$state = $module.Params.state
$prefix = $module.Params.prefix
$suffix = $module.Params.suffix

# Expand environment variables on non-path types
if ($null -ne $prefix) {
    $prefix = [System.Environment]::ExpandEnvironmentVariables($prefix)
}
if ($null -ne $suffix) {
    $suffix = [System.Environment]::ExpandEnvironmentVariables($suffix)
}

$module.Result.changed = $true
$module.Result.state = $state

$module.Result.path = New-TempFile -Path $path -Prefix $prefix -Suffix $suffix -Type $state -CheckMode $module.CheckMode

$module.ExitJson()
