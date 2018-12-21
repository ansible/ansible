#!powershell

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params "_ansible_check_mode" -type 'bool' -default $false
$_remote_tmp = Get-AnsibleParam $params "_ansible_remote_tmp" -type "path" -default $env:TMP

$location = Get-AnsibleParam -obj $params -name 'location' -type 'str'
$format = Get-AnsibleParam -obj $params -name 'format' -type 'str'
$unicode_language = Get-AnsibleParam -obj $params -name 'unicode_language' -type 'str'
$copy_settings = Get-AnsibleParam -obj $params -name 'copy_settings' -type 'bool' -default $false

$result = @{
    changed = $false
    restart_required = $false
}

# This is used to get the format values based on the LCType enum based through. When running Vista/7/2008/200R2
$lctype_util = @"
using System;
using System.Text;
using System.Runtime.InteropServices;
using System.ComponentModel;

namespace Ansible {
    public class LocaleHelper {
        private String Locale;

        public LocaleHelper(String locale) {
            Locale = locale;
        }

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern int GetLocaleInfoEx(String lpLocaleName, UInt32 LCType, StringBuilder lpLCData, int cchData);

        public String GetValueFromType(UInt32 LCType) {
            StringBuilder data = new StringBuilder(500);
            int result = GetLocaleInfoEx(Locale, LCType, data, 500);
            if (result == 0)
                throw new Exception(String.Format("Error getting locale info with legacy method: {0}", new Win32Exception(Marshal.GetLastWin32Error()).Message));

            return data.ToString();
        }
    }
}
"@

Function Get-ValidGeoIds($cultures) {
   $geo_ids = @()
   foreach($culture in $cultures) {
       try {
           $geo_id = [System.Globalization.RegionInfo]$culture.Name
           $geo_ids += $geo_id.GeoId
       } catch {}
   }
   $geo_ids
}

Function Test-RegistryProperty($reg_key, $property) {
    $type = Get-ItemProperty $reg_key -Name $property -ErrorAction SilentlyContinue
    if ($type -eq $null) {
        $false
    } else {
        $true
    }
}

Function Copy-RegistryKey($source, $target) {
    # Using Copy-Item -Recurse is giving me weird results, doing it recursively
    Copy-Item -Path $source -Destination $target -WhatIf:$check_mode

    foreach($key in Get-ChildItem $source) {
        $sourceKey = "$source\$($key.PSChildName)"
        $targetKey = (Get-Item $source).PSChildName
        Copy-RegistryKey -source "$sourceKey" -target "$target\$targetKey"
    }
}

# With the legacy options (needed for OS < Windows 8 and Server 2012) we need to check multiple reg
# keys and modify them if they need changing. This is because Microsoft only made changing these
# values with the newer versions of Windows and didn't backport these features to the older ones,
# thanks a bunch there Microsoft :(
Function Set-CultureLegacy($culture) {
    # For when Set-Culture is not available (Pre Windows 8 and Server 2012)
    $reg_key = 'HKCU:\Control Panel\International'

    $original_tmp = $env:TMP
    $env:TMP = $_remote_tmp
    Add-Type -TypeDefinition $lctype_util
    $env:TMP = $original_tmp

    $lookup = New-Object Ansible.LocaleHelper($culture)
    # hex values are from http://www.pinvoke.net/default.aspx/kernel32/GetLocaleInfoEx.html
    $wanted_values = @{
        Locale = '{0:x8}' -f ([System.Globalization.CultureInfo]$culture).LCID
        LocaleName = $culture
        s1159 = $lookup.GetValueFromType(0x00000028)
        s2359 = $lookup.GetValueFromType(0x00000029)
        sCountry = $lookup.GetValueFromType(0x00000006)
        sCurrency = $lookup.GetValueFromType(0x00000014)
        sDate = $lookup.GetValueFromType(0x0000001D)
        sDecimal = $lookup.GetValueFromType(0x0000000E)
        sGrouping = $lookup.GetValueFromType(0x00000010)
        sLanguage = $lookup.GetValueFromType(0x00000003) # LOCALE_ABBREVLANGNAME
        sList = $lookup.GetValueFromType(0x0000000C)
        sLongDate = $lookup.GetValueFromType(0x00000020)
        sMonDecimalSep = $lookup.GetValueFromType(0x00000016)
        sMonGrouping = $lookup.GetValueFromType(0x00000018)
        sMonThousandSep = $lookup.GetValueFromType(0x00000017)
        sNativeDigits = $lookup.GetValueFromType(0x00000013)
        sNegativeSign = $lookup.GetValueFromType(0x00000051)
        sPositiveSign = $lookup.GetValueFromType(0x00000050)
        sShortDate = $lookup.GetValueFromType(0x0000001F)
        sThousand = $lookup.GetValueFromType(0x0000000F)
        sTime = $lookup.GetValueFromType(0x0000001E)
        sTimeFormat = $lookup.GetValueFromType(0x00001003)
        sYearMonth = $lookup.GetValueFromType(0x00001006)
        iCalendarType = $lookup.GetValueFromType(0x00001009)
        iCountry = $lookup.GetValueFromType(0x00000005)
        iCurrDigits = $lookup.GetValueFromType(0x00000019)
        iCurrency = $lookup.GetValueFromType(0x0000001B)
        iDate = $lookup.GetValueFromType(0x00000021)
        iDigits = $lookup.GetValueFromType(0x00000011)
        NumShape = $lookup.GetValueFromType(0x00001014) # LOCALE_IDIGITSUBSTITUTION
        iFirstDayOfWeek = $lookup.GetValueFromType(0x0000100C)
        iFirstWeekOfYear = $lookup.GetValueFromType(0x0000100D)
        iLZero = $lookup.GetValueFromType(0x00000012)
        iMeasure = $lookup.GetValueFromType(0x0000000D)
        iNegCurr = $lookup.GetValueFromType(0x0000001C)
        iNegNumber = $lookup.GetValueFromType(0x00001010)
        iPaperSize = $lookup.GetValueFromType(0x0000100A)
        iTime = $lookup.GetValueFromType(0x00000023)
        iTimePrefix = $lookup.GetValueFromType(0x00001005)
        iTLZero = $lookup.GetValueFromType(0x00000025)
    }

    if (Test-RegistryProperty -reg_key $reg_key -property 'sShortTime') {
        # sShortTime was added after Vista, will check anyway and add in the value if it exists
        $wanted_values.sShortTime = $lookup.GetValueFromType(0x00000079)
    }

    $properties = Get-ItemProperty $reg_key
    foreach($property in $properties.PSObject.Properties) {
        if (Test-RegistryProperty -reg_key $reg_key -property $property.Name) {
            $name = $property.Name
            $old_value = $property.Value
            $new_value = $wanted_values.$name

            if ($new_value -ne $old_value) {
                Set-ItemProperty -Path $reg_key -Name $name -Value $new_value -WhatIf:$check_mode
                $result.changed = $true
            }
        }
    }
}

Function Set-SystemLocaleLegacy($unicode_language) {
    # For when Get/Set-WinSystemLocale is not available (Pre Windows 8 and Server 2012)
    $current_language_value = (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Nls\Language').Default
    $wanted_language_value = '{0:x4}' -f ([System.Globalization.CultureInfo]$unicode_language).LCID
    if ($current_language_value -ne $wanted_language_value) {
        Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\Nls\Language' -Name 'Default' -Value $wanted_language_value -WhatIf:$check_mode
        $result.changed = $true
        $result.restart_required = $true
    }

    # This reads from the non registry (Default) key, the extra prop called (Default) see below for more details
    $current_locale_value = (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Nls\Locale')."(Default)"
    $wanted_locale_value = '{0:x8}' -f ([System.Globalization.CultureInfo]$unicode_language).LCID
    if ($current_locale_value -ne $wanted_locale_value) {
        # Need to use .net to write property value, Locale has 2 (Default) properties
        # 1: The actual (Default) property, we don't want to change Set-ItemProperty writes to this value when using (Default)
        # 2: A property called (Default), this is what we want to change and only .net SetValue can do this one
        if (-not $check_mode) {
            $hive = [Microsoft.Win32.RegistryKey]::OpenRemoteBaseKey("LocalMachine", $env:COMPUTERNAME)
            $key = $hive.OpenSubKey("SYSTEM\CurrentControlSet\Control\Nls\Locale", $true)
            $key.SetValue("(Default)", $wanted_locale_value, [Microsoft.Win32.RegistryValueKind]::String)
        }
        $result.changed = $true
        $result.restart_required = $true
    }

    $codepage_path = 'HKLM:\SYSTEM\CurrentControlSet\Control\Nls\CodePage'
    $current_codepage_info = Get-ItemProperty $codepage_path
    $wanted_codepage_info = ([System.Globalization.CultureInfo]::GetCultureInfo($unicode_language)).TextInfo

    $current_a_cp = $current_codepage_info.ACP
    $current_oem_cp = $current_codepage_info.OEMCP
    $current_mac_cp = $current_codepage_info.MACCP
    $wanted_a_cp = $wanted_codepage_info.ANSICodePage
    $wanted_oem_cp = $wanted_codepage_info.OEMCodePage
    $wanted_mac_cp = $wanted_codepage_info.MacCodePage

    if ($current_a_cp -ne $wanted_a_cp) {
        Set-ItemProperty -Path $codepage_path -Name 'ACP' -Value $wanted_a_cp -WhatIf:$check_mode
        $result.changed = $true
        $result.restart_required = $true
    }
    if ($current_oem_cp -ne $wanted_oem_cp) {
        Set-ItemProperty -Path $codepage_path -Name 'OEMCP' -Value $wanted_oem_cp -WhatIf:$check_mode
        $result.changed = $true
        $result.restart_required = $true
    }
    if ($current_mac_cp -ne $wanted_mac_cp) {
        Set-ItemProperty -Path $codepage_path -Name 'MACCP' -Value $wanted_mac_cp -WhatIf:$check_mode
        $result.changed = $true
        $result.restart_required = $true
    }
}

if ($format -eq $null -and $location -eq $null -and $unicode_language -eq $null) {
    Fail-Json $result "An argument for 'format', 'location' or 'unicode_language' needs to be supplied"
} else {
    $valid_cultures = [System.Globalization.CultureInfo]::GetCultures('InstalledWin32Cultures')
    $valid_geoids = Get-ValidGeoIds -cultures $valid_cultures

    if ($location -ne $null) {
        if ($valid_geoids -notcontains $location) {
            Fail-Json $result "The argument location '$location' does not contain a valid Geo ID"
        }
    }

    if ($format -ne $null) {
        if ($valid_cultures.Name -notcontains $format) {
            Fail-Json $result "The argument format '$format' does not contain a valid Culture Name"
        }
    }

    if ($unicode_language -ne $null) {
        if ($valid_cultures.Name -notcontains $unicode_language) {
            Fail-Json $result "The argument unicode_language '$unicode_language' does not contain a valid Culture Name"
        }
    }
}

if ($location -ne $null) {
    # Get-WinHomeLocation was only added in Server 2012 and above
    # Use legacy option if older
    if (Get-Command 'Get-WinHomeLocation' -ErrorAction SilentlyContinue) {
        $current_location = (Get-WinHomeLocation).GeoId
        if ($current_location -ne $location) {
            if (-not $check_mode) {
                Set-WinHomeLocation -GeoId $location
            }
            $result.changed = $true
        }
    } else {
        $current_location = (Get-ItemProperty -Path 'HKCU:\Control Panel\International\Geo').Nation
        if ($current_location -ne $location) {
            Set-ItemProperty -Path 'HKCU:\Control Panel\International\Geo' -Name 'Nation' -Value $location -WhatIf:$check_mode
            $result.changed = $true
        }
    }
}

if ($format -ne $null) {
    $current_format = (Get-Culture).Name
    if ($current_format -ne $format) {
        # Set-Culture was only added in Server 2012 and above, use legacy option if older
        if (Get-Command 'Set-Culture' -ErrorAction SilentlyContinue) {
            if (-not $check_mode) {
                Set-Culture -CultureInfo $format
            }
        } else {
            Set-CultureLegacy -culture $format
        }
        $result.changed = $true
    }
}

if ($unicode_language -ne $null) {
    # Get/Set-WinSystemLocale was only added in Server 2012 and above, use legacy option if older
    if (Get-Command 'Get-WinSystemLocale' -ErrorAction SilentlyContinue) {
        $current_unicode_language = (Get-WinSystemLocale).Name
        if ($current_unicode_language -ne $unicode_language) {
            if (-not $check_mode) {
                Set-WinSystemLocale -SystemLocale $unicode_language
            }
            $result.changed = $true
            $result.restart_required = $true
        }
    } else {
        Set-SystemLocaleLegacy -unicode_language $unicode_language
    }
}

if ($copy_settings -eq $true -and $result.changed -eq $true) {
    if (-not $check_mode) {
        $defaultHiveKey = 'HKU\TEMP'
        reg load $defaultHiveKey 'C:\Users\Default\NTUSER.DAT'
        New-PSDrive -Name HKU -PSProvider Registry -Root Registry::HKEY_USERS

        $sids = 'TEMP', '.DEFAULT', 'S-1-5-19', 'S-1-5-20'
        foreach ($sid in $sids) {
            Copy-RegistryKey -source "HKCU:\Keyboard Layout" -target "HKU:\$sid"
            Copy-RegistryKey -source "HKCU:\Control Panel\International" -target "HKU:\$sid\Control Panel"
            Copy-RegistryKey -source "HKCU:\Control Panel\Input Method" -target "HKU:\$sid\Control Panel"
        }

        Remove-PSDrive HKU
        [gc]::collect()
        reg unload $defaultHiveKey
    }
    $result.changed = $true
}

Exit-Json $result
