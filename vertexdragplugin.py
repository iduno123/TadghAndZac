# Import necessary QGIS modules
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY
from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.utils import iface

class VertexDragPlugin:

    def __init__(self):
        self.layer = None
        self.rb = None
        self.map_tool = None

    def initGui(self):
        # Create the plugin action
        self.action = QAction("Vertex Drag Plugin", iface.mainWindow())
        self.action.setCheckable(True)
        self.action.triggered.connect(self.toggle_map_tool)

        # Add the plugin action to the toolbar
        iface.addToolBarIcon(self.action)

    def unload(self):
        # Remove the plugin action from the toolbar
        iface.removeToolBarIcon(self.action)

    def toggle_map_tool(self):
        # Toggle the map tool when the plugin action is triggered
        if self.action.isChecked():
            self.start_map_tool()
        else:
            self.stop_map_tool()

    def start_map_tool(self):
        # Start the map tool to enable vertex dragging
        self.layer = iface.activeLayer()

        if self.layer is None or not isinstance(self.layer, QgsVectorLayer):
            QMessageBox.warning(iface.mainWindow(), "Error", "Please select a valid vector layer.")
            self.action.setChecked(False)
            return

        self.map_tool = VertexDragMapTool(self.layer, iface.mapCanvas())
        iface.mapCanvas().setMapTool(self.map_tool)

    def stop_map_tool(self):
        # Stop the map tool
        if self.map_tool:
            self.map_tool.deactivate()
            iface.mapCanvas().unsetMapTool(self.map_tool)
            self.map_tool = None


class VertexDragMapTool(QgsMapTool):
    def __init__(self, layer, canvas):
        QgsMapTool.__init__(self, canvas)
        self.layer = layer
        self.rb = QgsRubberBand(self.canvas(), QgsWkbTypes.LineGeometry)
        self.rb.setColor(QColor(255, 0, 0, 127))
        self.rb.setWidth(2)

    def canvasPressEvent(self, event):
        # Identify the clicked vertex
        point = self.toMapCoordinates(event.pos())
        snapped_vertex = self.layer.snapToVertex(point, QgsPointXY(), 5)
        
        if snapped_vertex:
            self.dragged_vertex = snapped_vertex
            self.original_geometry = QgsGeometry(self.layer.getFeature(snapped_vertex[1]).geometry())
            self.start_point = self.toMapCoordinates(event.pos())
        else:
            self.dragged_vertex = None

    def canvasMoveEvent(self, event):
        # Move the vertex while dragging
        if hasattr(self, 'dragged_vertex') and self.dragged_vertex:
            new_point = self.toMapCoordinates(event.pos())
            displacement = new_point - self.start_point
            modified_geometry = QgsGeometry(self.original_geometry)
            modified_geometry.moveVertex(self.dragged_vertex[2], displacement.x(), displacement.y())
            self.rb.setToGeometry(modified_geometry)

    def canvasReleaseEvent(self, event):
        # Update the feature with the modified geometry
        if hasattr(self, 'dragged_vertex') and self.dragged_vertex:
            new_point = self.toMapCoordinates(event.pos())
            displacement = new_point - self.start_point
            modified_geometry = QgsGeometry(self.original_geometry)
            modified_geometry.moveVertex(self.dragged_vertex[2], displacement.x(), displacement.y())

            feature = QgsFeature()
            feature.setGeometry(modified_geometry)
            feature.setId(self.dragged_vertex[1])
            self.layer.dataProvider().changeGeometryValues({self.dragged_vertex[1]: feature})

            # Clear rubber band
            self.rb.reset()

            del self.dragged_vertex
            del self.original_geometry
            del self.start_point


# Instantiate the plugin
vertex_drag_plugin = VertexDragPlugin()


def classFactory():
    return vertex_drag_plugin
