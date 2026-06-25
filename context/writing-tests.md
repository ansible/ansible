# Writing tests

## Test expectations for pull requests

- Appropriate tests are required and should cover the changed code.
- Unit tests should be pytest style, and functional rather than tightly coupled to mocking.
- Integration tests are required for almost all plugin changes (tests the public API).
- Tests should exercise the actual changed code, not just add random coverage.
