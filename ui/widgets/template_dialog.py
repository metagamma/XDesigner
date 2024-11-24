from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QLineEdit, QPushButton, QFileDialog, QFormLayout)
from PySide6.QtCore import Qt

class TemplateDialog(QDialog):
    def __init__(self, parent=None, template=None):
        super().__init__(parent)
        self.template = template
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Template Properties")
        self.setModal(True)
        
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Template name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter template name")
        if self.template:
            self.name_edit.setText(self.template.Nombre)
        form_layout.addRow("Template Name:", self.name_edit)

        # Image file selection
        self.image_path = QLineEdit()
        self.image_path.setReadOnly(True)
        if self.template:
            self.image_path.setText(self.template.Imagen)
            
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_image)
        
        image_layout = QHBoxLayout()
        image_layout.addWidget(self.image_path)
        image_layout.addWidget(browse_button)
        form_layout.addRow("Image File:", image_layout)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def browse_image(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select Template Image",
            "",
            "Image Files (*.tif *.tiff);;All Files (*)"
        )
        if file_name:
            self.image_path.setText(file_name)

    def get_template_data(self):
        return {
            'name': self.name_edit.text(),
            'image_path': self.image_path.text()
        }