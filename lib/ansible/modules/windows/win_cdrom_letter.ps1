#!powershell

# Copyright: (c) 2019, RusoSova
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#AnsibleRequires -OSVersion 6.2

$ErrorActionPreference = "Stop"

$spec = @{
    options = @{
        drive_letter = @{ type="str" }
        change_single = @{ type="str" }
        dismount_virtual = @{ type="bool"; default=$false }
        dismount_only = @{ type="bool"; default=$false }
    }
    required_one_of = @(
        ,@('drive_letter', 'dismount_only')
    )
    mutually_exclusive = @(
        ,@('drive_letter', 'dismount_only')
    )
    supports_check_mode = $true
}


$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$drive_letter = $module.Params.drive_letter
$single = $module.Params.change_single
$dismount_virtual = $module.Params.dismount_virtual
$dismount_only = $module.Params.dismount_only

###Validate Input###
if ($drive_letter -and $drive_letter -notmatch "^(?:([C-Zc-z])(?!.*?\1),)*[C-Zc-z]$") {
    $module.FailJson("The parameter drive_letter should be a list of unique characters c-zC-Z separated by comma")
}

if ($single -and $single.trim() -notmatch "^[C-Zc-z]{1}$") {
    $module.FailJson("The parameter change_single should be a single character c-zC-Z")
} elseif ($single) {
    $single=$single.Trim().ToUpper()+":" #.contains method is case sensitive, that will be used latter
}
###


#Function to get the list of CDROMS Letters
function Get-CDROMList {
    param(
        [Parameter(Position=0)][string]$failedMessge,
        [Parameter(Position=1)][bool]$skipError=$False
    )
    try {
       [array]$cdroms=(Get-CimInstance -ClassName Win32_CDROMDrive).drive
    } catch {
        $module.FailJson("There was an error retrieving the list of CDROMs $($_.Exception.Message)")
    }
    if ($cdroms.count -eq 0 -and -not $skipError) {
        $module.FailJson($failedMessge)
    }
    return $cdroms;
}

#Function to get the list of Virtual CDROMS Letters
function Get-VirtualCDROMList {
    try {
        $vcdroms=(Get-CimInstance -ClassName Win32_CDROMDrive -filter "Caption = 'Microsoft Virtual DVD-ROM'").drive
    } catch {
        $module.FailJson("There was an error retrieving the list of virtual CDROMs $letter - $($_.Exception.Message)")
    }
    return $vcdroms;
}

#Function to check if all the drives in drieve_letter are already CDROMs
function AllCDs {
    param(
        [Parameter(Position=0)][array]$driveletters
    )
    $counter=0
    foreach ($drive in $driveletters) { 
        $drive =$drive +":"
        if (Get-CimInstance -ClassName Win32_CDROMDrive -filter "Drive = `"$drive`"") { $counter++ }
    }
    if ($driveletters.count -eq $counter) {
        return $True;
    } else {
        return $False;
    }
}

#Function dismount virtual CDROMs
function Dismount-VirtualCDROM {
    param(
        [Parameter(Position=0)][string]$letter
    )
    try {
        (new-object -COM Shell.Application).NameSpace(17).ParseName($letter).InvokeVerb('Eject')
        start-sleep -Seconds 1 #need to pause after dismount, otherwise it might not register properly
    } catch {
        $module.FailJson("There was an error dismounting virtual CDROM $letter - $($_.Exception.Message)")
    }
}

#Function to change CDROM Letter
function Set-CDROMLetter {
    param(
        [Parameter(Position=0)]$from,
        [Parameter(Position=1)]$to
    )
    try {
        Set-CimInstance -InputObject $from -Property @{DriveLetter=$to} | out-null
    } catch {
        $module.FailJson("There was an error changing letter of the CDROM $letterToChange - $($_.Exception.Message)")
    }
}


#Collect the initial state of the CDROM drives and pass it to the module Result
$initialListOfCDROMs=Get-CDROMList -failedMessge "There are no CDROMs on this system"
$module.Result.before_change=$initialListOfCDROMs

#Dismount Virtual CDROMs
if ($dismount_virtual -or $dismount_only) {
    $virtualCDROMs=Get-VirtualCDROMList
    if ($virtualCDROMs) {
        #Logic for when Single drive was provided
        if ($single) {  
            if ($virtualCDROMs.contains($single)) {
                $virtualCDROMs=$single
            } elseif ($dismount_only) { #Fail if single is not Virtual CDROM and we dismount only
                $module.FailJson("$single is not a Windows virtual CDROM")
            } else {
                $virtualCDROMs=$null  #Do nothing if the single drive is not a virtual CDROM
            }
        }
        foreach ($letter in $virtualCDROMs ) {
            if (-not $module.CheckMode) {
                Dismount-VirtualCDROM -letter $letter
            }
        }
        $module.Result.changed = $true
    }
    $module.Result.dismounted=$virtualCDROMs -join ","

    ##Account for check mode. Since the Virtual CDROMs were not actually dismounted, we need to fix the array of remaining CDROM manually by removing "dismounted" virtual CDROMs
    if ($module.CheckMode) {
        [array]$checkmodepresentCDROMs = $initialListOfCDROMs | Where-Object { $virtualCDROMs -notcontains $_ } #Remove dismounted CDROMs from the list of available CDROMs on the system
        if ($checkmodepresentCDROMs.count -eq 0 -and -not $dismount_only) {
            $module.FailJson("There are no CDROMs left on this system after dismounting Windows virtual CDROMs")
        }
        if ($dismount_only) {
            [array]$checkmodeChange=$checkmodepresentCDROMs
        }
    }
}

if (-not $dismount_only) {
    #Collect the list if CDROM drives after possibly dismounting the Virtual ones and account for possible checkmode with virtual dismounts
    if ($checkmodepresentCDROMs) {
        $presentCDROMs=$checkmodepresentCDROMs
    } else {
        $presentCDROMs=Get-CDROMList -failedMessge "There are no CDROMs left on this system after dismounting Windows virtual CDROMs"
    }

    [array]$checkmodeChange=$presentCDROMs
    [array]$drvLetterArr=$drive_letter.split(",")

    #Check if change_single drive letter exists and then create an array with just a single drive letter, otherwise create an array with all the CDROMs
    if ($single) {
        if ($presentCDROMs.contains($single)) {
            [array]$listToChange=$single
        } else {
            $module.FailJson("$single is not a CDROM")
        }
    } else {
        [array]$listToChange=$presentCDROMs
    }

    $allCDroms=AllCDs -driveletters $drvLetterArr
    $currentVolumes=get-volume | Select-Object -ExpandProperty DriveLetter #Collect all the letters in use
    $listToChange=$listToChange | Where-Object { $drvLetterArr -notcontains $_.replace(":",'') } #Sanitize the list of affected CDROMs by removing any letter provided in drive_letter that are already CDROMs
    $drvLetterArr=$drvLetterArr | Where-Object { $currentVolumes -notContains $_ }  #Sanitize $drvLetterArr and remove any letters that are already assigned to the volumes
    if ($drvLetterArr.count -gt 0 -or ($drvLetterArr.count -eq 0 -and $listToChange.count -eq 0) -or $allCDroms) {
        if ($drvLetterArr.count -lt $listToChange.count ) {
            $objectsToCount=$drvLetterArr.count #If less drive letter than cdroms were provided, change the counter to the number drive letters
        } else {
            $objectsToCount=$listToChange.count #Default counter=number of CDROMS
        }
        #Loop through the list and change the mapped letters
        for ($x=0; $x -le $objectsToCount-1; $x++) {
            $cdRomToChange=$null ; $letterToChange=$listToChange[$x] ; $letterToBe=$drvLetterArr[$x]+":"
            $cdRomToChange=Get-CimInstance -ClassName Win32_Volume -filter "DriveLetter = `"$letterToChange`"" 
            if ($cdRomToChange) {
                if (-not $module.CheckMode) {
                    Set-CDROMLetter -from  $cdRomToChange -to $letterToBe
                } else {
                    $checkmodeChange=$checkmodeChange.replace($letterToChange,$letterToBe) #Update Check mode variable with the change
                }
                $changeCount="remap[$x]"
                $module.Result.$changeCount=("$letterToChange --> $letterToBe")
            } else {
                $module.FailJson("There was an error finding CDROM $letterToChange")
            }
        }
        $module.Result.changed = $true
        $module.Result.number_of_cdroms=$presentCDROMs.count
        $module.Result.number_of_changes=$x
    } else {
        $module.FailJson("All the provided letter(s) [$drive_letter] are already in use")
    }
}

if (-not $module.CheckMode) {
    $module.Result.post_change=Get-CDROMList -skipError:$True
} else {
    $module.Result.post_change=$checkmodeChange
}

$module.ExitJson()
