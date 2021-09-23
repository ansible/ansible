"""Test runner for all Ansible tests."""
from __future__ import annotations

import os
import sys

# This import should occur as early as possible.
# It must occur before subprocess has been imported anywhere in the current process.
from .init import (
    CURRENT_RLIMIT_NOFILE,
)

from .util import (
    ApplicationError,
    display,
    MAXFD,
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


def main():
    """Main program function."""
    try:
        os.chdir(data_context().content.root)
        args = parse_args()
        config = args.config(args)  # type: CommonConfig
        display.verbosity = config.verbosity
        display.truncate = config.truncate
        display.redact = config.redact
        display.color = config.color
        display.info_stderr = config.info_stderr
        configure_timeout(config)

        display.info('RLIMIT_NOFILE: %s' % (CURRENT_RLIMIT_NOFILE,), verbosity=2)
        display.info('MAXFD: %d' % MAXFD, verbosity=2)

        delegate_args = None
        target_names = None

        try:
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
            # noinspection PyTypeChecker
            delegate(config, *delegate_args)

        if target_names:
            for target_name in target_names:
                print(target_name)  # info goes to stderr, this should be on stdout

        display.review_warnings()
        config.success = True
    except ApplicationWarning as ex:
        display.warning(u'%s' % ex)
        sys.exit(0)
    except ApplicationError as ex:
        display.error(u'%s' % ex)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(2)
    except BrokenPipeError:
        sys.exit(3)
