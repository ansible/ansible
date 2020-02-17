#!powershell

# Copyright: (c) 2020, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic

$spec = @{
    options = @{
        domain_password = @{ type = 'str'; no_log = $true }
        domain_server = @{ type = 'str' }
        domain_username = @{ type = 'str' }
        filter = @{ type = 'str' }
        identity = @{ type = 'str' }
        include_deleted = @{ type = 'bool'; default = $false }
        ldap_filter = @{ type = 'str' }
        properties = @{ type = 'list'; elements = 'str' }
        search_base = @{ type = 'str' }
        search_scope = @{ type = 'str'; choices = @('base', 'one_level', 'subtree') }
    }
    supports_check_mode = $true
    mutually_exclusive = @(
        @('filter', 'identity', 'ldap_filter'),
        @('identity', 'search_base'),
        @('identity', 'search_scope')
    )
    required_one_of = @(
        ,@('filter', 'identity', 'ldap_filter')
    )
    required_together = @(,@('domain_username', 'domain_password'))
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$module.Result.objects = @()  # Always ensure this is returned even in a failure.

$domainServer = $module.Params.domain_server
$domainPassword = $module.Params.domain_password
$domainUsername = $module.Params.domain_username
$filter = $module.Params.filter
$identity = $module.Params.identity
$includeDeleted = $module.Params.include_deleted
$ldapFilter = $module.Params.ldap_filter
$properties = $module.Params.properties
$searchBase = $module.Params.search_base
$searchScope = $module.Params.search_scope

$credential = $null
if ($domainUsername) {
    $credential = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList @(
        $domainUsername,
        (ConvertTo-SecureString -AsPlainText -Force -String $domainPassword)
    )
}

Function ConvertTo-OutputValue {
    [CmdletBinding()]
    Param (
        [Parameter(Mandatory=$true)]
        [AllowNull()]
        [Object]
        $InputObject
    )

    if ($InputObject -is [System.Security.Principal.SecurityIdentifier]) {
        # Syntax: SID - Only serialize the SID as a string and not the other metadata properties.
        $sidInfo = @{
            Sid = $InputObject.Value
        }

        # Try and map the SID to the account name, this may fail if the SID is invalid or not mappable.
        try {
            $sidInfo.Name = $InputObject.Translate([System.Security.Principal.NTAccount]).Value
        } catch [System.Security.Principal.IdentityNotMappedException] {
            $sidInfo.Name = $null
        }

        $sidInfo
    } elseif ($InputObject -is [Byte[]]) {
        # Syntax: Octet String - By default will serialize as a list of decimal values per byte, instead return a
        # Base64 string as Ansible can easily parse that.
        [System.Convert]::ToBase64String($InputObject)
    } elseif ($InputObject -is [DateTime]) {
        # Syntax: UTC Coded Time - .NET DateTimes serialized as in the form "Date(FILETIME)" which isn't easily
        # parsable by Ansible, instead return as an ISO 8601 string in the UTC timezone.
        [TimeZoneInfo]::ConvertTimeToUtc($InputObject).ToString("o")
    } elseif ($InputObject -is [System.Security.AccessControl.ObjectSecurity]) {
        # Complex object which isn't easily serializable. Instead we should just return the SDDL string. If a user
        # needs to parse this then they really need to reprocess the SDDL string and process their results on another
        # win_shell task.
        $InputObject.GetSecurityDescriptorSddlForm(([System.Security.AccessControl.AccessControlSections]::All))
    } else {
        # Syntax: (All Others) - The default serialization handling of other syntaxes are fine, don't do anything.
        $InputObject
    }
}

<#
Calling Get-ADObject that returns multiple objects with -Properties * will only return the properties that were set on
the first found object. To counter this problem we will first call Get-ADObject to list all the objects that match the
filter specified then get the properties on each object.
#>

$commonParams = @{
    IncludeDeletedObjects = $includeDeleted
}

if ($credential) {
    $commonParams.Credential = $credential
}

if ($domainServer) {
    $commonParams.Server = $domainServer
}

# First get the IDs for all the AD objects that match the filter specified.
$getParams = @{
    Properties = @('DistinguishedName', 'ObjectGUID')
}

if ($filter) {
    $getParams.Filter = $filter
} elseif ($identity) {
    $getParams.Identity = $identity
} elseif ($ldapFilter) {
    $getParams.LDAPFilter = $ldapFilter
}

# Explicit check on $null as an empty string is different from not being set.
if ($null -ne $searchBase) {
    $getParams.SearchBase = $searchbase
}

if ($searchScope) {
    $getParams.SearchScope = switch($searchScope) {
        base { 'Base' }
        one_level { 'OneLevel' }
        subtree { 'Subtree' }
    }
}

try {
    # We run this in a custom PowerShell pipeline so that users of this module can't use any of the variables defined
    # above in their filter. While the cmdlet won't execute sub expressions we don't want anyone implicitly relying on
    # a defined variable in this module in case we ever change the name or remove it.
    $ps = [PowerShell]::Create()
    $null = $ps.AddCommand('Get-ADObject').AddParameters($commonParams).AddParameters($getParams)
    $null = $ps.AddCommand('Select-Object').AddParameter('Property', @('DistinguishedName', 'ObjectGUID'))

    $foundGuids = @($ps.Invoke())
} catch {
    # Because we ran in a pipeline we can't catch ADIdentityNotFoundException. Instead just get the base exception and
    # do the error checking on that.
    if ($_.Exception.GetBaseException() -is [Microsoft.ActiveDirectory.Management.ADIdentityNotFoundException]) {
        $foundGuids = @()
    } else {
        # The exception is from the .Invoke() call, compare on the InnerException which was what was actually raised by
        # the pipeline.
        $innerException = $_.Exception.InnerException.InnerException
        if ($innerException -is [Microsoft.ActiveDirectory.Management.ADServerDownException]) {
            # Point users in the direction of the double hop problem as that is what is typically the cause of this.
            $msg = "Failed to contact the AD server, this could be caused by the double hop problem over WinRM. "
            $msg += "Try using the module with auth as Kerberos with credential delegation or CredSSP, become, or "
            $msg += "defining the domain_username and domain_password module parameters."
            $module.FailJson($msg, $innerException)
        } else {
            throw $innerException
        }
    }
}

$getParams = @{}
if ($properties) {
    $getParams.Properties = $properties
}
$module.Result.objects = @(foreach ($adId in $foundGuids) {
    try {
        $adObject = Get-ADObject @commonParams @getParams -Identity $adId.ObjectGUID
    } catch {
        $msg = "Failed to retrieve properties for AD Object '$($adId.DistinguishedName): $($_.Exception.Message)"
        $module.Warn($msg)
        continue
    }

    $propertyNames = $adObject.PropertyNames
    $propertyNames += ($properties | Where-Object { $_ -ne '*' })

    # Now process each property to an easy to represent string
    $filteredObject = [Ordered]@{}
    foreach ($name in ($propertyNames | Sort-Object)) {
        # In the case of explicit properties that were asked for but weren't set, Get-ADObject won't actually return
        # the property so this is a defensive check against that scenario.
        if (-not $adObject.PSObject.Properties.Name.Contains($name)) {
            $filteredObject.$name = $null
            continue
        }

        $value = $adObject.$name
        if ($value -is [Microsoft.ActiveDirectory.Management.ADPropertyValueCollection]) {
            $value = foreach ($v in $value) {
                ConvertTo-OutputValue -InputObject $v
            }
        } else {
            $value = ConvertTo-OutputValue -InputObject $value
        }
        $filteredObject.$name = $value
    }

    $filteredObject
})

$module.ExitJson()
