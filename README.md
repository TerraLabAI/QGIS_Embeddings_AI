# AlphaEarth - QGIS Plugin

**Geospatial similarity search using Google DeepMind's AlphaEarth embeddings via Google Earth Engine.**

![Plugin Version](https://img.shields.io/badge/version-0.1.0-blue)
![QGIS](https://img.shields.io/badge/QGIS-3.28%2B-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

## Overview

AlphaEarth is a QGIS plugin that enables geospatial similarity search using **AlphaEarth embeddings** — a Google DeepMind foundation model trained on petabyte-scale geospatial data. Discover similar geographic features anywhere on the globe through AI-driven vector similarity analysis.

## Features

- **Point-based search**: Select reference points on the map
- **Configurable buffer**: Define search radius (0.5 - 100 km)
- **Year selection**: Access data from 2017-2023
- **Similarity visualization**: Color-coded heatmap (green = similar, red = different)
- **Custom color palette**: Adjust visualization colors to your preference
- **Google Satellite basemap**: Quick import for reference

## Requirements

> **Important**: This plugin requires the Google Earth Engine plugin to function.

1. **QGIS 3.28+**
2. **Google Earth Engine Plugin** — Install from QGIS Plugin Manager
3. **Google Cloud Project** — With Earth Engine API enabled
4. **GEE Authentication** — Connected and authenticated

## Installation

1. Download or clone this repository
2. Copy the `AlphaEarth-Lilien` folder to your QGIS plugins directory:
   - **macOS**: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
   - **Windows**: `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
   - **Linux**: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
3. Restart QGIS
4. Enable the plugin in **Plugins → Manage and Install Plugins**

## Usage

1. Click the **AlphaEarth** icon in the toolbar
2. Import a basemap for reference (optional)
3. Use **Add Point** to select a reference location on the map
4. Adjust parameters:
   - **Year**: Select the year for satellite data (2017-2023)
   - **Buffer**: Search radius in kilometers
   - **Threshold**: Maximum distance for visualization
   - **Resolution**: Output resolution in meters
5. Click **Search Similarity**
6. Results appear as layers in QGIS

## Project Structure

```
AlphaEarth-Lilien/
├── __init__.py          # Plugin entry point
├── alpha_earth.py       # Main plugin class
├── metadata.txt         # Plugin metadata
├── icons/               # Plugin icons
│   └── alpha_earth.svg
├── tools/               # Core functionality
│   ├── canvas_tool.py   # Map interaction tools
│   ├── gee_tool.py      # GEE integration
│   └── widget_tool.py   # Main UI widget
└── ui/                  # UI configuration
    └── __init__.py
```

## Technical Details

### AlphaEarth Embeddings

The plugin uses `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL` image collection from Google Earth Engine. These embeddings encode geospatial features into high-dimensional vectors, enabling similarity comparison through Euclidean distance.

### Similarity Calculation

1. Extract mean embedding vector from reference geometry
2. Calculate Euclidean distance for each pixel in search area
3. Visualize as color gradient (configurable palette)

## Author

**Lilien Auger**  
[LinkedIn](https://www.linkedin.com/in/lilien-auger/)

## License

MIT License - See LICENSE file for details.

## Contributing

Issues and pull requests are welcome on the [GitHub repository](https://github.com/lilien/alpha-earth-qgis).
