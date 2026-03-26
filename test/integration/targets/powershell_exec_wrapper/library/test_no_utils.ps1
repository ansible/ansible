#!powershell

#AnsibleRequires -Wrapper

@{
    changed = $false
    complex_args = $complex_args
} | ConvertTo-Json -Depth 99
