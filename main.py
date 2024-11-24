import sys
import logging
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QMessageBox
from PySide6.QtGui import QGuiApplication, QIcon

from core.config import AppConfig 
from database.service import DatabaseService
from ui.main_window import MainWindow
from utils.logging_utils import setup_logging

class Application:
    def __init__(self):
        self.setup_high_dpi()
        self.setup_application()
        
        self.settings = QSettings('SAFD', 'IMAGING-CAPTURE')
        self.config = AppConfig()
        self.setup_logging()
        self.db_service = None
        self.main_window = None

    @staticmethod
    def setup_high_dpi():
        """Configure HiDPI settings before QApplication creation"""
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        QApplication.setAttribute(Qt.AA_Use96Dpi)

    def setup_application(self):
        """Initialize QApplication with proper settings"""
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.app.setOrganizationName("SAFD")
        self.app.setApplicationName("IMAGING-CAPTURE")
        self.app.setStyle("Fusion")
        self.app.setWindowIcon(QIcon(":/resources/icons/app_icon.png"))

    def setup_logging(self):
        """Initialize logging configuration"""
        log_path = Path(self.config.LOGS_PATH) / "app.log" if hasattr(self.config, 'LOGS_PATH') else Path("logs/app.log")
        setup_logging(
            log_path=log_path,
            level=logging.INFO,
            max_bytes=5_242_880,  # 5MB
            backup_count=5,
            json_format=False
        )
        self.logger = logging.getLogger(__name__)

    def initialize_database(self) -> bool:
        """Initialize database connection"""
        try:
            self.db_service = DatabaseService(self.config)
            self.db_service.initialize()
            return True
        except Exception as e:
            self.logger.error(f"Database initialization error: {e}")
            self.show_error_dialog("Database Error", f"Failed to initialize database: {e}")
            return False

    def initialize_main_window(self) -> bool:
        """Initialize and configure main application window"""
        try:
            self.main_window = MainWindow(
                db_service=self.db_service,
                config=self.config
            )
            
            if geometry := self.settings.value("geometry"):
                self.main_window.restoreGeometry(geometry)
            else:
                self.main_window.showMaximized()
                
            return True
        except Exception as e:
            self.logger.error(f"Main window initialization error: {e}")
            self.show_error_dialog("UI Error", f"Failed to initialize main window: {e}")
            return False

    def show_error_dialog(self, title: str, message: str):
        """Display error message to user"""
        QMessageBox.critical(None, title, f"{message}\n\nThe application will close.")

    def cleanup(self):
        """Perform cleanup operations"""
        try:
            if self.main_window:
                self.settings.setValue("geometry", self.main_window.saveGeometry())
                self.settings.sync()
            
            if self.db_service:
                self.db_service.close()
                
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")

    def run(self) -> int:
        """Main application execution"""
        try:
            if not self.initialize_database() or not self.initialize_main_window():
                return 1
                
            self.main_window.show()
            return_code = self.app.exec()
            self.cleanup()
            return return_code
            
        except Exception as e:
            self.logger.critical(f"Fatal error: {e}", exc_info=True)
            self.show_error_dialog("Fatal Error", str(e))
            return 1

def main():
    try:
        app = Application()
        return app.run()
    except Exception as e:
        logging.critical(f"Unhandled exception: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())