#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) 2018, Matt Martz <matt@sivel.net>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import argparse
import csv

from collections import namedtuple

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
except ImportError:
    raise SystemExit('matplotlib is required for this script to work')


Data = namedtuple('Data', ['axis_name', 'dates', 'names', 'values'])


def task_start_ticks(dates, names):
    item = None
    ret = []
    for i, name in enumerate(names):
        if name == item:
            continue
        item = name
        ret.append((dates[i], name))
    return ret


def create_axis_data(filename, relative=False):
    x_base = None if relative else 0

    axis_name, dummy = os.path.splitext(os.path.basename(filename))

    dates = []
    names = []
    values = []
    with open(filename) as f:
        reader = csv.reader(f)
        for row in reader:
            if x_base is None:
                x_base = float(row[0])
            dates.append(mdates.epoch2num(float(row[0]) - x_base))
            names.append(row[1])
            values.append(float(row[3]))

    return Data(axis_name, dates, names, values)


def create_graph(data1, data2, width=11.0, height=8.0, filename='out.png', title=None):
    fig, ax1 = plt.subplots(figsize=(width, height), dpi=300)

    task_ticks = task_start_ticks(data1.dates, data1.names)

    ax1.grid(linestyle='dashed', color='lightgray')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%X'))
    ax1.plot(data1.dates, data1.values, 'b-')
    if title:
        ax1.set_title(title)
    ax1.set_xlabel('Time')
    ax1.set_ylabel(data1.axis_name, color='b')
    for item in ax1.get_xticklabels():
        item.set_rotation(60)

    ax2 = ax1.twiny()
    ax2.set_xticks([x[0] for x in task_ticks])
    ax2.set_xticklabels([x[1] for x in task_ticks])
    ax2.grid(axis='x', linestyle='dashed', color='lightgray')
    ax2.xaxis.set_ticks_position('bottom')
    ax2.xaxis.set_label_position('bottom')
    ax2.spines['bottom'].set_position(('outward', 86))
    ax2.set_xlabel('Task')
    ax2.set_xlim(ax1.get_xlim())
    for item in ax2.get_xticklabels():
        item.set_rotation(60)

    ax3 = ax1.twinx()
    ax3.plot(data2.dates, data2.values, 'g-')
    ax3.set_ylabel(data2.axis_name, color='g')
    fig.tight_layout()
    fig.savefig(filename, format='png')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs=2, help='2 CSV files produced by cgroup_perf_recap to graph together')
    parser.add_argument('--relative', default=False, action='store_true',
                        help='Use relative dates instead of absolute')
    parser.add_argument('--output', default='out.png', help='output path of PNG file: Default %s(default)s')
    parser.add_argument('--width', type=float, default=11.0,
                        help='Width of output image in inches. Default %(default)s')
    parser.add_argument('--height', type=float, default=8.0,
                        help='Height of output image in inches. Default %(default)s')
    parser.add_argument('--title', help='Title for graph')
    return parser.parse_args()


def main():
    args = parse_args()
    data1 = create_axis_data(args.files[0], relative=args.relative)
    data2 = create_axis_data(args.files[1], relative=args.relative)
    create_graph(data1, data2, width=args.width, height=args.height, filename=args.output, title=args.title)
    print('Graph written to %s' % os.path.abspath(args.output))


if __name__ == '__main__':
    main()
