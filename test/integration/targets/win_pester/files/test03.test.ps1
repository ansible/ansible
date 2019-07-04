Describe -Name 'Test03 without tag' {
    It -name 'Third Test without tag' {
        {Get-Service} | Should Not Throw
    }
}

Describe -Name 'Test03 with tag' -Tag tag1 {
    It -name 'Third Test with tag' {
        {Get-Service} | Should Not Throw
    }
}