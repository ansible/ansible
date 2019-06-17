#!powershell

# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Wilmar den Ouden <wilmaro@intermax.nl>
# Copyright: (c) 2018, Intermax Cloudsourcing
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic

$spec = @{
    options = @{
        name = @{ type = "str"; required = $true }
        state = @{ type = "str"; choices = "present", "absent", "created", "started", "stopped", "restarted"; default = "present" }
        force_stop = @{ type = "bool"; default = $false }
        hostserver = @{ type = "str"; }
        generation = @{ type = "int"; choices = 1, 2; default = 1; }
        cpu = @{ type = "int"; default = 1 }
        memory = @{ type = "str"; default = "512MB" }
        disks = @{ type = "list";}
        network_adapters = @{ type = "list" }
        secure_boot = @{ type = "bool"; default = $false }
        secure_boot_template = @{ type = "str"; choices = "MicrosoftWindows", "MicrosoftUEFICertificateAuthority"; default = $null }
        wait_for_ip = @{ type = "bool"; default = $false }
        timeout = @{ type = "int"; default = 30 }
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$name = $module.Params.name
$state = $module.Params.state
$force_stop = $module.Params.force_stop
$hostserver = $module.Params.hostserver
$cpu = $module.Params.cpu
$memory = $module.Params.memory
$generation = $module.Params.generation
$disks = $module.Params.disks
$network_adapters = $module.Params.network_adapters
$secure_boot = $module.Params.secure_boot
$secure_boot_template = $module.Params.secure_boot_template
$wait_for_ip = $module.Params.wait_for_ip
$timeout = $module.Params.timeout

$module.Result.changed = $false

if (($secure_boot) -and $generation -eq 1) {
  # If secure_boot or secure_boot_template specified with generation 1 VM
  $module.FailJson("Secure boot options are not valid for generation 1 machines")
}
elseif ((-not $secure_boot) -and $secure_boot_template) {
  # If secure_boot is set to false and secure_boot_templace is specified
  $module.FailJson("Secure_boot_template is not valid when secure_boot is false")
}
if ($disks) {
  # When unique contains less items then the hashtable size there are duplicate paths
  if (($disks | ForEach-Object { $_.path } | Select-Object -unique).Count -lt $disks.Count) {
    $module.FailJson("There are duplicate disk paths defined")
  }

  $first_boot_counter = 0
  foreach ($disk in $disks) {
    if (-not $disk.size) {
        $module.FailJson("No size is specified for $($disk.path)")
    }

    if ($disk.ContainsKey("parent_path")) {
      # If disk contains parent_path do some checking
      if ($([System.IO.Path]::GetExtension($disk.path)) -ne $([System.IO.Path]::GetExtension($disk.parent_path))) {
        # If parent_path and disk_path have different extensions
        $module.FailJson("The path and parent_path have different extensions $($disk.path) and $($disk.parent_path)")
      }
      elseif (-Not $(Test-Path -LiteralPath $disk.parent_path)) {
        # If parent_path does not exist, module does not support creation of parent disks
        $module.FailJson("The parent disk does not exist $($disk.parent_path)")
      }
    }
    if ($disk.ContainsKey("first_boot_device")) {
      if ($disk.first_boot_device) {
        $first_boot_counter++
        if ($generation -eq 1) {
          # First_boot_device is not support on generation 1 machines since Set-VMBios has no such thing
          $module.FailJson("The first_boot_device parameter is not supported for generation 1")
        }
      }
      if ($first_boot_counter -gt 1) {
        $module.FailJson("The first_boot_device parameter is set on multiple disks")
      }
    }
  }
}
if ($network_adapters) {
  # When unique contains less items then the hashtable size there are duplicate names
  if (($network_adapters | ForEach-Object { $_.name } | Select-Object -unique).Count -lt $network_adapters.Count) {
        $module.FailJson("There are duplicate network adapter names defined")
  }
}

Function New-Guest() {
  $new_vm_args = @{
    Name               = $name
    MemoryStartupBytes = $memory
    Generation         = $generation
    NoVHD              = $true
  }

  try {
    $vm = New-VM @set_args @new_vm_args
    $module.Result.changed = $true
  }
  catch {
    $module.FailJson("Failed to create VM", $_.Exception.Message)
  }

  if ($vm) {
    $vm_properties = @{
      ProcessorCount = $cpu
    }
    Edit-Guest-Properties $vm $vm_properties

    if ($secure_boot) {
      $firmware_properties = @{
        SecureBoot = if ($secure_boot) {"On"} else {"Off"}
      }
      if ($secure_boot_template) {
        $firmware_properties.SecureBootTemplate = $secure_boot_template
      }
      Edit-Guest-Firmware $vm $firmware_properties
    }

    if ($disks) {
      foreach ($disk in $disks) {
        $vm_disk = Add-Guest-HardDiskDrive $vm $disk
        if ($disk.ContainsKey('first_boot_device')) {
          # If first_boot_device is defined
          if ($disk.first_boot_device) {
            Edit-Guest-Firmware $vm @{
              FirstBootDevice = $vm_disk
            }
          }
        }
      }
    }

    if ($network_adapters) {
      $vm_network_adapters = @()
      foreach($vm_network_adapter in $vm.NetworkAdapters) {
        $vm_network_adapters += @{
          name = $vm_network_adapter.Name
          switch_name = $vm_network_adapter.SwitchName
        }
      }
      if ($vm_network_adapters.Count -eq 0) {
        # No network adapter present on VM all adapters should be added
        foreach($network_adapter in $network_adapters) {
          Add-Guest-NetworkAdapter $vm $network_adapter
        }
      }
      else {
        # Network adapter present on VM, diff to determine what to do
        $network_adapter_diffs = Compare-Object -ReferenceObject $network_adapters -DifferenceObject $vm_network_adapters -IncludeEqual -Property Name -PassThru
        foreach ($diff in $network_adapter_diffs) {
          if ($diff.SideIndicator -eq "<=") {
            # Network adapter defined but not existing
            Add-Guest-NetworkAdapter $vm $diff
          }
          elseif ($diff.SideIndicator -eq "==") {
            # Adapter defined and existing, call update
            Edit-Guest-NetworkAdapter $vm $diff
          }
          elseif ($diff.SideIndicator -eq "=>") {
            # Adapter undefined but present on machine, so remove
            Remove-Guest-NetworkAdapter $vm $diff
          }
        }
      }
    }
  }
  return $vm
}

#TODO: Implement diff_mode
Function Edit-Guest([Microsoft.HyperV.PowerShell.VirtualMachine] $vm) {
  $properties = @{
    ProcessorCount = $cpu
    MemoryStartup  = $memory
  }
  Edit-Guest-Properties $vm $properties

  if ($secure_boot) {
    $firmware_properties = @{
      SecureBoot = if ($secure_boot) {"On"} else {"Off"}
    }
    if ($secure_boot_template) {
      $firmware_properties.SecureBootTemplate = $secure_boot_template
    }
    Edit-Guest-Firmware $vm $firmware_properties
  }

  if ($disks) {
    $vm_vhds = @()
    foreach($vm_disk in $vm.HardDrives) {
      # Get VHD matching the harddrive path, the HardDrive object lack properties like size and parentPath
      $vm_vhd = Get-VHD @get_args -Path $vm_disk.Path
      $vm_vhds += @{
        path = $vm_vhd.Path
        size = $vm_vhd.Size
        parent_path = $vm_vhd.ParentPath
      }
    }
    if ($vm_vhds.Count -eq 0) {
      # No disk present on VM all disk should be added
      foreach ($disk in $disks) {
        Add-Guest-HardDiskDrive $vm $disk
      }
    } else {
      # Disks present on VM, diff to determine what to do
      $vhd_diffs = Compare-Object -ReferenceObject $disks -DifferenceObject $vm_vhds -IncludeEqual -Property Path -PassThru
      foreach ($diff in $vhd_diffs) {
        if ($diff.SideIndicator -eq "<=") {
          # Disk defined but not existing
          $vm_disk = Add-Guest-HardDiskDrive $vm $diff
        }
        elseif ($diff.SideIndicator -eq "==") {
          # Disk defined and existing, call update
          $vm_disk = Edit-Guest-HardDisk $vm $diff
        }
        elseif ($diff.SideIndicator -eq "=>") {
          # Disk undefined but present on machine, so remove
          Remove-Guest-HardDisk $vm $diff
        }

        if ($vm_disk -and $diff.ContainsKey('first_boot_device')) {
          # If first_boot_device is defined
          if ($diff.first_boot_device) {
            Edit-Guest-Firmware $vm @{
              FirstBootDevice = $vm_disk
            }
          }
        }
      }
    }
  }

  if ($network_adapters) {
    $vm_network_adapters = @()
    foreach($vm_network_adapter in $vm.NetworkAdapters) {
      $vm_network_adapters += @{
        name = $vm_network_adapter.Name
        switch_name = $vm_network_adapter.SwitchName
      }
    }
    if ($vm_network_adapters.Count -eq 0) {
      # No network adapter present on VM all adapters should be added
      foreach($network_adapter in $network_adapters) {
        Add-Guest-NetworkAdapter $vm $network_adapter
      }
    }
    else {
      # Network adapter present on VM, diff to determine what to do
      $network_adapter_diffs = Compare-Object -ReferenceObject $network_adapters -DifferenceObject $vm_network_adapters -IncludeEqual -Property Name -PassThru
      foreach ($diff in $network_adapter_diffs) {
        if ($diff.SideIndicator -eq "<=") {
          # Network adapter defined but not existing
          Add-Guest-NetworkAdapter $vm $diff
        }
        elseif ($diff.SideIndicator -eq "==") {
          # Adapter defined and existing, call update
          Edit-Guest-NetworkAdapter $vm $diff
        }
        elseif ($diff.SideIndicator -eq "=>") {
          # Adapter undefined but present on machine, so remove
          Remove-Guest-NetworkAdapter $vm $diff
        }
      }
    }
  }
}

Function Remove-Guest([Microsoft.HyperV.PowerShell.VirtualMachine] $vm) {
  if ($module.CheckMode) {
    return $module.Result.changed = $true
  }

  # Has to be poweredoff first
  if ($vm.State -eq "Running") {
    Stop-Guest $vm
  }

  # Remove-VM does not remove the harddisks
  if ($disks) {
    foreach ($disk in $disks) {
      Remove-Guest-HardDisk $vm $disk
    }
  }

  try {
    Remove-VM @set_args -VM $vm -Force
    $module.Result.changed = $true
  }
  catch {
    $module.FailJson("Failed to remove VM", $_.Exception)
  }
  return $vm
}

Function New-VirtualHardDisk([hashtable] $disk) {
  if ($module.CheckMode) {
    return $module.Result.changed = $true
  }

  $new_vhd_args = @{
    Path      = $disk.path
    SizeBytes = $disk.size
  }

  if ($disk.ContainsKey("parent_path")) {
    # If parent_path defined
    $new_vhd_args.ParentPath = $disk.parent_path
    $new_vhd_args.Differencing = $true
  }
  try {
    New-VHD @set_args @new_vhd_args > $null
    $module.Result.changed = $true
  }
  catch {
    $module.FailJson("Failed to create VHD", $_.Exception)
  }
}

Function Add-Guest-HardDiskDrive([Microsoft.HyperV.PowerShell.VirtualMachine] $vm, [Hashtable] $disk) {
  if ($module.CheckMode) {
    return $module.Result.changed = $true
  }

  if (-Not $(Test-Path -LiteralPath $disk.path)) {
    New-VirtualHardDisk $disk
  }
  try {
    $vm_disk = Add-VMHardDiskDrive @set_args -VM $vm -Path $disk.path -Passthru
    $module.Result.changed = $true
    return $vm_disk
  }
  catch {
    $module.FailJson("Failed to add VHD", $_.Exception)
  }
}

Function Edit-Guest-HardDisk([Microsoft.HyperV.PowerShell.VirtualMachine] $vm, [Hashtable] $disk) {
  if ($module.CheckMode) {
    return $module.Result.changed = $true
  }

  $vm_disk = $vm.HardDrives | Where-Object {$_.Path -eq $disk.path}
  $vm_vhd = $vm_disk | Get-VHD @get_args

  if ($disk.size -ne $vm_vhd.Size) {
    try {
      Resize-VHD @set_args -Path $disk.path -SizeBytes $disk.size
      $module.Result.changed = $true
    }
    catch {
      $module.FailJson("Failed to expand VHD", $_.Exception)
    }
  }
  if ($disk.ContainsKey("first_boot_device")) {
    if ($disk.first_boot_device) {
        Edit-Guest-Firmware $vm @{
        FirstBootDevice = $vm_disk
      }
    }
  }
}

Function Remove-Guest-HardDisk([Microsoft.HyperV.PowerShell.VirtualMachine] $vm, [Hashtable] $disk) {
  if ($module.CheckMode) {
    return $module.Result.changed = $true
  }

  $vm_disk = $vm.HardDrives | Where-Object {$_.Path -eq $disk.path}
  # When vm_disk not empty, the disk is connected to the VM
  if ($vm_disk) {
    # Remove disk from VM
    try {
      Remove-VMHardDiskDrive @set_args -VMHardDiskDrive $vm_disk
      $module.Result.changed = $true
    } catch {
      $module.FailJson("Failed to remove VHD from VM", $_.Exception)
    }
    # When state absent remove VHD from disk
    if ($state -eq "absent") {
      try {
        Remove-Item -LiteralPath $disk.path
        $module.Result.changed = $true
      } catch {
        $module.FailJson("Failed to remove VHD from VM", $_.Exception)
      }
    }
  }
  else {
    $module.FailJson("Failed to remove VHD: $($disk.path) not present on the VM")
  }
}
Function Add-Guest-NetworkAdapter([Microsoft.HyperV.PowerShell.VirtualMachine] $vm, [Hashtable] $network_adapter) {
  if ($module.CheckMode) {
    return $module.Result.changed = $true
  }

  $add_network_args = @{
    VM   = $vm
    Name = $network_adapter.name
  }

  if ($network_adapter.ContainsKey("switch_name")) {
    $add_network_args.SwitchName = $network_adapter.switch_name
  }
  try {
    Add-VMNetworkAdapter @set_args @add_network_args
    $module.Result.changed = $true
  }
  catch {
    $module.FailJson("Failed to add network adapter", $_.Exception)
  }
}

Function Edit-Guest-NetworkAdapter([Microsoft.HyperV.PowerShell.VirtualMachine] $vm, [Hashtable] $network_adapter) {
  if ($module.CheckMode) {
    return $module.Result.changed = $true
  }

  $vm_network_adapter = $vm.NetworkAdapters | Where-Object {$_.Name -eq $network_adapter.name}
  if ($vm_network_adapter -is [System.Array]) {
    $module.FailJson("Failed to update network adapter: Two network adapters found with the name: $($network_adapter.name)")
  }

  if ($network_adapter.ContainsKey("switch_name")) {
    if ($vm_network_adapter.SwitchName) {
      # Network adapter currently connected to switch, check for change
      if ($network_adapter.switch_name -ne $vm_network_adapter.SwitchName) {
        try {
          Connect-VMNetworkAdapter @set_args -VMNetworkAdapter $vm_network_adapter -SwitchName $network_adapter.switch_name
          $module.Result.changed = $true
        }
        catch {
          $module.FailJson("Failed to update network adapter", $_.Exception)
        }
      }
    } else {
      # SwitchName is null, adapter not connected to switch
      try {
        Connect-VMNetworkAdapter @set_args -VMNetworkAdapter $vm_network_adapter -SwitchName $network_adapter.switch_name
        $module.Result.changed = $true
      }
      catch {
        $module.FailJson("Failed to update network adapter", $_.Exception)
      }
    }
  }
}

Function Remove-Guest-NetworkAdapter([Microsoft.HyperV.PowerShell.VirtualMachine] $vm, [Hashtable] $network_adapter) {
  if ($module.CheckMode) {
    return $module.Result.changed = $true
  }

  $vm_network_adapter = $vm.NetworkAdapters | Where-Object {$_.Name -eq $network_adapter.name}
  if ($vm_network_adapter -is [System.Array]) {
    $module.FailJson("Failed to delete network adapter: Two network adapters found with the name: $($network_adapter.name)")
  }
  else {
    try {
      Remove-VMNetworkAdapter @set_args -VMNetworkAdapter $vm_network_adapter
      $module.Result.changed = $true
    }
    catch {
      $module.FailJson("Failed to delete network adapter", $_.Exception)
    }
  }
}

Function Edit-Guest-Properties([Microsoft.HyperV.PowerShell.VirtualMachine] $vm, [Hashtable] $properties) {
  if ($module.CheckMode) {
    return $module.Result.changed = $true
  }

  $set_vm_args = @{}
  foreach ($property in $properties.GetEnumerator()) {
    if ($vm.$($property.Name) -ne $property.Value) {
      # If value differs append to arguments
      if ($property.Name -eq "SecureBoot") {
        # Set parameter is different from property of VM
        $set_vm_args.EnableSecureBoot = $property.Value
      }
      else {
        $set_vm_args.$($property.Name) = $property.Value
      }
    }
  }
  if ($set_vm_args.Count -ne 0) {
    # If there is a parameter to set
    try {
      Set-VM -VM $vm @set_args @set_vm_args
      $module.Result.changed = $true
    }
    catch {
      $module.FailJson("Failed to update VM", $_.Exception)
    }
  }
}

Function Edit-Guest-Firmware([Microsoft.HyperV.PowerShell.VirtualMachine] $vm, [Hashtable] $firmware_values) {
  if ($module.CheckMode) {
    return $module.Result.changed = $true
  }

  $firmware_current_state = Get-VMFirmware @get_args -VM $vm
  $set_firmware_args = @{}
  foreach ($value in $firmware_values.GetEnumerator()) {
    if ($value.Name -eq "FirstBootDevice") {
      # Check if first in bootorder is the same disk as passed HardDiskDrive object
      if ($firmware_current_state.BootOrder[0].Device.Path -ne $value.Value.Path) {
        $set_firmware_args.$($value.Name) = $value.Value
      }
    }
    elseif ($firmware_current_state.$($value.Name) -ne $value.Value) {
      # If value differs from current state append to arguments
      $set_firmware_args.$($item.Name) = $value.Value
    }
  }
  if ($set_firmware_args.Count -ne 0) {
    # If there is a parameter to set
    try {
      Set-VMFirmware -VM $vm @set_args @set_firmware_args
      $module.Result.changed = $true
    }
    catch {
      $module.FailJson("Failed to update firmware", $_.Exception)
    }
  }
}

Function Start-Guest([Microsoft.HyperV.PowerShell.VirtualMachine] $vm) {
  if ($vm.State -eq "Off") {
    if ($module.CheckMode) {
      $module.Result.changed = $true
      return
    }

    try {
      Start-VM @set_args -VM $vm
      $module.Result.changed = $true
    }
    catch {
      $module.FailJson("Failed to start VM", $_.Exception)
    }

    if ($wait_for_ip) {
      Wait-For-Ip $vm
    }
  }
}

Function Stop-Guest([Microsoft.HyperV.PowerShell.VirtualMachine] $vm) {
  if ($vm.State -eq "Running") {
    if ($module.CheckMode) {
      $module.Result.changed = $true
      return
    }

    $stop_args = @{
      VM      = $vm
      TurnOff = $force_stop
    }
    try {
      Stop-VM @set_args @stop_args -Force
      $module.Result.changed = $true
    }
    catch {
      $module.FailJson("Failed to stop VM", $_.Exception)
    }
  }
}

Function Restart-Guest([Microsoft.HyperV.PowerShell.VirtualMachine] $vm) {
  if ($vm.State -eq "Running") {
    if ($module.CheckMode) {
      $module.Result.changed = $true
      return
    }

    try {
      Restart-VM @set_args -VM $vm -Force
      $module.Result.changed = $true
    }
    catch {
      $module.FailJson("Failed to restart VM", $_.Exception)
    }

    if ($wait_for_ip) {
      Wait-For-Ip $vm
    }
  }
}

Function Get-Guest() {
  # Get current state of VM, returns empty hashtable on error
  try {
    $vm = Get-VM @get_args -Name $name
  }
  catch {
    if ($_.Exception.Message -Match "Hyper-V was unable to find a virtual machine with name") {
      # VM does not exist
      $vm = @{
        name  = $name
        state = "absent"
      }
    }
    else {
      $module.FailJson("Failed to get state VM", $_.Exception)
      $vm = @{}
    }
  }
  return $vm
}

Function Format-Guest([Microsoft.HyperV.PowerShell.VirtualMachine] $vm) {
  if ($vm.IsDeleted) {
    # VM is deleted
    return @{
      name  = $vm.Name
      state = "absent"
    }
  }
  else {
    # VM still exists
    $vm_json = ConvertTo-Json -InputObject $vm -Depth 3
    return ConvertFrom-Json -InputObject $vm_json
  }
}

Function Wait-For-Ip([Microsoft.HyperV.PowerShell.VirtualMachine] $vm) {
  $timer = [Diagnostics.Stopwatch]::StartNew()
  # Loop until first network adapter has an IP address
  while (-not ($vm.NetworkAdapters[0].IPAddresses.length -gt 0)) {
    if ($timer.Elapsed.TotalSeconds -ge $timeout) {
      # Break and error when timer exeeds timout set for waiting
      $module.FailJson("Failed to get IPV4 for VM, timeout exceeded")
      break;
    }
  }
  $timer.Stop()
}

###################################################################
#
# MAIN
#
###################################################################
$get_args = @{
  ErrorAction = "Stop"
}
if ($hostserver) {
  $get_args.ComputerName = $hostserver
}

$set_args = $get_args.Clone()
$set_args.WhatIf = $module.CheckMode

# Normalize disk_paths, from YAML comes with double backslash so -eq does not work with Hyper-V provided paths
# Convert defined size of memory and disks to bytes by doing /1
# TODO: Check if better function or implementation is available for normalizing disk paths
foreach ($disk in $disks) {
  $disk.path = $disk.path.Replace('\\', '\')
  $disk.size = $disk.size / 1
}
$memory = $memory / 1

$vm = Get-Guest

if ($vm -is [Microsoft.HyperV.PowerShell.VirtualMachine]) {
  # VM exists
  if ($state -eq "present") {
    Edit-Guest $vm
    if ($vm.State -eq "Off") {
      Start-Guest $vm
    }
  }
  elseif ($state -eq "created") {
    Edit-Guest $vm
  }
  elseif ($state -eq "absent") {
    Remove-Guest $vm
  }
  elseif ($state -eq "started") {
    Edit-Guest $vm
    Start-Guest $vm
  }
  elseif ($state -eq "stopped") {
    Edit-Guest $vm
    Stop-Guest $vm
  }
  elseif ($state -eq "restarted") {
    Edit-Guest $vm
    if ($vm.State -eq "Running") {
      Restart-Guest $vm
    }
    elseif ($vm.State -eq "Off") {
      Start-Guest $vm
    }
  }
}
elseif ($vm.Count -gt 0) {
  # Get-Guest returned a filled hashtable so curret state must be absent
  if ($state -eq "present") {
    $vm = New-Guest
    if ($vm) {
      Start-Guest $vm
    }
  }
  elseif ($state -eq "created") {
    $vm = New-Guest
  }
}

# When VM is a object format to JSON for return
if ($vm -is [Microsoft.HyperV.PowerShell.VirtualMachine]) {
  $vm = Format-Guest $vm
}

$module.Result.instance = $vm
$module.ExitJson()