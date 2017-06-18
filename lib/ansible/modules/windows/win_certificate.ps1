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

$params = Parse-Args $args -supports_check_mode $true

$result = [PSCustomObject]@{
    changed = $false
    state = $null
    thumbprint = $null
    subject = $null
    hasPrivateKey = $null
	notValidBefore = $null
	notValidAfter = $null
    store = $null
    msg = $null
}

$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$state = Get-AnsibleParam -obj $params -name "state" -type "string" -validateSet "present","absent" -failifempty $true -resultobj $result
$path = Get-AnsibleParam -obj $params -name "path" -type "path" -failifempty $true -resultobj $result
$store = Get-AnsibleParam -obj $params -name "store" -type "string" -failifempty $true -validateSet "My","TrustedPublisher","Root","CA" -resultobj $result
$password = Get-AnsibleParam -obj $params -name "password" -type "string"
$exportable = Get-AnsibleParam -obj $params -name "privatekey_exportable" -type "bool" -default $false
$force = Get-AnsibleParam -obj $params -name "force" -type "bool" -default $false

Function ConvertTo-UnixDate ($DateTimeObj) {
   $epoch = [timezone]::CurrentTimeZone.ToLocalTime([datetime]'1/1/1970')
   (New-TimeSpan -Start $epoch -End $PSdate).TotalSeconds
}

#update result object with AnsibleParams
$result.state = $state
$result.store = $store

#check if certificate file is available and gather details about it like type, thumbprint, subject
if (Test-Path -Path $path) {
    $certExtension = ([IO.Path]::GetExtension($path)).ToLower()

    #proceed according to the file extension
    if ($certExtension -eq ".pfx" -or $certExtension -eq ".p12") {
        try {
            $certObj = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($path,(ConvertTo-SecureString -String $password -AsPlainText -Force))
        }
        catch {
            #unable to load the certificate object, either the certificate is damaged or the password is incorrect
            Fail-Json $result "Unable to gather certificate properties. Either the provided password is incorrect or the certificate file is corrupted. exception: $($error[0].Exception.Message)"
        }
    } elseif ($certExtension -eq ".cer" -or $certExtension -eq ".crt" -or $certExtension -eq ".p7b" -or $certExtension -eq ".spc") {
        try {
            $certObj = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($path)
        }
        catch {
            #unable to load the certificate object, either the certificate is damaged or the password is incorrect
            Fail-Json $result "Unable to gather certificate properties. exception: $($error[0].Exception.Message)"
        }
        
    } else {
        #unkown or unsupported file extension
        Fail-Json $result "Unkown or unsupported certificate file extension. extension: $($certExtension)"
    }
    $certThumbprint = $certObj.Thumbprint
    $certSubject = $certObj.Subject
    $certHasPK = $certObj.HasPrivateKey
	$certNotValidBefore = ConvertTo-UnixDate($certObj.NotBefore)
	$certNotValidAfter = ConvertTo-UnixDate($certObj.NotAfter)
} else {
    #certificate file not found
    Fail-Json $result "Certificate file not found. path: $($path)"
}

#update result object with gathered cert facts
$result.thumbprint = $certThumbprint
$result.subject = $certSubject
$result.hasPrivateKey = $certHasPK
$result.notValidBefore = $certNotValidBefore
$result.notValidAfter = $certNotValidAfter

#choose action depending on desired state
switch ($state) {
    "present" {
        #check if certificate is already imported
        if (Test-Path -Path "Cert:\LocalMachine\$($store)\$($certThumbprint)") {
            if (!$force) {
                #the certificate is already present and we dont want to reimport (force = false)
                $result.changed = $false
                $result.msg = "Certificate is already present."
                Exit-Json $result
            }
        }
        if ($certExtension -eq ".pfx" -or $certExtension -eq ".p12") {
            try {
                #import the certificate to the desired store
                if (!$check_mode) { $returnObj = Import-PfxCertificate -Exportable:$exportable -Password (ConvertTo-SecureString -String $password -AsPlainText -Force) `
                            -CertStoreLocation "Cert:\LocalMachine\$($store)" -FilePath $path }
                #complete module execution
               	$result.changed = $true
                $result.msg = "Certificate $($certThumbprint) successfully imported to store $($store)"
                Exit-Json $result
            }
            catch {
                #certificate import failed
                Fail-Json $result "Certificate import failed. exception: $($error[0].Exception.Message)"
            }
                
        } else {
            try {
                #import the certificate to the desired store
                if (!$check_mode) { $returnObj = Import-Certificate -FilePath $path -CertStoreLocation "Cert:\LocalMachine\$($store)" }
                #complete module execution
                $result.changed = $true
                $result.msg = "Certificate $($certThumbprint) successfully imported to store $($store)"
        	    Exit-Json $result
            }
            catch {
                #certificate import failed
                Fail-Json $result "Certificate import failed. exception: $($error[0].Exception.Message)"
            }        
        }
    }
    "absent" {
        #check if certificate is already imported
        if (Test-Path -Path "Cert:\LocalMachine\$($store)\$($certThumbprint)") {
            #certificate is present but the desired state is 'absent' - we're going to remove it
            try {
                if (!$check_mode) { $returnObj = Remove-Item -Path "Cert:\LocalMachine\$($store)\$($certThumbprint)" -Force }
                #complete module execution
                $result.changed = $true
                $result.msg = "Certificate $($certThumbprint) successfully removed from the store $($store)"
                Exit-Json $result
            }
            catch {
                #certificate removal failed
                Fail-Json $result "Certificate removal failed. exception: $($error[0].Exception.Message)"
            }
            
        } else {
            #complete module execution
            $result.changed = $false
            $result.msg = "Certificate $($certThumbprint) not present in store $($store)"
            Exit-Json $result
        }
    }
}