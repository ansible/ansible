#Requires -Version 5.0 -Modules CimCmdlets

Function Get-TargetResource
{
    [CmdletBinding()]
    [OutputType([Hashtable])]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet("Present", "Absent")]
        [String]
        $Ensure = "Present",

        [Parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [String]
        $Path
    )
    return @{
        Ensure = $Ensure
        Path = $Path
    }
}

Function Set-TargetResource
{
    [CmdletBinding()]
    param
    (
        [Parameter(Mandatory = $true)]
        [ValidateSet("Present", "Absent")]
        [String]
        $Ensure = "Present",

        [Parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [String]
        $Path,

        [String]
        $StringParam,

        [UInt32]
        $UInt32Param,

        [UInt64]
        $UInt64Param,

        [String[]]
        $StringArrayParam,

        [UInt32[]]
        $UInt32ArrayParam,

        [UInt64[]]
        $UInt64ArrayParam,

        [Boolean]
        $BooleanParam,

        [PSCredential]
        $PSCredentialParam,

        [Microsoft.Management.Infrastructure.CimInstance]
        $CimInstanceParam,

        [Microsoft.Management.Infrastructure.CimInstance[]]
        $CimInstanceArrayParam
    )

    $file_contents = @"
xTestResource Version: {{item.version}}

Ensure:
    Type: $($Ensure.GetType().FullName)
    Value: $($Ensure.ToString())

StringParam:
    Type: $($StringParam.GetType().FullName)
    Value: $($StringParam)

UInt32Param:
    Type: $($UInt32Param.GetType().FullName)
    Value: $($UInt32Param.ToString())

UInt64Param:
    Type: $($UInt64Param.GetType().FullName)
    Value: $($UInt64Param.ToString())

StringArrayParam:
    Type: $($StringArrayParam.GetType().FullName)
    Value: [ "$($StringArrayParam -join '", "')" ]

UInt32ArrayParam:
    Type: $($UInt32ArrayParam.GetType().FullName)
    Value: [ $($UInt32ArrayParam -join ', ') ]

UInt64ArrayParam:
    Type: $($UInt64ArrayParam.GetType().FullName)
    Value: [ $($UInt64ArrayParam -join ', ') ]

BooleanParam:
    Type: $($BooleanParam.GetType().FullName)
    Value: $($BooleanParam.ToString())

PSCredentialParam:
    Type: $($PSCredentialParam.GetType().FullName)
    Username: $($PSCredentialParam.GetNetworkCredential().Username)
    Password: $($PSCredentialParam.GetNetworkCredential().Password)

CimInstanceParam:
    Type: $($CimInstanceParam.GetType().FullName)

CimInstanceArrayParam:
    Type: $($CimInstanceArrayParam.GetType().FullName)
"@
    if (Test-Path -Path $Path)
    {
        Remove-Item -Path $Path -Force > $null
    }
    New-Item -Path $Path -ItemType File > $null
    Set-Content -Path $Path -Value $file_contents > $null
}

Function Test-TargetResource
{
    [CmdletBinding()]
    [OutputType([Boolean])]
    param
    (
        [Parameter(Mandatory = $true)]
        [ValidateSet("Present", "Absent")]
        [String]
        $Ensure = "Present",

        [Parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [String]
        $Path,

        [String]
        $StringParam,

        [UInt32]
        $UInt32Param,

        [UInt64]
        $UInt64Param,

        [String[]]
        $StringArrayParam,

        [UInt32[]]
        $UInt32ArrayParam,

        [UInt64[]]
        $UInt64ArrayParam,

        [Boolean]
        $BooleanParam,

        [PSCredential]
        $PSCredentialParam,

        [Microsoft.Management.Infrastructure.CimInstance]
        $CimInstanceParam,

        [Microsoft.Management.Infrastructure.CimInstance[]]
        $CimInstanceArrayParam
    )
    return $false
}

Export-ModuleMember -Function *-TargetResource
