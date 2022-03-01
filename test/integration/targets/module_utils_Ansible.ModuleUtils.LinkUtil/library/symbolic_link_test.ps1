#!powershell

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.LinkUtil
#Requires -Module Ansible.ModuleUtils.CommandUtil

$ErrorActionPreference = 'Stop'

$path = Join-Path -Path ([System.IO.Path]::GetFullPath($env:TEMP)) -ChildPath '.ansible .ÅÑŚÌβŁÈ [$!@^&test(;)]'

$folder_target = "$path\folder"
$file_target = "$path\file"
$symlink_file_path = "$path\file-symlink"
$symlink_folder_path = "$path\folder-symlink"
$hardlink_path = "$path\hardlink"
$hardlink_path_2 = "$path\hardlink2"
$junction_point_path = "$path\junction"

if (Test-Path -LiteralPath $path) {
    # Remove-Item struggles with broken symlinks, rely on trusty rmdir instead
    Run-Command -command "cmd.exe /c rmdir /S /Q `"$path`"" > $null
}
New-Item -Path $path -ItemType Directory | Out-Null
New-Item -Path $folder_target -ItemType Directory | Out-Null
New-Item -Path $file_target -ItemType File | Out-Null
Set-Content -LiteralPath $file_target -Value "a"

Function Assert-Equal($actual, $expected) {
    if ($actual -ne $expected) {
        Fail-Json @{} "actual != expected`nActual: $actual`nExpected: $expected"
    }
}

Function Assert-True($expression, $message) {
    if ($expression -ne $true) {
        Fail-Json @{} $message
    }
}

# need to manually set this
Load-LinkUtils

# path is not a link
$no_link_result = Get-Link -link_path $path
Assert-True -expression ($null -eq $no_link_result) -message "did not return null result for a non link"

# fail to create hard link pointed to a directory
try {
    New-Link -link_path "$path\folder-hard" -link_target $folder_target -link_type "hard"
    Assert-True -expression $false -message "creation of hard link should have failed if target was a directory"
}
catch {
    Assert-Equal -actual $_.Exception.Message -expected "cannot set the target for a hard link to a directory"
}

# fail to create a junction point pointed to a file
try {
    New-Link -link_path "$path\junction-fail" -link_target $file_target -link_type "junction"
    Assert-True -expression $false -message "creation of junction point should have failed if target was a file"
}
catch {
    Assert-Equal -actual $_.Exception.Message -expected "cannot set the target for a junction point to a file"
}

# fail to create a symbolic link with non-existent target
try {
    New-Link -link_path "$path\symlink-fail" -link_target "$path\fake-folder" -link_type "link"
    Assert-True -expression $false -message "creation of symbolic link should have failed if target did not exist"
}
catch {
    Assert-Equal -actual $_.Exception.Message -expected "link_target '$path\fake-folder' does not exist, cannot create link"
}

# create recursive symlink
Run-Command -command "cmd.exe /c mklink /D symlink-rel folder" -working_directory $path | Out-Null
$rel_link_result = Get-Link -link_path "$path\symlink-rel"
Assert-Equal -actual $rel_link_result.Type -expected "SymbolicLink"
Assert-Equal -actual $rel_link_result.SubstituteName -expected "folder"
Assert-Equal -actual $rel_link_result.PrintName -expected "folder"
Assert-Equal -actual $rel_link_result.TargetPath -expected "folder"
Assert-Equal -actual $rel_link_result.AbsolutePath -expected $folder_target
Assert-Equal -actual $rel_link_result.HardTargets -expected $null

# create a symbolic file test
New-Link -link_path $symlink_file_path -link_target $file_target -link_type "link"
$file_link_result = Get-Link -link_path $symlink_file_path
Assert-Equal -actual $file_link_result.Type -expected "SymbolicLink"
Assert-Equal -actual $file_link_result.SubstituteName -expected "\??\$file_target"
Assert-Equal -actual $file_link_result.PrintName -expected $file_target
Assert-Equal -actual $file_link_result.TargetPath -expected $file_target
Assert-Equal -actual $file_link_result.AbsolutePath -expected $file_target
Assert-Equal -actual $file_link_result.HardTargets -expected $null

# create a symbolic link folder test
New-Link -link_path $symlink_folder_path -link_target $folder_target -link_type "link"
$folder_link_result = Get-Link -link_path $symlink_folder_path
Assert-Equal -actual $folder_link_result.Type -expected "SymbolicLink"
Assert-Equal -actual $folder_link_result.SubstituteName -expected "\??\$folder_target"
Assert-Equal -actual $folder_link_result.PrintName -expected $folder_target
Assert-Equal -actual $folder_link_result.TargetPath -expected $folder_target
Assert-Equal -actual $folder_link_result.AbsolutePath -expected $folder_target
Assert-Equal -actual $folder_link_result.HardTargets -expected $null

# create a junction point test
New-Link -link_path $junction_point_path -link_target $folder_target -link_type "junction"
$junction_point_result = Get-Link -link_path $junction_point_path
Assert-Equal -actual $junction_point_result.Type -expected "JunctionPoint"
Assert-Equal -actual $junction_point_result.SubstituteName -expected "\??\$folder_target"
Assert-Equal -actual $junction_point_result.PrintName -expected $folder_target
Assert-Equal -actual $junction_point_result.TargetPath -expected $folder_target
Assert-Equal -actual $junction_point_result.AbsolutePath -expected $folder_target
Assert-Equal -actual $junction_point_result.HardTargets -expected $null

# create a hard link test
New-Link -link_path $hardlink_path -link_target $file_target -link_type "hard"
$hardlink_result = Get-Link -link_path $hardlink_path
Assert-Equal -actual $hardlink_result.Type -expected "HardLink"
Assert-Equal -actual $hardlink_result.SubstituteName -expected $null
Assert-Equal -actual $hardlink_result.PrintName -expected $null
Assert-Equal -actual $hardlink_result.TargetPath -expected $null
Assert-Equal -actual $hardlink_result.AbsolutePath -expected $null
if ($hardlink_result.HardTargets[0] -ne $hardlink_path -and $hardlink_result.HardTargets[1] -ne $hardlink_path) {
    Assert-True -expression $false -message "file $hardlink_path is not a target of the hard link"
}
if ($hardlink_result.HardTargets[0] -ne $file_target -and $hardlink_result.HardTargets[1] -ne $file_target) {
    Assert-True -expression $false -message "file $file_target is not a target of the hard link"
}
Assert-Equal -actual (Get-Content -LiteralPath $hardlink_path -Raw) -expected (Get-Content -LiteralPath $file_target -Raw)

# create a new hard link and verify targets go to 3
New-Link -link_path $hardlink_path_2 -link_target $file_target -link_type "hard"
$hardlink_result_2 = Get-Link -link_path $hardlink_path
$expected = "did not return 3 targets for the hard link, actual $($hardlink_result_2.Targets.Count)"
Assert-True -expression ($hardlink_result_2.HardTargets.Count -eq 3) -message $expected

# check if broken symbolic link still works
Remove-Item -LiteralPath $folder_target -Force | Out-Null
$broken_link_result = Get-Link -link_path $symlink_folder_path
Assert-Equal -actual $broken_link_result.Type -expected "SymbolicLink"
Assert-Equal -actual $broken_link_result.SubstituteName -expected "\??\$folder_target"
Assert-Equal -actual $broken_link_result.PrintName -expected $folder_target
Assert-Equal -actual $broken_link_result.TargetPath -expected $folder_target
Assert-Equal -actual $broken_link_result.AbsolutePath -expected $folder_target
Assert-Equal -actual $broken_link_result.HardTargets -expected $null

# check if broken junction point still works
$broken_junction_result = Get-Link -link_path $junction_point_path
Assert-Equal -actual $broken_junction_result.Type -expected "JunctionPoint"
Assert-Equal -actual $broken_junction_result.SubstituteName -expected "\??\$folder_target"
Assert-Equal -actual $broken_junction_result.PrintName -expected $folder_target
Assert-Equal -actual $broken_junction_result.TargetPath -expected $folder_target
Assert-Equal -actual $broken_junction_result.AbsolutePath -expected $folder_target
Assert-Equal -actual $broken_junction_result.HardTargets -expected $null

# delete file symbolic link
Remove-Link -link_path $symlink_file_path
Assert-True -expression (-not (Test-Path -LiteralPath $symlink_file_path)) -message "failed to delete file symbolic link"

# delete folder symbolic link
Remove-Link -link_path $symlink_folder_path
Assert-True -expression (-not (Test-Path -LiteralPath $symlink_folder_path)) -message "failed to delete folder symbolic link"

# delete junction point
Remove-Link -link_path $junction_point_path
Assert-True -expression (-not (Test-Path -LiteralPath $junction_point_path)) -message "failed to delete junction point"

# delete hard link
Remove-Link -link_path $hardlink_path
Assert-True -expression (-not (Test-Path -LiteralPath $hardlink_path)) -message "failed to delete hard link"

# cleanup after tests
Run-Command -command "cmd.exe /c rmdir /S /Q `"$path`"" > $null

Exit-Json @{ data = "success" }
