"""
Disallow direct linking to S3 buckets.
S3 buckets should be accessed through a CloudFront distribution.
"""

from __future__ import annotations

import re
import sys


def main():
    """Main entry point."""
    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        with open(path, 'rb') as path_fd:
            for line, b_text in enumerate(path_fd.readlines()):
                try:
                    text = b_text.decode()
                except UnicodeDecodeError:
                    continue

                if match := re.search(r'(http.*?s3\..*?amazonaws\.com)', text):
                    print(f'{path}:{line + 1}:{match.start(1) + 1}: use a CloudFront distribution instead of an S3 bucket: {match.group(1)}')


if __name__ == '__main__':
    main()
