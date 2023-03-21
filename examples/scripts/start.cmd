@ECHO OFF
SET ThisScriptsDirectory=%~dp0
SET PowerShellScriptPath=%ThisScriptsDirectory%ConfigureRemotingForAnsible.ps1
PowerShell -WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -Command "& {Start-Process -WindowStyle hidden PowerShell -ArgumentList '-WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -File ""%PowerShellScriptPath%""' -Verb RunAs}"