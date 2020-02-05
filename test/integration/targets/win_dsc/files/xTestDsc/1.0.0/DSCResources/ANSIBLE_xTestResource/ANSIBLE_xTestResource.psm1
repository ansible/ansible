#Requires -Version 5.0 -Modules CimCmdlets

Function ConvertFrom-CimInstance {
    param(
        [Parameter(Mandatory=$true)][CimInstance]$Instance
    )
    $hashtable = @{
        _cim_instance = $Instance.CimSystemProperties.ClassName
    }
    foreach ($prop in $Instance.CimInstanceProperties) {
        $hashtable."$($prop.Name)" = ConvertTo-OutputValue -Value $prop.Value
    }
    return $hashtable
}

Function ConvertTo-OutputValue {
    param($Value)

    if ($Value -is [DateTime[]]) {
        $Value = $Value | ForEach-Object { $_.ToString("o") }
    } elseif ($Value -is [DateTime]) {
        $Value = $Value.ToString("o")
    } elseif ($Value -is [Double]) {
        $Value = $Value.ToString()  # To avoid Python 2 double parsing issues on test validation
    } elseif ($Value -is [Double[]]) {
        $Value = $Value | ForEach-Object { $_.ToString() }
    } elseif ($Value -is [PSCredential]) {
        $password = $null
        $password_ptr = [System.Runtime.InteropServices.Marshal]::SecureStringToGlobalAllocUnicode($Value.Password)
        try {
            $password = [System.Runtime.InteropServices.Marshal]::PtrToStringUni($password_ptr)
        } finally {
            [System.Runtime.InteropServices.Marshal]::ZeroFreeGlobalAllocUnicode($password_ptr)
        }
        $Value = @{
            username = $Value.Username
            password = $password
        }
    } elseif ($Value -is [CimInstance[]]) {
        $value_list = [System.Collections.Generic.List`1[Hashtable]]@()
        foreach ($cim_instance in $Value) {
            $value_list.Add((ConvertFrom-CimInstance -Instance $cim_instance))
        }
        $Value = $value_list.ToArray()
    } elseif ($Value -is [CimInstance]) {
        $Value = ConvertFrom-CimInstance -Instance $Value
    }

    return ,$Value
}

Function Get-TargetResource
{
    [CmdletBinding()]
    [OutputType([Hashtable])]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet("Present", "Absent")]
        [String] $Ensure = "Present",

        [Parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [String] $Path
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
        [String] $Ensure = "Present",

        [Parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [String] $Path,

        [String] $DefaultParam = "Default",
        [String] $StringParam,
        [String[]] $StringArrayParam,
        [SByte] $Int8Param,
        [SByte[]] $Int8ArrayParam,
        [Byte] $UInt8Param,
        [Byte[]] $UInt8ArrayParam,
        [Int16] $Int16Param,
        [Int16[]] $Int16ArrayParam,
        [UInt16] $UInt16Param,
        [UInt16[]] $UInt16ArrayParam,
        [Int32] $Int32Param,
        [Int32[]] $Int32ArrayParam,
        [UInt32] $UInt32Param,
        [UInt32[]] $UInt32ArrayParam,
        [Int64] $Int64Param,
        [Int64[]] $Int64ArrayParam,
        [UInt64] $UInt64Param,
        [UInt64[]] $UInt64ArrayParam,
        [Bool] $BooleanParam,
        [Bool[]] $BooleanArrayParam,
        [Char] $CharParam,
        [Char[]] $CharArrayParam,
        [Single] $SingleParam,
        [Single[]] $SingleArrayParam,
        [Double] $DoubleParam,
        [Double[]] $DoubleArrayParam,
        [DateTime] $DateTimeParam,
        [DateTime[]] $DateTimeArrayParam,
        [PSCredential] $PSCredentialParam,
        [CimInstance[]] $HashtableParam,
        [CimInstance] $CimInstanceParam,
        [CimInstance[]] $CimInstanceArrayParam,
        [CimInstance] $NestedCimInstanceParam,
        [CimInstance[]] $NestedCimInstanceArrayParam
    )

    $info = @{
        Version = "1.0.0"
        Ensure = @{
            Type = $Ensure.GetType().FullName
            Value = $Ensure
        }
        Path = @{
            Type = $Path.GetType().FullName
            Value = $Path
        }
        DefaultParam = @{
            Type = $DefaultParam.GetType().FullName
            Value = $DefaultParam
        }
    }

    foreach ($kvp in $PSCmdlet.MyInvocation.BoundParameters.GetEnumerator()) {
        $info."$($kvp.Key)" = @{
            Type = $kvp.Value.GetType().FullName
            Value = (ConvertTo-OutputValue -Value $kvp.Value)
        }
    }

    if (Test-Path -Path $Path) {
        Remove-Item -Path $Path -Force > $null
    }
    New-Item -Path $Path -ItemType File > $null
    Set-Content -Path $Path -Value (ConvertTo-Json -InputObject $info -Depth 10) > $null
    Write-Verbose -Message "set verbose"
    Write-Warning -Message "set warning"
}

Function Test-TargetResource
{
    [CmdletBinding()]
    [OutputType([Boolean])]
    param
    (
        [Parameter(Mandatory = $true)]
        [ValidateSet("Present", "Absent")]
        [String] $Ensure = "Present",

        [Parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [String] $Path,

        [String] $DefaultParam = "Default",
        [String] $StringParam,
        [String[]] $StringArrayParam,
        [SByte] $Int8Param,
        [SByte[]] $Int8ArrayParam,
        [Byte] $UInt8Param,
        [Byte[]] $UInt8ArrayParam,
        [Int16] $Int16Param,
        [Int16[]] $Int16ArrayParam,
        [UInt16] $UInt16Param,
        [UInt16[]] $UInt16ArrayParam,
        [Int32] $Int32Param,
        [Int32[]] $Int32ArrayParam,
        [UInt32] $UInt32Param,
        [UInt32[]] $UInt32ArrayParam,
        [Int64] $Int64Param,
        [Int64[]] $Int64ArrayParam,
        [UInt64] $UInt64Param,
        [UInt64[]] $UInt64ArrayParam,
        [Bool] $BooleanParam,
        [Bool[]] $BooleanArrayParam,
        [Char] $CharParam,
        [Char[]] $CharArrayParam,
        [Single] $SingleParam,
        [Single[]] $SingleArrayParam,
        [Double] $DoubleParam,
        [Double[]] $DoubleArrayParam,
        [DateTime] $DateTimeParam,
        [DateTime[]] $DateTimeArrayParam,
        [PSCredential] $PSCredentialParam,
        [CimInstance[]] $HashtableParam,
        [CimInstance] $CimInstanceParam,
        [CimInstance[]] $CimInstanceArrayParam,
        [CimInstance] $NestedCimInstanceParam,
        [CimInstance[]] $NestedCimInstanceArrayParam
    )
    Write-Verbose -Message "test verbose"
    Write-Warning -Message "test warning"
    $exists = Test-Path -LiteralPath $Path -PathType Leaf
    if ($Ensure -eq "Present") {
        $exists
    } else {
        -not $exists
    }
}

Export-ModuleMember -Function *-TargetResource

