#!powershell

# Copyright: (c) 2020, Harry Saryan  <hs-hub-world@github>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#Requires -Module Ansible.ModuleUtils.Legacy

<#
    Note:
        When hash is generated very first time a change will not be triggered (change=false). Subsequent executions will compare file hash to detect changes
        This module can be used for various register/trigger purposes to save time with other modules. For example this module can be used with choco package manager to detect repair/reinstall.
        Since choco by design does not detect file changes and reinstall always returns a change and it slows down the process this module can save huge time
        by detecting changes and trigger choco reinstall accordingly by restoring files back to their original state(s).

    Params:
    - Path  is the src path where files will be parsed and hash will be generated for each file
    - hashfilepath is optional, is the path where the actual hashes will be stored. this is auto generated
    - hashfileName is optional, is the file name where the actual hashes will be stored. this is auto generated
    - FilestoExclude is optiona, it's a list where you can define files to be excluded from being monitoried for changes
    - FilesToInclude takes precedence over filestoexclude, this will include monitor specific files only.
    - reset is boolean can be used to trigger a reset/regenerate hash file without triggering a change.
#>



$ErrorActionPreference = "Stop"
$params                = Parse-Args $args -supports_check_mode $true
$Path                  = Get-AnsibleParam -obj $params -name "path" -type "str" -failifempty $true
$hashfilepath          = Get-AnsibleParam -obj $params -name "hashfilepath" -type "str"
$hashfileName          = Get-AnsibleParam -obj $params -name "hashfilename" -type "str" -default ".ans_hash"
$FilestoExclude        = Get-AnsibleParam -obj $params -name "FilestoExclude" -type "list" -default ""
$FilesToInclude        = Get-AnsibleParam -obj $params -name "FilesToInclude" -type "list" -default "*"
$reset                 = Get-AnsibleParam -obj $params -name "reset" -type "bool"


$msg              = "";
$configchanged    = $false
$hashmatches      = $false
$ChangedFiles     = @()
$pathMissing      = $false
$hashfileexists   = $false
$NewHashGenerated = $false


if(test-path -LiteralPath "$Path")
{
    if(!$hashfilepath)
    {
        $hashfilepath="$($Path)\$($hashfileName)"
    }

    if($reset)
    {
        $msg +="`r`n Doing Reset."
        if(test-path -LiteralPath "$hashfilepath")
        {
            try {
                Remove-Item -LiteralPath "$hashfilepath" -Force -Confirm:$false
            }
            catch {
                $msg +="`r`n Reset failed, trying to delete $($hashfilepath)"
                Throw "`r`n Reset failed, trying to delete $($hashfilepath)"
            }
        }
    }

    try {
        ##############
        #READ FILES
        ###############
        $Files       = Get-ChildItem -Recurse "$Path" -Include $FilesToInclude -Exclude $FilestoExclude
    }
    catch {
        $msg +="`r`n Error trying to read "
        throw "Error with anonymousAuthentication:$($_.Exception.Message)"
    }

    if(!(test-path -LiteralPath "$hashfilepath"))
    {
        $msg +="`r`nHash not found, generating new hash file"
        #Config should NOT be changed when generating hash very first time...
        #Generate hash.
        try {
            ##############
            #GENERATE HASH
            ###############
            $Files |Where-Object{Test-path -LiteralPath $_.FullName -PathType Leaf} | ForEach-Object{Write-Output "File:$($_.FullName)|Hash:$($(Get-FileHash -LiteralPath $_.FullName).hash)"}|Out-File  "$hashfilepath" -Append
            $HashGenTime = (get-item -LiteralPath "$hashfilepath").CreationTime.ToString("MM/dd/yyyy HH:mm:ss.fff")
            $NewHashGenerated = $true
        }
        catch {
            throw "Error with windowsAuthentication:$($_.Exception.Message)"
        }
    }
    else {
        $hashfileexists   = $true
        $HashGenTime      = (get-item -LiteralPath "$hashfilepath").CreationTime.ToString("MM/dd/yyyy HH:mm:ss.fff")
        #Hash exists, do compare
        #Config should be considered changed when existing hash does not match...
        $msg +="`r`nHash file found, doing compare"

        foreach($LineHash in (Get-Content -LiteralPath "$hashfilepath"))
        {
            try {
                $HashString = (($LineHash -split("File:"))[1].Split("|"))
                if(test-path -LiteralPath "$($HashString[0])")
                {
                    $OrigHash = ("$($HashString[1])" -split(":"))[1]
                    if((Get-FileHash -LiteralPath "$($HashString[0])").Hash -ne "$OrigHash")
                    {
                        $configchanged=$true
                        $msg +="`r`n File changed: $($HashString[0])"
                        $ChangedFiles +=$HashString[0]
                        #break;
                    }
                }
                else {
                    $configchanged=$true
                    $msg +="`r`n File changed[missing]: $($HashString[0])"
                    $ChangedFiles +=$HashString[0]
                    #break;
                }
            }
            catch {
                $msg +="`r`n Failed at for line item:$($LineHash)"
                Throw "Hash compare failed for line item:$($LineHash)"
            }
        }
    }
}
else {
    $pathMissing=$true
    $msg +="`r`n Path not found:$($path)"
    $configchanged = $true;  #return change to trigger necessary even to install/create the path
    $hashmatches = $false
}

$hashmatches = ($configchanged -eq $false)

$result = @{
  path             = $path
  HashGenTime      = $HashGenTime
  FilestoExclude   = $FilestoExclude
  FilesToInclude   = $FilesToInclude
  NewHashGenerated = $NewHashGenerated
  hashfilepath     = $hashfilepath
  hashfileexists   = $hashfileexists
  pathmissing      = $pathMissing
  changed          = $configchanged
  hashmatches      = $hashmatches
  ChangedFiles     = $ChangedFiles
  message          = $msg
}
Exit-Json $result

