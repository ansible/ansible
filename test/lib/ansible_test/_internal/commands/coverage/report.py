"""Generate console code coverage reports."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ..io import (
    read_json_file,
)

from ..util import (
    display,
)

from ..data import (
    data_context,
)

from .combine import (
    command_coverage_combine,
)

from . import (
    run_coverage,
    CoverageConfig,
)


def command_coverage_report(args):
    """
    :type args: CoverageReportConfig
    """
    output_files = command_coverage_combine(args)

    for output_file in output_files:
        if args.group_by or args.stub:
            display.info('>>> Coverage Group: %s' % ' '.join(os.path.basename(output_file).split('=')[1:]))

        if output_file.endswith('-powershell'):
            display.info(_generate_powershell_output_report(args, output_file))
        else:
            options = []

            if args.show_missing:
                options.append('--show-missing')

            if args.include:
                options.extend(['--include', args.include])

            if args.omit:
                options.extend(['--omit', args.omit])

            run_coverage(args, output_file, 'report', options)


def _generate_powershell_output_report(args, coverage_file):
    """
    :type args: CoverageReportConfig
    :type coverage_file: str
    :rtype: str
    """
    coverage_info = read_json_file(coverage_file)

    root_path = data_context().content.root + '/'

    name_padding = 7
    cover_padding = 8

    file_report = []
    total_stmts = 0
    total_miss = 0

    for filename in sorted(coverage_info.keys()):
        hit_info = coverage_info[filename]

        if filename.startswith(root_path):
            filename = filename[len(root_path):]

        if args.omit and filename in args.omit:
            continue
        if args.include and filename not in args.include:
            continue

        stmts = len(hit_info)
        miss = len([c for c in hit_info.values() if c == 0])

        name_padding = max(name_padding, len(filename) + 3)

        total_stmts += stmts
        total_miss += miss

        cover = "{0}%".format(int((stmts - miss) / stmts * 100))

        missing = []
        current_missing = None
        sorted_lines = sorted([int(x) for x in hit_info.keys()])
        for idx, line in enumerate(sorted_lines):
            hit = hit_info[str(line)]
            if hit == 0 and current_missing is None:
                current_missing = line
            elif hit != 0 and current_missing is not None:
                end_line = sorted_lines[idx - 1]
                if current_missing == end_line:
                    missing.append(str(current_missing))
                else:
                    missing.append('%s-%s' % (current_missing, end_line))
                current_missing = None

        if current_missing is not None:
            end_line = sorted_lines[-1]
            if current_missing == end_line:
                missing.append(str(current_missing))
            else:
                missing.append('%s-%s' % (current_missing, end_line))

        file_report.append({'name': filename, 'stmts': stmts, 'miss': miss, 'cover': cover, 'missing': missing})

    if total_stmts == 0:
        return ''

    total_percent = '{0}%'.format(int((total_stmts - total_miss) / total_stmts * 100))
    stmts_padding = max(8, len(str(total_stmts)))
    miss_padding = max(7, len(str(total_miss)))

    line_length = name_padding + stmts_padding + miss_padding + cover_padding

    header = 'Name'.ljust(name_padding) + 'Stmts'.rjust(stmts_padding) + 'Miss'.rjust(miss_padding) + \
             'Cover'.rjust(cover_padding)

    if args.show_missing:
        header += 'Lines Missing'.rjust(16)
        line_length += 16

    line_break = '-' * line_length
    lines = ['%s%s%s%s%s' % (f['name'].ljust(name_padding), str(f['stmts']).rjust(stmts_padding),
                             str(f['miss']).rjust(miss_padding), f['cover'].rjust(cover_padding),
                             '   ' + ', '.join(f['missing']) if args.show_missing else '')
             for f in file_report]
    totals = 'TOTAL'.ljust(name_padding) + str(total_stmts).rjust(stmts_padding) + \
             str(total_miss).rjust(miss_padding) + total_percent.rjust(cover_padding)

    report = '{0}\n{1}\n{2}\n{1}\n{3}'.format(header, line_break, "\n".join(lines), totals)
    return report


class CoverageReportConfig(CoverageConfig):
    """Configuration for the coverage report command."""
    def __init__(self, args):
        """
        :type args: any
        """
        super(CoverageReportConfig, self).__init__(args)

        self.show_missing = args.show_missing  # type: bool
        self.include = args.include  # type: str
        self.omit = args.omit  # type: str
