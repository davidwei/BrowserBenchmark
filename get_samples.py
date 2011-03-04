'''Run this script against a tarball, which gives you the first rep message/html
belonging to the same req.'''

import tarfile
import sys
import os

path = sys.argv[-1]
tarball = tarfile.open(path, mode='r:gz')
names = sorted(tarball.getnames())
req = ''
samples = []
for name in names:
  if os.path.splitext(name)[1] == '.html' and name[:name.find("_rep-")] != req:
    req = name[:name.find("_rep-")]
    samples.append(name)

for sample in samples:
  tarball.extract(sample)
tarball.close()
