# coding:utf-8
from typing import List

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtSql import QSqlDatabase, QSqlQuery
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QWidget, QHBoxLayout, QMessageBox, QSpacerItem
from qfluentwidgets import (FluentIcon, FlowLayout, SmoothScrollArea, ElevatedCardWidget, ToolButton,
                            TitleLabel, MessageBoxBase, LineEdit, InfoBar, CalendarPicker, InfoBarPosition,
                            RoundMenu, MenuAnimationType, Action, TextEdit, ToolTipFilter, ToolTipPosition,
                            setFont, MessageBox, SubtitleLabel)

from qfluentwidgets import FluentIcon as FIF

from .gallery_interface import GalleryInterface
from ..common.translator import Translator


class CustomMessageBox(MessageBoxBase):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.Title = SubtitleLabel(self)
        self.LocationLineEdit = LineEdit(self)
        self.ItmeLineEdit = LineEdit(self)
        self.NotesLineEdit = TextEdit(self)
        self.DateLineEdit = CalendarPicker(self)

        self.Title.setText('报修')
        self.LocationLineEdit.setPlaceholderText('维修地点')
        self.ItmeLineEdit.setPlaceholderText('维修项')
        self.NotesLineEdit.setPlaceholderText('备注')
        self.DateLineEdit.setText('报修时间')

        self.Title.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.NotesLineEdit.setFixedHeight(100)

        self.viewLayout.addWidget(self.Title)
        self.viewLayout.addWidget(self.LocationLineEdit)
        self.viewLayout.addWidget(self.ItmeLineEdit)
        self.viewLayout.addWidget(self.NotesLineEdit)
        self.viewLayout.addWidget(self.DateLineEdit)

        self.yesButton.setText('添加')
        self.cancelButton.setText('取消')

        self.widget.setMinimumWidth(250)

        self.yesButton.setDisabled(True)
        self.LocationLineEdit.textChanged.connect(self._validateUrl)
        self.ItmeLineEdit.textChanged.connect(self._validateUrl)
        self.DateLineEdit.dateChanged.connect(self._validateUrl)

    def _validateUrl(self):
        LocationText = self.LocationLineEdit.text()
        ItmeLineText = self.ItmeLineEdit.text()
        DateLineText = self.DateLineEdit.getDate().toString("yyyy-MM-dd")
        self.yesButton.setEnabled(LocationText != '' and ItmeLineText != '' and DateLineText != '')


class Repair_View(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.view = QFrame(self)
        self.scrollArea = SmoothScrollArea(self.view)
        self.scrollWidget = QWidget(self.scrollArea)

        self.vBoxLayout = QVBoxLayout(self)
        self.hBoxLayout = QHBoxLayout(self.view)
        self.flowLayout = FlowLayout(self.scrollWidget, needAni=False)
        self.view.setStyleSheet("background-color: rgba(0,0,0,0);border: none;")

        self.db = None
        self.db_connect()

        self.__initWidget()
        self.allData()

    def db_connect(self):
        self.db = QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName('./xldb.db')
        self.db.setUserName('root')
        self.db.setPassword('xl123')
        if not self.db.open():
            QMessageBox.critical(self, 'Database Connection', self.db.lastError().text())

    def __initWidget(self):
        self.flowLayout.removeAllWidgets()
        del_list = self.flowLayout.parent().findChildren(ToolButton) + self.flowLayout.parent().findChildren(ElevatedCardWidget)
        for i in del_list: i.deleteLater()
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setViewportMargins(0, 0, 0, 0)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addWidget(self.view)

        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.addWidget(self.scrollArea)

        self.flowLayout.setVerticalSpacing(8)
        self.flowLayout.setHorizontalSpacing(8)
        self.flowLayout.setContentsMargins(10, 10, 10, 10)

    def allData(self):
        query = QSqlQuery(self.db)
        if query.exec("SELECT * FROM repairs;"):
            while query.next():
                repairs_id = query.value("id")
                location = query.value("location")
                item = query.value("item")
                note = query.value("note")
                repair_date = query.value("repair_date")
                self.addItem(repairs_id, location, item, note, repair_date)
        self.addDormitory()

    def addItem(self, repairs_id, location, item, note, repair_date):
        card = ElevatedCardWidget(self)
        card.setMinimumSize(200, 110)
        card.setObjectName(f'card_{repairs_id}')
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        card.setLayout(layout)
        card.setBorderRadius(5)

        card.setToolTip(note)
        card.installEventFilter(ToolTipFilter(card, 1000, ToolTipPosition.BOTTOM))

        Titlelabel = TitleLabel()
        Titlelabel.setText(location)
        Titlelabel.setFont(QFont("黑体", 30))
        Titlelabel.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)

        Subtitlelabel = SubtitleLabel()
        Subtitlelabel.setText(item)
        Subtitlelabel.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)

        dataSubtitlelabel = SubtitleLabel()
        dataSubtitlelabel.setText(repair_date)
        dataSubtitlelabel.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        setFont(dataSubtitlelabel, 12)

        dcolor = QColor(127, 127, 127)
        dataSubtitlelabel.setTextColor(dcolor, dcolor)

        layout.addItem(QSpacerItem(10, 10))
        layout.addWidget(Titlelabel)
        layout.addWidget(Subtitlelabel)
        layout.addWidget(dataSubtitlelabel)
        layout.addItem(QSpacerItem(10, 10))

        card.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        card.customContextMenuRequested.connect(lambda event: self.showCustomContextMenu(event, card, repairs_id))

        self.flowLayout.addWidget(card)

    def showCustomContextMenu(self, event, card, repairs_id):
        self.__initWidget()
        self.allData()
        menu = RoundMenu(self)
        menu.addActions([Action(FIF.DELETE, '删除')])
        menu.actions()[0].triggered.connect(lambda: self.repairsRemoveRow(repairs_id))
        menu.exec(card.mapToGlobal(event), aniType=MenuAnimationType.DROP_DOWN)

    def repairsRemoveRow(self, repairs_id):
        tip = MessageBox('删除维修记录', '', self)
        tip.contentLabel.hide()
        if tip.exec():
            query = QSqlQuery(self.db)
            query.prepare("DELETE FROM repairs WHERE id = :id")
            query.bindValue(":id", repairs_id)
            if query.exec():
                self.__initWidget()
                self.allData()
                InfoBar.success(title='已删除', content="", isClosable=False, position=InfoBarPosition.TOP, duration=2000, parent=self)

    def addDormitory(self):
        icon = ToolButton(FluentIcon.ADD.icon(color='#BDBDBD'))
        icon.clicked.connect(self.showDialog)
        icon.setMinimumSize(200, 110)
        self.flowLayout.addWidget(icon)

    def showDialog(self, dormitory_name):
        w = CustomMessageBox(self)
        if dormitory_name:
            w.LocationLineEdit.setText(str(dormitory_name))
        if w.exec():
            query = QSqlQuery(self.db)
            query.prepare("INSERT INTO repairs (location, item, note, repair_date) VALUES (?, ?, ?, ?)")
            query.addBindValue(w.LocationLineEdit.text())
            query.addBindValue(w.ItmeLineEdit.text())
            query.addBindValue(w.NotesLineEdit.toPlainText())
            query.addBindValue(w.DateLineEdit.getDate().toString("yyyy-MM-dd"))
            if query.exec():
                self.__initWidget()
                self.allData()


class RepairManage(GalleryInterface):

    def __init__(self, parent=None):
        t = Translator()
        super().__init__(
            title=t.icons,
            subtitle="qfluentwidgets.common.icon",
            parent=parent
        )
        self.setObjectName('repairInterface')

        self.iconView = Repair_View(self)
        self.vBoxLayout.addWidget(self.iconView)
