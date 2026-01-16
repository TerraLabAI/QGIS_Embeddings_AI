# QGIS Embeddings AI

**Unlock the power of geospatial foundation models directly in QGIS**

![Plugin Version](https://img.shields.io/badge/version-0.1.0-blue)
![QGIS](https://img.shields.io/badge/QGIS-3.28%2B-green)
![License](https://img.shields.io/badge/license-GPL--3.0-lightgrey)

---

## What are Geospatial Foundation Models?

**Foundation models** are large-scale AI systems pre-trained on massive amounts of diverse geospatial data. Think of them as the "GPT" of Earth observation — they learn universal representations of our planet's surface that can be adapted to countless downstream tasks.

### How do they work?

1. **Training**: Models are trained on petabyte-scale datasets combining satellite imagery (optical + radar), elevation data, climate variables, and even text from Wikipedia and biodiversity databases.

2. **Embeddings**: Instead of storing raw pixels, the model converts each location into a **64-dimensional vector** (an "embedding") — a compact mathematical fingerprint that encodes:
   - Land cover and terrain patterns
   - Seasonal and temporal dynamics
   - Spatial context and relationships
   - Semantic meaning (what things *are*, not just how they look)

3. **Applications**: These embeddings enable powerful capabilities:
   - **Similarity search**: Find locations globally that "look like" your reference area
   - **Zero-shot learning**: Classify new phenomena without training data
   - **Multi-modal fusion**: Combine optical, radar, elevation seamlessly
   - **Text queries**: "Find tropical forests near water" → instant map

### Why embeddings?

- **Compression**: 16x data reduction while preserving information
- **Speed**: Pre-computed representations for instant analysis
- **Flexibility**: One model → many tasks (classification, segmentation, change detection)
- **Universality**: Works anywhere on Earth, across sensors and time periods

---

## Supported Foundation Models

| Model | Provider | Specialty | Status |
|-------|----------|-----------|--------|
| **AlphaEarth** | Google DeepMind | General-purpose Earth observation | ✅ Active |
| Clay | Clay Foundation | Multi-sensor embeddings | 🔜 Coming soon |
| Prithvi | IBM/NASA | Multi-temporal analysis | 🔜 Coming soon |

---

## Features

### Current (v0.1.0)
- ✅ **Point-based similarity search** with AlphaEarth
- ✅ **Configurable search radius** (0.5 - 100 km)
- ✅ **Year selection** (2017-2023)
- ✅ **Visual similarity heatmaps** (color-coded: green = similar, red = different)
- ✅ **Google Satellite basemap** integration

### Roadmap
- 🔜 Support for additional foundation models (Clay, Prithvi)
- 🔜 Text-to-map semantic search
- 🔜 Batch processing for large areas
- 🔜 Custom model fine-tuning interface

---

## Requirements

> **Critical**: This plugin requires the Google Earth Engine plugin

1. **QGIS 3.28+**
2. **Google Earth Engine Plugin** — Install from QGIS Plugin Manager
3. **Google Cloud Project** with Earth Engine API enabled
4. **GEE Authentication** — Connected and authenticated

---

## Installation

### From QGIS Plugin Manager (Recommended)
1. Open QGIS → **Plugins** → **Manage and Install Plugins**
2. Search for **"QGIS Embeddings AI"**
3. Click **Install**

### Manual Installation
1. Download or clone this repository
2. Copy folder to your QGIS plugins directory:
   - **macOS**: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
   - **Windows**: `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
   - **Linux**: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
3. Restart QGIS
4. Enable in **Plugins → Manage and Install Plugins**

---

## Usage

### Quick Start

1. **Launch the plugin**  
   Click the QGIS Embeddings AI icon in the toolbar

2. **Import a basemap** (optional)  
   Use the "Import Map" button for reference imagery

3. **Select a reference location**  
   Click "Add Point" and select a point of interest on the map

4. **Configure search parameters**
   - **Year**: Satellite data year (2017-2023)
   - **Buffer**: Search radius in kilometers
   - **Threshold**: Maximum dissimilarity (0-1)
   - **Resolution**: Output resolution in meters

5. **Run similarity search**  
   Click "Search Similarity" and wait for results

6. **Interpret results**  
   A new raster layer shows similarity:
   - **Green**: High similarity (vector distance close to 0)
   - **Yellow**: Medium similarity
   - **Red**: Low similarity (dissimilar areas)

---

## Technical Details

### AlphaEarth Architecture

- **Model**: Vision Transformer with STP (Space-Time-Precision) blocks
- **Input**: 10m resolution imagery (Sentinel-2, Landsat, SAR, DEM, ERA5, text)
- **Output**: 64-dimensional unit vector on hypersphere (von Mises-Fisher distribution)
- **Training**: Self-supervised contrastive learning on petabyte-scale data
- **Similarity metric**: Euclidean distance in embedding space

### Data Flow

```
User selects point → Extract mean embedding vector → Calculate distance for search area → Visualize as heatmap
```

---

## Project Structure

```
QGIS-Embeddings-AI/
├── __init__.py          # Plugin entry point
├── alpha_earth.py       # Main plugin class
├── metadata.txt         # Plugin metadata
├── LICENSE              # GPL-3.0 License
├── README.md            # This file
├── icons/               # Plugin icons
│   └── alpha_earth.svg
├── tools/               # Core functionality
│   ├── canvas_tool.py   # Map interaction tools
│   ├── gee_tool.py      # Google Earth Engine integration
│   └── widget_tool.py   # Main UI widget
└── ui/                  # UI configuration
    └── __init__.py
```

---

## Contributing

We welcome contributions! Future priorities:
- Integration of new foundation models (Clay, Prithvi, Satlas)
- Text-to-map semantic search
- Fine-tuning workflows for custom tasks
- Performance optimizations for large-scale analysis

---

## Citation

If you use this plugin in research, please cite:

```
QGIS Embeddings AI (2025). Open-source plugin for geospatial foundation models.
https://github.com/youruser/QGIS-Embeddings-AI
```

For AlphaEarth specifically:
```
Brown et al. (2024). AlphaEarth: A Foundation Model for Geospatial Analysis.
Google DeepMind.
```

---

## Author

**Lilien Auger**  
[LinkedIn](https://www.linkedin.com/in/lilien-auger/)

---

## License

GPL-3.0 License - See [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- Google DeepMind for AlphaEarth
- Google Earth Engine team
- QGIS community
