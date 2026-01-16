"""Main widget for AlphaEarth plugin - Similarity Search Dock."""

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox,
    QDoubleSpinBox, QListWidget, QListWidgetItem, QComboBox, QAbstractItemView,
    QTabWidget, QFrame, QSlider, QSpinBox, QScrollArea, QToolButton,
)
from qgis.PyQt.QtGui import QFont, QColor
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY,
    QgsSingleSymbolRenderer, QgsMarkerSymbol, QgsFillSymbol, QgsRasterLayer,
    QgsMessageLog, Qgis,
)
from qgis.gui import QgsColorButton

from .canvas_tool import PointPickerTool, BBoxPickerTool, PolygonPickerTool, ColorPickerTool
from .gee_tool import GEESimilaritySearch


class GeometryItem(QListWidgetItem):
    """Custom list item for geometry data."""
    
    def __init__(self, geom_type, data, name="", layer_id=None):
        super().__init__()
        self.geom_type = geom_type
        self.geom_data = data
        self.geom_name = name
        self.layer_id = layer_id
        self._update_display()
        self.setFlags(self.flags() | Qt.ItemIsEditable)
    
    def _update_display(self):
        prefixes = {'point': '[P]', 'bbox': '[B]', 'polygon': '[G]'}
        prefix = prefixes.get(self.geom_type, '[?]')
        self.setText(f"{prefix} {self.geom_name}")
    
    def setData(self, role, value):
        super().setData(role, value)
        if role == Qt.EditRole:
            text = value
            for prefix in ['[P]', '[B]', '[G]', '[?]']:
                if text.startswith(prefix):
                    text = text[len(prefix):].strip()
                    break
            self.geom_name = text
            self._update_display()


class SimilaritySearchWidget(QDockWidget):
    """Dockable panel for AlphaEarth similarity search."""

    STYLE_TOOL_NORMAL = """
        QPushButton {
            background-color: #4a4a4a; color: #e0e0e0;
            padding: 8px 12px; border-radius: 4px;
            border: 1px solid #5a5a5a; min-width: 60px;
        }
        QPushButton:hover { background-color: #5a5a5a; }
    """
    
    STYLE_TOOL_ACTIVE = """
        QPushButton {
            background-color: #5c7a99; color: white; font-weight: bold;
            padding: 8px 12px; border-radius: 4px;
            border: 2px solid #7a9bb8; min-width: 60px;
        }
        QPushButton:hover { background-color: #6d8aa8; }
    """
    
    STYLE_ACTION_PRIMARY = """
        QPushButton {
            background-color: #6b89a8; color: white; font-weight: bold;
            padding: 10px; border-radius: 4px;
        }
        QPushButton:hover { background-color: #7a9bb8; }
        QPushButton:disabled { background-color: #3a3a3a; color: #888888; }
    """
    
    STYLE_BASEMAP_BTN = """
        QPushButton {
            background-color: #5a6a7a; color: white; font-weight: bold;
            padding: 8px; border-radius: 4px;
        }
        QPushButton:hover { background-color: #6a7a8a; }
    """
    
    PREVIEW_COLOR_POINT = "#7a9bb8"
    PREVIEW_COLOR_BBOX = "#8a9aa8"
    PREVIEW_COLOR_POLYGON = "#6a8a9a"
    
    YEAR_MIN = 2017
    YEAR_MAX = 2023

    def __init__(self, iface, plugin_dir, parent=None):
        super().__init__("AlphaEarth Tool", parent)
        self.iface = iface
        self.plugin_dir = plugin_dir
        self.canvas = iface.mapCanvas()
        
        self.current_tool = None
        self.previous_map_tool = None
        self.gee_search = GEESimilaritySearch()
        self.geometry_counter = {'point': 0, 'bbox': 0, 'polygon': 0}
        self.preview_layers = {}
        
        self.point_tool = None
        self.bbox_tool = None
        self.polygon_tool = None
        
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.setMinimumWidth(320)
        
        self._setup_ui()
        QgsProject.instance().layerWillBeRemoved.connect(self._on_layer_removed_from_qgis)
    
    def _setup_ui(self):
        """Build the user interface."""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setWidget(scroll_area)
        
        content_widget = QWidget()
        scroll_area.setWidget(content_widget)
        
        main_layout = QVBoxLayout(content_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # === SEARCH TAB ===
        search_tab = QWidget()
        search_layout = QVBoxLayout(search_tab)
        search_layout.setSpacing(12)
        search_layout.setContentsMargins(8, 8, 8, 8)
        self.tab_widget.addTab(search_tab, "Search")
        
        # Basemap
        basemap_group = QGroupBox("Basemap")
        basemap_layout = QHBoxLayout(basemap_group)
        self.btn_add_basemap = QPushButton("Import Map")
        self.btn_add_basemap.setStyleSheet(self.STYLE_BASEMAP_BTN)
        self.btn_add_basemap.setToolTip("Import Google Satellite as reference")
        self.btn_add_basemap.clicked.connect(self._on_add_basemap_clicked)
        basemap_layout.addWidget(self.btn_add_basemap)
        search_layout.addWidget(basemap_group)
        
        # Tools
        prompts_frame = QFrame()
        prompts_frame.setFrameStyle(QFrame.StyledPanel)
        prompts_layout = QVBoxLayout(prompts_frame)
        prompts_layout.setSpacing(8)
        
        tools_row = QHBoxLayout()
        self.btn_point = QPushButton("Add Point")
        self.btn_point.setCheckable(True)
        self.btn_point.setStyleSheet(self.STYLE_TOOL_NORMAL)
        self.btn_point.setToolTip("Click on map to add a reference point")
        self.btn_point.clicked.connect(lambda: self._on_tool_clicked('point'))
        tools_row.addWidget(self.btn_point)
        tools_row.addStretch()
        prompts_layout.addLayout(tools_row)
        
        # Hidden buttons for compatibility
        self.btn_bbox = QPushButton()
        self.btn_bbox.setCheckable(True)
        self.btn_bbox.hide()
        self.btn_polygon = QPushButton()
        self.btn_polygon.setCheckable(True)
        self.btn_polygon.hide()
        
        actions_row = QHBoxLayout()
        self.btn_clear = QPushButton("Clear")
        self.btn_clear.clicked.connect(self._on_clear_clicked)
        actions_row.addWidget(self.btn_clear)
        self.btn_undo = QPushButton("Undo")
        self.btn_undo.clicked.connect(self._on_undo_clicked)
        actions_row.addWidget(self.btn_undo)
        prompts_layout.addLayout(actions_row)
        
        search_layout.addWidget(prompts_frame)
        
        # Geometries List
        list_group = QGroupBox("Geometries")
        list_layout = QVBoxLayout(list_group)
        self.list_geometries = QListWidget()
        self.list_geometries.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_geometries.setMinimumHeight(100)
        self.list_geometries.setMaximumHeight(150)
        self.list_geometries.itemChanged.connect(self._on_geometry_renamed)
        list_layout.addWidget(self.list_geometries)
        self.btn_remove = QPushButton("Remove Selected")
        self.btn_remove.clicked.connect(self._on_remove_clicked)
        list_layout.addWidget(self.btn_remove)
        search_layout.addWidget(list_group)
        
        # Run Button
        self.btn_run = QPushButton("Search Similarity")
        self.btn_run.setEnabled(False)
        self.btn_run.setStyleSheet(self.STYLE_ACTION_PRIMARY)
        self.btn_run.setMinimumHeight(40)
        self.btn_run.clicked.connect(self._on_run_clicked)
        search_layout.addWidget(self.btn_run)
        
        # Parameters
        params_group = QGroupBox("Parameters")
        params_layout = QVBoxLayout(params_group)
        
        year_row = QHBoxLayout()
        year_row.addWidget(QLabel("Year:"))
        self.spin_year = QSpinBox()
        self.spin_year.setRange(self.YEAR_MIN, self.YEAR_MAX)
        self.spin_year.setValue(2023)
        year_row.addWidget(self.spin_year)
        year_row.addStretch()
        params_layout.addLayout(year_row)
        
        buffer_row = QHBoxLayout()
        buffer_row.addWidget(QLabel("Buffer (km):"))
        self.spin_buffer = QDoubleSpinBox()
        self.spin_buffer.setRange(0.5, 100.0)
        self.spin_buffer.setValue(5.0)
        buffer_row.addWidget(self.spin_buffer)
        params_layout.addLayout(buffer_row)
        
        thresh_row = QHBoxLayout()
        thresh_row.addWidget(QLabel("Threshold:"))
        self.spin_threshold = QDoubleSpinBox()
        self.spin_threshold.setRange(0.1, 2.0)
        self.spin_threshold.setValue(0.5)
        self.spin_threshold.setSingleStep(0.1)
        thresh_row.addWidget(self.spin_threshold)
        params_layout.addLayout(thresh_row)
        
        res_row = QHBoxLayout()
        res_row.addWidget(QLabel("Resolution (m):"))
        self.spin_resolution = QSpinBox()
        self.spin_resolution.setRange(10, 200)
        self.spin_resolution.setValue(30)
        res_row.addWidget(self.spin_resolution)
        params_layout.addLayout(res_row)
        search_layout.addWidget(params_group)
        
        # Colors
        styles_group = QGroupBox("Similarity Colors")
        styles_group.setCheckable(True)
        styles_group.setChecked(False)
        styles_layout = QVBoxLayout(styles_group)
        
        for name, default, attr in [("Similar", "#00FF00", "color_similar"), 
                                    ("Neutral", "#FFFF00", "color_neutral"), 
                                    ("Different", "#FF0000", "color_different")]:
            row = QHBoxLayout()
            row.addWidget(QLabel(f"{name}:"))
            btn = QgsColorButton()
            btn.setColor(QColor(default))
            setattr(self, attr, btn)
            row.addWidget(btn)
            row.addStretch()
            styles_layout.addLayout(row)
        search_layout.addWidget(styles_group)
        
        self.btn_toggle_similarity = QPushButton("Show Similarity Only")
        self.btn_toggle_similarity.setCheckable(True)
        self.btn_toggle_similarity.clicked.connect(self._on_toggle_similarity_clicked)
        search_layout.addWidget(self.btn_toggle_similarity)
        search_layout.addStretch()
        
        # === EXTRACT TAB (hidden) ===
        extract_tab = QWidget()
        extract_layout = QVBoxLayout(extract_tab)
        extract_layout.setSpacing(12)
        extract_layout.setContentsMargins(8, 8, 8, 8)
        
        extract_group = QGroupBox("Extraction Settings")
        extract_group_layout = QVBoxLayout(extract_group)
        
        extract_color_row = QHBoxLayout()
        extract_color_row.addWidget(QLabel("Extract Color:"))
        
        self.btn_pick_color = QToolButton()
        self.btn_pick_color.setText("🖊️")
        self.btn_pick_color.setCheckable(True)
        self.btn_pick_color.setToolTip("Pick color from map")
        self.btn_pick_color.clicked.connect(self._on_pick_color_clicked)
        extract_color_row.addWidget(self.btn_pick_color)
        
        self.color_extract = QgsColorButton()
        self.color_extract.setColor(QColor("#00FF00"))
        extract_color_row.addWidget(self.color_extract)
        extract_color_row.addStretch()
        extract_group_layout.addLayout(extract_color_row)
        
        tol_row = QHBoxLayout()
        tol_row.addWidget(QLabel("Tolerance:"))
        self.slider_color_tolerance = QSlider(Qt.Horizontal)
        self.slider_color_tolerance.setRange(1, 100)
        self.slider_color_tolerance.setValue(30)
        self.slider_color_tolerance.valueChanged.connect(self._on_tolerance_changed)
        tol_row.addWidget(self.slider_color_tolerance)
        self.label_tolerance = QLabel("30%")
        tol_row.addWidget(self.label_tolerance)
        extract_group_layout.addLayout(tol_row)
        
        layer_row = QHBoxLayout()
        layer_row.addWidget(QLabel("Layer:"))
        self.combo_similarity_layer = QComboBox()
        layer_row.addWidget(self.combo_similarity_layer)
        self.btn_refresh_layers = QPushButton("↻")
        self.btn_refresh_layers.setMaximumWidth(30)
        self.btn_refresh_layers.clicked.connect(self._refresh_similarity_layers)
        layer_row.addWidget(self.btn_refresh_layers)
        extract_group_layout.addLayout(layer_row)
        
        extract_layout.addWidget(extract_group)
        
        self.btn_extract = QPushButton("Extract Polygons")
        self.btn_extract.setStyleSheet(self.STYLE_ACTION_PRIMARY)
        self.btn_extract.setMinimumHeight(40)
        self.btn_extract.clicked.connect(self._on_extract_clicked)
        extract_layout.addWidget(self.btn_extract)
        extract_layout.addStretch()
        
        # Status
        self.label_status = QLabel("Status: Ready")
        status_font = QFont()
        status_font.setItalic(True)
        self.label_status.setFont(status_font)
        main_layout.addWidget(self.label_status)
        
        self.color_picker_tool = ColorPickerTool(self.canvas)
        self.color_picker_tool.color_picked.connect(self._on_color_picked_from_map)
    
    def _on_add_basemap_clicked(self):
        """Add Google Satellite basemap."""
        try:
            basemaps = [
                {'name': 'Google Satellite', 'url': 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', 'zmax': 20},
                {'name': 'ESRI World Imagery', 'url': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', 'zmax': 19}
            ]
            
            for basemap_info in basemaps:
                url_encoded = basemap_info['url'].replace('&', '%26')
                uri = f"type=xyz&url={url_encoded}&zmax={basemap_info['zmax']}&zmin=0"
                layer = QgsRasterLayer(uri, basemap_info['name'], "wms")
                
                if layer.isValid():
                    QgsProject.instance().addMapLayer(layer)
                    self.canvas.refresh()
                    self._set_status(f"Added {basemap_info['name']}")
                    return
            
            self.iface.messageBar().pushWarning("AlphaEarth", "Could not load basemap.")
        except Exception as e:
            self.iface.messageBar().pushCritical("AlphaEarth", f"Basemap error: {str(e)}")
    
    def _create_preview_layer(self, geom_type, geom_data, name):
        """Create preview layer for geometry."""
        if geom_type == 'point':
            layer = QgsVectorLayer("Point?crs=EPSG:4326", f"[Preview] {name}", "memory")
            feature = QgsFeature()
            feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(geom_data['lon'], geom_data['lat'])))
            symbol = QgsMarkerSymbol.createSimple({
                'name': 'circle', 'color': self.PREVIEW_COLOR_POINT,
                'size': '4', 'outline_color': '#1976D2', 'outline_width': '0.5'
            })
        elif geom_type == 'bbox':
            layer = QgsVectorLayer("Polygon?crs=EPSG:4326", f"[Preview] {name}", "memory")
            feature = QgsFeature()
            points = [
                QgsPointXY(geom_data['min_lon'], geom_data['min_lat']),
                QgsPointXY(geom_data['max_lon'], geom_data['min_lat']),
                QgsPointXY(geom_data['max_lon'], geom_data['max_lat']),
                QgsPointXY(geom_data['min_lon'], geom_data['max_lat']),
            ]
            feature.setGeometry(QgsGeometry.fromPolygonXY([points]))
            symbol = QgsFillSymbol.createSimple({
                'color': '255,112,67,50', 'outline_color': self.PREVIEW_COLOR_BBOX, 'outline_width': '1.5'
            })
        elif geom_type == 'polygon':
            layer = QgsVectorLayer("Polygon?crs=EPSG:4326", f"[Preview] {name}", "memory")
            feature = QgsFeature()
            points = [QgsPointXY(lon, lat) for lon, lat in geom_data['coords']]
            feature.setGeometry(QgsGeometry.fromPolygonXY([points]))
            symbol = QgsFillSymbol.createSimple({
                'color': '129,199,132,50', 'outline_color': self.PREVIEW_COLOR_POLYGON, 'outline_width': '1.5'
            })
        else:
            return None
        
        layer.dataProvider().addFeature(feature)
        layer.setRenderer(QgsSingleSymbolRenderer(symbol))
        layer.triggerRepaint()
        
        QgsProject.instance().addMapLayer(layer)
        self.preview_layers[layer.id()] = layer
        return layer.id()
    
    def _remove_preview_layer(self, layer_id):
        """Remove preview layer from map."""
        if layer_id and layer_id in self.preview_layers:
            try:
                QgsProject.instance().removeMapLayer(layer_id)
                self.canvas.refresh()
            except:
                pass
            if layer_id in self.preview_layers:
                del self.preview_layers[layer_id]
    
    def _on_layer_removed_from_qgis(self, layer_id):
        """Sync when layer is removed from QGIS."""
        for i in range(self.list_geometries.count() - 1, -1, -1):
            item = self.list_geometries.item(i)
            if isinstance(item, GeometryItem) and item.layer_id == layer_id:
                self.list_geometries.takeItem(i)
                if layer_id in self.preview_layers:
                    del self.preview_layers[layer_id]
                break
        
        if self.list_geometries.count() == 0:
            self.btn_run.setEnabled(False)
    
    def _deactivate_tool(self):
        """Deactivate all map tools."""
        if self.canvas.mapTool() in [self.point_tool, self.bbox_tool, self.polygon_tool, getattr(self, 'color_picker_tool', None)]:
            self.canvas.unsetMapTool(self.canvas.mapTool())
        
        self.current_tool = None
        if self.point_tool:
            self.point_tool.deactivate()
        if self.bbox_tool:
            self.bbox_tool.deactivate()
        if self.polygon_tool:
            self.polygon_tool.deactivate()
        if hasattr(self, 'color_picker_tool') and self.color_picker_tool:
            self.color_picker_tool.deactivate()
        
        self._set_status("Ready")
    
    def _on_tool_clicked(self, tool_type):
        """Activate selected geometry tool."""
        buttons = {'point': self.btn_point, 'bbox': self.btn_bbox, 'polygon': self.btn_polygon}
        clicked_btn = buttons[tool_type]
        
        for t, btn in buttons.items():
            if t != tool_type:
                btn.setChecked(False)
                btn.setStyleSheet(self.STYLE_TOOL_NORMAL)
        
        if hasattr(self, 'btn_pick_color') and self.btn_pick_color:
            try:
                self.btn_pick_color.setChecked(False)
            except RuntimeError:
                self.btn_pick_color = None
        
        if clicked_btn.isChecked():
            clicked_btn.setStyleSheet(self.STYLE_TOOL_ACTIVE)
            self._activate_tool(tool_type)
        else:
            clicked_btn.setStyleSheet(self.STYLE_TOOL_NORMAL)
            self._deactivate_tool()
            
    def _activate_tool(self, tool_type):
        """Activate specific map tool."""
        self._deactivate_tool()
        self.current_tool = tool_type
        
        if tool_type == 'point':
            self.point_tool = PointPickerTool(self.canvas)
            self.point_tool.point_selected.connect(self._on_point_added)
            self.canvas.setMapTool(self.point_tool)
            self._set_status("Click on the map to add a point")
        elif tool_type == 'bbox':
            self.bbox_tool = BBoxPickerTool(self.canvas)
            self.bbox_tool.bbox_selected.connect(self._on_bbox_added)
            self.canvas.setMapTool(self.bbox_tool)
            self._set_status("Draw a bounding box on the map")
        elif tool_type == 'polygon':
            self.polygon_tool = PolygonPickerTool(self.canvas)
            self.polygon_tool.polygon_selected.connect(self._on_polygon_added)
            self.canvas.setMapTool(self.polygon_tool)
            self._set_status("Click vertices, right-click to finish")

    def _on_pick_color_clicked(self):
        """Activate color picker tool."""
        for btn in [self.btn_point, self.btn_bbox, self.btn_polygon]:
            btn.setChecked(False)
            btn.setStyleSheet(self.STYLE_TOOL_NORMAL)
            
        if self.btn_pick_color.isChecked():
            self._deactivate_tool()
            self.canvas.setMapTool(self.color_picker_tool)
            self._set_status("Click on map to pick a color")
        else:
            self._deactivate_tool()
    
    def _on_color_picked_from_map(self, color):
        """Handle color picked signal."""
        self.color_extract.setColor(color)
        self.btn_pick_color.setChecked(False)
        self._deactivate_tool()
        self._set_status(f"Picked color: {color.name()}")
        self.iface.messageBar().pushInfo("AlphaEarth", f"Color picked: {color.name()}")
    
    def _get_next_name(self, geom_type):
        """Get next available name for geometry type."""
        self.geometry_counter[geom_type] += 1
        type_names = {'point': 'Point', 'bbox': 'BBox', 'polygon': 'Polygon'}
        return f"{type_names[geom_type]} {self.geometry_counter[geom_type]}"
    
    def _on_point_added(self, lon, lat):
        name = self._get_next_name('point')
        data = {'lon': lon, 'lat': lat}
        layer_id = self._create_preview_layer('point', data, name)
        item = GeometryItem('point', data, name, layer_id)
        self.list_geometries.addItem(item)
        self.btn_run.setEnabled(True)
        self._set_status(f"Added: {name} ({lon:.4f}, {lat:.4f})")
    
    def _on_bbox_added(self, min_lon, min_lat, max_lon, max_lat):
        name = self._get_next_name('bbox')
        data = {'min_lon': min_lon, 'min_lat': min_lat, 'max_lon': max_lon, 'max_lat': max_lat}
        layer_id = self._create_preview_layer('bbox', data, name)
        item = GeometryItem('bbox', data, name, layer_id)
        self.list_geometries.addItem(item)
        self.btn_run.setEnabled(True)
        self._set_status(f"Added: {name}")
    
    def _on_polygon_added(self, coords):
        name = self._get_next_name('polygon')
        data = {'coords': coords}
        layer_id = self._create_preview_layer('polygon', data, name)
        item = GeometryItem('polygon', data, name, layer_id)
        self.list_geometries.addItem(item)
        self.btn_run.setEnabled(True)
        self._set_status(f"Added: {name} ({len(coords)} vertices)")
    
    def _on_geometry_renamed(self, item):
        if isinstance(item, GeometryItem) and item.layer_id:
            layer = QgsProject.instance().mapLayer(item.layer_id)
            if layer:
                layer.setName(f"[Preview] {item.geom_name}")
    
    def _on_clear_clicked(self):
        """Clear all geometries and preview layers."""
        layer_ids_to_remove = []
        for i in range(self.list_geometries.count()):
            item = self.list_geometries.item(i)
            if isinstance(item, GeometryItem) and item.layer_id:
                layer_ids_to_remove.append(item.layer_id)
        
        self.list_geometries.clear()
        
        for layer_id in layer_ids_to_remove:
            self._remove_preview_layer(layer_id)
        
        self.canvas.refresh()
        self.geometry_counter = {'point': 0, 'bbox': 0, 'polygon': 0}
        self.btn_run.setEnabled(False)
        self._set_status("Cleared all geometries")
    
    def _on_undo_clicked(self):
        count = self.list_geometries.count()
        if count > 0:
            item = self.list_geometries.takeItem(count - 1)
            if isinstance(item, GeometryItem):
                self._remove_preview_layer(item.layer_id)
            self._set_status(f"Removed: {item.geom_name}")
            if self.list_geometries.count() == 0:
                self.btn_run.setEnabled(False)
    
    def _on_remove_clicked(self):
        for item in self.list_geometries.selectedItems():
            if isinstance(item, GeometryItem):
                self._remove_preview_layer(item.layer_id)
            self.list_geometries.takeItem(self.list_geometries.row(item))
        if self.list_geometries.count() == 0:
            self.btn_run.setEnabled(False)
    
    def _on_run_clicked(self):
        """Run similarity search for all geometries."""
        if self.list_geometries.count() == 0:
            self.iface.messageBar().pushWarning("AlphaEarth", "Please add at least one geometry.")
            return
        
        buffer_km = self.spin_buffer.value()
        max_threshold = self.spin_threshold.value()
        resolution = self.spin_resolution.value()
        year_start = self.spin_year.value()
        year_end = year_start
        year_label = str(year_start)
        
        color_palette = [
            self.color_similar.color().name(),
            self.color_neutral.color().name(),
            self.color_different.color().name()
        ]
        
        self._set_status("Running search...")
        self.btn_run.setEnabled(False)
        
        items_to_process = []
        for i in range(self.list_geometries.count()):
            item = self.list_geometries.item(i)
            if isinstance(item, GeometryItem):
                items_to_process.append({
                    'geom_type': item.geom_type,
                    'geom_data': item.geom_data,
                    'geom_name': item.geom_name,
                    'layer_id': item.layer_id
                })
        
        try:
            for item_data in items_to_process:
                self._set_status(f"Processing: {item_data['geom_name']} ({year_label})...")
                
                result = self.gee_search.run_similarity_search_geometry(
                    geom_type=item_data['geom_type'],
                    geom_data=item_data['geom_data'],
                    buffer_km=buffer_km,
                    year_start=year_start,
                    year_end=year_end,
                    max_threshold=max_threshold
                )
                
                self._add_results_to_map(result, item_data['geom_name'], item_data['layer_id'], year_label, resolution, color_palette)
            
            self.btn_run.setEnabled(True)
            self._set_status(f"Search completed ({len(items_to_process)} geometries)")
            
        except Exception as e:
            self.iface.messageBar().pushCritical("AlphaEarth", f"Error: {str(e)}")
            self._set_status(f"Error: {str(e)}")
            self.btn_run.setEnabled(True)
    
    def _add_results_to_map(self, result, geom_name, preview_layer_id, year, resolution=30, color_palette=None):
        """Add search results to QGIS map."""
        try:
            from ee_plugin import Map
            import ee
            
            Map.centerObject(result['search_area'], 12)
            
            Map.addLayer(result['search_area'], {'color': 'red'}, f"[{geom_name}] Search Zone", True, 0.3)
            Map.addLayer(result['reference_geom'], {'color': '#7a9bb8'}, f"[{geom_name}] Reference", True, 1.0)
            
            optimized_similarity = result['similarity_image'].reproject(crs='EPSG:4326', scale=resolution)
            
            vis_params = result['vis_params'].copy()
            if color_palette:
                vis_params['palette'] = color_palette
            
            Map.addLayer(optimized_similarity, vis_params, f"[{geom_name}] Similarity ({year})")
            
            if preview_layer_id:
                try:
                    QgsProject.instance().removeMapLayer(preview_layer_id)
                except:
                    pass
            
        except ImportError:
            raise RuntimeError(
                "Google Earth Engine plugin is required. "
                "Please install from QGIS Plugin Manager and connect your Google Cloud Project."
            )
    
    def _set_status(self, message):
        self.label_status.setText(f"Status: {message}")
    
    def _on_toggle_similarity_clicked(self):
        """Toggle visibility of Zone and Reference layers."""
        show_only_similarity = self.btn_toggle_similarity.isChecked()
        
        for layer in QgsProject.instance().mapLayers().values():
            name = layer.name()
            if "] Search Zone" in name or "] Reference" in name:
                root = QgsProject.instance().layerTreeRoot()
                layer_node = root.findLayer(layer.id())
                if layer_node:
                    layer_node.setItemVisibilityChecked(not show_only_similarity)
        
        if show_only_similarity:
            self.btn_toggle_similarity.setText("Show All Layers")
            self._set_status("Showing Similarity layers only")
        else:
            self.btn_toggle_similarity.setText("Show Similarity Only")
            self._set_status("Showing all layers")
        
        self.canvas.refresh()
    
    def _on_tolerance_changed(self, value):
        self.label_tolerance.setText(f"{value}%")
    
    def _refresh_similarity_layers(self):
        self.combo_similarity_layer.clear()
        for layer in QgsProject.instance().mapLayers().values():
            if "] Similarity" in layer.name():
                self.combo_similarity_layer.addItem(layer.name(), layer.id())
        
        if self.combo_similarity_layer.count() == 0:
            self.combo_similarity_layer.addItem("No similarity layers found")
    
    def _on_extract_clicked(self):
        """Extract polygons from similarity layer based on color matching."""
        try:
            import processing
            from qgis.core import QgsProcessingFeedback
            import tempfile
            import os
            
            layer_id = self.combo_similarity_layer.currentData()
            if not layer_id:
                self._refresh_similarity_layers()
                if self.combo_similarity_layer.count() == 0 or "No similarity" in self.combo_similarity_layer.currentText():
                    self.iface.messageBar().pushWarning("AlphaEarth", "No similarity layers found. Run a search first.")
                    return
                layer_id = self.combo_similarity_layer.currentData()
            
            layer = QgsProject.instance().mapLayer(layer_id)
            if not layer or not layer.isValid():
                self.iface.messageBar().pushWarning("AlphaEarth", "Selected layer is not valid.")
                return
            
            target_color = self.color_extract.color()
            self._set_status("Extracting polygons from color...")
            
            canvas = self.iface.mapCanvas()
            extent = canvas.extent()
            temp_dir = tempfile.gettempdir()
            
            from qgis.core import QgsMapRendererParallelJob
            from qgis.PyQt.QtGui import QImage
            from qgis.PyQt.QtCore import QSize
            
            settings = canvas.mapSettings()
            settings.setLayers([layer])
            settings.setExtent(extent)
            
            canvas_size = self.iface.mapCanvas().size()
            width = canvas_size.width()
            height = canvas_size.height()
            
            max_dim = 2000
            if width > max_dim or height > max_dim:
                scale = min(max_dim/width, max_dim/height)
                width = int(width * scale)
                height = int(height * scale)
            
            settings.setBackgroundColor(QColor(0, 0, 0, 0))
            settings.setOutputSize(QSize(width, height))
            settings.setExtent(extent)
            
            job = QgsMapRendererParallelJob(settings)
            job.start()
            job.waitForFinished()
            
            image = job.renderedImage()
            r_target, g_target, b_target = target_color.red(), target_color.green(), target_color.blue()
            
            self._set_status("Vectorizing...")
            
            from osgeo import gdal, osr
            import numpy as np
            
            driver = gdal.GetDriverByName('GTiff')
            out_raster_path = os.path.join(temp_dir, "alpha_earth_mask.tif")
            out_ds = driver.Create(out_raster_path, width, height, 1, gdal.GDT_Byte)
            
            pixel_width = extent.width() / width
            pixel_height = extent.height() / height
            geo_transform = [extent.xMinimum(), pixel_width, 0, extent.yMaximum(), 0, -pixel_height]
            out_ds.SetGeoTransform(geo_transform)
            
            srs = osr.SpatialReference()
            srs.ImportFromWkt(settings.destinationCrs().toWkt())
            out_ds.SetProjection(srs.ExportToWkt())
            
            raster_data = np.zeros((height, width), dtype=np.uint8)
            
            slider_val = self.slider_color_tolerance.value()
            threshold_dist = (slider_val / 100.0) * 200.0 + 10.0
            threshold_sq = threshold_dist ** 2
            
            matched_pixels = 0
            for x in range(width):
                for y in range(height):
                    pixel = image.pixel(x, y)
                    
                    if (pixel >> 24) & 0xFF == 0:
                        continue
                    
                    r = (pixel >> 16) & 0xFF
                    g = (pixel >> 8) & 0xFF
                    b = pixel & 0xFF
                    
                    dist_sq = (r - r_target)**2 + (g - g_target)**2 + (b - b_target)**2
                    
                    if dist_sq <= threshold_sq:
                        raster_data[y, x] = 1
                        matched_pixels += 1
            
            out_band = out_ds.GetRasterBand(1)
            out_band.WriteArray(raster_data)
            out_band.FlushCache()
            out_ds = None
            
            output_vector = os.path.join(temp_dir, "alpha_earth_polygons.gpkg")
            
            params = {
                'INPUT': out_raster_path, 'BAND': 1, 'FIELD': 'value',
                'EIGHT_CONNECTEDNESS': False, 'EXTRA': '', 'OUTPUT': output_vector
            }
            
            result = processing.run("gdal:polygonize", params)
            
            if result and 'OUTPUT' in result:
                vector_path = result['OUTPUT']
                vlayer = QgsVectorLayer(vector_path, f"Extracted [{matched_pixels} px]", "ogr")
                
                if vlayer.isValid():
                    vlayer.setSubsetString("value = 1")
                    symbol = QgsFillSymbol.createSimple({
                        'color': self.color_extract.color().name(),
                        'outline_style': 'no', 'opacity': '0.7'
                    })
                    vlayer.renderer().setSymbol(symbol)
                    
                    QgsProject.instance().addMapLayer(vlayer)
                    self._set_status(f"Created polygons from {matched_pixels} pixels")
                    self.iface.messageBar().pushSuccess("AlphaEarth", "Extraction complete!")
                else:
                    self._set_status("Error loading vector result")
            else:
                self._set_status("Polygonize failed")
                
        except Exception as e:
            self.iface.messageBar().pushCritical("AlphaEarth", f"Error extracting polygons: {str(e)}")
            self._set_status(f"Error: {str(e)}")
            import traceback
            QgsMessageLog.logMessage(traceback.format_exc(), "AlphaEarth", Qgis.Critical)
    
    def closeEvent(self, event):
        self._deactivate_tool()
        for btn in [self.btn_point, self.btn_bbox, self.btn_polygon]:
            btn.setChecked(False)
            btn.setStyleSheet(self.STYLE_TOOL_NORMAL)
        super().closeEvent(event)
