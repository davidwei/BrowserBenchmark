#!/usr/bin/env python
__doc__ = '''
Since garble_image.py uses a couple of non-standard libraries, this setup allows
one to build binary on Windows and use the binary for conversion alone.
'''

__author__ = 'Yao Yue(yyue), yueyao@facebook.com'

from distutils.core import setup
import py2exe

setup(console=['garble_image.py'])
