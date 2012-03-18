#!/usr/bin/env python
# -*- coding: utf-8 -*-
# file: token_parser.py
# author: kyle isom <coder@kyleisom.net>
# license: ISC / public domain dual-license
#
# crude NLP code
"""
Contains functions for cleaning tokens of punctuation and invalid 
characters, identifying special characters, and preparing token lists for 
natural language processing. This class is inheritable and provides hooks 
for subsystem-specific parsing.
"""

import re
from config import internal_config

class TokenParser():
    """
    This class takes a list of tokens, processes them, and provides a list 
    of 'clean' tokens, separating out special tokens. There are several 
    special methods, all of which do not take arguments:
        sent:       returns a list of tokens where punctuation is included 
                    as separate elements.
        tokens:     returns a list of the original tokens passed into the
                    parser.
        clean:      returns a list of the clean tokens.
        special:    returns a list of special tokens.
        
    The parser works in three passes:
        pre_parse:  identify special tokens and add those to the list of 
                    special tokens so they are not lost during the parse.
        parse:      separates out punctuation into separate elements; 
                    creates a sentence which allows for NLP to parse the 
                    original sentence and a list of cleaned tokens which 
                    allows for keyword-matching.
        post_parse: any post-processing
        
    Specialized collection systems can inherit this class. In the __init__
    function, set up the hook functions in the config class
    (self.config._pre_tparse, self.config._do_tparse, 
    self.config._post_tparse) to run custom code. By default, hooks run 
    before the generic code, but 
    passing hook_priority = False to the instantiator will cause the hooks 
    to be run after the built-in functions. Any specialized hook functions 
    and changes to the internal variables should be set up in the derived 
    class's _init_hooks(self) method, which is run between setting up the 
    configuration object and the token representation dictionary. You can 
    define your _pre_tparse and so forth functions here as well as set up 
    custom config vars and regexes (self.regex[key]). There is also a 
    special post-processing function, _post_hooks(). By default, it is an 
    empty function that simply passes. This may be overridden to perform 
    specific post-processing actions.
    
    There are two types of parsing passes:
        token parsers (tparse):     parse each token list comprehension-
                                    style. generic parse function provided
                                    by parse_token(). token_parsers
                                    should return true or false; the
                                    parse_token function returns the list
                                    of tokens that matched. See __init__
                                    for an example of how to use this.
        sentence parsers (sparse):  parse the token list as a whole.
                                    sentence parsers should return a list
                                    of tokens (i.e. a sentence). the
                                    framework is provided by parse_sent.
    
    Also by default, the __str__ method will return the sentence list, 
    i.e. a list of tokens with punctuation.
    
    Hooks:
        There are six hooks: a tparse and sparse version of the pre, do, 
        and post-parsing. Ex, _pre_tparse, _do_sparse.
    
    Implementing a Derived Class:
        1. Add any additional TokenDict types, config attributes, regexes, 
        and parse hooks in an overridden _init_hooks method.
            a. If the derived class should perform its custom parsing 
            functions after the built-in functions, set 
            self.config.hook_priority to False.
            b. If there are certain custom tokens that should be preserved 
            in the final sentence, append the functions to 
            self.config.preserve_tokens.
        2. For any custom parsing functions, ensure they are implemented in         the class as per the rules above.
        3. For any new TokenDict keys, ensure each new key has a self.key() 
        and self.key_str() method that return the raw list and a string of 
        the associated value.
        4. If there is any custom post-processing to be done, the functions 
        may be added to _post_hooks. This may be useful for filling new 
        TokenDict key values.
    
    """

    ################
    # DATA MEMBERS #
    ################
    
    # data structures
    
    # regex dictionary is used to store regexes for use in parsing methods
    regex   = {
        'url':'[^\w\s]?([a-zA-Z]+://)?([a-z[A-Z]\w*\.)+(\w{2,8})+(/\w+)*[^\w\s]?',
        'email':'^([\w\!\#$\%\&\'\*\+\-\/\=\?\^\`{\|\}\~]+\.)*[\w\!\#$\%\&\'' +
                '\*\+\-\/\=\?\^\`{\|\}\~]+@((((([a-z0-9]{1}[a-z0-9\-]{0,62}'  +
                '[a-z0-9]{1})|[a-z])\.)+[a-z]{2,6})|(\d{1,3}\.){3}\d{1,3}'    +
                '(\:\d{1,5})?)$',
        'ticker':'^(\()?\$([A-Z]{1,5})(\))?$',
        'punc':'([\\s\\w]*)([^\\w\\s])([\\s\\w]*)',
        'emoticon':'(:-?[()OD/])',
        'strip':'[@#$%^&*]'
        }

    # internal TokenParser structure
    TokenDict   = None
    config      = None

    
    ##########################
    # initialization methods #
    ##########################
    
    def __init__(self, tokens):
        if hasattr(tokens, 'split'):        # if tokens is passed in as str,
            tokens = tokens.split(" ")      # convert to a list
            
        self._init_config()
        self._init_token_dict()
        self._init_hooks() 

        self.TokenDict['tokens'] = tokens[:]
        
        self.TokenDict['special'].extend(self._parse_tokens(
                                                self.config._pre_tparse,
                                                self.config.pre_tparsers,
                                                tokens[:]))
        self.TokenDict['sent']   = self._parse_sent(
                                                self.config._do_sparse,
                                                self.config.do_sparsers,
                                                tokens[:])
        self.TokenDict['clean']  = self._clean_tokens(
                                                self.TokenDict['sent'])
        self._post_hooks()                  # set up any post processing
        
    def _init_config(self):
        self.config = internal_config( )    
        self.config.hook_priority = True
        self.config.pre_tparsers  = [ 'self._is_url', 'self._is_emoticon',
                                      'self._is_stock', 'self._is_email' ]
        self.config.pre_sparsers  = [ ]
        self.config.do_tparsers   = [ ]
        self.config.do_sparsers   = [ 'self._replace_punctuation' ]
        self.config.post_tparsers = [ ]
        self.config.post_sparsers = [ ]
        
        # hooks
        self.config._pre_sparse     = [ ]
        self.config._pre_tparse     = [ ]
        self.config._do_sparse      = [ ]
        self.config._do_tparse      = [ ]
        self.config._pass_sparse    = [ ]
        self.config._pass_tparse    = [ ]
        
        # protected special tokens are special characters that should be
        # preserved because the special characters have semantic meaning to
        # the rest of the sentence. For example, a URL should be preserved.
        self.config.preserve_token  = [ 'self._is_url', 'self._is_emoticon',
                                        'self._is_stock' ]
    
    def _init_token_dict(self):
        self.TokenDict   = { }
        self.TokenDict['sent']      = [ ]   # store list of tokens such as
                                            # punctuation & special chars
        self.TokenDict['special']   = [ ]   # store special tokens like URLs
        self.TokenDict['clean']     = [ ]   # stores list of tokens without
                                            # punctuation or special chars
        self.TokenDict['tokens']    = [ ]   # the original list of tokens 
                                            # instance was instantiated with
    
    def _init_hooks(self):
        pass

    def _post_hooks(self):
        pass

    def __str__(self):
        return ''.join(self.TokenDict['sent'])
    
    
    ###################################
    # TokenDict access methods follow #
    ###################################
    
    def sent(self):
        return self.TokenDict['sent']
    
    def sent_str(self):
        return ' '.join(self.TokenDict['sent'])
        
    def special(self):
        return self.TokenDict['special']
    
    def special_str(self):
        return  ' '.join(self.TokenDict['special'])
    
    def clean(self):
        return self.TokenDict['clean']
    
    def clean_str(self):
        return ' '.join(self.TokenDict['clean'])
        
    def tokens(self):
        return self.TokenDict['tokens']
    
    def tokens_str(self):
        return ' '.join(self.TokenDict['tokens'])
            

    #########################
    # parser methods follow #
    #########################
    
    def _parse_tokens(self, hook, parsers, tokens):
        """
        Generic parsing pass method.
            hook should be the hook that derived classes can use to provide
            specific targeting, ex. config._do_parse. The hook will be a 
            pointer to a list of functions, i.e. [ '_is_usertag', 
            '_is_hashtag' ]
            
            parsers should be the function list for the pass, i.e.
            config.do_parse
            
            tokens is the list of tokens to be acted on, i.e. 
            TokenDict['sent'].
            
            Returns the parsebed list of tokens.
        """
        _tokens = [ ]                       # internal token list
        special = None
        
        if hook and self.config.hook_priority:
            
            for f in hook:
                if not f: continue
                special = [ token for token in tokens if eval(f)(token)]
                _tokens.extend(special)
            
        if parsers:
            for f in parsers:
                if not f: break
                special = [ token for token in tokens if eval(f)(token)]
                _tokens.extend(special)
            
        if hook and not self.config.hook_priority:
            for f in hook:
                if not f: continue
                special = [ token for token in tokens if eval(f)(token)]
                if special: _tokens.extend(special)

        
        return _tokens

    def _parse_sent(self, hook, parsers, tokens):
        """
        Generic sentence parsing pass method.
            hook should be the hook that derived classes can use to provide
            specific targeting, ex. config._do_parse. The hook will be a 
            pointer to a list of functions, i.e. [ '_is_usertag', 
            '_is_hashtag' ]
            
            parsers should be the function list for the pass, i.e.
            config.do_parse
            
            tokens is the list of tokens to be acted on, i.e. 
            TokenDict['sent'].
            
            Returns the parsed list of tokens.        
        """
        
        _tokens = tokens
        
        if hook and self.config.hook_priority:
            for f in hook:
                _tokens = eval(f)(_tokens)
        
        if parsers:
            for f in parsers:
                _tokens = eval(f)(_tokens)
        
        if hook and not self.config.hook_priority:
            for f in hook:
                _tokens = eval(f)(_tokens)
                
        return _tokens

    def _clean_tokens(self, tokens):
        _tokens =   [ token.lower() for token in tokens
                      if not token in self.TokenDict['special'] and
                         self._is_word(token)
                    ]
        return _tokens

    ##############################
    # internal parsing functions #
    ##############################
    
    def _is_url(self, token):
        """
        private function to determine if a token is a url.
        """
        return re.match(self.regex['url'], token, re.U)
    
    def _is_stock(self, token):
        """
        private function to determine if a token is a stock symbol
        """
        return re.match(self.regex['ticker'] , token, re.U)
    
    def _replace_punctuation(self, tokens):
        
        _tokens = tokens
        
        # strip characters should be stripped from any token and *not* 
        # inserted into a sentence.
        r = len(_tokens)
        i = 0
        
        while i < r:
            ignore = False
            for f in self.config.preserve_token:
                if eval(f)(_tokens[i]): ignore = True
            
            match = re.search(self.regex['punc'], _tokens[i], re.U)
            if not ignore and match:    # 'punc' regex uses second match to
                                        # store captured punctuation
                # store punctuation and parse it
                p           = match.group(2)
                _tokens[i]   = re.sub(self.regex['punc'], '\\1 \\3',
                                     _tokens[i], re.U)
                insert = _tokens[i].split()
                
                if not re.match(self.regex['strip'], p, re.U):
                    insert.insert(1, p)
    
                # and insert the punctuation after current token
                i += 1
                r += len(insert) - 1
                _tokens = _tokens[:i - 1] + insert + _tokens[i:]
    
            i += 1
        
        _tokens  = [ token for token in _tokens if not token == '' ]

        return _tokens
    
    def _is_emoticon(self, token):
        return re.match(self.regex['emoticon'], token, re.U)
    
    def _is_email(self, token):
        return re.match(self.regex['email'], token, re.I | re.U)
    
    def _is_word(self, token):
        return re.match('^\w*$', token, re.U)

