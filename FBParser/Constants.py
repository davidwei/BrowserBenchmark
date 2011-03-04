#!/usr/bin/env python
__doc__ = '''
FBParser/constants.py

Constants
'''
__author__ = 'Yao Yue(yyue), yueyao@facebook.com'

__all__ = [
            'INDENT_WIDTH',
            'MODE_MONO', 'MODE_BABBLE',
            'PIPE_FIELDS',
            'EMPTY_ELEMENTS', 'HTML_ELEMENTS', 'EXEMPTED_TAGS',
          ]

INDENT_WIDTH = 2

# how to anonymize characters
MODE_MONO = 0
MODE_BABBLE = 1

# list
PIPE_FIELDS = ('id', 'phase', 'last', 'append', 'dep', 'boot',
               'css', 'js', 'rscmap', 'require', 'provide',
               'oncache', 'onaftercache', 'refresh', 'invalidate',
               'content', 'cache')

EMPTY_ELEMENTS = [
                  'area', 'base', 'basefont', 'br', 'col', 'frame', 'wbr',
                  'hr', 'img', 'input', 'isindex', 'link', 'meta', 'param',
                 ]

HTML_ELEMENTS = [  # selector names that are useful to styling
                 'type', 'action', 'class', 'id', 'rel', 'media', 'href',
                 'meta', 'src', 'style', 'width', 'height', 'tabindex',
                ]

EXEMPTED_TAGS = [  # tags that need not be anonymized
                 'html', 'meta',
                ]
