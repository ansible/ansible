#!powershell

#AnsibleRequires -CSharpUtil Ansible.Basic
#AnsibleRequires -CSharpUtil Ansible.Link
#AnsibleRequires -CSharpUtil Ansible.IO

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

Function Set-AnsibleContent {
    [CmdletBinding()]
    Param (
        [Parameter(Mandatory=$true)][System.String]$Path,
        [Parameter(Mandatory=$true)][System.String]$Value
    )

    $file_h = [Ansible.IO.FileSystem]::CreateFile($Path, "Create", "Write", "None", "None")

    try {
        $fs = New-Object -TypeName System.IO.FileStream -ArgumentList $file_h, "Write"

        try {
            $bytes = [System.Text.Encoding]::UTF8.GetBytes($Value)
            $fs.Write($bytes, 0, $bytes.Length)
        } finally {
            $fs.Dispose()
        }
    } finally {
        $file_h.Dispose()
    }
}

Function Get-AnsibleContent {
    [CmdletBinding()]
    Param (
        [Parameter(Mandatory=$true)][System.String]$Path
    )

    $file_h = [Ansible.IO.FileSystem]::CreateFile($Path, "Open", "Read", "None", "None")

    try {
        $fs = New-Object -TypeName System.IO.FileStream -ArgumentList $file_h, "Read"

        try {
            $bytes = New-Object -TypeName byte[] -ArgumentList $fs.Length
            $fs.Read($bytes, 0, $bytes.Length)
            [System.Text.Encoding]::UTF8.GetString($bytes)
        } finally {
            $fs.Dispose()
        }
    } finally {
        $file_h.Dispose()
    }
}

Function Get-Pagefile {
    $pagefile = $null
    $cs = Get-CimInstance -ClassName Win32_ComputerSystem
    if ($cs.AutomaticManagedPagefile) {
        $pagefile = "$($env:SystemRoot.Substring(0, 1)):\pagefile.sys"
    } else {
        $pf = Get-CimInstance -ClassName Win32_PageFileSetting
        if ($null -ne $pf) {
            $pagefile = $pf[0].Name
        }
    }
    return $pagefile
}

Function Set-RestrictedSD {
    [CmdletBinding()]
    Param (
        [Parameter(Mandatory=$true)][System.String]$Path
    )

    # Sets a an empty DACL (no permissions) and a different group/owner from the current user.
    $system_sid = New-Object -TypeName System.Security.Principal.SecurityIdentifier -ArgumentList "S-1-5-18"
    $acl = New-Object -TypeName System.Security.AccessControl.DirectorySecurity
    $acl.SetGroup($system_sid)
    $acl.SetOwner($system_sid)
    $acl.SetAccessRuleProtection($true, $false)
    [System.IO.Directory]::SetAccessControl($Path, $acl)
}

$tests = [Ordered]@{
    "Copy a directory that does not exist" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")

        $failed = $false
        try {
            [Ansible.IO.FileSystem]::CopyDirectory($source, $target, $false, $false)
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.DirectoryNotFoundException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "Could not find a part of the path '$source'."
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Copy an directory to non-existing dest" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")
        [Ansible.IO.FileSystem]::CreateDirectory($source)

        $failed = $false
        try {
            [Ansible.IO.FileSystem]::CopyDirectory($source, $target, $false, $false)
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.DirectoryNotFoundException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "Could not find a part of the path '$target'."
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Copy a directory, source is a file" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")
        [Ansible.IO.FileSystem]::CreateDirectory($target)
        Set-AnsibleContent -Path $source -Value "Hi"

        $failed = $true
        try {
            [Ansible.IO.FileSystem]::CopyDirectory($source, $target, $false, $false)
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.IOException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "The source path '$source' is a file, not a directory."
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Copy a directory, dest is a file" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")
        [Ansible.IO.FileSystem]::CreateDirectory($source)
        Set-AnsibleContent -Path $target -Value "Hi"

        $failed = $true
        try {
            [Ansible.IO.FileSystem]::CopyDirectory($source, $target, $false, $false)
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.IOException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "The target path '$target' is a file, not a directory."
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Copy an empty directory without recurse" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")
        [Ansible.IO.FileSystem]::CreateDirectory($source)
        [Ansible.IO.FileSystem]::CreateDirectory($target)

        [Ansible.IO.FileSystem]::CopyDirectory($source, $target, $false, $false)

        [Ansible.IO.FileSystem]::DirectoryExists([Ansible.IO.Path]::Combine($target, "source")) | Assert-Equals -Expected $true
        $actual = [System.Collections.Generic.List`1[String]]@()
        foreach ($path in [Ansible.IO.FileSystem]::EnumerateFolder($target, "*", "AllDirectories", $true, $true)) {
            $actual.Add($path)
        }
        $actual.Count | Assert-Equals -Expected 1
        $actual[0] | Assert-Equals -Expected ([Ansible.IO.Path]::Combine($target, "source"))
    }

    "Copy an empty directory with recurse" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")
        [Ansible.IO.FileSystem]::CreateDirectory($source)
        [Ansible.IO.FileSystem]::CreateDirectory($target)

        [Ansible.IO.FileSystem]::CopyDirectory($source, $target, $true, $false)

        [Ansible.IO.FileSystem]::DirectoryExists([Ansible.IO.Path]::Combine($target, "source")) | Assert-Equals -Expected $true
        $actual = [System.Collections.Generic.List`1[String]]@()
        foreach ($path in [Ansible.IO.FileSystem]::EnumerateFolder($target, "*", "AllDirectories", $true, $true)) {
            $actual.Add($path)
        }
        $actual.Count | Assert-Equals -Expected 1
        $actual[0] | Assert-Equals -Expected ([Ansible.IO.Path]::Combine($target, "source"))
    }

    "Copy a directory with files without recurse" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")
        [Ansible.IO.FileSystem]::CreateDirectory($source)
        [Ansible.IO.FileSystem]::CreateDirectory($target)
        Set-AnsibleContent -Path ([Ansible.IO.Path]::Combine($source, "file.txt")) -Value "foo"

        [Ansible.IO.FileSystem]::CopyDirectory($source, $target, $false, $false)

        [Ansible.IO.FileSystem]::DirectoryExists([Ansible.IO.Path]::Combine($target, "source")) | Assert-Equals -Expected $true
        [Ansible.IO.FileSystem]::FileExists([Ansible.IO.Path]::Combine($target, "source", "file.txt")) | Assert-Equals -Expected $false
    }

    "Copy a directory with files with recurse" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")
        [Ansible.IO.FileSystem]::CreateDirectory($source)
        [Ansible.IO.FileSystem]::CreateDirectory($target)
        Set-AnsibleContent -Path ([Ansible.IO.Path]::Combine($source, "file.txt")) -Value "foo"

        [Ansible.IO.FileSystem]::CopyDirectory($source, $target, $true, $false)

        [Ansible.IO.FileSystem]::DirectoryExists([Ansible.IO.Path]::Combine($target, "source")) | Assert-Equals -Expected $true
        [Ansible.IO.FileSystem]::FileExists([Ansible.IO.Path]::Combine($target, "source", "file.txt")) | Assert-Equals -Expected $true
        Get-AnsibleContent -Path ([Ansible.IO.Path]::Combine($target, "source", "file.txt")) | Assert-Equals -Expected "foo"
    }

    "Copy a directory with files and folders without recurse" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")
        [Ansible.IO.FileSystem]::CreateDirectory($source)
        [Ansible.IO.FileSystem]::CreateDirectory($target)

        $sub_folder = [Ansible.IO.Path]::Combine($source, "folder")
        [Ansible.IO.FileSystem]::CreateDirectory($sub_folder)
        Set-AnsibleContent -Path ([Ansible.IO.Path]::Combine($source, "file.txt")) -Value "foo"
        Set-AnsibleContent -Path ([Ansible.IO.Path]::Combine($sub_folder, "file.txt")) -Value "bar"

        [Ansible.IO.FileSystem]::CopyDirectory($source, $target, $false, $false)

        [Ansible.IO.FileSystem]::DirectoryExists([Ansible.IO.Path]::Combine($target, "source")) | Assert-Equals -Expected $true
        $dir_contents = [System.Collections.Generic.List`1[String]]@()
        foreach ($path in [Ansible.IO.FileSystem]::EnumerateFolder($target, "*", "AllDirectories", $true, $true)) {
            $dir_contents.Add($path)
        }
        $dir_contents.Count | Assert-Equals -Expected 1
        $dir_contents[0] | Assert-Equals -Expected ([Ansible.IO.Path]::Combine($target, "source"))
    }

    "Copy a directory with files and folders with recurse" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")
        [Ansible.IO.FileSystem]::CreateDirectory($source)
        [Ansible.IO.FileSystem]::CreateDirectory($target)

        $sub_folder = [Ansible.IO.Path]::Combine($source, "folder")
        [Ansible.IO.FileSystem]::CreateDirectory($sub_folder)
        Set-AnsibleContent -Path ([Ansible.IO.Path]::Combine($source, "file.txt")) -Value "foo"
        Set-AnsibleContent -Path ([Ansible.IO.Path]::Combine($sub_folder, "file.txt")) -Value "bar"

        [Ansible.IO.FileSystem]::CopyDirectory($source, $target, $true, $false)

        [Ansible.IO.FileSystem]::DirectoryExists([Ansible.IO.Path]::Combine($target, "source")) | Assert-Equals -Expected $true
        $dir_contents = [System.Collections.Generic.List`1[String]]@()
        foreach ($path in [Ansible.IO.FileSystem]::EnumerateFolder($target, "*", "AllDirectories", $true, $true)) {
            $dir_contents.Add($path)
        }
        $dir_contents = $dir_contents | Sort-Object
        $dir_contents.Count | Assert-Equals -Expected 4
        $dir_contents[0] | Assert-Equals -Expected ([Ansible.IO.Path]::Combine($target, "source"))
        $dir_contents[1] | Assert-Equals -Expected ([Ansible.IO.Path]::Combine($target, "source", "file.txt"))
        $dir_contents[2] | Assert-Equals -Expected ([Ansible.IO.Path]::Combine($target, "source", "folder"))
        $dir_contents[3] | Assert-Equals -Expected ([Ansible.IO.Path]::Combine($target, "source", "folder", "file.txt"))
        Get-AnsibleContent -Path ([Ansible.IO.Path]::Combine($target, "source", "file.txt")) | Assert-Equals -Expected "foo"
        Get-AnsibleContent -Path ([Ansible.IO.Path]::Combine($target, "source", "folder", "file.txt")) | Assert-Equals -Expected "bar"
    }

    "Copy a directory with a link" = {
        # This verifies it doesn't choke on links and replicates the behaviour of Copy-Item
        $source = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")
        [Ansible.IO.FileSystem]::CreateDirectory($source)
        [Ansible.IO.FileSystem]::CreateDirectory($target)

        $sub_folder = [Ansible.IO.Path]::Combine($source, "folder")
        [Ansible.IO.FileSystem]::CreateDirectory($sub_folder)
        Set-AnsibleContent -Path ([Ansible.IO.Path]::Combine($source, "file.txt")) -Value "foo"
        Set-AnsibleContent -Path ([Ansible.IO.Path]::Combine($source, "folder", "file.txt")) -Value "bar"
        [Ansible.Link.LinkUtil]::CreateLink([Ansible.IO.Path]::Combine($source, "sym-link"), $sub_folder, "SymbolicLink")
        [Ansible.Link.LinkUtil]::CreateLink([Ansible.IO.Path]::Combine($source, "sym-link-missing"), "missing", "SymbolicLink")
        [Ansible.Link.LinkUtil]::CreateLink([Ansible.IO.Path]::Combine($source, "sym-link.txt"), [Ansible.IO.Path]::Combine($sub_folder, "file.txt"), "SymbolicLink")
        [Ansible.Link.LinkUtil]::CreateLink([Ansible.IO.Path]::Combine($source, "sym-link-missing.txt"), "missing.txt", "SymbolicLink")
        [Ansible.Link.LinkUtil]::CreateLink([Ansible.IO.Path]::Combine($source, "hard.txt"), [Ansible.IO.Path]::Combine($sub_folder, "file.txt"), "HardLink")

        # Junction points don't work over UNC paths, adjust the test slightly for this scenario
        $expected_count = 10
        if (-not ($test_path.StartsWith("\\") -or $test_path.StartsWith("\\?\UNC"))) {
            $expected_count = 12
            [Ansible.Link.LinkUtil]::CreateLink([Ansible.IO.Path]::Combine($source, "zzjunction"), $sub_folder, "JunctionPoint")
        }

        [Ansible.IO.FileSystem]::CopyDirectory($source, $target, $true, $false)

        [Ansible.IO.FileSystem]::DirectoryExists([Ansible.IO.Path]::Combine($target, "source")) | Assert-Equals -Expected $true
        $dir_contents = [System.Collections.Generic.List`1[String]]@()
        foreach ($path in [Ansible.IO.FileSystem]::EnumerateFolder($target, "*", "AllDirectories", $true, $true)) {
            $dir_contents.Add($path)
        }
        $dir_contents = $dir_contents | Sort-Object
        $dir_contents.Count | Assert-Equals -Expected $expected_count
        $dir_contents[0] | Assert-Equals -Expected ([Ansible.IO.Path]::Combine($target, "source"))
        $dir_contents[1] | Assert-Equals -Expected ([Ansible.IO.Path]::Combine($target, "source", "file.txt"))
        $dir_contents[2] | Assert-Equals -Expected ([Ansible.IO.Path]::Combine($target, "source", "folder"))
        $dir_contents[3] | Assert-Equals -Expected ([Ansible.IO.Path]::Combine($target, "source", "folder", "file.txt"))
        $dir_contents[4] | Assert-Equals -Expected ([Ansible.IO.Path]::Combine($target, "source", "hard.txt"))
        $dir_contents[5] | Assert-Equals -Expected ([Ansible.IO.Path]::Combine($target, "source", "sym-link"))
        $dir_contents[6] | Assert-Equals -Expected ([Ansible.IO.Path]::Combine($target, "source", "sym-link.txt"))
        $dir_contents[7] | Assert-Equals -Expected ([Ansible.IO.Path]::Combine($target, "source", "sym-link", "file.txt"))
        $dir_contents[8] | Assert-Equals -Expected ([Ansible.IO.Path]::Combine($target, "source", "sym-link-missing"))
        $dir_contents[9] | Assert-Equals -Expected ([Ansible.IO.Path]::Combine($target, "source", "sym-link-missing.txt"))

        Get-AnsibleContent -Path ([Ansible.IO.Path]::Combine($target, "source", "file.txt")) | Assert-Equals -Expected "foo"
        Get-AnsibleContent -Path ([Ansible.IO.Path]::Combine($target, "source", "folder", "file.txt")) | Assert-Equals -Expected "bar"
        Get-AnsibleContent -Path ([Ansible.IO.Path]::Combine($target, "source", "hard.txt")) | Assert-Equals -Expected "bar"
        Get-AnsibleContent -Path ([Ansible.IO.Path]::Combine($target, "source", "sym-link.txt")) | Assert-Equals -Expected "bar"
        Get-AnsibleContent -Path ([Ansible.IO.Path]::Combine($target, "source", "sym-link", "file.txt")) | Assert-Equals -Expected "bar"
        Get-AnsibleContent -Path ([Ansible.IO.Path]::Combine($target, "source", "folder", "file.txt")) | Assert-Equals -Expected "bar"
        Get-AnsibleContent -Path ([Ansible.IO.Path]::Combine($target, "source", "sym-link", "file.txt")) | Assert-Equals -Expected "bar"
        Get-AnsibleContent -Path ([Ansible.IO.Path]::Combine($target, "source", "sym-link-missing.txt")) | Assert-Equals -Expected ""

        # Change contents of original link sources to ensure the copies are not actual links
        Set-AnsibleContent -Path ([Ansible.IO.Path]::Combine($target, "source", "file.txt")) -Value "foo2"
        Set-AnsibleContent -Path ([Ansible.IO.Path]::Combine($target, "source", "folder", "file.txt")) -Value "bar2"

        Get-AnsibleContent -Path ([Ansible.IO.Path]::Combine($target, "source", "hard.txt")) | Assert-Equals -Expected "bar"
        Get-AnsibleContent -Path ([Ansible.IO.Path]::Combine($target, "source", "sym-link.txt")) | Assert-Equals -Expected "bar"
        Get-AnsibleContent -Path ([Ansible.IO.Path]::Combine($target, "source", "sym-link", "file.txt")) | Assert-Equals -Expected "bar"
        Get-AnsibleContent -Path ([Ansible.IO.Path]::Combine($target, "source", "sym-link", "file.txt")) | Assert-Equals -Expected "bar"

        if (-not ($test_path.StartsWith("\\") -or $test_path.StartsWith("\\?\UNC"))) {
            $dir_contents[10] | Assert-Equals -Expected ([Ansible.IO.Path]::Combine($target, "source", "zzjunction"))
            $dir_contents[11] | Assert-Equals -Expected ([Ansible.IO.Path]::Combine($target, "source", "zzjunction", "file.txt"))
            Get-AnsibleContent -Path ([Ansible.IO.Path]::Combine($target, "source", "zzjunction", "file.txt")) | Assert-Equals -Expected "bar"
        }
    }

    "Copy directory without overwrite" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")
        [Ansible.IO.FileSystem]::CreateDirectory($source)
        [Ansible.IO.FileSystem]::CreateDirectory($target)

        $sub_folder = [Ansible.IO.Path]::Combine($source, "folder")
        [Ansible.IO.FileSystem]::CreateDirectory($sub_folder)
        Set-AnsibleContent -Path ([Ansible.IO.Path]::Combine($source, "file.txt")) -Value "foo"
        Set-AnsibleContent -Path ([Ansible.IO.Path]::Combine($source, "folder", "file.txt")) -Value "bar"

        # Create dest dir structure to ensure it doesn't fail if only dirs are there
        [Ansible.IO.FileSystem]::CreateDirectory([Ansible.IO.Path]::Combine($target, "source", "folder"))
        [Ansible.IO.FileSystem]::CopyDirectory($source, $target, $true, $false)

        # Now that the files have been copied, it should fail without overwrite
        try {
            [Ansible.IO.FileSystem]::CopyDirectory($source, $target, $true, $false)
        } catch {
            $target_file = [Ansible.IO.Path]::Combine($target, "source", "file.txt")
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.IOException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "The file '$target_file' already exists."
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Copy directory with broken file symlink without overwrite" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")
        [Ansible.IO.FileSystem]::CreateDirectory($source)
        [Ansible.IO.FileSystem]::CreateDirectory($target)
        [Ansible.Link.LinkUtil]::CreateLink([Ansible.IO.Path]::Combine($source, "sym-link.txt"), "missing", "SymbolicLink")

        # Copy it once
        [Ansible.IO.FileSystem]::CopyDirectory($source, $target, $true, $false)

        # Set the content of the copied blank symlink so we can test it wasn't changed in the next call
        $target_file = [Ansible.IO.Path]::Combine($target, "source", "sym-link.txt")
        [Ansible.IO.FileSystem]::FileExists($target_file) | Assert-Equals -Expected $true
        Set-AnsibleContent -Path $target_file -Value "foo"

        try {
            # Copy it again expecting a failure
            [Ansible.IO.FileSystem]::CopyDirectory($source, $target, $true, $false)
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.IOException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "The file '$target_file' already exists."
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
        Get-AnsibleContent -Path $target_file | Assert-Equals -Expected "foo"
    }

    "Copy directory with broken file symlink with overwrite" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")
        [Ansible.IO.FileSystem]::CreateDirectory($source)
        [Ansible.IO.FileSystem]::CreateDirectory($target)
        [Ansible.Link.LinkUtil]::CreateLink([Ansible.IO.Path]::Combine($source, "sym-link.txt"), "missing", "SymbolicLink")

        # Copy it once
        [Ansible.IO.FileSystem]::CopyDirectory($source, $target, $true, $false)

        # Set the content of the copied blank symlink so we can test it was changed in the next call
        $target_file = [Ansible.IO.Path]::Combine($target, "source", "sym-link.txt")
        [Ansible.IO.FileSystem]::FileExists($target_file) | Assert-Equals -Expected $true
        Set-AnsibleContent -Path $target_file -Value "foo"

        [Ansible.IO.FileSystem]::CopyDirectory($source, $target, $true, $true)
        Get-AnsibleContent -Path $target_file | Assert-Equals -Expected ""
    }

    "Copy directory with overwrite" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")
        [Ansible.IO.FileSystem]::CreateDirectory($source)
        [Ansible.IO.FileSystem]::CreateDirectory($target)

        $sub_folder = [Ansible.IO.Path]::Combine($source, "folder")
        [Ansible.IO.FileSystem]::CreateDirectory($sub_folder)
        Set-AnsibleContent -Path ([Ansible.IO.Path]::Combine($source, "file.txt")) -Value "foo"
        Set-AnsibleContent -Path ([Ansible.IO.Path]::Combine($source, "folder", "file.txt")) -Value "bar"

        # Copy once
        [Ansible.IO.FileSystem]::CopyDirectory($source, $target, $true, $false)

        # Edit copied file to ensure the next operation overwrites it
        Set-AnsibleContent -Path ([Ansible.IO.Path]::Combine($target, "source", "file.txt")) -Value "foo2"

        # Copy again with overwrite
        [Ansible.IO.FileSystem]::CopyDirectory($source, $target, $true, $true)
        Get-AnsibleContent -Path ([Ansible.IO.Path]::Combine($target, "source", "file.txt")) | Assert-Equals -Expected "foo"
        Get-AnsibleContent -Path ([Ansible.IO.Path]::Combine($target, "source", "folder", "file.txt")) | Assert-Equals -Expected "bar"
    }

    "Copy a file" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        Set-AnsibleContent -Path $source -Value "Hello World"
        $target = [Ansible.IO.Path]::Combine($test_path, "target.txt")

        [Ansible.IO.FileSystem]::CopyFile($source, $target, $false)

        [Ansible.IO.FileSystem]::FileExists($target) | Assert-Equals -Expected $true
        $actual = Get-AnsibleContent -Path $target
        $actual | Assert-Equals -Expected "Hello World"
    }

    "Copy a file fail to overwrite" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        Set-AnsibleContent -Path $source -Value "Hello World"
        $target = [Ansible.IO.Path]::Combine($test_path, "target.txt")

        [Ansible.IO.FileSystem]::CopyFile($source, $target, $false)

        $failed = $false
        try {
            [Ansible.IO.FileSystem]::CopyFile($source, $target, $false)
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.IOException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "The file '$target' already exists."
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Copy a file with overwrite" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        Set-AnsibleContent -Path $source -Value "Hello World"
        $target = [Ansible.IO.Path]::Combine($test_path, "target.txt")
        [Ansible.IO.FileSystem]::CopyFile($source, $target, $false)
        Set-AnsibleContent -Path $source -Value "Hello back"

        [Ansible.IO.FileSystem]::CopyFile($source, $target, $true)

        [Ansible.IO.FileSystem]::FileExists($target) | Assert-Equals -Expected $true
        $actual = Get-AnsibleContent -Path $target
        $actual | Assert-Equals -Expected "Hello back"
    }

    "Copy a file fail with dir source" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")
        [Ansible.IO.FileSystem]::CreateDirectory($source)

        $failed = $false
        try {
            [Ansible.IO.FileSystem]::CopyFile($source, $target, $false)
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.IOException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "The source file '$source' is a directory, not a file."
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Copy a file fail with dir target" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")
        Set-AnsibleContent -Path $source -Value "abc"
        [Ansible.IO.FileSystem]::CreateDirectory($target)

        $failed = $false
        try {
            [Ansible.IO.FileSystem]::CopyFile($source, $target, $false)
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.IOException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "The target file '$target' is a directory, not a file."
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Copy a file fail with missing source" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        $target = [Ansible.IO.Path]::Combine($test_path, "target.txt")

        $failed = $false
        try {
            [Ansible.IO.FileSystem]::CopyFile($source, $target, $false)
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.FileNotFoundException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "Could not find file '$source'"
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Copy a file with custom attributes" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        $target = [Ansible.IO.Path]::Combine($test_path, "target.txt")
        Set-AnsibleContent -Path $source -Value "a"
        Set-AnsibleContent -Path $target -Value "b"
        [Ansible.IO.FileSystem]::SetAttributes($source, "Hidden, ReadOnly")

        [Ansible.IO.FileSystem]::CopyFile($source, $target, $true)
        Get-AnsibleContent -Path $target | Assert-Equals -Expected "a"

        $actual = [Ansible.IO.FileSystem]::GetFileAttributeData($target)
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::Hidden) | Assert-Equals -Expected $true
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::ReadOnly) | Assert-Equals -Expected $true
    }

    "Copy a file with read only attribute as dest" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        $target = [Ansible.IO.Path]::Combine($test_path, "target.txt")
        Set-AnsibleContent -Path $source -Value "a"
        Set-AnsibleContent -Path $target -Value "b"
        [Ansible.IO.FileSystem]::SetAttributes($target, "ReadOnly")

        [Ansible.IO.FileSystem]::CopyFile($source, $target, $true)
        Get-AnsibleContent -Path $target | Assert-Equals -Expected "a"
        $actual = [Ansible.IO.FileSystem]::GetFileAttributeData($target)
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::ReadOnly) | Assert-Equals -Expected $false
    }

    "Copy a file with a hidden attribute as dest" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        $target = [Ansible.IO.Path]::Combine($test_path, "target.txt")
        Set-AnsibleContent -Path $source -Value "a"
        Set-AnsibleContent -Path $target -Value "b"
        [Ansible.IO.FileSystem]::SetAttributes($target, "Hidden")

        [Ansible.IO.FileSystem]::CopyFile($source, $target, $true)
        Get-AnsibleContent -Path $target | Assert-Equals -Expected "a"
        $actual = [Ansible.IO.FileSystem]::GetFileAttributeData($target)
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::Hidden) | Assert-Equals -Expected $false
    }

    "Copy a symbolic link file" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        $target = [Ansible.IO.Path]::Combine($test_path, "target.txt")
        $link_target = [Ansible.IO.Path]::Combine($test_path, "link-target.txt")
        Set-AnsibleContent -Path $link_target -Value "abc"
        [Ansible.Link.LinkUtil]::CreateLink($source, $link_target, "SymbolicLink")

        [Ansible.IO.FileSystem]::CopyFile($source, $target, $false)
        [Ansible.IO.FileSystem]::FileExists($target) | Assert-Equals -Expected $true
        Get-AnsibleContent -Path $target | Assert-Equals -Expected "abc"

        # Verify the copied file is a copy of the original target and not an actual symlink
        $actual = [Ansible.IO.FileSystem]::GetFileAttributeData($target)
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::ReparsePoint) | Assert-Equals -Expected $false
    }

    "Copy a broken symbolic link file" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        $target = [Ansible.IO.Path]::Combine($test_path, "target.txt")
        $link_target = [Ansible.IO.Path]::Combine($test_path, "link-target.txt")
        [Ansible.Link.LinkUtil]::CreateLink($source, $link_target, "SymbolicLink")

        [Ansible.IO.FileSystem]::CopyFile($source, $target, $false)
        [Ansible.IO.FileSystem]::FileExists($target) | Assert-Equals -Expected $true
        Get-AnsibleContent -Path $target | Assert-Equals -Expected ""

        # Verify the copied file is a copy of the original target and not an actual symlink
        $actual = [Ansible.IO.FileSystem]::GetFileAttributeData($target)
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::ReparsePoint) | Assert-Equals -Expected $false
    }

    "Copy a hard link" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        $target = [Ansible.IO.Path]::Combine($test_path, "target.txt")
        $link_target = [Ansible.IO.Path]::Combine($test_path, "link-target.txt")
        Set-AnsibleContent -Path $link_target -Value "abc"
        [Ansible.Link.LinkUtil]::CreateLink($source, $link_target, "HardLink")

        [Ansible.IO.FileSystem]::CopyFile($source, $target, $false)
        [Ansible.IO.FileSystem]::FileExists($target) | Assert-Equals -Expected $true
        Get-AnsibleContent -Path $target | Assert-Equals -Expected "abc"

        # Verify the copied file is a copy of the original target and not an actual hard link
        Set-AnsibleContent -Path $link_target -Value "def"
        Get-AnsibleContent -Path $target | Assert-Equals -Expected "abc"
    }

    "Create directory" = {
        $dir_path = [Ansible.IO.Path]::Combine($test_path, "directory")
        [Ansible.IO.FileSystem]::CreateDirectory($dir_path)

        [Ansible.IO.FileSystem]::DirectoryExists($dir_path) | Assert-Equals -Expected $true
    }

    "Create nested directory" = {
        $dir_path = [Ansible.IO.Path]::Combine($test_path, "directory", "nested")
        [Ansible.IO.FileSystem]::CreateDirectory($dir_path)

        [Ansible.IO.FileSystem]::DirectoryExists($dir_path) | Assert-Equals -Expected $true
    }

    "Create directory with file path" = {
        $dir_path = [Ansible.IO.Path]::Combine($test_path, "directory")
        Set-AnsibleContent -Path $dir_path -Value "abc"

        $failed = $false
        try {
            [Ansible.IO.FileSystem]::CreateDirectory($dir_path)
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.IOException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "Cannot create '$dir_path' because a file or directory with the same name already exists."
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Create directory that exists" = {
        $dir_path = [Ansible.IO.Path]::Combine($test_path, "directory")
        [Ansible.IO.FileSystem]::CreateDirectory($dir_path)

        [Ansible.IO.FileSystem]::DirectoryExists($dir_path) | Assert-Equals -Expected $true
        [Ansible.IO.FileSystem]::CreateDirectory($dir_path)
    }

    "Create directory with no permissions" = {
        if ($test_path.StartsWith("\\?\")) {
            # We use some .NET APIs to set the permissions which fail on a long path. Just skip that test for now.
            return
        }

        $base_dir = [Ansible.IO.Path]::Combine($test_path, "directory")
        [Ansible.IO.FileSystem]::CreateDirectory($base_dir)
        Set-RestrictedSD -Path $base_dir

        $dir_path = [Ansible.IO.Path]::Combine($base_dir, "nested")
        [Ansible.IO.FileSystem]::CreateDirectory($dir_path)
        [Ansible.IO.FileSystem]::DirectoryExists($dir_path) | Assert-Equals -Expected $true
    }

    "Create new file" = {
        $file_path = [Ansible.IO.Path]::Combine($test_path, "file.txt")

        $handle = [Ansible.IO.FileSystem]::CreateFile($file_path, "CreateNew", "Read", "None", "None")
        try {
            $handle.IsInvalid | Assert-Equals -Expected $false
            $handle.IsClosed | Assert-Equals -Expected $false
        } finally {
            $handle.Dispose()
        }
        $handle.IsClosed | Assert-Equals -Expected $true

        $failed = $false
        try {
            [Ansible.IO.FileSystem]::CreateFile($file_path, "CreateNew", "Read", "None", "None")
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.IOException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "The file '$file_path' already exists."
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Create new file over existing file" = {
        $file_path = [Ansible.IO.Path]::Combine($test_path, "file.txt")

        $handle = [Ansible.IO.FileSystem]::CreateFile($file_path, "Create", "Read", "None", "None")
        try {
            $handle.IsInvalid | Assert-Equals -Expected $false
            $handle.IsClosed | Assert-Equals -Expected $false
        } finally {
            $handle.Dispose()
        }
        $handle.IsClosed | Assert-Equals -Expected $true
        Set-AnsibleContent -Path $file_path -Value "abc"

        $handle = [Ansible.IO.FileSystem]::CreateFile($file_path, "Create", "Read", "None", "None")
        try {
            $handle.IsInvalid | Assert-Equals -Expected $false
            $handle.IsClosed | Assert-Equals -Expected $false
        } finally {
            $handle.Dispose()
        }
        $handle.IsClosed | Assert-Equals -Expected $true

        # Getting a handle with Create will create a new file, erasing the existing one
        Get-AnsibleContent -Path $file_path | Assert-Equals -Expected ""
    }

    "Open existing file" = {
        $file_path = [Ansible.IO.Path]::Combine($test_path, "file.txt")

        $failed = $false
        try {
            [Ansible.IO.FileSystem]::CreateFile($file_path, "Open", "Read", "None", "None")
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.FileNotFoundException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "Could not find file '$file_path'"
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true

        Set-AnsibleContent -Path $file_path -Value "abc"
        $handle = [Ansible.IO.FileSystem]::CreateFile($file_path, "Open", "Read", "None", "None")
        try {
            $handle.IsInvalid | Assert-Equals -Expected $false
            $handle.IsClosed | Assert-Equals -Expected $false
        } finally {
            $handle.Dispose()
        }
        $handle.IsClosed | Assert-Equals -Expected $true
    }

    "Open existing file or create new" = {
        $file_path = [Ansible.IO.Path]::Combine($test_path, "file.txt")

        $handle = [Ansible.IO.FileSystem]::CreateFile($file_path, "OpenOrCreate", "Read", "None", "None")
        try {
            $handle.IsInvalid | Assert-Equals -Expected $false
            $handle.IsClosed | Assert-Equals -Expected $false
        } finally {
            $handle.Dispose()
        }
        $handle.IsClosed | Assert-Equals -Expected $true
        Set-AnsibleContent -Path $file_path -Value "abc"

        $handle = [Ansible.IO.FileSystem]::CreateFile($file_path, "OpenOrCreate", "Read", "None", "None")
        try {
            $handle.IsInvalid | Assert-Equals -Expected $false
            $handle.IsClosed | Assert-Equals -Expected $false
        } finally {
            $handle.Dispose()
        }
        $handle.IsClosed | Assert-Equals -Expected $true

        Get-AnsibleContent -Path $file_path | Assert-Equals -Expected "abc"
    }

    "Open file without any sharing" = {
        $file_path = [Ansible.IO.Path]::Combine($test_path, "file.txt")

        $handle = [Ansible.IO.FileSystem]::CreateFile($file_path, "Create", "Read", "None", "None")
        try {
            $failed = $true
            try {
                [Ansible.IO.FileSystem]::CreateFile($file_path, "Open", "Read", "Read", "None")
            } catch {
                $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.IOException"
                $_.Exception.InnerException.Message | Assert-Equals -Expected "The process cannot access the file '$file_path' because it is being used by another process."
                $failed = $true
            }
            $failed | Assert-Equals -Expected $true
        } finally {
            $handle.Dispose()
        }
    }

    "Open file with read sharing" = {
        $file_path = [Ansible.IO.Path]::Combine($test_path, "file.txt")

        $handle = [Ansible.IO.FileSystem]::CreateFile($file_path, "Create", "Read", "Read", "None")
        try {
            $sub_handle = [Ansible.IO.FileSystem]::CreateFile($file_path, "Open", "Read", "Read", "None")
            try {
                $sub_handle.IsInvalid | Assert-Equals -Expected $false
                $sub_handle.IsClosed | Assert-Equals -Expected $false
            } finally {
                $sub_handle.Dispose()
            }
            $sub_handle.IsClosed | Assert-Equals -Expected $true

            $failed = $true
            try {
                [Ansible.IO.FileSystem]::CreateFile($file_path, "Open", "Write", "Read", "None")
            } catch {
                $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.IOException"
                $_.Exception.InnerException.Message | Assert-Equals -Expected "The process cannot access the file '$file_path' because it is being used by another process."
                $failed = $true
            }
            $failed | Assert-Equals -Expected $true
        } finally {
            $handle.Dispose()
        }
    }

    "Open file with read/write sharing" = {
        $file_path = [Ansible.IO.Path]::Combine($test_path, "file.txt")

        $handle = [Ansible.IO.FileSystem]::CreateFile($file_path, "Create", "Read", "ReadWrite", "None")
        try {
            $sub_handle = [Ansible.IO.FileSystem]::CreateFile($file_path, "Open", "ReadWrite", "ReadWrite", "None")
            try {
                $sub_handle.IsInvalid | Assert-Equals -Expected $false
                $sub_handle.IsClosed | Assert-Equals -Expected $false
            } finally {
                $sub_handle.Dispose()
            }
            $sub_handle.IsClosed | Assert-Equals -Expected $true
        } finally {
            $handle.Dispose()
        }
    }

    "Open file with delete on close" = {
        $file_path = [Ansible.IO.Path]::Combine($test_path, "file.txt")

        $handle = [Ansible.IO.FileSystem]::CreateFile($file_path, "Create", "Read", "None", "DeleteOnClose")
        try {
            $handle.IsInvalid | Assert-Equals -Expected $false
            $handle.IsClosed | Assert-Equals -Expected $false
            [Ansible.IO.FileSystem]::FileExists($file_path) | Assert-Equals -Expected $true
        } finally {
            $handle.Dispose()
        }
        $handle.IsClosed | Assert-Equals -Expected $true

        [Ansible.IO.FileSystem]::FileExists($file_path) | Assert-Equals -Expected $false
    }

    "Create file in directory with no permissions" = {
        if ($test_path.StartsWith("\\?\")) {
            # We use some .NET APIs to set the permissions which fail on a long path. Just skip that test for now.
            return
        }

        $base_dir = [Ansible.IO.Path]::Combine($test_path, "directory")
        $file_path = [Ansible.IO.Path]::Combine($base_dir, "file.txt")
        [Ansible.IO.FileSystem]::CreateDirectory($base_dir)
        Set-AnsibleContent -Path $file_path -Value "abc"
        Set-RestrictedSD -Path $base_dir

        $failed = $false
        try {
            [Ansible.IO.FileSystem]::CreateFile($file_path, "Open", "Read", "None", "None")
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.UnauthorizedAccessException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "Access to the path '$file_path' is denied."
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true

        $priv_enabler = New-Object -TypeName Ansible.Privilege.PrivilegeEnabler -ArgumentList $true, "SeBackupPrivilege"
        try {
            $handle = [Ansible.IO.FileSystem]::CreateFile($file_path, "Open", "Read", "None", 0x02000000)  # FILE_FLAG_BACKUP_SEMANTICS
            try {
                $handle.IsInvalid | Assert-Equals -Expected $false
                $handle.IsClosed | Assert-Equals -Expected $false
            } finally {
                $handle.Dispose()
            }
            $handle.IsClosed | Assert-Equals -Expected $true
        } finally {
            $priv_enabler.Dispose()
        }
    }

    "CreateFile with directory" = {
        $dir_path = [Ansible.IO.Path]::Combine($test_path, "directory")
        [Ansible.IO.FileSystem]::CreateDirectory($dir_path)

        $handle = [Ansible.IO.FileSystem]::CreateFile($dir_path, "Open", "Read", "None", 0x02000000)
        try {
            $handle.IsInvalid | Assert-Equals -Expected $false
            $handle.IsClosed | Assert-Equals -Expected $false
        } finally {
            $handle.Dispose()
        }
        $handle.IsClosed | Assert-Equals -Expected $true
    }

    "Delete file" = {
        $file_path = [Ansible.IO.Path]::Combine($test_path, "file.txt")
        Set-AnsibleContent -Path $file_path -Value "abc"

        [Ansible.IO.FileSystem]::DeleteFile($file_path)

        [Ansible.IO.FileSystem]::FileExists($file_path) | Assert-Equals -Expected $false
    }

    "Delete file that does not exist" = {
        $file_path = [Ansible.IO.Path]::Combine($test_path, "file.txt")

        [Ansible.IO.FileSystem]::DeleteFile($file_path)

        [Ansible.IO.FileSystem]::FileExists($file_path) | Assert-Equals -Expected $false
    }

    "Delete file in a dir that does not exist" = {
        $file_path = [Ansible.IO.Path]::Combine($test_path, "missing", "file.txt")

        $failed = $false
        try {
            [Ansible.IO.FileSystem]::DeleteFile($file_path)
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.DirectoryNotFoundException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "Could not find a part of the path '$file_path'."
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Delete file that is a folder" = {
        $file_path = [Ansible.IO.Path]::Combine($test_path, "folder")
        [Ansible.IO.FileSystem]::CreateDirectory($file_path)

        $failed = $false
        try {
            [Ansible.IO.FileSystem]::DeleteFile($file_path)
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.UnauthorizedAccessException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "Access to the path '$file_path' is denied."
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Delete file that is hidden" = {
        $file_path = [Ansible.IO.Path]::Combine($test_path, "file.txt")
        Set-AnsibleContent -Path $file_path -Value "abc"
        [Ansible.IO.FileSystem]::SetAttributes($file_path, "Hidden")

        [Ansible.IO.FileSystem]::DeleteFile($file_path)

        [Ansible.IO.FileSystem]::FileExists($file_path) | Assert-Equals -Expected $false
    }

    "Delete file that is read only" = {
        $file_path = [Ansible.IO.Path]::Combine($test_path, "file.txt")
        Set-AnsibleContent -Path $file_path -Value "abc"
        [Ansible.IO.FileSystem]::SetAttributes($file_path, "ReadOnly")

        [Ansible.IO.FileSystem]::DeleteFile($file_path)

        [Ansible.IO.FileSystem]::FileExists($file_path) | Assert-Equals -Expected $false
    }

    "Delete file with no permissions" = {
        if ($test_path.StartsWith("\\?\")) {
            # We use some .NET APIs to set the permissions which fail on a long path. Just skip that test for now.
            return
        }

        $base_dir = [Ansible.IO.Path]::Combine($test_path, "directory")
        [Ansible.IO.FileSystem]::CreateDirectory($base_dir)

        $file_path = [Ansible.IO.Path]::Combine($base_dir, "file.txt")
        Set-AnsibleContent -Path $file_path -Value "abc"
        Set-RestrictedSD -Path $base_dir

        [Ansible.IO.FileSystem]::DeleteFile($file_path)
        [Ansible.IO.FileSystem]::FileExists($file_path) | Assert-Equals -Expected $false
    }

    "Delete file that is a symlink" = {
        $file_path = [Ansible.IO.Path]::Combine($test_path, "file.txt")
        $link_target = [Ansible.IO.Path]::Combine($test_path, "link_target.txt")
        Set-AnsibleContent -Path $link_target -Value "abc"
        [Ansible.Link.LinkUtil]::CreateLink($file_path, $link_target, "SymbolicLink")

        [Ansible.IO.FileSystem]::DeleteFile($file_path)

        [Ansible.IO.FileSystem]::FileExists($file_path) | Assert-Equals -Expected $false
    }

    "Delete file that is a broken symlink" = {
        $file_path = [Ansible.IO.Path]::Combine($test_path, "file.txt")
        $link_target = [Ansible.IO.Path]::Combine($test_path, "link_target.txt")
        [Ansible.Link.LinkUtil]::CreateLink($file_path, $link_target, "SymbolicLink")

        [Ansible.IO.FileSystem]::DeleteFile($file_path)

        [Ansible.IO.FileSystem]::FileExists($file_path) | Assert-Equals -Expected $false
    }

    "Delete file that is a hard link" = {
        $file_path = [Ansible.IO.Path]::Combine($test_path, "file.txt")
        $link_target = [Ansible.IO.Path]::Combine($test_path, "link_target.txt")
        Set-AnsibleContent -Path $link_target -Value "abc"
        [Ansible.Link.LinkUtil]::CreateLink($file_path, $link_target, "HardLink")

        [Ansible.IO.FileSystem]::DeleteFile($file_path)

        [Ansible.IO.FileSystem]::FileExists($file_path) | Assert-Equals -Expected $false
    }

    "Directory exists for dir" = {
        $dir_path = [Ansible.IO.Path]::Combine($test_path, "directory")
        [Ansible.IO.FileSystem]::CreateDirectory($dir_path)

        [Ansible.IO.FileSystem]::Exists($dir_path) | Assert-Equals -Expected $true
        [Ansible.IO.FileSystem]::DirectoryExists($dir_path) | Assert-Equals -Expected $true
    }

    "Directory exists for file" = {
        $dir_path = [Ansible.IO.Path]::Combine($test_path, "file.txt")
        Set-AnsibleContent -Path $dir_path -Value "abc"

        [Ansible.IO.FileSystem]::Exists($dir_path) | Assert-Equals -Expected $true
        [Ansible.IO.FileSystem]::DirectoryExists($dir_path) | Assert-Equals -Expected $false
    }

    "Directory exists for missing dir" = {
        $dir_path = [Ansible.IO.Path]::Combine($test_path, "directory")

        [Ansible.IO.FileSystem]::Exists($dir_path) | Assert-Equals -Expected $false
        [Ansible.IO.FileSystem]::DirectoryExists($dir_path) | Assert-Equals -Expected $false
    }

    "Directory exists for missing nested dir" = {
        $dir_path = [Ansible.IO.Path]::Combine($test_path, "directory", "nested")

        [Ansible.IO.FileSystem]::Exists($dir_path) | Assert-Equals -Expected $false
        [Ansible.IO.FileSystem]::DirectoryExists($dir_path) | Assert-Equals -Expected $false
    }

    "Directory exists for dir with no permissions" = {
        if ($test_path.StartsWith("\\?\")) {
            # We use some .NET APIs to set the permissions which fail on a long path. Just skip that test for now.
            return
        }

        $dir_path = [Ansible.IO.Path]::Combine($test_path, "directory")
        $nested_dir_path = [Ansible.IO.Path]::Combine($dir_path, "nested")
        [Ansible.IO.FileSystem]::CreateDirectory($dir_path)
        [Ansible.IO.FileSystem]::CreateDirectory($nested_dir_path)
        Set-RestrictedSD -Path $dir_path

        [Ansible.IO.FileSystem]::Exists($dir_path) | Assert-Equals -Expected $true
        [Ansible.IO.FileSystem]::DirectoryExists($dir_path) | Assert-Equals -Expected $true
        [Ansible.IO.FileSystem]::Exists($nested_dir_path) | Assert-Equals -Expected $true
        [Ansible.IO.FileSystem]::DirectoryExists($nested_dir_path) | Assert-Equals -Expected $true
    }

    "Enumerate directory that is empty" = {
        $dir_path = [Ansible.IO.Path]::Combine($test_path, "directory")
        [Ansible.IO.FileSystem]::CreateDirectory($dir_path)

        $actual = [System.Collections.Generic.List`1[String]]@()
        foreach($e in [Ansible.IO.FileSystem]::EnumerateFolder($dir_path, "*", "TopDirectoryOnly", $true, $true)) {
            $actual.Add($e)
        }
        $actual.Count | Assert-Equals -Expected 0
    }

    "Enumerate directory non recursively" = {
        $dir_path = [Ansible.IO.Path]::Combine($test_path, "directory")
        $nested_dir_path = [Ansible.IO.Path]::Combine($dir_path, "nested")
        $file_path = [Ansible.IO.Path]::Combine($nested_dir_path, "file.txt")
        [Ansible.IO.FileSystem]::CreateDirectory($nested_dir_path)
        Set-AnsibleContent $file_path -Value "abc"

        $actual = [System.Collections.Generic.List`1[String]]@()
        foreach($e in [Ansible.IO.FileSystem]::EnumerateFolder($dir_path, "*", "TopDirectoryOnly", $true, $true)) {
            $actual.Add($e)
        }
        $actual.Count | Assert-Equals -Expected 1
        $actual[0] | Assert-Equals -Expected $nested_dir_path
    }

    "Enumerate directory recursively" = {
        $dir_path = [Ansible.IO.Path]::Combine($test_path, "directory")
        $nested_dir_path = [Ansible.IO.Path]::Combine($dir_path, "nested")
        $file_path = [Ansible.IO.Path]::Combine($nested_dir_path, "file.txt")
        [Ansible.IO.FileSystem]::CreateDirectory($nested_dir_path)
        Set-AnsibleContent $file_path -Value "abc"

        $actual = [System.Collections.Generic.List`1[String]]@()
        foreach($e in [Ansible.IO.FileSystem]::EnumerateFolder($dir_path, "*", "AllDirectories", $true, $true)) {
            $actual.Add($e)
        }
        $actual.Count | Assert-Equals -Expected 2
        $actual[0] | Assert-Equals -Expected $nested_dir_path
        $actual[1] | Assert-Equals -Expected $file_path
    }

    "Enumerate directory recursively with pattern" = {
        $dir_path = [Ansible.IO.Path]::Combine($test_path, "directory")
        $nested_dir_path = [Ansible.IO.Path]::Combine($dir_path, "nested")
        $file_path1 = [Ansible.IO.Path]::Combine($nested_dir_path, "file1.txt")
        $file_path2 = [Ansible.IO.Path]::Combine($nested_dir_path, "files2.txt")
        $file_path3 = [Ansible.IO.Path]::Combine($nested_dir_path, "file3.txt")
        [Ansible.IO.FileSystem]::CreateDirectory($nested_dir_path)
        Set-AnsibleContent $file_path1 -Value "abc"
        Set-AnsibleContent $file_path2 -Value "abc"
        Set-AnsibleContent $file_path3 -Value "abc"

        $actual = [System.Collections.Generic.List`1[String]]@()
        foreach($e in [Ansible.IO.FileSystem]::EnumerateFolder($dir_path, "file?.txt", "AllDirectories", $true, $true)) {
            $actual.Add($e)
        }
        $actual.Count | Assert-Equals -Expected 2
        $actual[0] | Assert-Equals -Expected $file_path1
        $actual[1] | Assert-Equals -Expected $file_path3
    }

    "Enumerate directory return directories" = {
        $dir_path = [Ansible.IO.Path]::Combine($test_path, "directory")
        $nested_dir_path = [Ansible.IO.Path]::Combine($dir_path, "nested")
        $file_path = [Ansible.IO.Path]::Combine($nested_dir_path, "file.txt")
        [Ansible.IO.FileSystem]::CreateDirectory($nested_dir_path)
        Set-AnsibleContent $file_path -Value "abc"

        $actual = [System.Collections.Generic.List`1[String]]@()
        foreach($e in [Ansible.IO.FileSystem]::EnumerateFolder($dir_path, "*", "AllDirectories", $true, $false)) {
            $actual.Add($e)
        }
        $actual.Count | Assert-Equals -Expected 1
        $actual[0] | Assert-Equals -Expected $nested_dir_path
    }

    "Enumerate directory return files" = {
        $dir_path = [Ansible.IO.Path]::Combine($test_path, "directory")
        $nested_dir_path = [Ansible.IO.Path]::Combine($dir_path, "nested")
        $file_path = [Ansible.IO.Path]::Combine($nested_dir_path, "file.txt")
        [Ansible.IO.FileSystem]::CreateDirectory($nested_dir_path)
        Set-AnsibleContent $file_path -Value "abc"

        $actual = [System.Collections.Generic.List`1[String]]@()
        foreach($e in [Ansible.IO.FileSystem]::EnumerateFolder($dir_path, "*", "AllDirectories", $false, $true)) {
            $actual.Add($e)
        }
        $actual.Count | Assert-Equals -Expected 1
        $actual[0] | Assert-Equals -Expected $file_path
    }

    "File exists for file" = {
        $file_path = [Ansible.IO.Path]::Combine($test_path, "file.txt")
        Set-AnsibleContent -Path $file_path -Value "abc"

        [Ansible.IO.FileSystem]::Exists($file_path) | Assert-Equals -Expected $true
        [Ansible.IO.FileSystem]::FileExists($file_path) | Assert-Equals -Expected $true
    }

    "File exists for dir" = {
        $file_path = [Ansible.IO.Path]::Combine($test_path, "file.txt")
        [Ansible.IO.FileSystem]::CreateDirectory($file_path)

        [Ansible.IO.FileSystem]::Exists($file_path) | Assert-Equals -Expected $true
        [Ansible.IO.FileSystem]::FileExists($file_path) | Assert-Equals -Expected $false
    }

    "File exists for missing file in missing dir" = {
        $dir_path = [Ansible.IO.Path]::Combine($test_path, "directory")
        $file_path = [Ansible.IO.Path]::Combine($dir_path, "file.txt")

        [Ansible.IO.FileSystem]::Exists($file_path) | Assert-Equals -Expected $false
        [Ansible.IO.FileSystem]::FileExists($file_path) | Assert-Equals -Expected $false
    }

    "File exists for file with no permissions" = {
        if ($test_path.StartsWith("\\?\")) {
            # We use some .NET APIs to set the permissions which fail on a long path. Just skip that test for now.
            return
        }

        $dir_path = [Ansible.IO.Path]::Combine($test_path, "directory")
        $file_path = [Ansible.IO.Path]::Combine($dir_path, "file.txt")
        [Ansible.IO.FileSystem]::CreateDirectory($dir_path)
        Set-AnsibleContent -Path $file_path -Value "abc"
        Set-RestrictedSD -Path $dir_path

        [Ansible.IO.FileSystem]::Exists($file_path) | Assert-Equals -Expected $true
        [Ansible.IO.FileSystem]::FileExists($file_path) | Assert-Equals -Expected $true
    }

    "File exists for pagefile.sys" = {
        if ($test_path.StartsWith("\\")) {
            # We only need to test this once
            return
        }

        # The pagefile.sys is a special file that usually is locked. It requires special handling to check if it exists
        $pagefile = Get-Pagefile
        if ($null -eq $pagefile) {
            return
        }

        [Ansible.IO.FileSystem]::Exists($pagefile) | Assert-Equals -Expected $true
        [Ansible.IO.FileSystem]::FileExists($pagefile) | Assert-Equals -Expected $true
    }

    "Get file attribute data for file" = {
        $file_path = [Ansible.IO.Path]::Combine($test_path, "file.txt")
        Set-AnsibleContent -Path $file_path -Value "abc"

        $actual = [Ansible.IO.FileSystem]::GetFileAttributeData($file_path)
        $actual.GetType().FullName | Assert-Equals -Expected "Ansible.IO.FileAttributeData"
        $actual.FileAttributes.GetType().FullName | Assert-Equals -Expected "System.IO.FileAttributes"
        $actual.CreationTime.GetType().FullName | Assert-Equals -Expected "System.DateTimeOffset"
        $actual.LastAccessTime.GetType().FullName | Assert-Equals -Expected "System.DateTimeOffset"
        $actual.LastWriteTime.GetType().FullName | Assert-Equals -Expected "System.DateTimeOffset"
        $actual.FileSize | Assert-Equals -Expected 3
    }

    "Get file attribute data for directory" = {
        $dir_path = [Ansible.IO.Path]::Combine($test_path, "directory")
        [Ansible.IO.FileSystem]::CreateDirectory($dir_path)

        $actual = [Ansible.IO.FileSystem]::GetFileAttributeData($dir_path)
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::Directory) | Assert-Equals -Expected $true
        $actual.CreationTime.GetType().FullName | Assert-Equals -Expected "System.DateTimeOffset"
        $actual.LastAccessTime.GetType().FullName | Assert-Equals -Expected "System.DateTimeOffset"
        $actual.LastWriteTime.GetType().FullName | Assert-Equals -Expected "System.DateTimeOffset"
        $actual.FileSize | Assert-Equals -Expected 0
    }

    "Get file attribute data for missing file" = {
        $file_path = [Ansible.IO.Path]::Combine($test_path, "missing")

        $failed = $false
        try {
            [Ansible.IO.FileSystem]::GetFileAttributeData($file_path)
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.FileNotFoundException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "Could not find file '$file_path'"
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Get file attribute data for file in missing directory" = {
        $file_path = [Ansible.IO.Path]::Combine($test_path, "missing", "file.txt")

        $failed = $false
        try {
            [Ansible.IO.FileSystem]::GetFileAttributeData($file_path)
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.DirectoryNotFoundException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "Could not find a part of the path '$file_path'."
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Get file attribute data for hidden, system, and read only file" = {
        $file_path = [Ansible.IO.Path]::Combine($test_path, "file.txt")
        Set-AnsibleContent -Path $file_path -Value "abc"
        [Ansible.IO.FileSystem]::SetAttributes($file_path, "Hidden, ReadOnly, System")

        $actual = [Ansible.IO.FileSystem]::GetFileAttributeData($file_path)
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::Hidden) | Assert-Equals -Expected $true
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::ReadOnly) | Assert-Equals -Expected $true
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::System) | Assert-Equals -Expected $true
    }

    "Get file attribute data for symbolic link" = {
        $file_path = [Ansible.IO.Path]::Combine($test_path, "file.txt")
        $link_target = [Ansible.IO.Path]::Combine($test_path, "link_target.txt")
        Set-AnsibleContent -Path $link_target -Value "abc"

        [Ansible.Link.LinkUtil]::CreateLink($file_path, $link_target, "SymbolicLink")

        $actual = [Ansible.IO.FileSystem]::GetFileAttributeData($file_path)
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::ReparsePoint) | Assert-Equals -Expected $true
        $actual.FileSize | Assert-Equals -Expected 0

        # Delete the target and try again
        [Ansible.IO.FileSystem]::DeleteFile($link_target)
        $actual2 = [Ansible.IO.FileSystem]::GetFileAttributeData($file_path)
        $actual2.FileAttributes | Assert-Equals -Expected $actual.FileAttributes
        $actual2.CreationTime | Assert-Equals -Expected $actual.CreationTime
        $actual2.LastAccessTime | Assert-Equals -Expected $actual.LastAccessTime
        $actual2.LastWriteTime | Assert-Equals -Expected $actual.LastWriteTime
        $actual2.FileSize | Assert-Equals -Expected $actual.FileSize
    }

    "Get file attribute data for junction point" = {
        $dir_path = [Ansible.IO.Path]::Combine($test_path, "dir")
        $link_target = [Ansible.IO.Path]::Combine($test_path, "link_target")
        [Ansible.IO.FileSystem]::CreateDirectory($link_target)

        [Ansible.Link.LinkUtil]::CreateLink($dir_path, $link_target, "JunctionPoint")

        $actual = [Ansible.IO.FileSystem]::GetFileAttributeData($dir_path)
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::Directory) | Assert-Equals -Expected $true
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::ReparsePoint) | Assert-Equals -Expected $true
        $actual.FileSize | Assert-Equals -Expected 0

        # Delete the target and try again
        [Ansible.IO.FileSystem]::RemoveDirectory($link_target, $false)
        $actual2 = [Ansible.IO.FileSystem]::GetFileAttributeData($dir_path)
        $actual2.FileAttributes | Assert-Equals -Expected $actual.FileAttributes
        $actual2.CreationTime | Assert-Equals -Expected $actual.CreationTime
        $actual2.LastAccessTime | Assert-Equals -Expected $actual.LastAccessTime
        $actual2.LastWriteTime | Assert-Equals -Expected $actual.LastWriteTime
        $actual2.FileSize | Assert-Equals -Expected $actual.FileSize
    }

    "Get file attribute data for pagefile.sys" = {
        if ($test_path.StartsWith("\\")) {
            # We only need to test this once
            return
        }

        # The pagefile.sys is a special file that usually is locked. It requires special handling to check if it exists
        $pagefile = Get-Pagefile
        if ($null -eq $pagefile) {
            return
        }

        $actual = [Ansible.IO.FileSystem]::GetFileAttributeData($pagefile)
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::Archive) | Assert-Equals -Expected $true
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::Hidden) | Assert-Equals -Expected $true
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::System) | Assert-Equals -Expected $true
    }

    "Get file attribute data for file and dir without permissions" = {
        if ($test_path.StartsWith("\\?\")) {
            # We use some .NET APIs to set the permissions which fail on a long path. Just skip that test for now.
            return
        }

        $dir_path = [Ansible.IO.Path]::Combine($test_path, "directory")
        $file_path = [Ansible.IO.Path]::Combine($dir_path, "file.txt")
        [Ansible.IO.FileSystem]::CreateDirectory($dir_path)
        Set-AnsibleContent -Path $file_path -Value "abc"
        Set-RestrictedSD -Path $dir_path

        $actual = [Ansible.IO.FileSystem]::GetFileAttributeData($file_path)
        $actual.GetType().FullName | Assert-Equals -Expected "Ansible.IO.FileAttributeData"
        $actual.FileAttributes.GetType().FullName | Assert-Equals -Expected "System.IO.FileAttributes"
        $actual.CreationTime.GetType().FullName | Assert-Equals -Expected "System.DateTimeOffset"
        $actual.LastAccessTime.GetType().FullName | Assert-Equals -Expected "System.DateTimeOffset"
        $actual.LastWriteTime.GetType().FullName | Assert-Equals -Expected "System.DateTimeOffset"
        $actual.FileSize | Assert-Equals -Expected 3
    }

    "Move file" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        $target = [Ansible.IO.Path]::Combine($test_path, "target.txt")
        Set-AnsibleContent -Path $source -Value "abc"

        [Ansible.IO.FileSystem]::MoveFile($source, $target)

        [Ansible.IO.FileSystem]::FileExists($source) | Assert-Equals -Expected $false
        [Ansible.IO.FileSystem]::FileExists($target) | Assert-Equals -Expected $true
        Get-AnsibleContent -Path $target | Assert-Equals -Expected "abc"
    }

    "Move directory" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source")
        $source_dir = [Ansible.IO.Path]::Combine($source, "directory")
        $source_file = [Ansible.IO.Path]::Combine($source_dir, "file.txt")

        $target = [Ansible.IO.Path]::Combine($test_path, "target")
        $target_dir = [Ansible.IO.Path]::Combine($target, "directory")
        $target_file = [Ansible.IO.Path]::Combine($target_dir, "file.txt")

        [Ansible.IO.FileSystem]::CreateDirectory($source_dir)
        Set-AnsibleContent -Path $source_file -Value "abc"

        [Ansible.IO.FileSystem]::MoveFile($source, $target)

        [Ansible.IO.FileSystem]::DirectoryExists($source) | Assert-Equals -Expected $false
        [Ansible.IO.FileSystem]::DirectoryExists($target) | Assert-Equals -Expected $true
        [Ansible.IO.FileSystem]::DirectoryExists($target_dir) | Assert-Equals -Expected $true
        [Ansible.IO.FileSystem]::FileExists($target_file) | Assert-Equals -Expected $true
        Get-AnsibleContent -Path $target_file | Assert-Equals -Expected "abc"
    }

    "Move missing file" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        $target = [Ansible.IO.Path]::Combine($test_path, "target.txt")

        $failed = $false
        try {
            [Ansible.IO.FileSystem]::MoveFile($source, $target)
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.FileNotFoundException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "Could not find file '$source'"
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Move missing directory" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        $target = [Ansible.IO.Path]::Combine($test_path, "missing", "target.txt")
        Set-AnsibleContent -Path $source -Value "abc"

        $failed = $false
        try {
            [Ansible.IO.FileSystem]::MoveFile($source, $target)
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.DirectoryNotFoundException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "Could not find a part of the path '$target'."
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Move file to existing path" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        $target = [Ansible.IO.Path]::Combine($test_path, "target.txt")
        Set-AnsibleContent -Path $source -Value "abc"
        Set-AnsibleContent -Path $target -Value "def"

        $failed = $false
        try {
            [Ansible.IO.FileSystem]::MoveFile($source, $target)
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.IOException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "Cannot create '$target' because a file or directory with the same name already exists."
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true

        [Ansible.IO.FileSystem]::FileExists($source) | Assert-Equals -Expected $true
        Get-AnsibleContent -Path $source | Assert-Equals -Expected "abc"
        [Ansible.IO.FileSystem]::FileExists($target) | Assert-Equals -Expected $true
        Get-AnsibleContent -Path $target | Assert-Equals -Expected "def"
    }

    "Remove directory" = {
        $dir_path = [Ansible.IO.Path]::Combine($test_path, "directory")
        [Ansible.IO.FileSystem]::CreateDirectory($dir_path)

        [Ansible.IO.FileSystem]::RemoveDirectory($dir_path, $false)

        [Ansible.IO.FileSystem]::Exists($dir_path) | Assert-Equals -Expected $false
        [Ansible.IO.FileSystem]::DirectoryExists($dir_path) | Assert-Equals -Expected $false
    }

    "Remove directory with contents and without recurse" = {
        $dir_path = [Ansible.IO.Path]::Combine($test_path, "directory")
        $nested_dir = [Ansible.IO.Path]::Combine($dir_path, "nested")
        [Ansible.IO.FileSystem]::CreateDirectory($nested_dir)

        $failed = $false
        try {
            [Ansible.IO.FileSystem]::RemoveDirectory($dir_path, $false)
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.IOException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "The directory is not empty: '$dir_path'"
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true

        [Ansible.IO.FileSystem]::Exists($nested_dir) | Assert-Equals -Expected $true
        [Ansible.IO.FileSystem]::DirectoryExists($nested_dir) | Assert-Equals -Expected $true
    }

    "Remove directory with contents and with recurse" = {
        $dir_path = [Ansible.IO.Path]::Combine($test_path, "directory")
        $nested_dir = [Ansible.IO.Path]::Combine($dir_path, "nested")
        [Ansible.IO.FileSystem]::CreateDirectory($nested_dir)

        [Ansible.IO.FileSystem]::RemoveDirectory($dir_path, $true)

        [Ansible.IO.FileSystem]::Exists($dir_path) | Assert-Equals -Expected $false
        [Ansible.IO.FileSystem]::DirectoryExists($dir_path) | Assert-Equals -Expected $false
    }

    "Remove directory with file path" = {
        $dir_path = [Ansible.IO.Path]::Combine($test_path, "file.txt")
        Set-AnsibleContent -Path $dir_path -Value "abc"

        $failed = $false
        try {
            [Ansible.IO.FileSystem]::RemoveDirectory($dir_path, $true)
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.IOException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "The directory name is invalid: '$dir_path'"
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Remove directory without permissions" = {
        if ($test_path.StartsWith("\\?\")) {
            # We use some .NET APIs to set the permissions which fail on a long path. Just skip that test for now.
            return
        }

        $parent_dir = [Ansible.IO.Path]::Combine($test_path, "parent directory")
        $dir_path = [Ansible.IO.Path]::Combine($parent_dir, "directory")
        $file_path = [Ansible.IO.Path]::Combine($dir_path, "file.txt")
        [Ansible.IO.FileSystem]::CreateDirectory($dir_path)
        Set-AnsibleContent -Path $file_path -Value "abc"
        Set-RestrictedSD -Path $parent_dir

        [Ansible.IO.FileSystem]::RemoveDirectory($dir_path, $true)

        [Ansible.IO.FileSystem]::Exists($dir_path) | Assert-Equals -Expected $false
        [Ansible.IO.FileSystem]::DirectoryExists($dir_path) | Assert-Equals -Expected $false
    }

    "Replace file without backup" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        $target = [Ansible.IO.Path]::Combine($test_path, "target.txt")
        Set-AnsibleContent -Path $source -Value "abc"
        Set-AnsibleContent -Path $target -Value "def"

        [Ansible.IO.FileSystem]::ReplaceFile($source, $target, $null, $false)

        [Ansible.IO.FileSystem]::FileExists($source) | Assert-Equals -Expected $false
        [Ansible.IO.FileSystem]::FileExists($target) | Assert-Equals -Expected $true
        Get-AnsibleContent -Path $target | Assert-Equals -Expected "abc"
    }

    "Replace file with backup" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        $target = [Ansible.IO.Path]::Combine($test_path, "target.txt")
        $backup = [Ansible.IO.Path]::Combine($test_path, "backup.txt")
        Set-AnsibleContent -Path $source -Value "abc"
        Set-AnsibleContent -Path $target -Value "def"

        [Ansible.IO.FileSystem]::ReplaceFile($source, $target, $backup, $false)

        [Ansible.IO.FileSystem]::FileExists($source) | Assert-Equals -Expected $false
        [Ansible.IO.FileSystem]::FileExists($target) | Assert-Equals -Expected $true
        Get-AnsibleContent -Path $target | Assert-Equals -Expected "abc"
        [Ansible.IO.FileSystem]::FileExists($backup) | Assert-Equals -Expected $true
        Get-AnsibleContent -Path $backup | Assert-Equals -Expected "def"
    }

    "Replace file with backup that already exists" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        $target = [Ansible.IO.Path]::Combine($test_path, "target.txt")
        $backup = [Ansible.IO.Path]::Combine($test_path, "backup.txt")
        Set-AnsibleContent -Path $source -Value "abc"
        Set-AnsibleContent -Path $target -Value "def"
        Set-AnsibleContent -Path $backup -Value "ghi"

        [Ansible.IO.FileSystem]::ReplaceFile($source, $target, $backup, $false)

        [Ansible.IO.FileSystem]::FileExists($source) | Assert-Equals -Expected $false
        [Ansible.IO.FileSystem]::FileExists($target) | Assert-Equals -Expected $true
        Get-AnsibleContent -Path $target | Assert-Equals -Expected "abc"
        [Ansible.IO.FileSystem]::FileExists($backup) | Assert-Equals -Expected $true
        Get-AnsibleContent -Path $backup | Assert-Equals -Expected "def"
    }

    "Replace directory with file" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")
        [Ansible.IO.FileSystem]::CreateDirectory($target)
        Set-AnsibleContent -Path $source -Value "abc"

        $failed = $false
        try {
            [Ansible.IO.FileSystem]::ReplaceFile($source, $target, $null, $false)
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.UnauthorizedAccessException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "Access to the path '$target' is denied."
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Replace file with directory" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target.txt")
        [Ansible.IO.FileSystem]::CreateDirectory($source)
        Set-AnsibleContent -Path $target -Value "abc"

        $failed = $false
        try {
            [Ansible.IO.FileSystem]::ReplaceFile($source, $target, $null, $false)
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.UnauthorizedAccessException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "Access to the path '$source' is denied."
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Replace file with dest in missing dir" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        $target = [Ansible.IO.Path]::Combine($test_path, "missing", "target.txt")
        Set-AnsibleContent -Path $source -Value "abc"

        $failed = $false
        try {
            [Ansible.IO.FileSystem]::ReplaceFile($source, $target, $null, $false)
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.DirectoryNotFoundException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "Could not find a part of the path '$target'."
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Replace file with missing dest" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        $target = [Ansible.IO.Path]::Combine($test_path, "target.txt")
        Set-AnsibleContent -Path $source -Value "abc"

        $failed = $false
        try {
            [Ansible.IO.FileSystem]::ReplaceFile($source, $target, $null, $false)
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.FileNotFoundException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "Could not find file '$target'"
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Set attributes on file" = {
        $file_path = [Ansible.IO.Path]::Combine($test_path, "file.txt")
        Set-AnsibleContent -Path $file_path -Value "abc"

        [Ansible.IO.FileSystem]::SetAttributes($file_path, "Hidden, System, ReadOnly")

        $actual = [Ansible.IO.FileSystem]::GetFileAttributeData($file_path)
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::Hidden) | Assert-Equals -Expected $true
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::ReadOnly) | Assert-Equals -Expected $true
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::System) | Assert-Equals -Expected $true

        [Ansible.IO.FileSystem]::SetAttributes($file_path, "Hidden, ReadOnly")

        $actual = [Ansible.IO.FileSystem]::GetFileAttributeData($file_path)
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::Hidden) | Assert-Equals -Expected $true
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::ReadOnly) | Assert-Equals -Expected $true
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::System) | Assert-Equals -Expected $false
    }

    "Set attributes on directory" = {
        $dir_path = [Ansible.IO.Path]::Combine($test_path, "directory")
        [Ansible.IO.FileSystem]::CreateDirectory($dir_path)

        [Ansible.IO.FileSystem]::SetAttributes($dir_path, "Hidden, System, ReadOnly")

        $actual = [Ansible.IO.FileSystem]::GetFileAttributeData($dir_path)
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::Directory) | Assert-Equals -Expected $true
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::Hidden) | Assert-Equals -Expected $true
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::ReadOnly) | Assert-Equals -Expected $true
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::System) | Assert-Equals -Expected $true

        [Ansible.IO.FileSystem]::SetAttributes($dir_path, "Hidden, ReadOnly")

        $actual = [Ansible.IO.FileSystem]::GetFileAttributeData($dir_path)
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::Directory) | Assert-Equals -Expected $true
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::Hidden) | Assert-Equals -Expected $true
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::ReadOnly) | Assert-Equals -Expected $true
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::System) | Assert-Equals -Expected $false
    }

    "Set same attributes on file" = {
        $file_path = [Ansible.IO.Path]::Combine($test_path, "file.txt")
        Set-AnsibleContent -Path $file_path -Value "abc"

        [Ansible.IO.FileSystem]::SetAttributes($file_path, "Hidden, System, ReadOnly")

        $actual = [Ansible.IO.FileSystem]::GetFileAttributeData($file_path)
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::Hidden) | Assert-Equals -Expected $true
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::ReadOnly) | Assert-Equals -Expected $true
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::System) | Assert-Equals -Expected $true

        [Ansible.IO.FileSystem]::SetAttributes($file_path, "Hidden, System, ReadOnly")
        $actual2 = [Ansible.IO.FileSystem]::GetFileAttributeData($file_path)
        $actual2.FileAttributes | Assert-Equals -Expected $actual.FileAttributes
    }

    "Set attributes on missing file" = {
        $file_path = [Ansible.IO.Path]::Combine($test_path, "file.txt")

        $failed = $false
        try {
            [Ansible.IO.FileSystem]::SetAttributes($file_path, "Hidden")
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.FileNotFoundException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "Could not find file '$file_path'"
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Set attributes on missing directory" = {
        $file_path = [Ansible.IO.Path]::Combine($test_path, "missing", "file.txt")

        $failed = $false
        try {
            [Ansible.IO.FileSystem]::SetAttributes($file_path, "Hidden")
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.IO.DirectoryNotFoundException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "Could not find a part of the path '$file_path'."
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Set attributes in dir with no permissions" = {
        if ($test_path.StartsWith("\\?\")) {
            # We use some .NET APIs to set the permissions which fail on a long path. Just skip that test for now.
            return
        }

        $dir_path = [Ansible.IO.Path]::Combine($test_path, "directory")
        $file_path = [Ansible.IO.Path]::Combine($dir_path, "file.txt")
        [Ansible.IO.FileSystem]::CreateDirectory($dir_path)
        Set-AnsibleContent -Path $file_path -Value "abc"
        Set-RestrictedSD -Path $dir_path

        [Ansible.IO.FileSystem]::SetAttributes($file_path, "Hidden")

        $actual = [Ansible.IO.FileSystem]::GetFileAttributeData($file_path)
        $actual.FileAttributes.HasFlag([System.IO.FileAttributes]::Hidden) | Assert-Equals -Expected $true
    }

    "Set creation time on file" = {
        $file_path = [Ansible.IO.Path]::Combine($test_path, "file.txt")
        Set-AnsibleContent -Path $file_path -Value "abc"

        $file_info = [Ansible.IO.FileSystem]::GetFileAttributeData($file_path)
        $cdate = Get-Date -Year 1999 -Month 12 -Day 31 -Hour 23 -Minute 59 -Second 59 -Millisecond 999
        $adate = $file_info.LastAccessTime
        $wdate = $file_info.LastWriteTime

        [Ansible.IO.FileSystem]::SetFileTime($file_path, $cdate, $null, $null)

        $actual = [Ansible.IO.FileSystem]::GetFileAttributeData($file_path)
        $actual.CreationTime | Assert-Equals -Expected $cdate
        $actual.LastAccessTime | Assert-Equals -Expected $adate
        $actual.LastWriteTime | Assert-Equals -Expected $wdate
    }

    "Set access time on file" = {
        $file_path = [Ansible.IO.Path]::Combine($test_path, "file.txt")
        Set-AnsibleContent -Path $file_path -Value "abc"

        $file_info = [Ansible.IO.FileSystem]::GetFileAttributeData($file_path)
        $cdate = $file_info.CreationTime
        $adate = Get-Date -Year 1999 -Month 12 -Day 31 -Hour 23 -Minute 59 -Second 59 -Millisecond 999
        $wdate = $file_info.LastWriteTime

        [Ansible.IO.FileSystem]::SetFileTime($file_path, $null, $adate, $null)

        $actual = [Ansible.IO.FileSystem]::GetFileAttributeData($file_path)
        $actual.CreationTime | Assert-Equals -Expected $cdate
        $actual.LastAccessTime | Assert-Equals -Expected $adate
        $actual.LastWriteTime | Assert-Equals -Expected $wdate
    }

    "Set write time on file" = {
        $file_path = [Ansible.IO.Path]::Combine($test_path, "file.txt")
        Set-AnsibleContent -Path $file_path -Value "abc"

        $file_info = [Ansible.IO.FileSystem]::GetFileAttributeData($file_path)
        $cdate = $file_info.CreationTime
        $adate = $file_info.LastAccessTime
        $wdate = Get-Date -Year 1999 -Month 12 -Day 31 -Hour 23 -Minute 59 -Second 59 -Millisecond 999

        [Ansible.IO.FileSystem]::SetFileTime($file_path, $null, $null, $wdate)

        $actual = [Ansible.IO.FileSystem]::GetFileAttributeData($file_path)
        $actual.CreationTime | Assert-Equals -Expected $cdate
        $actual.LastAccessTime | Assert-Equals -Expected $adate
        $actual.LastWriteTime | Assert-Equals -Expected $wdate
    }

    "Set time on directory" = {
        $file_path = [Ansible.IO.Path]::Combine($test_path, "file.txt")
        Set-AnsibleContent -Path $file_path -Value "abc"

        $cdate = Get-Date -Year 1999 -Month 12 -Day 31 -Hour 23 -Minute 59 -Second 57 -Millisecond 999
        $adate = Get-Date -Year 1999 -Month 12 -Day 31 -Hour 23 -Minute 59 -Second 58 -Millisecond 999
        $wdate = Get-Date -Year 1999 -Month 12 -Day 31 -Hour 23 -Minute 59 -Second 59 -Millisecond 999

        [Ansible.IO.FileSystem]::SetFileTime($file_path, $cdate, $adate, $wdate)

        $actual = [Ansible.IO.FileSystem]::GetFileAttributeData($file_path)
        $actual.CreationTime | Assert-Equals -Expected $cdate
        $actual.LastAccessTime | Assert-Equals -Expected $adate
        $actual.LastWriteTime | Assert-Equals -Expected $wdate
    }

    "Set time on file with no permissions" = {
        if ($test_path.StartsWith("\\?\")) {
            # We use some .NET APIs to set the permissions which fail on a long path. Just skip that test for now.
            return
        }

        $dir_path = [Ansible.IO.Path]::Combine($test_path, "directory")
        $file_path = [Ansible.IO.Path]::Combine($dir_path, "file.txt")
        [Ansible.IO.FileSystem]::CreateDirectory($dir_path)
        Set-AnsibleContent -Path $file_path -Value "abc"
        Set-RestrictedSD -Path $dir_path

        $cdate = Get-Date -Year 1999 -Month 12 -Day 31 -Hour 23 -Minute 59 -Second 57 -Millisecond 999
        $adate = Get-Date -Year 1999 -Month 12 -Day 31 -Hour 23 -Minute 59 -Second 58 -Millisecond 999
        $wdate = Get-Date -Year 1999 -Month 12 -Day 31 -Hour 23 -Minute 59 -Second 59 -Millisecond 999

        [Ansible.IO.FileSystem]::SetFileTime($file_path, $cdate, $adate, $wdate)

        $actual = [Ansible.IO.FileSystem]::GetFileAttributeData($file_path)
        $actual.CreationTime | Assert-Equals -Expected $cdate
        $actual.LastAccessTime | Assert-Equals -Expected $adate
        $actual.LastWriteTime | Assert-Equals -Expected $wdate
    }
}

foreach ($test_impl in $tests.GetEnumerator()) {
    # Run each test with
    #     1. A normal path
    #     2. A path that exceeds MAX_PATH
    #     3. A UNC path
    #     4. A UNC path that exceeds MAX_PATH

    # Normal path
    $test_path = [Ansible.IO.Path]::Combine($module.Tmpdir, "short")
    Clear-Directory -Path $test_path
    $test = $test_impl.Key
    &$test_impl.Value

    # Local MAX_PATH
    $test_path = [Ansible.IO.Path]::Combine("\\?\$($module.Tmpdir)", "a" * 255)
    Clear-Directory -Path $test_path
    $test = "$($test_impl.Key) - MAX_PATH"
    &$test_impl.Value

    # UNC Path
    $unc_path = [Ansible.IO.Path]::Combine("localhost", "$($module.Tmpdir.Substring(0, 1))$", $module.Tmpdir.Substring(3))
    $test_path = [Ansible.IO.Path]::Combine("\\$unc_path", "short")
    Clear-Directory -Path $test_path
    $test = "$($test_impl.Key) - UNC Path"
    &$test_impl.Value

    # UNC MAX_PATH
    $test_path = [Ansible.IO.Path]::Combine("\\?\UNC\$unc_path", "a" * 255)
    Clear-Directory -Path $test_path
    $test = "$($test_impl.Key) - UNC MAX_PATH"
    &$test_impl.Value
}

# These tests are based on results when running on 2016 which has less restrictions when it comes to long paths.
$path_tests = [Ordered]@{
    "GetDirectoryName tests" = {
        $long_path = "{0}\{0}\{0}\{0}\{0}\{0}\{0}\dir" -f ("a" * 250)

        [Ansible.IO.Path]::GetDirectoryName("C:\path\dir") | Assert-Equals -Expected "C:\path"
        [Ansible.IO.Path]::GetDirectoryName("C:/path/dir") | Assert-Equals -Expected "C:\path"
        [Ansible.IO.Path]::GetDirectoryName("\\?\C:\path\dir") | Assert-Equals -Expected "\\?\C:\path"
        [Ansible.IO.Path]::GetDirectoryName("\\?\C:\path\$long_path\dir") | Assert-Equals -Expected "\\?\C:\path\$long_path"
        [Ansible.IO.Path]::GetDirectoryName("\\127.0.0.1\c$\path\dir") | Assert-Equals -Expected "\\127.0.0.1\c$\path"
        [Ansible.IO.Path]::GetDirectoryName("\\?\UNC\127.0.0.1\c$\path\$long_path\dir") | Assert-Equals -Expected "\\?\UNC\127.0.0.1\c$\path\$long_path"

        [Ansible.IO.Path]::GetDirectoryName("C:\path\dir\file.txt") | Assert-Equals -Expected "C:\path\dir"
        [Ansible.IO.Path]::GetDirectoryName("C:/path/dir/file.txt") | Assert-Equals -Expected "C:\path\dir"
        [Ansible.IO.Path]::GetDirectoryName("\\?\C:\path\dir\file.txt") | Assert-Equals -Expected "\\?\C:\path\dir"
        [Ansible.IO.Path]::GetDirectoryName("\\?\C:\path\$long_path\dir\file.txt") | Assert-Equals -Expected "\\?\C:\path\$long_path\dir"
        [Ansible.IO.Path]::GetDirectoryName("\\127.0.0.1\c$\path\dir\file.txt") | Assert-Equals -Expected "\\127.0.0.1\c$\path\dir"
        [Ansible.IO.Path]::GetDirectoryName("\\?\UNC\127.0.0.1\c$\path\$long_path\dir\file.txt") | Assert-Equals -Expected "\\?\UNC\127.0.0.1\c$\path\$long_path\dir"

        [Ansible.IO.Path]::GetDirectoryName("C:\path\dir\file.") | Assert-Equals -Expected "C:\path\dir"
        [Ansible.IO.Path]::GetDirectoryName("C:/path/dir/file.") | Assert-Equals -Expected "C:\path\dir"
        [Ansible.IO.Path]::GetDirectoryName("\\?\C:\path\dir\file.") | Assert-Equals -Expected "\\?\C:\path\dir"
        [Ansible.IO.Path]::GetDirectoryName("\\?\C:\path\$long_path\dir\file.") | Assert-Equals -Expected "\\?\C:\path\$long_path\dir"
        [Ansible.IO.Path]::GetDirectoryName("\\127.0.0.1\c$\path\dir\file.") | Assert-Equals -Expected "\\127.0.0.1\c$\path\dir"
        [Ansible.IO.Path]::GetDirectoryName("\\?\UNC\127.0.0.1\c$\path\$long_path\dir\file.") | Assert-Equals -Expected "\\?\UNC\127.0.0.1\c$\path\$long_path\dir"

        [Ansible.IO.Path]::GetDirectoryName($null) | Assert-Equals -Expected $null
        [Ansible.IO.Path]::GetDirectoryName("") | Assert-Equals -Expected $null
        [Ansible.IO.Path]::GetDirectoryName("C") | Assert-Equals -Expected ""
        [Ansible.IO.Path]::GetDirectoryName("C:") | Assert-Equals -Expected $null
        [Ansible.IO.Path]::GetDirectoryName("C:\") | Assert-Equals -Expected $null
        [Ansible.IO.Path]::GetDirectoryName("C:/") | Assert-Equals -Expected $null
        [Ansible.IO.Path]::GetDirectoryName("C:\a") | Assert-Equals -Expected "C:\"
        [Ansible.IO.Path]::GetDirectoryName("C:\a\") | Assert-Equals -Expected "C:\a"
        [Ansible.IO.Path]::GetDirectoryName("C:\a\b") | Assert-Equals -Expected "C:\a"
        [Ansible.IO.Path]::GetDirectoryName("C:/a") | Assert-Equals -Expected "C:\"
        [Ansible.IO.Path]::GetDirectoryName("\\?") | Assert-Equals -Expected $null
        [Ansible.IO.Path]::GetDirectoryName("\\?\C:") | Assert-Equals -Expected $null
        [Ansible.IO.Path]::GetDirectoryName("\\?\C:\") | Assert-Equals -Expected $null
        [Ansible.IO.Path]::GetDirectoryName("\\?\C:/") | Assert-Equals -Expected $null
        [Ansible.IO.Path]::GetDirectoryName("\\?\C:\a") | Assert-Equals -Expected "\\?\C:\"
        [Ansible.IO.Path]::GetDirectoryName("\\?\C:/a") | Assert-Equals -Expected "\\?\C:/"
        [Ansible.IO.Path]::GetDirectoryName("\\?\C:/a/") | Assert-Equals -Expected "\\?\C:/a"
        [Ansible.IO.Path]::GetDirectoryName("\\?\C:/a/b") | Assert-Equals -Expected "\\?\C:/a"

        [Ansible.IO.Path]::GetDirectoryName("\\") | Assert-Equals -Expected $null
        [Ansible.IO.Path]::GetDirectoryName("\\server") | Assert-Equals -Expected $null
        [Ansible.IO.Path]::GetDirectoryName("\\server\") | Assert-Equals -Expected $null
        [Ansible.IO.Path]::GetDirectoryName("\\server\share") | Assert-Equals -Expected $null
        [Ansible.IO.Path]::GetDirectoryName("\\server\share\") | Assert-Equals -Expected "\\server\share"
        [Ansible.IO.Path]::GetDirectoryName("\\server\share\path") | Assert-Equals -Expected "\\server\share"

        [Ansible.IO.Path]::GetDirectoryName("//") | Assert-Equals -Expected $null
        [Ansible.IO.Path]::GetDirectoryName("//server") | Assert-Equals -Expected $null
        [Ansible.IO.Path]::GetDirectoryName("//server/") | Assert-Equals -Expected $null
        [Ansible.IO.Path]::GetDirectoryName("//server/share") | Assert-Equals -Expected $null
        [Ansible.IO.Path]::GetDirectoryName("//server/share/") | Assert-Equals -Expected "\\server\share"
        [Ansible.IO.Path]::GetDirectoryName("//server/share/path") | Assert-Equals -Expected "\\server\share"

        [Ansible.IO.Path]::GetDirectoryName("\\?\UNC\") | Assert-Equals -Expected $null
        [Ansible.IO.Path]::GetDirectoryName("\\?\UNC\server") | Assert-Equals -Expected $null
        [Ansible.IO.Path]::GetDirectoryName("\\?\UNC\server\") | Assert-Equals -Expected $null
        [Ansible.IO.Path]::GetDirectoryName("\\?\UNC\server\share") | Assert-Equals -Expected $null
        [Ansible.IO.Path]::GetDirectoryName("\\?\UNC\server\share\") | Assert-Equals -Expected "\\?\UNC\server\share"
        [Ansible.IO.Path]::GetDirectoryName("\\?\UNC\server\share\path") | Assert-Equals -Expected "\\?\UNC\server\share"
        [Ansible.IO.Path]::GetDirectoryName("\\?\UNC\server/share\path") | Assert-Equals -Expected "\\?\UNC\server/share"
        [Ansible.IO.Path]::GetDirectoryName("\\?\UNC\server/share\path\") | Assert-Equals -Expected "\\?\UNC\server/share\path"
        [Ansible.IO.Path]::GetDirectoryName("\\?\UNC\server/share\path/") | Assert-Equals -Expected "\\?\UNC\server/share\path"

        [Ansible.IO.Path]::GetDirectoryName("\\?/UNC/server/share/") | Assert-Equals -Expected "\\?\UNC\server\share"
        [Ansible.IO.Path]::GetDirectoryName("\\?/UNC/server/share/path") | Assert-Equals -Expected "\\?\UNC\server\share"

        [Ansible.IO.Path]::GetDirectoryName("\\?\UNC/") | Assert-Equals -Expected "\\?\UNC"
        [Ansible.IO.Path]::GetDirectoryName("\\?\UNC/server") | Assert-Equals -Expected "\\?\UNC"
        [Ansible.IO.Path]::GetDirectoryName("\\?\UNC/server/") | Assert-Equals -Expected "\\?\UNC/server"
        [Ansible.IO.Path]::GetDirectoryName("\\?\UNC/server/share") | Assert-Equals -Expected "\\?\UNC/server"
        [Ansible.IO.Path]::GetDirectoryName("\\?\UNC/server/share/") | Assert-Equals -Expected "\\?\UNC/server/share"
        [Ansible.IO.Path]::GetDirectoryName("\\?\UNC/server/share/path") | Assert-Equals -Expected "\\?\UNC/server/share"
    }

    "GetFullPath tests" = {
        $long_path = "{0}\{0}\{0}\{0}\{0}\{0}\{0}\dir" -f ("a" * 250)

        # GetFullPath - we differ a bit from the latest System.IO.Path.GetFullPath where we still resolve if the prefix starts with \\?\
        [Ansible.IO.Path]::GetFullPath("C:\path\dir") | Assert-Equals -Expected "C:\path\dir"
        [Ansible.IO.Path]::GetFullPath("C:/path/dir") | Assert-Equals -Expected "C:\path\dir"
        [Ansible.IO.Path]::GetFullPath("\\?\C:\path\dir") | Assert-Equals -Expected "\\?\C:\path\dir"
        [Ansible.IO.Path]::GetFullPath("\\?\C:\path/dir") | Assert-Equals -Expected "\\?\C:\path\dir"
        [Ansible.IO.Path]::GetFullPath("\\?\C:\path\$long_path\dir") | Assert-Equals -Expected "\\?\C:\path\$long_path\dir"
        [Ansible.IO.Path]::GetFullPath("\\127.0.0.1\c$\path\dir") | Assert-Equals -Expected "\\127.0.0.1\c$\path\dir"
        [Ansible.IO.Path]::GetFullPath("\\?\UNC\127.0.0.1\c$\path\$long_path\dir") | Assert-Equals -Expected "\\?\UNC\127.0.0.1\c$\path\$long_path\dir"
        [Ansible.IO.Path]::GetFullPath("\\?\UNC\127.0.0.1\c$\path/$long_path\dir") | Assert-Equals -Expected "\\?\UNC\127.0.0.1\c$\path\$long_path\dir"

        [Ansible.IO.Path]::GetFullPath("C:\path\dir\file.txt") | Assert-Equals -Expected "C:\path\dir\file.txt"
        [Ansible.IO.Path]::GetFullPath("C:/path/dir/file.txt") | Assert-Equals -Expected "C:\path\dir\file.txt"
        [Ansible.IO.Path]::GetFullPath("\\?\C:\path\dir\file.txt") | Assert-Equals -Expected "\\?\C:\path\dir\file.txt"
        [Ansible.IO.Path]::GetFullPath("\\?\C:\path\$long_path\dir\file.txt") | Assert-Equals -Expected "\\?\C:\path\$long_path\dir\file.txt"
        [Ansible.IO.Path]::GetFullPath("\\127.0.0.1\c$\path\dir\file.txt") | Assert-Equals -Expected "\\127.0.0.1\c$\path\dir\file.txt"
        [Ansible.IO.Path]::GetFullPath("\\127.0.0.1\c$\path\dir/file.txt") | Assert-Equals -Expected "\\127.0.0.1\c$\path\dir\file.txt"
        [Ansible.IO.Path]::GetFullPath("\\?\UNC\127.0.0.1\c$\path\$long_path\dir\file.txt") | Assert-Equals -Expected "\\?\UNC\127.0.0.1\c$\path\$long_path\dir\file.txt"
        [Ansible.IO.Path]::GetFullPath("\\?\UNC\127.0.0.1\c$\path\$long_path\dir/file.txt") | Assert-Equals -Expected "\\?\UNC\127.0.0.1\c$\path\$long_path\dir\file.txt"

        [Ansible.IO.Path]::GetFullPath("C:\path\dir\file.") | Assert-Equals -Expected "C:\path\dir\file"
        [Ansible.IO.Path]::GetFullPath("C:/path/dir/file.") | Assert-Equals -Expected "C:\path\dir\file"
        [Ansible.IO.Path]::GetFullPath("\\?\C:\path\dir\file.") | Assert-Equals -Expected "\\?\C:\path\dir\file"
        [Ansible.IO.Path]::GetFullPath("\\?\C:\path\$long_path\dir\file.") | Assert-Equals -Expected "\\?\C:\path\$long_path\dir\file"
        [Ansible.IO.Path]::GetFullPath("\\127.0.0.1\c$\path\dir\file.") | Assert-Equals -Expected "\\127.0.0.1\c$\path\dir\file"
        [Ansible.IO.Path]::GetFullPath("\\?\UNC\127.0.0.1\c$\path\dir\file.") | Assert-Equals -Expected "\\?\UNC\127.0.0.1\c$\path\dir\file"

        $failed = $false
        try {
            [Ansible.IO.Path]::GetFullPath($null)
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.ArgumentException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "The path is not of a legal form."
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true

        $failed = $false
        try {
            [Ansible.IO.Path]::GetFullPath("")
        } catch {
            $_.Exception.InnerException.GetType().FullName | Assert-Equals -Expected "System.ArgumentException"
            $_.Exception.InnerException.Message | Assert-Equals -Expected "The path is not of a legal form."
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true

        [Ansible.IO.Path]::GetFullPath("C:\") | Assert-Equals -Expected "C:\"
        [Ansible.IO.Path]::GetFullPath("C:/") | Assert-Equals -Expected "C:\"
        [Ansible.IO.Path]::GetFullPath("C:\a") | Assert-Equals -Expected "C:\a"
        [Ansible.IO.Path]::GetFullPath("C:\a\") | Assert-Equals -Expected "C:\a\"
        [Ansible.IO.Path]::GetFullPath("C:\a\b") | Assert-Equals -Expected "C:\a\b"
        [Ansible.IO.Path]::GetFullPath("C:/a") | Assert-Equals -Expected "C:\a"
        [Ansible.IO.Path]::GetFullPath("\\?") | Assert-Equals -Expected "\\?\"
        [Ansible.IO.Path]::GetFullPath("\\?\") | Assert-Equals -Expected "\\?\"
        [Ansible.IO.Path]::GetFullPath("\\?\C") | Assert-Equals -Expected "\\?\C"
        [Ansible.IO.Path]::GetFullPath("\\?\C:") | Assert-Equals -Expected "\\?\C:"
        [Ansible.IO.Path]::GetFullPath("\\?\C:\") | Assert-Equals -Expected "\\?\C:\"
        [Ansible.IO.Path]::GetFullPath("\\?\C:/") | Assert-Equals -Expected "\\?\C:\"
        [Ansible.IO.Path]::GetFullPath("\\?\C:\a") | Assert-Equals -Expected "\\?\C:\a"
        [Ansible.IO.Path]::GetFullPath("\\?\C:/a") | Assert-Equals -Expected "\\?\C:\a"
        [Ansible.IO.Path]::GetFullPath("\\?\C:/a/") | Assert-Equals -Expected "\\?\C:\a\"
        [Ansible.IO.Path]::GetFullPath("\\?\C:/a/b") | Assert-Equals -Expected "\\?\C:\a\b"

        [Ansible.IO.Path]::GetFullPath("\\server\share") | Assert-Equals -Expected "\\server\share"
        [Ansible.IO.Path]::GetFullPath("\\server\share\") | Assert-Equals -Expected "\\server\share\"
        [Ansible.IO.Path]::GetFullPath("\\server\share\path") | Assert-Equals -Expected "\\server\share\path"

        [Ansible.IO.Path]::GetFullPath("//server/share") | Assert-Equals -Expected "\\server\share"
        [Ansible.IO.Path]::GetFullPath("//server/share/") | Assert-Equals -Expected "\\server\share\"
        [Ansible.IO.Path]::GetFullPath("//server/share/path") | Assert-Equals -Expected "\\server\share\path"

        [Ansible.IO.Path]::GetFullPath("\\?\UNC") | Assert-Equals -Expected "\\?\UNC"
        [Ansible.IO.Path]::GetFullPath("\\?\UNC\") | Assert-Equals -Expected "\\?\UNC\"
        [Ansible.IO.Path]::GetFullPath("\\?\UNC\server") | Assert-Equals -Expected "\\?\UNC\server"
        [Ansible.IO.Path]::GetFullPath("\\?\UNC\server\") | Assert-Equals -Expected "\\?\UNC\server\"
        [Ansible.IO.Path]::GetFullPath("\\?\UNC\server\share") | Assert-Equals -Expected "\\?\UNC\server\share"
        [Ansible.IO.Path]::GetFullPath("\\?\UNC\server\share\") | Assert-Equals -Expected "\\?\UNC\server\share\"
        [Ansible.IO.Path]::GetFullPath("\\?\UNC\server\share\path") | Assert-Equals -Expected "\\?\UNC\server\share\path"
        [Ansible.IO.Path]::GetFullPath("\\?\UNC\server/share\path") | Assert-Equals -Expected "\\?\UNC\server\share\path"
        [Ansible.IO.Path]::GetFullPath("\\?\UNC\server/share\path\") | Assert-Equals -Expected "\\?\UNC\server\share\path\"
        [Ansible.IO.Path]::GetFullPath("\\?\UNC\server/share\path/") | Assert-Equals -Expected "\\?\UNC\server\share\path\"

        [Ansible.IO.Path]::GetFullPath("\\?/UNC") | Assert-Equals -Expected "\\?\UNC"
        [Ansible.IO.Path]::GetFullPath("\\?/UNC/") | Assert-Equals -Expected "\\?\UNC\"
        [Ansible.IO.Path]::GetFullPath("\\?/UNC/server") | Assert-Equals -Expected "\\?\UNC\server"
        [Ansible.IO.Path]::GetFullPath("\\?/UNC/server/") | Assert-Equals -Expected "\\?\UNC\server\"
        [Ansible.IO.Path]::GetFullPath("\\?/UNC/server/share") | Assert-Equals -Expected "\\?\UNC\server\share"
        [Ansible.IO.Path]::GetFullPath("\\?/UNC/server/share/") | Assert-Equals -Expected "\\?\UNC\server\share\"
        [Ansible.IO.Path]::GetFullPath("\\?/UNC/server/share/path") | Assert-Equals -Expected "\\?\UNC\server\share\path"

        [Ansible.IO.Path]::GetFullPath("\\?\UNC") | Assert-Equals -Expected "\\?\UNC"
        [Ansible.IO.Path]::GetFullPath("\\?\UNC/") | Assert-Equals -Expected "\\?\UNC\"
        [Ansible.IO.Path]::GetFullPath("\\?\UNC/server") | Assert-Equals -Expected "\\?\UNC\server"
        [Ansible.IO.Path]::GetFullPath("\\?\UNC/server/") | Assert-Equals -Expected "\\?\UNC\server\"
        [Ansible.IO.Path]::GetFullPath("\\?\UNC/server/share") | Assert-Equals -Expected "\\?\UNC\server\share"
        [Ansible.IO.Path]::GetFullPath("\\?\UNC/server/share/") | Assert-Equals -Expected "\\?\UNC\server\share\"
        [Ansible.IO.Path]::GetFullPath("\\?\UNC/server/share/path") | Assert-Equals -Expected "\\?\UNC\server\share\path"
    }

    "GetPathRoot tests" = {
        $long_path = "{0}\{0}\{0}\{0}\{0}\{0}\{0}\dir" -f ("a" * 250)

        [Ansible.IO.Path]::GetPathRoot("C:\path\dir") | Assert-Equals -Expected "C:\"
        [Ansible.IO.Path]::GetPathRoot("C:/path/dir") | Assert-Equals -Expected "C:\"
        [Ansible.IO.Path]::GetPathRoot("\\?\C:\path\dir") | Assert-Equals -Expected "\\?\C:\"
        [Ansible.IO.Path]::GetPathRoot("\\?\C:\path\$long_path\dir") | Assert-Equals -Expected "\\?\C:\"
        [Ansible.IO.Path]::GetPathRoot("\\127.0.0.1\c$\path\dir") | Assert-Equals -Expected "\\127.0.0.1\c$"
        [Ansible.IO.Path]::GetPathRoot("\\?\UNC\127.0.0.1\c$\path\$long_path\dir") | Assert-Equals -Expected "\\?\UNC\127.0.0.1\c$"

        [Ansible.IO.Path]::GetPathRoot("C:\path\dir\file.txt") | Assert-Equals -Expected "C:\"
        [Ansible.IO.Path]::GetPathRoot("C:/path/dir/file.txt") | Assert-Equals -Expected "C:\"
        [Ansible.IO.Path]::GetPathRoot("\\?\C:\path\dir\file.txt") | Assert-Equals -Expected "\\?\C:\"
        [Ansible.IO.Path]::GetPathRoot("\\?\C:\path\$long_path\dir\file.txt") | Assert-Equals -Expected "\\?\C:\"
        [Ansible.IO.Path]::GetPathRoot("\\127.0.0.1\c$\path\dir\file.txt") | Assert-Equals -Expected "\\127.0.0.1\c$"
        [Ansible.IO.Path]::GetPathRoot("\\?\UNC\127.0.0.1\c$\path\$long_path\dir\file.txt") | Assert-Equals -Expected "\\?\UNC\127.0.0.1\c$"

        [Ansible.IO.Path]::GetPathRoot("C:\path\dir\file.") | Assert-Equals -Expected "C:\"
        [Ansible.IO.Path]::GetPathRoot("C:/path/dir/file.") | Assert-Equals -Expected "C:\"
        [Ansible.IO.Path]::GetPathRoot("\\?\C:\path\dir\file.") | Assert-Equals -Expected "\\?\C:\"
        [Ansible.IO.Path]::GetPathRoot("\\?\C:\path\$long_path\dir\file.") | Assert-Equals -Expected "\\?\C:\"
        [Ansible.IO.Path]::GetPathRoot("\\127.0.0.1\c$\path\dir\file.") | Assert-Equals -Expected "\\127.0.0.1\c$"
        [Ansible.IO.Path]::GetPathRoot("\\?\UNC\127.0.0.1\c$\path\$long_path\dir\file.") | Assert-Equals -Expected "\\?\UNC\127.0.0.1\c$"

        [Ansible.IO.Path]::GetPathRoot("test") | Assert-Equals -Expected ""
        [Ansible.IO.Path]::GetPathRoot(".\test") | Assert-Equals -Expected ""
        [Ansible.IO.Path]::GetPathRoot("C:") | Assert-Equals -Expected "C:"
        [Ansible.IO.Path]::GetPathRoot("\\?\C:") | Assert-Equals -Expected "\\?\C:"
        [Ansible.IO.Path]::GetPathRoot("C:\") | Assert-Equals -Expected "C:\"
        [Ansible.IO.Path]::GetPathRoot("\\?\C:\") | Assert-Equals -Expected "\\?\C:\"
        [Ansible.IO.Path]::GetPathRoot("C:\path") | Assert-Equals -Expected "C:\"
        [Ansible.IO.Path]::GetPathRoot("\\?\C:\path") | Assert-Equals -Expected "\\?\C:\"
        [Ansible.IO.Path]::GetPathRoot("\\") | Assert-Equals -Expected "\\"
        [Ansible.IO.Path]::GetPathRoot("\\?\UNC\") | Assert-Equals -Expected "\\?\UNC\"
        [Ansible.IO.Path]::GetPathRoot("\\server") | Assert-Equals -Expected "\\server"
        [Ansible.IO.Path]::GetPathRoot("\\?\UNC\server") | Assert-Equals -Expected "\\?\UNC\server"
        [Ansible.IO.Path]::GetPathRoot("\\server\share") | Assert-Equals -Expected "\\server\share"
        [Ansible.IO.Path]::GetPathRoot("\\?\UNC\server\share") | Assert-Equals -Expected "\\?\UNC\server\share"
        [Ansible.IO.Path]::GetPathRoot("\\server\share\path") | Assert-Equals -Expected "\\server\share"
        [Ansible.IO.Path]::GetPathRoot("\\?\UNC\server\share\path") | Assert-Equals -Expected "\\?\UNC\server\share"
    }
}

foreach ($test_impl in $path_tests.GetEnumerator()) {
    $test = $test_impl.Key
    &$test_impl.Value
}

# Make sure a path that exceeds MAX_PATH is in the module tmpdir. This checks to make sure that the AnsibleModule
# cleanup task is able to delete these folders when Ansible.IO has been imported.
$max_folder = [Ansible.IO.Path]::Combine("\\?\$($module.Tmpdir)", "z" * 255)
[Ansible.IO.FileSystem]::CreateDirectory($max_folder)

$module.Result.data = "success"
$module.ExitJson()
