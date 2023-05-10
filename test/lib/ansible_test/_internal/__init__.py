"""Test runner for all Ansible tests."""
from __future__ import annotations

import os
import sys
import typing as t

# This import should occur as early as possible.
# It must occur before subprocess has been imported anywhere in the current process.
from .init import (
    CURRENT_RLIMIT_NOFILE,
)

from .constants import (
    STATUS_HOST_CONNECTION_ERROR,
)

from .util import (
    ApplicationError,
    HostConnectionError,
    TimeoutExpiredError,
    display,
)

from .delegation import (
    delegate,
)

from .executor import (
    ApplicationWarning,
    Delegate,
    ListTargets,
)

from .timeout import (
    configure_timeout,
)

from .data import (
    data_context,
)

from .util_common import (
    CommonConfig,
)

from .cli import (
    parse_args,
)

from .provisioning import (
    PrimeContainers,
)


def main(cli_args=None):  # type: (t.Optional[t.List[str]]) -> None
    """Main program function."""
    try:
        os.chdir(data_context().content.root)
        args = parse_args(cli_args)
        config = args.config(args)  # type: CommonConfig
        display.verbosity = config.verbosity
        display.truncate = config.truncate
        display.redact = config.redact
        display.color = config.color
        display.fd = sys.stderr if config.display_stderr else sys.stdout
        configure_timeout(config)

        display.info('RLIMIT_NOFILE: %s' % (CURRENT_RLIMIT_NOFILE,), verbosity=2)

        delegate_args = None
        target_names = None

        try:
            if config.check_layout:
                data_context().check_layout()

            args.func(config)
        except PrimeContainers:
            pass
        except ListTargets as ex:
            # save target_names for use once we exit the exception handler
            target_names = ex.target_names
        except Delegate as ex:
            # save delegation args for use once we exit the exception handler
            delegate_args = (ex.host_state, ex.exclude, ex.require)

        if delegate_args:
            delegate(config, *delegate_args)

        if target_names:
            for target_name in target_names:
                print(target_name)  # display goes to stderr, this should be on stdout

        display.review_warnings()
        config.success = True
    except HostConnectionError as ex:
        display.fatal(str(ex))
        ex.run_callback()
        sys.exit(STATUS_HOST_CONNECTION_ERROR)
    except ApplicationWarning as ex:
        display.warning(u'%s' % ex)
        sys.exit(0)
    except ApplicationError as ex:
        display.fatal(u'%s' % ex)
        sys.exit(1)
    except TimeoutExpiredError as ex:
        display.fatal('%s' % ex)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(2)
    except BrokenPipeError:
        sys.exit(3)
