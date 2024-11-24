from PySide6.QtWidgets import QWidget, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsItem
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import QImage, QPixmap, QPen, QColor, QPainter
from PIL import Image
import io

class GraphicsRectItem(QGraphicsRectItem):
    def __init__(self, x, y, w, h, id_rect, parent=None):
        super().__init__(x, y, w, h, parent)
        self.id = id_rect
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setPen(QPen(QColor(255, 0, 0), 2))

class ImageViewer(QGraphicsView):
    rectAdded = Signal(QRectF, int)  # Emits when a new rectangle is added
    rectSelected = Signal(int)  # Emits the ID of the selected rectangle
    rectMoved = Signal(QRectF, int)  # Emits when a rectangle is moved

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

        self.drawing = False
        self.current_rect = None
        self.start_pos = None
        self.current_image = None
        self.rect_counter = 0
        self.rectangles = {}
        self.drawing_enabled = False

    def set_drawing_enabled(self, enabled: bool):
        self.drawing_enabled = enabled
        self.setDragMode(
            QGraphicsView.NoDrag if enabled else QGraphicsView.ScrollHandDrag
        )

    def load_image(self, image_data, page_number):
        self.scene.clear()
        self.rectangles.clear()
        
        if isinstance(image_data, str):  # If image_data is a file path
            image = Image.open(image_data)
            if page_number > 0:
                image.seek(page_number)
            
            # Convert PIL image to QImage
            with io.BytesIO() as bio:
                image.save(bio, format='PNG')
                image_data = bio.getvalue()
                qimage = QImage.fromData(image_data)
        else:
            qimage = QImage.fromData(image_data)
            self.current_image = qimage
        pixmap = QPixmap.fromImage(qimage)
        self.scene.addPixmap(pixmap)
        self.scene.setSceneRect(QRectF(pixmap.rect()))
        self.fit_in_view()

    def fit_in_view(self):
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.current_image:
            self.fit_in_view()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing_enabled:
            self.drawing = True
            scene_pos = self.mapToScene(event.pos())
            self.start_pos = scene_pos
            self.current_rect = None
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.drawing and self.start_pos:
            if self.current_rect:
                self.scene.removeItem(self.current_rect)
            
            scene_pos = self.mapToScene(event.pos())
            rect = QRectF(
                min(self.start_pos.x(), scene_pos.x()),
                min(self.start_pos.y(), scene_pos.y()),
                abs(scene_pos.x() - self.start_pos.x()),
                abs(scene_pos.y() - self.start_pos.y())
            )
            
            self.current_rect = GraphicsRectItem(
                rect.x(), rect.y(), rect.width(), rect.height(), 
                self.rect_counter
            )
            self.scene.addItem(self.current_rect)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False
            if self.current_rect and self.current_rect.rect().width() > 10 and self.current_rect.rect().height() > 10:
                self.rectangles[self.rect_counter] = self.current_rect
                normalized_rect = self.get_normalized_rect(self.current_rect.rect())
                self.rectAdded.emit(normalized_rect, self.rect_counter)
                self.rect_counter += 1
            elif self.current_rect:
                self.scene.removeItem(self.current_rect)
            self.current_rect = None
        else:
            super().mouseReleaseEvent(event)

    def get_normalized_rect(self, rect):
        scene_rect = self.scene.sceneRect()
        return QRectF(
            rect.x() / scene_rect.width(),
            rect.y() / scene_rect.height(),
            rect.width() / scene_rect.width(),
            rect.height() / scene_rect.height()
        )

    def add_rectangle(self, normalized_rect, rect_id):
        scene_rect = self.scene.sceneRect()
        rect = QRectF(
            normalized_rect.x() * scene_rect.width(),
            normalized_rect.y() * scene_rect.height(),
            normalized_rect.width() * scene_rect.width(),
            normalized_rect.height() * scene_rect.height()
        )
        graphics_rect = GraphicsRectItem(
            rect.x(), rect.y(), rect.width(), rect.height(), rect_id
        )
        self.scene.addItem(graphics_rect)
        self.rectangles[rect_id] = graphics_rect
        return graphics_rect

    def remove_rectangle(self, rect_id):
        if rect_id in self.rectangles:
            self.scene.removeItem(self.rectangles[rect_id])
            del self.rectangles[rect_id]