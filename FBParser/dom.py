#!/usr/bin/env python
__doc__ = '''
FBParser/dom.py

Image related functionalities when parsing a Facebook DOM/html page.
'''
__author__ = 'Yao Yue(yyue), yueyao@facebook.com'

__all__ = [
    'prettify', 'anonym_dom', 'unload_pagelets',
    'descript_pipeonly', 'descript_onclick',
    'descript_html', 'descript_injected',
    'unload_css', 'decss_injected', 'decss_all',
    ]

#
# Imports
#
from FBParser.Constants import *
from FBParser.regexp import *
from FBParser import url_to_file, jsonify, del_blockcomment
# external imports
import re
import sys
import codecs
import random
from urllib import unquote
import time

# @param s(str)  string to be worked on
# @param pos(int)  position of the leading quote marking
# @param char_quote='"'(str)  whether the quote mark is a "'" or a '"'
# @return (int) position after the trailing quote mark
def skip_quote(s, pos, char_quote='"'):
  '''
  Get the end of the quote given the position of the first quote mark.
  '''
  pos += 1
  while s[pos] != char_quote:
    if s[pos] == '\\':
      pos += 2  # skip escape characters
    else:
      pos += 1
  return pos + 1


# @param s(str)  string to be worked on
# @param start(int)  starting position
# @return (int)  start of the next tag
def skip_content(s, start):
  '''
  Skip content between tags.
  '''
  current = start
  while (current < len(s) and
         (s[current] != '<' or s[current:current + 2] == '<!')):
    # jump to next tag and avoid trapped by escape chars or quotes
    if s[current] == '\\':
      current += 2
    elif s[current] == '"':
      current = skip_quote(s, current, '"')
    else:
      current += 1
  return current


# @param s(str)  string that needs to be indented
# @param depth(int)  The 'depth' of the string in the nested structure
# @param newline=True(Boolean)  Do we need to start a new line for the string?
# @param unit=INDENT_WIDTH(int)  Indentation unit defined in Constants.py
# @return (str) An indented string
def indent(s, depth, newline=True, unit=INDENT_WIDTH):
  '''
  Add indentation to a string, start a new line as well by default.
  '''
  if newline:
    return '\r\n' + ' ' * depth * unit + s
  else:
    return ' ' * depth * unit + s


# @param s(str)  dom string to be worked on
# @param rootid(str)  opening id whose subtree is to be cut
# @return (dict)  the dom node and the rest of the original dom
def cut_dom_node(s, rootid):
  '''
  Cut a dom node with given tag from the dom tree.
  '''
  if s.find(rootid) < 0:
    return {'node': '', 'dom': s}
  else:
    start = re.search("<.*?{id}>".format(id=rootid), s).end()
  depth = 0
  current = start
  maxpos = len(s)
  while depth >= 0:
    while (current < maxpos and \
           (s[current] != '<' or re_tag.match(s[current:]) == None)):
      if s[current] == '\\':
        current += 2
      elif s[current] == '"':
        current = skip_quote(s, current, '"')
      else:
        current += 1
    if current >= maxpos:  # reached EOF w/o a match, DOM probably corrupted
      return {'node': '', 'dom': s}
    tag = re_tag.match(s[current:]).group(0)
    tag_label = re_tag_label.match(tag).group('label')
    if tag_label in EMPTY_ELEMENTS:
      current += len(tag)
    elif tag[1] == '/':  # closing tags, not empty elements
      depth -= 1
      if depth >= 0:  # not paired with root
        current += len(tag)
    else:  # opening tag that needs to be paired later
      depth += 1
      current += len(tag)
  return {'node': s[start:current], 'dom': s[:start] + s[current:]}


# @param s(str)  the original string
# @param mode=MODE_MONO(int)  how to replace the original characters
# @return (str)  anonymized string
def anonym_str(s, mode=MODE_MONO):
  '''
  Anonymize a string. All whitespace chars are kept to maintain formatting.
  MODE_MONO replaces chars with '?';
  MODE_BABBLE replaces each with 'a'-'z' randomly.
  '''
  if mode == MODE_MONO:  # use one char to replace all non whitespace chars
    return re.sub("[^\s]", "?", s)
  if mode == MODE_BABBLE:
    return re.sub("[^\s]{1}", chr(random.randint(97, 122)), s)


# @param v(str)  the original value string
# @param selectors(list)  a list of css selectors
# @param mode(str)  How to replace a string with meaningless chars
# @return (str)  anonymized (attribute) value field
def anonym_val(v, selectors, mode):
  '''
  Keep values that match some css selector and anonymize the rest.
  '''
  items = v.split()
  new_v = ''
  for item in items:
    new_v += ' '
    if item in selectors:  # css selector
      new_v += item
    elif '-' in item:  # composed value
      [key, suffix] = item.split('-', 1)
      if key in selectors:  # part of the value is a css selector
        new_v += key + '-' + anonym_str(suffix, mode)
      else:
        new_v += anonym_str(key, mode) + '-' + anonym_str(suffix, mode)
    else:  # not important to rendering
      new_v += anonym_str(item, mode)
  return new_v[1:]


# @param t(str)  a tag, looking like <name attr="val">, to be anonymized
# @param selectors(dict)  a dictionary of css selectors (id & class)
# @param mode(str)  How to replace a string with meaningless chars
# @return (str) Anonymized tag
def anonym_tag(t, selectors, mode):
  '''
  Anonymize a tag, any attribute that doesn't involve styling is anonymized.
  '''
  tag_label = re_tag_label.match(t).group('label')
  if tag_label in EXEMPTED_TAGS:
    return t
  new_t = t
  m_attrs = []
  for match in re_attr_sq.finditer(t):
    m_attrs.append(match)
  for match in re_attr_dq.finditer(t):
    m_attrs.append(match)
  for m_attr in m_attrs:
    name = m_attr.group('name')
    value = m_attr.group('value')
    if name in selectors.keys():  # id or class
      anon_value = anonym_val(value, selectors[name], mode)
      new_t = new_t.replace(
        m_attr.group(0),
        ' {name}="{value}"'.format(name=name, value=anon_value),
        1)
    elif name not in HTML_ELEMENTS:  # attributes not useful for styling
      anon_value = anonym_str(value, mode)
      new_t = new_t.replace(
        m_attr.group(0),
        ' {name}="{value}"'.format(name=name, value=anon_value),
        1)
  return new_t

#
# APIs
#


# @param dom(str)  the content to be prettified.
# @return (str)  containing prettified content.
def prettify(dom):
  '''
  Add indentation to a DOM file so that it is easier to read.
  '''
  # delete commenting
  dom = del_blockcomment(dom)
  start = 0
  depth = -1
  new_dom = ''
  m_tag = re_tag.search(dom)
  while m_tag:  # more tags
    tag = m_tag.group(0)
    label = re_tag_label.match(tag).group('label')
    # jump to the start of the tag, what's in front is probably comments
    current = dom.find(tag, start)
    if current > 0:
      new_dom += dom[start:current]
      start = current
    # indent tag
    if label not in EMPTY_ELEMENTS:  # has effect on depth
      if tag[1] == '/':  # closing tag
        depth -= 1
      else:  # opening tag
        depth += 1
      new_dom += indent(tag, depth)
    else:  # still need to indent by one unit more
      new_dom += indent(tag, depth + 1)
    # start a new line for content after a tag
    start += len(tag)
    current = skip_content(dom, start)
    if current > start and not re_empty.match(dom[start:current]):
      new_dom += indent(dom[start:current], depth + 1)
    start = current
    m_tag = re_tag.search(dom[start:])
  return new_dom


# @param dom(str)  source file content to be anonymized
# @param selectors(dict)  contains id & class list
# @param mode(str)  How to replace a string with meaningless chars
# @return (str)  anonymized source file
def anonym_dom(dom, selectors, mode):
  '''
  Anonymize the script by removing scripts that disclose user info,
  garble contents in the DOM tree, and stuff them back into big pipes.
  '''
  dom = del_blockcomment(dom)
  start = 0
  m_tag = re_tag.search(dom, start)
  new_dom = ''
  while m_tag:  # more tags
    tag = m_tag.group(0)
    # skipping content before the tag
    current = m_tag.start()
    if current > 0:
      new_dom += dom[start:current]
      start = current
    # handle tag
    if tag[1] == '/':  # closing tags are harmless
      new_dom += tag
    else:  # opening tag
      new_dom += anonym_tag(tag, selectors, mode)
    # getting none tag part after the tag
    start = m_tag.end()
    current = skip_content(dom, start)
    if current > start and\
      not re_empty.match(dom[start:current]) and\
      tag[1:7] != 'script':
      new_dom += anonym_str(dom[start:current], mode)
    else:
      new_dom += dom[start:current]
    start = current
    m_tag = re_tag.search(dom, start)
  return new_dom


# @param dom(str)  source file content to be anonymized
# @param pipe_exclude(list)  A list of group ids that should be excluded
# @return (dict)  anonymized source file and a list of all pagelet ids
def unload_pagelets(dom, pipe_exclude=[]):
  '''
  Only remove pagelets from DOM and stuff them back into the big pipes.
  We need to do this because otherwise the pipe content is not localized.
  '''
  m_pipes = []
  m_scripts = re_html_js.finditer(dom)
  for m_script in m_scripts:
    if re_html_bigpipe.match(m_script.group(0)):
      m_pipes.append(re_html_bigpipe.match(m_script.group(0)))
  # to handle pagelet embedding
  # we scan both the dom and already cut out nodes for
  pagelets = []
  nodes = {}   # with which we replace the "content" field of the pipe
  idx = 0
  ids = []
  for m_pipe in m_pipes:
    id = m_pipe.group('id')[6:-2]
    ids.append(id)
    pagelets.append(m_pipe.groupdict())
    pagelets[idx]['orig'] = m_pipe.group(0)
    # try cutting the content from dom tree first
    rootid = 'id="{id}"'.format(id=id)
    ret = cut_dom_node(dom, rootid)
    dom = ret['dom']
    nodes[idx] = ret['node']
    # empty pipes: last pagelet & pagelets that are not visible
    # (e.g. pagelet_nav_lite/pagelet_nav_full)
    # if not found (probably embedded in another node), get it from nodes
    # NOTE: the orig dom is not affected because the content is cut out already
    if nodes[idx] == '':
      for i in range(idx - 1):
        ret = cut_dom_node(nodes[i], rootid)
        if ret['node'] != '':
          nodes[idx] = ret['node']
          nodes[i] = ret['dom']
          break
    idx += 1
  # assemble the pipes with new content and replace the original pipes
  for idx in range(len(pagelets)):
    if nodes[idx]:
      pagelets[idx]['content'] = '"content":{' + pagelets[idx]['id'][5:-1] +\
      ':"' + jsonify(nodes[idx]) + '"},'
    else:
      pagelets[idx]['content'] = '"content":[],'
    pipe = '<script>big_pipe.onPageletArrive({'
    for field in PIPE_FIELDS:
      if pagelets[idx][field] and field not in pipe_exclude:
        pipe += pagelets[idx][field]
    pipe += '});</script>'
    dom = dom.replace(pagelets[idx]['orig'], pipe, 1)
  return {'html': dom, 'pagelets': ids}


# @param dom(str)  source file content to be de-javascripted
# @return (str)  descripted source file
def descript_html(dom):
  '''
  Set all scripts enclosed by a pair of script tags to null.
  '''
  return re_html_js.sub('<script></script>', dom)


# @param dom(str)  source file content to be de-javascripted
# @return (str)  descripted source file
def descript_onclick(dom):
  '''
  Set all onclicks to null.
  '''
  dom = re_onclick_sq.sub('', dom)
  dom = re_onclick_dq.sub('', dom)
  # dom = re_onclick_sq.sub(' onclick=""', dom)
  # dom = re_onclick_dq.sub(' onclick=""', dom)
  return dom


# @param dom(str)  dom content
# @return (str)  keep pipe related javascript only
def descript_pipeonly(dom):
  '''
  Delete all embedded scripts unless it is related to big pipe.
  '''
  m_scripts = re_html_js.finditer(dom)
  for m_script in m_scripts:
    content = m_script.group('content')
    if content and \
      content[:25] != 'Bootloader.setResourceMap' and\
      content[:8] != 'big_pipe':
      lines = m_script.group(0).split('\n')
      newlines = []
      for line in lines:  # keep the bootloader js, they matter to load
        if line.find('Bootloader.done') >= 0 or\
          line.find('Bootloader.configurePage') >= 0:
          newlines.append(line)
      dom = dom.replace(
        m_script.group(0),
        '<script>{script}</script>'.format(script='\n'.join(newlines)), 1)
  return dom

# @param dom(str)  dom content
# @return (str)  dom content without injected js reference
def descript_injected(dom):
  '''
  Delete all js references injected into the dom after loading.
  '''
  start = dom.find('title="Facebook"')
  end = dom.find('</head>')
  return dom[:start] + re_html_js.sub('', dom[start:end]) + dom[end:]


# @param dom(str)  dom content
# @return (str)  dom content without injected css references
def decss_injected(dom):
  '''
  Delete all css references injected into the dom after loading.
  '''
  start = dom.find('</title>')
  end = dom.find('</head>')
  return dom[:start] + re_html_css.sub('', dom[start:end]) + dom[end:]


# @param dom(str)  dom content
# @param dummy='dummy.css'(str)  a dummy css file to replace all legit css
# @return (str)  dom content without css references on any level
def unload_css(dom, dummy='dummy.css'):
  '''
  Delete all css references, both as tags and on resource maps.
  '''
  dom = re_html_css.sub(
    '<link type="text/css" rel="stylesheet" href="{url}">'.format(url=dummy),
    dom)
  return re_json_css.sub('"src":"{url}"'.format(url=dummy), dom)
