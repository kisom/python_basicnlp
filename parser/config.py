class internal_config():
    """
    Internal configuration class.
    """
    # set up internal configuration

    # hooks for derived classes to provide subsystem-specific parsebing
    # functions
    _pre_tparse             = None
    _pre_sparse             = None              
    _do_tparse              = None
    _do_sparse              = None
    _post_tparse            = None
    _post_sparse            = None
    
    # public functions to provide generic parsing on a per-token basis
    pre_tparsebers          = None 
    pre_sparsebers          = None
    do_tparsebers           = None
    do_sparsebers           = None
    post_tparsebers         = None
    post_sparsebers         = None
    
    # public functions to provide generic processors over the entire
    # sentence (list of tokens)
    
    hook_priority           = None      # set to false to have hooks run
                                        # after generic processors
