#!/usr/bin/env python
# -*- coding: utf-8 -*-
# file: macro_parser.py
# author: kyle isom <coder@kyleisom.net>
# license: ISC / public domain dual-license
#
# collections of TokenParsers

from token_parser import TokenParser
from nltk import FreqDist

class MacroParser():
    """
    MacroParser is a collection of TokenParsers that stores frequency
    distributions of the Parsers in its database. It is designed to be the 
    basis for a statistical analysis of tokens in a given structure. It is 
    built by storing a number of TokenParsers. Multiple extensions to 
    TokenParser can be used, for example a TwitterParser and WebParser, 
    provided both are valid extensions of the TokenParser class.
    
    If the class is going to be dealing primarily or entirely with a 
    specific type of TokenParser, the class may be extended and the 
    attribute self.DefaultParserClass overridden from its default of 
    TokenParser to the derived class (i.e. WebParser). There is also an 
    _init_hooks() function (by default an empty passing function) to 
    perform any custom setup.
    
    There are four entry methods to add data to an instance:
        import_parser(p)        -   import a TokenParser p
        import_raw(text)        -   import text. This is implemented such 
                                    that a new DefaultParserClass is 
                                    created with text as the argument. This 
                                    new TokenParser is added to the list 
                                    of Parsers.
        load_parsers(p_list)    -   load a list of parsers. calls 
                                    import_parser on each p.
        load_raw(texts)         -   expects texts to be a list containing 
                                    the inputs to len(texts) new 
                                    DefaultParserClass objects.
    
    There are three data access functions:
        get_keys()              -   returns a list of stored distributions
        get_fd(key)             -   returns the FreqDist stored in key or 
                                    None in the case of an invalid key.
        get_parsers()           -   returns the list of parsers
    """
    
    Parsers                     = None
    Distributions               = None
    DistributionKeys            = None
    
    DefaultParserClass          = None
    
    
    def __init__(self):
        self.Parsers            = [ ]
        self.DistributionKeys   = [ ]
        self.Distributions      = { }
        
        self.DefaultParserClass = TokenParser
        
        self._init_hooks()
    
    def _init_hooks(self):
        """
        Custom initialisation code to be overridden in derived classes.
        """
        pass
    
    def import_parser(self, p):
        """
        Import a single TokenParser. Expects p to have a TokenDict 
        dictionary.
        """
        
        if p in self.Parsers:
            return None
        
        self.Parsers.append(p)
        
        keys    = p.TokenDict.keys()
        
        for key in keys:
            if not key in self.DistributionKeys:
                loader                      = "p." + key + "()"
                data                        = eval(loader)
                self.Distributions[key]     = FreqDist(data)
                self.DistributionKeys.append(key)
            else:
                for token in p.TokenDict[key]:
                    self.Distributions[key].inc(token)
                
    
    def import_raw(self, text):
        """
        Creates a new TokenParser from text.
        """
        p = self.DefaultParserClass(text)
        self.import_parser(p)
    

    def load_parsers(p_list):
        """
        Load a list of TokenParsers into the MacroParser.
        """
        for p in p_list:
            self.import_parser(p)
    
    
    def load_raw(self, texts):
        """
        Load a list of texts into the MacroParser.
        """
        for text in texts:
            self.import_raw(text)


    def get_fd(self, key):
        if key in self.DistributionKeys:
            return self.Distributions[key]
        else:
            return None
    
    def get_keys(self):
        return self.DistributionKeys
    
    def get_parsers(self):
        return self.Parsers
