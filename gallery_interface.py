# coding:utf-8
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout

from qfluentwidgets import ScrollArea
from ..common.style_sheet import StyleSheet


class GalleryInterface(ScrollArea):
    """ Gallery interface """

    def __init__(self, title: str, subtitle: str, parent=None):
        """
        Parameters
        ----------
        title: str
            The title of gallery

        subtitle: str
            The subtitle of gallery

        parent: QWidget
            parent widget
        """
        super().__init__(parent=parent)
        self.view = QWidget(self)
        self.vBoxLayout = QVBoxLayout(self.view)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidget(self.view)
        self.setWidgetResizable(True)

        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)

        self.view.setObjectName('view')
        StyleSheet.GALLERY_INTERFACE.apply(self)

    def resizeEvent(self, e):
        super().resizeEvent(e)
