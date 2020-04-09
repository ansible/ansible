
<# Module to add local printer to the current system #>

<#
    .SYNOPSIS
    Add local printer to the specified port, printer driver and printer name.

    .PARAMETER portName
    [String]The Unused Port Name for the specified printer.

    .PARAMETER printDriverName
    [String] The Printer Driver to install printer. For Driver Information please check your printer manual.

    .PARAMTER name
    [String] The name which you want to give to printer.
    #>
Function Add-Localprinter {
    [CmdletBinding()]
    Param(
        [Parameter(Mandatory=$true)][string]$portName,
        [Parameter(Mandatory=$true)][string]$printDriverName,
        [Parameter(Mandatory=$true)][string]$name
    )
    #To Add Local Printer by specifying port name, Driver and Printer name
    try {
        $portExists = Get-Printerport -Name $portname -ErrorAction SilentlyContinue
        if (-not $portExists) {
            Add-PrinterPort -name $portName
        }
        $printDriverExists = Get-PrinterDriver -name $printDriverName -ErrorAction SilentlyContinue
        if ($printDriverExists) {
            Add-Printer -Name $name -PortName $portName -DriverName $printDriverName
        }
        else {
            Write-Warning "Printer Driver not installed"
        }
        Restart-Service -Name Spooler -Force
}
    }
    catch {
        # It will throw an error if printer driver,
        # Port or printer name not found
        throw $_
    }

Export-ModuleMember -Function Add-Localprinter
