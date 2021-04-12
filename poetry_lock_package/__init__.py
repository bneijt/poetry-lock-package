try:
    from importlib.metadata import version
except ImportError:
    # compatability import
    from importlib_metadata import version

__version__ = version(__name__)
