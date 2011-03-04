#!/usr/bin/env python
__doc__ = '''
    Parse Facebook DOM file.
'''
__author__ = 'Yao Yue(yyue), yueyao@facebook.com'

#
# Imports
#
import FBParser
import FBParser.img
import FBParser.garble_image
import FBParser.dom
import FBParser.css
import FBParser.js
# external imports
import re
import sys
import os
import random
try:
  from argparse import ArgumentParser
  from argparse import RawDescriptionHelpFormatter
except ImportError:
  print '''This script uses the argparse module.
           It is included by default for Python 2.7+.
           You can download argparse.py online.
        '''
  sys.exit(1)

PIPE_EXCLUDES = ['onload', 'onafterload']
SUBDIRS = ['css', 'img', 'js', 'misc']


# @return (dict)  Arguments in a dictionary
def get_args():
  '''
  Parse command line options and return them in a dict.
  '''
  parser = ArgumentParser(
    formatter_class=RawDescriptionHelpFormatter,
    description=__doc__)
  subparsers = parser.add_subparsers(dest='action')
  parser.add_argument('file')

  parser_pretty = subparsers.add_parser(
    'pretty',
    help='''
      Indent labels in DOM/html to make the source nicely aligned & readable.
      ''')

  parser_decouple = subparsers.add_parser(
    'convert',
    help='''
      Localize all external resources to focus solely on browser performance.
      Result pages are coded based on how [js, css] components are stripped off
      from the original html.

      There are different levels on which we keep js and css resources.
      Dimension 1, javascript:
        js0: no javascript at all
        js1: only javascript necessary to make Big Pipe work is kept
        js2: all tag-enclosed javascript is kept, w/ onclick tossed away
        js3: all remains
      Dimension 2, css:
        css0: no css rules applied
        css1: all css rules are applied
      *Special:
        fp: I call it "fake pipe", which takes a js0-css1 dom tree, and insert
        pagelets into DOM like Big Pipe does, but with minimal script overhead.

      The 2-D combination of these possibilities, together with the option of
      anonymizing or not, gives us 9 + 5 = 14 eventual outputs!

      Given a DOM in html, <filename>, the following html files are generated:
      For clear-text html files, we have:
      ''')
  return parser.parse_args()


# @param dom(str)  DOM string to search
# @param path(str)  path to the source file
# @param prefix(str)  prefix of sub-dir to store the external resources
# @return (str)  DOM with href anonymized
def localize_misc(dom, path, prefix='misc'):
  '''
  A few standalone resources to localize, including an xml, an ico and an iframe
  '''
  misc_path = os.path.join(path, prefix)
  if not os.path.exists(misc_path):
    os.mkdir(misc_path)
  re_search = re.compile(
'<link rel="search" type="application/opensearchdescription\+xml" \
href="(?P<url>http://.*?\.xml)" title="Facebook">')
  m_search = re_search.search(dom)
  url = m_search.group('url')
  file = FBParser.url_to_file(url)
  FBParser.save_resource(url, misc_path, file)
  dom = dom.replace(url, os.path.join(prefix, file))
  re_ico = re.compile(
'<link rel="shortcut icon" href="(?P<url>http://.*?\.ico)">')
  m_ico = re_ico.search(dom)
  url = m_ico.group('url')
  file = FBParser.url_to_file(url)
  FBParser.save_resource(url, misc_path, file)
  dom = dom.replace(url, os.path.join(prefix, file))
  re_uicif = re.compile('<iframe src="(?P<url>http://.*?\.html)"')
  m_uicif = re_uicif.search(dom)
  if m_uicif:
    url = m_uicif.group('url')
    file = FBParser.url_to_file(url)
    FBParser.save_resource(url, misc_path, file)
    dom = dom.replace(url, os.path.join(prefix, file))
  # redirect the rest of the hrefs to about:blank (most of them are hyperlinks)
  # (call this after localize_css!)
  dom = re.sub('href="http://.+?"', 'href="about:blank"', dom)
  return dom


# @param dom(str)  DOM string to search
# @param path(str)  path to the source file
# @param prefix(str)  prefix of sub-dir to store the external resources
# @return (str)  DOM with external resources localized
def localize_css(dom, path, prefix='css'):
  '''
  Find out all css files loaded for this page, replace urls with local files.
  '''
  # create a subfolder if necessary
  css_path = os.path.join(path, prefix)
  if not os.path.exists(css_path):
    os.mkdir(css_path)
  css_set = set()
  ret = FBParser.css.css_in_html(dom, dir=css_path, prefix=prefix + '/')
  dom = ret['source']
  css_set.update(ret['csses'])
  ret = FBParser.css.css_in_json(dom, dir=css_path, prefix=prefix + '\/')
  dom = ret['source']
  css_set.update(ret['csses'])
  images = set()
  # localize images in the css files
  for css_file in css_set:
    css = FBParser.get_content(os.path.join(path, css_file), encoding='ascii')
    ret = FBParser.img.img_in_css(css, dir=css_path, prefix=prefix + '/')
    FBParser.save_content(
      ret['source'],
      os.path.join(path, css_file),
      encoding='ascii')
    images.update(ret['images'])
  FBParser.save_content(
    '\n'.join(list(images)),
    os.path.join(path, filename.rstrip('html') + 'cssimage_list'),
    encoding='ascii')
  FBParser.save_content(
    '\n'.join(list(css_set)),
    os.path.join(path, filename.rstrip('html') + 'css_list'),
    encoding='ascii')
  return dom


# @param dom(str)  DOM string to search
# @param path(str)  path to the source file
# @param prefix(str)  prefix of sub-dir to store the external resources
# @return (str)  DOM with external resources localized
def localize_img(dom, path, prefix='img'):
  '''
  Find out all images loaded for this page, replace urls with local files.
  '''
  # create a subfolder if necessary
  img_path = os.path.join(path, prefix)
  if not os.path.exists(img_path):
    os.mkdir(img_path)
  ret = FBParser.img.img_in_html(
    dom,
    dir=img_path,
    prefix=prefix + '/')
  dom = ret['source']
  FBParser.save_content(
    '\n'.join(list(ret['images'])),
    os.path.join(path, filename.rstrip('html') + 'img_list'),
    encoding='ascii')
  return dom


# @param dom(str)  DOM string to search
# @param path(str)  path to the source file
# @param prefix(str)  prefix of sub-dir to store the external resources
# @return (str)  DOM with external resources localized
def localize_js(dom, path, prefix='js'):
  '''
  Find out all js files loaded for this page, replace urls with local files.
  '''
  # create a subfolder if necessary
  js_path = os.path.join(path, prefix)
  if not os.path.exists(js_path):
    os.mkdir(js_path)
  js_set = set()
  ret = FBParser.js.js_in_html(dom, dir=js_path, prefix=prefix + '/')
  dom = ret['source']
  js_set.update(ret['javascripts'])
  ret = FBParser.js.js_in_json(dom, dir=js_path, prefix=prefix + '\/')
  dom = ret['source']
  js_set.update(ret['javascripts'])
  FBParser.save_content(
    '\n'.join(list(js_set)),
    os.path.join(path, filename.rstrip('html') + 'js_list'),
    mode='w',
    encoding='ascii')
  return dom


# @param path(str)  path of the DOM file
# @param filename(str)  name of the DOM file
# @return (dict)  a set of selectors for each type (id, calss)
def get_css_selectors(path, filename):
  '''
  Get all the selectors from a list of css files.
  Call this AFTER localizing all css resources and css_list is in place.
  '''
  #   first collect css selectors from css files
  selectors = {}
  css_files = FBParser.get_content(
    os.path.join(path, filename.rstrip('html') + 'css_list'),
    encoding='ascii')
  css_files = css_files.split('\n')
  for css_file in css_files:
    css_file = css_file.replace('\\', '')
    css = FBParser.get_content(os.path.join(path, css_file), encoding='ascii')
    ret = FBParser.css.selector_index(css)
    for key in ret.keys():
      if key in selectors:
        selectors[key].update(ret[key])
      else:
        selectors[key] = ret[key]
  return selectors


# @param dom(str)  DOM in a string
# @param path(str)  path of DOM/html files
# @return  (str)  new DOM with anonymized image sources
def anonym_images(dom, path, filename):
  '''
  Anonymize images and regenerate file names.
  '''
  img_files = FBParser.get_content(
    os.path.join(path, filename.rstrip('html') + 'img_list'),
    encoding='ascii')
  img_files = img_files.split('\n')
  images = {}
  if os.path.isfile(
    os.path.join(path, filename.rstrip('html') + 'img_mapping')):
  # already have garbled images, only replace filenames in dom
    img_mapping = FBParser.get_content(
      os.path.join(path, filename.rstrip('html') + 'img_mapping'),
      encoding='ascii')
    img_mapping = img_mapping.split('\n')
    for mapping in img_mapping:
      img_file, new_file = mapping.split(': ')
      dom = dom.replace(img_file, new_file)
  else:  # garbled image not generated yet
    for img_file in img_files:
      ext = os.path.splitext(img_file)[1]
      prefix = os.path.split(img_file)[0]
      new_file = prefix + '/anonym_' + str(random.getrandbits(40)) + ext
      images[img_file] = new_file
      dom = dom.replace(img_file, new_file)
      FBParser.save_resource(os.path.join(path, img_file), path, new_file)
    st_mapping = []
    for key, val in images.items():
      st_mapping.append(key + ': ' + val)
    FBParser.save_content(
      '\n'.join(st_mapping),
      os.path.join(path, filename.rstrip('html') + 'img_mapping'),
      encoding='ascii')
    for image in images:
      images[image] = os.path.join(path, images[image])
    FBParser.garble_image.garble(images.values())
  return dom


def retry_resource(path):
  for subdir in SUBDIRS:
    dir = os.path.join(path, subdir)
    log = os.path.join(dir, 'missing_files.log')
    err_log = open(os.path.join(path, 'missing_files.log'), 'w')
    if os.path.isfile(log):
      f = open(log, 'r')
      files = f.readlines(f)
      f.close()
      os.remove(log)
      for entry in entries:
        url, file = entry.rstrip('\n').split()
        try:
          urlretrieve(url, os.path.join(dir, file))
        except ValueError, err:
          err_log.write(url + ' ' + os.path.join(subdir, file) + '\n')
  err_log.close()


# main
if __name__ == '__main__':
  args = get_args()
  path, filename = os.path.split(args.file)
  dom = FBParser.get_content(args.file)

  if args.action == 'pretty':
    pretty_dom = FBParser.dom.prettify(dom)
    FBParser.save_content(
      pretty_dom,
      os.path.join(path, 'pretty-' + filename))

  if args.action == "convert":
    dom = FBParser.js.remove_cavalry(dom)
    dom = FBParser.dom.decss_injected(dom)
    dom = localize_css(dom, path)
    dom = localize_js(dom, path)
    dom = localize_img(dom, path)
    local_dom = localize_misc(dom, path)
    retry_resource(path)
    dom_13 = local_dom
    print "css 1, javascript 3"
    ret = FBParser.dom.unload_pagelets(dom_13)
    html_13 = ret['html']
    pagelets = ret['pagelets']
    FBParser.save_content(
      html_13,
      os.path.join(path, 'css1js3-' + filename))
    print "css 1, javascript 2"
    dom_12 = FBParser.dom.descript_onclick(dom_13)
    html_12 = FBParser.dom.unload_pagelets(dom_12)['html']
    FBParser.save_content(
      html_12,
      os.path.join(path, 'css1js2-' + filename))
    print "css 1, javascript 1"
    dom_11 = FBParser.dom.descript_pipeonly(dom_12)
    html_11 = FBParser.dom.unload_pagelets(dom_11, PIPE_EXCLUDES)['html']
    FBParser.save_content(
      html_11,
      os.path.join(path, 'css1js1-' + filename))
    print "css 1, javascript 0"
    html_10 = FBParser.dom.descript_html(dom_12)
    FBParser.save_content(
      html_10,
      os.path.join(path, 'css1js0-' + filename))
    # css-free source files
    print "css 0, javascript 3"
    FBParser.save_content(
      FBParser.dom.unload_css(html_13),
      os.path.join(path, 'css0js3-' + filename))
    print "css 0, javascript 2"
    FBParser.save_content(
      FBParser.dom.unload_css(html_12),
      os.path.join(path, 'css0js2-' + filename))
    print "css 0, javascript 1"
    FBParser.save_content(
      FBParser.dom.unload_css(html_11),
      os.path.join(path, 'css0js1-' + filename))
    print "css 0, javascript 0"
    FBParser.save_content(
      FBParser.dom.unload_css(html_10),
      os.path.join(path, 'css0js0-' + filename))

    # Anonymized pages, we don't go beyond js level 2
    selectors = {'id': set(pagelets), 'class': set()}
    ret = get_css_selectors(path, filename)
    for key in selectors.keys():
      if key in ret:
        selectors[key].update(ret[key])
    anondom = anonym_images(dom_11, path, filename)
    print "anonymized, css 1, javascript 1"
    anondom_11 = FBParser.dom.anonym_dom(anondom, selectors)
    anonhtml_11 = \
      FBParser.dom.unload_pagelets(anondom_11, PIPE_EXCLUDES)['html']
    FBParser.save_content(
      anonhtml_11,
      os.path.join(path, 'anon_css1js1-' + filename))
    print "anonymized, css 1, javascript 0"
    anonhtml_10 = FBParser.dom.descript_html(anondom_11)
    FBParser.save_content(
      anonhtml_10,
      os.path.join(path, 'anon_css1js0-' + filename))
    # css-free anonymous source files
    print "anonymized, css 0, javascript 1"
    FBParser.save_content(
      FBParser.dom.unload_css(anonhtml_11),
      os.path.join(path, 'anon_css0js1-' + filename))
    print "anonymized, css 0, javascript 0"
    FBParser.save_content(
      FBParser.dom.unload_css(anonhtml_10),
      os.path.join(path, 'anon_css0js0-' + filename))
