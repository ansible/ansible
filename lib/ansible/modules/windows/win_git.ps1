#!powershell

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Anatoliy Ivashina <tivrobo@gmail.com>
# Pablo Estigarribia <pablodav@gmail.com>
# Michael Hay <project.hay@gmail.com>
# Ripon Banik <ripon.banik@gmail.com>

#Requires -Module Ansible.ModuleUtils.Legacy

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode  = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

# Module Params
$repo = Get-AnsibleParam -obj $params -name "repo"  -type "str" -failifempty $true -aliases "name"
$dest = Get-AnsibleParam -obj $params -name "dest"  -type "str" 
$remote = Get-AnsibleParam -obj $params -name "remote" -type "str" -default "origin"
$version = Get-AnsibleParam -obj $params -name "version" -type "str" -default "HEAD"
$clone = ConvertTo-Bool (Get-AnsibleParam -obj $params -name "clone" -default $true)
$update = ConvertTo-Bool (Get-AnsibleParam -obj $params -name "update" -default $false)
$replace_dest = ConvertTo-Bool (Get-AnsibleParam -obj $params -name "replace_dest" -default $false)
$accept_hostkey = ConvertTo-Bool (Get-AnsibleParam -obj $params -name "accept_hostkey" -default $true)
$depth =  Get-AnsibleParam -obj $params -name "depth"  -type "int" -default $null
$key_file = Get-AnsibleParam -obj $params -name "key_file" -type "str"

$result = @{      
    changed = $false    
    dest = $null        
    status =  $null      
    git_output = $null
    return_code = $null
    method = $null
    branch_status = "master"
    git_opts = $null
}

# Add Git to PATH variable
# Test with git 2.14
$env:Path += ";" + "C:\Program Files\Git\bin"
$env:Path += ";" + "C:\Program Files\Git\usr\bin"
$env:Path += ";" + "C:\Program Files (x86)\Git\bin"
$env:Path += ";" + "C:\Program Files (x86)\Git\usr\bin"
$env:Path += ";" + "C:\Program Files\Git\cmd"
$env:Path += ";" + "C:\Program Files (x86)\Git\cmd"

# Functions
function Find-Command {
    [CmdletBinding()]
    param(
      [Parameter(Mandatory=$true, Position=0)] [string] $command
    )
    $installed = get-command $command -erroraction Ignore
    write-verbose "$installed"
    if ($installed){
        return $installed
    }
    return $null
}

function FindGit {
    [CmdletBinding()]
    param()
    $p = Find-Command "git.exe"
    if ($p -ne $null){
        $path=((Get-Command git.exe).Path | Split-Path)
        $env:Path += ";" + $path
        Set-Attr $result "status" "Git found in $path"
        return $p
    }
    Fail-Json -obj $result -message "git.exe is not installed. It must be installed (use chocolatey)"
}

# Remove dest if it exests
function PrepareDestination {
    [CmdletBinding()]
    param()
    if ((Test-Path $dest) -And (-Not $check_mode)) {
        try {
            Remove-Item $dest -Force -Recurse | Out-Null            
            if (-Not (Test-Path($dest))) {
               New-Item -ItemType directory -Path $dest      
            }
            Set-Attr $result "status" "Successfully replaced dir $dest"
            Set-Attr $result "changed" $true            
        } catch {
            $ErrorMessage = $_.Exception.Message
            Fail-Json $result "Error removing $dest! Msg: $ErrorMessage"
        }
    }
}

# SSH Keys
function CheckSshKnownHosts {
    [CmdletBinding()]
    param()
    # Get the Git Hostrepo
    $gitServer = $($repo -replace "^(\w+)\@([\w-_\.]+)\:(.*)$", '$2')
    $gitHome = ((Get-Command git.exe).Path | Split-Path | Split-Path)
    $gitKeyGenPath = Join-Path -Path $gitHome -ChildPath /usr/bin/ssh-keygen.exe
    $gitKeyScanPath = Join-Path -Path $gitHome -ChildPath /usr/bin/ssh-keyscan.exe
    $gitKeyAddPath = Join-Path -Path $gitHome -ChildPath /usr/bin/ssh-add.exe
   
    & cmd /c $gitKeyGenPath -F $gitServer | Out-Null
    $rc = $LASTEXITCODE

    if ($rc -ne 0) {    
        if (-Not (Test-Path -Path $env:Userprofile\.ssh\known_hosts)) {   
           New-Item -ItemType file -Path $env:Userprofile\.ssh\known_hosts
        }   
    }    
    
    # SSH Known Host Config        
    if ($accept_hostkey){
        # workaround for disable BOM
        # https://github.com/tivrobo/ansible-win_git/issues/7
        $sshHostKey = & cmd /c $gitKeyScanPath -t ssh-rsa $gitServer
        $sshHostKey += "`n"                
        $sshKnownHostsPath = Join-Path -Path $env:Userprofile -ChildPath \.ssh\known_hosts
        $key_search = Get-Content -Path $sshKnownHostsPath  | Select-String "$gitServer" 
        if ([string]::IsNullOrEmpty($key_search)) {
            try {  
                [System.IO.File]::AppendAllText($sshKnownHostsPath, $sshHostKey, $(New-Object System.Text.UTF8Encoding $False))
                Set-Attr $result "status" "Successfully updated $sshKnownHostsPath"
            }
            catch {
               $ErrorMessage = $_.Exception.Message
               Fail-Json $result "Error updating $sshKnownHostsPath Msg: $ErrorMessage"               
            }               
        }  
        else {
            Set-Attr $result "status" "No update to $sshKnownHostsPath. $key_search exits"
        }    
    }
    else {
        Fail-Json -obj $result -message  "Host is not known!"
    }      

    # SSH Private Key Config for Host
    if (Test-Path -Path $key_file){
        $sshConfigPath = Join-Path -Path ((Get-Command git.exe).Path | Split-Path | Split-Path) -ChildPath /etc/ssh/ssh_config
        $key_search = Get-Content -Path $sshConfigPath  | Select-String "Host $gitServer" 
        
        if (-Not (Test-Path -Path $env:Userprofile\.ssh)) { New-Item -ItemType directory -Path $env:Userprofile\.ssh }        
        if (-Not (Test-Path -Path $env:Userprofile\.ssh\id_rsa)) {
          Get-Content -Path $key_file | Set-Content -Path $env:Userprofile\.ssh\id_rsa                           
        }         
        # Add Host Config if not exists
        if ([string]::IsNullOrEmpty($key_search)) {               
            try {
              [System.IO.File]::AppendAllText($sshConfigPath, "Host $gitServer`n", $(New-Object System.Text.UTF8Encoding $False))
              [System.IO.File]::AppendAllText($sshConfigPath, "IdentityFile $key_file", $(New-Object System.Text.UTF8Encoding $False))       
              Set-Attr $result "status" "Successfully updated $sshConfigPath"
            }
            catch {
                $ErrorMessage = $_.Exception.Message
                Fail-Json $result "Error updating $sshConfigPath Msg: $ErrorMessage"
            }            
        }   
        else {
            Set-Attr $result "status" "No update to $sshConfigPath. $key_search exits"
        }         
        & cmd /c start-ssh-agent.cmd | Out-Null
        & cmd /c $gitKeyAddPath $env:Userprofile\.ssh\id_rsa      

    }
    else {
        Fail-Json -obj $result -message  "Key Path not found!"
    }    
    
}


function CheckSshIdentity {
    [CmdletBinding()]
    param()

    & cmd /c git.exe ls-remote $repo | Out-Null
    $rc = $LASTEXITCODE
    if ($rc -ne 0) {
        Fail-Json -obj $result -message  "Something wrong with connection!"
    }
}

function CheckPath {
    [CmdletBinding()]
    param(
      [Parameter(Mandatory=$true, Position=0)] [string] $path
    )
    if( (Test-Path -Path $path) -And ((Get-ChildItem $path | Measure-Object).Count -eq 0) ){
        return $true
    }    
    return $false
}    
function get_version {
    # samples the version of the git repo 
    # example:  git rev-parse HEAD
    #           output: 931ec5d25bff48052afae405d600964efd5fd3da
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$false, Position=0)] [string] $refs = "HEAD"
    )
    $git_opts = @()
    $git_opts += "--no-pager"
    $git_opts += "rev-parse"
    $git_opts += "$refs"
    $git_cmd_output = ""
    
    [hashtable]$Return = @{} 
    Set-Location $dest; &git $git_opts | Tee-Object -Variable git_cmd_output | Out-Null
    $Return.rc = $LASTEXITCODE
    $Return.git_output = $git_cmd_output
    
    return $Return
}

function checkout {
    [CmdletBinding()]
    param()
    [hashtable]$Return = @{} 
    $local_git_output = ""

    $git_opts = @()
    $git_opts += "--no-pager"
    $git_opts += "checkout"
    
    if ($version -ne "HEAD") {
        $git_opts += $version
    }

    Set-Location $dest; &git $git_opts  | Tee-Object -Variable local_git_output | Out-Null

    $Return.git_output = $local_git_output
    
    if ($version -ne "HEAD") {
      Set-Location $dest; &git status --short --branch $version | Tee-Object -Variable branch_status | Out-Null
      $branch_status = $branch_status.split("/")[1]
      Set-Attr $result "branch_status" "$branch_status"

        if ( $branch_status -ne "$version" ) {
            Fail-Json $result "Failed to checkout to $branch"
        }
    }      
    
    return $Return
}

function clone {
    # git clone command
    [CmdletBinding()]
    param()

    Set-Attr $result "method" "clone"
    [hashtable]$Return = @{} 
    $git_output = ""

    $git_opts = @()
    $git_opts += "--no-pager"
    $git_opts += "clone"
    $git_opts += $repo 
    $git_opts += $dest
    
    if ($version -ne "HEAD") {
      $git_opts += "--branch"
      $git_opts += $version
    } 

    if ($depth){
       $git_opts += "--depth"
       $git_opts += $depth
    } 

    Set-Attr $result "git_opts" $git_opts

    #Only clone if $dest does not exist and not in check mode    
    if( -Not $check_mode) {    

        if (CheckPath "$dest") {   
            &git $git_opts | Tee-Object -Variable git_output | Out-Null
            Set-Attr $result "git_output" "$git_output"   
            
            $Return.rc = $LASTEXITCODE
            $Return.git_output = $git_output
            
            if ($LASTEXITCODE -eq 0) {
               $result.changed = $true           
               Set-Attr $result "status" "Successfully cloned $repo into $dest"    
            }
            else {
               $result.changed = $false
               Set-Attr $result "status" "Failed to clone $repo into $dest"                   
            }
     
        }    
        else {
            Set-Attr $result "status" "Failed to clone $repo into $dest. It is either not empty or does not exist"    
        }

        Set-Attr $result "return_code" $LASTEXITCODE
        Set-Attr $result "git_output" $git_output
    }
    else {
        $Return.rc = 0
        $Return.git_output = $git_output        
        Set-Attr $result "status" "Check Mode - Skipping clone of $repo"
    }

    # Check if branch is the correct one
    if ($version -ne "HEAD") {
        Set-Location $dest; &git status --short --branch $version | Tee-Object -Variable branch_status | Out-Null
        $branch_status = $branch_status.split("/")[1]
        Set-Attr $result "branch_status" "$branch_status"

            if ( $branch_status -ne "$version" ) {
                Fail-Json $result "Branch $branch_status is not $branch"
            }
    }     

    return $Return
}

function update {
    # git clone command
    [CmdletBinding()]
    param()

    Set-Attr $result "method" "pull"
    [hashtable]$Return = @{}
    $git_output = ""

    # Build Arguments
    $git_opts = @()
    $git_opts += "--no-pager"
    $git_opts += "pull"
    $git_opts += $remote
    
    if ($version -ne "HEAD") {
       $git_opts += $version
    } 

    Set-Attr $result "git_opts" $git_opts
    #Only update if $dest does exist and not in check mode
    if(-Not $check_mode) {
        # move into correct branch before pull
        checkout
        # perform git pull
        Set-Location $dest; &git $git_opts | Tee-Object -Variable git_output | Out-Null
        $Return.rc = $LASTEXITCODE
        $Return.git_output = $git_output
        if ($LASTEXITCODE -eq 0) {
            Set-Attr $result "changed" $true
            Set-Attr $result "status" "Successfully updated $repo to $version"
        }  
        #TODO: handle correct status change when using update        
        Set-Attr $result "return_code" $LASTEXITCODE
        Set-Attr $result "git_output" $git_output
    } else {
        $Return.rc = 0
        $Return.git_output =  $git_output
        Set-Attr $result "status" "Check Mode - Skipping update of $repo"
    }

    return $Return
}


if ($repo -eq ($null -or "")) {
    Fail-Json $result "Repository cannot be empty or `$null"
}

# set the default dest under user profile
if ($dest -eq $null){
    $repo_name = $repo.split("/")[-1]
    $dest="$env:USERPROFILE\$repo_name"     
} 

if (-Not (Test-Path($dest))) {
    New-Item -ItemType directory -Path $dest      
 }


Set-Attr $result "dest" $dest

$git_output = ""
$rc = 0

try {

    FindGit

    if ($replace_dest) {
        PrepareDestination
    }
    if ([system.uri]::IsWellFormedUriString($repo,[System.UriKind]::Absolute)) {
        # http/https repositories doesn't need Ssh handle
        # fix to avoid wrong usage of CheckSshKnownHosts CheckSshIdentity for http/https
        Set-Attr $result "status" "$repo is valid url"
    } else {
        CheckSshKnownHosts
        CheckSshIdentity
    }
    if ($clone) {
        clone
    }
    if ($update) {
        update
    }
}
catch {
    $ErrorMessage = $_.Exception.Message        
    Fail-Json $result "$ErrorMessage"
}

Exit-Json $result
