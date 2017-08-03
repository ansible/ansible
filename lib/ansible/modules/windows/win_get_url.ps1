#!powershell
# This file is part of Ansible.
#
# (c)) 2015, Paul Durivage <paul.durivage@rackspace.com>, Tal Auslander <tal@cloudshare.com>
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

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$url = Get-AnsibleParam -obj $params -name "url" -type "str" -failifempty $true
$dest = Get-AnsibleParam -obj $params -name "dest" -type "path" -failifempty $true
$skip_certificate_validation = Get-AnsibleParam -obj $params -name "skip_certificate_validation" -type "bool"
$validate_certs = Get-AnsibleParam -obj $params -name "validate_certs" -type "bool" -default $true
$username = Get-AnsibleParam -obj $params -name "username" -type "str"
$password = Get-AnsibleParam -obj $params -name "password" -type "str"
$proxy_url = Get-AnsibleParam -obj $params -name "proxy_url" -type "str"
$proxy_username = Get-AnsibleParam -obj $params -name "proxy_username" -type "str"
$proxy_password = Get-AnsibleParam -obj $params -name "proxy_password" -type "str"
$force = Get-AnsibleParam -obj $params -name "force" -type "bool" -default $true

$result = @{
    changed = $false
    win_get_url = @{
        dest = $dest
        url = $url
    }
}

# If skip_certificate_validation was specified, use validate_certs
if ($skip_certificate_validation -ne $null) {
    Add-DeprecationWarning -obj $result -msg "The parameter 'skip_vertificate_validation' is being replaced with 'validate_certs'" -version 2.8
    $validate_certs = -not $skip_certificate_validation
}

if (-not $validate_certs) {
    [System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}
}


Function Download-File($result, $url, $dest, $username, $password, $proxy_url, $proxy_username, $proxy_password) {
    # use last part of url for dest file name if a directory is supplied for $dest
    If ( Test-Path -PathType Container $dest ) {
       $url_basename = Split-Path -leaf $url
       If ( $url_basename.Length -gt 0 ) {
          $dest = Join-Path -Path $dest -ChildPath $url_basename
          $result.win_get_url.actual_dest = $dest
       }
    }
    # check $dest parent folder exists before attempting download, which avoids unhelpful generic error message.
    $dest_parent = Split-Path -Path $dest
    $result.win_get_url.dest_parent = $dest_parent
    If ( -not (Test-Path -Path $dest_parent -PathType Container)) {
        $result.changed = $false
        Fail-Json $result "The path '$dest_parent' does not exist for destination '$dest', or is not visible to the current user.  Ensure download destination folder exists (perhaps using win_file state=directory) before win_get_url runs."
    }
    $webClient = New-Object System.Net.WebClient
    if($proxy_url) {
        $proxy_server = New-Object System.Net.WebProxy($proxy_url, $true)
        if($proxy_username -and $proxy_password){
            $proxy_credential = New-Object System.Net.NetworkCredential($proxy_username, $proxy_password)
            $proxy_server.Credentials = $proxy_credential
        }
        $webClient.Proxy = $proxy_server
    }

    if($username -and $password){
        $webClient.Credentials = New-Object System.Net.NetworkCredential($username, $password)
    }

    Try {
        if (-not $check_mode) {
            $webClient.DownloadFile($url, $dest)
        }
        $result.changed = $true
    }
    Catch {
        Fail-Json $result "Error downloading $url to $dest $($_.Exception.Message)"
    }
}


If ($force -or -not (Test-Path -Path $dest)) {
    
    Download-File -result $result -url $url -dest $dest -username $username -password $password -proxy_url $proxy_url -proxy_username $proxy_username -proxy_password $proxy_password
}
Else {
    $fileLastMod = ([System.IO.FileInfo]$dest).LastWriteTimeUtc
    $webLastMod = $null

    Try {
        $webRequest = [System.Net.HttpWebRequest]::Create($url)
        if ($proxy_url) {
          $proxy_server = New-Object System.Net.WebProxy($proxy_url, $true)
          if ($proxy_username -and $proxy_password) {
            $proxy_credential = New-Object System.Net.NetworkCredential($proxy_username, $proxy_password)
            $proxy_server.Credentials = $proxy_credential
          }
          $webRequest.Proxy = $proxy_server
        }

        if($username -and $password){
            $webRequest.Credentials = New-Object System.Net.NetworkCredential($username, $password)
        }

        $webRequest.Method = "HEAD"
        [System.Net.HttpWebResponse]$webResponse = $webRequest.GetResponse()

        $webLastMod = $webResponse.GetResponseHeader("Last-Modified")
        $webResponse.Close()
    }
    Catch {
        Fail-Json $result "Error when requesting Last-Modified date from $url $($_.Exception.Message)"
    }

    If (($webLastMod) -and ((Get-Date -Date $webLastMod ) -lt $fileLastMod)) {
        $result.changed = $false
    } Else {
        Download-File -result $result -url $url -dest $dest -username $username -password $password -proxy_url $proxy_url -proxy_username $proxy_username -proxy_password $proxy_password
    }

}

Exit-Json $result
