#!/usr/bin/env python

import os
import sys
import subprocess

path = sys.argv[-1]
dirs = os.listdir(path)
for dir in dirs:
  real_path = os.path.join(path, dir)
  if os.path.isdir(real_path):
    ret = subprocess.call(
      ["python",
       "get_benchmark.py",
       "convert",
       os.path.join(real_path, "dom.html")])
    if ret != 0:
      print >> sys.stderr, "error with", dir
      subprocess.call(["rm", "-rf", real_path])
