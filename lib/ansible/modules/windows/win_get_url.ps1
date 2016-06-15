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

$params = Parse-Args $args;

$result = New-Object psobject @{
    win_get_url = New-Object psobject
    changed = $false
}

$url = Get-AnsibleParam $params -name "url" -failifempty $true
$dest = Get-AnsibleParam $params -name "dest" -failifempty $true

$skip_certificate_validation = Get-AnsibleParam $params -name "skip_certificate_validation" -default $false
$skip_certificate_validation = $skip_certificate_validation | ConvertTo-Bool
$username = Get-AnsibleParam $params "username"
$password = Get-AnsibleParam $params "password"

$proxy_url = Get-AnsibleParam $params "proxy_url"
$proxy_username = Get-AnsibleParam $params "proxy_username"
$proxy_password = Get-AnsibleParam $params "proxy_password"

if($skip_certificate_validation){
  [System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}
}

$force = Get-AnsibleParam -obj $params -name "force" -default $true
$force = $force | ConvertTo-Bool

Function Download-File($result, $url, $dest, $username, $password, $proxy_url, $proxy_username, $proxy_password) {
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
        $webClient.DownloadFile($url, $dest)
        $result.changed = $true
    }
    Catch {
        Fail-Json $result "Error downloading $url to $dest $($_.Exception.Message)"
    }

}


If ($force -or -not (Test-Path $dest)) {
   Download-File -result $result -url $url -dest $dest -username $username -password $password -proxy_url $proxy_url -proxy_username $proxy_username -proxy_password $proxy_password

}
Else {
    $fileLastMod = ([System.IO.FileInfo]$dest).LastWriteTimeUtc
    $webLastMod = $null

    Try {
        $webRequest = [System.Net.HttpWebRequest]::Create($url)

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

Set-Attr $result.win_get_url "url" $url
Set-Attr $result.win_get_url "dest" $dest

Exit-Json $result;
