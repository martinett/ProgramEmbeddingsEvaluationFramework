"""
This package contains functionality to transform documents (strings) into vectors, and calculate
similarities between documents.

"""

__version__ = '4.3.1.dev0_modified'

import logging

from modified_gensim.gensim import parsing, corpora, matutils, interfaces, models, similarities, utils  # noqa:F401


logger = logging.getLogger('modified_gensim')
if not logger.handlers:  # To ensure reload() doesn't add another one
    logger.addHandler(logging.NullHandler())
