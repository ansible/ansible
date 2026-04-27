#!powershell

#AnsibleRequires -Wrapper

@{
    env_vars = @(Get-ChildItem -LiteralPath Env: | ForEach-Object { "$($_.Name)=$($_.Value)" })
} | ConvertTo-Json -Compress
