#!/usr/bin/env python2
# Copyright (C) 2016 Russell Haley
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, division, print_function

import sys
sys.path.append('/usr/local/lib64/python2.7/site-packages')
import xwiimote
import select
import time
import os
import argparse
from contextlib import contextmanager
from collections import deque

class BalanceBoardConnectionError(Exception):
    pass

@contextmanager
def get_balance_board_iface():
    mon = xwiimote.monitor(True, True)
    wiimote_path = mon.poll()
    while wiimote_path is not None:
        dev = xwiimote.iface(wiimote_path)
        if dev.get_extension() == 'balanceboard':
            mask = dev.available() | xwiimote.IFACE_BALANCE_BOARD
            dev.open(mask)
            yield dev
            dev.close()
            break
        wiimote_path = mon.poll()
    else:
        raise BalanceBoardConnectionError

def weight_gen():
    with get_balance_board_iface() as bb:
        p = select.poll()
        p.register(bb.get_fd(), select.POLLIN)
        event = xwiimote.event()
        while True:
            p.poll()
            bb.dispatch(event)
            decigrams = sum(x[0] for x in (event.get_abs(i) for i in range(4)))
            yield decigrams / 100.0

def get_weight(navg=100):
    head_samples = deque([0] * navg)
    tail_samples = deque([0] * navg)
    head_sum = 0.0
    tail_sum = 0.0
    seen = 0
    for samp in weight_gen():
        # Two moving averages. The head average is of the last navg samples,
        # and the tail average is the navg samples before that.  By comparing
        # them, we can tell if the measurement has settled.  Verbose
        # monstrosity to avoid traversing deque more than once.
        head_samples.append(samp)
        head_sum += samp
        head_sum -= head_samples[0]
        tail_sum += head_samples[0]
        tail_samples.append(head_samples.popleft())
        tail_sum -= tail_samples[0]
        tail_samples.popleft()
        head_avg = head_sum / navg
        tail_avg = tail_sum / navg
        seen += 1
        if seen > navg * 2 and abs(head_avg - tail_avg) < 0.1:
            return head_avg

def log_weight_to_file(filename):
    if not os.path.exists(filename):
        with open(filename, 'w') as logfile:
            logfile.write('time weight_kg\n')
    with open(filename, 'a') as logfile:
        logfile.write('{:.0f} {:.2f}\n'.format(time.time(), get_weight()))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Measure weight with a Wii Balance Board and log to file.')
    parser.add_argument('logfile', help='Where to log the weight.')
    args = parser.parse_args()
    print('Please step onto the balace board.')
    log_weight_to_file(args.logfile)



