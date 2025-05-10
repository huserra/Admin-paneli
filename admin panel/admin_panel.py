from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import QTimer
import sys

class TypewriterEffect:
    def __init__(self, label, text, speed=100):
        self.label = label
        self.text = text
        self.index = 0
        self.speed = speed
        self.timer = QTimer()
        self.timer.timeout.connect(self.typing)
        self.timer.start(self.speed)

    def typing(self):
        if self.index < len(self.text):
            self.label.setText(self.text[:self.index] + "|")  # Cursor efekti
            self.index += 1
        else:
            self.label.setText(self.text)  # Tamamlanınca cursor kalkar
            self.timer.stop()

class AdminPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Smart Locker Admin Panel")
        self.setGeometry(200, 200, 600, 400)
        layout = QVBoxLayout()
        self.setStyleSheet("background-color: #222; color: white; font-size: 18px; padding: 20px;")

        # Başlık (Cursor efekti ile yazılacak)
        self.header = QLabel("")
        layout.addWidget(self.header)
        TypewriterEffect(self.header, "📊 Dashboard", speed=50)

        # Menü Öğeleri (Cursor efekti ile yazılacak)
        menu_items = [
            "👥 User Management",
            "🔒 Locker Management",
            "📅 Reservation Management",
            "💳 Payment Management",
            "🔔 Notifications"
        ]
        self.labels = []
        for item in menu_items:
            lbl = QLabel("")
            lbl.setStyleSheet("margin-top: 10px;")  # Menü öğeleri aralıklı olsun
            layout.addWidget(lbl)
            self.labels.append(lbl)
            TypewriterEffect(lbl, item, speed=50)

        self.setLayout(layout)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AdminPanel()
    window.show()  # Pencereyi göster
    sys.exit(app.exec_())  # Main event loop'u başlat
