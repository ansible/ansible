#!powershell

#AnsibleRequires -CSharpUtil Ansible.Basic
#AnsibleRequires -CSharpUtil Ansible.IO
#Requires -Module Ansible.ModuleUtils.LinkUtil

$module = [Ansible.Basic.AnsibleModule]::Create($args, @{})

$path = [Ansible.IO.Path]::Combine($module.Tmpdir, '.ansible ÅÑŚÌβŁÈ [$!@^&test(;)]')

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

$tests = [Ordered]@{
    "Get-Link with normal directory" = {
        $actual = Get-Link -Path $test_path
        $actual | Assert-Equals -Expected $null
    }

    "Fail to create hard link to a non-existant target" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        $target = [Ansible.IO.Path]::Combine($test_path, "target.txt")

        $failed = $false
        try {
            New-Link -Path $source -TargetPath $target -Type hard
        } catch {
            $_.Exception.Message | Assert-Equals -Expected "link target '$target' does not exist, cannot create hard link"
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Fail to create hard link to a directory" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        $target = [Ansible.IO.Path]::Combine($test_path, "target.txt")
        [Ansible.IO.FileSystem]::CreateDirectory($target)

        $failed = $false
        try {
            New-Link -Path $source -TargetPath $target -Type hard
        } catch {
            $_.Exception.Message | Assert-Equals -Expected "cannot set the target for a hard link to a directory"
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Fail to create junction point to a file" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target.txt")
        Set-AnsibleContent -Path $target -Value "abc"

        $failed = $false
        try {
            New-Link -Path $source -TargetPath $target -Type junction
        } catch {
            $_.Exception.Message | Assert-Equals -Expected "cannot set the target for a junction point to a file"
            $failed = $true
        }
        $failed | Assert-Equals -Expected $true
    }

    "Create a relative symlink" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")
        [Ansible.IO.FileSystem]::CreateDirectory($target)

        # First try with -WhatIf
        New-Link -Path $source -TargetPath target -Type link -WhatIf
        [Ansible.IO.FileSystem]::Exists($source) | Assert-Equals -Expected $false

        New-Link -Path $source -TargetPath target -Type link
        [Ansible.IO.FileSystem]::DirectoryExists($source) | Assert-Equals -Expected $true

        $actual = Get-Link -Path $source
        $actual.Type | Assert-Equals -Expected "SymbolicLink"
        $actual.SubstituteName | Assert-Equals -Expected "target"
        $actual.PrintName | Assert-Equals -Expected "target"
        $actual.TargetPath | Assert-Equals -Expected "target"
        $actual.AbsolutePath | Assert-Equals -Expected $target
        $actual.HardTargets | Assert-Equals -Expected $null

        # Delete link with -WhatIf
        Remove-Link -Path $source -WhatIf
        [Ansible.IO.FileSystem]::DirectoryExists($source) | Assert-Equals -Expected $true

        Remove-Link -Path $source
        [Ansible.IO.FileSystem]::DirectoryExists($source) | Assert-Equals -Expected $false
    }

    "Create a file symbolic link" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")
        Set-AnsibleContent -Path $target -Value "abc"

        New-Link -Path $source -TargetPath $target -Type link -WhatIf
        [Ansible.IO.FileSystem]::Exists($source) | Assert-Equals -Expected $false

        New-Link -Path $source -TargetPath $target -Type link
        [Ansible.IO.FileSystem]::FileExists($source) | Assert-Equals -Expected $true


        if ($test_path.StartsWith("\\?\")) {
            $expected_sub_name = "\??\$($target.Substring(4))"
        } elseif ($test_path.StartsWith("\\")) {
            $expected_sub_name = "\??\UNC\$($target.Substring(2))"
        } else {
            $expected_sub_name = "\??\$target"
        }

        $actual = Get-Link -Path $source
        $actual.Type | Assert-Equals -Expected "SymbolicLink"
        $actual.SubstituteName | Assert-Equals -Expected $expected_sub_name
        $actual.PrintName | Assert-Equals -Expected $target
        $actual.TargetPath | Assert-Equals -Expected $target
        $actual.AbsolutePath | Assert-Equals -Expected $target
        $actual.HardTargets | Assert-Equals -Expected $null

        Remove-Link -Path $source -WhatIf
        [Ansible.IO.FileSystem]::FileExists($source) | Assert-Equals -Expected $true

        Remove-Link -Path $source
        [Ansible.IO.FileSystem]::FileExists($source) | Assert-Equals -Expected $false
    }

    "Create a file symbolic link to missing target" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source.txt")
        $target = [Ansible.IO.Path]::Combine($test_path, "target.txt")

        New-Link -Path $source -TargetPath $target -Type link -WhatIf
        [Ansible.IO.FileSystem]::Exists($source) | Assert-Equals -Expected $false

        New-Link -Path $source -TargetPath $target -Type link
        [Ansible.IO.FileSystem]::FileExists($source) | Assert-Equals -Expected $true

        if ($test_path.StartsWith("\\?\")) {
            $expected_sub_name = "\??\$($target.Substring(4))"
        } elseif ($test_path.StartsWith("\\")) {
            $expected_sub_name = "\??\UNC\$($target.Substring(2))"
        } else {
            $expected_sub_name = "\??\$target"
        }

        $actual = Get-Link -Path $source
        $actual.Type | Assert-Equals -Expected "SymbolicLink"
        $actual.SubstituteName | Assert-Equals -Expected $expected_sub_name
        $actual.PrintName | Assert-Equals -Expected $target
        $actual.TargetPath | Assert-Equals -Expected $target
        $actual.AbsolutePath | Assert-Equals -Expected $target
        $actual.HardTargets | Assert-Equals -Expected $null

        Remove-Link -Path $source -WhatIf
        [Ansible.IO.FileSystem]::FileExists($source) | Assert-Equals -Expected $true

        Remove-Link -Path $source
        [Ansible.IO.FileSystem]::FileExists($source) | Assert-Equals -Expected $false
    }

    "Create a directory symbolic link" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")
        [Ansible.IO.FileSystem]::CreateDirectory($target)

        New-Link -Path $source -TargetPath $target -Type link -WhatIf
        [Ansible.IO.FileSystem]::Exists($source) | Assert-Equals -Expected $false

        New-Link -Path $source -TargetPath $target -Type link
        [Ansible.IO.FileSystem]::DirectoryExists($source) | Assert-Equals -Expected $true

        if ($test_path.StartsWith("\\?\")) {
            $expected_sub_name = "\??\$($target.Substring(4))"
        } elseif ($test_path.StartsWith("\\")) {
            $expected_sub_name = "\??\UNC\$($target.Substring(2))"
        } else {
            $expected_sub_name = "\??\$target"
        }

        $actual = Get-Link -Path $source
        $actual.Type | Assert-Equals -Expected "SymbolicLink"
        $actual.SubstituteName | Assert-Equals -Expected $expected_sub_name
        $actual.PrintName | Assert-Equals -Expected $target
        $actual.TargetPath | Assert-Equals -Expected $target
        $actual.AbsolutePath | Assert-Equals -Expected $target
        $actual.HardTargets | Assert-Equals -Expected $null

        Remove-Link -Path $source -WhatIf
        [Ansible.IO.FileSystem]::DirectoryExists($source) | Assert-Equals -Expected $true

        Remove-Link -Path $source
        [Ansible.IO.FileSystem]::DirectoryExists($source) | Assert-Equals -Expected $false
    }

    "Create directory symbolic link to missing target" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")

        New-Link -Path $source -TargetPath $target -Type link -WhatIf
        [Ansible.IO.FileSystem]::Exists($source) | Assert-Equals -Expected $false

        New-Link -Path $source -TargetPath $target -Type link
        [Ansible.IO.FileSystem]::DirectoryExists($source) | Assert-Equals -Expected $true

        if ($test_path.StartsWith("\\?\")) {
            $expected_sub_name = "\??\$($target.Substring(4))"
        } elseif ($test_path.StartsWith("\\")) {
            $expected_sub_name = "\??\UNC\$($target.Substring(2))"
        } else {
            $expected_sub_name = "\??\$target"
        }

        $actual = Get-Link -Path $source
        $actual.Type | Assert-Equals -Expected "SymbolicLink"
        $actual.SubstituteName | Assert-Equals -Expected $expected_sub_name
        $actual.PrintName | Assert-Equals -Expected $target
        $actual.TargetPath | Assert-Equals -Expected $target
        $actual.AbsolutePath | Assert-Equals -Expected $target
        $actual.HardTargets | Assert-Equals -Expected $null

        Remove-Link -Path $source -WhatIf
        [Ansible.IO.FileSystem]::DirectoryExists($source) | Assert-Equals -Expected $true

        Remove-Link -Path $source
        [Ansible.IO.FileSystem]::DirectoryExists($source) | Assert-Equals -Expected $false
    }

    "Create a junction point" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")
        [Ansible.IO.FileSystem]::CreateDirectory($target)

        New-Link -Path $source -TargetPath $target -Type junction -WhatIf
        [Ansible.IO.FileSystem]::Exists($source) | Assert-Equals -Expected $false

        New-Link -Path $source -TargetPath $target -Type junction
        [Ansible.IO.FileSystem]::DirectoryExists($source) | Assert-Equals -Expected $true

        if ($test_path.StartsWith("\\?\")) {
            $expected_sub_name = "\??\$($target.Substring(4))"
        } elseif ($test_path.StartsWith("\\")) {
            $expected_sub_name = "\??\\\$($target.Substring(2))"
        } else {
            $expected_sub_name = "\??\$target"
        }

        $actual = Get-Link -Path $source
        $actual.Type | Assert-Equals -Expected "JunctionPoint"
        $actual.SubstituteName | Assert-Equals -Expected $expected_sub_name
        $actual.PrintName | Assert-Equals -Expected $target
        $actual.TargetPath | Assert-Equals -Expected $target
        $actual.AbsolutePath | Assert-Equals -Expected $target
        $actual.HardTargets | Assert-Equals -Expected $null

        Remove-Link -Path $source -WhatIf
        [Ansible.IO.FileSystem]::DirectoryExists($source) | Assert-Equals -Expected $true

        Remove-Link -Path $source
        [Ansible.IO.FileSystem]::DirectoryExists($source) | Assert-Equals -Expected $false
    }

    "Create a junction point to missing target" = {
        $source = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")

        New-Link -Path $source -TargetPath $target -Type junction -WhatIf
        [Ansible.IO.FileSystem]::Exists($source) | Assert-Equals -Expected $false

        New-Link -Path $source -TargetPath $target -Type junction
        [Ansible.IO.FileSystem]::DirectoryExists($source) | Assert-Equals -Expected $true

        if ($test_path.StartsWith("\\?\")) {
            $expected_sub_name = "\??\$($target.Substring(4))"
        } elseif ($test_path.StartsWith("\\")) {
            $expected_sub_name = "\??\\\$($target.Substring(2))"
        } else {
            $expected_sub_name = "\??\$target"
        }

        $actual = Get-Link -Path $source
        $actual.Type | Assert-Equals -Expected "JunctionPoint"
        $actual.SubstituteName | Assert-Equals -Expected $expected_sub_name
        $actual.PrintName | Assert-Equals -Expected $target
        $actual.TargetPath | Assert-Equals -Expected $target
        $actual.AbsolutePath | Assert-Equals -Expected $target
        $actual.HardTargets | Assert-Equals -Expected $null

        Remove-Link -Path $source -WhatIf
        [Ansible.IO.FileSystem]::DirectoryExists($source) | Assert-Equals -Expected $true

        Remove-Link -Path $source
        [Ansible.IO.FileSystem]::DirectoryExists($source) | Assert-Equals -Expected $false
    }

    "Create a hard link" = {
        if ($test_path.StartsWith("\\")) {
            # Cannot enumerate hard links over network path
            return
        }
        $source = [Ansible.IO.Path]::Combine($test_path, "source")
        $target = [Ansible.IO.Path]::Combine($test_path, "target")
        Set-AnsibleContent -Path $target -Value "abc"

        New-Link -Path $source -TargetPath $target -Type hard -WhatIf
        [Ansible.IO.FileSystem]::Exists($source) | Assert-Equals -Expected $false

        New-Link -Path $source -TargetPath $target -Type hard
        [Ansible.IO.FileSystem]::FileExists($source) | Assert-Equals -Expected $true

        $actual = Get-Link -Path $source
        $actual.Type | Assert-Equals -Expected "HardLink"
        $actual.SubstituteName | Assert-Equals -Expected $null
        $actual.PrintName | Assert-Equals -Expected $null
        $actual.TargetPath | Assert-Equals -Expected $null
        $actual.AbsolutePath | Assert-Equals -Expected $null
        $hard_targets = $actual.HardTargets | Sort-Object

        $hard_targets.Length | Assert-Equals -Expected 2
        $hard_targets[0] | Assert-Equals -Expected $source
        $hard_targets[1] | Assert-Equals -Expected $target
        Get-AnsibleContent -Path $source | Assert-Equals -Expected "abc"

        # Create a 2nd hard link
        $link2 = [Ansible.IO.Path]::Combine($test_path, "source2")
        New-Link -Path $link2 -TargetPath $target -Type hard
        [Ansible.IO.FileSystem]::FileExists($link2) | Assert-Equals -Expected $true

        $actual = Get-Link -Path $link2
        $hard_targets = $actual.HardTargets | Sort-Object
        $hard_targets.Length | Assert-Equals -Expected 3
        $hard_targets[0] | Assert-Equals -Expected $source
        $hard_targets[1] | Assert-Equals -Expected $link2
        $hard_targets[2] | Assert-Equals -Expected $target
        Get-AnsibleContent -Path $link2 | Assert-Equals -Expected "abc"

        Remove-Link -Path $source -WhatIf
        [Ansible.IO.FileSystem]::FileExists($source) | Assert-Equals -Expected $true

        Remove-Link -Path $source
        [Ansible.IO.FileSystem]::FileExists($source) | Assert-Equals -Expected $false

        $actual = Get-Link -Path $link2
        $actual.HardTargets.Length | Assert-Equals -Expected 2
    }

    "Remove-Link with normal file" = {
        $file_path = [Ansible.IO.Path]::Combine($test_path, "file.txt")
        Set-AnsibleContent -Path $file_path -Value "abc"

        Remove-Link -Path $file_path

        # Because the file is not a link it won't be deleted
        [Ansible.IO.FileSystem]::FileExists($file_path) | Assert-Equals -Expected $true
    }

    "Remove-Link with normal directory" = {
        $dir_path = [Ansible.IO.Path]::Combine($test_path, "directory")
        [Ansible.IO.FileSystem]::CreateDirectory($dir_path)

        Remove-Link -Path $dir_path

        # Because the dir is not a link it won't be deleted
        [Ansible.IO.FileSystem]::DirectoryExists($dir_path) | Assert-Equals -Expected $true
    }
}

foreach ($test_impl in $tests.GetEnumerator()) {
    # Run each test with
    #     1. A normal path
    #     2. A path that exceeds MAX_PATH
    #     3. A UNC path
    #     4. A UNC path that exceeds MAX_PATH

    # Normal path
    $test_path = [Ansible.IO.Path]::Combine($path, "short")
    Clear-Directory -Path $test_path
    $test = $test_impl.Key
    &$test_impl.Value

    # Local MAX_PATHi
    $test_path = [Ansible.IO.Path]::Combine("\\?\$path", "a" * 255)
    Clear-Directory -Path $test_path
    $test = "$($test_impl.Key) - MAX_PATH"
    &$test_impl.Value

    # UNC Path
    $unc_path = [Ansible.IO.Path]::Combine("localhost", "$($path.Substring(0, 1))$", $path.Substring(3))
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

$module.Result.data = "success"
$module.ExitJson()
