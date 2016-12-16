#!powershell

#this file is part of Ansible
#Copyright © 2015 Sam Liu <sam.liu@activenetwork.com>

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

# WANT_JSON
# POWERSHELL_COMMON

$params = Parse-Args $args;

$result = New-Object psobject @{
    win_file_version = New-Object psobject
    changed = $false
}

$path = Get-AnsibleParam $params "path" -failifempty $true -resultobj $result

If (-Not (Test-Path -Path $path -PathType Leaf)){
    Fail-Json $result "Specfied path $path does exist or is not a file."
}
$ext = [System.IO.Path]::GetExtension($path)
If ( $ext -notin '.exe', '.dll'){
    Fail-Json $result "Specfied path $path is not a vaild file type; must be DLL or EXE."
}

Try {
    $_version_fields = [System.Diagnostics.FileVersionInfo]::GetVersionInfo($path)
    $file_version = $_version_fields.FileVersion
    If ($file_version -eq $null){
        $file_version = ''
    }
    $product_version = $_version_fields.ProductVersion
    If ($product_version -eq $null){
        $product_version= ''
    }
    $file_major_part = $_version_fields.FileMajorPart
    If ($file_major_part -eq $null){
        $file_major_part= ''
    }
    $file_minor_part = $_version_fields.FileMinorPart
    If ($file_minor_part -eq $null){
        $file_minor_part= ''
    }
    $file_build_part = $_version_fields.FileBuildPart
    If ($file_build_part -eq $null){
        $file_build_part = ''
    }
    $file_private_part = $_version_fields.FilePrivatePart
    If ($file_private_part -eq $null){
        $file_private_part = ''
    }
}
Catch{
    Fail-Json $result "Error: $_.Exception.Message"
}

Set-Attr $result.win_file_version "path" $path.toString()
Set-Attr $result.win_file_version "file_version" $file_version.toString()
Set-Attr $result.win_file_version "product_version" $product_version.toString()
Set-Attr $result.win_file_version "file_major_part" $file_major_part.toString()
Set-Attr $result.win_file_version "file_minor_part" $file_minor_part.toString()
Set-Attr $result.win_file_version "file_build_part" $file_build_part.toString()
Set-Attr $result.win_file_version "file_private_part" $file_private_part.toString()
Exit-Json $result;

