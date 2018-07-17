#!powershell

# Copyright: (c) 2015, Jon Hawkesworth (@jhawkesworth) <figs@unity.demon.co.uk>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

Function Convert-RegistryPath {
    Param (
        [parameter(Mandatory=$True)]
        [ValidateNotNullOrEmpty()]$Path
    )

    $output = $Path -replace "HKLM:", "HKLM"
    $output = $output -replace "HKCU:", "HKCU" 

    Return $output
}

$result = @{
    changed = $false
}
$params = Parse-Args $args

$path = Get-AnsibleParam -obj $params -name "path" -type "path" -failifempty $true -resultobj $result
$compare_to = Get-AnsibleParam -obj $params -name "compare_to" -type "str" -resultobj $result

# check it looks like a reg key, warn if key not present - will happen first time
# only accepting PS-Drive style key names (starting with HKLM etc, not HKEY_LOCAL_MACHINE etc)

$do_comparison = $False

If ($compare_to) {
    $compare_to_key = $params.compare_to.ToString()
    If (Test-Path $compare_to_key -pathType container ) {
        $do_comparison = $True
    } Else {
        $result.compare_to_key_found = $false
    }
}

If ( $do_comparison -eq $True ) {
  $guid = [guid]::NewGuid()
  $exported_path = $env:TEMP + "\" + $guid.ToString() + 'ansible_win_regmerge.reg'

  $expanded_compare_key = Convert-RegistryPath ($compare_to_key) 

  # export from the reg key location to a file
  $reg_args = @("EXPORT", "$expanded_compare_key", $exported_path)
  & reg.exe $reg_args

  # compare the two files
  $comparison_result = Compare-Object -ReferenceObject $(Get-Content $path) -DifferenceObject $(Get-Content $exported_path)

  If (Get-Member -InputObject $comparison_result -Name "count" -MemberType Properties )
  {
     # Something is different, actually do reg merge
     $reg_import_args = @("IMPORT", "$path")
     $ret = & reg.exe $reg_import_args 2>&1
     If ($LASTEXITCODE -eq 0) {
         $result.changed = $true
         $result.difference_count = $comparison_result.count
     } Else {
         $result.rc = $LASTEXITCODE
         Fail-Json $result "$ret"
     }
  } Else {
      $result.difference_count = 0
  }

  Remove-Item $exported_path
  $result.compared = $true

} Else {
     # not comparing, merge and report changed
     $reg_import_args = @("IMPORT", "$path")
     $ret = & reg.exe $reg_import_args 2>&1
     If ( $LASTEXITCODE -eq 0 ) {
         $result.changed = $true
         $result.compared = $false
     } Else {
         $result.rc = $LASTEXITCODE
         Fail-Json $result "$ret"
     }
}

Exit-Json $result
