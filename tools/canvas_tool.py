"""Canvas tools for map interactions - Point, BBox, Polygon, and Color picking."""

from qgis.PyQt.QtCore import pyqtSignal, Qt
from qgis.PyQt.QtGui import QCursor, QColor
from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.core import QgsWkbTypes, QgsPointXY, QgsCoordinateTransform, QgsCoordinateReferenceSystem, QgsProject


class PointPickerTool(QgsMapTool):
    """Map tool for point selection."""
    
    point_selected = pyqtSignal(float, float)
    
    def __init__(self, canvas):
        super().__init__(canvas)
        self.canvas = canvas
        self.setCursor(QCursor(Qt.CrossCursor))
    
    def canvasReleaseEvent(self, event):
        point = self.toMapCoordinates(event.pos())
        point_wgs84 = self._to_wgs84(point)
        self.point_selected.emit(point_wgs84.x(), point_wgs84.y())
    
    def _to_wgs84(self, point):
        crs = self.canvas.mapSettings().destinationCrs()
        if crs.authid() != "EPSG:4326":
            transform = QgsCoordinateTransform(
                crs, QgsCoordinateReferenceSystem("EPSG:4326"), QgsProject.instance()
            )
            return transform.transform(point)
        return point


class BBoxPickerTool(QgsMapTool):
    """Map tool for bounding box drawing."""
    
    bbox_selected = pyqtSignal(float, float, float, float)
    
    def __init__(self, canvas):
        super().__init__(canvas)
        self.canvas = canvas
        self.setCursor(QCursor(Qt.CrossCursor))
        self.start_point = None
        self.rubber_band = None
    
    def canvasPressEvent(self, event):
        self.start_point = self.toMapCoordinates(event.pos())
        self.rubber_band = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self.rubber_band.setColor(QColor(255, 0, 0, 100))
        self.rubber_band.setWidth(2)
    
    def canvasMoveEvent(self, event):
        if self.start_point and self.rubber_band:
            end_point = self.toMapCoordinates(event.pos())
            self._update_rubber_band(self.start_point, end_point)
    
    def canvasReleaseEvent(self, event):
        if self.start_point:
            end_point = self.toMapCoordinates(event.pos())
            start_wgs84 = self._to_wgs84(self.start_point)
            end_wgs84 = self._to_wgs84(end_point)
            
            min_lon = min(start_wgs84.x(), end_wgs84.x())
            max_lon = max(start_wgs84.x(), end_wgs84.x())
            min_lat = min(start_wgs84.y(), end_wgs84.y())
            max_lat = max(start_wgs84.y(), end_wgs84.y())
            
            self.bbox_selected.emit(min_lon, min_lat, max_lon, max_lat)
            
            if self.rubber_band:
                self.canvas.scene().removeItem(self.rubber_band)
                self.rubber_band = None
            self.start_point = None
    
    def _update_rubber_band(self, start, end):
        self.rubber_band.reset(QgsWkbTypes.PolygonGeometry)
        self.rubber_band.addPoint(QgsPointXY(start.x(), start.y()), False)
        self.rubber_band.addPoint(QgsPointXY(end.x(), start.y()), False)
        self.rubber_band.addPoint(QgsPointXY(end.x(), end.y()), False)
        self.rubber_band.addPoint(QgsPointXY(start.x(), end.y()), True)
    
    def _to_wgs84(self, point):
        crs = self.canvas.mapSettings().destinationCrs()
        if crs.authid() != "EPSG:4326":
            transform = QgsCoordinateTransform(
                crs, QgsCoordinateReferenceSystem("EPSG:4326"), QgsProject.instance()
            )
            return transform.transform(point)
        return point
    
    def deactivate(self):
        if self.rubber_band:
            self.canvas.scene().removeItem(self.rubber_band)
            self.rubber_band = None
        super().deactivate()


class PolygonPickerTool(QgsMapTool):
    """Map tool for polygon drawing."""
    
    polygon_selected = pyqtSignal(list)
    
    def __init__(self, canvas):
        super().__init__(canvas)
        self.canvas = canvas
        self.setCursor(QCursor(Qt.CrossCursor))
        self.points = []
        self.rubber_band = None
    
    def canvasPressEvent(self, event):
        if event.button() == Qt.LeftButton:
            point = self.toMapCoordinates(event.pos())
            self.points.append(point)
            
            if not self.rubber_band:
                self.rubber_band = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
                self.rubber_band.setColor(QColor(0, 255, 0, 100))
                self.rubber_band.setWidth(2)
            
            self._update_rubber_band()
            
        elif event.button() == Qt.RightButton:
            if len(self.points) >= 3:
                wgs84_points = [self._to_wgs84(p) for p in self.points]
                coords = [(p.x(), p.y()) for p in wgs84_points]
                self.polygon_selected.emit(coords)
            self._reset()
    
    def canvasMoveEvent(self, event):
        if self.rubber_band and self.points:
            temp_point = self.toMapCoordinates(event.pos())
            self._update_rubber_band(temp_point)
    
    def _update_rubber_band(self, temp_point=None):
        self.rubber_band.reset(QgsWkbTypes.PolygonGeometry)
        for p in self.points:
            self.rubber_band.addPoint(QgsPointXY(p.x(), p.y()), False)
        if temp_point:
            self.rubber_band.addPoint(QgsPointXY(temp_point.x(), temp_point.y()), False)
        if self.points:
            self.rubber_band.addPoint(QgsPointXY(self.points[0].x(), self.points[0].y()), True)
    
    def _to_wgs84(self, point):
        crs = self.canvas.mapSettings().destinationCrs()
        if crs.authid() != "EPSG:4326":
            transform = QgsCoordinateTransform(
                crs, QgsCoordinateReferenceSystem("EPSG:4326"), QgsProject.instance()
            )
            return transform.transform(point)
        return point
    
    def _reset(self):
        self.points = []
        if self.rubber_band:
            self.canvas.scene().removeItem(self.rubber_band)
            self.rubber_band = None
    
    def deactivate(self):
        self._reset()
        super().deactivate()


class ColorPickerTool(QgsMapTool):
    """Map tool for color picking from canvas."""
    
    color_picked = pyqtSignal(QColor)
    
    def __init__(self, canvas):
        super().__init__(canvas)
        self.canvas = canvas
        self.setCursor(QCursor(Qt.CrossCursor))
    
    def canvasReleaseEvent(self, event):
        point = event.pos()
        
        from qgis.PyQt.QtCore import QRect
        from qgis.PyQt.QtWidgets import QApplication
        
        try:
            pixmap = self.canvas.grab(QRect(point.x(), point.y(), 1, 1))
            image = pixmap.toImage()
            
            if image.width() > 0 and image.height() > 0:
                color = image.pixelColor(0, 0)
                self.color_picked.emit(color)
        except Exception:
            try:
                screen = QApplication.screenAt(self.canvas.mapToGlobal(point))
                if screen:
                    pixmap = screen.grabWindow(
                        0, self.canvas.mapToGlobal(point).x(), 
                        self.canvas.mapToGlobal(point).y(), 1, 1
                    )
                    image = pixmap.toImage()
                    color = image.pixelColor(0, 0)
                    self.color_picked.emit(color)
            except:
                pass
