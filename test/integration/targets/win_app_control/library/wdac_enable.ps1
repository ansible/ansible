#!powershell

#AnsibleRequires -CSharpUtil Ansible.Basic

$spec = @{
    options = @{
        remote_tmp_dir = @{
            type = 'path'
            required = $true
        }
    }
}
$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$tmpPath = $module.Params.remote_tmp_dir
$module.Result.changed = $true

$policyPath = Join-Path $tmpPath policy.xml
$certPath = Join-Path $tmpPath signing.cer
# Using $tmpPath has this step fail
$policyBinPath = "$env:windir\System32\CodeIntegrity\SiPolicy.p7b"
$policyName = 'Ansible_AppControl_Test'

Copy-Item -LiteralPath "$env:windir\schemas\CodeIntegrity\ExamplePolicies\DefaultWindows_Enforced.xml" $policyPath

$signScript = {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory)]
        [string]
        $PolicyName,

        [Parameter(Mandatory)]
        [string]
        $PolicyPath,

        [Parameter(Mandatory)]
        [string]
        $PolicyBinPath,

        [Parameter(Mandatory)]
        [string[]]
        $CertPath
    )

    $ErrorActionPreference = 'Stop'

    Set-CIPolicyIdInfo -FilePath $PolicyPath -PolicyName $PolicyName -PolicyId (New-Guid)
    Set-CIPolicyVersion -FilePath $PolicyPath -Version "1.0.0.0"

    $CertPath | ForEach-Object -Process {
        Add-SignerRule -FilePath $PolicyPath -CertificatePath $_ -User
    }
    Set-RuleOption -FilePath $PolicyPath -Option 0          # Enabled:UMCI
    Set-RuleOption -FilePath $PolicyPath -Option 3 -Delete  # Enabled:Audit Mode
    Set-RuleOption -FilePath $PolicyPath -Option 11 -Delete # Disabled:Script Enforcement
    Set-RuleOption -FilePath $PolicyPath -Option 19         # Enabled:Dynamic Code Security

    $null = ConvertFrom-CIPolicy -XmlFilePath $PolicyPath -BinaryFilePath $PolicyBinPath
}

if ($IsCoreCLR) {
    # WDAC cmdlets only work in WinPS so we need to run it in a sub session
    # running as WinPS. We also need to trust the signing certs for pwsh.exe
    # and related DLLs so we export those and pass them to the job.
    $psSigningCerts = Get-ChildItem -LiteralPath $PSHome |
        Where-Object Extension -in @('.dll', '.exe') |
        Get-AuthenticodeSignature |
        Select-Object -ExpandProperty SignerCertificate -Unique |
        ForEach-Object -Process {
            $newCertPath = Join-Path -Path $tmpPath -ChildPath "$($_.Thumbprint).cer"
            [System.IO.File]::WriteAllBytes($newCertPath, $_.Export('Cert'))
            $newCertPath
        }

    Start-Job -ScriptBlock $signScript -ArgumentList @(
        $policyName,
        $policyPath,
        $policyBinPath,
        @($certPath; $psSigningCerts)
    ) -PSVersion 5.1 | Receive-Job -Wait -AutoRemoveJob
}
else {
    & $signScript -PolicyName $policyName -PolicyPath $policyPath -PolicyBinPath $policyBinPath -CertPath $certPath
}

$ciTool = Get-Command -Name CiTool.exe -ErrorAction SilentlyContinue
$policyId = $null
if ($ciTool) {
    $setInfo = & $ciTool --update-policy $policyBinPath *>&1
    if ($LASTEXITCODE) {
        throw "citool.exe --update-policy failed ${LASTEXITCODE}: $setInfo"
    }

    $policyId = & $ciTool --list-policies --json |
        ConvertFrom-Json |
        Select-Object -ExpandProperty Policies |
        Where-Object FriendlyName -eq $policyName |
        Select-Object -ExpandProperty PolicyID
}
else {
    $rc = Invoke-CimMethod -Namespace root\Microsoft\Windows\CI -ClassName PS_UpdateAndCompareCIPolicy -MethodName Update -Arguments @{
        FilePath = $policyBinPath
    }
    if ($rc.ReturnValue) {
        $module.FailJson("PS_UpdateAndCompareCIPolicy Update failed $($rc.ReturnValue)")
    }
}

$module.Result.policy_id = $policyId
$module.Result.path = $policyBinPath
$module.ExitJson()
