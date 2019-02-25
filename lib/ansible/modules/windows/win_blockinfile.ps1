#!powershell

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Module Ansible.ModuleUtils.Backup

# Large portions borrowed from Brian Lloyd's (@brianlloyd) win_lineinfile 
# and Yaegashi Takeshi's (@yaegashi) blockinfile

$spec = @{
    options = @{
        path = @{ type='path'; required=$true; aliases=@( "dest", "destfile", "name" )  }
        state = @{ type='str'; default='present'; choices=@( "absent", "present" ) }
        block = @{ type='str'; aliases=@( 'content' ) }
        insertafter = @{ type='str' }
        insertbefore = @{ type='str' }
        create = @{ type='bool'; default=$false }
        backup = @{ type='bool'; default=$false }
        encoding = @{ type='str'; default="auto" }
        newline = @{ type='str'; default="windows"; choices=@( "windows", "unix" ) }
        marker = @{ type='str'; default="# {mark} ANSIBLE MANAGED BLOCK" }
        marker_begin = @{ type='str'; default="BEGIN" }
        marker_end = @{ type='str'; default="END" }
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$path = $module.Params.path
$state = $module.Params.state
$block = $module.Params.block
$insertafter = $module.Params.insertafter
$insertbefore = $module.Params.insertbefore
$create = $module.Params.create
$backup = $module.Params.backup
$encoding = $module.Params.encoding
$newline = $module.Params.newline
$marker = $module.Params.marker
$marker_begin = $module.Params.marker_begin
$marker_end = $module.Params.marker_end

$check_mode = $module.CheckMode
$diff_support = $module.Diff

function WriteLines {
    param(
        [System.Collections.ArrayList]$outlines,
        [String]$path,
        [String]$linesep,
        [Object]$encodingobj,
        [bool]$check_mode
    );

    $acl = $null

    Try {
        If (Test-Path -LiteralPath $path) {
            $acl = Get-Acl -LiteralPath $path
        }
    }
    Catch {
        $module.FailJson("Cannot get ACL from original file! ($($_.Exception.Message))", $_);
    }

    Try {
        $temppath = [System.IO.Path]::GetTempFileName();
    }
    Catch {
        $module.FailJson("Cannot create temporary file! ($($_.Exception.Message))", $_);
    }

    Try {
        $joined = $outlines -join $linesep;
        [System.IO.File]::WriteAllText($temppath, $joined, $encodingobj);

        Try {
            Move-Item -LiteralPath $temppath -Destination $path -force -ErrorAction Stop -WhatIf:$check_mode;
        }
        Catch {
            $module.FailJson("Cannot write to: $path ($($_.Exception.Message))", $_);
        }

        If ($acl) {
            Try {
                Set-Acl -LiteralPath $path -AclObject $acl -WhatIf:$check_mode 
            }
            Catch {
                $module.FailJson("Cannot set ACL on new file! ($($_.Exception.Message))", $_);
            }
        }
        return $joined;
    }
    Finally {
        If (Test-Path -LiteralPath $temppath) {
            Remove-Item -LiteralPath $temppath -Force
        }
    }

}

function GuessFileEncoding {
    param([String]$path);

    # The default encoding is UTF-8 without BOM
    $encodingObject = [System.Text.UTF8Encoding] $false;

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
                    $encodingObject = $encoding;
                    $found = $true;
                }
            }
            If ($found) {
                break;
            }
        }
    }
    return $encodingObject;
}

If (Test-Path -LiteralPath $path -PathType "container") {
    $module.FailJson("Path $path is a directory", $_);
}

$linesep = "`r`n"
If ($newline -eq "unix") {
    $linesep = "`n";
}

If ($insertbefore -and $insertafter) {
    $module.Warn("Both insertbefore and insertafter parameters found, ignoring `"insertafter=$insertafter`"")
}

If (-not $insertbefore -and -not $insertafter) {
    $insertafter = "EOF";
}

$insre = $null;
If ($insertafter -and $insertafter -ne "BOF" -and $insertafter -ne "EOF") {
    $insre = New-Object Regex $insertafter, 'Compiled';
}
ElseIf ($insertbefore -and $insertbefore -ne "BOF" -and $insertbefore -ne "EOF") {
    $insre = New-Object Regex $insertbefore, 'Compiled';
}


# The default encoding is UTF-8 without BOM
$encodingobj = [System.Text.UTF8Encoding] $false;

If ($encoding -ne "auto") {
    $encodingobj = [System.Text.Encoding]::GetEncoding($encoding);
}
ElseIf (Test-Path -LiteralPath $path) {
    $encodingobj = GuessFileEncoding $path

}

$module.Result.backup = ""
$module.Result.changed = $false
$module.Result.msg = ""

$cleanpath = $path.Replace("/", "\");
If (-not (Test-Path -LiteralPath $path)) {
    If ($state -eq "absent") {
        $module.Result.changed = $false
        $module.Result.msg = "File does not exist"
        $module.ExitJson()
    }
    If (-not $create) {
        $module.FailJson("Path $path does not exist and create not specified", $_);
    }
    $lines = New-Object System.Collections.ArrayList($null)
}
Else {
    # Read the dest file lines using the indicated encoding into a mutable ArrayList. Note
    # that we have to clean up the path because ansible wants to treat / and \ as
    # interchangeable in windows pathnames, but .NET framework internals do not support that.

    # We read the file using ReadAllText in order to preserve ending newlines
    $origContent = [System.IO.File]::ReadAllText($cleanpath, $encodingobj);
    If (($null -eq $origContent) -or ($origContent -eq "")) {
        $lines = New-Object System.Collections.ArrayList;
    }
    Else {
        $lines = [System.Collections.ArrayList] ($origContent -split "\r\n|\r(?!\n)|\n");
    }
}

If ($diff_support) {
    $module.Diff.before = $origContent
}

# This logic lifted from Yaegashi Takeshi's (@yaegashi) blockinfile

$marker0 = $marker.Replace("{mark}", $marker_begin);
$marker1 = $marker.Replace("{mark}", $marker_end);

If (($state -eq "present") -and ($null -ne $block)) {
    $block = $block.Replace("`r", "");
    $blocklines = @($marker0) + ($block -split "\r\n|\r(?!\n)|\n") + @($marker1);
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
    If ($null -ne $insre -and ($lines[$i] -match $insre)) {
        $insertLine = $i;
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
    $module.Diff.after = $after
}
$module.Result.encoding = $encodingobj.WebName;

If ($origContent -ne $after) {
    $module.Result.changed = $true;
    If ($backup) {
        $module.Result.backup_file = Backup-File -path $path -WhatIf:$check_mode
    }
    WriteLines $lines $path $linesep $encodingobj $check_mode
    If ($blocklines.Count -gt 0) {
        $module.Result.msg = "Block inserted"
    }
    else {
        $module.Result.msg = "Block removed"
    }
}
Else {
    $module.Result.changed = $false;
}

$module.ExitJson();
