'''
FBParser/__init__.py

Basic functionalities used in parsing Facebook pages
to get DOM & CSS characteristics.
'''
__author__ = 'Yao Yue (yueyao@facebook.com)'

__all__ = [
            'css', 'dom', 'js', 'img', 'garble_image',
            'Constants',
            'get_content', 'save_content',
            'url_to_file', 'save_resource',
            'del_blockcomment',
            'jsonify', 'dejsonify',
          ]

#
# Imports
#
from FBParser.regexp import re_doctype, re_blockcomment
# external imports
import sys
import codecs
import os.path
from urllib import urlretrieve

#
# APIs, common
#


# @param url(str)  a url
# @return (str)  file name, dropping the domain/path prefix
def url_to_file(url):
  '''
  Get the filename from a url.
  '''
  pos = url.rfind('/') + 1
  if url.rfind('%') >= pos:
    pos = url.rfind('%') + 1
  return url[pos:]


# @param s(str)  string to be worked on
# @return (str)  the argument string with its block comment removed
def del_blockcomment(s):
    '''
    Removing source code block comments (/* */) from the string sent.
    '''
    # skip DOCTYPE info
    m_doctype = re_doctype.match(s)
    if m_doctype:
      start = len(m_doctype.group(0))
    else:
      start = 0
    return  s[:start] + re_blockcomment.sub("", s[start:])


# @param s(str)  string to be JSON-ified
# @return (str)  JSON-ifyed string
def jsonify(s):
  '''
  Add backslash to escape characters.
  '''
  s = s.replace("\\", "\\\\")
  s = s.replace("/", "\\/")
  s = s.replace("'", "\\'")
  s = s.replace('"', '\\"')
  s = s.replace('\r', '\\r')
  s = s.replace('\n', '\\n')
  return s


# @param s(str)  string to be JSON-ified
# @return (String)  JSON-ifyed string
def dejsonify(s):
  '''
  Remove backslash from escape characters.
  '''
  s = s.replace("\\\\", "\\")
  s = s.replace("\\/", "/")
  s = s.replace("\\'", "'")
  s = s.replace('\\"', '"')
  s = s.replace('\\r', '\r')
  s = s.replace('\\n', '\n')
  return s


# @param filename(str)  name of the file whose content we want
# @param encoding='utf-8'(str)  encoding used by the file
# @return (str)  the content as a string
def get_content(filename, encoding='utf-8'):
  '''
  Fetch the content of the file and return it as a string.
  '''
  try:
    f = codecs.open(filename, 'r', encoding)
    s = ''.join(f.readlines())
    f.close()
  except IOError, err:
    print >> sys.stderr, err
    s = ''
  return s


# @param s(str)  content
# @param filename(str)  name of the file to keep the content
# @param mode='w'(str)  mode used to open the file
# @param encoding='utf-8'(str)  encoding used for the file
# @return (Boolean)  success (or not)
def save_content(s, filename, mode='w', encoding='utf-8'):
  '''
  Save the content to a file.
  '''
  try:
    f = codecs.open(filename, mode, encoding)
    f.write(s)
    f.close()
  except IOError, err:
    print >> sys.stderr, err
    return False
  return True


# @param url(str)  complete url of the external resource
# @param dir(str)  Directory where the file should be saved
# @param file(str)  Name of the file to be saved. Note: we can but don't infer
#                   from url for sublties/variances in url encoding
# @return (Boolean)  success (or not)
def save_resource(url, dir, file):
  '''
  Retrieve resource (url) and save it to file in the given directory.
  If the retrieval fails, the url and filename are appended to a log file,
  inside the target directory, so that one can retry later.
  '''
  if not os.path.isfile(os.path.join(dir, file)):
    try:
      urlretrieve(url, os.path.join(dir, file))
    except ValueError, err:
      print >> sys.stderr, "Cannot retrieve {url}: {err}".format(
        url=url, err=err)
      f = open(os.path.join(dir, 'missing_files.log'), 'a')
      f.write(url + ' ' + file + '\n')
      f.close()
      return False
  return True
