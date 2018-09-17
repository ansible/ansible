# Launchd integration tests

How to run the tests locally on macOS:

```bash
$ ./test/runner/ansible-test integration -v launchd
```

To generate coverage data run the following command:

```bash
$ ./test/runner/ansible-test integration -v --coverage launchd
```

And after the tests finish generate an html report:

```bash
$ ./test/runner/ansible-test coverage html
$ open -a /Applications/Google\ Chrome.app/ test/results/reports/coverage/index.html
```
