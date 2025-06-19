@{
    language_mode = $ExecutionContext.SessionState.LanguageMode.ToString()
    whoami = [Environment]::UserName
    ünicode = $args[0]
} | ConvertTo-Json
