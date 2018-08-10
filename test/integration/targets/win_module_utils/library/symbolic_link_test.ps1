#!powershell

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.LinkUtil

$ErrorActionPreference = 'Stop'

$params = Parse-Args $args
$path = Get-AnsibleParam -obj $params -name "path" -type "path" -failifempty $true

$result = @{
    changed = $false
}

# need to manually set this
Import-LinkUtil

Function Assert-Equals($actual, $expected) {
    if ($actual -ne $expected) {
        $call_stack = (Get-PSCallStack)[1]
        $error_msg = "AssertionError:`r`nActual: `"$actual`" != Expected: `"$expected`"`r`nLine: $($call_stack.ScriptLineNumber), Method: $($call_stack.Position.Text)"
        Fail-Json -obj $result -message $error_msg
    }
}

Function Remove-TestDirectory($path) {
    if (Test-AnsiblePath -Path $path) {
        # previous tests may have ended in a bad state and some folders are not
        # accessible to the current user. This defensively set's the owner back to
        # the current user so we can delete the folders
        $current_sid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
        $search_path = $path
        if (-not $search_path.StartsWith("\\?\")) {
            $search_path = "\\?\$search_path"
        }
        $dirs = [Ansible.IO.Directory]::GetDirectories($search_path, "*", [System.IO.SearchOption]::AllDirectories)
        foreach ($dir in $dirs) {
            # SetAccessControl should be setting SeReplace, and SeTakeOwnershipPrivilege for us
            $acl = New-Object -TypeName System.Security.AccessControl.DirectorySecurity
            $acl.SetOwner($current_sid)
            $ace = New-Object -TypeName System.Security.AccessControl.FileSystemAccessRule -ArgumentList @(
                $current_sid,
                [System.Security.AccessControl.FileSystemRights]::Delete,
                [System.Security.AccessControl.AccessControlType]::Allow
            )
            $acl.AddAccessRule($ace)
            [Ansible.IO.Directory]::SetAccessControl($dir, $acl)
        }

        [Ansible.IO.Directory]::Delete($search_path, $true)
    }
}

Function Test-LinkUtil($path) {
    $folder_target = "$path\folder"
    $file_target = "$path\file"
    $symlink_file_path = "$path\file-symlink"
    $symlink_folder_path = "$path\folder-symlink"
    $symlink_missing_path = "$path\symlink-folder-missing"
    $hardlink_path = "$path\hardlink"
    $hardlink_path_2 = "$path\hardlink2"
    $junction_point_path = "$path\junction"

    Remove-TestDirectory -path $path
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
    Assert-Equals -actual ($null -eq $no_link_result) -expected $true

    # fail to create hard link pointed to a directory
    $failed = $false
    try {
        New-Link -link_path "$path\folder-hard" -link_target $folder_target -link_type "hard"
    } catch {
        $failed = $true
        Assert-Equals -actual $_.Exception.Message -expected "cannot set the target for a hard link to a directory"
    }
    Assert-Equals -actual $failed -expected $true

    # hard link target does not exist
    $failed = $false
    try {
        New-Link -link_path "$path\hard-missing" -link_target "$path\fake" -link_type "hard"
    } catch {
        $failed = $true
        Assert-Equals -actual $_.Exception.Message -expected "link_target '$path\fake' does not exist, cannot create hard link"
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

    # create relative symlink dir
    New-Link -link_path "$path\symlink-rel" -link_target "folder" -link_type "link"
    $rel_link_result = Get-Link -link_path "$path\symlink-rel"
    Assert-Equals -actual $rel_link_result.Type -expected "SymbolicLink"
    Assert-Equals -actual $rel_link_result.SubstituteName -expected "folder"
    Assert-Equals -actual $rel_link_result.PrintName -expected "folder"
    Assert-Equals -actual $rel_link_result.TargetPath -expected "folder"
    Assert-Equals -actual $rel_link_result.AbsolutePath -expected $folder_target
    Assert-Equals -actual $rel_link_result.HardTargets -expected $null

    # create relative symlink file
    New-Link -link_path "$path\folder\symlink-rel-file" -link_target "..\file" -link_type "link"
    $rel_link_result = Get-Link -link_path "$path\folder\symlink-rel-file"
    Assert-Equals -actual $rel_link_result.Type -expected "SymbolicLink"
    Assert-Equals -actual $rel_link_result.SubstituteName -expected "..\file"
    Assert-Equals -actual $rel_link_result.PrintName -expected "..\file"
    Assert-Equals -actual $rel_link_result.TargetPath -expected "..\file"
    Assert-Equals -actual $rel_link_result.AbsolutePath -expected $file_target
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

    # create a symbolic link with missing target and no file extension (auto dir)
    New-Link -link_path $symlink_missing_path -link_target "$path\symlink-target" -link_type "link"
    $folder_link_result = Get-Link -link_path $symlink_missing_path
    Assert-Equals -actual $folder_link_result.Type -expected "SymbolicLink"
    if ($path.StartsWith("\\?\")) {
        Assert-Equals -actual $folder_link_result.SubstituteName -expected "\??\$($path.Substring(4))\symlink-target"
    } else {
        Assert-Equals -actual $folder_link_result.SubstituteName -expected "\??\$($path)\symlink-target"
    }
    Assert-Equals -actual $folder_link_result.PrintName -expected "$path\symlink-target"
    Assert-Equals -actual $folder_link_result.TargetPath -expected "$path\symlink-target"
    Assert-Equals -actual $folder_link_result.AbsolutePath -expected "$path\symlink-target"
    Assert-Equals -actual $folder_link_result.HardTargets -expected $null

    # create a symbolic link with missing target and file extension (auto file)
    New-Link -link_path "$path\symlink-file-missing" -link_target "$path\symlink-target.txt" -link_type "link"
    $folder_link_result = Get-Link -link_path "$path\symlink-file-missing"
    Assert-Equals -actual $folder_link_result.Type -expected "SymbolicLink"
    if ($path.StartsWith("\\?\")) {
        Assert-Equals -actual $folder_link_result.SubstituteName -expected "\??\$($path.Substring(4))\symlink-target.txt"
    } else {
        Assert-Equals -actual $folder_link_result.SubstituteName -expected "\??\$($path)\symlink-target.txt"
    }
    Assert-Equals -actual $folder_link_result.PrintName -expected "$path\symlink-target.txt"
    Assert-Equals -actual $folder_link_result.TargetPath -expected "$path\symlink-target.txt"
    Assert-Equals -actual $folder_link_result.AbsolutePath -expected "$path\symlink-target.txt"
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

    # create a junction point with missing target test
    New-Link -link_path "$path\junction-missing" -link_target "$path\fail" -link_type "junction"
    $junction_point_result = Get-Link -link_path "$path\junction-missing"
    Assert-Equals -actual $junction_point_result.Type -expected "JunctionPoint"
    if ($path.StartsWith("\\?\")) {
        Assert-Equals -actual $junction_point_result.SubstituteName -expected "\??\$($path.Substring(4))\fail"
    } else {
        Assert-Equals -actual $junction_point_result.SubstituteName -expected "\??\$($path)\fail"
    }
    Assert-Equals -actual $junction_point_result.PrintName -expected "$path\fail"
    Assert-Equals -actual $junction_point_result.TargetPath -expected "$path\fail"
    Assert-Equals -actual $junction_point_result.AbsolutePath -expected "$path\fail"
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
    [Ansible.IO.Directory]::Delete($folder_target, $true)
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

    # remove all rights to a symlink that verifies SeBackupPrivilege is set when getting link info
    $system_sid = New-Object -TypeName System.Security.Principal.SecurityIdentifier -ArgumentList "S-1-5-18"
    $ace = New-Object -TypeName System.Security.AccessControl.FileSystemAccessRule -ArgumentList @($system_sid,
        [System.Security.AccessControl.FileSystemRights]::FullControl,
        [System.Security.AccessControl.AccessControlType]::Allow)
    $acl = [Ansible.IO.Directory]::GetAccessControl($symlink_missing_path, [System.Security.AccessControl.AccessControlSections]"Access, Owner, Group")
    $acl.SetAccessRule($ace)
    $acl.SetAccessRuleProtection($true, $false)  # disable inheritance
    $acl.SetGroup($system_sid)
    $acl.SetOwner($system_sid)
    [Ansible.IO.Directory]::SetAccessControl($symlink_missing_path, $acl)
    $folder_link_result = Get-Link -link_path $symlink_missing_path
    Assert-Equals -actual $folder_link_result.Type -expected "SymbolicLink"
    if ($path.StartsWith("\\?\")) {
        Assert-Equals -actual $folder_link_result.SubstituteName -expected "\??\$($path.Substring(4))\symlink-target"
    } else {
        Assert-Equals -actual $folder_link_result.SubstituteName -expected "\??\$($path)\symlink-target"
    }
    Assert-Equals -actual $folder_link_result.PrintName -expected "$path\symlink-target"
    Assert-Equals -actual $folder_link_result.TargetPath -expected "$path\symlink-target"
    Assert-Equals -actual $folder_link_result.AbsolutePath -expected "$path\symlink-target"
    Assert-Equals -actual $folder_link_result.HardTargets -expected $null

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

Function Test-LinkUtilUNC($path) {
    Remove-TestDirectory -path $path
    $local_path = "$path\local"
    [Ansible.IO.Directory]::CreateDirectory($local_path) > $null
    $local_dir = "$local_path\directory"
    $local_file = "$local_dir\file.txt"
    [Ansible.IO.Directory]::CreateDirectory($local_dir) > $null
    [Ansible.IO.File]::WriteAllText($local_file, "local")

    if ($path.StartsWith("\\?\")) {
        $unc_path = "\\?\UNC\127.0.0.1\c$\$($path.Substring(7))\unc"
    } else {
        $unc_path = "\\127.0.0.1\c$\$($path.Substring(3))\unc"
    }
    [Ansible.IO.Directory]::CreateDirectory($unc_path) > $null
    $unc_dir = "$unc_path\directory"
    $unc_file = "$unc_dir\file.txt"
    [Ansible.IO.Directory]::CreateDirectory($unc_dir) > $null
    [Ansible.IO.File]::WriteAllText($unc_file, "unc")

    $local_to_unc_dir_path = "$local_path\to-unc-dir"
    $local_to_unc_file_path = "$local_path\to-unc-file"
    $unc_to_local_dir_path = "$unc_path\to-unc-dir"
    $unc_to_local_file_path = "$unc_path\to-local-dir"

    # test create a symlink dir from local => unc
    New-Link -link_path $local_to_unc_dir_path -link_target $unc_dir -link_type "link"
    $local_to_unc_dir = Get-Link -link_path $local_to_unc_dir_path
    $local_to_unc_dir_text = [Ansible.IO.File]::ReadAllText("$local_to_unc_dir_path\file.txt")
    Assert-Equals -actual $local_to_unc_dir.Type -expected "SymbolicLink"
    if ($path.StartsWith("\\?\")) {
        Assert-Equals -actual $local_to_unc_dir.SubstituteName -expected "\??\$($unc_dir.Substring(4))"
    } else {
        Assert-Equals -actual $local_to_unc_dir.SubstituteName -expected "\??\UNC$($unc_dir.Substring(1))"
    }
    Assert-Equals -actual $local_to_unc_dir.PrintName -expected $unc_dir
    Assert-Equals -actual $local_to_unc_dir.TargetPath -expected $unc_dir
    Assert-Equals -actual $local_to_unc_dir.AbsolutePath -expected $unc_dir
    Assert-Equals -actual $local_to_unc_dir.HardTargets -expected $null
    Assert-Equals -actual $local_to_unc_dir_text -expected "unc"

    # test create a symlink file from local => unc
    New-Link -link_path $local_to_unc_file_path -link_target $unc_file -link_type "link"
    $local_to_unc_file = Get-Link -link_path $local_to_unc_file_path
    $local_to_unc_file_text = [Ansible.IO.File]::ReadAllText($local_to_unc_file_path)
    Assert-Equals -actual $local_to_unc_file.Type -expected "SymbolicLink"
    if ($path.StartsWith("\\?\")) {
        Assert-Equals -actual $local_to_unc_file.SubstituteName -expected "\??\$($unc_file.Substring(4))"
    } else {
        Assert-Equals -actual $local_to_unc_file.SubstituteName -expected "\??\UNC$($unc_file.Substring(1))"
    }
    Assert-Equals -actual $local_to_unc_file.PrintName -expected $unc_file
    Assert-Equals -actual $local_to_unc_file.TargetPath -expected $unc_file
    Assert-Equals -actual $local_to_unc_file.AbsolutePath -expected $unc_file
    Assert-Equals -actual $local_to_unc_file.HardTargets -expected $null
    Assert-Equals -actual $local_to_unc_file_text -expected "unc"

    # test create a symlink dir from unc => local
    New-Link -link_path $unc_to_local_dir_path -link_target $local_dir -link_type "link"
    $unc_to_local_dir = Get-Link -link_path $unc_to_local_dir_path
    $unc_to_local_dir_text = [Ansible.IO.File]::ReadAllText("$unc_to_local_dir_path\file.txt")
    Assert-Equals -actual $unc_to_local_dir.Type -expected "SymbolicLink"
    if ($path.StartsWith("\\?\")) {
        Assert-Equals -actual $unc_to_local_dir.SubstituteName -expected "\??\$($local_dir.Substring(4))"
    } else {
        Assert-Equals -actual $unc_to_local_dir.SubstituteName -expected "\??\$local_dir"
    }
    Assert-Equals -actual $unc_to_local_dir.PrintName -expected $local_dir
    Assert-Equals -actual $unc_to_local_dir.TargetPath -expected $local_dir
    Assert-Equals -actual $unc_to_local_dir.AbsolutePath -expected $local_dir
    Assert-Equals -actual $unc_to_local_dir.HardTargets -expected $null
    Assert-Equals -actual $unc_to_local_dir_text -expected "local"

    # test create a symlink file from unc => local
    New-Link -link_path $unc_to_local_file_path -link_target $local_file -link_type "link"
    $unc_to_local_file = Get-Link -link_path $unc_to_local_file_path
    $unc_to_local_file_text = [Ansible.IO.File]::ReadAllText($unc_to_local_file_path)
    Assert-Equals -actual $unc_to_local_file.Type -expected "SymbolicLink"
    if ($path.StartsWith("\\?\")) {
        Assert-Equals -actual $unc_to_local_file.SubstituteName -expected "\??\$($local_file.Substring(4))"
    } else {
        Assert-Equals -actual $unc_to_local_file.SubstituteName -expected "\??\$local_file"
    }
    Assert-Equals -actual $unc_to_local_file.PrintName -expected $local_file
    Assert-Equals -actual $unc_to_local_file.TargetPath -expected $local_file
    Assert-Equals -actual $unc_to_local_file.AbsolutePath -expected $local_file
    Assert-Equals -actual $unc_to_local_file.HardTargets -expected $null
    Assert-Equals -actual $unc_to_local_file_text -expected "local"
}

# tests a really long path ~ 2000 chars
$path = "$path\link-util-test"
$long_path = "\\?\$path\{0}\{0}\{0}\{0}\{0}\{0}\{0}" -f ("a" * 250)

Test-LinkUtil -path $path
Test-LinkUtil -path $long_path

# only symbolic links work across volumes/UNC so these tests need to stay separate to the above
Test-LinkUtilUNC -path $path
Test-LinkUtilUNC -path $long_path

Remove-TestDirectory -path "\\?\$path"

$result.data = "success"
Exit-Json -obj $result
