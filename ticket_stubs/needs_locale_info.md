This issue may be related to locale or text encoding. To help troubleshoot and reproduce the issue, we need some additional information.

If running ansible from the command line, try to gather this information from the same shell and terminal.

To collect the locale, language and text encoding settings, use the ```locale``` command:
``` shell
    locale
```

That output should look something like:
```
LANG="en_US.UTF-8"
LC_COLLATE="en_US.UTF-8"
LC_CTYPE="en_US.UTF-8"
LC_MESSAGES="en_US.UTF-8"
LC_MONETARY="en_US.UTF-8"
LC_NUMERIC="en_US.UTF-8"
LC_TIME="en_US.UTF-8"
LC_ALL=
```

If 'sudo' or similar tools are being used, we will need the locale info from a sudo shell as well.
For example:
``` shell
sudo locale
```

Also include the value of the ```TERM``` environment variable. To get the info, paste the output of echoing the ```TERM``` variable from a shell like:
``` shell
echo $TERM
```

Cut & paste the output from those commands into a comment here. To preserve the original
formatting, use \`\`\` around the text, for example:

\`\`\`
    LANG="en_US.UTF-8"
    LC_COLLATE="en_US.UTF-8"
    LC_CTYPE="en_US.UTF-8"
    LC_MESSAGES="en_US.UTF-8"
    LC_MONETARY="en_US.UTF-8"
    LC_NUMERIC="en_US.UTF-8"
    LC_TIME="en_US.UTF-8"
    LC_ALL=
\`\`\`
