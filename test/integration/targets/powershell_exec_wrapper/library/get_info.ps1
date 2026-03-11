#!powershell

#AnsibleRequires -Wrapper

if (-not (Get-Variable -Name IsWindows -ErrorAction Ignore)) {
    Set-Variable -Name IsWindows -Value $true
}

@{
    current_time = [DateTime]::Now.ToFileTime()
    is_windows = $IsWindows
} | ConvertTo-Json -Compress
