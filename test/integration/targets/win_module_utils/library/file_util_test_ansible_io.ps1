#!powershell

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.FileUtil

$ErrorActionPreference = "Stop"

$params = Parse-Args $args
$path = Get-AnsibleParam -obj $params -name "path" -type "path" -failifempty $true
$encrypt_tests = Get-AnsibleParam -obj $params -name "encrypt_tests" -type "bool" -default $false

$result = @{
    changed = $false
}

Import-FileUtil

Function Assert-Equals($actual, $expected) {
    if ($actual -ne $expected) {
        $call_stack = (Get-PSCallStack)[1]
        $error_msg = "AssertionError:`r`nActual: `"$actual`" != Expected: `"$expected`"`r`nLine: $($call_stack.ScriptLineNumber), Method: $($call_stack.Position.Text)"
        Fail-Json -obj $result -message $error_msg
    }
}

Function Assert-ArrayEquals($actual, $expected) {
    $equals = $true
    if ($actual.Count -ne $expected.Count) {
        $equals = $false
    } else {
        for ($i = 0; $i -lt $actual.Count; $i++) {
            if ($actual[$i] -ne $expected[$i]) {
                $equals = $false
                break
            }
        }
    }
    
    if (-not $equals) {
        $call_stack = (Get-PSCallStack)[1]
        $error_msg = "AssertionError:`r`nActual: `"$actual`" != Expected: `"$expected`"`r`nLine: $($call_stack.ScriptLineNumber), Method: $($call_stack.Position.Text)"
        Fail-Json -obj $result -message $error_msg
    }
}

Function Clear-TestDirectory($path) {
    $search_path = $path
    if (-not $search_path.StartsWith("\\?\")) {
        $search_path = "\\?\$search_path"
    }

    if (Test-AnsiblePath -Path $search_path) {
        # previous tests may have ended in a bad state and some folders are not
        # accessible to the current user. This defensively set's the owner back to
        # the current user so we can delete the folders
        $current_sid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
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

    [Ansible.IO.Directory]::CreateDirectory($search_path) > $null
}

Function Test-FileClass($root_path) {
    $file_path = "$root_path\file.txt"

    ### FileInfo Tests ###
    # Test Class Attributes when file does not exist
    $file = New-Object -TypeName Ansible.IO.FileInfo -ArgumentList $file_path
    Assert-Equals -actual ([Int32]$file.Attributes) -expected -1
    Assert-Equals -actual $file.CreationTimeUtc.ToFileTimeUtc() -expected 0
    Assert-Equals -actual $file.Directory.FullName -expected $root_path
    Assert-Equals -actual $file.DirectoryName -expected $root_path
    Assert-Equals -actual $file.DiskLength -expected $null
    Assert-Equals -actual $file.Exists -expected $false
    Assert-Equals -actual $file.Extension -expected ".txt"
    Assert-Equals -actual $file.FullName -expected $file_path
    Assert-Equals -actual $file.IsReadOnly -expected $true
    Assert-Equals -actual $file.LastAccessTimeUtc.ToFileTimeUtc() -expected 0
    Assert-Equals -actual $file.LastWriteTimeUtc.ToFileTimeUtc() -expected 0
    Assert-Equals -actual $file.Length -expected $null
    Assert-Equals -actual $file.Name -expected "file.txt"
    
    # Test Class Attributes when file exists
    $current_time = (Get-Date).ToFileTimeUtc()
    $fs = $file.Create()
    $fs.Close()
    $file.Refresh()
    Assert-Equals -actual $file.Attributes -expected ([System.IO.FileAttributes]::Archive)
    Assert-Equals -actual ($file.CreationTimeUtc.ToFileTimeUtc() -ge $current_time) -expected $true
    Assert-Equals -actual $file.Directory.FullName -expected $root_path
    Assert-Equals -actual $file.DirectoryName -expected $root_path
    Assert-Equals -actual $file.DiskLength -expected 0
    Assert-Equals -actual $file.Exists -expected $true
    Assert-Equals -actual $file.Extension -expected ".txt"
    Assert-Equals -actual $file.FullName -expected $file_path
    Assert-Equals -actual $file.IsReadOnly -expected $false
    Assert-Equals -actual ($file.LastAccessTimeUtc.ToFileTimeUtc() -ge $current_time) -expected $true
    Assert-Equals -actual ($file.LastWriteTimeUtc.ToFileTimeUtc() -ge $current_time) -expected $true
    Assert-Equals -actual $file.Length -expected 0
    Assert-Equals -actual $file.Name -expected "file.txt"

    # Set Properties
    $file.Attributes = $file.Attributes -bor [System.IO.FileAttributes]::Hidden
    Assert-Equals -actual $file.Attributes -expected ([System.IO.FileAttributes]::Archive -bor [System.IO.FileAttributes]::Hidden)

    $file.IsReadOnly = $true
    Assert-Equals -actual $file.Attributes.HasFlag([System.IO.FileAttributes]::ReadOnly) -expected $true

    $file.IsReadOnly = $false
    Assert-Equals -actual $file.Attributes.HasFlag([System.IO.FileAttributes]::ReadOnly) -expected $false
    
    $new_date = (Get-Date -Date "1993-06-11 06:51:32Z")
    $file.CreationTimeUtc = $new_date
    Assert-Equals -actual $file.CreationTimeUtc -expected $new_date

    $file.LastAccessTimeUtc = $new_date
    Assert-Equals -actual $file.LastAccessTimeUtc -expected $new_date

    $file.LastWriteTimeUtc = $new_date
    Assert-Equals -actual $file.LastWriteTimeUtc -expected $new_date

    # Test Functions
    # CreateText() fails if the file is already open
    $failed = $false
    try {
        $sw = $file.CreateText()
        $sw.Close()
    } catch {
        $failed = $true
        Assert-Equals -actual $_.Exception.Message -expected "Exception calling `"CreateText`" with `"0`" argument(s): `"Access to the path '$root_path\file.txt' is denied.`""
    }
    Assert-Equals -actual $failed -expected $true

    # compress/decompress
    $file.Compress()
    $file.Refresh()
    $actual = $file.Attributes
    Assert-Equals -actual $actual.HasFlag([System.IO.FileAttributes]::Compressed) -expected $true

    $file.Decompress()
    $file.Refresh()
    $actual = $file.Attributes
    Assert-Equals -actual $actual.HasFlag([System.IO.FileAttributes]::Compressed) -expected $false

    [Ansible.IO.File]::Compress($file.FullName)
    $actual = [Ansible.IO.File]::GetAttributes($file.FullName)
    Assert-Equals -actual $actual.HasFlag([System.IO.FileAttributes]::Compressed) -expected $true

    [Ansible.IO.File]::Decompress($file.FullName)
    $actual = [Ansible.IO.File]::GetAttributes($file.FullName)
    Assert-Equals -actual $actual.HasFlag([System.IO.FileAttributes]::Compressed) -expected $false

    $file.Delete()
    $file.Refresh()
    Assert-Equals -actual $file.Exists -expected $false
    
    $sw = $file.CreateText()
    try {
        $sw.WriteLine("line1")
        $sw.WriteLine("line2")
    } finally {
        $sw.Close()
    }
    $file.Refresh()

    $sr = $file.OpenText()
    try {
        $file_contents = $sr.ReadToEnd()
    } finally {
        $sr.Close()
    }
    Assert-Equals -actual $file_contents -expected "line1`r`nline2`r`n"

    $copied_file = $file.CopyTo("$root_path\copy.txt")
    Assert-Equals -actual $file.Exists -expected $true
    Assert-Equals -actual ([Ansible.IO.File]::Exists("$root_path\copy.txt")) -expected $true
    $file_hash = Get-AnsibleFileHash -Path $file.FullName
    $copied_file_hash = Get-AnsibleFileHash -Path $copied_file.FullName
    Assert-Equals -actual $file_hash -expected $copied_file_hash

    $failed = $false
    try {
        $file.CopyTo("$root_path\copy.txt")
    } catch {
        Assert-Equals -actual $_.Exception.Message -expected "Exception calling `"CopyTo`" with `"1`" argument(s): `"The file '$root_path\copy.txt' already exists.`""
        $failed = $true
    }
    Assert-Equals -actual $failed -expected $true

    $sw = $file.AppendText()
    try {
        $sw.WriteLine("line3")
    } finally {
        $sw.Close()
    }
    $copied_file = $file.CopyTo("$root_path\copy.txt", $true)
    Assert-Equals -actual $file.Exists -expected $true
    Assert-Equals -actual ([Ansible.IO.File]::Exists("$root_path\copy.txt")) -expected $true
    $file_hash = Get-AnsibleFileHash -Path $file.FullName
    $copied_file_hash = Get-AnsibleFileHash -Path $copied_file.FullName
    Assert-Equals -actual $file_hash -expected $copied_file_hash

    # also test out the line3 was appended correctly
    $sr = $file.OpenText()
    try {
        $file_contents = $sr.ReadToEnd()
    } finally {
        $sr.Close()
    }
    Assert-Equals -actual $file_contents -expected "line1`r`nline2`r`nline3`r`n"

    # these tests will only work over WinRM when become or CredSSP is used
    if ($encrypt_tests) {
        $file.Encrypt()
        $file.Refresh()
        Assert-Equals $file.Attributes.HasFlag([System.IO.FileAttributes]::Encrypted) -expected $true

        $file.Decrypt()
        $file.Refresh()
        Assert-Equals $file.Attributes.HasFlag([System.IO.FileAttributes]::Encrypted) -expected $false

        # try setting through attributes (this cannot be done in System.IO.* but we implemented here)
        $file.Attributes = [System.IO.FileAttributes]::Encrypted
        $file.Refresh()
        Assert-Equals $file.Attributes.HasFlag([System.IO.FileAttributes]::Encrypted) -expected $true

        $file.Attributes = [System.IO.FileAttributes]::Normal
        $file.Refresh()
        Assert-Equals $file.Attributes.HasFlag([System.IO.FileAttributes]::Encrypted) -expected $false
    }

    # set sparse through attribute (this cannot be done in System.IO.* but we implemented here)
    $file.Attributes = [System.IO.FileAttributes]::SparseFile
    $file.Refresh()
    Assert-Equals $file.Attributes.HasFlag([System.IO.FileAttributes]::SparseFile) -expected $true

    $file.Attributes = [System.IO.FileAttributes]::Normal
    $file.Refresh()
    Assert-Equals $file.Attributes.HasFlag([System.IO.FileAttributes]::SparseFile) -expected $false

    $original_hash = Get-AnsibleFileHash -Path $copied_file.FullName
    $copied_file.MoveTo("$root_path\moved.txt")
    Assert-Equals -actual ([Ansible.IO.File]::Exists("$root_path\copy.txt")) -expected $false
    Assert-Equals -actual ([Ansible.IO.File]::Exists("$root_path\moved.txt")) -expected $true
    $moved_hash = Get-AnsibleFileHash -path "$root_path\moved.txt"
    Assert-Equals -actual $moved_hash -expected $original_hash

    $target_file = New-Object -TypeName Ansible.IO.FileInfo -ArgumentList "$root_path\target.txt"
    $backup_file = New-Object -TypeName Ansible.IO.FileInfo -ArgumentList "$root_path\backup.txt"
    $sw = $target_file.CreateText()
    try {
        $sw.WriteLine("original target")
    } finally {
        $sw.Close()
    }
    $original_target_hash = Get-AnsibleFileHash -Path $target_file.FullName
    $original_source_hash = Get-AnsibleFileHash -Path $file.FullName
    $replaced_file = $file.Replace($target_file.FullName, $backup_file.FullName)
    $file.Refresh()
    $target_file.Refresh()
    $backup_file.Refresh()
    $new_target_hash = Get-AnsibleFileHash -Path $replaced_file.FullName
    $backup_hash = Get-AnsibleFileHash -Path $backup_file.FullName
    Assert-Equals -actual $file.Exists -expected $false
    Assert-Equals -actual $replaced_file.FullName -expected $target_file.FullName
    Assert-Equals -actual $replaced_file.Exists -expected $true
    Assert-Equals -actual $backup_file.Exists -expected $true
    Assert-Equals -actual $new_target_hash -expected $original_source_hash
    Assert-Equals -actual $backup_hash -expected $original_target_hash
    $file = $replaced_file

    $fs = $file.OpenRead()
    $failed = $false
    try {
        $fs.WriteByte([byte]0x21)
    } catch {
        $failed = $true
        Assert-Equals -actual $_.Exception.Message -expected "Exception calling `"WriteByte`" with `"1`" argument(s): `"Stream does not support writing.`""
    } finally {
        $fs.Close()
    }
    Assert-Equals -actual $failed -expected $true

    $fs = $file.OpenRead()
    try {
        $file_bytes = New-Object -TypeName Byte[] -ArgumentList $fs.Length
        $bytes_read = $fs.Read($file_bytes, 0, $fs.Length)
    } finally {
        $fs.Close()
    }
    $file_contents = ([System.Text.Encoding]::UTF8).GetString($file_bytes)
    Assert-Equals -actual $file_contents -expected "line1`r`nline2`r`nline3`r`n"

    $fs = $file.OpenWrite()
    try {
        $fs.WriteByte([byte]0x21)
    } finally {
        $fs.Close()
    }
    $fs = $file.OpenRead()
    try {
        $file_bytes = New-Object -TypeName Byte[] -ArgumentList $fs.Length
        $bytes_read = $fs.Read($file_bytes, 0, $fs.Length)
    } finally {
        $fs.Close()
    }
    $file_contents = ([System.Text.Encoding]::UTF8).GetString($file_bytes)
    Assert-Equals -actual $file_contents -expected "!ine1`r`nline2`r`nline3`r`n"

    $fs = $file.Open([System.IO.FileMode]::Create, [System.IO.FileAccess]::Write, [System.IO.FileShare]::ReadWrite)
    try {
        $fs.WriteByte([byte]0x21)
        $fs.Flush()
    } finally {
        $fs.Close()
    }
    $fs = $file.Open([System.IO.FileMode]::Open, [System.IO.FileAccess]::Read)
    try {
        $file_bytes = New-Object -TypeName Byte[] -ArgumentList $fs.Length
        $bytes_read = $fs.Read($file_bytes, 0, $fs.Length)
    } finally {
        $fs.Close()
    }
    $file_contents = ([System.Text.Encoding]::UTF8).GetString($file_bytes)
    Assert-Equals -actual $file_contents -expected "!"

    # open a file with append (CreateFileW doesn't work with append so make sure the stuff around it is fine)
    $fs = $file.Open([System.IO.FileMode]::Append, [System.IO.FileAccess]::Write)
    try {
        $fs.WriteByte([byte]0x21)
        $fs.Flush()
    } finally {
        $fs.Close()
    }
    $fs = $file.Open([System.IO.FileMode]::Open, [System.IO.FileAccess]::Read)
    try {
        $file_bytes = New-Object -TypeName Byte[] -ArgumentList $fs.Length
        $bytes_read = $fs.Read($file_bytes, 0, $fs.Length)
    } finally {
        $fs.Close()
    }
    $file_contents = ([System.Text.Encoding]::UTF8).GetString($file_bytes)
    Assert-Equals -actual $file_contents -expected "!!"

    # test out alternative streams
    $actual = $file.GetStreamInfo()
    Assert-Equals -actual $actual.Count -expected 1
    Assert-Equals -actual $actual[0].GetType().FullName -expected "Ansible.IO.StreamInformation"
    $actual = [Ansible.IO.File]::GetStreamInfo($file.FullName)
    Assert-Equals -actual $actual.Count -expected 1
    Assert-Equals -actual $actual[0].GetType().FullName -expected "Ansible.IO.StreamInformation"
    Assert-Equals -actual $actual[0].Length -expected 2
    Assert-Equals -actual $actual[0].StreamName -expected ""
    Assert-Equals -actual $actual[0].StreamPath -expected "$($file.FullName)::`$DATA"
    Assert-Equals -actual $actual[0].StreamType -expected '$DATA'

    # write to the alternative streams
    [Ansible.IO.File]::WriteAllText($file.FullName, "default stream")
    [Ansible.IO.File]::WriteAllText("$($file.FullName):alternative stream 1", "alternative stream 1")
    [Ansible.IO.File]::WriteAllText("$($file.FullName):alternative stream 2:`$DATA", "alternative stream 2")
    $actual = [Ansible.IO.File]::GetStreamInfo($file.FullName)
    Assert-Equals -actual $actual.Count -expected 3
    Assert-Equals -actual $actual[0].GetType().FullName -expected "Ansible.IO.StreamInformation"
    $actual = [Ansible.IO.FIle]::GetStreamInfo($file.FullName)
    Assert-Equals -actual $actual.Count -expected 3
    Assert-Equals -actual $actual[0].Length -expected 14
    Assert-Equals -actual $actual[0].StreamName -expected ""
    Assert-Equals -actual $actual[0].StreamPath -expected "$($file.FullName)::`$DATA"
    Assert-Equals -actual $actual[0].StreamType -expected '$DATA'
    Assert-Equals -actual $actual[1].Length -expected 20
    Assert-Equals -actual $actual[1].StreamName -expected "alternative stream 1"
    Assert-Equals -actual $actual[1].StreamPath -expected "$($file.FullName):alternative stream 1:`$DATA"
    Assert-Equals -actual $actual[1].StreamType -expected '$DATA'
    Assert-Equals -actual $actual[2].Length -expected 20
    Assert-Equals -actual $actual[2].StreamName -expected "alternative stream 2"
    Assert-Equals -actual $actual[2].StreamPath -expected "$($file.FullName):alternative stream 2:`$DATA"
    Assert-Equals -actual $actual[2].StreamType -expected '$DATA'

    # test that we can use the path returned by a StreamInformation object
    $actual_stream1 = [Ansible.IO.File]::ReadAllText($actual[0].StreamPath)
    $actual_stream2 = [Ansible.IO.File]::ReadAllText($actual[1].StreamPath)
    $actual_stream3 = [Ansible.IO.File]::ReadAllText($actual[2].StreamPath)
    $actual_stream_manual = [Ansible.IO.File]::ReadAllText("$($file.FullName):alternative stream 1")
    Assert-Equals -actual $actual_stream1 -expected "default stream"
    Assert-Equals -actual $actual_stream2 -expected "alternative stream 1"
    Assert-Equals -actual $actual_stream3 -expected "alternative stream 2"
    Assert-Equals -actual $actual_stream_manual -expected "alternative stream 1"

    $current_sid = ([System.Security.Principal.WindowsIdentity]::GetCurrent()).User
    $everyone_sid = New-Object -TypeName System.Security.Principal.SecurityIdentifier -ArgumentList "S-1-1-0"
    
    $acl = New-Object -TypeName System.Security.AccessControl.FileSecurity
    $acl.SetGroup($everyone_sid)
    $acl.SetOwner($current_sid)
    $acl.SetAccessRule((New-Object -TypeName System.Security.AccessControl.FileSystemAccessRule -ArgumentList $everyone_sid, "FullControl", "Allow"))
    $file.SetAccessControl($acl)

    $file.Refresh()
    $acl = $file.GetAccessControl()
    $access_rules = $acl.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier])
    $explicit_access_rules = $access_rules | Where-Object { $_.IsInherited -eq $false }
    $owner = $acl.GetOwner([System.Security.Principal.SecurityIdentifier])
    $group = $acl.GetGroup([System.Security.Principal.SecurityIdentifier])
    Assert-Equals -actual $owner -expected $current_sid
    Assert-Equals -actual $group -expected $everyone_sid
    Assert-Equals -actual $explicit_access_rules.Count -expected 1
    Assert-Equals -actual $explicit_access_rules[0].IdentityReference -expected $everyone_sid
    
    $limited_acl = $file.GetAccessControl([System.Security.AccessControl.AccessControlSections]::Owner)
    $owner = $limited_acl.GetOwner([System.Security.Principal.SecurityIdentifier])
    $group = $limited_acl.GetGroup([System.Security.Principal.SecurityIdentifier])
    Assert-Equals -actual $owner -expected $current_sid
    Assert-Equals -actual $group -expected $null

    ### File Tests ###
    Assert-Equals -actual ([Ansible.IO.File]::Exists($root_path)) -expected $false
    Assert-Equals -actual ([Ansible.IO.File]::Exists($file_path)) -expected $false

    $fs = [Ansible.IO.File]::Create($file_path)
    $fs.Close()
    Assert-Equals -actual ([Ansible.IO.File]::Exists($file_path)) -expected $true

    [Ansible.IO.File]::Delete($file_path)
    Assert-Equals -actual ([Ansible.IO.File]::Exists($file_path)) -expected $false

    # make sure we can delete a file with the ReadOnly attribute set
    $fs = [Ansible.IO.File]::Create($file_path)
    $fs.Close()
    [Ansible.IO.File]::SetAttributes($file_path, [System.IO.FileAttributes]::ReadOnly)
    [Ansible.IO.File]::Delete($file_path)
    Assert-Equals -actual ([Ansible.IO.File]::Exists($file_path)) -expected $false

    $fs = [Ansible.IO.File]::Create($file_path, 4096, [System.IO.FileOptions]::None, $acl)
    $fs.Close()
    $acl = [Ansible.IO.File]::GetAccessControl($file_path)
    $access_rules = $acl.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier])
    $explicit_access_rules = $access_rules | Where-Object { $_.IsInherited -eq $false }
    $owner = $acl.GetOwner([System.Security.Principal.SecurityIdentifier])
    $group = $acl.GetGroup([System.Security.Principal.SecurityIdentifier])
    Assert-Equals -actual $owner -expected $current_sid
    Assert-Equals -actual $group -expected $everyone_sid
    Assert-Equals -actual $explicit_access_rules.Count -expected 1
    Assert-Equals -actual $explicit_access_rules[0].IdentityReference -expected $everyone_sid

    # need to be an admin to set this
    if ([bool](([System.Security.Principal.WindowsIdentity]::GetCurrent()).groups -match "S-1-5-32-544")) {
        $admin_sid = New-Object -TypeName System.Security.Principal.SecurityIdentifier -ArgumentList "S-1-5-32-544"
        $acl.SetOwner($admin_sid)
        [Ansible.IO.File]::SetAccessControl($file_path, $acl)

        $limited_acl = [Ansible.IO.File]::GetAccessControl($file_path, [System.Security.AccessControl.AccessControlSections]::Owner)
        $owner = $limited_acl.GetOwner([System.Security.Principal.SecurityIdentifier])
        $group = $limited_acl.GetGroup([System.Security.Principal.SecurityIdentifier])
        Assert-Equals -actual $owner -expected $admin_sid
        Assert-Equals -actual $group -expected $null
    }

    [Ansible.IO.File]::SetCreationTimeUtc($file_path, $new_date)
    $creation_time = [Ansible.IO.File]::GetCreationTimeUtc($file_path)
    Assert-Equals -actual $creation_time -expected $new_date

    [Ansible.IO.File]::SetLastAccessTimeUtc($file_path, $new_date)
    $lastaccess_time = [Ansible.IO.File]::GetLastAccessTimeUtc($file_path)
    Assert-Equals -actual $lastaccess_time -expected $new_date

    [Ansible.IO.File]::SetLastWriteTimeUtc($file_path, $new_date)
    $lastwrite_time = [Ansible.IO.File]::GetLastWriteTimeUtc($file_path)
    Assert-Equals -actual $lastwrite_time -expected $new_date

    $attributes = [Ansible.IO.File]::GetAttributes($file_path)
    Assert-Equals -actual $attributes -expected ([System.IO.FileAttributes]::Archive)

    [Ansible.IO.File]::SetAttributes($file_path, ($attributes -bor [System.IO.FileAttributes]::Hidden))
    $attributes = [Ansible.IO.File]::GetAttributes($file_path)
    Assert-Equals -actual $attributes -expected ([System.IO.FileAttributes]::Archive -bor [System.IO.FileAttributes]::Hidden)

    if ($encrypt_tests) {
        [Ansible.IO.File]::Encrypt($file_path)
        $attributes = [Ansible.IO.File]::GetAttributes($file_path)
        Assert-Equals -actual $attributes.HasFlag([System.IO.FileAttributes]::Encrypted) -expected $true

        [Ansible.IO.File]::Decrypt($file_path)
        $attributes = [Ansible.IO.File]::GetAttributes($file_path)
        Assert-Equals -actual $attributes.HasFlag([System.IO.FileAttributes]::Encrypted) -expected $false
    }

    [Ansible.IO.File]::AppendAllText($file_path, "line1`r`nline2`r`n")
    $file_contents = [Ansible.IO.File]::ReadAllText($file_path)
    Assert-Equals -actual $file_contents -expected "line1`r`nline2`r`n"

    [Ansible.IO.File]::AppendAllText($file_path, "line3`r`nline4`r`n")
    $file_contents = [Ansible.IO.File]::ReadAllText($file_path)
    Assert-Equals -actual $file_contents -expected "line1`r`nline2`r`nline3`r`nline4`r`n"

    [Ansible.IO.File]::Copy($file_path, "$root_path\copy-file.txt")
    Assert-Equals -actual ([Ansible.IO.File]::Exists($file_path)) -expected $true
    Assert-Equals -actual ([Ansible.IO.File]::Exists("$root_path\copy-file.txt")) -expected $true
    $source_hash = Get-AnsibleFileHash -Path $file_path
    $target_hash = Get-AnsibleFileHash -Path "$root_path\copy-file.txt"
    Assert-Equals -actual $target_hash -expected $source_hash

    [Ansible.IO.File]::Move($file_path, "$root_path\move-file.txt")
    Assert-Equals -actual ([Ansible.IO.File]::Exists($file_path)) -expected $false
    Assert-Equals -actual ([Ansible.IO.File]::Exists("$root_path\move-file.txt")) -expected $true
    $target_hash = Get-AnsibleFileHash -Path "$root_path\move-file.txt"
    Assert-Equals -actual $target_hash -expected $source_hash

    $failed = $false
    try {
        [Ansible.IO.File]::Move("$root_path\copy-file.txt", "$root_path\move-file.txt")
    } catch {
        $failed = $true
        Assert-Equals -actual $_.Exception.Message -expected "Exception calling `"Move`" with `"2`" argument(s): `"Cannot create a file when that file already exists`""
    }
    Assert-Equals -actual $failed -expected $true

    $fs = [Ansible.IO.File]::Create($file_path)
    $fs.Close()
    [Ansible.IO.File]::AppendAllText($file_path, "source text")
    [Ansible.IO.File]::Delete("$root_path\target.txt")
    $fs = [Ansible.IO.File]::Create("$root_path\target.txt")
    $fs.Close()
    [Ansible.IO.File]::AppendAllText("$root_path\target.txt", "target text")

    $source_hash = Get-AnsibleFileHash -Path $file_path
    $target_hash = Get-AnsibleFileHash -Path "$root_path\target.txt"
    [Ansible.IO.File]::Replace($file_path, "$root_path\target.txt", "$root_path\backup.txt")
    Assert-Equals -actual ([Ansible.IO.File]::Exists($file_path)) -expected $false
    Assert-Equals -actual ([Ansible.IO.File]::Exists("$root_path\target.txt")) -expected $true
    Assert-Equals -actual ([Ansible.IO.File]::Exists("$root_path\backup.txt")) -expected $true
    $new_target_hash = Get-AnsibleFileHash -Path "$root_path\target.txt"
    $backup_hash = Get-AnsibleFileHash -Path "$root_path\backup.txt"
    Assert-Equals -actual $new_target_hash -expected $source_hash
    Assert-Equals -actual $backup_hash -expected $target_hash

    $file_bytes = [Ansible.IO.File]::ReadAllBytes("$root_path\target.txt")
    $file_contents = ([System.Text.Encoding]::UTF8).GetString($file_bytes)
    Assert-Equals -actual $file_contents -expected "source text"

    $utf8_bytes = ([System.Text.Encoding]::UTF8).GetBytes("Hello World!")
    $utf16_bytes = ([System.Text.Encoding]::Unicode).GetBytes("Hello World!")
    $fs = [Ansible.IO.File]::OpenWrite("$root_path\utf8.txt")
    try {
        $fs.Write($utf8_bytes, 0, $utf8_bytes.Length)
    } finally {
        $fs.Close()
    }
    $fs = [Ansible.IO.File]::OpenWrite("$root_path\utf16.txt")
    try {
        $fs.Write($utf16_bytes, 0, $utf16_bytes.Length)
    } finally {
        $fs.Close()
    }

    [Ansible.IO.File]::AppendAllText("$root_path\utf8.txt", "`r`nanother line")
    $expected_text = "Hello World!`r`nanother line"
    $expected_bytes = ([System.Text.Encoding]::UTF8).GetBytes($expected_text)
    $file_bytes = [Ansible.IO.File]::ReadAllBytes("$root_path\utf8.txt")
    $file_text = [Ansible.IO.File]::ReadAllText("$root_path\utf8.txt")
    $file_lines = [Ansible.IO.File]::ReadAllLines("$root_path\utf8.txt")
    $file_lines_enumerable = [Ansible.IO.File]::ReadLines("$root_path\utf8.txt")
    Assert-ArrayEquals -actual $file_bytes -expected $expected_bytes
    Assert-Equals -actual $file_text -expected $expected_text
    Assert-Equals -actual $file_lines.Count -expected 2
    Assert-Equals -actual $file_lines[0] -expected "Hello World!"
    Assert-Equals -actual $file_lines[1] -expected "another line"
    $is_first = $true
    foreach ($line in $file_lines_enumerable) {
        if ($is_first) {
            Assert-Equals -actual $line -expected "Hello World!"
        } else {
            Assert-Equals -actual $line -expected "another line"
        }
        $is_first = $false
    }


    [Ansible.IO.File]::AppendAllText("$root_path\utf16.txt", "`r`nanother line", [System.Text.Encoding]::Unicode)
    $expected_text = "Hello World!`r`nanother line"
    $expected_bytes = ([System.Text.Encoding]::Unicode).GetBytes($expected_text)
    $file_bytes = [Ansible.IO.File]::ReadAllBytes("$root_path\utf16.txt")
    $file_text = [Ansible.IO.File]::ReadAllText("$root_path\utf16.txt", [System.Text.Encoding]::Unicode)
    $file_lines = [Ansible.IO.File]::ReadAllLines("$root_path\utf16.txt", [System.Text.Encoding]::Unicode)
    $file_lines_enumerable = [Ansible.IO.File]::ReadLines("$root_path\utf16.txt", [System.Text.Encoding]::Unicode)
    Assert-ArrayEquals -actual $file_bytes -expected $expected_bytes
    Assert-Equals -actual $file_text -expected $expected_text
    Assert-Equals -actual $file_lines.Count -expected 2
    Assert-Equals -actual $file_lines[0] -expected "Hello World!"
    Assert-Equals -actual $file_lines[1] -expected "another line"
    $is_first = $true
    foreach ($line in $file_lines_enumerable) {
        if ($is_first) {
            Assert-Equals -actual $line -expected "Hello World!"
        } else {
            Assert-Equals -actual $line -expected "another line"
        }
        $is_first = $false
    }

    [Ansible.IO.File]::WriteAllLines("$root_path\utf8.txt", [string[]]@("line 1", "line 2"))
    $expected_bytes = [System.Text.Encoding]::UTF8.GetBytes("line 1`r`nline 2`r`n")
    $file_bytes = [Ansible.IO.File]::ReadAllBytes("$root_path\utf8.txt")
    Assert-ArrayEquals -actual $file_bytes -expected $expected_bytes

    [Ansible.IO.File]::WriteAllLines("$root_path\utf16.txt", [string[]]@("line 1", "line 2"), [System.Text.Encoding]::Unicode)
    $expected_bytes = [byte[]](([System.Text.Encoding]::Unicode).GetPreamble() + ([System.Text.Encoding]::Unicode).GetBytes("line 1`r`nline 2`r`n"))
    $file_bytes = [Ansible.IO.File]::ReadAllBytes("$root_path\utf16.txt")
    Assert-ArrayEquals -actual $file_bytes -expected $expected_bytes

    [Ansible.IO.File]::WriteAllText("$root_path\utf8.txt", "another line 1`r`nanother line 2`r`n")
    $expected_bytes = [System.Text.Encoding]::UTF8.GetBytes("another line 1`r`nanother line 2`r`n")
    $file_bytes = [Ansible.IO.File]::ReadAllBytes("$root_path\utf8.txt")
    Assert-ArrayEquals -actual $file_bytes -expected $expected_bytes

    [Ansible.IO.File]::WriteAllText("$root_path\utf16.txt", "another line 1`r`nanother line 2`r`n", [System.Text.Encoding]::Unicode)
    $expected_bytes = [byte[]](([System.Text.Encoding]::Unicode).GetPreamble() + ([System.Text.Encoding]::Unicode).GetBytes("another line 1`r`nanother line 2`r`n"))
    $file_bytes = [Ansible.IO.File]::ReadAllBytes("$root_path\utf16.txt")
    Assert-ArrayEquals -actual $file_bytes -expected $expected_bytes

    [Ansible.IO.File]::WriteAllBytes("$root_path\utf8.txt", [byte[]]@(0x21, 0x21))
    $file_contents = [Ansible.IO.File]::ReadAllText("$root_path\utf8.txt")
    Assert-Equals -actual $file_contents -expected "!!"

    $sw = [Ansible.IO.File]::AppendText("$root_path\utf8.txt")
    try {
        $sw.WriteLine("!!")
    } finally {
        $sw.Close()
    }
    $file_contents = [Ansible.IO.File]::ReadAllText("$root_path\utf8.txt")
    Assert-Equals -actual $file_contents -expected "!!!!`r`n"

    $sw = [Ansible.IO.File]::CreateText("$root_path\utf8.txt")
    try {
        $sw.WriteLine("!!")
    } finally {
        $sw.Close()
    }
    $file_contents = [Ansible.IO.File]::ReadAllText("$root_path\utf8.txt")
    Assert-Equals -actual $file_contents -expected "!!`r`n"

    $sr = [Ansible.IO.File]::OpenText("$root_path\utf8.txt")
    try {
        $file_contents = $sr.ReadToEnd()
    } finally {
        $sr.Close()
    }
    Assert-Equals -actual $file_contents -expected "!!`r`n"

    $fs = [Ansible.IO.File]::OpenRead("$root_path\utf8.txt")
    try {
        Assert-Equals -actual $fs.CanRead -expected $true
        Assert-Equals -actual $fs.CanWrite -expected $false
        $file_bytes = New-Object -TypeName Byte[] -ArgumentList $fs.Length
        $bytes_read = $fs.Read($file_bytes, 0, $fs.Length)
    } finally {
        $fs.Close()
    }
    Assert-ArrayEquals -actual $file_bytes -expected ([byte[]]@(33, 33, 13, 10))

    $fs = [Ansible.IO.File]::OpenWrite("$root_path\utf8.txt")
    try {
        Assert-Equals -actual $fs.CanRead -expected $false
        Assert-Equals -actual $fs.CanWrite -expected $true
        $fs.WriteByte([byte]32)
    } finally {
        $fs.Close()
    }
    $file_bytes = [Ansible.IO.File]::ReadAllBytes("$root_path\utf8.txt")
    Assert-ArrayEquals -actual $file_bytes -expected ([byte[]]@(32, 33, 13, 10))

    $fs = [Ansible.IO.File]::Open("$root_path\utf8.txt", [System.IO.FileMode]::Create, [System.IO.FileAccess]::Write, [System.IO.FileShare]::ReadWrite)
    try {
        Assert-Equals -actual $fs.CanRead -expected $false
        Assert-Equals -actual $fs.CanWrite -expected $true
        $fs.WriteByte([byte]33)
        $fs.Flush()
    } finally {
        $fs.Close()
    }
    $fs = [Ansible.IO.File]::Open("$root_path\utf8.txt", [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read)
    try {
        Assert-Equals -actual $fs.CanRead -expected $true
        Assert-Equals -actual $fs.CanWrite -expected $false
        $file_bytes = New-Object -TypeName Byte[] -ArgumentList $fs.Length
        $bytes_read = $fs.Read($file_bytes, 0, $fs.Length)
    } finally {
        $fs.Close()
    }
    Assert-ArrayEquals -actual $file_bytes -expected ([byte[]]@(33))

    # open a file with append (CreateFileW doesn't work with append so make sure the stuff around it is fine)
    $fs = [Ansible.IO.File]::Open("$root_path\utf8.txt", [System.IO.FileMode]::Append, [System.IO.FileAccess]::ReadWrite)
    try {
        Assert-Equals -actual $fs.CanRead -expected $true
        Assert-Equals -actual $fs.CanWrite -expected $true
        $fs.WriteByte([byte]32)
        $fs.Flush()
    } finally {
        $fs.Close()
    }
    $file_bytes = [Ansible.IO.File]::ReadAllBytes("$root_path\utf8.txt")
    Assert-ArrayEquals -actual $file_bytes -expected ([byte[]]@(33, 32))
}

Function Test-DirectoryClass($root_path) {
    $directory_path = "$root_path\dir"

    ### DirectoryInfo Tests ###
    $dir = New-Object -TypeName Ansible.IO.DirectoryInfo -ArgumentList $directory_path

    # Test class attributes when it doesn't exist
    Assert-Equals -actual $dir.Exists -expected $false
    Assert-Equals -actual $dir.Name -expected "dir"
    Assert-Equals -actual $dir.Parent.ToString() -expected $root_path
    if ($root_path.StartsWith("\\?\UNC\127.0.0.1")) {
        Assert-Equals -actual $dir.Root.ToString() -expected "\\?\UNC\127.0.0.1\c$"
    } elseif ($root_path.StartsWith("\\?\")) {
        Assert-Equals -actual $dir.Root.ToString() -expected "\\?\C:\"
    } elseif ($root_path.StartsWith("\\127.0.0.1")) {
        Assert-Equals -actual $dir.Root.ToString() -expected "\\127.0.0.1\c$"
    } else {
        Assert-Equals -actual $dir.Root.ToString() -expected "C:\"
    }
    Assert-Equals -actual ([Int32]$dir.Attributes) -expected -1
    Assert-Equals -actual $dir.CreationTimeUtc.ToFileTimeUtc() -expected 0
    Assert-Equals -actual $dir.Extension -expected ""
    Assert-Equals -actual $dir.FullName -expected $directory_path
    Assert-Equals -actual $dir.LastAccessTimeUtc.ToFileTimeUtc() -expected 0
    Assert-Equals -actual $dir.LastWriteTimeUtc.ToFileTimeUtc() -expected 0

    # create directory
    $current_time = (Get-Date).ToFileTimeUtc()
    $dir.Create()
    $dir.Refresh() # resets the properties of the class

    # Test class attributes when it does exist
    Assert-Equals -actual $dir.Exists -expected $true
    Assert-Equals -actual $dir.Name -expected "dir"
    Assert-Equals -actual $dir.Parent.ToString() -expected $root_path 
    if ($root_path.StartsWith("\\?\UNC\127.0.0.1")) {
        Assert-Equals -actual $dir.Root.ToString() -expected "\\?\UNC\127.0.0.1\c$"
    } elseif ($root_path.StartsWith("\\?\")) {
        Assert-Equals -actual $dir.Root.ToString() -expected "\\?\C:\"
    } elseif ($root_path.StartsWith("\\127.0.0.1")) {
        Assert-Equals -actual $dir.Root.ToString() -expected "\\127.0.0.1\c$"
    } else {
        Assert-Equals -actual $dir.Root.ToString() -expected "C:\"
    }
    Assert-Equals -actual $dir.Attributes -expected ([System.IO.FileAttributes]::Directory)
    Assert-Equals -actual ($dir.CreationTimeUtc.ToFileTimeUtc() -ge $current_time) -expected $true
    Assert-Equals -actual $dir.Extension -expected ""
    Assert-Equals -actual $dir.FullName -expected $directory_path
    Assert-Equals -actual ($dir.LastAccessTimeUtc.ToFileTimeUtc() -ge $current_time) -expected $true
    Assert-Equals -actual ($dir.LastWriteTimeUtc.ToFileTimeUtc() -ge $current_time) -expected $true

    # set properties
    $dir.Attributes = $dir.Attributes -bor [System.IO.FileAttributes]::Archive -bor [System.IO.FileAttributes]::Hidden
    Assert-Equals -actual $dir.Attributes -expected ([System.IO.FileAttributes]::Directory -bor [System.IO.FileAttributes]::Archive -bor [System.IO.FileAttributes]::Hidden)

    $new_date = (Get-Date -Date "1993-06-11 06:51:32Z")
    $dir.CreationTimeUtc = $new_date
    Assert-Equals -actual $dir.CreationTimeUtc.ToFileTimeUtc() -expected $new_date.ToFileTimeUtc()
    $dir.LastAccessTimeUtc = $new_date
    Assert-Equals -actual $dir.LastAccessTimeUtc.ToFileTimeUtc() -expected $new_date.ToFileTimeUtc()
    $dir.LastWriteTimeUtc = $new_date
    Assert-Equals -actual $dir.LastWriteTimeUtc.ToFileTimeUtc() -expected $new_date.ToFileTimeUtc()

    # test DirectoryInfo methods
    # create tests
    $subdir = $dir.CreateSubDirectory("subdir")
    Assert-Equals -actual ([Ansible.IO.Directory]::Exists("$directory_path\subdir")) -expected $true

    # compress/decompress
    $dir.Compress()
    $dir.Refresh()
    $actual = $dir.Attributes
    Assert-Equals -actual $actual.HasFlag([System.IO.FileAttributes]::Compressed) -expected $true

    $dir.Decompress()
    $dir.Refresh()
    $actual = $dir.Attributes
    Assert-Equals -actual $actual.HasFlag([System.IO.FileAttributes]::Compressed) -expected $false

    # set through attributes - System.IO does not offer this
    $dir.Attributes = [System.IO.FileAttributes]::Compressed
    $dir.Refresh()
    Assert-Equals -actual $dir.Attributes.HasFlag([System.IO.FileAttributes]::Compressed) -expected $true

    $dir.Decompress()
    $dir.Attributes = [System.IO.FileAttributes]::Directory
    $dir.Refresh()
    Assert-Equals -actual $dir.Attributes.HasFlag([System.IO.FileAttributes]::Compressed) -expected $false

    [Ansible.IO.Directory]::Compress($dir.FullName)
    $actual = [Ansible.IO.File]::GetAttributes($dir.FullName)
    Assert-Equals -actual $actual.HasFlag([System.IO.FileAttributes]::Compressed) -expected $true

    [Ansible.IO.Directory]::Decompress($dir.FullName)
    $actual = [Ansible.IO.File]::GetAttributes($dir.FullName)
    Assert-Equals -actual $actual.HasFlag([System.IO.FileAttributes]::Compressed) -expected $false

    # enumerate tests
    $subdir1 = $dir.CreateSubDirectory("subdir-1")
    $subdir2 = $dir.CreateSubDirectory("subdir-2")
    $subdir1.CreateSubDirectory("subdir3") > $null
    $file = [Ansible.IO.File]::CreateText("$directory_path\file.txt")
    try {
        $file.WriteLine("abc")
    } finally {
        $file.Dispose()
    }
    $file = [Ansible.IO.File]::CreateText("$directory_path\anotherfile.txt")
    try {
        $file.WriteLine("abc")
    } finally {
        $file.Dispose()
    }
    $file = [Ansible.IO.File]::CreateText("$directory_path\subdir-1\file-1.txt")
    try {
        $file.WriteLine("abc")
    } finally {
        $file.Dispose()
    }
    $file = [Ansible.IO.File]::CreateText("$directory_path\subdir-2\file-2.txt")
    try {
        $file.WriteLine("abc")
    } finally {
        $file.Dispose()
    }
    $file = [Ansible.IO.File]::CreateText("$directory_path\subdir-1\subdir3\file-3.txt")
    try {
        $file.WriteLine("abc")
    } finally {
        $file.Dispose()
    }

    $dir_dirs = $dir.EnumerateDirectories()
    foreach ($dir_name in $dir_dirs) {
        Assert-Equals -actual $dir_name.GetType().FullName -expected "Ansible.IO.DirectoryInfo"
        Assert-Equals -actual ($dir_name.Name -in (
            "subdir",
            "subdir-1",
            "subdir-2")) -expected $true
    }
    $dir_dirs = $dir.EnumerateDirectories("subdir-?")
    foreach ($dir_name in $dir_dirs) {
        Assert-Equals -actual $dir_name.GetType().FullName -expected "Ansible.IO.DirectoryInfo"
        Assert-Equals -actual ($dir_name.Name -in (
            "subdir-1",
            "subdir-2")) -expected $true
    }
    $dir_dirs = $dir.EnumerateDirectories("*", [System.IO.SearchOption]::AllDirectories)
    foreach ($dir_name in $dir_dirs) {
        Assert-Equals -actual $dir_name.GetType().FullName -expected "Ansible.IO.DirectoryInfo"
        Assert-Equals -actual ($dir_name.Name -in (
            "subdir",
            "subdir-1",
            "subdir-2",
            "subdir3")) -expected $true
    }

    $dir_dirs = $dir.GetDirectories()
    foreach ($dir_name in $dir_dirs) {
        Assert-Equals -actual $dir_name.GetType().FullName -expected "Ansible.IO.DirectoryInfo"
        Assert-Equals -actual ($dir_name.Name -in (
            "subdir",
            "subdir-1",
            "subdir-2")) -expected $true
    }
    $dir_dirs = $dir.GetDirectories("subdir-?")
    foreach ($dir_name in $dir_dirs) {
        Assert-Equals -actual $dir_name.GetType().FullName -expected "Ansible.IO.DirectoryInfo"
        Assert-Equals -actual ($dir_name.Name -in (
            "subdir-1",
            "subdir-2")) -expected $true
    }
    $dir_dirs = $dir.GetDirectories("*", [System.IO.SearchOption]::AllDirectories)
    foreach ($dir_name in $dir_dirs) {
        Assert-Equals -actual $dir_name.GetType().FullName -expected "Ansible.IO.DirectoryInfo"
        Assert-Equals -actual ($dir_name.Name -in (
            "subdir",
            "subdir-1",
            "subdir-2",
            "subdir3")) -expected $true
    }

    $dir_files = $dir.EnumerateFiles()
    foreach ($dir_file in $dir_files) {
        Assert-Equals -actual $dir_file.GetType().FullName -expected "Ansible.IO.FileInfo"
        Assert-Equals -actual ($dir_file.Name -in (
            "file.txt",
            "anotherfile.txt")) -expected $true
    }
    $dir_files = $dir.EnumerateFiles("anotherfile*")
    foreach ($dir_file in $dir_files) {
        Assert-Equals -actual $dir_file.GetType().FullName -expected "Ansible.IO.FileInfo"
        Assert-Equals -actual ($dir_file.Name -in ("anotherfile.txt")) -expected $true
    }
    $dir_files = $dir.EnumerateFiles("*", [System.IO.SearchOption]::AllDirectories)
    foreach ($dir_file in $dir_files) {
        Assert-Equals -actual $dir_file.GetType().FullName -expected "Ansible.IO.FileInfo"
        Assert-Equals -actual ($dir_file.Name -in (
            "file.txt",
            "anotherfile.txt",
            "file-1.txt",
            "file-2.txt",
            "file-3.txt")) -expected $true
    }

    $dir_files = $dir.GetFiles()
    foreach ($dir_file in $dir_files) {
        Assert-Equals -actual $dir_file.GetType().FullName -expected "Ansible.IO.FileInfo"
        Assert-Equals -actual ($dir_file.Name -in (
            "file.txt",
            "anotherfile.txt")) -expected $true
    }
    $dir_files = $dir.GetFiles("anotherfile*")
    foreach ($dir_file in $dir_files) {
        Assert-Equals -actual $dir_file.GetType().FullName -expected "Ansible.IO.FileInfo"
        Assert-Equals -actual ($dir_file.Name -in ("anotherfile.txt")) -expected $true
    }
    $dir_files = $dir.GetFiles("*", [System.IO.SearchOption]::AllDirectories)
    foreach ($dir_file in $dir_files) {
        Assert-Equals -actual $dir_file.GetType().FullName -expected "Ansible.IO.FileInfo"
        Assert-Equals -actual ($dir_file.Name -in (
            "file.txt",
            "anotherfile.txt",
            "file-1.txt",
            "file-2.txt",
            "file-3.txt")) -expected $true
    }

    $dir_entries = $dir.EnumerateFileSystemInfos()
    foreach ($dir_entry in $dir_entries) {
        Assert-Equals -actual ($dir_entry.GetType().FullName -in @("Ansible.IO.FileInfo", "Ansible.IO.DirectoryInfo")) -expected $true
        Assert-Equals -actual ($dir_entry.Name -in (
            "file.txt",
            "anotherfile.txt",
            "subdir",
            "subdir-1",
            "subdir-2")) -expected $true
    }
    $dir_entries = $dir.EnumerateFileSystemInfos("anotherfile*")
    foreach ($dir_entry in $dir_entries) {
        Assert-Equals -actual ($dir_entry.GetType().FullName -in @("Ansible.IO.FileInfo", "Ansible.IO.DirectoryInfo")) -expected $true
        Assert-Equals -actual ($dir_entry.Name -in ("anotherfile.txt")) -expected $true
    }
    $dir_entries = $dir.EnumerateFileSystemInfos("*", [System.IO.SearchOption]::AllDirectories)
    foreach ($dir_entry in $dir_entries) {
        Assert-Equals -actual ($dir_entry.GetType().FullName -in @("Ansible.IO.FileInfo", "Ansible.IO.DirectoryInfo")) -expected $true
        Assert-Equals -actual ($dir_entry.Name -in (
            "file.txt",
            "anotherfile.txt",
            "file-1.txt",
            "file-2.txt",
            "file-3.txt",
            "subdir",
            "subdir-1",
            "subdir-2",
            "subdir3")) -expected $true
    }

    $dir_entries = $dir.GetFileSystemInfos()
    foreach ($dir_entry in $dir_entries) {
        Assert-Equals -actual ($dir_entry.GetType().FullName -in @("Ansible.IO.FileInfo", "Ansible.IO.DirectoryInfo")) -expected $true
        Assert-Equals -actual ($dir_entry.Name -in (
            "file.txt",
            "anotherfile.txt",
            "subdir",
            "subdir-1",
            "subdir-2")) -expected $true
    }
    $dir_entries = $dir.GetFileSystemInfos("anotherfile*")
    foreach ($dir_entry in $dir_entries) {
        Assert-Equals -actual ($dir_entry.GetType().FullName -in @("Ansible.IO.FileInfo", "Ansible.IO.DirectoryInfo")) -expected $true
        Assert-Equals -actual ($dir_entry.Name -in ("anotherfile.txt")) -expected $true
    }
    $dir_entries = $dir.GetFileSystemInfos("*", [System.IO.SearchOption]::AllDirectories)
    foreach ($dir_entry in $dir_entries) {
        Assert-Equals -actual ($dir_entry.GetType().FullName -in @("Ansible.IO.FileInfo", "Ansible.IO.DirectoryInfo")) -expected $true
        Assert-Equals -actual ($dir_entry.Name -in (
            "file.txt",
            "anotherfile.txt",
            "file-1.txt",
            "file-2.txt",
            "file-3.txt",
            "subdir",
            "subdir-1",
            "subdir-2",
            "subdir3")) -expected $true
    }
    
    # move tests
    $subdir2.MoveTo("$directory_path\subdir-move")
    Assert-Equals -actual ([Ansible.IO.Directory]::Exists("$directory_path\subdir-move")) -expected $true
    Assert-Equals -actual ([Ansible.IO.File]::Exists("$directory_path\subdir-move\file-2.txt")) -expected $true

    # delete tests
    $failed = $false
    try {
        # fail to delete a directory that has contents
        $subdir1.Delete()
    } catch {
        $failed = $true
        Assert-Equals -actual $_.Exception.Message -expected "Exception calling `"Delete`" with `"0`" argument(s): `"The directory is not empty : '$($subdir1.FullName)'`""
    }
    Assert-Equals -actual $failed -expected $true
    $subdir1.Delete($true)
    Assert-Equals -actual ([Ansible.IO.Directory]::Exists("$directory_path\subdir-1")) -expected $false
    $subdir = $dir.CreateSubDirectory("subdir")
    $subdir.Delete()
    Assert-Equals -actual ([Ansible.IO.Directory]::Exists("$directory_path\subdir")) -expected $false

    # ACL tests
    $current_sid = ([System.Security.Principal.WindowsIdentity]::GetCurrent()).User
    $everyone_sid = New-Object -TypeName System.Security.Principal.SecurityIdentifier -ArgumentList "S-1-1-0"

    $dir_sec = New-Object -TypeName System.Security.AccessControl.DirectorySecurity
    $read_rule = New-Object -TypeName System.Security.AccessControl.FileSystemAccessRule -ArgumentList $everyone_sid, "FullControl", "Allow"
    $dir_sec.SetAccessRule($read_rule)
    $dir_sec.SetOwner($current_sid)
    $dir_sec.SetGroup($everyone_sid)
    $acl_dir = $dir.CreateSubDirectory("acl-dir", $dir_sec)

    $actual_acl = $acl_dir.GetAccessControl()
    $access_rules = $actual_acl.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier])

    $acl_owner = $actual_acl.GetOwner([System.Security.Principal.SecurityIdentifier])
    $acl_group = $actual_acl.GetGroup([System.Security.Principal.SecurityIdentifier])
    Assert-Equals -actual $acl_owner -expected $current_sid
    Assert-Equals -actual $acl_group -expected $everyone_sid

    # only admins can set audit rules, we test for failure if not running as admin
    $audit_rule = New-Object -TypeName System.Security.AccessControl.FileSystemAuditRule -ArgumentList $everyone_sid, "Read", "Success"
    $dir_sec = $acl_dir.GetAccessControl()
    $dir_sec.SetAuditRule($audit_rule)
    if ([bool](([System.Security.Principal.WindowsIdentity]::GetCurrent()).groups -match "S-1-5-32-544")) {
        $acl_dir.SetAccessControl($dir_sec)
        $actual_acl = $acl_dir.GetAccessControl([System.Security.AccessControl.AccessControlSections]::All)
        $audit_rules = $actual_acl.GetAuditRules($true, $true, [System.Security.Principal.SecurityIdentifier])
        Assert-Equals -actual $audit_rules.Count -expected 1
        Assert-Equals -actual $audit_rules[0].FileSystemRights.ToString() -expected "Read"
        Assert-Equals -actual $audit_rules[0].AuditFlags.ToString() -expected "Success"
        Assert-Equals -actual $audit_rules[0].IsInherited -expected $false
        Assert-Equals -actual $audit_rules[0].IdentityReference -expected $everyone_sid
    } else {
        $failed = $false
        try {
            $acl_dir.SetAccessControl($dir_sec)
        } catch {
            $failed = $true
            Assert-Equals -actual $_.Exception.Message -expected "Exception calling `"SetAccessControl`" with `"1`" argument(s): `"Failed to enable privilege(s) SeSecurityPrivilege: AdjustTokenPrivileges() failed (Not all privileges or groups referenced are assigned to the caller, Win32ErrorCode 1300)`""
        }
        Assert-Equals -actual $failed -expected $true
    }

    # clear for the Ansible.IO.Directory tests
    [Ansible.IO.Directory]::Delete($directory_path, $true)

    ### Directory Tests ###
    $dir = [Ansible.IO.Directory]::CreateDirectory($directory_path)
    Assert-Equals -actual ($dir -is [Ansible.IO.DirectoryInfo]) -expected $true
    Assert-Equals -actual ([Ansible.IO.Directory]::Exists($directory_path)) -expected $true

    # delete directory with the ReadOnly attribute set
    $dir.Attributes = [System.IO.FileAttributes]"Directory, ReadOnly"
    [Ansible.IO.Directory]::Delete($directory_path)
    Assert-Equals -actual ([Ansible.IO.Directory]::Exists($directory_path)) -expected $false

    $dir = [Ansible.IO.Directory]::CreateDirectory($directory_path)

    # ACL Tests
    $acl = New-Object -TypeName System.Security.AccessControl.DirectorySecurity
    $read_rule = New-Object -TypeName System.Security.AccessControl.FileSystemAccessRule -ArgumentList $everyone_sid, "FullControl", "Allow"
    $acl.SetAccessRule($read_rule)
    $acl.SetOwner($current_sid)
    $acl.SetGroup($everyone_sid)
    $acl_dir = [Ansible.IO.Directory]::CreateDirectory("$directory_path\acl-dir", $acl)
    Assert-Equals -actual ($acl_dir -is [Ansible.IO.DirectoryInfo]) -expected $true

    $acl = [Ansible.IO.Directory]::GetAccessControl("$directory_path\acl-dir")
    $access_rules = $acl.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier])
    $owner = $acl.GetOwner([System.Security.Principal.SecurityIdentifier])
    $group = $acl.GetGroup([System.Security.Principal.SecurityIdentifier])
    Assert-Equals -actual $access_rules.Count -expected 1
    Assert-Equals -actual $access_rules[0].IdentityReference -expected $everyone_sid
    Assert-Equals -actual $access_rules[0].IsInherited -expected $false
    Assert-Equals -actual $owner -expected $current_sid
    Assert-Equals -actual $group -expected $everyone_sid

    # only admins can set this
    if ([bool](([System.Security.Principal.WindowsIdentity]::GetCurrent()).groups -match "S-1-5-32-544")) {
        $acl = [Ansible.IO.Directory]::GetAccessControl("$directory_path\acl-dir")
        $admin_sid = New-Object -TypeName System.Security.Principal.SecurityIdentifier -ArgumentList "S-1-5-32-544"
        $acl.SetOwner($admin_sid)
        [Ansible.IO.Directory]::SetAccessControl("$directory_path\acl-dir", $acl)

        $acl_owner = [Ansible.IO.Directory]::GetAccessControl("$directory_path\acl-dir", [System.Security.AccessControl.AccessControlSections]::Owner)
        $owner = $acl_owner.GetOwner([System.Security.Principal.SecurityIdentifier])
        $group = $acl_owner.GetGroup([System.Security.Principal.SecurityIdentifier])
        Assert-Equals -actual $owner -expected $admin_sid
        Assert-Equals -actual $group -expected $null
    }

    [Ansible.IO.Directory]::CreateDirectory("$directory_path\subdir-1") > $null
    [Ansible.IO.Directory]::CreateDirectory("$directory_path\subdir-1\subdir-3") > $null
    [Ansible.IO.Directory]::CreateDirectory("$directory_path\subdir-2") > $null
    $file = [Ansible.IO.File]::CreateText("$directory_path\file.txt")
    try {
        $file.WriteLine("abc")
    } finally {
        $file.Dispose()
    }
    $file = [Ansible.IO.File]::CreateText("$directory_path\anotherfile.txt")
    try {
        $file.WriteLine("abc")
    } finally {
        $file.Dispose()
    }
    $file = [Ansible.IO.File]::CreateText("$directory_path\subdir-1\file-1.txt")
    try {
        $file.WriteLine("abc")
    } finally {
        $file.Dispose()
    }
    $file = [Ansible.IO.File]::CreateText("$directory_path\subdir-1\subdir-3\file-3.txt")
    try {
        $file.WriteLine("abc")
    } finally {
        $file.Dispose()
    }
    $file = [Ansible.IO.File]::CreateText("$directory_path\subdir-2\file-2.txt")
    try {
        $file.WriteLine("abc")
    } finally {
        $file.Dispose()
    }

    $dir_dirs = [Ansible.IO.Directory]::EnumerateDirectories($directory_path)
    foreach ($dir_name in $dir_dirs) {
        Assert-Equals -actual $dir_name.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_name -in (
            "$directory_path\subdir-1",
            "$directory_path\subdir-2",
            "$directory_path\acl-dir")) -expected $true
    }
    $dir_dirs = [Ansible.IO.Directory]::EnumerateDirectories($directory_path, "acl-*")
    foreach ($dir_name in $dir_dirs) {
        Assert-Equals -actual $dir_name.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_name -in ("$directory_path\acl-dir")) -expected $true
    }
    $dir_dirs = [Ansible.IO.Directory]::EnumerateDirectories($directory_path, "*", [System.IO.SearchOption]::AllDirectories)
    foreach ($dir_name in $dir_dirs) {
        Assert-Equals -actual $dir_name.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_name -in (
            "$directory_path\subdir-1",
            "$directory_path\subdir-1\subdir-3",
            "$directory_path\subdir-2",
            "$directory_path\acl-dir")) -expected $true
    }

    $dir_dirs = [Ansible.IO.Directory]::GetDirectories($directory_path)
    Assert-Equals -actual ($dir_dirs.Count) -expected 3
    foreach ($dir_name in $dir_dirs) {
        Assert-Equals -actual $dir_name.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_name -in (
            "$directory_path\subdir-1",
            "$directory_path\subdir-2",
            "$directory_path\acl-dir")) -expected $true
    }
    $dir_dirs = [Ansible.IO.Directory]::GetDirectories($directory_path, "acl-*")
    Assert-Equals -actual ($dir_dirs.Count) -expected 1
    foreach ($dir_name in $dir_dirs) {
        Assert-Equals -actual $dir_name.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_name -in ("$directory_path\acl-dir")) -expected $true
    }
    $dir_dirs = [Ansible.IO.Directory]::GetDirectories($directory_path, "*", [System.IO.SearchOption]::AllDirectories)
    Assert-Equals -actual ($dir_dirs.Count) -expected 4
    foreach ($dir_name in $dir_dirs) {
        Assert-Equals -actual $dir_name.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_name -in (
            "$directory_path\subdir-1",
            "$directory_path\subdir-1\subdir-3",
            "$directory_path\subdir-2",
            "$directory_path\acl-dir")) -expected $true
    }

    $dir_files = [Ansible.IO.Directory]::EnumerateFiles($directory_path)
    foreach ($dir_file in $dir_files) {
        Assert-Equals -actual $dir_file.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_file -in (
            "$directory_path\file.txt",
            "$directory_path\anotherfile.txt")) -expected $true
    }
    $dir_files = [Ansible.IO.Directory]::EnumerateFiles($directory_path, "another*")
    foreach ($dir_file in $dir_files) {
        Assert-Equals -actual $dir_file.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_file -in ("$directory_path\anotherfile.txt")) -expected $true
    }
    $dir_files = [Ansible.IO.Directory]::EnumerateFiles($directory_path, "*", [System.IO.SearchOption]::AllDirectories)
    foreach ($dir_file in $dir_files) {
        Assert-Equals -actual $dir_file.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_file -in (
            "$directory_path\file.txt",
            "$directory_path\anotherfile.txt",
            "$directory_path\subdir-1\file-1.txt",
            "$directory_path\subdir-1\subdir-3\file-3.txt",
            "$directory_path\subdir-2\file-2.txt")) -expected $true
    }

    $dir_files = [Ansible.IO.Directory]::GetFiles($directory_path)
    Assert-Equals -actual ($dir_files.Count) -expected 2
    foreach ($dir_file in $dir_files) {
        Assert-Equals -actual $dir_file.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_file -in (
            "$directory_path\file.txt",
            "$directory_path\anotherfile.txt")) -expected $true
    }
    $dir_files = [Ansible.IO.Directory]::GetFiles($directory_path, "another*")
    Assert-Equals -actual ($dir_files.Count) -expected 1
    foreach ($dir_file in $dir_files) {
        Assert-Equals -actual $dir_file.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_file -in ("$directory_path\anotherfile.txt")) -expected $true
    }
    $dir_files = [Ansible.IO.Directory]::GetFiles($directory_path, "*", [System.IO.SearchOption]::AllDirectories)
    Assert-Equals -actual ($dir_files.Count) -expected 5
    foreach ($dir_file in $dir_files) {
        Assert-Equals -actual $dir_file.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_file -in (
            "$directory_path\file.txt",
            "$directory_path\anotherfile.txt",
            "$directory_path\subdir-1\file-1.txt",
            "$directory_path\subdir-1\subdir-3\file-3.txt",
            "$directory_path\subdir-2\file-2.txt")) -expected $true
    }

    $dir_entries = [Ansible.IO.Directory]::EnumerateFileSystemEntries($directory_path)
    foreach ($dir_entry in $dir_entries) {
        Assert-Equals -actual $dir_entry.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_entry -in (
            "$directory_path\subdir-1",
            "$directory_path\subdir-2",
            "$directory_path\acl-dir",
            "$directory_path\file.txt",
            "$directory_path\anotherfile.txt")) -expected $true
    }
    $dir_entries = [Ansible.IO.Directory]::EnumerateFileSystemEntries($directory_path, "another*")
    foreach ($dir_entry in $dir_entries) {
        Assert-Equals -actual $dir_entry.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_entry -in ("$directory_path\anotherfile.txt")) -expected $true
    }
    $dir_entries = [Ansible.IO.Directory]::EnumerateFileSystemEntries($directory_path, "*", [System.IO.SearchOption]::AllDirectories)
    foreach ($dir_entry in $dir_entries) {
        Assert-Equals -actual $dir_entry.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_entry -in (
            "$directory_path\subdir-1",
            "$directory_path\subdir-1\subdir-3",
            "$directory_path\subdir-2",
            "$directory_path\acl-dir",
            "$directory_path\file.txt",
            "$directory_path\anotherfile.txt",
            "$directory_path\subdir-1\file-1.txt",
            "$directory_path\subdir-1\subdir-3\file-3.txt",
            "$directory_path\subdir-2\file-2.txt")) -expected $true
    }
    
    $dir_entries = [Ansible.IO.Directory]::GetFileSystemInfos($directory_path)
    Assert-Equals -actual ($dir_entries.Count) -expected 5
    foreach ($dir_entry in $dir_entries) {
        Assert-Equals -actual $dir_entry.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_entry -in (
            "$directory_path\subdir-1",
            "$directory_path\subdir-2",
            "$directory_path\acl-dir",
            "$directory_path\file.txt",
            "$directory_path\anotherfile.txt")) -expected $true
    }
    $dir_entries = [Ansible.IO.Directory]::GetFileSystemInfos($directory_path, "another*")
    Assert-Equals -actual ($dir_entries.Count) -expected 1
    foreach ($dir_entry in $dir_entries) {
        Assert-Equals -actual $dir_entry.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_entry -in ("$directory_path\anotherfile.txt")) -expected $true
    }
    $dir_entries = [Ansible.IO.Directory]::GetFileSystemInfos($directory_path, "*", [System.IO.SearchOption]::AllDirectories)
    Assert-Equals -actual ($dir_entries.Count) -expected 9
    foreach ($dir_entry in $dir_entries) {
        Assert-Equals -actual $dir_entry.GetType().FullName -expected "System.String"
        Assert-Equals -actual ($dir_entry -in (
            "$directory_path\subdir-1",
            "$directory_path\subdir-1\subdir-3",
            "$directory_path\subdir-2",
            "$directory_path\acl-dir",
            "$directory_path\file.txt",
            "$directory_path\anotherfile.txt",
            "$directory_path\subdir-1\file-1.txt",
            "$directory_path\subdir-1\subdir-3\file-3.txt",
            "$directory_path\subdir-2\file-2.txt")) -expected $true
    }

    [Ansible.IO.Directory]::Move("$directory_path\subdir-1", "$directory_path\moved-dir")
    Assert-Equals -actual ([Ansible.IO.Directory]::Exists("$directory_path\subdir-1")) -expected $false
    Assert-Equals -actual ([Ansible.IO.Directory]::Exists("$directory_path\moved-dir")) -expected $true
    
    $parent_dir = [Ansible.IO.Directory]::GetParent("$directory_path\moved-dir")
    Assert-Equals -actual $parent_dir.GetType().FullName -expected "Ansible.IO.DirectoryInfo"
    Assert-Equals -actual $parent_dir.Fullname -expected $directory_path

    [Ansible.IO.Directory]::Delete("$directory_path\acl-dir")
    Assert-Equals -actual ([Ansible.IO.Directory]::Exists("$directory_path\acl-dir")) -expected $false
    $failed = $false
    try {
        [Ansible.IO.Directory]::Delete("$directory_path\moved-dir")
    } catch {
        $failed = $true
        Assert-Equals -actual $_.Exception.Message -expected "Exception calling `"Delete`" with `"1`" argument(s): `"The directory is not empty : '$directory_path\moved-dir'`""
    }
    Assert-Equals -actual $failed -expected $true
    Assert-Equals -actual ([Ansible.IO.Directory]::Exists("$directory_path\moved-dir")) -expected $true
    Assert-Equals -actual ([Ansible.IO.Directory]::Exists("$directory_path\moved-dir\subdir-3")) -expected $true
    Assert-Equals -actual ([Ansible.IO.File]::Exists("$directory_path\moved-dir\file-1.txt")) -expected $true
    Assert-Equals -actual ([Ansible.IO.File]::Exists("$directory_path\moved-dir\subdir-3\file-3.txt")) -expected $true

    [Ansible.IO.Directory]::Delete("$directory_path\moved-dir", $true)
    Assert-Equals -actual ([Ansible.IO.Directory]::Exists("$directory_path\moved-dir")) -expected $false

    $current_time = (Get-Date).ToFileTimeUtc()
    [Ansible.IO.Directory]::CreateDirectory("$directory_path\date") > $null

    $creation_time = [Ansible.IO.Directory]::GetCreationTimeUtc("$directory_path\date")
    Assert-Equals -actual $creation_time.GetType().FullName -expected "System.DateTime"
    Assert-Equals -actual ($creation_time.ToFileTimeUtc() -ge $current_time) -expected $true

    $lastaccess_time = [Ansible.IO.Directory]::GetLastAccessTimeUtc("$directory_path\date")
    Assert-Equals -actual $lastaccess_time.GetType().FullName -expected "System.DateTime"
    Assert-Equals -actual ($lastaccess_time.ToFileTimeUtc() -ge $current_time) -expected $true

    $lastwrite_time = [Ansible.IO.Directory]::GetLastWriteTimeUtc("$directory_path\date")
    Assert-Equals -actual $lastwrite_time.GetType().FullName -expected "System.DateTime"
    Assert-Equals -actual ($lastwrite_time.ToFileTimeUtc() -ge $current_time) -expected $true

    [Ansible.IO.Directory]::SetCreationTimeUtc("$directory_path\date", $new_date)
    $creation_time = [Ansible.IO.Directory]::GetCreationTimeUtc("$directory_path\date")
    Assert-Equals -actual $creation_time -expected $new_date

    [Ansible.IO.Directory]::SetLastAccessTimeUtc("$directory_path\date", $new_date)
    $lastaccess_time = [Ansible.IO.Directory]::GetLastAccessTimeUtc("$directory_path\date")
    Assert-Equals -actual $lastaccess_time -expected $new_date

    [Ansible.IO.Directory]::SetLastWriteTimeUtc("$directory_path\date", $new_date)
    $lastwrite_time = [Ansible.IO.Directory]::GetLastWriteTimeUtc("$directory_path\date")
    Assert-Equals -actual $lastwrite_time -expected $new_date
}

Function Test-IOPath($root_path) {
    $long_path = "{0}\{0}\{0}\{0}\{0}\{0}\{0}\dir" -f ("a" * 250)
    ### A lot of these expectations were derived by running System.IO.Path on 2016 which is more lenient with most long paths ###

    # ChangeExtension
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("C:\path\dir", "")) -expected "C:\path\dir."
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("C:\path\dir", "txt")) -expected "C:\path\dir.txt"
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("C:/path/dir", "")) -expected "C:/path/dir."
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("C:/path/dir", "txt")) -expected "C:/path/dir.txt"
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("\\?\C:\path\dir", "")) -expected "\\?\C:\path\dir."
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("\\?\C:\path\dir", "txt")) -expected "\\?\C:\path\dir.txt"
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("\\?\C:\path\$long_path\dir", "")) -expected "\\?\C:\path\$long_path\dir."
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("\\?\C:\path\$long_path\dir", "txt")) -expected "\\?\C:\path\$long_path\dir.txt"
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("\\127.0.0.1\c$\path\dir", "")) -expected "\\127.0.0.1\c$\path\dir."
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("\\127.0.0.1\c$\path\dir", "txt")) -expected "\\127.0.0.1\c$\path\dir.txt"
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("\\?\UNC\127.0.0.1\c$\path\$long_path\dir", "")) -expected "\\?\UNC\127.0.0.1\c$\path\$long_path\dir."
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("\\?\UNC\127.0.0.1\c$\path\$long_path\dir", "txt")) -expected "\\?\UNC\127.0.0.1\c$\path\$long_path\dir.txt"

    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("C:\path\dir\file.txt", "")) -expected "C:\path\dir\file."
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("C:\path\dir\file.txt", "txt2")) -expected "C:\path\dir\file.txt2"
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("C:/path/dir/file.txt", "")) -expected "C:/path/dir/file."
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("C:/path/dir/file.txt", "txt2")) -expected "C:/path/dir/file.txt2"
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("\\?\C:\path\dir\file.txt", "")) -expected "\\?\C:\path\dir\file."
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("\\?\C:\path\dir\file.txt", "txt2")) -expected "\\?\C:\path\dir\file.txt2"
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("\\?\C:\path\$long_path\dir\file.txt", "")) -expected "\\?\C:\path\$long_path\dir\file."
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("\\?\C:\path\$long_path\dir\file.txt", "txt2")) -expected "\\?\C:\path\$long_path\dir\file.txt2"
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("\\127.0.0.1\c$\path\dir\file.txt", "")) -expected "\\127.0.0.1\c$\path\dir\file."
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("\\127.0.0.1\c$\path\dir\file.txt", "txt2")) -expected "\\127.0.0.1\c$\path\dir\file.txt2"
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("\\?\UNC\127.0.0.1\c$\path\$long_path\dir\file.txt", "")) -expected "\\?\UNC\127.0.0.1\c$\path\$long_path\dir\file."
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("\\?\UNC\127.0.0.1\c$\path\$long_path\dir\file.txt", "txt2")) -expected "\\?\UNC\127.0.0.1\c$\path\$long_path\dir\file.txt2"

    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("C:\path\dir\file.", "")) -expected "C:\path\dir\file."
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("C:\path\dir\file.", "txt")) -expected "C:\path\dir\file.txt"
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("C:/path/dir/file.", "")) -expected "C:/path/dir/file."
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("C:/path/dir/file.", "txt")) -expected "C:/path/dir/file.txt"
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("\\?\C:\path\dir\file.", "")) -expected "\\?\C:\path\dir\file."
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("\\?\C:\path\dir\file.", "txt")) -expected "\\?\C:\path\dir\file.txt"
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("\\?\C:\path\$long_path\dir\file.", "")) -expected "\\?\C:\path\$long_path\dir\file."
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("\\?\C:\path\$long_path\dir\file.", "txt")) -expected "\\?\C:\path\$long_path\dir\file.txt"
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("\\127.0.0.1\c$\path\dir\file.", "")) -expected "\\127.0.0.1\c$\path\dir\file."
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("\\127.0.0.1\c$\path\dir\file.", "txt")) -expected "\\127.0.0.1\c$\path\dir\file.txt"
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("\\?\UNC\127.0.0.1\c$\path\$long_path\dir\file.", "")) -expected "\\?\UNC\127.0.0.1\c$\path\$long_path\dir\file."
    Assert-Equals -actual ([Ansible.IO.Path]::ChangeExtension("\\?\UNC\127.0.0.1\c$\path\$long_path\dir\file.", "txt")) -expected "\\?\UNC\127.0.0.1\c$\path\$long_path\dir\file.txt"

    # Combine
    Assert-Equals -actual ([Ansible.IO.Path]::Combine("C:\path\dir", "dir", "file.txt")) -expected "C:\path\dir\dir\file.txt"
    Assert-Equals -actual ([Ansible.IO.Path]::Combine("C:/path/dir", "dir", "file.txt")) -expected "C:/path/dir\dir\file.txt"
    Assert-Equals -actual ([Ansible.IO.Path]::Combine("\\?\C:\path\dir", "dir", "file.txt")) -expected "\\?\C:\path\dir\dir\file.txt"
    Assert-Equals -actual ([Ansible.IO.Path]::Combine("\\?\C:\path\$long_path\dir", "dir", "file.txt")) -expected "\\?\C:\path\$long_path\dir\dir\file.txt"
    Assert-Equals -actual ([Ansible.IO.Path]::Combine("\\127.0.0.1\c$\path\dir", "dir", "file.txt")) -expected "\\127.0.0.1\c$\path\dir\dir\file.txt"
    Assert-Equals -actual ([Ansible.IO.Path]::Combine("\\?\UNC\127.0.0.1\c$\path\$long_path\dir", "dir", "file.txt")) -expected "\\?\UNC\127.0.0.1\c$\path\$long_path\dir\dir\file.txt"

    # GetDirectoryName - this is manually done so lots of scrutiny needed here
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("C:\path\dir")) -expected "C:\path"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("C:/path/dir")) -expected "C:\path"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?\C:\path\dir")) -expected "\\?\C:\path"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?\C:\path\$long_path\dir")) -expected "\\?\C:\path\$long_path"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\127.0.0.1\c$\path\dir")) -expected "\\127.0.0.1\c$\path"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?\UNC\127.0.0.1\c$\path\$long_path\dir")) -expected "\\?\UNC\127.0.0.1\c$\path\$long_path"

    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("C:\path\dir\file.txt")) -expected "C:\path\dir"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("C:/path/dir/file.txt")) -expected "C:\path\dir"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?\C:\path\dir\file.txt")) -expected "\\?\C:\path\dir"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?\C:\path\$long_path\dir\file.txt")) -expected "\\?\C:\path\$long_path\dir"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\127.0.0.1\c$\path\dir\file.txt")) -expected "\\127.0.0.1\c$\path\dir"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?\UNC\127.0.0.1\c$\path\$long_path\dir\file.txt")) -expected "\\?\UNC\127.0.0.1\c$\path\$long_path\dir"

    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("C:\path\dir\file.")) -expected "C:\path\dir"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("C:/path/dir/file.")) -expected "C:\path\dir"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?\C:\path\dir\file.")) -expected "\\?\C:\path\dir"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?\C:\path\$long_path\dir\file.")) -expected "\\?\C:\path\$long_path\dir"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\127.0.0.1\c$\path\dir\file.")) -expected "\\127.0.0.1\c$\path\dir"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?\UNC\127.0.0.1\c$\path\$long_path\dir\file.")) -expected "\\?\UNC\127.0.0.1\c$\path\$long_path\dir"

    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName($null)) -expected $null
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("")) -expected $null
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("C")) -expected ""
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("C:")) -expected $null
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("C:\")) -expected $null
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("C:/")) -expected $null
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("C:\a")) -expected "C:\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("C:\a\")) -expected "C:\a"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("C:\a\b")) -expected "C:\a"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("C:/a")) -expected "C:\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?")) -expected $null
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?\C:")) -expected $null
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?\C:\")) -expected $null
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?\C:/")) -expected $null
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?\C:\a")) -expected "\\?\C:\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?\C:/a")) -expected "\\?\C:/"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?\C:/a/")) -expected "\\?\C:/a"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?\C:/a/b")) -expected "\\?\C:/a"

    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\")) -expected $null
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\server")) -expected $null
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\server\")) -expected $null
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\server\share")) -expected $null
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\server\share\")) -expected "\\server\share"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\server\share\path")) -expected "\\server\share"

    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("//")) -expected $null
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("//server")) -expected $null
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("//server/")) -expected $null
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("//server/share")) -expected $null
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("//server/share/")) -expected "\\server\share"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("//server/share/path")) -expected "\\server\share"

    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?\UNC\")) -expected $null
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?\UNC\server")) -expected $null
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?\UNC\server\")) -expected $null
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?\UNC\server\share")) -expected $null
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?\UNC\server\share\")) -expected "\\?\UNC\server\share"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?\UNC\server\share\path")) -expected "\\?\UNC\server\share"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?\UNC\server/share\path")) -expected "\\?\UNC\server/share"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?\UNC\server/share\path\")) -expected "\\?\UNC\server/share\path"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?\UNC\server/share\path/")) -expected "\\?\UNC\server/share\path"

    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?/UNC/server/share/")) -expected "\\?\UNC\server\share"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?/UNC/server/share/path")) -expected "\\?\UNC\server\share"

    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?\UNC/")) -expected "\\?\UNC"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?\UNC/server")) -expected "\\?\UNC"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?\UNC/server/")) -expected "\\?\UNC/server"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?\UNC/server/share")) -expected "\\?\UNC/server"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?\UNC/server/share/")) -expected "\\?\UNC/server/share"
    Assert-Equals -actual ([Ansible.IO.Path]::GetDirectoryName("\\?\UNC/server/share/path")) -expected "\\?\UNC/server/share"

    # GetExtension
    Assert-Equals -actual ([Ansible.IO.Path]::GetExtension("C:\path\dir")) -expected ""
    Assert-Equals -actual ([Ansible.IO.Path]::GetExtension("C:/path/dir")) -expected ""
    Assert-Equals -actual ([Ansible.IO.Path]::GetExtension("\\?\C:\path\dir")) -expected ""
    Assert-Equals -actual ([Ansible.IO.Path]::GetExtension("\\?\C:\path\$long_path\dir")) -expected ""
    Assert-Equals -actual ([Ansible.IO.Path]::GetExtension("\\127.0.0.1\c$\path\dir")) -expected ""
    Assert-Equals -actual ([Ansible.IO.Path]::GetExtension("\\?\UNC\127.0.0.1\c$\path\$long_path\dir")) -expected ""

    Assert-Equals -actual ([Ansible.IO.Path]::GetExtension("C:\path\dir\file.txt")) -expected ".txt"
    Assert-Equals -actual ([Ansible.IO.Path]::GetExtension("C:/path/dir/file.txt")) -expected ".txt"
    Assert-Equals -actual ([Ansible.IO.Path]::GetExtension("\\?\C:\path\dir\file.txt")) -expected ".txt"
    Assert-Equals -actual ([Ansible.IO.Path]::GetExtension("\\?\C:\path\$long_path\dir\file.txt")) -expected ".txt"
    Assert-Equals -actual ([Ansible.IO.Path]::GetExtension("\\127.0.0.1\c$\path\dir\file.txt")) -expected ".txt"
    Assert-Equals -actual ([Ansible.IO.Path]::GetExtension("\\?\UNC\127.0.0.1\c$\path\$long_path\dir\file.txt")) -expected ".txt"

    Assert-Equals -actual ([Ansible.IO.Path]::GetExtension("C:\path\dir\file.")) -expected ""
    Assert-Equals -actual ([Ansible.IO.Path]::GetExtension("C:/path/dir/file.")) -expected ""
    Assert-Equals -actual ([Ansible.IO.Path]::GetExtension("\\?\C:\path\dir\file.")) -expected ""
    Assert-Equals -actual ([Ansible.IO.Path]::GetExtension("\\?\C:\path\$long_path\dir\file.")) -expected ""
    Assert-Equals -actual ([Ansible.IO.Path]::GetExtension("\\127.0.0.1\c$\path\dir\file.")) -expected ""
    Assert-Equals -actual ([Ansible.IO.Path]::GetExtension("\\?\UNC\127.0.0.1\c$\path\$long_path\dir\file.")) -expected ""

    # GetFileName
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileName("C:\path\dir")) -expected "dir"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileName("C:/path/dir")) -expected "dir"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileName("\\?\C:\path\dir")) -expected "dir"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileName("\\?\C:\path\$long_path\dir")) -expected "dir"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileName("\\127.0.0.1\c$\path\dir")) -expected "dir"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileName("\\?\UNC\127.0.0.1\c$\path\$long_path\dir")) -expected "dir"

    Assert-Equals -actual ([Ansible.IO.Path]::GetFileName("C:\path\dir\file.txt")) -expected "file.txt"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileName("C:/path/dir/file.txt")) -expected "file.txt"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileName("\\?\C:\path\dir\file.txt")) -expected "file.txt"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileName("\\?\C:\path\$long_path\dir\file.txt")) -expected "file.txt"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileName("\\127.0.0.1\c$\path\dir\file.txt")) -expected "file.txt"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileName("\\?\UNC\127.0.0.1\c$\path\$long_path\dir\file.txt")) -expected "file.txt"

    Assert-Equals -actual ([Ansible.IO.Path]::GetFileName("C:\path\dir\file.")) -expected "file."
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileName("C:/path/dir/file.")) -expected "file."
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileName("\\?\C:\path\dir\file.")) -expected "file."
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileName("\\?\C:\path\$long_path\dir\file.")) -expected "file."
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileName("\\127.0.0.1\c$\path\dir\file.")) -expected "file."
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileName("\\?\UNC\127.0.0.1\c$\path\$long_path\dir\file.")) -expected "file."

    # GetFileNameWithoutExtension
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("C:\path\dir")) -expected "dir"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("C:/path/dir")) -expected "dir"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("\\?\C:\path\dir")) -expected "dir"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("\\?\C:\path\$long_path\dir")) -expected "dir"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("\\127.0.0.1\c$\path\dir")) -expected "dir"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("\\?\UNC\127.0.0.1\c$\path\$long_path\dir")) -expected "dir"

    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("C:\path\dir\file.txt")) -expected "file"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("C:/path/dir/file.txt")) -expected "file"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("\\?\C:\path\dir\file.txt")) -expected "file"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("\\?\C:\path\$long_path\dir\file.txt")) -expected "file"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("\\127.0.0.1\c$\path\dir\file.txt")) -expected "file"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("\\?\UNC\127.0.0.1\c$\path\$long_path\dir\file.txt")) -expected "file"

    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("C:\path\dir\file.")) -expected "file"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("C:/path/dir/file.")) -expected "file"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("\\?\C:\path\dir\file.")) -expected "file"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("\\?\C:\path\$long_path\dir\file.")) -expected "file"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("\\127.0.0.1\c$\path\dir\file.")) -expected "file"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("\\?\UNC\127.0.0.1\c$\path\$long_path\dir\file.")) -expected "file"

    # GetFullPath - we differ a bit from the latest System.IO.Path.GetFullPath where we still resolve if the prefix starts with \\?\
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("C:\path\dir")) -expected "C:\path\dir"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("C:/path/dir")) -expected "C:\path\dir"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\C:\path\dir")) -expected "\\?\C:\path\dir"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\C:\path/dir")) -expected "\\?\C:\path\dir"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\C:\path\$long_path\dir")) -expected "\\?\C:\path\$long_path\dir"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\127.0.0.1\c$\path\dir")) -expected "\\127.0.0.1\c$\path\dir"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\UNC\127.0.0.1\c$\path\$long_path\dir")) -expected "\\?\UNC\127.0.0.1\c$\path\$long_path\dir"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\UNC\127.0.0.1\c$\path/$long_path\dir")) -expected "\\?\UNC\127.0.0.1\c$\path\$long_path\dir"

    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("C:\path\dir\file.txt")) -expected "C:\path\dir\file.txt"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("C:/path/dir/file.txt")) -expected "C:\path\dir\file.txt"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\C:\path\dir\file.txt")) -expected "\\?\C:\path\dir\file.txt"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\C:\path\$long_path\dir\file.txt")) -expected "\\?\C:\path\$long_path\dir\file.txt"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\127.0.0.1\c$\path\dir\file.txt")) -expected "\\127.0.0.1\c$\path\dir\file.txt"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\127.0.0.1\c$\path\dir/file.txt")) -expected "\\127.0.0.1\c$\path\dir\file.txt"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\UNC\127.0.0.1\c$\path\$long_path\dir\file.txt")) -expected "\\?\UNC\127.0.0.1\c$\path\$long_path\dir\file.txt"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\UNC\127.0.0.1\c$\path\$long_path\dir/file.txt")) -expected "\\?\UNC\127.0.0.1\c$\path\$long_path\dir\file.txt"

    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("C:\path\dir\file.")) -expected "C:\path\dir\file"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("C:/path/dir/file.")) -expected "C:\path\dir\file"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\C:\path\dir\file.")) -expected "\\?\C:\path\dir\file"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\C:\path\$long_path\dir\file.")) -expected "\\?\C:\path\$long_path\dir\file"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\127.0.0.1\c$\path\dir\file.")) -expected "\\127.0.0.1\c$\path\dir\file"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\UNC\127.0.0.1\c$\path\dir\file.")) -expected "\\?\UNC\127.0.0.1\c$\path\dir\file"

    $failed = $false
    try {
        [Ansible.IO.Path]::GetFullPath($null)
    } catch [System.ArgumentException] {
        $failed = $true
        Assert-Equals -actual $_.Exception.Message -expected "The path is not of a legal form."
    }
    Assert-Equals -actual $failed -expected $true
    $failed = $false
    try {
        [Ansible.IO.Path]::GetFullPath("")
    } catch [System.ArgumentException] {
        $failed = $true
        Assert-Equals -actual $_.Exception.Message -expected "The path is not of a legal form."
    }
    Assert-Equals -actual $failed -expected $true

    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("C:\")) -expected "C:\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("C:/")) -expected "C:\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("C:\a")) -expected "C:\a"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("C:\a\")) -expected "C:\a\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("C:\a\b")) -expected "C:\a\b"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("C:/a")) -expected "C:\a"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?")) -expected "\\?\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\")) -expected "\\?\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\C")) -expected "\\?\C"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\C:")) -expected "\\?\C:"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\C:\")) -expected "\\?\C:\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\C:/")) -expected "\\?\C:\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\C:\a")) -expected "\\?\C:\a"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\C:/a")) -expected "\\?\C:\a"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\C:/a/")) -expected "\\?\C:\a\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\C:/a/b")) -expected "\\?\C:\a\b"

    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\server\share")) -expected "\\server\share"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\server\share\")) -expected "\\server\share\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\server\share\path")) -expected "\\server\share\path"

    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("//server/share")) -expected "\\server\share"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("//server/share/")) -expected "\\server\share\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("//server/share/path")) -expected "\\server\share\path"

    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\UNC")) -expected "\\?\UNC"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\UNC\")) -expected "\\?\UNC\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\UNC\server")) -expected "\\?\UNC\server"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\UNC\server\")) -expected "\\?\UNC\server\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\UNC\server\share")) -expected "\\?\UNC\server\share"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\UNC\server\share\")) -expected "\\?\UNC\server\share\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\UNC\server\share\path")) -expected "\\?\UNC\server\share\path"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\UNC\server/share\path")) -expected "\\?\UNC\server\share\path"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\UNC\server/share\path\")) -expected "\\?\UNC\server\share\path\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\UNC\server/share\path/")) -expected "\\?\UNC\server\share\path\"

    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?/UNC")) -expected "\\?\UNC"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?/UNC/")) -expected "\\?\UNC\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?/UNC/server")) -expected "\\?\UNC\server"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?/UNC/server/")) -expected "\\?\UNC\server\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?/UNC/server/share")) -expected "\\?\UNC\server\share"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?/UNC/server/share/")) -expected "\\?\UNC\server\share\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?/UNC/server/share/path")) -expected "\\?\UNC\server\share\path"

    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\UNC")) -expected "\\?\UNC"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\UNC/")) -expected "\\?\UNC\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\UNC/server")) -expected "\\?\UNC\server"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\UNC/server/")) -expected "\\?\UNC\server\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\UNC/server/share")) -expected "\\?\UNC\server\share"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\UNC/server/share/")) -expected "\\?\UNC\server\share\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFullPath("\\?\UNC/server/share/path")) -expected "\\?\UNC\server\share\path"

    # GetPathRoot() - custom impl
    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot("C:\path\dir")) -expected "C:\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot("C:/path/dir")) -expected "C:\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot("\\?\C:\path\dir")) -expected "\\?\C:\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot("\\?\C:\path\$long_path\dir")) -expected "\\?\C:\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot("\\127.0.0.1\c$\path\dir")) -expected "\\127.0.0.1\c$"
    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot("\\?\UNC\127.0.0.1\c$\path\$long_path\dir")) -expected "\\?\UNC\127.0.0.1\c$"

    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot("C:\path\dir\file.txt")) -expected "C:\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot("C:/path/dir/file.txt")) -expected "C:\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot("\\?\C:\path\dir\file.txt")) -expected "\\?\C:\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot("\\?\C:\path\$long_path\dir\file.txt")) -expected "\\?\C:\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot("\\127.0.0.1\c$\path\dir\file.txt")) -expected "\\127.0.0.1\c$"
    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot("\\?\UNC\127.0.0.1\c$\path\$long_path\dir\file.txt")) -expected "\\?\UNC\127.0.0.1\c$"

    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot("C:\path\dir\file.")) -expected "C:\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot("C:/path/dir/file.")) -expected "C:\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot("\\?\C:\path\dir\file.")) -expected "\\?\C:\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot("\\?\C:\path\$long_path\dir\file.")) -expected "\\?\C:\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot("\\127.0.0.1\c$\path\dir\file.")) -expected "\\127.0.0.1\c$"
    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot("\\?\UNC\127.0.0.1\c$\path\$long_path\dir\file.")) -expected "\\?\UNC\127.0.0.1\c$"

    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot("test")) -expected ""
    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot(".\test")) -expected ""
    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot("C:")) -expected "C:"
    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot("\\?\C:")) -expected "\\?\C:"
    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot("C:\")) -expected "C:\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot("\\?\C:\")) -expected "\\?\C:\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot("C:\path")) -expected "C:\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot("\\?\C:\path")) -expected "\\?\C:\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot("\\")) -expected "\\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot("\\?\UNC\")) -expected "\\?\UNC\"
    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot("\\server")) -expected "\\server"
    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot("\\?\UNC\server")) -expected "\\?\UNC\server"
    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot("\\server\share")) -expected "\\server\share"
    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot("\\?\UNC\server\share")) -expected "\\?\UNC\server\share"
    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot("\\server\share\path")) -expected "\\server\share"
    Assert-Equals -actual ([Ansible.IO.Path]::GetPathRoot("\\?\UNC\server\share\path")) -expected "\\?\UNC\server\share"

    # HasExtension()
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("C:\path\dir")) -expected "dir"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("C:/path/dir")) -expected "dir"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("\\?\C:\path\dir")) -expected "dir"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("\\?\C:\path\$long_path\dir")) -expected "dir"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("\\127.0.0.1\c$\path\dir")) -expected "dir"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("\\?\UNC\127.0.0.1\c$\path\$long_path\dir")) -expected "dir"

    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("C:\path\dir\file.txt")) -expected "file"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("C:/path/dir/file.txt")) -expected "file"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("\\?\C:\path\dir\file.txt")) -expected "file"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("\\?\C:\path\$long_path\dir\file.txt")) -expected "file"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("\\127.0.0.1\c$\path\dir\file.txt")) -expected "file"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("\\?\UNC\127.0.0.1\c$\path\$long_path\dir\file.txt")) -expected "file"

    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("C:\path\dir\file.")) -expected "file"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("C:/path/dir/file.")) -expected "file"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("\\?\C:\path\dir\file.")) -expected "file"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("\\?\C:\path\$long_path\dir\file.")) -expected "file"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("\\127.0.0.1\c$\path\dir\file.")) -expected "file"
    Assert-Equals -actual ([Ansible.IO.Path]::GetFileNameWithoutExtension("\\?\UNC\127.0.0.1\c$\path\$long_path\dir\file.")) -expected "file"

    # IsPathRooted()
    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted("C:\path\dir")) -expected $true
    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted("C:/path/dir")) -expected $true
    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted("\\?\C:\path\dir")) -expected $true
    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted("\\?\C:\path\$long_path\dir")) -expected $true
    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted("\\127.0.0.1\c$\path\dir")) -expected $true
    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted("\\?\UNC\127.0.0.1\c$\path\$long_path\dir")) -expected $true

    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted("C:\path\dir\file.txt")) -expected $true
    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted("C:/path/dir/file.txt")) -expected $true
    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted("\\?\C:\path\dir\file.txt")) -expected $true
    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted("\\?\C:\path\$long_path\dir\file.txt")) -expected $true
    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted("\\127.0.0.1\c$\path\dir\file.txt")) -expected $true
    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted("\\?\UNC\127.0.0.1\c$\path\$long_path\dir\file.txt")) -expected $true

    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted("C:\path\dir\file.")) -expected $true
    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted("C:/path/dir/file.")) -expected $true
    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted("\\?\C:\path\dir\file.")) -expected $true
    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted("\\?\C:\path\$long_path\dir\file.")) -expected $true
    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted("\\127.0.0.1\c$\path\dir\file.")) -expected $true
    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted("\\?\UNC\127.0.0.1\c$\path\$long_path\dir\file.")) -expected $true

    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted("test")) -expected $false
    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted(".\test")) -expected $false
    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted("C:")) -expected $true
    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted("\\?\C:")) -expected $true
    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted("C:\")) -expected $true
    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted("\\?\C:\")) -expected $true
    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted("C:\path")) -expected $true
    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted("\\?\C:\path")) -expected $true
    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted("\\")) -expected $true
    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted("\\?\UNC\")) -expected $true
    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted("\\server")) -expected $true
    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted("\\?\UNC\server")) -expected $true
    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted("\\server\share")) -expected $true
    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted("\\?\UNC\server\share")) -expected $true
    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted("\\server\share\path")) -expected $true
    Assert-Equals -actual ([Ansible.IO.Path]::IsPathRooted("\\?\UNC\server\share\path")) -expected $true
}

Function Test-SparseFileClass($root_path) {
    $sparse_path = "$root_path\sparse.txt"

    # don't run if on Server 2008 and it's a network drive, this won't work
    $os_version = [Version](Get-Item -Path $env:SystemRoot\System32\kernel32.dll).FileVersion.ProductVersion
    if ($sparse_path.StartsWith("\\") -or $sparse_path.StartsWith("\\?\UNC\") -and $os_version -lt [Version]"6.1") {
        return
    }

    # create the empty file and check the size + regions
    [Ansible.IO.File]::WriteAllBytes($sparse_path, [byte[]]@())
    $sparse_file = New-Object -TypeName Ansible.IO.FileInfo -ArgumentList $sparse_path
    $actual = [Ansible.IO.SparseFile]::GetAllAllocations($sparse_path)
    Assert-Equals -actual $sparse_file.DiskLength -expected 0
    Assert-Equals -actual $sparse_file.Length -expected 0
    Assert-Equals -actual $actual.Count -expected 0

    # zero out 3MB of space
    [Ansible.IO.SparseFile]::ZeroData($sparse_path, 0, 3MB)

    # even though we zero'd out the space we still haven't placed any data so the file is empty
    $sparse_file.Refresh()
    $actual = [Ansible.IO.SparseFile]::GetAllAllocations($sparse_path)
    Assert-Equals -actual $sparse_file.DiskLength -expected 0
    Assert-Equals -actual $sparse_file.Length -expected 0
    Assert-Equals -actual $actual.Count -expected 0

    # add an end marker byte (outside of freed data) - the disk size will still be full as we never marked the file as sparse
    $fs = [Ansible.IO.File]::OpenWrite($sparse_file)
    try {
        $fs.Seek(3MB, [System.IO.SeekOrigin]::Begin) > $null
        $fs.WriteByte(0)
    } finally {
        $fs.Close()
    }
    $sparse_file.Refresh()
    $actual = [Ansible.IO.SparseFile]::GetAllAllocations($sparse_path)
    Assert-Equals -actual $sparse_file.Attributes.HasFlag([System.IO.FileAttributes]::SparseFile) -expected $false
    Assert-Equals -actual ([Ansible.IO.SparseFile]::IsSparseFile($sparse_path)) -expected $false
    Assert-Equals -actual $sparse_file.DiskLength -expected (3MB + 1)
    Assert-Equals -actual $sparse_file.Length -expected (3MB + 1)
    Assert-Equals -actual $actual.Count -expected 1
    Assert-Equals -actual $actual[0].GetType().FullName -expected "Ansible.IO.SparseAllocations"
    Assert-Equals -actual $actual[0].Length -expected (3MB + 1)
    Assert-Equals -actual $actual[0].FileOffset -expected 0

    # verify that setting the sparse flag post zero out won't work
    [Ansible.IO.SparseFile]::AddSparseAttribute($sparse_path)
    $sparse_file.Refresh()
    Assert-Equals -actual $sparse_file.Attributes.HasFlag([System.IO.FileAttributes]::SparseFile) -expected $true
    Assert-Equals -actual ([Ansible.IO.SparseFile]::IsSparseFile($sparse_path)) -expected $true
    Assert-Equals -actual $sparse_file.DiskLength -expected (3MB + 1)
    Assert-Equals -actual $sparse_file.Length -expected (3MB + 1)

    [Ansible.IO.SparseFile]::RemoveSparseAttribute($sparse_path)
    $sparse_file.Refresh()
    Assert-Equals -actual $sparse_file.Attributes.HasFlag([System.IO.FileAttributes]::SparseFile) -expected $false
    Assert-Equals -actual ([Ansible.IO.SparseFile]::IsSparseFile($sparse_path)) -expected $false

    # delete and try again after marking file as sparse
    $sparse_file.Delete()
    [Ansible.IO.File]::WriteAllBytes($sparse_path, [byte[]]@())
    [Ansible.IO.SparseFile]::AddSparseAttribute($sparse_path)
    $sparse_file.Refresh()
    $actual = [Ansible.IO.SparseFile]::GetAllAllocations($sparse_path)
    Assert-Equals -actual $sparse_file.Attributes.HasFlag([System.IO.FileAttributes]::SparseFile) -expected $true
    Assert-Equals -actual ([Ansible.IO.SparseFile]::IsSparseFile($sparse_path)) -expected $true
    Assert-Equals -actual $sparse_file.DiskLength -expected 0
    Assert-Equals -actual $sparse_file.Length -expected 0
    Assert-Equals -actual $actual.Count -expected 0

    # add marker at the end of the sparse region
    [Ansible.IO.SparseFile]::ZeroData($sparse_path, 0, 3MB)
    $fs = [Ansible.IO.File]::OpenWrite($sparse_file)
    try {
        $fs.Seek(3MB, [System.IO.SeekOrigin]::Begin) > $null
        $fs.WriteByte(0)
    } finally {
        $fs.Close()
    }
    $sparse_file.Refresh()
    $actual = [Ansible.IO.SparseFile]::GetAllAllocations($sparse_path)
    Assert-Equals -actual $sparse_file.DiskLength -expected 65536
    Assert-Equals -actual $sparse_file.Length -expected (3MB + 1)
    Assert-Equals -actual $actual.Count -expected 1
    Assert-Equals -actual $actual[0].GetType().FullName -expected "Ansible.IO.SparseAllocations"
    Assert-Equals -actual $actual[0].Length -expected 1
    Assert-Equals -actual $actual[0].FileOffset -expected 3MB

    # write 10 and 20 bytes at the 1 and 2 MB mark respectively
    $fs = [Ansible.IO.File]::OpenWrite($sparse_file)
    try {
        $fs.Seek(1MB, [System.IO.SeekOrigin]::Begin) > $null
        $fs.WriteByte(1)

        $fs.Seek(2MB, [System.IO.SeekOrigin]::Begin) > $null
        $fs.WriteByte(2)
    } finally {
        $fs.Close()
    }
    
    $actual = [Ansible.IO.SparseFile]::GetAllAllocations($sparse_path)
    Assert-Equals -actual $actual.Count -expected 3
    Assert-Equals -actual $actual[0].GetType().FullName -expected "Ansible.IO.SparseAllocations"
    Assert-Equals -actual $actual[0].Length -expected 65536  # NTFS block size - may need to dynamic get this for test
    Assert-Equals -actual $actual[0].FileOffset -expected 1MB
    Assert-Equals -actual $actual[1].Length -expected 65536
    Assert-Equals -actual $actual[1].FileOffset -expected 2MB
    Assert-Equals -actual $actual[2].Length -expected 1
    Assert-Equals -actual $actual[2].FileOffset -expected 3MB

    # get allocation only on specific offset
    $actual = [Ansible.IO.SParseFile]::GetAllocations($sparse_path, 0.5KB, 2MB)
    Assert-Equals -actual $actual.Count -expected 1  # should ignore our 2nd allocation as it doesn't go through the entire range
    Assert-Equals -actual $actual[0].Length -expected 65536
    Assert-Equals -actual $actual[0].FileOffset -expected 1MB

    $actual = [Ansible.IO.SParseFile]::GetAllocations($sparse_path, 0.5KB, 2.5MB)
    Assert-Equals -actual $actual.Count -expected 2
    Assert-Equals -actual $actual[0].Length -expected 65536
    Assert-Equals -actual $actual[0].FileOffset -expected 1MB
    Assert-Equals -actual $actual[1].Length -expected 65536
    Assert-Equals -actual $actual[1].FileOffset -expected 2MB

    # zero out from 0 to 1.5 MB
    [Ansible.IO.SparseFile]::ZeroData($sparse_path, 0, 1.5MB)
    $actual = [Ansible.IO.SparseFile]::GetAllAllocations($sparse_path)
    Assert-Equals -actual $actual.Count -expected 2
    Assert-Equals -actual $actual[0].Length -expected 65536
    Assert-Equals -actual $actual[0].FileOffset -expected 2MB
    Assert-Equals -actual $actual[1].Length -expected 1
    Assert-Equals -actual $actual[1].FileOffset -expected 3MB
}

# call each test group five times
# 1 - Normal Path
# 2 - Normal Path with the \\?\ prefix
# 3 - Path exceeding 260 chars with the \\?\ prefix
# 4 - Normal UNC Path
# 5 - Extended UNC Path with the \\?\UNC\ prefix

Clear-TestDirectory -path $path
Test-FileClass -root_path $path
Test-DirectoryClass -root_path $path
Test-SparseFileClass -root_path $path

Clear-TestDirectory -path $path
Test-FileClass -root_path "\\?\$path"
Test-DirectoryClass -root_path "\\?\$path"
Test-SparseFileClass -root_path "\\?\$path"

Clear-TestDirectory -path $path
$long_path = "\\?\$path\long-path-test\{0}\{0}\{0}\{0}\{0}\{0}\{0}" -f ("a" * 250)
[Ansible.IO.Directory]::CreateDirectory($long_path) > $null
Test-FileClass -root_path $long_path
Test-DirectoryClass -root_path $long_path
Test-SparseFileClass -root_path $long_path

Clear-TestDirectory -path $path
Test-FileClass -root_path "\\127.0.0.1\c$\$($path.Substring(3))"
Test-DirectoryClass -root_path "\\127.0.0.1\c$\$($path.Substring(3))"
Test-SparseFileClass -root_path "\\127.0.0.1\c$\$($path.Substring(3))"

Clear-TestDirectory -path $path
$long_unc_path = "\\?\UNC\127.0.0.1\c$\$($path.Substring(3))\long-path-test\{0}\{0}\{0}\{0}\{0}\{0}\{0}" -f ("a" * 250)
[Ansible.IO.Directory]::CreateDirectory($long_unc_path) > $null
Test-FileClass -root_path $long_unc_path
Test-DirectoryClass -root_path $long_unc_path
Test-SparseFileClass -root_path $long_unc_path

# Ansible.IO.Path tests
Test-IOPath -root_path $path

[Ansible.IO.Directory]::Delete("\\?\" + $path, $true)
$result.data = "success"
Exit-Json -obj $result
