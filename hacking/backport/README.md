# backport scripts

This directory contains scripts useful for dealing with and maintaining
backports. Scripts in it depend on pygithub, and expect a valid environment
variable called `GITHUB_TOKEN`.

To generate a Github token, go to <https://github.com/settings/tokens/new>

## `backport_of_line_adder.py`

This script will attempt to add a reference line ("Backport of ...") to a new
backport PR.

It is called like this:

```shell
./backport_of_line_adder.py <backport> <original PR>
```

However, it contains some logic to try to automatically deduce the original PR
for you. You can trigger that logic by making the second argument be `auto`.

```shell
./backport_of_line_adder.py 12345 auto
```

... for example, will look for an appropriate reference to add to backport PR #12345.

The script will prompt you before making any changes, and give you a chance to
review the PR that it is about to reference.

It will add the reference right below the 'SUMMARY' header if it exists, or
otherwise it will add it to the very bottom of the PR body.
