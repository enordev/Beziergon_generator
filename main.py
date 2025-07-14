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
        if event.button() != Qt.LeftButton:
            return

        pos = event.pos()
        px, py = pos.x(), pos.y()

        # 1. Check if clicking near an existing point (for dragging)
        for i, (x, y) in enumerate(self.points):
            if (QPointF(x, y) - pos).manhattanLength() < 10:
                self.dragging_index = i
                return

        # 2. Check if clicking near a line segment (for inserting)
        insert_index = self.find_insert_index(pos)
        insert_index, insert_pos = self.find_insert_on_curve(pos)
        if insert_index is not None:
            self.points.insert(insert_index, insert_pos)

        else:
            # 3. Otherwise add as a new endpoint
            self.points.append((px, py))

        self.update()

    def keyPressEvent(self, event):
        if event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_Z:
            if self.points:
                self.points.pop()
                self.update()


    def find_insert_index(self, pos, threshold=10):
        if len(self.points) < 2:
            return None

        px, py = pos.x(), pos.y()
        for i in range(len(self.points) - 1):  # Only valid segments
            a = self.points[i]
            b = self.points[i + 1]

            dist = self.point_to_segment_distance(px, py, *a, *b)
            if dist < threshold:
                return i + 1
        return None

    
    def point_to_segment_distance(self, px, py, x1, y1, x2, y2):
        """Returns distance from (px, py) to segment (x1,y1)-(x2,y2)"""
        line_mag_sq = (x2 - x1)**2 + (y2 - y1)**2
        if line_mag_sq == 0:
            return np.hypot(px - x1, py - y1)

        t = max(0, min(1, ((px - x1)*(x2 - x1) + (py - y1)*(y2 - y1)) / line_mag_sq))
        proj_x = x1 + t * (x2 - x1)
        proj_y = y1 + t * (y2 - y1)
        return np.hypot(px - proj_x, py - proj_y)
    
    def find_insert_on_curve(self, pos, threshold=10):
        if len(self.points) < 4:
            return None, None

        px, py = pos.x(), pos.y()

        x, y = zip(*self.points)
        try:
            tck, _ = splprep([x, y], s=0, per=True)
            u_fine = np.linspace(0, 1, 300)
            x_fine, y_fine = splev(u_fine, tck)
        except Exception as e:
            print("Spline error in insert:", e)
            return None, None

        min_dist = float('inf')
        insert_index = None
        insert_point = None

        for i in range(len(x_fine) - 1):
            ax, ay = x_fine[i], y_fine[i]
            bx, by = x_fine[i + 1], y_fine[i + 1]
            dist = self.point_to_segment_distance(px, py, ax, ay, bx, by)

            if dist < threshold and dist < min_dist:
                min_dist = dist
                insert_index = i
                # Insert point is the projection on segment (ax,ay)-(bx,by)
                insert_point = self.closest_point_on_segment(px, py, ax, ay, bx, by)

        if insert_index is not None and insert_point:
            # Estimate where in control points this point best fits
            # Here, a heuristic: find closest pair in control points
            best_cp_index = self.estimate_control_insertion_index(insert_point)
            return best_cp_index, insert_point

        return None, None

    def closest_point_on_segment(self, px, py, x1, y1, x2, y2):
        """Returns (x, y) of closest point on segment"""
        dx = x2 - x1
        dy = y2 - y1
        if dx == dy == 0:
            return x1, y1
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
        return x1 + t * dx, y1 + t * dy

    def estimate_control_insertion_index(self, insert_point):
        """Finds where to insert the new control point based on distance between control points"""
        min_dist = float('inf')
        index = 0
        for i in range(len(self.points) - 1):
            dist = self.point_to_segment_distance(*insert_point, *self.points[i], *self.points[i + 1])
            if dist < min_dist:
                min_dist = dist
                index = i + 1
        return index


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