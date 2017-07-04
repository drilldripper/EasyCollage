""" Transform image using corresponding points. 
"""

import os.path

from PyQt5.QtCore import Qt, QRectF, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QBrush
from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QFileDialog, \
    QGraphicsEllipseItem, QGraphicsPixmapItem

from src.homography import register_by_homography


class EllipseItem(QGraphicsEllipseItem):
    """
    Draw a point on clicked position.
    """

    def __init__(self, index, pos, parent=None):
        QGraphicsPixmapItem.__init__(self, parent)
        self.index = index
        self.setRect(QRectF(pos.x(), pos.y(), 10, 10))
        self.select_color(self.index)

    def select_color(self, color_index):
        """ Select color by index number"""

        color_index %= 6
        if color_index == 0:
            color = QBrush(Qt.red)
        elif color_index == 1:
            color = QBrush(Qt.green)
        elif color_index == 2:
            color = QBrush(Qt.blue)
        elif color_index == 3:
            color = QBrush(Qt.magenta)
        elif color_index == 4:
            color = QBrush(Qt.yellow)
        elif color_index == 5:
            color = QBrush(Qt.gray)
        self.setBrush(color)


class ImageViewerQt(QGraphicsView):
    """ 
    Mouse action:Zoom and pan. 
    Left Click: put sign object
    """
    leftMouseButtonPressed = pyqtSignal(float, float)
    rightMouseButtonPressed = pyqtSignal(float, float)
    leftMouseButtonReleased = pyqtSignal(float, float)
    rightMouseButtonReleased = pyqtSignal(float, float)
    leftMouseButtonDoubleClicked = pyqtSignal(float, float)
    rightMouseButtonDoubleClicked = pyqtSignal(float, float)

    def __init__(self):
        QGraphicsView.__init__(self)

        # Image is displayed as a QPixmap in a QGraphicsScene attached to this QGraphicsView.
        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        # Store a local handle to the scene's current image pixmap.
        self._pixmapHandle = None

        # Image aspect ratio mode.
        self.aspectRatioMode = Qt.KeepAspectRatio

        # Scroll bar behaviour.
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Stack of QRectF zoom boxes in scene coordinates.
        self.zoomStack = []

        # Flags for enabling/disabling mouse interaction.
        self.canZoom = True
        self.canPan = True

        # Clicked position data.
        self.index = 0
        self.posArray = []

        self.fileName = ''

        # Corresponding points history.
        self.itemHistory = []

    def hasImage(self):
        """ Returns whether or not the scene contains an image pixmap.
        """
        return self._pixmapHandle is not None

    def clearImage(self):
        """ Removes the current image pixmap from the scene if it exists.
        """
        if self.hasImage():
            self.scene.removeItem(self._pixmapHandle)
            self._pixmapHandle = None

    def pixmap(self):
        """ Returns the scene's current image pixmap as a QPixmap, or else None if no image exists.
        :rtype: QPixmap | None
        """
        if self.hasImage():
            return self._pixmapHandle.pixmap()
        return None

    def image(self):
        """ Returns the scene's current image pixmap as a QImage, or else None if no image exists.
        :rtype: QImage | None
        """
        if self.hasImage():
            return self._pixmapHandle.pixmap().toImage()
        return None

    def setImage(self, image):
        """ Set the scene's current image pixmap to the input QImage or QPixmap.
        Raises a RuntimeError if the input image has type other than QImage or QPixmap.
        :type image: QImage | QPixmap
        """
        if type(image) is QPixmap:
            pixmap = image
        elif type(image) is QImage:
            pixmap = QPixmap.fromImage(image)
        else:
            raise RuntimeError("ImageViewer.setImage: Argument must be a QImage or QPixmap.")
        if self.hasImage():
            self._pixmapHandle.setPixmap(pixmap)
        else:
            self._pixmapHandle = self.scene.addPixmap(pixmap)
        self.setSceneRect(QRectF(pixmap.rect()))  # Set scene size to image size.
        self.updateViewer()

    def loadImageFromFile(self, fileName=""):
        """ Load an image from file.
        If you not set filename as constructor, launch a file dialog.
        """

        if fileName == "":
            self.fileName, dummy = QFileDialog.getOpenFileName(self, "Open image file.")
        else:
            self.fileName = fileName

        if len(self.fileName) and os.path.isfile(self.fileName):
            image = QImage(self.fileName)
            self.setImage(image)

    def updateViewer(self):
        """ Show current zoom.
        """
        if not self.hasImage():
            return
        if len(self.zoomStack) and self.sceneRect().contains(self.zoomStack[-1]):
            self.fitInView(self.zoomStack[-1], Qt.IgnoreAspectRatio)  # Show zoomed rect (ignore aspect ratio).
        else:
            self.zoomStack = []  # Clear the zoom stack (in case we got here because of an invalid zoom).
            self.fitInView(self.sceneRect(), self.aspectRatioMode)  # Show entire image (use current aspect ratio mode).

    def mouseReleaseEvent(self, event):
        """ Put items on mouse position. 
        """
        scenePos = self.mapToScene(event.pos())

        if event.button() == Qt.LeftButton:
            print("mouse event")
            ellipseItem = EllipseItem(self.index, scenePos)

            self.scene.addItem(ellipseItem)
            self.itemHistory.append(ellipseItem)
            print(self.itemHistory)
            self.index += 1

            print(scenePos.x(), scenePos.y())
            self.posArray.append([int(scenePos.x()), int(scenePos.y())])

        elif event.button() == Qt.RightButton:
            print("right click!!")
            print(self.posArray)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_U:
            try:
                last = self.itemHistory.pop()
                self.scene.removeItem(last)
            except IndexError:
                print("No items to remove.")
                return
            print("A last item was removed.")

    def wheelEvent(self, event):
        """Zoom and pans by mouse wheel.
        """
        factor = 1.41 ** (-event.angleDelta().y() / 240.0)
        self.scale(factor, factor)


class MainWindow(ImageViewerQt):
    def __init__(self, mode):
        super().__init__()
        self.show()

        self.referenceView = ImageViewerQt()
        self.referenceView.loadImageFromFile()  # Pops up file dialog.
        # Handle left mouse clicks with custom slot.
        self.referenceView.leftMouseButtonPressed.connect(handleLeftClick)
        self.referenceView.setWindowTitle('Reference Image')

        self.targetView = ImageViewerQt()
        self.targetView.loadImageFromFile()  # Pops up file dialog.
        # Handle left mouse clicks with custom slot.
        self.targetView.leftMouseButtonPressed.connect(handleLeftClick)
        self.tawgetView.setWindowTitle('Target Image')

        # Show viewer and run application.
        self.referenceView.show()
        self.targetView.show()
        sys.exit(app.exec_())

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_T:
            print("T key is pressed")
            ref_pos = self.referenceView.posArray
            target_pos = self.targetView.posArray

            img, filename = register_by_homography(self.referenceView.fileName,
                                   self.targetView.fileName,
                                   ref_pos, target_pos)

            self.loadImageFromFile(filename)
            self.resize(img.shape[1], img.shape[0])

if __name__ == '__main__':
    import sys

    def handleLeftClick(x, y):
        """Handle mouse cllck event. And print coord."""
        row = int(y)
        column = int(x)
        print("Clicked on image pixel (row="+str(row)+", column="+str(column)+")")

    # Create the application.
    app = QApplication(sys.argv)
    main = MainWindow("REG")
    main.show()

    sys.exit(app.exec_())

