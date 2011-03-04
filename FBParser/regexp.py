#!/usr/bin/env python
__doc__ = '''
FBParser/regexp.py

Regular Expressions
'''
__author__ = 'Yao Yue(yyue), yueyao@facebook.com'

__all__ = [
            're_html_img', 're_css_img',
            're_html_js', 're_json_js',
            're_onclick_sq', 're_onclick_dq', 're_html_bigpipe',
            're_html_css', 're_json_css',
            're_cssrule', 're_css_id', 're_css_class',
            're_blockcomment', 're_empty', 're_doctype', 're_iframe',
            're_tag', 're_tag_label',
            're_attr_sq', 're_attr_dq',
          ]

#
# Imports
#
import re

# general
re_doctype = re.compile('<!DOCTYPE.*?>')
re_blockcomment = re.compile("(?s)/\*.*?\*/")

# css related
# of src/href, NOTE: we ignore embedded css (<style></style> or style="")
re_html_css = re.compile('<link[^<>]*?href="(?P<url>[^"]+?\.css)".*?>')
re_json_css = re.compile('"src":"(?P<url>[^"]+?\.css)"')
# of css file content
re_cssrule = re.compile("(?P<selector>[^\s].*?){.*?}")
re_css_id = re.compile("#(\w+)")  # id selector (within a rule)
re_css_class = re.compile("\.(\w+)")  # class selector (within a rule)

# image related
re_html_img = re.compile(
'<img.*?src="(?P<url>[^"]+?\.(?P<ext>gif|png|jpg))".*?>')
re_css_img = re.compile('url\((?P<url>[^()]+?\.(?:jpg|gif|png))\)')

# javascript related
re_html_js = re.compile(
'(?s)<script[^<>]*?([\s]+src="(?P<url>[^"]+?\.js)")?[^>]*?>\
(?P<content>.*?)</script>')
re_json_js = re.compile('"src":"(?P<url>[^"]+?\.js)"')
re_onclick_sq = re.compile(" onclick='[^']*?'")
re_onclick_dq = re.compile(' onclick="[^"]*?"')
re_html_bigpipe = re.compile(
'(?s)<script>big_pipe\.onPageletArrive\(\{\
(?P<id>"id":"\w*?",)\
(?P<phase>"phase":\d+?,)\
(?P<last>"is_last":\w+?,)\
(?P<append>"append":\w+?,)\
(?P<dep>"display_dependency":\[[\w",]*?\],)?\
(?P<boot>"bootloadable":(?:\[\]|\{.+?\}),)\
(?P<css>"css":\[.*?\],)\
(?P<js>"js":\[.*?\],)\
(?P<rscmap>"resource_map":(?:\[\]|\{(?P<mapdict>.+?)\}),)\
(?P<require>"requires":\[(?P<req>.+?)?\],)\
(?P<provide>"provides":\[.*?\],)\
(?P<onload>"onload":\[.*?\],)\
(?P<onafterload>"onafterload":\[.*?\],)\
(?P<oncache>"onpagecache":\[.*?\],)\
(?P<onaftercache>"onafterpagecache":\[.*?\],)\
(?P<refresh>"refresh_pagelets":\[.*?\],)\
(?P<invalidate>"invalidate_cache":\[.*?\],)\
(?P<content>"content":(?:\[\]|\{.+?\}),)\
(?P<cache>"page_cache":\w+?)\}\);</script>')

re_tag = re.compile("(?s)<[\w/][^<>]*>")  # this matches both tag start and end
re_tag_label = re.compile("(?s)(?:<|</)(?P<label>[^\s]+).*?>")
# double quoted attr
re_attr_dq = re.compile('(?s)[\s]+(?:(?P<name>[^\s]+?)="(?P<value>[^"]*?)")')
# single quoted attr
re_attr_sq = re.compile("(?s)[\s]+(?:(?P<name>[^\s]+?)='(?P<value>[^']*?)')")

re_empty = re.compile("[\s]+$")
re_iframe = re.compile("(?s)<iframe(.*?)>(.*?)</iframe>")
