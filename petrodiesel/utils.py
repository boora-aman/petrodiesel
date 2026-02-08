"""Compatibility shim for legacy imports.

Routes petrodiesel.utils to the actual module under petrodiesel.petrodiesel.utils.
"""

from petrodiesel.petrodiesel.utils import *  # noqa: F401,F403
