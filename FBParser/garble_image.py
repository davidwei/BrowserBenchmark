#!/usr/bin/env python
__doc__ = '''
FBParser/garble_image.py

Convert a JPEG image to blurred noise (most photos, thumnails).
Replace a PNG image by white rectangle (some ads pictures).
GIF images are left untouched, for now.
All images retain their original height and width.
'''
__author__ = 'Yao Yue(yyue), yueyao@facebook.com'

__all__ = [
            'garble',
          ]

#
# Imports
#
import sys
import os
import struct
import Image
import random
from Crypto.Cipher import Blowfish
from Crypto.Util.randpool import RandomPool
try:
  from argparse import ArgumentParser, RawDescriptionHelpFormatter
except ImportError:
  print '''This script uses the argparse module.
           It is included by default for Python 2.7+.
           You can download argparse.py online.
        '''
  sys.exit(1)

#
# Internal functions
#

# Constants used by encryption and padding
KEY_LEN = 8  # key length
BLK_LEN = 8  # block size


# @return (dict)  Arguments in a dictionary
def _get_args():
  '''
  Parse command line options and return them in a dict.
  '''
  parser = ArgumentParser(
    formatter_class=RawDescriptionHelpFormatter,
    description=__doc__)
  parser.add_argument(
    '-t', '--type',
    help='''
      Supported filetype/suffix includes JPEG(jpg), PNG(png) & GIF(gif).
      Specify multiple suffices by separating them with whitespace.
      Omitted if you specify the file name, default to all three types.
      ''',
      nargs='*',
      choices=['.gif', '.jpg', '.png', 'gif', 'jpg', 'png'],
    default=['.gif', '.jpg', '.png'])
  parser.add_argument(
    '-f', '--file',
    help='''
      File to be converted.
      ''',
    nargs='?',
    default='')
  parser.add_argument(
    '-d', '--dir',
    help='''
      All images matching the type(s) under this directory will be converted.
      Default to current folder.
      Not recursive.
      ''',
    nargs='?',
    default='.')
  return parser.parse_args()


# @param data(Image data)  a list like object containing pixel information
# @param mode(Image mode)  (color) mode of the image
# @return (list)  A string (gif) or list of encrypted pixels
def _encrypt(data, mode='RGB'):
  '''
  Encrypt the pixels (as a concatinated string).
  '''
  # unit: how many bytes does the smallest component have
  # size: how many components does each pixel have
  if mode == '1' or mode == 'I' or mode == 'F':
    print "Mode {mode} is not supported at the moment!".format(mode=mode)
    return []
  else:
    unit = 1
    format = 'B'
  cleartext = ''
  if type(data[0]) == int:
    pixel_size = 1
    for pixel in data:
      cleartext += chr(pixel)
  else:
    pixel_size = len(data[0])  # get the vector size based on the last pixel
    for pixel in data:
      for val in pixel:
        cleartext += chr(val)
  num_pixels = len(data)
  # encrypt the data string, pay attention to the length
  key = RandomPool().get_bytes(KEY_LEN)
  blowfish = Blowfish.new(key, mode=2)
  padding = '\x00' * (BLK_LEN - (len(cleartext) - 1) % BLK_LEN - 1)
  cleartext += padding
  ciphered = blowfish.encrypt(cleartext)
  ciphered = ciphered[len(padding):]  # don't really care if data is messed...
  ret = []
  chunk_size = unit * pixel_size
  for i in range(num_pixels):
    pixel = struct.unpack(
      format * pixel_size,
      ciphered[chunk_size * i: chunk_size * (1 + i)])
    ret.append(pixel)
  return ret

#
# APIs
#


# @param images(list)  A list of image file names (with full path).
# @return (list)  A list of images that are successfully garbled.
def garble(images):
  '''ig.
  convert a list of images.
  '''
  success = []
  for image in images:
    f = open(image, 'rb')
    img_mapping = {}
    try:
      img = Image.open(f)
      img.load()
    except StandardError:
      f.close()
    else:
      f.close()
      if img.format == 'JPEG':
        data = img.getdata()
        if img.mode != 'RGB' and img.mode != 'RGBA':
          img = img.convert('RGBA')
        img.putdata(_encrypt(data), 1, 0)
        img.save(image, 'JPEG')
      elif img.format == 'PNG':
        size = img.size
        img = Image.new("RGB", size, "orange")
        img.save(image, 'PNG')
      elif img.format == 'GIF':
        pixels = []
        for pixel in range(img.size[0] * img.size[1]):
          pixels.append(random.uniform(0, 255))
        img.putdata(pixels, 1, 0)
        img.save(image, 'GIF')
      success.append(image)
  return success

#
# Default
#


def main():
  args = _get_args()
  images = []

  for type in args.type:
    if type[0] != '.':
      type = '.' + type
  if args.file:
    args.file = os.path.realpath(os.path.expanduser(args.path))
    if not os.path.isfile(args.file):
      print >> sys.stderr, "{file} is not a file".format(file=args.file)
      sys.exit(1)
    images.append(args.file)
  else:
    args.dir = os.path.realpath(os.path.expanduser(args.dir))
    print args.dir
    if not os.path.isdir(args.dir):
      print >> sys.stderr, "{dir} is not a directory".format(file=args.dir)
      sys.exit(1)
    # go through all files (directly) under args.dir
    print os.listdir(args.dir)
    for entry in os.listdir(args.dir):
      if os.path.isfile(os.path.join(args.dir, entry)):
        if os.path.splitext(entry)[1] in args.type:
          images.append(os.path.join(args.dir, entry))
  print images
  garble(images)

if __name__ == '__main__':
  main()
