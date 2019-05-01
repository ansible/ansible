#!powershell

#AnsibleRequires -CSharpUtil Ansible.Basic
#AnsibleRequires -CSharpUtil Ansible.IO
#AnsibleRequires -CSharpUtil Ansible.Link

$module = [Ansible.Basic.AnsibleModule]::Create($args, @{})

Function Assert-Equals {
    param(
        [Parameter(Mandatory=$true, ValueFromPipeline=$true)][AllowNull()]$Actual,
        [Parameter(Mandatory=$true, Position=0)][AllowNull()]$Expected
    )

    $matched = $false
    if ($Actual -is [System.Collections.ArrayList] -or $Actual -is [Array]) {
        $Actual.Count | Assert-Equals -Expected $Expected.Count
        for ($i = 0; $i -lt $Actual.Count; $i++) {
            $actual_value = $Actual[$i]
            $expected_value = $Expected[$i]
            Assert-Equals -Actual $actual_value -Expected $expected_value
        }
        $matched = $true
    } else {
        $matched = $Actual -ceq $Expected
    }

    if (-not $matched) {
        if ($Actual -is [PSObject]) {
            $Actual = $Actual.ToString()
        }

        $call_stack = (Get-PSCallStack)[1]
        $module.Result.test = $test
        $module.Result.actual = $Actual
        $module.Result.expected = $Expected
        $module.Result.line = $call_stack.ScriptLineNumber
        $module.Result.method = $call_stack.Position.Text

        $module.FailJson("AssertionError: actual != expected")
    }
}

Function Clear-Directory {
    [CmdletBinding()]
    Param (
        [Parameter(Mandatory=$true)][System.String]$Path
    )

    if ([Ansible.IO.FileSystem]::DirectoryExists($Path)) {
        [Ansible.IO.FileSystem]::RemoveDirectory($Path, $true)
    }
    [Ansible.IO.FileSystem]::CreateDirectory($Path)
}

$tests = @{
    "Get link info on non existent path" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "fake.txt")

        $failed = $false
        try {
            [Ansible.Link.LinkUtil]::GetLinkInfo($path)
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.FileNotFoundException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "Could not find file '$path'"
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Get link info on missing parent dir" = {
        $path = [System.IO.Path]::Combine($test_path, "fake folder", "fake")

        $failed = $false
        try {
            [Ansible.Link.LinkUtil]::GetLinkInfo($path)
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.DirectoryNotFoundException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "Could not find a part of the path '$path'."
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Get link info for normal file" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "file.txt")
        $file_h = [Ansible.IO.FileSystem]::CreateFile($path, "CreateNew", "Write", "None", "None")
        $file_h.Dispose()

        $actual = [Ansible.Link.LinkUtil]::GetLinkInfo($path)
        $actual | Assert-Equals -Expected $null
    }

    "Get link info for normal directory" = {
        $actual = [Ansible.Link.LinkUtil]::GetLinkInfo($test_path)
        $actual | Assert-Equals -Expected $null
    }

    "Create a directory symbolic link to absolute target" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")
        [Ansible.IO.FileSystem]::CreateDirectory($target)

        [Ansible.Link.LinkUtil]::CreateLink($path, $target, "SymbolicLink")
        $actual = [Ansible.Link.LinkUtil]::GetLinkInfo($path)

        if ($test_path.StartsWith("\\?\")) {
            # Need to remove the \\?\ from the target path
            $expected_sub_name = "\??\$($target.Substring(4))"
        } else {
            $expected_sub_name = "\??\$target"
        }

        ([Ansible.IO.FileSystem]::DirectoryExists($path)) | Assert-Equals -Expected $true
        $actual.GetType().FullName | Assert-Equals -Expected "Ansible.Link.LinkInfo"
        $actual.Type | Assert-Equals -Expected ([Ansible.Link.LinkType]::SymbolicLink)
        $actual.PrintName | Assert-Equals -Expected $target
        $actual.SubstituteName | Assert-Equals -Expected $expected_sub_name
        $actual.AbsolutePath | Assert-Equals -Expected $target
        $actual.TargetPath | Assert-Equals -Expected $target
        $actual.HardTargets.Length | Assert-Equals -Expected 0
    }

    "Create a directory symbolic link to missing absolute target" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")

        [Ansible.Link.LinkUtil]::CreateLink($path, $target, "SymbolicLink")
        $actual = [Ansible.Link.LinkUtil]::GetLinkInfo($path)

        if ($test_path.StartsWith("\\?\")) {
            # Need to remove the \\?\ from the target path
            $expected_sub_name = "\??\$($target.Substring(4))"
        } else {
            $expected_sub_name = "\??\$target"
        }

        ([Ansible.IO.FileSystem]::DirectoryExists($path)) | Assert-Equals -Expected $true
        $actual.GetType().FullName | Assert-Equals -Expected "Ansible.Link.LinkInfo"
        $actual.Type | Assert-Equals -Expected ([Ansible.Link.LinkType]::SymbolicLink)
        $actual.PrintName | Assert-Equals -Expected $target
        $actual.SubstituteName | Assert-Equals -Expected $expected_sub_name
        $actual.AbsolutePath | Assert-Equals -Expected $target
        $actual.TargetPath | Assert-Equals -Expected $target
        $actual.HardTargets.Length | Assert-Equals -Expected 0
    }

    "Create a directory symbolic link to relative target" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine(".", "target")
        $target_abs = [Ansible.IO.Path]::Combine($test_path, "target")
        [Ansible.IO.FileSystem]::CreateDirectory($target_abs)

        [Ansible.Link.LinkUtil]::CreateLink($path, $target, "SymbolicLink")
        $actual = [Ansible.Link.LinkUtil]::GetLinkInfo($path)

        ([Ansible.IO.FileSystem]::DirectoryExists($path)) | Assert-Equals -Expected $true
        $actual.GetType().FullName | Assert-Equals -Expected "Ansible.Link.LinkInfo"
        $actual.Type | Assert-Equals -Expected ([Ansible.Link.LinkType]::SymbolicLink)
        $actual.PrintName | Assert-Equals -Expected $target
        $actual.SubstituteName | Assert-Equals -Expected $target
        $actual.AbsolutePath | Assert-Equals -Expected $target_abs
        $actual.TargetPath | Assert-Equals -Expected $target
        $actual.HardTargets.Length | Assert-Equals -Expected 0
    }

    "Create a directory symbolic link to missing relative target" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine(".", "target")
        $target_abs = [Ansible.IO.Path]::Combine($test_path, "target")

        [Ansible.Link.LinkUtil]::CreateLink($path, $target, "SymbolicLink")
        $actual = [Ansible.Link.LinkUtil]::GetLinkInfo($path)

        ([Ansible.IO.FileSystem]::DirectoryExists($path)) | Assert-Equals -Expected $true
        $actual.GetType().FullName | Assert-Equals -Expected "Ansible.Link.LinkInfo"
        $actual.Type | Assert-Equals -Expected ([Ansible.Link.LinkType]::SymbolicLink)
        $actual.PrintName | Assert-Equals -Expected $target
        $actual.SubstituteName | Assert-Equals -Expected $target
        $actual.AbsolutePath | Assert-Equals -Expected $target_abs
        $actual.TargetPath | Assert-Equals -Expected $target
        $actual.HardTargets.Length | Assert-Equals -Expected 0
    }

    "Create a file symbolic link to absolute target" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        $target = [Ansible.IO.Path]::Combine($test_path, "target.txt")
        $file_h = [Ansible.IO.FileSystem]::CreateFile($target, "CreateNew", "Write", "None", "None")
        $file_h.Dispose()

        [Ansible.Link.LinkUtil]::CreateLink($path, $target, "SymbolicLink")
        $actual = [Ansible.Link.LinkUtil]::GetLinkInfo($path)

        if ($test_path.StartsWith("\\?\")) {
            # Need to remove the \\?\ from the target path
            $expected_sub_name = "\??\$($target.Substring(4))"
        } else {
            $expected_sub_name = "\??\$target"
        }

        ([Ansible.IO.FileSystem]::FileExists($path)) | Assert-Equals -Expected $true
        $actual.GetType().FullName | Assert-Equals -Expected "Ansible.Link.LinkInfo"
        $actual.Type | Assert-Equals -Expected ([Ansible.Link.LinkType]::SymbolicLink)
        $actual.PrintName | Assert-Equals -Expected $target
        $actual.SubstituteName | Assert-Equals -Expected $expected_sub_name
        $actual.AbsolutePath | Assert-Equals -Expected $target
        $actual.TargetPath | Assert-Equals -Expected $target
        $actual.HardTargets.Length | Assert-Equals -Expected 0
    }

    "Create a file symbolic link to missing absolute target" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        $target = [Ansible.IO.Path]::Combine($test_path, "target.txt")

        [Ansible.Link.LinkUtil]::CreateLink($path, $target, "SymbolicLink")
        $actual = [Ansible.Link.LinkUtil]::GetLinkInfo($path)

        if ($test_path.StartsWith("\\?\")) {
            # Need to remove the \\?\ from the target path
            $expected_sub_name = "\??\$($target.Substring(4))"
        } else {
            $expected_sub_name = "\??\$target"
        }

        ([Ansible.IO.FileSystem]::FileExists($path)) | Assert-Equals -Expected $true
        $actual.GetType().FullName | Assert-Equals -Expected "Ansible.Link.LinkInfo"
        $actual.Type | Assert-Equals -Expected ([Ansible.Link.LinkType]::SymbolicLink)
        $actual.PrintName | Assert-Equals -Expected $target
        $actual.SubstituteName | Assert-Equals -Expected $expected_sub_name
        $actual.AbsolutePath | Assert-Equals -Expected $target
        $actual.TargetPath | Assert-Equals -Expected $target
        $actual.HardTargets.Length | Assert-Equals -Expected 0
    }

    "Create a file symbolic link to missing absolute target dest no extension" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")

        [Ansible.Link.LinkUtil]::CreateLink($path, $target, "SymbolicLink")
        $actual = [Ansible.Link.LinkUtil]::GetLinkInfo($path)

        if ($test_path.StartsWith("\\?\")) {
            # Need to remove the \\?\ from the target path
            $expected_sub_name = "\??\$($target.Substring(4))"
        } else {
            $expected_sub_name = "\??\$target"
        }

        ([Ansible.IO.FileSystem]::FileExists($path)) | Assert-Equals -Expected $true
        $actual.GetType().FullName | Assert-Equals -Expected "Ansible.Link.LinkInfo"
        $actual.Type | Assert-Equals -Expected ([Ansible.Link.LinkType]::SymbolicLink)
        $actual.PrintName | Assert-Equals -Expected $target
        $actual.SubstituteName | Assert-Equals -Expected $expected_sub_name
        $actual.AbsolutePath | Assert-Equals -Expected $target
        $actual.TargetPath | Assert-Equals -Expected $target
        $actual.HardTargets.Length | Assert-Equals -Expected 0
    }

    "Create a file symbolic link to relative target" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        $target = [Ansible.IO.Path]::Combine(".", "target.txt")
        $target_abs = [Ansible.IO.Path]::Combine($test_path, "target.txt")
        $file_h = [Ansible.IO.FileSystem]::CreateFile($target_abs, "CreateNew", "Write", "None", "None")
        $file_h.Dispose()

        [Ansible.Link.LinkUtil]::CreateLink($path, $target, "SymbolicLink")
        $actual = [Ansible.Link.LinkUtil]::GetLinkInfo($path)

        ([Ansible.IO.FileSystem]::FileExists($path)) | Assert-Equals -Expected $true
        $actual.GetType().FullName | Assert-Equals -Expected "Ansible.Link.LinkInfo"
        $actual.Type | Assert-Equals -Expected ([Ansible.Link.LinkType]::SymbolicLink)
        $actual.PrintName | Assert-Equals -Expected $target
        $actual.SubstituteName | Assert-Equals -Expected $target
        $actual.AbsolutePath | Assert-Equals -Expected $target_abs
        $actual.TargetPath | Assert-Equals -Expected $target
        $actual.HardTargets.Length | Assert-Equals -Expected 0
    }

    "Create a file symbolic link to missing relative target" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        $target = [Ansible.IO.Path]::Combine(".", "target.txt")
        $target_abs = [Ansible.IO.Path]::Combine($test_path, "target.txt")

        [Ansible.Link.LinkUtil]::CreateLink($path, $target, "SymbolicLink")
        $actual = [Ansible.Link.LinkUtil]::GetLinkInfo($path)

        ([Ansible.IO.FileSystem]::FileExists($path)) | Assert-Equals -Expected $true
        $actual.GetType().FullName | Assert-Equals -Expected "Ansible.Link.LinkInfo"
        $actual.Type | Assert-Equals -Expected ([Ansible.Link.LinkType]::SymbolicLink)
        $actual.PrintName | Assert-Equals -Expected $target
        $actual.SubstituteName | Assert-Equals -Expected $target
        $actual.AbsolutePath | Assert-Equals -Expected $target_abs
        $actual.TargetPath | Assert-Equals -Expected $target
        $actual.HardTargets.Length | Assert-Equals -Expected 0
    }

    "Create a symbolic link to network path" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "source")

        if ($test_path.StartsWith("\\?\")) {
            $target_unc = "\\?\UNC\localhost\c$" + $test_path.Substring(6)
            $expected_sub_name = "\??\UNC\localhost\c`$$($test_path.Substring(6))\target"
        } else {
            $target_unc = "\\localhost\c$" + $test_path.Substring(2)
            $expected_sub_name = "\??\UNC\localhost\c`$$($test_path.Substring(2))\target"
        }
        $target = [Ansible.IO.Path]::Combine($target_unc, "target")
        [Ansible.IO.FileSystem]::CreateDirectory($target)

        [Ansible.Link.LinkUtil]::CreateLink($path, $target, "SymbolicLink")
        $actual = [Ansible.Link.LinkUtil]::GetLinkInfo($path)

        ([Ansible.IO.FileSystem]::DirectoryExists($path)) | Assert-Equals -Expected $true
        $actual.GetType().FullName | Assert-Equals -Expected "Ansible.Link.LinkInfo"
        $actual.Type | Assert-Equals -Expected ([Ansible.Link.LinkType]::SymbolicLink)
        $actual.PrintName | Assert-Equals -Expected $target
        $actual.SubstituteName | Assert-Equals -Expected $expected_sub_name
        $actual.AbsolutePath | Assert-Equals -Expected $target
        $actual.TargetPath | Assert-Equals -Expected $target
        $actual.HardTargets.Length | Assert-Equals -Expected 0
    }

    "Read symbolic link with no rights to link" = {
        if ($test_path.StartsWith("\\?\")) {
            # We use some .NET APIs to set the permissions which fail on a long path. Just skip that test for now.
            return
        }

        # Create parent path that we have no rights to
        $parent_path = [Ansible.IO.Path]::Combine($test_path, "parent")
        [Ansible.IO.FileSystem]::CreateDirectory($parent_path)

        $path = [Ansible.IO.Path]::Combine($parent_path, "source")
        $target = [Ansible.IO.Path]::Combine($parent_path, "target")
        [Ansible.Link.LinkUtil]::CreateLink($path, $target, "SymbolicLink")

        # Sets a an empty DACL (no permissions) and a different group/owner from the current user.
        $system_sid = New-Object -TypeName System.Security.Principal.SecurityIdentifier -ArgumentList "S-1-5-18"
        $acl = New-Object -TypeName System.Security.AccessControl.DirectorySecurity
        $acl.SetGroup($system_sid)
        $acl.SetOwner($system_sid)
        $acl.SetAccessRuleProtection($true, $false)
        [System.IO.Directory]::SetAccessControl($parent_path, $acl)

        $actual = [Ansible.Link.LinkUtil]::GetLinkInfo($path)
        $actual.GetType().FullName | Assert-Equals -Expected "Ansible.Link.LinkInfo"
        $actual.Type | Assert-Equals -Expected ([Ansible.Link.LinkType]::SymbolicLink)
        $actual.PrintName | Assert-Equals -Expected $target
        $actual.SubstituteName | Assert-Equals -Expected "\??\$target"
        $actual.AbsolutePath | Assert-Equals -Expected $target
        $actual.TargetPath | Assert-Equals -Expected $target
        $actual.HardTargets.Length | Assert-Equals -Expected 0
    }

    "Fail to create symbolic link with missing parent dir" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "parent", "link")

        $failed = $false
        try {
            [Ansible.Link.LinkUtil]::CreateLink($path, $test_path, "SymbolicLink")
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.DirectoryNotFoundException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "Could not find a part of the path '$path'."
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Delete a link that does not exist" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "source")

        $failed = $false
        try {
            [Ansible.Link.LinkUtil]::DeleteLink($path)
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.FileNotFoundException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "Could not find file '$path'"
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Delete a link that is a normal directory" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "source")
        [Ansible.IO.FileSystem]::CreateDirectory($path)

        # DeleteLink does not fail if the path is not a link, just calls the normal delete functions.
        [Ansible.Link.LinkUtil]::DeleteLink($path)
        [Ansible.IO.FileSystem]::DirectoryExists($path) | Assert-Equals -Expected $false
    }

    "Delete a link that is a normal file" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        $file_h = [Ansible.IO.FileSystem]::CreateFile($path, "CreateNew", "Read", "None", "None")
        $file_h.Dispose()

        # DeleteLink does not fail if the path is not a link, just calls the normal delete functions.
        [Ansible.Link.LinkUtil]::DeleteLink($path)
        [Ansible.IO.FileSystem]::FileExists($path) | Assert-Equals -Expected $false
    }

    "Delete a directory symbolic link" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")
        [Ansible.IO.FileSystem]::CreateDirectory($target)

        [Ansible.Link.LinkUtil]::CreateLink($path, $target, "SymbolicLink")
        [Ansible.Link.LinkUtil]::DeleteLink($path)

        [Ansible.IO.FileSystem]::DirectoryExists($path) | Assert-Equals -Expected $false
    }

    "Delete a file symbolic link" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        $target = [Ansible.IO.Path]::Combine($test_path, "target.txt")
        $file_h = [Ansible.IO.FileSystem]::CreateFile($target, "CreateNew", "Read", "None", "None")
        $file_h.Dispose()

        [Ansible.Link.LinkUtil]::CreateLink($path, $target, "SymbolicLink")
        [Ansible.Link.LinkUtil]::DeleteLink($path)

        [Ansible.IO.FileSystem]::FileExists($path) | Assert-Equals -Expected $false
    }

    "Delete a relative directory symbolic link" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine(".", "target")
        $target_abs = [Ansible.IO.Path]::Combine($test_path, "target")
        [Ansible.IO.FileSystem]::CreateDirectory($target_abs)

        [Ansible.Link.LinkUtil]::CreateLink($path, $target, "SymbolicLink")
        [Ansible.Link.LinkUtil]::DeleteLink($path)

        [Ansible.IO.FileSystem]::DirectoryExists($path) | Assert-Equals -Expected $false
    }

    "Delete a relative file symbolic link" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        $target = [Ansible.IO.Path]::Combine(".", "target.txt")
        $target_abs = [Ansible.IO.Path]::Combine($test_path, "target.txt")
        $file_h = [Ansible.IO.FileSystem]::CreateFile($target_abs, "CreateNew", "Read", "None", "None")
        $file_h.Dispose()

        [Ansible.Link.LinkUtil]::CreateLink($path, $target, "SymbolicLink")
        [Ansible.Link.LinkUtil]::DeleteLink($path)

        [Ansible.IO.FileSystem]::FileExists($path) | Assert-Equals -Expected $false
    }

    "Delete a directory symbolic link with missing target" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")

        [Ansible.Link.LinkUtil]::CreateLink($path, $target, "SymbolicLink")
        [Ansible.Link.LinkUtil]::DeleteLink($path)

        [Ansible.IO.FileSystem]::DirectoryExists($path) | Assert-Equals -Expected $false
    }

    "Delete a file symbolic link with a missing target" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        $target = [Ansible.IO.Path]::Combine($test_path, "target.txt")

        [Ansible.Link.LinkUtil]::CreateLink($path, $target, "SymbolicLink")
        [Ansible.Link.LinkUtil]::DeleteLink($path)

        [Ansible.IO.FileSystem]::FileExists($path) | Assert-Equals -Expected $false
    }

    "Create junction point to relative path - failure" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine(".", "target")

        $failed = $false
        try {
            [Ansible.Link.LinkUtil]::CreateLink($path, $target, "JunctionPoint")
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.ArgumentException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "Cannot create junction point because target '$target' is not an absolute path."
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Create junction point to file - failure" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "file.txt")
        $file_h = [Ansible.IO.FileSystem]::CreateFile($target, "CreateNew", "Write", "None", "None")
        $file_h.Dispose()

        $failed = $false
        try {
            [Ansible.Link.LinkUtil]::CreateLink($path, $target, "JunctionPoint")
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.ArgumentException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "Cannot create junction point because target '$target' is a file."
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Create junction point to directory" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")
        [Ansible.IO.FileSystem]::CreateDirectory($target)

        [Ansible.Link.LinkUtil]::CreateLink($path, $target, "JunctionPoint")
        $actual = [Ansible.Link.LinkUtil]::GetLinkInfo($path)

        if ($test_path.StartsWith("\\?\")) {
            # Need to remove the \\?\ from the target path
            $expected_sub_name = "\??\$($target.Substring(4))"
        } else {
            $expected_sub_name = "\??\$target"
        }

        ([Ansible.IO.FileSystem]::DirectoryExists($path)) | Assert-Equals -Expected $true
        $actual.GetType().FullName | Assert-Equals -Expected "Ansible.Link.LinkInfo"
        $actual.Type | Assert-Equals -Expected ([Ansible.Link.LinkType]::JunctionPoint)
        $actual.PrintName | Assert-Equals -Expected $target
        $actual.SubstituteName | Assert-Equals -Expected $expected_sub_name
        $actual.AbsolutePath | Assert-Equals -Expected $target
        $actual.TargetPath | Assert-Equals -Expected $target
        $actual.HardTargets.Length | Assert-Equals -Expected 0
    }

    "Create junction point to missing directory" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")

        [Ansible.Link.LinkUtil]::CreateLink($path, $target, "JunctionPoint")
        $actual = [Ansible.Link.LinkUtil]::GetLinkInfo($path)

        if ($test_path.StartsWith("\\?\")) {
            # Need to remove the \\?\ from the target path
            $expected_sub_name = "\??\$($target.Substring(4))"
        } else {
            $expected_sub_name = "\??\$target"
        }

        ([Ansible.IO.FileSystem]::DirectoryExists($path)) | Assert-Equals -Expected $true
        $actual.GetType().FullName | Assert-Equals -Expected "Ansible.Link.LinkInfo"
        $actual.Type | Assert-Equals -Expected ([Ansible.Link.LinkType]::JunctionPoint)
        $actual.PrintName | Assert-Equals -Expected $target
        $actual.SubstituteName | Assert-Equals -Expected $expected_sub_name
        $actual.AbsolutePath | Assert-Equals -Expected $target
        $actual.TargetPath | Assert-Equals -Expected $target
        $actual.HardTargets.Length | Assert-Equals -Expected 0
    }

    "Create junction point that replaces empty directory" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "source")
        [Ansible.IO.FileSystem]::CreateDirectory($path)
        $target = [Ansible.IO.Path]::Combine($test_path, "target")
        [Ansible.IO.FileSystem]::CreateDirectory($target)

        [Ansible.Link.LinkUtil]::CreateLink($path, $target, "JunctionPoint")
        $actual = [Ansible.Link.LinkUtil]::GetLinkInfo($path)

        if ($test_path.StartsWith("\\?\")) {
            # Need to remove the \\?\ from the target path
            $expected_sub_name = "\??\$($target.Substring(4))"
        } else {
            $expected_sub_name = "\??\$target"
        }

        ([Ansible.IO.FileSystem]::DirectoryExists($path)) | Assert-Equals -Expected $true
        $actual.GetType().FullName | Assert-Equals -Expected "Ansible.Link.LinkInfo"
        $actual.Type | Assert-Equals -Expected ([Ansible.Link.LinkType]::JunctionPoint)
        $actual.PrintName | Assert-Equals -Expected $target
        $actual.SubstituteName | Assert-Equals -Expected $expected_sub_name
        $actual.AbsolutePath | Assert-Equals -Expected $target
        $actual.TargetPath | Assert-Equals -Expected $target
        $actual.HardTargets.Length | Assert-Equals -Expected 0
    }

    "Create junction point that replaces non empty directory - fail" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "source")
        [Ansible.IO.FileSystem]::CreateDirectory([Ansible.IO.Path]::Combine($path, "orig"))
        $target = [Ansible.IO.Path]::Combine($test_path, "target")

        $failed = $false
        try {
            [Ansible.Link.LinkUtil]::CreateLink($path, $target, "JunctionPoint")
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.IOException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "The directory is not empty: '$path'"
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Delete junction point" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")
        [Ansible.IO.FileSystem]::CreateDirectory($target)

        [Ansible.Link.LinkUtil]::CreateLink($path, $target, "JunctionPoint")
        [Ansible.Link.LinkUtil]::DeleteLink($path)

        [Ansible.IO.FileSystem]::DirectoryExists($patH) | Assert-Equals -Expected $false
    }

    "Delete junction point with missing target" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")

        [Ansible.Link.LinkUtil]::CreateLink($path, $target, "JunctionPoint")
        [Ansible.Link.LinkUtil]::DeleteLink($path)

        [Ansible.IO.FileSystem]::DirectoryExists($patH) | Assert-Equals -Expected $false
    }

    "Create hard link to directory - fail" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")
        [Ansible.IO.FileSystem]::CreateDirectory($target)

        $failed = $false
        try {
            [Ansible.Link.LinkUtil]::CreateLink($path, $target, "HardLink")
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.IOException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "The target file '$target' is a directory, not a file."
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Create hard link to missing file - fail" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")

        $failed = $false
        try {
            [Ansible.Link.LinkUtil]::CreateLink($path, $target, "HardLink")
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.FileNotFoundException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "Could not find file '$target'"
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Create hard link" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        $target = [Ansible.IO.Path]::Combine($test_path, "target.txt")
        $file_h = [Ansible.IO.FileSystem]::CreateFile($target, "CreateNew", "Write", "None", "None")
        $file_h.Dispose()

        [Ansible.Link.LinkUtil]::CreateLink($path, $target, "HardLink")
        $actual = [Ansible.Link.LinkUtil]::GetLinkInfo($path)
        $actual.Type | Assert-Equals -Expected ([Ansible.Link.LinkType]::HardLink)
        $actual.HardTargets.Length | Assert-Equals -Expected 2
        ($actual.HardTargets | Sort-Object)[0] | Assert-Equals -Expected $path
        ($actual.HardTargets | Sort-Object)[1] | Assert-Equals -Expected $target

        # Create another link to the same target and verify the HardTarget array is 3
        $new_link = [Ansible.IO.Path]::Combine($test_path, "source2.txt")
        [Ansible.Link.LinkUtil]::CreateLink($new_link, $target, "HardLink")

        $actual = [Ansible.Link.LinkUtil]::GetLinkInfo($path)
        $actual.Type | Assert-Equals -Expected ([Ansible.Link.LinkType]::HardLink)
        $actual.HardTargets.Length | Assert-Equals -Expected 3
        ($actual.HardTargets | Sort-Object)[0] | Assert-Equals -Expected $path
        ($actual.HardTargets | Sort-Object)[1] | Assert-Equals -Expected $new_link
        ($actual.HardTargets | Sort-Object)[2] | Assert-Equals -Expected $target
    }

    "Create hard link to relative target" = {
        # Cannot change dir to path that exceeds MAX_PATH so skip that scenario
        if ($test_path.StartsWith("\\?\")) {
            return
        }

        $path = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine(".", "target")
        $target_abs = [Ansible.IO.Path]::Combine($test_path, "target")
        $file_h = [Ansible.IO.FileSystem]::CreateFile($target_abs, "CreateNew", "Write", "None", "None")
        $file_h.Dispose()

        $orig_cwd = [System.Environment]::CurrentDirectory
        try {
            # Relative paths are resolved in creation based on the cwd not relative to the link path
            [System.Environment]::CurrentDirectory = $test_path
            [Ansible.Link.LinkUtil]::CreateLink($path, $target, "HardLink")
        } finally {
            [System.Environment]::CurrentDirectory = $orig_cwd
        }

        $actual = [Ansible.Link.LinkUtil]::GetLinkInfo($path)
        $actual.Type | Assert-Equals -Expected ([Ansible.Link.LinkType]::HardLink)
        $actual.HardTargets.Length | Assert-Equals -Expected 2
        ($actual.HardTargets | Sort-Object)[0] | Assert-Equals -Expected $path
        ($actual.HardTargets | Sort-Object)[1] | Assert-Equals -Expected $target_abs
    }

    "Read hard link with no rights to link" = {
        if ($test_path.StartsWith("\\?\")) {
            # We use some .NET APIs to set the permissions which fail on a long path. Just skip that test for now.
            return
        }

        # Create parent path that we have no rights to
        $parent_path = [Ansible.IO.Path]::Combine($test_path, "parent")
        [Ansible.IO.FileSystem]::CreateDirectory($parent_path)

        $path = [Ansible.IO.Path]::Combine($parent_path, "source.txt")
        $target = [Ansible.IO.Path]::Combine($parent_path, "target.txt")
        $file_h = [Ansible.IO.FileSystem]::CreateFile($target, "CreateNew", "Write", "None", "None")
        $file_h.Dispose()
        [Ansible.Link.LinkUtil]::CreateLink($path, $target, "HardLink")

        # Sets a an empty DACL (no permissions) and a different group/owner from the current user.
        $system_sid = New-Object -TypeName System.Security.Principal.SecurityIdentifier -ArgumentList "S-1-5-18"
        $acl = New-Object -TypeName System.Security.AccessControl.DirectorySecurity
        $acl.SetGroup($system_sid)
        $acl.SetOwner($system_sid)
        $acl.SetAccessRuleProtection($true, $false)
        [System.IO.Directory]::SetAccessControl($parent_path, $acl)

        $failed = $false
        try {
            # Even with SeBackupPrivilege we won't be able to get this info
            [Ansible.Link.LinkUtil]::GetLinkInfo($path)
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.UnauthorizedAccessException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "Access to the path '$path' is denied."
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Delete hard link" = {
        $path = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        $new_link = [Ansible.IO.Path]::Combine($test_path, "source2.txt")
        $target = [Ansible.IO.Path]::Combine($test_path, "target.txt")
        $file_h = [Ansible.IO.FileSystem]::CreateFile($target, "CreateNew", "Write", "None", "None")
        $file_h.Dispose()

        [Ansible.Link.LinkUtil]::CreateLink($path, $target, "HardLink")
        [Ansible.Link.LinkUtil]::CreateLink($new_link, $target, "HardLink")

        [Ansible.Link.LinkUtil]::DeleteLink($path)

        [Ansible.IO.FileSystem]::FileExists($path) | Assert-Equals -Expected $false
        [Ansible.IO.FileSystem]::FileExists($new_link) | Assert-Equals -Expected $true
        [Ansible.IO.FileSystem]::FileExists($target) | Assert-Equals -Expected $true

        [Ansible.Link.LinkUtil]::DeleteLink($new_link)

        [Ansible.IO.FileSystem]::FileExists($path) | Assert-Equals -Expected $false
        [Ansible.IO.FileSystem]::FileExists($new_link) | Assert-Equals -Expected $false
        [Ansible.IO.FileSystem]::FileExists($target) | Assert-Equals -Expected $true
    }
}

foreach ($test_impl in $tests.GetEnumerator()) {
    # Run each test with a normal path and a path that exceeds MAX_PATH
    $test_path = [Ansible.IO.Path]::Combine($module.Tmpdir, "short")
    Clear-Directory -Path $test_path
    $test = $test_impl.Key
    &$test_impl.Value

    $test_path = [Ansible.IO.Path]::Combine("\\?\$($module.Tmpdir)", "a" * 255)
    Clear-Directory -Path $test_path
    $test = "$($test_impl.Key) - MAX_PATH"
    &$test_impl.Value
}

$module.Result.data = "success"
$module.ExitJson()
