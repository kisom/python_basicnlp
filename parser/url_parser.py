# -*- coding: utf-8 -*-
# file: url_parser.py
# author: kyle isom
# license: ISC / public domain dual-licensed
#
# url scanning token parser

from token_parser import TokenParser

class UrlParser(TokenParser):
    def __init__(self, tokens):
        TokenParser.__init__(self, tokens)

    def _init_hooks(self):
        self.regex['url'] = 'https?://(\\w)+\.(\\w)(([\\w/.]*)*)'

        self.TokenDict['sites']     = [ ]
        self.TokenDict['titles']    = [ ]


