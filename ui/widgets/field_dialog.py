from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QLineEdit, QComboBox, QPushButton, QFormLayout)
from PySide6.QtCore import Qt
from core.constants import RegionType
from utils.validators import validate_field_name

class FieldDialog(QDialog):
    def __init__(self, coords, parent=None):
        super().__init__(parent)
        self.coords = coords
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Field Properties")
        self.setModal(True)
        
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Field name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter field name")
        self.name_edit.textChanged.connect(self.on_name_changed)
        form_layout.addRow("Field Name:", self.name_edit)

        # Field type
        self.type_combo = QComboBox()
        for region_type in RegionType:
            self.type_combo.addItem(region_type.value)
        form_layout.addRow("Field Type:", self.type_combo)

        # Coordinates display
        coords_layout = QFormLayout()
        self.x_label = QLabel(f"{self.coords.x():.4f}")
        self.y_label = QLabel(f"{self.coords.y():.4f}")
        self.width_label = QLabel(f"{self.coords.width():.4f}")
        self.height_label = QLabel(f"{self.coords.height():.4f}")
        
        coords_layout.addRow("X:", self.x_label)
        coords_layout.addRow("Y:", self.y_label)
        coords_layout.addRow("Width:", self.width_label)
        coords_layout.addRow("Height:", self.height_label)
        
        layout.addLayout(form_layout)
        layout.addLayout(coords_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.ok_button.setEnabled(False)
        self.ok_button.clicked.connect(self.accept)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def on_name_changed(self, text):
        valid, _ = validate_field_name(text.upper())
        self.ok_button.setEnabled(valid)
        if valid:
            self.name_edit.setText(text.upper())

    def get_field_data(self):
        return {
            'name': self.name_edit.text().upper(),
            'type': self.type_combo.currentText(),
            'coords': self.coords
        }