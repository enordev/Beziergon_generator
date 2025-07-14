from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog
from PyQt5.QtGui import QPainter, QPen, QPainterPath
from PyQt5.QtSvg import QSvgGenerator
from PyQt5.QtCore import Qt, QPointF, QRect
import sys

class SplineDrawer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spline Drawer with SVG Export")
        self.setGeometry(100, 100, 600, 400)

        self.points = []

        self.save_button = QPushButton("Save as SVG", self)
        self.save_button.move(10, 10)
        self.save_button.clicked.connect(self.save_svg)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.points.append(event.pos())
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        self.draw_spline(painter)

    def draw_spline(self, painter):
        pen = QPen(Qt.black, 2)
        painter.setPen(pen)

        if len(self.points) >= 4:
            path = QPainterPath()
            path.moveTo(self.points[0])
            i = 1
            while i + 2 < len(self.points):
                path.cubicTo(self.points[i], self.points[i + 1], self.points[i + 2])
                i += 3
            painter.drawPath(path)

        for p in self.points:
            painter.drawEllipse(p, 3, 3)

    def save_svg(self):
        if len(self.points) < 4:
            return

        path = QFileDialog.getSaveFileName(self, "Save SVG", "", "SVG files (*.svg)")[0]
        if not path:
            return

        generator = QSvgGenerator()
        generator.setFileName(path)
        generator.setSize(self.size())
        generator.setViewBox(QRect(0, 0, self.width(), self.height()))
        generator.setTitle("Spline Drawing")
        generator.setDescription("Spline drawn with PyQt5")

        painter = QPainter()
        painter.begin(generator)
        self.draw_spline(painter)
        painter.end()
        print(f"SVG saved to: {path}")

app = QApplication(sys.argv)
window = SplineDrawer()
window.show()
sys.exit(app.exec_())