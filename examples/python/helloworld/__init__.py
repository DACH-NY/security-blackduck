"""
project metadata
"""

try:
    import importlib.metadata as importlib_metadata
except ModuleNotFoundError:
    import importlib_metadata

__version__ = importlib_metadata.version(__name__)
__title__ = "helloworld"
__description__ = "Simple hello world python sample"
