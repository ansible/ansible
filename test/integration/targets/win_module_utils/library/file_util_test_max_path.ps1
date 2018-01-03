#!powershell

# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.FileUtil

$ErrorActionPreference = "Stop"

$params = Parse-Args $args
$path = Get-AnsibleParam -obj $params -name "path" -type "path" -failifempty $true

$result = @{
    changed = $false
}
Load-FileUtilFunctions

Function Assert-Equals($actual, $expected, $msg) {
    if ($actual -ne $expected) {
        $call_stack = (Get-PSCallStack)[1]
        $error_msg = "AssertionError:`r`nActual: `"$actual`" != Expected: `"$expected`"`r`nLine: $($call_stack.ScriptLineNumber), Method: $($call_stack.Position.Text)"
        if ($msg) {
            $error_msg += "`r`n$msg"
        }
        Fail-Json -obj $result -message $error_msg
    }
}

Function Clear-TestDirectory($path) {
    $path = "\\?\$path"
    if ([Ansible.IO.Directory]::Exists($path)) {
        [Ansible.IO.Directory]::Delete($path, $true) > $null
    }
    [Ansible.IO.Directory]::CreateDirectory($path) > $null
}

Function Test-FileClass($root_path) {
    ### FileInfo Tests ### https://msdn.microsoft.com/en-us/library/system.io.fileinfo(v=vs.110).aspx
    # Test Class Attributes when file does not exist

    # Test Class Attributes when file does exist

    # Test properties

    # Test Functions

    ### File Tests ### https://msdn.microsoft.com/en-us/library/system.io.file(v=vs.110).aspx
    # AppendAllLines(String, IEnumerable<String>)
    # AppendAllLines(String, IEnumerable<String>, Encoding)
    # AppendAllText(String, String)
    # AppendAllText(String, Encoding)
    # AppendText(String)
    # Copy(String, String)
    # Copy(String, String, Boolean)
    # Create(String)
    # Create(String, Int32)
    # Create(string, Int32, FileOptions)
    # Create(String, Int32, FileOptions, FileSecurity)
    # CreateText(String)
    # Decrypt(String)
    # Delete(string)
    # Encrypt(String)
    # Exists(String)
    # GetAccessControl(String)
    # GetAccessControl(String, AccessControlSelections)
    # GetAttributes(String)
    # GetCreationTime(String)
    # GetCreationTimeUtc(String)
    # GetLastAccessTime(String)
    # GetLastAccessTimeUtc(String)
    # GetLastWriteTime(String)
    # GetLastWriteTimeUtc(String)
    # Move(String, String)
    # Open(String, FileMode)
    # Open(String, FileMode, FileAccess)
    # Open(String, FileMode, FileAccess, FileShare)
    # OpenRead(String)
    # OpenText(String)
    # OpenWrite(String)
    # ReadAllBytes(String)
    # ReadAllLines(String)
    # ReadAllLines(String, Encoding)
    # ReadAllText(String)
    # ReadAllText(String, Encoding)
    # ReadLines(String)
    # ReadLines(String, Encoding)
    # Replace(String, String, String)
    # Replace(String, String, String, Boolean)
    # SetAccessControl(String, FileSecurity)
    # SetAttributes(String, FileAttributes)
    # SetCreationTime(String, DateTime)
    # SetCreationTimeUtc(String, DateTime)
    # SetLastAccessTime(String, DateTime)
    # SetLastAccessTimeUtc(String, DateTime)
    # SetLastWriteTime(String, DateTime)
    # SetLastWriteTimeUtc(String, DateTime)
    # WriteAllBytes(String, Byte[])
    # WriteAllLines(String, IEnumerable<String>)
    # WriteAllLines(String, IEnumerable<String>, Encoding)
    # WriteAllLines(String, String[])
    # WriteAllLines(String, String[], Encoding)
    # WriteAllText(String, String)
    # WriteAllText(String, String, Encoding)
}
Function Test-DirectoryClass($root_path) {
    $directory_path = "$root_path\dir"

    ### DirectoryInfo Tests ###
    $dir = New-Object -TypeName Ansible.IO.DirectoryInfo -ArgumentList $directory_path

    # Test class attributes when it doesn't exist
    Assert-Equals -actual $dir.Exists -expected $false
    Assert-Equals -actual $dir.Name -expected "dir"
    Assert-Equals -actual $dir.Parent.ToString() -expected $root_path
    if ($root_path.StartsWith("\\?\")) {
        Assert-Equals -actual $dir.Root.ToString() -expected "\\?\C:\"
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
    if ($root_path.StartsWith("\\?\")) {
        Assert-Equals -actual $dir.Root.ToString() -expected "\\?\C:\"
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
    $dir.Refresh()
    Assert-Equals -actual $dir.Attributes -expected ([System.IO.FileAttributes]::Directory -bor [System.IO.FileAttributes]::Archive -bor [System.IO.FileAttributes]::Hidden)

    $new_date = (Get-Date -Date "1993-06-11 06:51:32Z")
    $dir.CreationTimeUtc = $new_date
    $dir.Refresh()
    Assert-Equals -actual $dir.CreationTimeUtc.ToFileTimeUtc() -expected $new_date.ToFileTimeUtc()
    $dir.LastAccessTimeUtc = $new_date
    $dir.Refresh()
    Assert-Equals -actual $dir.LastAccessTimeUtc.ToFileTimeUtc() -expected $new_date.ToFileTimeUtc()
    $dir.LastWriteTimeUtc = $new_date
    $dir.Refresh()
    Assert-Equals -actual $dir.LastWriteTimeUtc.ToFileTimeUtc() -expected $new_date.ToFileTimeUtc()

    # test DirectoryInfo methods
    # create tests
    $subdir = $dir.CreateSubDirectory("subdir")
    Assert-Equals -actual ([Ansible.IO.Directory]::Exists("$directory_path\subdir")) -expected $true

    # enumerate tests
    $subdir1 = $dir.CreateSubDirectory("subdir-1")
    $subdir2 = $dir.CreateSubDirectory("subdir-2")
    $subdir3 = $subdir1.CreateSubDirectory("subdir3")
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
        Assert-Equals -actual ($dir_name.Name -in ("subdir", "subdir-1", "subdir-2")) -expected $true
    }
    $dir_dirs = $dir.EnumerateDirectories("subdir-?")
    foreach ($dir_name in $dir_dirs) {
        Assert-Equals -actual $dir_name.GetType().FullName -expected "Ansible.IO.DirectoryInfo"
        Assert-Equals -actual ($dir_name.Name -in ("subdir-1", "subdir-2")) -expected $true
    }
    $dir_dirs = $dir.EnumerateDirectories("*", [System.IO.SearchOption]::AllDirectories)
    foreach ($dir_name in $dir_dirs) {
        Assert-Equals -actual $dir_name.GetType().FullName -expected "Ansible.IO.DirectoryInfo"
        Assert-Equals -actual ($dir_name.Name -in ("subdir", "subdir-1", "subdir-2", "subdir3")) -expected $true
    }

    $dir_dirs = $dir.GetDirectories()
    foreach ($dir_name in $dir_dirs) {
        Assert-Equals -actual $dir_name.GetType().FullName -expected "Ansible.IO.DirectoryInfo"
        Assert-Equals -actual ($dir_name.Name -in ("subdir", "subdir-1", "subdir-2")) -expected $true
    }
    $dir_dirs = $dir.GetDirectories("subdir-?")
    foreach ($dir_name in $dir_dirs) {
        Assert-Equals -actual $dir_name.GetType().FullName -expected "Ansible.IO.DirectoryInfo"
        Assert-Equals -actual ($dir_name.Name -in ("subdir-1", "subdir-2")) -expected $true
    }
    $dir_dirs = $dir.GetDirectories("*", [System.IO.SearchOption]::AllDirectories)
    foreach ($dir_name in $dir_dirs) {
        Assert-Equals -actual $dir_name.GetType().FullName -expected "Ansible.IO.DirectoryInfo"
        Assert-Equals -actual ($dir_name.Name -in ("subdir", "subdir-1", "subdir-2", "subdir3")) -expected $true
    }

    $dir_files = $dir.EnumerateFiles()
    foreach ($dir_file in $dir_files) {
        Assert-Equals -actual $dir_file.GetType().FullName -expected "Ansible.IO.FileInfo"
        Assert-Equals -actual ($dir_file.Name -in ("file.txt", "anotherfile.txt")) -expected $true
    }
    $dir_files = $dir.EnumerateFiles("anotherfile*")
    foreach ($dir_file in $dir_files) {
        Assert-Equals -actual $dir_file.GetType().FullName -expected "Ansible.IO.FileInfo"
        Assert-Equals -actual ($dir_file.Name -in ("anotherfile.txt")) -expected $true
    }
    $dir_files = $dir.EnumerateFiles("*", [System.IO.SearchOption]::AllDirectories)
    foreach ($dir_file in $dir_files) {
        Assert-Equals -actual $dir_file.GetType().FullName -expected "Ansible.IO.FileInfo"
        Assert-Equals -actual ($dir_file.Name -in ("file.txt", "anotherfile.txt", "file-1.txt", "file-2.txt", "file-3.txt")) -expected $true
    }

    $dir_files = $dir.GetFiles()
    foreach ($dir_file in $dir_files) {
        Assert-Equals -actual $dir_file.GetType().FullName -expected "Ansible.IO.FileInfo"
        Assert-Equals -actual ($dir_file.Name -in ("file.txt", "anotherfile.txt")) -expected $true
    }
    $dir_files = $dir.GetFiles("anotherfile*")
    foreach ($dir_file in $dir_files) {
        Assert-Equals -actual $dir_file.GetType().FullName -expected "Ansible.IO.FileInfo"
        Assert-Equals -actual ($dir_file.Name -in ("anotherfile.txt")) -expected $true
    }
    $dir_files = $dir.GetFiles("*", [System.IO.SearchOption]::AllDirectories)
    foreach ($dir_file in $dir_files) {
        Assert-Equals -actual $dir_file.GetType().FullName -expected "Ansible.IO.FileInfo"
        Assert-Equals -actual ($dir_file.Name -in ("file.txt", "anotherfile.txt", "file-1.txt", "file-2.txt", "file-3.txt")) -expected $true
    }

    $dir_entries = $dir.EnumerateFileSystemInfos()
    foreach ($dir_entry in $dir_entries) {
        Assert-Equals -actual ($dir_entry.GetType().FullName -in @("Ansible.IO.FileInfo", "Ansible.IO.DirectoryInfo")) -expected $true
        Assert-Equals -actual ($dir_entry.Name -in ("file.txt", "anotherfile.txt", "subdir", "subdir-1", "subdir-2")) -expected $true
    }
    $dir_entries = $dir.EnumerateFileSystemInfos("anotherfile*")
    foreach ($dir_entry in $dir_entries) {
        Assert-Equals -actual ($dir_entry.GetType().FullName -in @("Ansible.IO.FileInfo", "Ansible.IO.DirectoryInfo")) -expected $true
        Assert-Equals -actual ($dir_entry.Name -in ("anotherfile.txt")) -expected $true
    }
    $dir_entries = $dir.EnumerateFileSystemInfos("*", [System.IO.SearchOption]::AllDirectories)
    foreach ($dir_entry in $dir_entries) {
        Assert-Equals -actual ($dir_entry.GetType().FullName -in @("Ansible.IO.FileInfo", "Ansible.IO.DirectoryInfo")) -expected $true
        Assert-Equals -actual ($dir_entry.Name -in ("file.txt", "anotherfile.txt", "file-1.txt", "file-2.txt", "file-3.txt", "subdir", "subdir-1", "subdir-2", "subdir3")) -expected $true
    }

    $dir_entries = $dir.GetFileSystemInfos()
    foreach ($dir_entry in $dir_entries) {
        Assert-Equals -actual ($dir_entry.GetType().FullName -in @("Ansible.IO.FileInfo", "Ansible.IO.DirectoryInfo")) -expected $true
        Assert-Equals -actual ($dir_entry.Name -in ("file.txt", "anotherfile.txt", "subdir", "subdir-1", "subdir-2")) -expected $true
    }
    $dir_entries = $dir.GetFileSystemInfos("anotherfile*")
    foreach ($dir_entry in $dir_entries) {
        Assert-Equals -actual ($dir_entry.GetType().FullName -in @("Ansible.IO.FileInfo", "Ansible.IO.DirectoryInfo")) -expected $true
        Assert-Equals -actual ($dir_entry.Name -in ("anotherfile.txt")) -expected $true
    }
    $dir_entries = $dir.GetFileSystemInfos("*", [System.IO.SearchOption]::AllDirectories)
    foreach ($dir_entry in $dir_entries) {
        Assert-Equals -actual ($dir_entry.GetType().FullName -in @("Ansible.IO.FileInfo", "Ansible.IO.DirectoryInfo")) -expected $true
        Assert-Equals -actual ($dir_entry.Name -in ("file.txt", "anotherfile.txt", "file-1.txt", "file-2.txt", "file-3.txt", "subdir", "subdir-1", "subdir-2", "subdir3")) -expected $true
    }
    
    # move tests
    $subdir2.MoveTo("$directory_path\subdir-move")
    Assert-Equals -actual ([Ansible.IO.Directory]::Exists("$directory_path\subdir-move")) -expected $true
    Assert-Equals -actual ([Ansible.IO.File]::Exists("$directory_path\subdir-move\file-2.txt")) -expected $true

    # delete tests
    try {
        # fail to delete a directory that has contents
        $subdir1.Delete()
    } catch {
        Assert-Equals -actual $_.Exception.Message -expected "Exception calling `"Delete`" with `"0`" argument(s): `"RemoveDirectoryW($($subdir1.FullName)) failed (The directory is not empty, Win32ErrorCode 145)`""
    }
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
        try {
            $acl_dir.SetAccessControl($dir_sec)
        } catch {
            Assert-Equals -actual $_.Exception.Message -expected "Exception calling `"SetAccessControl`" with `"1`" argument(s): `"SetNamedSecurityInfoW($($acl_dir.FullName)) failed (A required privilege is not held by the client, Win32ErrorCode 1314)`""
        }
    }

    ### Directory Tests ###
    # CreateDirectory(String)
    # CreateDirectory(String, DirectorySecurity)
    # Delete(String)
    # Delete(String, Boolean)
    # EnumerateDirectories(String)
    # EnumerateDirectories(String, String)
    # EnumerateDirectories(String, String, SearchOption)
    # EnumerateFiles(String)
    # EnumerateFiles(String, String)
    # EnumerateFiles(String, String, SearchOption)
    # EnumerateFileSystemEntries(String)
    # EnumerateFileSystemEntries(String, String)
    # EnumerateFileSystemEntries(String, String, SearchOption)
    # Exists(String)
    # GetAccessControl(String)
    # GetAccessControl(String, AccessControlSelections)
    # GetCreationTime(String)
    # GetCreationTimeUtc(String)
    # GetDirectories(String)
    # GetDirectories(String, String)
    # GetDirectories(String, String, SearchOption)
    # GetFiles(String)
    # GetFiles(String, String)
    # GetFiles(String, String, SearchOption)
    # GetFileSystemEntries(String)
    # GetFileSystemEntries(String, String)
    # GetFileSystemEntries(String, String, SearchOption)
    # GetLastAccessTime(String)
    # GetLastAccessTimeUtc(String)
    # GetLastWriteTime(String)
    # GetLastWriteTimeUtc(String)
    # GetParent(String)
    # Move(String, String)
    # SetAccessControl(String, DirectorySecurity)
    # SetCreationTime(String, DateTime)
    # SetCreationTimeUtc(String, DateTime)
    # SetLastAccessTime(String, DateTime)
    # SetLastAccessTimeUtc(String, DateTime)
    # SetLastWriteTime(String, DateTime)
    # SetLastWriteTimeUtc(String, DateTime)
}

# call each test three times
# 1 - Normal Path
# 2 - Normal Path with the \\?\ prefix
# 3 - Path exceeding 260 chars with the \\?\ prefix
Clear-TestDirectory -path $path
Test-FileClass -root_path $path
Test-DirectoryClass -root_path $path

Clear-TestDirectory -path $path
Test-FileClass -root_path "\\?\$path"
Test-DirectoryClass -root_path "\\?\$path"

Clear-TestDirectory -path $path
$long_path = "\\?\$path\long-path-test\$("a" * 240)"
[Ansible.IO.Directory]::CreateDirectory($long_path) > $null
Test-FileClass -root_path $long_path
Test-DirectoryClass -root_path $long_path

[Ansible.IO.Directory]::Delete("\\?\" + $path, $true) > $null
$result.data = "success"
Exit-Json -obj $result

