#!/usr/bin/env python
__doc__ = '''
FBParser/img.py

Image related functionalities when parsing a Facebook DOM/html page.
'''
__author__ = 'Yao Yue(yyue), yueyao@facebook.com'


__all__ = [
            'img_in_html', 'img_in_css',
          ]

#
# Imports
#
from FBParser.regexp import re_css_img, re_html_img
from FBParser import garble_image
from FBParser import save_content, url_to_file, save_resource
# external imports
from urllib import unquote

#
# APIs
#


# @param s(str)  a string that may contain url of css files
# @param localize(Boolean)  Wether these images should be fetched and saved
# @param site='http://www.facebook.com'(str)  Domain prefix of the image urls
# @param dir=''(str)  Directory where the file should be saved
# @param prefix=''(str) a prefix to the replaced filename (e.g. relative path)
# @return (dict) string with url replaced by local file,
#                and a set of images that are included
def img_in_css(s,
               localize=True,
               site='http://static.ak.fbcdn.net',
               dir='',
               prefix=''):
  '''
  Retrieve image information from the CSS and download them.
  '''
  images = set()
  m_images = re_css_img.finditer(s)
  for m_image in m_images:
    url = m_image.group('url')
    file = url_to_file(url)
    if localize and url[0:9] == '/rsrc.php':
      images.add(prefix + file)
      s = s.replace(url, prefix + file, 1)
      save_resource(site + url, dir, file)
    else:  # just form the set, don't need to be or already localized
      images.add(url)
  return {'source': s, 'images': images}


# @param s(str)  a string that may contain url of image files
# @param localize(Boolean)  Wether these images should be fetched and saved
# @param dir=''(str)  Directory where the file should be saved
# @param prefix=''(str) a prefix to the replaced filename (e.g. relative path)
# @return (dict)  html with image url replaced by new names,
#                 and a dictionary mapping original filenames to new names
def img_in_html(s,
                localize=True,
                site='http://static.ak.fbcdn.net',
                dir='',
                prefix=''):
  '''
  Retrieve image information from the DOM/src and download them.
  '''
  m_images = re_html_img.finditer(s)
  images = set()
  for m_image in m_images:
    url = m_image.group('url')
    if url[0] == '/':
      url = site + url
    if localize:
      file = url_to_file(url)
      download_url = unquote(url).replace('&amp;', '&')
      save_resource(download_url, dir, file)
      images.add(prefix + file)
      s = s.replace(url, prefix + file, 1)
    else:  # only getting a list of urls
      images.add(url)
  return {'source': s, 'images': images}
