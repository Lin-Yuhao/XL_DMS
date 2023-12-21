# coding:utf-8
from typing import List

from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtGui import QFont, QRegularExpressionValidator
from PyQt6.QtSql import QSqlDatabase, QSqlQuery
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QWidget, QHBoxLayout, QMessageBox, QStackedWidget
from qfluentwidgets import (FluentIcon, FlowLayout, SmoothScrollArea, ToolButton, SubtitleLabel,
                            TitleLabel, ProgressBar, MessageBoxBase, LineEdit, InfoBar, InfoBarPosition,
                            SegmentedWidget, Pivot, RoundMenu, Action, MenuAnimationType, MessageBox, CardWidget,
                            setCustomStyleSheet)

from qfluentwidgets import FluentIcon as FIF
from .gallery_interface import GalleryInterface
from ..common.translator import Translator
from ..common.config import cfg
from ..common.trie import Trie
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename='oh.log',
                    filemode='a')


class CustomMessageBox(MessageBoxBase):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.pivot = Pivot(self)
        self.stackedWidget = QStackedWidget(self)
        self.lastSele = 0

        self.songInterface = QFrame(self)
        self.albumInterface = QFrame(self)
        self.aloneLayout = QVBoxLayout()
        self.batchLayout = QVBoxLayout()
        self.batchLayout.setSpacing(10)
        self.songInterface.setLayout(self.aloneLayout)
        self.albumInterface.setLayout(self.batchLayout)
        self.aloneLayout.setSpacing(15)
        self.batchLayout.setSpacing(15)

        self.dormitoryLineEdit = LineEdit(self)
        self.BedsLineEdit = LineEdit(self)
        self.dormitoryLineEdit.setPlaceholderText('宿舍号')
        self.dormitoryLineEdit.setClearButtonEnabled(True)
        self.BedsLineEdit.setPlaceholderText('床位数量')
        self.BedsLineEdit.setClearButtonEnabled(True)

        self.startEdit = LineEdit(self)
        self.startEdit.setPlaceholderText('起始宿舍号')
        self.endEdit = LineEdit(self)
        self.endEdit.setPlaceholderText('结尾宿舍号')
        self.BedsEdit = LineEdit(self)
        self.BedsEdit.setPlaceholderText('统一床位数量')

        self.albumInterface.layout().addWidget(self.startEdit)
        self.albumInterface.layout().addWidget(self.endEdit)
        self.albumInterface.layout().addWidget(self.BedsEdit)
        self.songInterface.layout().addWidget(self.dormitoryLineEdit)
        self.songInterface.layout().addWidget(self.BedsLineEdit)

        self.addSubInterface(self.songInterface, 'songInterface', '单独添加')
        self.addSubInterface(self.albumInterface, 'albumInterface', '批量添加')

        self.viewLayout.addWidget(self.pivot)
        self.viewLayout.addWidget(self.stackedWidget)

        self.yesButton.setText('添加')
        self.cancelButton.setText('取消')

        self.widget.setMinimumWidth(350)
        self.yesButton.setDisabled(True)
        self.dormitoryLineEdit.textChanged.connect(self._validateUrl)
        self.BedsLineEdit.textChanged.connect(self._validateUrl)
        self.startEdit.textChanged.connect(self._validateUrl)
        self.endEdit.textChanged.connect(self._validateUrl)
        self.BedsEdit.textChanged.connect(self._validateUrl)
        self.pivot.setCurrentItem(self.songInterface.objectName())

    def addSubInterface(self, widget: QFrame, objectName, text):
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(routeKey=objectName, text=text, onClick=lambda: self.switchInputs(widget))

    def switchInputs(self, widget):
        self.stackedWidget.setCurrentWidget(widget)
        if self.lastSele == self.stackedWidget.currentIndex():
            self.lastSele = self.stackedWidget.currentIndex()
        else:
            self.lastSele = self.stackedWidget.currentIndex()
            if self.lastSele == 0:
                self.startEdit.clear()
                self.endEdit.clear()
                self.BedsEdit.clear()
            else:
                self.dormitoryLineEdit.clear()
                self.BedsLineEdit.clear()

    def _validateUrl(self):
        if self.lastSele == 0:
            dormText = self.dormitoryLineEdit.text()
            bedsText = self.BedsLineEdit.text()
            self.yesButton.setEnabled(dormText.isdigit() and bedsText.isdigit() and dormText[0] != '0' and bedsText[0] != '0')
        else:
            startEdit = self.startEdit.text()
            endEdit = self.endEdit.text()
            BedsEdit = self.BedsEdit.text()
            self.yesButton.setEnabled(startEdit.isdigit() and endEdit.isdigit() and BedsEdit.isdigit() and int(startEdit) < int(endEdit) and startEdit[0] != '0' and endEdit[0] != '0')


class IconCardView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.view = QFrame(self)
        self.scrollArea = SmoothScrollArea(self.view)
        self.scrollWidget = QWidget(self.scrollArea)

        self.vBoxLayout = QVBoxLayout(self)
        self.hBoxLayout = QHBoxLayout(self.view)
        self.flowLayout = FlowLayout(self.scrollWidget, needAni=False)
        self.view.setStyleSheet("background-color: rgba(0,0,0,0);border: none;")

        self.currentIndex = -1

        self.db = None
        self.db_connect()

        self.pivot = SegmentedWidget(self)
        self.vBoxLayout.addWidget(self.pivot)

        self.pivot.addItem(routeKey='all', text='全部', onClick=lambda: self.filterLayer(-1))
        self.pivot.addItem(routeKey='1', text='1', onClick=lambda: self.filterLayer(1))
        self.pivot.addItem(routeKey='2', text='2', onClick=lambda: self.filterLayer(2))
        self.pivot.addItem(routeKey='3', text='3', onClick=lambda: self.filterLayer(3))
        self.pivot.addItem(routeKey='4', text='4', onClick=lambda: self.filterLayer(4))
        self.pivot.addItem(routeKey='5', text='5', onClick=lambda: self.filterLayer(5))
        self.pivot.addItem(routeKey='6', text='6', onClick=lambda: self.filterLayer(6))
        # self.pivot.addItem(routeKey='7', text='7', onClick=lambda: self.filterLayer(7))
        # self.pivot.addItem(routeKey='8', text='8', onClick=lambda: self.filterLayer(8))
        # self.pivot.addItem(routeKey='9', text='9', onClick=lambda: self.filterLayer(9))

        self.__initWidget()
        self.allData()

    def filterLayer(self, filterInt):
        self.currentIndex = filterInt
        self.__initWidget()
        if filterInt != -1:
            self.partialData(filterInt)
        else:
            self.allData()

    def db_connect(self):
        self.db = QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName('./xldb.db')
        self.db.setUserName('root')
        self.db.setPassword('xl123')
        if not self.db.open():
            QMessageBox.critical(self, 'Database Connection', self.db.lastError().text())
        query = QSqlQuery(self.db)
        query.exec("""
            CREATE TABLE IF NOT EXISTS dormitories (
                id INTEGER PRIMARY KEY,
                dormitory_name INTEGER NOT NULL UNIQUE,
                bed_number INTEGER NOT NULL,
                num_students INTEGER
            );
        """)
        query.exec("""
            CREATE TABLE IF NOT EXISTS students (  
                id INTEGER PRIMARY KEY,  
                name TEXT NOT NULL,  
                phone TEXT,  
                parent_name TEXT,
                parent_phone TEXT,
                gender TEXT NOT NULL CHECK (gender IN ('男', '女')),  
                class TEXT,  
                dormitory_id INTEGER,  
                bed_number INTEGER,  
                address TEXT,
                arrival_date TEXT,
                FOREIGN KEY (dormitory_id) REFERENCES dormitories(id)  
            );  
        """)
        query.exec("""
                    CREATE TABLE IF NOT EXISTS students_out(  
                        id INTEGER PRIMARY KEY,  
                        name TEXT,  
                        phone TEXT,  
                        parent_name TEXT,
                        parent_phone TEXT,
                        gender TEXT,  
                        class TEXT,  
                        dormitory_id INTEGER,  
                        bed_number INTEGER,  
                        address TEXT,
                        arrival_date TEXT,
                        check_out_date TEXT,
                        stayDays TEXT
                    );  
                """)
        query.exec("""  
            CREATE TABLE IF NOT EXISTS repairs (  
                id INTEGER PRIMARY KEY,  
                location VARCHAR(255) NOT NULL,  
                item VARCHAR(255) NOT NULL,  
                note TEXT,  
                repair_date DATE  
            );  
        """)

    def initWidget(self):
        self.__initWidget()
        self.allData()

    def __initWidget(self):
        self.flowLayout.removeAllWidgets()
        del_list = self.flowLayout.parent().findChildren(ToolButton) + self.flowLayout.parent().findChildren(
            CardWidget)
        for i in del_list:
            i.deleteLater()
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setViewportMargins(0, 0, 0, 0)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.vBoxLayout.setContentsMargins(5, 5, 5, 5)
        self.vBoxLayout.addWidget(self.view)

        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.addWidget(self.scrollArea)

        self.flowLayout.setVerticalSpacing(8)
        self.flowLayout.setHorizontalSpacing(8)
        self.flowLayout.setContentsMargins(10, 10, 10, 10)

        # self.flowLayout.setVerticalSpacing(0)
        # self.flowLayout.setHorizontalSpacing(0)
        # self.flowLayout.setContentsMargins(0, 0, 0, 0)

        self.__setQss()
        cfg.themeChanged.connect(self.__setQss)

    def partialData(self, filterInt: int):
        query = QSqlQuery(self.db)
        if query.exec(f"SELECT * FROM dormitories WHERE dormitory_name LIKE '{filterInt}%'"):
            while query.next():
                dormitory_id = query.value("id")
                dormitory_name = query.value("dormitory_name")
                bed_number = query.value("bed_number")
                num_students = query.value("num_students")
                self.addItem(dormitory_id, dormitory_name, bed_number, num_students)
        self.addDormitory()

    def allData(self):
        query = QSqlQuery(self.db)
        if query.exec("SELECT * FROM dormitories ORDER BY CAST(dormitory_name AS INTEGER) ASC;"):
            while query.next():
                dormitory_id = query.value("id")
                dormitory_name = query.value("dormitory_name")
                bed_number = query.value("bed_number")
                num_students = query.value("num_students")
                self.addItem(dormitory_id, dormitory_name, bed_number, num_students)
        self.addDormitory()

    # def resizeEvent(self, event):
    #     super().resizeEvent(event)
    #     winWidth = self.parent().parent().size().width()
    #     if winWidth < 1000:
    #         for card in self.flowLayout.parent().findChildren(CardWidget) + self.flowLayout.parent().findChildren(ToolButton):
    #             card.setMinimumSize(200, 110)
    #     elif winWidth < 1600:
    #         for card in self.flowLayout.parent().findChildren(CardWidget) + self.flowLayout.parent().findChildren(ToolButton):
    #             card.setMinimumSize(250, 110)
        #         int(self.parent().parent().size().width() / 6)-12
        # else:
        #     for card in self.flowLayout.parent().findChildren(ElevatedCardWidget) + self.flowLayout.parent().findChildren(ToolButton):
        #         card.setMinimumSize(int(self.parent().parent().size().width() / 10) -12, 110)

    def addItem(self, dormitory_id, dormitory_name: str, bed_number, num_students):
        card = CardWidget(self)
        # print(int(self.parent().parent().size().width() / 4) -12)
        card.setMinimumSize(196, 110)
        card.setObjectName(f'card_{dormitory_id}')
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        card.setLayout(layout)
        card.setBorderRadius(5)

        Titlelabel = TitleLabel()
        Titlelabel.setText(f"{dormitory_name}")
        Titlelabel.setFont(QFont("黑体", 30))
        Titlelabel.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)

        gress = ProgressBar()
        if isinstance(bed_number, int):
            gress.setValue(min(int((num_students/bed_number)*100), 100))
            gress.setUseAni(False)
            if num_students >= bed_number:
                gress.setError(True)

        Subtitlelabel = SubtitleLabel()
        Subtitlelabel.setText(f"{num_students}/{bed_number}")
        Subtitlelabel.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(Titlelabel)
        layout.addWidget(Subtitlelabel)
        layout.addWidget(gress)

        card.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        card.customContextMenuRequested.connect(lambda event: self.showCustomContextMenu(event, card, dormitory_name, bed_number))

        self.flowLayout.addWidget(card)

    def showCustomContextMenu(self, event, card, dormitory_name, bed_number):
        menu = RoundMenu(self)
        menu.addAction(Action(FIF.CLEAR_SELECTION, '查看人员'))
        menu.addAction(Action(FIF.BRUSH, '宿舍报修'))
        menu.addSeparator()
        menu.addAction(Action(FIF.DELETE, '修改'))
        menu.addAction(Action(FIF.DELETE, '删除'))
        menu.actions()[0].triggered.connect(lambda: self.selectDormitory(dormitory_name))
        menu.actions()[1].triggered.connect(lambda: self.selectRepair(dormitory_name))
        menu.actions()[2].triggered.connect(lambda: self.reviseBedNub(dormitory_name))
        menu.actions()[3].triggered.connect(lambda: self.dormitoryRemoveRow(dormitory_name))
        menu.exec(card.mapToGlobal(event), aniType=MenuAnimationType.DROP_DOWN)

    def reviseBedNub(self, dormitory_name):
        tip = MessageBox('修改床位数量', '', self)
        tip.contentLabel.hide()
        bedNub = LineEdit()
        bedNub.setPlaceholderText('床位数量')

        intvalidator = QRegularExpressionValidator()
        regex = QRegularExpression("^\d{20}$")
        intvalidator.setRegularExpression(regex)

        bedNub.setValidator(intvalidator)
        tip.textLayout.addWidget(bedNub)
        tip.textLayout.setSpacing(25)

        if tip.exec():
            query = QSqlQuery(self.db)
            query.prepare("UPDATE dormitories SET bed_number = :bed_number WHERE dormitory_name = :dormitory_name")
            query.bindValue(":bed_number", bedNub.text())
            query.bindValue(":dormitory_name", dormitory_name)
            query.exec()
            logging.info(f'修改床位数量 - {dormitory_name}')
            self.parent().parent().parent().parent().parent().parent().dormitoryReportInterface.loadText()
            self.__initWidget()
            self.allData()

    def dormitoryRemoveRow(self, dormitory_name):
        tip = MessageBox('删除宿舍', '宿舍内的学生将会变为无宿舍状态', self)
        # tip.contentLabel.hide()
        qss = '''
                PushButton{background-color: #E53935; border-color: #E53935; color: #FFFFFF}
                PushButton::hover{background-color: #EF5350; border-color: #EF5350}
                '''
        setCustomStyleSheet(tip.yesButton, qss, qss)
        if tip.exec():
            query = QSqlQuery(self.db)
            query.prepare("DELETE FROM dormitories WHERE dormitory_name = :dormitory_name")
            query.bindValue(":dormitory_name", dormitory_name)
            if query.exec():
                query = QSqlQuery(self.db)
                query.prepare("UPDATE students SET dormitory_id = '' WHERE dormitory_id = :dormitory_name")
                query.bindValue(":dormitory_name", dormitory_name)
                if query.exec():
                    self.__initWidget()
                    self.allData()
                    logging.info(f'删除宿舍 - {dormitory_name}')
                    self.parent().parent().parent().parent().parent().parent().dormitoryReportInterface.loadText()
                    self.parent().parent().parent().parent().parent().parent().moveIntoInterface.dormitoryCompleter()
                    self.parent().parent().parent().parent().parent().parent().moveIntoInterface.model.select()
                    InfoBar.success(title='已删除', content="", isClosable=False, position=InfoBarPosition.TOP, duration=2000, parent=self)

    def selectDormitory(self, dormitory_name):
        moveIntoInterface = self.parent().parent().parent().parent().parent().parent().moveIntoInterface
        self.parent().parent().parent().parent().parent().parent().switchTo(moveIntoInterface)
        moveIntoInterface.SearchLineEdit_DormitoryId.setText(str(dormitory_name))

    def selectRepair(self, dormitory_name):
        repairManageInterface = self.parent().parent().parent().parent().parent().parent().repairManageInterface
        self.parent().parent().parent().parent().parent().parent().switchTo(repairManageInterface)
        repairManageInterface.showDialog(dormitory_name)

    def addDormitory(self):
        icon = ToolButton(FluentIcon.ADD.icon(color='#BDBDBD'))
        icon.clicked.connect(self.showDialog)
        icon.setMinimumSize(200, 110)
        self.flowLayout.addWidget(icon)

    def showDialog(self):
        w = CustomMessageBox(self)
        if w.exec():
            query = QSqlQuery(self.db)
            if w.lastSele == 0:
                query.prepare(f"INSERT INTO dormitories(dormitory_name, bed_number, num_students) VALUES (?, ?, ?)")
                query.addBindValue(int(w.dormitoryLineEdit.text()))
                query.addBindValue(int(w.BedsLineEdit.text()))
                query.addBindValue(0)
                if query.exec():
                    self.__initWidget()
                    self.partialData(int(w.dormitoryLineEdit.text()[0]))
                    self.pivot.setCurrentItem(w.dormitoryLineEdit.text()[0])
                    self.parent().parent().parent().parent().parent().parent().moveIntoInterface.dormitoryCompleter()
                    logging.info(f'新增宿舍 - {w.dormitoryLineEdit.text()}')
                    self.parent().parent().parent().parent().parent().parent().dormitoryReportInterface.loadText()
                    InfoBar.success(title='添加成功', content="", isClosable=False, position=InfoBarPosition.BOTTOM_RIGHT, duration=2000, parent=self)
                else:
                    InfoBar.warning(title='重复输入', content="", isClosable=False, position=InfoBarPosition.BOTTOM_RIGHT, duration=4000, parent=self)
            else:
                data = [(i, int(w.BedsEdit.text()), 0) for i in range(int(w.startEdit.text()), int(w.endEdit.text())+1)]
                for startEdit, BedsEdit, i in data:
                    logging.info(f'新增宿舍 - {startEdit}')
                    self.parent().parent().parent().parent().parent().parent().dormitoryReportInterface.loadText()
                    query.exec(f"INSERT INTO dormitories(dormitory_name, bed_number, num_students) VALUES ({startEdit}, {BedsEdit}, {i})")
                self.parent().parent().parent().parent().parent().parent().moveIntoInterface.dormitoryCompleter()
                InfoBar.success(title='批量处理完成', content="", isClosable=False, position=InfoBarPosition.BOTTOM_RIGHT, duration=2000, parent=self)
                self.__initWidget()
                self.allData()
                self.pivot.setCurrentItem('-1')

    def __setQss(self):
        self.view.setObjectName('CardView')
        self.scrollWidget.setObjectName('scrollWidget')


class DormitoryManage(GalleryInterface):
    """ Icon interface """

    def __init__(self, parent=None):
        t = Translator()
        super().__init__(
            title=t.icons,
            subtitle="qfluentwidgets.common.icon",
            parent=parent
        )
        self.setObjectName('dormitoryInterface')

        self.iconView = IconCardView(self)
        self.vBoxLayout.addWidget(self.iconView)
