#!/usr/bin/env python
__doc__ = '''
FBParser/css.py

Functionalities related to style sheets.
'''
__author__ = 'Yao Yue(yyue), yueyao@facebook.com'

__all__ = [
            'selector_index',
            'css_in_html', 'css_in_json',
          ]

#
# Imports
#
from FBParser import get_content, save_content, save_resource
from FBParser import del_blockcomment, dejsonify, url_to_file
from FBParser.regexp import re_json_css, re_html_css
from FBParser.regexp import re_cssrule, re_css_id, re_css_class

#
# APIs
#


# @param s(str)  css string
# @return (dict)  two sets of indices, for 'id' & 'class' respectively
def selector_index(s):
  '''
  This function scans css to find distinctive selectors.
  '''
  s = del_blockcomment(s)
  # build indices of selectors:
  # one for ids (#NAME), one for classes (.CLASS)
  set_id = set()
  set_class = set()
  selectors = re_cssrule.findall(s)
  for selector in selectors:
    set_id.update(re_css_id.findall(selector))
    set_class.update(re_css_class.findall(selector))
  return {'id': set_id, 'class': set_class}


# @param s(str)  a string that may contain url of css files
# @param localize(Boolean)  Wether these css files should be retrieved and saved
# @param dir=''(str)  Directory where the files should be saved
# @param prefix=''(str) a prefix to the replaced filename (e.g. relative path)
# @return (dict)  source with js urls replaced by local files (if localize),
#                 and a set of css files that are included
def css_in_html(s, localize=True, dir='', prefix=''):
  '''
  Retrieve css package information from the DOM/src and download them.
  '''
  m_csses = re_html_css.finditer(s)
  csses = set()
  for m_css in m_csses:
    if m_css.group(0).find('type="text/css"') < 0:  # avoid false positives
      continue
    url = m_css.group('url')
    if localize:
      file = url_to_file(url)
      save_resource(url, dir, file)
      s = s.replace(url, prefix + file, 1)
      csses.add(prefix + file)
    else:
      csses.add(url)
  return {'source': s, 'csses': csses}


# @param s(str)  a string that may contain url of css files
# @param localize(Boolean)  Wether these css files should be retrieved and saved
# @param dir=''(str)  Directory where the files should be saved
# @param prefix=''(str) a prefix to the replaced filename (e.g. relative path)
# @return (dict)  source with js urls replaced by local files (if localize),
#                 and a set of css files that are included
def css_in_json(s, localize=True, dir='', prefix=''):
  '''
  Retrieve css package information from the DOM/src and download them.
  NOTE: if prefix is a dir, remember to replace '/' with '\/'!
  '''
  m_csses = re_json_css.finditer(s)
  csses = set()
  for m_css in m_csses:
    url = m_css.group('url')
    download_url = dejsonify(url)
    if localize:
      file = url_to_file(url)
      s = s.replace(url, prefix + file, 1)
      save_resource(download_url, dir, file)
      csses.add(prefix + file)
    else:
      csses.add(url)
  return {'source': s, 'csses': csses}
