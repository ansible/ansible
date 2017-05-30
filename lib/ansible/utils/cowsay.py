#
# From https://github.com/jcn/cowsay-py
#
# A python implementation of cowsay <http://www.nog.net/~tony/warez/cowsay.shtml>
# Copyright 2011 Jesse Chan-Norris <jcn@pith.org>
# Licensed under the GNU LGPL version 3.0

import textwrap


def cowsay(msg, length=40):
    return build_bubble(msg, length) + build_cow()


def build_cow():
    return """
         \   ^__^
          \  (oo)\_______
             (__)\       )\/\\
                 ||----w |
                 ||     ||
    """


def build_bubble(msg, length=40):
    bubble = []

    lines = normalize_text(msg, length)

    bordersize = len(lines[0])

    bubble.append("  " + "_" * bordersize)

    for index, line in enumerate(lines):
        border = get_border(lines, index)

        bubble.append("%s %s %s" % (border[0], line, border[1]))

    bubble.append("  " + "-" * bordersize)

    return "\n".join(bubble)


def normalize_text(msg, length):
    lines = textwrap.wrap(msg, length)
    maxlen = len(max(lines, key=len))
    return [line.ljust(maxlen) for line in lines]


def get_border(lines, index):
    if len(lines) < 2:
        return ["<", ">"]

    elif index == 0:
        return ["/", "\\"]

    elif index == len(lines) - 1:
        return ["\\", "/"]

    else:
        return ["|", "|"]


if __name__ == "__main__":
    import sys
    print(cowsay(' '.join(sys.argv)))
