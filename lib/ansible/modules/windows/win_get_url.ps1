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

If ($params.url) {
    $url = $params.url
}
Else {
    Fail-Json $result "missing required argument: url"
}

If ($params.dest) {
    $dest = $params.dest
}
Else {
    Fail-Json $result "missing required argument: dest"
}

$skip_certificate_validation = Get-Attr $params "skip_certificate_validation" $false | ConvertTo-Bool
$username = Get-Attr $params "username"
$password = Get-Attr $params "password"

if($skip_certificate_validation){
  [System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}
}

$force = Get-Attr -obj $params -name "force" "yes" | ConvertTo-Bool

If ($force -or -not (Test-Path $dest)) {
    $client = New-Object System.Net.WebClient

    if($username -and $password){
        $client.Credentials = New-Object System.Net.NetworkCredential($username, $password)
    }

    Try {
        $client.DownloadFile($url, $dest)
        $result.changed = $true
    }
    Catch {
        Fail-Json $result "Error downloading $url to $dest $($_.Exception.Message)"
    }
}
Else {
    Try {
        $webRequest = [System.Net.HttpWebRequest]::Create($url)

        if($username -and $password){
            $webRequest.Credentials = New-Object System.Net.NetworkCredential($username, $password)
        }

        $webRequest.IfModifiedSince = ([System.IO.FileInfo]$dest).LastWriteTime
        $webRequest.Method = "GET"
        [System.Net.HttpWebResponse]$webResponse = $webRequest.GetResponse()
        
        $stream = New-Object System.IO.StreamReader($response.GetResponseStream())
        
        $stream.ReadToEnd() | Set-Content -Path $dest -Force -ErrorAction Stop
        
        $result.changed = $true
    }
    Catch [System.Net.WebException] {
        If ($_.Exception.Response.StatusCode -ne [System.Net.HttpStatusCode]::NotModified) {
            Fail-Json $result "Error downloading $url to $dest $($_.Exception.Message)"
        }
    }
    Catch {
        Fail-Json $result "Error downloading $url to $dest $($_.Exception.Message)"
    }
}

Set-Attr $result.win_get_url "url" $url
Set-Attr $result.win_get_url "dest" $dest

Exit-Json $result;
