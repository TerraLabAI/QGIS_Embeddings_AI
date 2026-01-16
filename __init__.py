"""AlphaEarth - QGIS Plugin for geospatial similarity search using Google Earth Engine."""

from .alpha_earth import AlphaEarth


def classFactory(iface):
    """Load AlphaEarth plugin class."""
    return AlphaEarth(iface)
