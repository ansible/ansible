#!powershell

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

# Large portions borrowed from Brian Lloyd's (@brianlloyd) win_lineinfile 
# and Yaegashi Takeshi's (@yaegashi) blockinfile

function WriteLines($outlines, $path, $linesep, $encodingobj, $validate, $check_mode) {

    $acl = $null

    Try {
        If (Test-Path -LiteralPath $path) {
            $acl = Get-Acl -Path $path
        }
    }
    Catch {
        Fail-Json @{} "Cannot get ACL from original file temporary file! ($($_.Exception.Message))";
    }
    Try {
        $temppath = [System.IO.Path]::GetTempFileName();
    }
    Catch {
        Fail-Json @{} "Cannot create temporary file! ($($_.Exception.Message))";
    }
    $joined = $outlines -join $linesep;
    [System.IO.File]::WriteAllText($temppath, $joined, $encodingobj);

    If ($validate) {

        If (-not ($validate -like "*%s*")) {
            Fail-Json @{} "validate must contain %s: $validate";
        }

        $validate = $validate.Replace("%s", $temppath);

        $parts = [System.Collections.ArrayList] $validate.Split(" ");
        $cmdname = $parts[0];

        $cmdargs = $validate.Substring($cmdname.Length + 1);

        $process = [Diagnostics.Process]::Start($cmdname, $cmdargs);
        $process.WaitForExit();

        If ($process.ExitCode -ne 0) {
            [string] $output = $process.StandardOutput.ReadToEnd();
            [string] $error = $process.StandardError.ReadToEnd();
            Remove-Item $temppath -force;
            Fail-Json @{} "failed to validate $cmdname $cmdargs with error: $output $error";
        }

    }

    # Commit changes to the path
    $cleanpath = $path.Replace("/", "\");
    Try {
        Copy-Item $temppath $cleanpath -force -ErrorAction Stop -WhatIf:$check_mode;
    }
    Catch {
        Fail-Json @{} "Cannot write to: $cleanpath ($($_.Exception.Message))";
    }

    If ($acl) {
        Try {
            Set-Acl -Path $cleanpath -AclObject $acl -WhatIf:$check_mode 
        }
        Catch {
            Fail-Json @{} "Cannot set ACL on new file! ($($_.Exception.Message))";
        }
    }

    Try {
        Remove-Item $temppath -force -ErrorAction Stop;
    }
    Catch {
        Fail-Json @{} "Cannot remove temporary file: $temppath ($($_.Exception.Message))";
    }

    return $joined;
}


# Backup the file specified with a date/time filename
function BackupFile($path, $check_mode) {
    $backuppath = $path + "." + [DateTime]::Now.ToString("yyyyMMdd-HHmmss");
    Try {
        Copy-Item $path $backuppath -WhatIf:$check_mode;
    }
    Catch {
        Fail-Json @{} "Cannot copy backup file! ($($_.Exception.Message))";
    }
    If (-not $check_mode) {
        Try {
            Get-Acl -Path $path | Set-Acl -Path $backuppath
        }
        Catch {
            Fail-Json @{} "Cannot copy ACL to backup file! ($($_.Exception.Message))";
        }
    }
    return $backuppath;
}

# Parse the parameters file dropped by the Ansible machinery
$params = Parse-Args $args -supports_check_mode $true;
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false;
$diff_support = Get-AnsibleParam -obj $params -name "_ansible_diff" -type "bool" -default $false;

# Initialize defaults for input parameters.
$path = Get-AnsibleParam -obj $params -name "path" -type "path" -failifempty $true -aliases "dest", "destfile", "name";
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present", "absent";
$block = Get-AnsibleParam -obj $params -name "block" -type "str";
$insertafter = Get-AnsibleParam -obj $params -name "insertafter" -type "str";
$insertbefore = Get-AnsibleParam -obj $params -name "insertbefore" -type "str";
$create = Get-AnsibleParam -obj $params -name "create" -type "bool" -default $false;
$backup = Get-AnsibleParam -obj $params -name "backup" -type "bool" -default $false;
$validate = Get-AnsibleParam -obj $params -name "validate" -type "str";
$encoding = Get-AnsibleParam -obj $params -name "encoding" -type "str" -default "auto";
$newline = Get-AnsibleParam -obj $params -name "newline" -type "str" -default "windows" -validateset "unix", "windows";
$marker = Get-AnsibleParam -obj $params -name "marker" -type "str" -default "# {mark} ANSIBLE MANAGED BLOCK";
$marker_begin = Get-AnsibleParam -obj $params -name "marker_begin" -type "str" -default "BEGIN";
$marker_end = Get-AnsibleParam -obj $params -name "marker_end" -type "str" -default "END";

# Fail if the path is not a file
If (Test-Path -LiteralPath $path -PathType "container") {
    Fail-Json @{} "Path $path is a directory";
}

# Default to windows line separator - probably most common
$linesep = "`r`n"
If ($newline -eq "unix") {
    $linesep = "`n";
}

If ($insertbefore -and $insertafter) {
    Add-Warning $result "Both insertbefore and insertafter parameters found, ignoring `"insertafter=$insertafter`""
}

If (-not $insertbefore -and -not $insertafter) {
    $insertafter = "EOF";
}

# Compile the regex for insertafter or insertbefore, if provided
$insre = $null;
If ($insertafter -and $insertafter -ne "BOF" -and $insertafter -ne "EOF") {
    $insre = New-Object Regex $insertafter, 'Compiled';
}
ElseIf ($insertbefore -and $insertbefore -ne "BOF" -and $insertbefore -ne "EOF") {
    $insre = New-Object Regex $insertbefore, 'Compiled';
}


# Figure out the proper encoding to use for reading / writing the target file.

# The default encoding is UTF-8 without BOM
$encodingobj = [System.Text.UTF8Encoding] $false;

If ($encoding -ne "auto") {
    # If an explicit encoding is specified, use that instead
    $encodingobj = [System.Text.Encoding]::GetEncoding($encoding);
}
ElseIf (Test-Path -LiteralPath $path) {
    # Otherwise see if we can determine the current encoding of the target file.
    # If the file doesn't exist yet (create == 'yes') we use the default or
    # explicitly specified encoding set above.

    # Get a sorted list of encodings with preambles, longest first
    $max_preamble_len = 0;
    $sortedlist = New-Object System.Collections.SortedList;
    Foreach ($encodinginfo in [System.Text.Encoding]::GetEncodings()) {
        $encoding = $encodinginfo.GetEncoding();
        $plen = $encoding.GetPreamble().Length;
        If ($plen -gt $max_preamble_len) {
            $max_preamble_len = $plen;
        }
        If ($plen -gt 0) {
            $sortedlist.Add( - ($plen * 1000000 + $encoding.CodePage), $encoding) > $null;
        }
    }

    # Get the first N bytes from the file, where N is the max preamble length we saw
    [Byte[]]$bom = Get-Content -Encoding Byte -ReadCount $max_preamble_len -TotalCount $max_preamble_len -LiteralPath $path;

    # Iterate through the sorted encodings, looking for a full match.
    $found = $false;
    Foreach ($encoding in $sortedlist.GetValueList()) {
        $preamble = $encoding.GetPreamble();
        If ($preamble -and $bom) {
            Foreach ($i in 0..($preamble.Length - 1)) {
                If ($i -ge $bom.Length) {
                    break;
                }
                If ($preamble[$i] -ne $bom[$i]) {
                    break;
                }
                ElseIf ($i + 1 -eq $preamble.Length) {
                    $encodingobj = $encoding;
                    $found = $true;
                }
            }
            If ($found) {
                break;
            }
        }
    }
}

# Initialize result information
$result = @{
    backup  = "";
    changed = $false;
    msg     = "";
}

$cleanpath = $path.Replace("/", "\");
If (-not (Test-Path -LiteralPath $path)) {
    If ($state -eq "absent") {
        $result = @{
            changed = $false
            msg     = "File does not exist"
        };
        Exit-Json $result;
    }
    If (-not $create) {
        Fail-Json @{} "Path $path does not exist and create not specified";
    }
    $lines = New-Object System.Collections.ArrayList($null)
}
Else {
    # Read the dest file lines using the indicated encoding into a mutable ArrayList. Note
    # that we have to clean up the path because ansible wants to treat / and \ as
    # interchangeable in windows pathnames, but .NET framework internals do not support that.
    $origContent = [System.IO.File]::ReadAllText($cleanpath, $encodingobj);
    If (($null -eq $origContent) -or ($origContent -eq "")) {
        $lines = New-Object System.Collections.ArrayList;
    }
    Else {
        $lines = [System.Collections.ArrayList] ($origContent -split "\r\n|\r(?!\n)|\n");
    }
}

If ($diff_support) {
    $result.diff = @{
        before = $origContent
    }
}

# This logic lifted from Yaegashi Takeshi's (@yaegashi) blockinfile

$marker0 = $marker.Replace("{mark}", $marker_begin);
$marker1 = $marker.Replace("{mark}", $marker_end);

If (($state -eq "present") -and ($null -ne $block)) {
    $block = $block.Replace("`r", "");
    $blocklines = @($marker0) + $block.Split("`n") + @($marker1);
}
else {
    $blocklines = @();
}

$marker0Line = $null;
$marker1Line = $null;
$insertLine = $null;

For ($i = 0; $i -lt $lines.Count; $i++) {
    If ($lines[$i] -eq $marker0) {
        $marker0Line = $i;
    }
    If ($lines[$i] -eq $marker1) {
        $marker1Line = $i;
    }
    If ($null -ne $insre) {
        If ($insre.Match($lines[$i]).Success) {
            $insertLine = $i;
        }
    }
}

If (($null -eq $marker0Line) -Or ($null -eq $marker1Line)) {
    If ($null -ne $insre) {
        If ($null -eq $insertLine) {
            $insertLine = $lines.Count;
        }
        ElseIf ($insertafter) {
            $insertLine++;
        }
    }
    ElseIf (($insertbefore -eq "BOF") -Or ($insertafter -eq "BOF")) {
        $insertLine = 0;
    }
    Else {
        $insertLine = $lines.Count;
    }
}
ElseIf ($marker0Line -lt $marker1Line) {
    $insertLine = $marker0Line;
    $lines.RemoveRange($marker0Line, ($marker1Line - $marker0Line) + 1);
}
Else {
    $lines.RemoveRange($marker1Line, ($marker0Line - $marker1Line) + 1);
    $insertLine = $marker1Line;
}

$lines.InsertRange($insertLine, $blocklines);

$after = $lines -join $linesep;
If ($diff_support) {
    $result.diff.after = $after
}
$result.encoding = $encodingobj.WebName;

If ($origContent -ne $after) {
    $result.changed = $true;
    If ($backup) {
        $result.backup = BackupFile $path $check_mode
    }
    WriteLines $lines $path $linesep $encodingobj $validate $check_mode
    If ($blocklines.Count > 0) {
        $result.msg = "Block inserted"
    }
    else {
        $result.msg = "Block removed"
    }
}
Else {
    $result.changed = $false;
}

Exit-Json $result;
