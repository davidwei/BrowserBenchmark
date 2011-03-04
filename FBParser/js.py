#!/usr/bin/env python
__doc__ = '''
FBParser/js.py

Functionalities related to JavaScript.
'''
__author__ = 'Yao Yue(yyue), yueyao@facebook.com'

__all__ = [
            'js_in_html', 'js_in_json', 'remove_cavalry',
          ]

#
# Imports
#
from FBParser.regexp import re_json_js, re_html_js
from FBParser import dejsonify, url_to_file, save_resource

#
# APIs
#


# @param s(str)  html source that may contain urls of javascript
# @param localize(Boolean)  Wether these js files should be retrieved and saved
# @param dir=''(str)  Directory where the files should be saved
# @param prefix=''(str) a prefix to the replaced filename (e.g. relative path)
# @return (dict)  source with js urls replaced by local files (if localize),
#                 and a set of javascript files that are included
def js_in_html(s, localize=True, dir='', prefix=''):
  '''
  Retrieve js information from the html/DOM and download them by default.
  At the mean time replace all js url references by refs to local file.
  '''
  m_javascripts = re_html_js.finditer(s)
  javascripts = set()
  for m_javascript in m_javascripts:
    url = m_javascript.group('url')
    if url:
      if localize:
        file = url_to_file(url)
        s = s.replace(url, prefix + file, 1)
        save_resource(url, dir, file)
        javascripts.add(prefix + file)
      else:
        javascripts.add(url)
  return {'source': s, 'javascripts': javascripts}


# @param s(str)  html source that may contain urls of javascript
# @param localize(Boolean)  Wether these js files should be retrieved and saved
# @param dir=''(str)  Directory where the files should be saved
# @param prefix=''(str) a prefix to the replaced filename (e.g. relative path)
# @return (dict)  source with js urls replaced by local files (if localize),
#                 and a set of javascript files that are included
def js_in_json(s, localize=True, dir='', prefix=''):
  '''
  Retrieve js information from json strings and download them by default.
  At the mean time replace all js url references by refs to local file.
  NOTE: if prefix is a dir, remember to replace '/' with '\/'!
  '''
  m_jssources = re_json_js.finditer(s)
  javascripts = set()
  for m_jssource in m_jssources:
    url = m_jssource.group('url')
    download_url = dejsonify(url)
    if localize:
      file = url_to_file(url)
      s = s.replace(url, prefix + file, 1)
      save_resource(download_url, dir, file)
      javascripts.add(prefix + file)
    else:
      javascripts.add(url)
  return {'source': s, 'javascripts': javascripts}


# @param dom(str)  html source that may contain logging-related scripts
# @return (str)  source with Cavalry removed
def remove_cavalry(dom):
  '''
  Remove Cavalry related script, as they are not part of a standard page
  but prevails in perflab traces.
  '''
  first_js = re_html_js.search(dom).group(0)
  if first_js.find("CavalryLogger") >= 0:
    dom = dom.replace(first_js, '')
  return dom
