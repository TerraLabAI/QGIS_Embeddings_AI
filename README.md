# QGIS Embeddings AI

A QGIS plugin for geospatial similarity search using foundation model embeddings.

![Version](https://img.shields.io/badge/version-0.1.0-blue?style=flat-square)
![QGIS](https://img.shields.io/badge/QGIS-3.28%2B-green?style=flat-square)
![License](https://img.shields.io/badge/license-GPL--3.0-lightgrey?style=flat-square)

![Screenshot](docs/screenshot.png)

<img src="docs/screenshot_ui.png" width="300">

---

## What it does

This plugin finds locations similar to a reference point using AlphaEarth embeddings from Google Earth Engine. Each location on Earth is represented as a 64-dimensional vector that captures land cover patterns, seasonal dynamics, and spatial context.

## Features

- Point-based similarity search
- Configurable search radius (0.5 to 100 km)
- Year selection (2017-2023)
- Visual similarity heatmaps
- Export results as GeoTIFF
- Google Satellite basemap integration

## Requirements

- QGIS 3.28+
- Google Earth Engine Plugin (installed and authenticated)
- Google Cloud Project with Earth Engine API enabled

## Installation

**From QGIS Plugin Manager:**

Plugins → Manage and Install Plugins → Search "QGIS Embeddings AI" → Install

**Manual:**

Copy this folder to your QGIS plugins directory:
- macOS: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
- Windows: `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins/`
- Linux: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`

## Usage

1. Click the plugin icon in the toolbar
2. Import a basemap (optional)
3. Click "Add Point" and select a reference location
4. Adjust parameters (year, buffer, threshold, resolution)
5. Click "Search Similarity"
6. Export results with "Export Results" button

## Authors

**Lilien Auger** — [LinkedIn](https://www.linkedin.com/in/lilien-auger/)

**Yvann Barbot** — [LinkedIn](https://www.linkedin.com/in/yvann-barbot/)

**Stéphane Barbot** — [LinkedIn](https://www.linkedin.com/in/stephane-barbot/)

## License

GPL-3.0

## Acknowledgments

- Google DeepMind (AlphaEarth)
- Google Earth Engine
- QGIS community
