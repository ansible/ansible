"""Generate HTML code coverage reports."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ..io import (
    make_dirs,
)

from ..util import (
    display,
)

from ..util_common import (
    ResultType,
)

from .combine import (
    command_coverage_combine,
)

from . import (
    run_coverage,
    CoverageConfig,
)


def command_coverage_html(args):
    """
    :type args: CoverageConfig
    """
    output_files = command_coverage_combine(args)

    for output_file in output_files:
        if output_file.endswith('-powershell'):
            # coverage.py does not support non-Python files so we just skip the local html report.
            display.info("Skipping output file %s in html generation" % output_file, verbosity=3)
            continue

        dir_name = os.path.join(ResultType.REPORTS.path, os.path.basename(output_file))
        make_dirs(dir_name)
        run_coverage(args, output_file, 'html', ['-i', '-d', dir_name])

        display.info('HTML report generated: file:///%s' % os.path.join(dir_name, 'index.html'))
