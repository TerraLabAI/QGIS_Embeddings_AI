"""AlphaEarth icons module."""

import os
from qgis.PyQt.QtGui import QIcon

_icons_dir = os.path.dirname(__file__)


def get_icon(name):
    """Get icon by filename."""
    return QIcon(os.path.join(_icons_dir, name))


ICON_ALPHA_EARTH = get_icon("alpha_earth.svg")
