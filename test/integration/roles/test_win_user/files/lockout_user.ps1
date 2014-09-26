trap
{
    Write-Error -ErrorRecord $_
    exit 1;
}

$username = $args[0]
[void][system.reflection.assembly]::LoadWithPartialName('System.DirectoryServices.AccountManagement')
$pc = New-Object -TypeName System.DirectoryServices.AccountManagement.PrincipalContext 'Machine', $env:COMPUTERNAME
For ($i = 1; $i -le 10; $i++) {
    try {
        $pc.ValidateCredentials($username, 'b@DP@ssw0rd')
    }
    catch {
        break
    }
}
