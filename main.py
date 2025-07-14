from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog
from PyQt5.QtGui import QPainter, QPen, QPainterPath
from PyQt5.QtSvg import QSvgGenerator
from PyQt5.QtCore import Qt, QRectF, QPointF
import sys
import numpy as np
from scipy.interpolate import splprep, splev

class BSplineDrawer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Closed B-Spline Drawer with Draggable Points")
        self.setGeometry(100, 100, 600, 400)

        self.points = []
        self.dragging_index = None  # Index of the point being dragged

        self.save_button = QPushButton("Save as SVG", self)
        self.save_button.move(10, 10)
        self.save_button.clicked.connect(self.save_svg)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            # Check if clicking near an existing point
            for i, (x, y) in enumerate(self.points):
                if (QPointF(x, y) - pos).manhattanLength() < 10:
                    self.dragging_index = i
                    return
            # Otherwise add a new point
            self.points.append((pos.x(), pos.y()))
            self.update()

    def mouseMoveEvent(self, event):
        if self.dragging_index is not None:
            self.points[self.dragging_index] = (event.pos().x(), event.pos().y())
            self.update()

    def mouseReleaseEvent(self, event):
        self.dragging_index = None

    def paintEvent(self, event):
        painter = QPainter(self)
        self.draw_bspline(painter)

    def draw_bspline(self, painter):
        if len(self.points) < 4:
            pen = QPen(Qt.gray, 1, Qt.DashLine)
            painter.setPen(pen)
            if self.points:
                path = QPainterPath()
                path.moveTo(*self.points[0])
                for pt in self.points[1:]:
                    path.lineTo(*pt)
                painter.drawPath(path)

            # Draw control points
            for x, y in self.points:
                painter.setPen(QPen(Qt.black))
                painter.drawEllipse(QRectF(x - 3, y - 3, 6, 6))
            return

        # Normal spline drawing as before...


        pen = QPen(Qt.black, 2)
        painter.setPen(pen)

        path = self.bspline_path(self.points, closed=True)
        painter.drawPath(path)

        # Draw control points
        for x, y in self.points:
            painter.drawEllipse(QRectF(x - 3, y - 3, 6, 6))

    def bspline_path(self, points, closed=True, resolution=100):
        if len(points) < 4:
            return QPainterPath()

        x, y = zip(*points)

        try:
            tck, u = splprep([x, y], s=0, per=closed)
        except Exception as e:
            print("Spline error:", e)
            return QPainterPath()

        u_fine = np.linspace(0, 1, resolution)
        x_fine, y_fine = splev(u_fine, tck)

        path = QPainterPath()
        path.moveTo(x_fine[0], y_fine[0])
        for xf, yf in zip(x_fine[1:], y_fine[1:]):
            path.lineTo(xf, yf)

        if closed:
            path.closeSubpath()

        return path

    def save_svg(self):
        if len(self.points) < 4:
            return

        file_path = QFileDialog.getSaveFileName(self, "Save SVG", "", "SVG files (*.svg)")[0]
        if not file_path:
            return

        generator = QSvgGenerator()
        generator.setFileName(file_path)
        generator.setSize(self.size())
        generator.setViewBox(self.rect())
        generator.setTitle("Closed B-Spline Drawing")
        generator.setDescription("Closed B-spline with draggable points")

        painter = QPainter()
        painter.begin(generator)
        self.draw_bspline(painter)
        painter.end()
        print(f"SVG saved to: {file_path}")

app = QApplication(sys.argv)
window = BSplineDrawer()
window.show()
sys.exit(app.exec_())