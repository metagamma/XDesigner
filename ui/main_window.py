from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                              QToolBar, QMessageBox, QDockWidget, QDialog, QListWidget, QListWidgetItem, QDialogButtonBox)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QIcon, QAction

from ui.widgets.image_viewer import ImageViewer
from ui.widgets.fields_tree import FieldsTree
from ui.widgets.field_dialog import FieldDialog
from ui.widgets.template_dialog import TemplateDialog
from database.repository import Template, Field
from utils.image_utils import get_image_dpi, pixels_to_inches
from core.constants import RegionType

class MainWindow(QMainWindow):
    def __init__(self, db_service, config, parent=None):
        super().__init__(parent)
        self.db_service = db_service
        self.config = config
        self.current_template = None
        self.current_page = 0
        self.dpi = (300, 300)  # Default DPI
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Template Editor")
        self.resize(1200, 800)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create toolbar
        self.create_toolbar()

        # Create image viewer
        self.image_viewer = ImageViewer()
        self.image_viewer.rectAdded.connect(self.on_rect_added)
        self.image_viewer.rectSelected.connect(self.on_rect_selected)
        self.image_viewer.rectMoved.connect(self.on_rect_moved)
        layout.addWidget(self.image_viewer)

        # Create fields tree dock widget
        fields_dock = QDockWidget("Fields", self)
        fields_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.fields_tree = FieldsTree()
        self.fields_tree.fieldSelected.connect(self.on_field_selected)
        fields_dock.setWidget(self.fields_tree)
        self.addDockWidget(Qt.RightDockWidgetArea, fields_dock)

    def create_toolbar(self):
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        # Template actions
        new_template_action = QAction("New Template", self)
        new_template_action.triggered.connect(self.new_template)
        toolbar.addAction(new_template_action)

        open_template_action = QAction("Open Template", self)
        open_template_action.triggered.connect(self.open_template)
        toolbar.addAction(open_template_action)

        save_template_action = QAction("Save Template", self)
        save_template_action.triggered.connect(self.save_template)
        toolbar.addAction(save_template_action)

        delete_template_action = QAction("Delete Template", self)
        delete_template_action.triggered.connect(self.delete_template)
        toolbar.addAction(delete_template_action)

        toolbar.addSeparator()

        # Drawing actions
        self.draw_action = QAction("Draw Field", self)
        self.draw_action.setCheckable(True)
        self.draw_action.triggered.connect(self.toggle_drawing)
        toolbar.addAction(self.draw_action)

        delete_field_action = QAction("Delete Field", self)
        delete_field_action.triggered.connect(self.delete_selected_field)
        toolbar.addAction(delete_field_action)

        toolbar.addSeparator()

        # Page navigation
        self.prev_page_action = QAction("Previous Page", self)
        self.prev_page_action.triggered.connect(self.previous_page)
        toolbar.addAction(self.prev_page_action)

        self.next_page_action = QAction("Next Page", self)
        self.next_page_action.triggered.connect(self.next_page)
        toolbar.addAction(self.next_page_action)

    def new_template(self):
        dialog = TemplateDialog(self)
        if dialog.exec():
            data = dialog.get_template_data()
            try:
                template = Template(
                    ID=0,
                    Nombre=data['name'],
                    Xmp='',
                    Imagen=data['image_path'],
                    ID_Grado=1  # Default value
                )
                template_id = self.db_service.create_template(template)
                template.ID = template_id
                self.load_template(template)
                QMessageBox.information(self, "Success", "Template created successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create template: {str(e)}")

    def open_template(self):
        try:
            templates = self.db_service.get_templates()
            if not templates:
                QMessageBox.information(self, "No Templates", "No templates found")
                return

            dialog = QDialog(self)
            dialog.setWindowTitle("Select Template")
            layout = QVBoxLayout(dialog)
            
            list_widget = QListWidget()
            for template in templates:
                item = QListWidgetItem(template.Nombre)
                item.setData(Qt.UserRole, template)
                list_widget.addItem(item)
            
            layout.addWidget(list_widget)
            
            buttons = QDialogButtonBox(
                QDialogButtonBox.Ok | QDialogButtonBox.Cancel
            )
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            
            if dialog.exec() == QDialog.Accepted:
                selected_items = list_widget.selectedItems()
                if selected_items:
                    template = selected_items[0].data(Qt.UserRole)
                    self.load_template(template)
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load templates: {str(e)}")

    def load_template(self, template):
        try:
            self.current_template = template
            self.current_page = 0
            self.dpi = get_image_dpi(template.Imagen)
            
            # Load image
            self.image_viewer.load_image(template.Imagen, self.current_page)
            
            # Load fields
            self.load_fields()
            
            # Update window title
            self.setWindowTitle(f"Template Editor - {template.Nombre}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load template: {str(e)}")

    def save_template(self):
        if not self.current_template:
            return
            
        try:
            if self.db_service.update_template(self.current_template):
                QMessageBox.information(self, "Success", "Template saved successfully")
            else:
                QMessageBox.warning(self, "Warning", "No changes to save")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save template: {str(e)}")

    def delete_template(self):
        if not self.current_template:
            return
            
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete template '{self.current_template.Nombre}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if self.db_service.delete_template(self.current_template.ID):
                    self.current_template = None
                    self.image_viewer.scene.clear()
                    self.fields_tree.clear()
                    self.setWindowTitle("Template Editor")
                    QMessageBox.information(self, "Success", "Template deleted successfully")
                else:
                    QMessageBox.warning(self, "Warning", "Failed to delete template")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete template: {str(e)}")

    def toggle_drawing(self, enabled):
        self.image_viewer.set_drawing_enabled(enabled)

    def delete_selected_field(self):
        selected_items = self.fields_tree.selectedItems()
        if not selected_items:
            return
            
        field_id = selected_items[0].data(0, Qt.UserRole)
        if field_id is None:
            return
            
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this field?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if self.db_service.delete_field(field_id):
                    self.image_viewer.remove_rectangle(field_id)
                    self.load_fields()  # Refresh fields tree
                    QMessageBox.information(self, "Success", "Field deleted successfully")
                else:
                    QMessageBox.warning(self, "Warning", "Failed to delete field")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete field: {str(e)}")

    def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.image_viewer.load_image(self.current_template.Imagen, self.current_page)
            self.load_fields()

    def next_page(self):
        if self.current_template:
            try:
                self.current_page += 1
                self.image_viewer.load_image(self.current_template.Imagen, self.current_page)
                self.load_fields()
            except Exception:
                self.current_page -= 1
                QMessageBox.warning(self, "Warning", "No more pages")

    def on_rect_added(self, rect: QRectF, rect_id: int):
        if not self.current_template:
            return
            
        dialog = FieldDialog(rect, self)
        if dialog.exec():
            field_data = dialog.get_field_data()
            
            # Convert coordinates to inches
            x = pixels_to_inches(rect.x() * self.image_viewer.scene.width(), self.dpi[0])
            y = pixels_to_inches(rect.y() * self.image_viewer.scene.height(), self.dpi[1])
            width = pixels_to_inches(rect.width() * self.image_viewer.scene.width(), self.dpi[0])
            height = pixels_to_inches(rect.height() * self.image_viewer.scene.height(), self.dpi[1])
            
            try:
                field = Field(
                    ID=0,
                    ID_Template=self.current_template.ID,
                    Nombre_Campo=field_data['name'],
                    Tipo_Campo=field_data['type'],
                    Cord_x=x,
                    Cord_y=y,
                    Cord_width=width,
                    Cord_height=height,
                    NroPagina=self.current_page,
                    IdRectangulo=rect_id
                )
                
                field_id = self.db_service.create_field(field)
                self.load_fields()  # Refresh fields tree
                
            except Exception as e:
                self.image_viewer.remove_rectangle(rect_id)
                QMessageBox.critical(self, "Error", f"Failed to create field: {str(e)}")

    def on_rect_selected(self, rect_id: int):
        # Find the corresponding field in the tree and select it
        root = self.fields_tree.invisibleRootItem()
        for i in range(root.childCount()):
            page_item = root.child(i)
            for j in range(page_item.childCount()):
                field_item = page_item.child(j)
                if field_item.data(0, Qt.UserRole) == rect_id:
                    self.fields_tree.setCurrentItem(field_item)
                    break

    def on_rect_moved(self, rect: QRectF, rect_id: int):
        if not self.current_template:
            return
            
        try:
            fields = self.db_service.get_template_fields(self.current_template.ID)
            field = next((f for f in fields if f.IdRectangulo == rect_id), None)
            
            if field:
                # Update coordinates
                x = pixels_to_inches(rect.x() * self.image_viewer.scene.width(), self.dpi[0])
                y = pixels_to_inches(rect.y() * self.image_viewer.scene.height(), self.dpi[1])
                width = pixels_to_inches(rect.width() * self.image_viewer.scene.width(), self.dpi[0])
                height = pixels_to_inches(rect.height() * self.image_viewer.scene.height(), self.dpi[1])
                
                field.Cord_x = x
                field.Cord_y = y
                field.Cord_width = width
                field.Cord_height = height
                
                self.db_service.update_field(field)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update field position: {str(e)}")

    def on_field_selected(self, field_id: int):
        # Highlight the corresponding rectangle in the image viewer
        if field_id in self.image_viewer.rectangles:
            rect = self.image_viewer.rectangles[field_id]
            rect.setSelected(True)

    def load_fields(self):
        if not self.current_template:
            return
            
        try:
            fields = self.db_service.get_template_fields(self.current_template.ID)
            
            # Clear existing rectangles
            self.image_viewer.scene.clear()
            self.image_viewer.rectangles.clear()
            
            # Reload current image
            self.image_viewer.load_image(self.current_template.Imagen, self.current_page)
            
            # Add rectangles for fields on current page
            for field in fields:
                if field.NroPagina == self.current_page:
                    # Convert inches to normalized coordinates
                    x = field.Cord_x * self.dpi[0] / self.image_viewer.scene.width()
                    y = field.Cord_y * self.dpi[1] / self.image_viewer.scene.height()
                    width = field.Cord_width * self.dpi[0] / self.image_viewer.scene.width()
                    height = field.Cord_height * self.dpi[1] / self.image_viewer.scene.height()
                    
                    rect = QRectF(x, y, width, height)
                    self.image_viewer.add_rectangle(rect, field.IdRectangulo)
            
            # Update fields tree
            self.fields_tree.update_fields(fields)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load fields: {str(e)}")