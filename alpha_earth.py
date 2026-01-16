"""Main plugin class for AlphaEarth."""

import os
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction


class AlphaEarth:
    """AlphaEarth plugin main class."""

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu_name = "&AlphaEarth"
        self._similarity_dock = None
        self.toolbar = None

    def initGui(self):
        """Create UI elements."""
        self.toolbar = self.iface.addToolBar("AlphaEarth")
        self.toolbar.setObjectName("AlphaEarthToolbar")
        
        icon_path = os.path.join(self.plugin_dir, "icons", "alpha_earth.svg")
        
        self.action_similarity = self._add_action(
            icon_path=icon_path,
            text="Similarity Search",
            callback=self.toggle_similarity_dock,
            status_tip="Open AlphaEarth Similarity Search Tool",
            checkable=True,
            parent=self.iface.mainWindow(),
        )

    def unload(self):
        """Clean up resources."""
        if self._similarity_dock is not None:
            self.iface.removeDockWidget(self._similarity_dock)
            self._similarity_dock.deleteLater()
            self._similarity_dock = None
        
        for action in self.actions:
            self.iface.removePluginMenu(self.menu_name, action)
            self.iface.removeToolBarIcon(action)
        
        if self.toolbar:
            del self.toolbar

    def _add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        checkable=False,
        parent=None,
    ):
        """Add action to menu and toolbar."""
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        action.setCheckable(checkable)
        
        if status_tip:
            action.setStatusTip(status_tip)
        
        if add_to_toolbar and self.toolbar:
            self.toolbar.addAction(action)
        
        if add_to_menu:
            self.iface.addPluginToMenu(self.menu_name, action)
        
        self.actions.append(action)
        return action

    def toggle_similarity_dock(self):
        """Toggle similarity search dock visibility."""
        if self._similarity_dock is None:
            from .tools.widget_tool import SimilaritySearchWidget
            
            self._similarity_dock = SimilaritySearchWidget(
                iface=self.iface,
                plugin_dir=self.plugin_dir,
                parent=self.iface.mainWindow()
            )
            self._similarity_dock.setObjectName("AlphaEarthSimilarityDock")
            self._similarity_dock.visibilityChanged.connect(self._on_dock_visibility_changed)
            
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self._similarity_dock)
            self._similarity_dock.show()
        else:
            if self._similarity_dock.isVisible():
                self._similarity_dock.hide()
            else:
                self._similarity_dock.show()
                self._similarity_dock.raise_()

    def _on_dock_visibility_changed(self, visible):
        """Sync button state with dock visibility."""
        if self.action_similarity.isChecked() != visible:
            self.action_similarity.setChecked(visible)
