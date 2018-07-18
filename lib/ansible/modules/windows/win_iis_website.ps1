#!powershell

# Copyright: (c) 2015, Henrik Wallström <henrik@wallstroms.nu>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = "Stop"

$params = Parse-Args $args
$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$application_pool = Get-AnsibleParam -obj $params -name "application_pool" -type "str"
$physical_path = Get-AnsibleParam -obj $params -name "physical_path" -type "str"
$site_id = Get-AnsibleParam -obj $params -name "site_id" -type "str"
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -validateset "absent","restarted","started","stopped"

# Binding Parameters
$bind_port = Get-AnsibleParam -obj $params -name "port" -type "int"
$bind_ip = Get-AnsibleParam -obj $params -name "ip" -type "str"
$bind_hostname = Get-AnsibleParam -obj $params -name "hostname" -type "str"
$bind_ssl = Get-AnsibleParam -obj $params -name "ssl" -type "str"

# Custom site Parameters from string where properties
# are separated by a pipe and property name/values by colon.
# Ex. "foo:1|bar:2"
$parameters = Get-AnsibleParam -obj $params -name "parameters" -type "str"
if($parameters -ne $null) {
  $parameters = @($parameters -split '\|' | ForEach {
    return ,($_ -split "\:", 2);
  })
}


# Ensure WebAdministration module is loaded
if ((Get-Module "WebAdministration" -ErrorAction SilentlyContinue) -eq $null) {
  Import-Module WebAdministration
}

# Result
$result = @{
  site = @{}
  changed = $false
}

# Site info
$site = Get-Website | Where { $_.Name -eq $name }

Try {
  # Add site
  If(($state -ne 'absent') -and (-not $site)) {
    If (-not $physical_path) {
      Fail-Json -obj $result -message "missing required arguments: physical_path"
    }
    ElseIf (-not (Test-Path $physical_path)) {
      Fail-Json -obj $result -message "specified folder must already exist: physical_path"
    }

    $site_parameters = @{
      Name = $name
      PhysicalPath = $physical_path
    }

    If ($application_pool) {
      $site_parameters.ApplicationPool = $application_pool
    }

    If ($site_id) {
        $site_parameters.ID = $site_id
    }

    If ($bind_port) {
      $site_parameters.Port = $bind_port
    }

    If ($bind_ip) {
      $site_parameters.IPAddress = $bind_ip
    }

    If ($bind_hostname) {
      $site_parameters.HostHeader = $bind_hostname
    }

    # Fix for error "New-Item : Index was outside the bounds of the array."
    # This is a bug in the New-WebSite commandlet. Apparently there must be at least one site configured in IIS otherwise New-WebSite crashes.
    # For more details, see http://stackoverflow.com/questions/3573889/ps-c-new-website-blah-throws-index-was-outside-the-bounds-of-the-array
    $sites_list = get-childitem -Path IIS:\sites
    if ($sites_list -eq $null) { $site_parameters.ID = 1 }

    $site = New-Website @site_parameters -Force
    $result.changed = $true
  }

  # Remove site
  If ($state -eq 'absent' -and $site) {
    $site = Remove-Website -Name $name
    $result.changed = $true
  }

  $site = Get-Website | Where { $_.Name -eq $name }
  If($site) {
    # Change Physical Path if needed
    if($physical_path) {
      If (-not (Test-Path $physical_path)) {
        Fail-Json -obj $result -message "specified folder must already exist: physical_path"
      }

      $folder = Get-Item $physical_path
      If($folder.FullName -ne $site.PhysicalPath) {
        Set-ItemProperty "IIS:\Sites\$($site.Name)" -name physicalPath -value $folder.FullName
        $result.changed = $true
      }
    }

    # Change Application Pool if needed
    if($application_pool) {
      If($application_pool -ne $site.applicationPool) {
        Set-ItemProperty "IIS:\Sites\$($site.Name)" -name applicationPool -value $application_pool
        $result.changed = $true
      }
    }

    # Set properties
    if($parameters) {
      $parameters | foreach {
        $property_value = Get-ItemProperty "IIS:\Sites\$($site.Name)" $_[0]

        switch ($property_value.GetType().Name)
        {
            "ConfigurationAttribute" { $parameter_value = $property_value.value }
            "String" { $parameter_value = $property_value }
        }

        if((-not $parameter_value) -or ($parameter_value) -ne $_[1]) {
          Set-ItemProperty "IIS:\Sites\$($site.Name)" $_[0] $_[1]
          $result.changed = $true
        }
      }
    }

    # Set run state
    if (($state -eq 'stopped') -and ($site.State -eq 'Started'))
    {
      Stop-Website -Name $name -ErrorAction Stop
      $result.changed = $true
    }
    if ((($state -eq 'started') -and ($site.State -eq 'Stopped')) -or ($state -eq 'restarted'))
    {
      Start-Website -Name $name -ErrorAction Stop
      $result.changed = $true
    }
  }
}
Catch
{
  Fail-Json -obj $result -message $_.Exception.Message
}

if ($state -ne 'absent')
{
  $site = Get-Website | Where { $_.Name -eq $name }
}

if ($site)
{
  $result.site = @{
    Name = $site.Name
    ID = $site.ID
    State = $site.State
    PhysicalPath = $site.PhysicalPath
    ApplicationPool = $site.applicationPool
    Bindings = @($site.Bindings.Collection | ForEach-Object { $_.BindingInformation })
  }
}

Exit-Json -obj $result
