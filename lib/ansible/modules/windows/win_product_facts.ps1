#!powershell

# Copyright: (c) 2017, Dag Wieers (dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic

# This modules does not accept any options
$spec = @{
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

# First try to find the product key from ACPI
try {
    $product_key = (Get-CimInstance -Class SoftwareLicensingService).OA3xOriginalProductKey
} catch {
    $product_key = $null
}

if (-not $product_key) {
    # Else try to get it from the registry instead
    try {
        $data = Get-ItemPropertyValue -Path "HKLM:\Software\Microsoft\Windows NT\CurrentVersion" -Name DigitalProductId
    } catch {
        $data = $null
    }

    # And for Windows 2008 R2
    if (-not $data) {
        try {
            $data = Get-ItemPropertyValue -Path "HKLM:\Software\Microsoft\Windows NT\CurrentVersion" -Name DigitalProductId4
        } catch {
            $data = $null
        }
    }

    if ($data) {
        $product_key = $null
        $hexdata = $data[52..66]
        $chardata = "B","C","D","F","G","H","J","K","M","P","Q","R","T","V","W","X","Y","2","3","4","6","7","8","9"

        # Decode base24 binary data
        for ($i = 24; $i -ge 0; $i--) {
            $k = 0
            for ($j = 14; $j -ge 0; $j--) {
                $k = $k * 256 -bxor $hexdata[$j]
                $hexdata[$j] = [math]::truncate($k / 24)
                $k = $k % 24
            }
            $product_key = $chardata[$k] + $product_key
            if (($i % 5 -eq 0) -and ($i -ne 0)) {
                $product_key = "-" + $product_key
            }
        }
    }
}

try {
    $license_info = Get-CimInstance SoftwareLicensingProduct | Where-Object PartialProductKey

    switch ($license_info.LicenseStatus){
        0 {
            $winlicense_status="Unlicensed"
        }

        1 {
            $winlicense_status="Licensed"
        }

        2 {
            $winlicense_status="OOBGrace"
        }

        3 {
            $winlicense_status="OOTGrace"
        }

        4 {
            $winlicense_status="NonGenuineGrace"
        }

        5 {
            $winlicense_status="Notification"
        }

        6 {
            $winlicense_status="ExtendedGrace"
        }

        default {
            $winlicense_status="NA"
        }
    }

    $winlicense_edition = $license_info.Name
    $winlicense_channel = $license_info.ProductKeyChannel

} catch {
    $winlicense_edition = "NA"
    $winlicense_channel = "NA"
    $winlicense_status = "NA"
}


$module.Result.ansible_facts = @{
    ansible_os_product_id = (Get-CimInstance Win32_OperatingSystem).SerialNumber
    ansible_os_product_key = $product_key
    ansible_winlicense_edition = $winlicense_edition
    ansible_winlicense_channel = $winlicense_channel 
    ansible_winlicense_status = $winlicense_status 
}

$module.ExitJson()
