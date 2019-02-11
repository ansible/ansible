Describe -Name 'Test02' {
    It -name 'Second Test' {
        {Get-Service} | Should Throw
    }
}