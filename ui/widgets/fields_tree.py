from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem
from PySide6.QtCore import Qt, Signal

class FieldsTree(QTreeWidget):
    fieldSelected = Signal(int)  # Emits field ID when selected

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.setHeaderLabels(["Fields"])
        self.setColumnCount(1)
        self.setSelectionMode(QTreeWidget.SingleSelection)
        self.itemSelectionChanged.connect(self.on_selection_changed)

    def update_fields(self, fields):
        self.clear()
        pages = {}
        
        for field in fields:
            if field.NroPagina not in pages:
                page_item = QTreeWidgetItem(self)
                page_item.setText(0, f"Page {field.NroPagina + 1}")
                pages[field.NroPagina] = page_item
                
            field_item = QTreeWidgetItem(pages[field.NroPagina])
            field_item.setText(0, field.Nombre_Campo)
            field_item.setData(0, Qt.UserRole, field.ID)
            field_item.setData(0, Qt.UserRole + 1, field.Tipo_Campo)

    def on_selection_changed(self):
        selected_items = self.selectedItems()
        if selected_items:
            item = selected_items[0]
            field_id = item.data(0, Qt.UserRole)
            if field_id is not None:
                self.fieldSelected.emit(field_id)