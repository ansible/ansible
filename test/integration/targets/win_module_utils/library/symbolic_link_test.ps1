#!powershell

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.LinkUtil
#Requires -Module Ansible.ModuleUtils.CommandUtil
#Requires -Module Ansible.ModuleUtils.FileUtil

$ErrorActionPreference = 'Stop'

$params = Parse-Args $args;
$path = Get-AnsibleParam -obj $params -name "path" -type "path" -failifempty $true

$result = @{
    changed = $false
}

# need to manually set this
Load-LinkUtils
Load-FileUtilFunctions

Function Assert-Equals($actual, $expected) {
    if ($actual -ne $expected) {
        $call_stack = (Get-PSCallStack)[1]
        $error_msg = "AssertionError:`r`nActual: `"$actual`" != Expected: `"$expected`"`r`nLine: $($call_stack.ScriptLineNumber), Method: $($call_stack.Position.Text)"
        Fail-Json -obj $result -message $error_msg
    }
}

Function Run-LinkTests($path) {
    $folder_target = "$path\folder"
    $file_target = "$path\file"
    $symlink_file_path = "$path\file-symlink"
    $symlink_folder_path = "$path\folder-symlink"
    $hardlink_path = "$path\hardlink"
    $hardlink_path_2 = "$path\hardlink2"
    $junction_point_path = "$path\junction"

    if (Test-AnsiblePath -Path $path) {
        [Ansible.IO.Directory]::Delete($path, $true)
    }
    [Ansible.IO.Directory]::CreateDirectory($path) > $null
    [Ansible.IO.Directory]::CreateDirectory($folder_target) > $null
    $sw = [Ansible.IO.File]::CreateText($file_target)
    try {
        $sw.Write("a")
    } finally {
        $sw.Close()
    }

    # path is not a link
    $no_link_result = Get-Link -link_path $path
    Assert-Equals -actual ($no_link_result -eq $null) -expected $true

    # fail to create hard link pointed to a directory
    $failed = $false
    try {
        New-Link -link_path "$path\folder-hard" -link_target $folder_target -link_type "hard"
    } catch {
        $failed = $true
        Assert-Equals -actual $_.Exception.Message -expected "cannot set the target for a hard link to a directory"
    }
    Assert-Equals -actual $failed -expected $true

    # fail to create a junction point pointed to a file
    $failed = $false
    try {
        New-Link -link_path "$path\junction-fail" -link_target $file_target -link_type "junction"
    } catch {
        $failed = $true
        Assert-Equals -actual $_.Exception.Message -expected "cannot set the target for a junction point to a file"
    }
    Assert-Equals -actual $failed -expected $true

    # fail to create a symbolic link with non-existent target
    try {
        New-Link -link_path "$path\symlink-fail" -link_target "$path\fake-folder" -link_type "link"
    } catch {
        $failed = $true
        Assert-Equals -actual $_.Exception.Message -expected "link_target '$path\fake-folder' does not exist, cannot create link"
    }
    Assert-Equals -actual $failed -expected $true

    # create relative symlink
    if ($path.StartsWith("\\?\")) {
        $chdir = $path.Substring(4)
    } else {
        $chdir = $path
    }
    Run-Command -command "cmd.exe /c mklink /D symlink-rel folder" -working_directory $chdir | Out-Null
    $rel_link_result = Get-Link -link_path "$path\symlink-rel"
    Assert-Equals -actual $rel_link_result.Type -expected "SymbolicLink"
    Assert-Equals -actual $rel_link_result.SubstituteName -expected "folder"
    Assert-Equals -actual $rel_link_result.PrintName -expected "folder"
    Assert-Equals -actual $rel_link_result.TargetPath -expected "folder"
    Assert-Equals -actual $rel_link_result.AbsolutePath -expected $folder_target
    Assert-Equals -actual $rel_link_result.HardTargets -expected $null

    # create a symbolic file test
    New-Link -link_path $symlink_file_path -link_target $file_target -link_type "link"
    $file_link_result = Get-Link -link_path $symlink_file_path
    Assert-Equals -actual $file_link_result.Type -expected "SymbolicLink"
    if ($path.StartsWith("\\?\")) {
        Assert-Equals -actual $file_link_result.SubstituteName -expected "\??\$($file_target.Substring(4))"
    } else {
        Assert-Equals -actual $file_link_result.SubstituteName -expected "\??\$($file_target)"
    }
    Assert-Equals -actual $file_link_result.PrintName -expected $file_target
    Assert-Equals -actual $file_link_result.TargetPath -expected $file_target
    Assert-Equals -actual $file_link_result.AbsolutePath -expected $file_target
    Assert-Equals -actual $file_link_result.HardTargets -expected $null

    # create a symbolic link folder test
    New-Link -link_path $symlink_folder_path -link_target $folder_target -link_type "link"
    $folder_link_result = Get-Link -link_path $symlink_folder_path
    Assert-Equals -actual $folder_link_result.Type -expected "SymbolicLink"
    if ($path.StartsWith("\\?\")) {
        Assert-Equals -actual $folder_link_result.SubstituteName -expected "\??\$($folder_target.Substring(4))"
    } else {
        Assert-Equals -actual $folder_link_result.SubstituteName -expected "\??\$($folder_target)"
    }
    Assert-Equals -actual $folder_link_result.PrintName -expected $folder_target
    Assert-Equals -actual $folder_link_result.TargetPath -expected $folder_target
    Assert-Equals -actual $folder_link_result.AbsolutePath -expected $folder_target
    Assert-Equals -actual $folder_link_result.HardTargets -expected $null

    # create a junction point test
    New-Link -link_path $junction_point_path -link_target $folder_target -link_type "junction"
    $junction_point_result = Get-Link -link_path $junction_point_path
    Assert-Equals -actual $junction_point_result.Type -expected "JunctionPoint"
    if ($path.StartsWith("\\?\")) {
        Assert-Equals -actual $junction_point_result.SubstituteName -expected "\??\$($folder_target.Substring(4))"
    } else {
        Assert-Equals -actual $junction_point_result.SubstituteName -expected "\??\$($folder_target)"
    }
    Assert-Equals -actual $junction_point_result.PrintName -expected $folder_target
    Assert-Equals -actual $junction_point_result.TargetPath -expected $folder_target
    Assert-Equals -actual $junction_point_result.AbsolutePath -expected $folder_target
    Assert-Equals -actual $junction_point_result.HardTargets -expected $null

    # create a hard link test
    New-Link -link_path $hardlink_path -link_target $file_target -link_type "hard"
    $hardlink_result = Get-Link -link_path $hardlink_path
    Assert-Equals -actual $hardlink_result.Type -expected "HardLink"
    Assert-Equals -actual $hardlink_result.SubstituteName -expected $null
    Assert-Equals -actual $hardlink_result.PrintName -expected $null
    Assert-Equals -actual $hardlink_result.TargetPath -expected $null
    Assert-Equals -actual $hardlink_result.AbsolutePath -expected $null
    if ($hardlink_result.HardTargets[0] -ne $hardlink_path -and $hardlink_result.HardTargets[1] -ne $hardlink_path) {
        # file $hardlink_path is not a target of the hard link
        Assert-Equals -actual $true -expected $false
    }
    if ($hardlink_result.HardTargets[0] -ne $file_target -and $hardlink_result.HardTargets[1] -ne $file_target) {
        # file $file_target is not a target of the hard link
        Assert-Equals -actual $true -expected $false
    }
    $hardlink_contents = [Ansible.IO.File]::ReadAllText($hardlink_path)
    $file_contents = [Ansible.IO.File]::ReadAllText($file_target)
    Assert-Equals -actual $hardlink_contents -expected $file_contents

    # create a new hard link and verify targets go to 3
    New-Link -link_path $hardlink_path_2 -link_target $file_target -link_type "hard"
    $hardlink_result_2 = Get-Link -link_path $hardlink_path
    Assert-Equals -actual ($hardlink_result_2.HardTargets.Count -eq 3) -expected $true

    # check if broken symbolic link still works
    Remove-Item -Path $folder_target -Force | Out-Null
    $broken_link_result = Get-Link -link_path $symlink_folder_path
    Assert-Equals -actual $broken_link_result.Type -expected "SymbolicLink"
    if ($path.StartsWith("\\?\")) {
        Assert-Equals -actual $broken_link_result.SubstituteName -expected "\??\$($folder_target.Substring(4))"
    } else {
        Assert-Equals -actual $broken_link_result.SubstituteName -expected "\??\$($folder_target)"
    }
    Assert-Equals -actual $broken_link_result.PrintName -expected $folder_target
    Assert-Equals -actual $broken_link_result.TargetPath -expected $folder_target
    Assert-Equals -actual $broken_link_result.AbsolutePath -expected $folder_target
    Assert-Equals -actual $broken_link_result.HardTargets -expected $null

    # check if broken junction point still works
    $broken_junction_result = Get-Link -link_path $junction_point_path
    Assert-Equals -actual $broken_junction_result.Type -expected "JunctionPoint"
    if ($path.StartsWith("\\?\")) {
        Assert-Equals -actual $broken_junction_result.SubstituteName -expected "\??\$($folder_target.Substring(4))"
    } else {
        Assert-Equals -actual $broken_junction_result.SubstituteName -expected "\??\$($folder_target)"
    }
    Assert-Equals -actual $broken_junction_result.PrintName -expected $folder_target
    Assert-Equals -actual $broken_junction_result.TargetPath -expected $folder_target
    Assert-Equals -actual $broken_junction_result.AbsolutePath -expected $folder_target
    Assert-Equals -actual $broken_junction_result.HardTargets -expected $null

    # delete file symbolic link
    Remove-Link -link_path $symlink_file_path
    Assert-Equals -actual (-not (Test-Path -Path $symlink_file_path)) -expected $true

    # delete folder symbolic link
    Remove-Link -link_path $symlink_folder_path
    Assert-Equals -actual (-not (Test-Path -Path $symlink_folder_path)) -expected $true

    # delete junction point
    Remove-Link -link_path $junction_point_path
    Assert-Equals -actual (-not (Test-Path -Path $junction_point_path)) -expected $true

    # delete hard link
    Remove-Link -link_path $hardlink_path
    Assert-Equals -actual (-not (Test-Path -Path $hardlink_path)) -expected $true
}

Run-LinkTests -path $path
Run-LinkTests -path "\\?\$path"

$result.data = "success"
Exit-Json -obj $result

