#!powershell
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# WANT_JSON
# POWERSHELL_COMMON


# Parse the parameters file dropped by the Ansible machinery

$params = Parse-Args $args;


# Initialize defaults for input parameters.

$dest= Get-Attr $params "dest" $FALSE;
$regexp = Get-Attr $params "regexp" $FALSE;
$state = Get-Attr $params "state" "present";
$line = Get-Attr $params "line" $FALSE;
$backrefs = Get-Attr $params "backrefs" "no";
$insertafter = Get-Attr $params "insertafter" $FALSE;
$insertbefore = Get-Attr $params "insertbefore" $FALSE;
$create = Get-Attr $params "create" "no";
$backup = Get-Attr $params "backup" "no";
$validate = Get-Attr $params "validate" $FALSE;
$encoding = Get-Attr $params "encoding" "auto";
$newline = Get-Attr $params "newline" "windows";


# Parse dest / name /destfile param aliases for compatibility with lineinfile
# and fail if at least one spelling of the parameter is not provided.

$dest = Get-Attr $params "dest" $FALSE;
If ($dest -eq $FALSE) {
    $dest = Get-Attr $params "name" $FALSE;
    If ($dest -eq $FALSE) {
        $dest = Get-Attr $params "destfile" $FALSE;
        If ($dest -eq $FALSE) {
            Fail-Json (New-Object psobject) "missing required argument: dest";
        }
    }
}


# Fail if the destination is not a file

If (Test-Path $dest -pathType container) {
    Fail-Json (New-Object psobject) "destination is a directory";
}


# Write lines to a file using the specified line separator and encoding, 
# performing validation if a validation command was specified.

function WriteLines($outlines, $dest, $linesep, $encodingobj, $validate) {
	$temppath = [System.IO.Path]::GetTempFileName();
	$joined = $outlines -join $linesep;
	[System.IO.File]::WriteAllText($temppath, $joined, $encodingobj);
	
	If ($validate -ne $FALSE) {
		
		If (!($validate -like "*%s*")) {
			Fail-Json (New-Object psobject) "validate must contain %s: $validate";
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
			Fail-Json (New-Object psobject) "failed to validate $cmdname $cmdargs with error: $output $error";
		}

	}
	
	# Commit changes to the destination file
	$cleandest = $dest.Replace("/", "\");
	Copy-Item $temppath $cleandest -force;	
	Remove-Item $temppath -force;
}


# Backup the file specified with a date/time filename

function BackupFile($path) {
	$backuppath = $path + "." + [DateTime]::Now.ToString("yyyyMMdd-HHmmss");
	Copy-Item $path $backuppath;
	return $backuppath;
}



# Implement the functionality for state == 'present'

function Present($dest, $regexp, $line, $insertafter, $insertbefore, $create, $backup, $backrefs, $validate, $encodingobj, $linesep) {

	# Note that we have to clean up the dest path because ansible wants to treat / and \ as 
	# interchangable in windows pathnames, but .NET framework internals do not support that.
	$cleandest = $dest.Replace("/", "\");

	# Check if destination exists. If it does not exist, either create it if create == "yes"
	# was specified or fail with a reasonable error message.
	If (!(Test-Path $dest)) {
		If ($create -eq "no") {
			Fail-Json (New-Object psobject) "Destination $dest does not exist !";
		}
		# Create new empty file, using the specified encoding to write correct BOM
		[System.IO.File]::WriteAllLines($cleandest, "", $encodingobj);
	}

	# Read the dest file lines using the indicated encoding into a mutable ArrayList.
    $content = [System.IO.File]::ReadAllLines($cleandest, $encodingobj);
    If ($content -eq $null) {
		$lines = New-Object System.Collections.ArrayList;
	}
	Else {
		$lines = [System.Collections.ArrayList] $content;
	}
	
	# Compile the regex specified, if provided
	$mre = $FALSE;
	If ($regexp -ne $FALSE) {
		$mre = New-Object Regex $regexp, 'Compiled';
	}
	
	# Compile the regex for insertafter or insertbefore, if provided
	$insre = $FALSE;
	
	If ($insertafter -ne $FALSE -and $insertafter -ne "BOF" -and $insertafter -ne "EOF") {
		$insre = New-Object Regex $insertafter, 'Compiled';
	}
	ElseIf ($insertbefore -ne $FALSE -and $insertbefore -ne "BOF") {
		$insre = New-Object Regex $insertbefore, 'Compiled';
	}

    # index[0] is the line num where regexp has been found
    # index[1] is the line num where insertafter/inserbefore has been found
	$index = -1, -1;
	$lineno = 0;
	
	# The latest match object and matched line
	$matched_line = "";
	$m = $FALSE;

	# Iterate through the lines in the file looking for matches
	Foreach ($cur_line in $lines) {
		If ($regexp -ne $FALSE) {
			$m = $mre.Match($cur_line);
			$match_found = $m.Success;
			If ($match_found) {
				$matched_line = $cur_line;
			}
		}
		Else {
			$match_found = $line -ceq $cur_line;
		}
		If ($match_found) {
			$index[0] = $lineno;
		}
		ElseIf ($insre -ne $FALSE -and $insre.Match($cur_line).Success) {
			If ($insertafter -ne $FALSE) {
				$index[1] = $lineno + 1;
			}
			If ($insertbefore -ne $FALSE) {
				$index[1] = $lineno;
			}	
		}
		$lineno = $lineno + 1;
	}
	
	$changed = $FALSE;
	$msg = "";

	If ($index[0] -ne -1) {
		If ($backrefs -ne "no") {
		    $new_line = [regex]::Replace($matched_line, $regexp, $line);
		}
		Else {
			$new_line = $line;
		}
		If ($lines[$index[0]] -cne $new_line) {
			$lines[$index[0]] = $new_line;
			$msg = "line replaced";
			$changed = $TRUE;
		}
	}
	ElseIf ($backrefs -ne "no") {
		# No matches - no-op
	}
	ElseIf ($insertbefore -eq "BOF" -or $insertafter -eq "BOF") {
		$lines.Insert(0, $line);
		$msg = "line added";
		$changed = $TRUE;
	}
	ElseIf ($insertafter -eq "EOF" -or $index[1] -eq -1) {
		$lines.Add($line);
		$msg = "line added";
		$changed = $TRUE;
	}
	Else {
		$lines.Insert($index[1], $line);
		$msg = "line added";
		$changed = $TRUE;
	}

	# Write backup file if backup == "yes"
    $backupdest = "";

	If ($changed -eq $TRUE -and $backup -eq "yes") {
		$backupdest = BackupFile $dest;
	}
	
	# Write changes to the destination file if changes were made
	If ($changed) {
		WriteLines $lines $dest $linesep $encodingobj $validate;
	}

	$encodingstr = $encodingobj.WebName;

	# Return result information
	$result = New-Object psobject @{
    	changed = $changed
		msg = $msg
		backup = $backupdest
		encoding = $encodingstr
	}
	
	Exit-Json $result;
}


# Implement the functionality for state == 'absent'

function Absent($dest, $regexp, $line, $backup, $validate, $encodingobj, $linesep) {

	# Check if destination exists. If it does not exist, fail with a reasonable error message.
	If (!(Test-Path $dest)) {
		Fail-Json (New-Object psobject) "Destination $dest does not exist !";
	}

	# Read the dest file lines using the indicated encoding into a mutable ArrayList. Note
	# that we have to clean up the dest path because ansible wants to treat / and \ as 
	# interchangeable in windows pathnames, but .NET framework internals do not support that.
	 
	$cleandest = $dest.Replace("/", "\");
    $content = [System.IO.File]::ReadAllLines($cleandest, $encodingobj);
    If ($content -eq $null) {
		$lines = New-Object System.Collections.ArrayList;
	}
	Else {
		$lines = [System.Collections.ArrayList] $content;
	}
	
	# Initialize message to be returned on success
	$msg = "";

	# Compile the regex specified, if provided
	$cre = $FALSE;
	If ($regexp -ne $FALSE) {
		$cre = New-Object Regex $regexp, 'Compiled';
	}

	$found = New-Object System.Collections.ArrayList;
	$left = New-Object System.Collections.ArrayList;
	$changed = $FALSE;

	Foreach ($cur_line in $lines) {
		If ($cre -ne $FALSE) {
			$m = $cre.Match($cur_line);
			$match_found = $m.Success;
		}
		Else {
			$match_found = $line -ceq $cur_line;
		}
		If ($match_found) {
			$found.Add($cur_line);
			$changed = $TRUE;
		}
		Else {
			$left.Add($cur_line);
		}
	}

	# Write backup file if backup == "yes"
    $backupdest = "";

	If ($changed -eq $TRUE -and $backup -eq "yes") {
		$backupdest = BackupFile $dest;
	}
	
	# Write changes to the destination file if changes were made
	If ($changed) {
		WriteLines $left $dest $linesep $encodingobj $validate;
	}

	# Return result information
	$fcount = $found.Count;
	$msg = "$fcount line(s) removed";
	$encodingstr = $encodingobj.WebName;

	$result = New-Object psobject @{
    	changed = $changed
		msg = $msg
		backup = $backupdest
		found = $fcount
		encoding = $encodingstr
	}
	
	Exit-Json $result;
}


# Default to windows line separator - probably most common

$linesep = "`r`n";

If ($newline -ne "windows") {
	$linesep = "`n";
}


# Fix any CR/LF literals in the line argument. PS will not recognize either backslash
# or backtick literals in the incoming string argument without this bit of black magic.

If ($line -ne $FALSE) {
	$line = $line.Replace("\r", "`r");
	$line = $line.Replace("\n", "`n");
}


# Figure out the proper encoding to use for reading / writing the target file.

# The default encoding is UTF-8 without BOM
$encodingobj = [System.Text.UTF8Encoding] $FALSE;

# If an explicit encoding is specified, use that instead
If ($encoding -ne "auto") {
	$encodingobj = [System.Text.Encoding]::GetEncoding($encoding);
}

# Otherwise see if we can determine the current encoding of the target file.
# If the file doesn't exist yet (create == 'yes') we use the default or 
# explicitly specified encoding set above.
Elseif (Test-Path $dest) {

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
			$sortedlist.Add(-($plen * 1000000 + $encoding.CodePage), $encoding);
		}
	}

	# Get the first N bytes from the file, where N is the max preamble length we saw
	
	[Byte[]]$bom = Get-Content -Encoding Byte -ReadCount $max_preamble_len -TotalCount $max_preamble_len -Path $dest;
  
	# Iterate through the sorted encodings, looking for a full match.
	
	$found = $FALSE;
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
				Elseif ($i + 1 -eq $preamble.Length) {
					$encodingobj = $encoding;
					$found = $TRUE;
				}
			}
			If ($found) {
				break;
			}
		}
	}
}


# Main dispatch - based on the value of 'state', perform argument validation and 
# call the appropriate handler function.

If ($state -eq "present") {

	If ( $backrefs -ne "no" -and $regexp -eq $FALSE ) {
	    Fail-Json (New-Object psobject) "regexp= is required with backrefs=true";
	}
	
	If ($line -eq $FALSE) {
		Fail-Json (New-Object psobject) "line= is required with state=present";
	}
	
	If ($insertbefore -eq $FALSE -and $insertafter -eq $FALSE) {
		$insertafter = "EOF";
	}

	Present $dest $regexp $line $insertafter $insertbefore $create $backup $backrefs $validate $encodingobj $linesep;

}
Else {

	If ($regexp -eq $FALSE -and $line -eq $FALSE) {
		Fail-Json (New-Object psobject) "one of line= or regexp= is required with state=absent";
	}
	
	Absent $dest $regexp $line $backup $validate $encodingobj $linesep;
}

















