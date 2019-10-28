#!/bin/bash
#
#

PYTHONPATH=.

# This is required for Threading
LD_PRELOAD=libgcc_s.so.1
export LD_PRELOAD

export PYTHONPATH

nice -20 python3 ./launcher_test.py $1 $2

