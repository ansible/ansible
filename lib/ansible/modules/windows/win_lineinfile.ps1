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


# Write lines to a file using the specified line separator and encoding,
# performing validation if a validation command was specified.
function WriteLines($outlines, $path, $linesep, $encodingobj, $validate, $check_mode) {
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

	Try {
		Remove-Item $temppath -force -ErrorAction Stop -WhatIf:$check_mode;
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
	return $backuppath;
}


# Implement the functionality for state == 'present'
function Present($path, $regexp, $line, $insertafter, $insertbefore, $create, $backup, $backrefs, $validate, $encodingobj, $linesep, $check_mode, $diff_support) {

	# Note that we have to clean up the path because ansible wants to treat / and \ as
	# interchangeable in windows pathnames, but .NET framework internals do not support that.
	$cleanpath = $path.Replace("/", "\");

	# Check if path exists. If it does not exist, either create it if create == "yes"
	# was specified or fail with a reasonable error message.
	If (-not (Test-Path -Path $path)) {
		If (-not $create) {
			Fail-Json @{} "Path $path does not exist !";
		}
		# Create new empty file, using the specified encoding to write correct BOM
		[System.IO.File]::WriteAllLines($cleanpath, "", $encodingobj);
	}

	# Initialize result information
	$result = @{
		backup = "";
		changed = $false;
		msg = "";
	}

	# Read the dest file lines using the indicated encoding into a mutable ArrayList.
	$before = [System.IO.File]::ReadAllLines($cleanpath, $encodingobj)
	If ($before -eq $null) {
		$lines = New-Object System.Collections.ArrayList;
	}
	Else {
		$lines = [System.Collections.ArrayList] $before;
	}

	if ($diff_support) {
		$result.diff = @{
			before = $before -join $linesep;
		}
	}

	# Compile the regex specified, if provided
	$mre = $null;
	If ($regexp) {
		$mre = New-Object Regex $regexp, 'Compiled';
	}

	# Compile the regex for insertafter or insertbefore, if provided
	$insre = $null;
	If ($insertafter -and $insertafter -ne "BOF" -and $insertafter -ne "EOF") {
		$insre = New-Object Regex $insertafter, 'Compiled';
	}
	ElseIf ($insertbefore -and $insertbefore -ne "BOF") {
		$insre = New-Object Regex $insertbefore, 'Compiled';
	}

	# index[0] is the line num where regexp has been found
	# index[1] is the line num where insertafter/inserbefore has been found
	$index = -1, -1;
	$lineno = 0;

	# The latest match object and matched line
	$matched_line = "";

	# Iterate through the lines in the file looking for matches
	Foreach ($cur_line in $lines) {
		If ($regexp) {
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
		ElseIf ($insre -and $insre.Match($cur_line).Success) {
			If ($insertafter) {
				$index[1] = $lineno + 1;
			}
			If ($insertbefore) {
				$index[1] = $lineno;
			}
		}
		$lineno = $lineno + 1;
	}

	If ($index[0] -ne -1) {
		If ($backrefs) {
		    $new_line = [regex]::Replace($matched_line, $regexp, $line);
		}
		Else {
			$new_line = $line;
		}
		If ($lines[$index[0]] -cne $new_line) {
			$lines[$index[0]] = $new_line;
			$result.changed = $true;
			$result.msg = "line replaced";
		}
	}
	ElseIf ($backrefs) {
		# No matches - no-op
	}
	ElseIf ($insertbefore -eq "BOF" -or $insertafter -eq "BOF") {
		$lines.Insert(0, $line);
		$result.changed = $true;
		$result.msg = "line added";
	}
	ElseIf ($insertafter -eq "EOF" -or $index[1] -eq -1) {
		$lines.Add($line);
		$result.changed = $true;
		$result.msg = "line added";
	}
	Else {
		$lines.Insert($index[1], $line);
		$result.changed = $true;
		$result.msg = "line added";
	}

	# Write changes to the path if changes were made
	If ($result.changed) {

		# Write backup file if backup == "yes"
		If ($backup) {
			$result.backup = BackupFile $path $check_mode;
		}

		$after = WriteLines $lines $path $linesep $encodingobj $validate $check_mode;

		if ($diff_support) {
			$result.diff.after = $after;
		}
	}

	$result.encoding = $encodingobj.WebName;

	Exit-Json $result;
}


# Implement the functionality for state == 'absent'
function Absent($path, $regexp, $line, $backup, $validate, $encodingobj, $linesep, $check_mode, $diff_support) {

	# Check if path exists. If it does not exist, fail with a reasonable error message.
	If (-not (Test-Path -Path $path)) {
		Fail-Json @{} "Path $path does not exist !";
	}

	# Initialize result information
	$result = @{
		backup = "";
		changed = $false;
		msg = "";
	}

	# Read the dest file lines using the indicated encoding into a mutable ArrayList. Note
	# that we have to clean up the path because ansible wants to treat / and \ as
	# interchangeable in windows pathnames, but .NET framework internals do not support that.
	$cleanpath = $path.Replace("/", "\");
	$before = [System.IO.File]::ReadAllLines($cleanpath, $encodingobj);
	If ($before -eq $null) {
		$lines = New-Object System.Collections.ArrayList;
	}
	Else {
		$lines = [System.Collections.ArrayList] $before;
	}

	if ($diff_support) {
		$result.diff = @{
			before = $before -join $linesep;
		}
	}

	# Compile the regex specified, if provided
	$cre = $null;
	If ($regexp) {
		$cre = New-Object Regex $regexp, 'Compiled';
	}

	$found = New-Object System.Collections.ArrayList;
	$left = New-Object System.Collections.ArrayList;

	Foreach ($cur_line in $lines) {
		If ($regexp) {
			$m = $cre.Match($cur_line);
			$match_found = $m.Success;
		}
		Else {
			$match_found = $line -ceq $cur_line;
		}
		If ($match_found) {
			$found.Add($cur_line);
			$result.changed = $true;
		}
		Else {
			$left.Add($cur_line);
		}
	}

	# Write changes to the path if changes were made
	If ($result.changed) {

		# Write backup file if backup == "yes"
		If ($backup) {
			$result.backup = BackupFile $path $check_mode;
		}

		$after = WriteLines $left $path $linesep $encodingobj $validate $check_mode;

		if ($diff_support) {
			$result.diff.after = $after;
		}
	}

	$result.encoding = $encodingobj.WebName;
	$result.found = $found.Count;
	$result.msg = "$($found.Count) line(s) removed";

	Exit-Json $result;
}


# Parse the parameters file dropped by the Ansible machinery
$params = Parse-Args $args -supports_check_mode $true;
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false;
$diff_support = Get-AnsibleParam -obj $params -name "_ansible_diff" -type "bool" -default $false;

# Initialize defaults for input parameters.
$path = Get-AnsibleParam -obj $params -name "path" -type "path" -failifempty $true -aliases "dest","destfile","name";
$regexp = Get-AnsibleParam -obj $params -name "regexp" -type "str";
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present","absent";
$line = Get-AnsibleParam -obj $params -name "line" -type "str";
$backrefs = Get-AnsibleParam -obj $params -name "backrefs" -type "bool" -default $false;
$insertafter = Get-AnsibleParam -obj $params -name "insertafter" -type "str";
$insertbefore = Get-AnsibleParam -obj $params -name "insertbefore" -type "str";
$create = Get-AnsibleParam -obj $params -name "create" -type "bool" -default $false;
$backup = Get-AnsibleParam -obj $params -name "backup" -type "bool" -default $false;
$validate = Get-AnsibleParam -obj $params -name "validate" -type "str";
$encoding = Get-AnsibleParam -obj $params -name "encoding" -type "str" -default "auto";
$newline = Get-AnsibleParam -obj $params -name "newline" -type "str" -default "windows" -validateset "unix","windows";

# Fail if the path is not a file
If (Test-Path -Path $path -PathType "container") {
	Fail-Json @{} "Path $path is a directory";
}

# Default to windows line separator - probably most common
$linesep = "`r`n"
If ($newline -eq "unix") {
	$linesep = "`n";
}

# Fix any CR/LF literals in the line argument. PS will not recognize either backslash
# or backtick literals in the incoming string argument without this bit of black magic.
If ($line) {
	$line = $line.Replace("\r", "`r");
	$line = $line.Replace("\n", "`n");
	$line = $line.Replace("``r", "`r");
	$line = $line.Replace("``n", "`n");
}

# Figure out the proper encoding to use for reading / writing the target file.

# The default encoding is UTF-8 without BOM
$encodingobj = [System.Text.UTF8Encoding] $false;

# If an explicit encoding is specified, use that instead
If ($encoding -ne "auto") {
	$encodingobj = [System.Text.Encoding]::GetEncoding($encoding);
}

# Otherwise see if we can determine the current encoding of the target file.
# If the file doesn't exist yet (create == 'yes') we use the default or
# explicitly specified encoding set above.
ElseIf (Test-Path -Path $path) {

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
	[Byte[]]$bom = Get-Content -Encoding Byte -ReadCount $max_preamble_len -TotalCount $max_preamble_len -Path $path;

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


# Main dispatch - based on the value of 'state', perform argument validation and
# call the appropriate handler function.
If ($state -eq "present") {

	If ($backrefs -and -not $regexp) {
	    Fail-Json @{} "regexp= is required with backrefs=true";
	}

	If (-not $line) {
		Fail-Json @{} "line= is required with state=present";
	}

	If ($insertbefore -and $insertafter) {
		Add-Warning $result "Both insertbefore and insertafter parameters found, ignoring `"insertafter=$insertafter`""
	}

	If (-not $insertbefore -and -not $insertafter) {
		$insertafter = "EOF";
	}

	Present $path $regexp $line $insertafter $insertbefore $create $backup $backrefs $validate $encodingobj $linesep $check_mode $diff_support;

}
ElseIf ($state -eq "absent") {

	If (-not $regexp -and -not $line) {
		Fail-Json @{} "one of line= or regexp= is required with state=absent";
	}

	Absent $path $regexp $line $backup $validate $encodingobj $linesep $check_mode $diff_support;
}
