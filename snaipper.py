import sys
import openai
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QInputDialog, QRubberBand, QLabel, QMessageBox,
                             QMenu, QMenuBar, QAction, QStyleFactory)
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5.QtCore import QPoint, QRect, Qt, QSize

import pygetwindow as gw
from PIL import ImageGrab

class SnaipperApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Snaipper - AI-Powered Snipping Tool')
        self.setGeometry(100, 100, 400, 300)

        self.setup_menu()

        self.snip_btn = QPushButton('Snip', self)
        self.snip_btn.move(50, 50)
        self.snip_btn.clicked.connect(self.snip)

        self.send_to_ai_btn = QPushButton('Send to AI', self)
        self.send_to_ai_btn.move(250, 50)
        self.send_to_ai_btn.clicked.connect(self.send_to_ai)
        self.send_to_ai_btn.setEnabled(False)

    def setup_menu(self):
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)

        file_menu = QMenu('&File', self)
        menu_bar.addMenu(file_menu)

        snip_action = QAction('&Snip', self)
        snip_action.setShortcut('Ctrl+S')
        snip_action.triggered.connect(self.snip)
        file_menu.addAction(snip_action)

        send_to_ai_action = QAction('Send to &AI', self)
        send_to_ai_action.setShortcut('Ctrl+A')
        send_to_ai_action.triggered.connect(self.send_to_ai)
        send_to_ai_action.setEnabled(False)
        file_menu.addAction(send_to_ai_action)

        self.send_to_ai_action = send_to_ai_action

        exit_action = QAction('&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def snip(self):
        try:
            self.showMinimized()
            QApplication.processEvents()

            screenshot = ImageGrab.grab()
            self.screenshot = screenshot.convert("RGBA")
            
            self.showNormal()
            self.activateWindow()
            
            self.screen_overlay = QLabel(self)
            self.screen_overlay.setGeometry(self.geometry())
            self.screen_overlay.setPixmap(QPixmap.fromImage(self.pil_image_to_qimage(self.screenshot)))
            self.screen_overlay.show()

            self.rubber_band = QRubberBand(QRubberBand.Rectangle, self.screen_overlay)
            self.origin = QPoint()
            self.screen_overlay.mousePressEvent = self.mouse_press_event
            self.screen_overlay.mouseMoveEvent = self.mouse_move_event
            self.screen_overlay.mouseReleaseEvent = self.mouse_release_event
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'An error occurred during snipping: {e}')

    def pil_image_to_qimage(self, image):
        data = image.tobytes("raw", "RGBA")
        qimage = QImage(data, image.size[0], image.size[1], QImage.Format_RGBA8888)
        return qimage

    def mouse_press_event(self, event):
        self.origin = event.pos()
        self.rubber_band.setGeometry(QRect(self.origin, QSize()))
        self.rubber_band.show()

    def mouse_move_event(self, event):
        self.rubber_band.setGeometry(QRect(self.origin, event.pos()).normalized())

    def mouse_release_event(self, event):
        self.rubber_band.hide()
        selected_rect = self.rubber_band.geometry()
        self.snipped_image = self.screenshot.crop((selected_rect.x(), selected_rect.y(), selected_rect.x() + selected_rect.width(), selected_rect.y() + selected_rect.height()))
        self.screen_overlay.close()

        self.prompt, ok = QInputDialog.getText(self, 'Enter prompt', 'Enter the prompt:')
        if ok:
            self.send_to_ai_btn.setEnabled(True)
            self.send_to_ai_action.setEnabled(True)

    def send_to_ai(self):
        try:
            prompt = f"{self.prompt}: {self.snipped_image}"
            response = self.generate_ai_response(prompt)

            if response:
                QMessageBox.information(self, 'AI Response', response)
            else:
                QMessageBox.warning(self, 'Error', 'Could not generate a response from the AI.')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'An error occurred while sending to AI: {e}')

        self.send_to_ai_btn.setEnabled(False)
        self.send_to_ai_action.setEnabled(False)

    def generate_ai_response(self, prompt):
        try:
            response = openai.Completion.create(
                engine="text-davinci-002",
                prompt=prompt,
                max_tokens=100,
                n=1,
                stop=None,
                temperature=0.8,
            )
            return response.choices[0].text.strip()
        except Exception as e:
            print(e)
            return None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    snaipper = SnaipperApp()
    snaipper.show()
    sys.exit(app.exec_())
