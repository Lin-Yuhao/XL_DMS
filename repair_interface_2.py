# coding:utf-8
from PyQt6.QtSql import QSqlTableModel, QSqlDatabase, QSqlQuery
from PyQt6.QtCore import Qt, QRegularExpression, QDate
from PyQt6.QtGui import QPalette, QColor, QRegularExpressionValidator
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFrame, QHeaderView, QCompleter, QApplication, QLineEdit
from qfluentwidgets import ScrollArea, setFont, InfoBarPosition, InfoBar, MessageBox, RoundMenu, Action, \
    MenuAnimationType, CalendarPicker, MessageBoxBase, SubtitleLabel, LineEdit, TextEdit
from qfluentwidgets import FluentIcon as FIF
from ..UI.RepairManage import Ui_Frame
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename='oh.log',
                    filemode='a')


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


class RepairManage(Ui_Frame, QFrame):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.setObjectName('repairinterface')
        self.scrollAreaWidgetContents.parent().parent().setStyleSheet("background-color: rgba(0,0,0,0);border: none;")

        self.db = QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName('./xldb.db')

        self.__inteWindow()

    def __inteWindow(self):
        self.SearchLineEdit_Dormitory.searchButton.hide()
        setFont(self.SearchLineEdit_Dormitory, 16)
        setFont(self.CalendarPicker_Enroll, 16)

        # 表格模型
        self.model = QSqlTableModel(self)
        self.model.setTable('repairs')
        self.queryStudents()
        for section, header in enumerate(['维修日期', '宿舍号', '维修项', '','备注']):
            self.model.setHeaderData(section, Qt.Orientation.Horizontal, header)

        self.TableView.setModel(self.model)
        self.TableView.setColumnWidth(1, 20)
        self.TableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.TableView.setBorderVisible(True)
        self.TableView.verticalHeader().hide()
        self.TableView.setBorderRadius(8)
        self.TableView.hideColumn(3)

        self.PushButton_Remove.clicked.connect(self.clearInput)
        self.PrimaryPushButton_Create.clicked.connect(self.showDialog)
        self.SearchLineEdit_Dormitory.textChanged.connect(self.queryStudents)
        self.CalendarPicker_Enroll.dateChanged.connect(self.queryStudents)

        self.TableView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.TableView.customContextMenuRequested.connect(self.showCustomContextMenu)

        self.dormitoryCompleter(self.SearchLineEdit_Dormitory)

    def dormitoryCompleter(self, edit: QLineEdit):
        query = QSqlQuery(self.db)
        querydata = []
        if query.exec("SELECT dormitory_name FROM dormitories"):
            while query.next():
                querydata.append(str(query.value(0)))
        completer = QCompleter(querydata, self.SearchLineEdit_Dormitory)
        edit.setCompleter(completer)

    def showCustomContextMenu(self, position):
        index = self.TableView.indexAt(position)
        if not index.isValid(): return

        menu = RoundMenu(self)
        menu.addActions([Action(FIF.ADD_TO, '删除')])
        self.TableView.setCurrentIndex(index)
        menu.actions()[0].triggered.connect(lambda: self.tableViewRemoveRow(index))
        menu.exec(self.TableView.mapToGlobal(position), aniType=MenuAnimationType.DROP_DOWN)

    def clearInput(self):
        self.SearchLineEdit_Dormitory.clear()

        CalendarPicker_Casual = CalendarPicker()
        self.SimpleCardWidget.layout().replaceWidget(self.CalendarPicker_Enroll, CalendarPicker_Casual)
        self.CalendarPicker_Enroll.deleteLater()
        self.CalendarPicker_Enroll = CalendarPicker_Casual
        self.CalendarPicker_Enroll.setText('登记日期')
        self.CalendarPicker_Enroll.dateChanged.connect(self.queryStudents)
        self.queryStudents()

    def queryStudents(self):
        query = QSqlQuery(self.db)
        query.prepare("""
                    SELECT repair_date, location, item, id, note
                    FROM repairs
                    WHERE location LIKE :location
                    AND repair_date LIKE :repair_date
        """)
        query.bindValue(":location", f'%{self.SearchLineEdit_Dormitory.text()}%')
        query.bindValue(":repair_date", f'%{self.CalendarPicker_Enroll.date.toString("yyyy-MM-dd")}%')
        if query.exec():
            self.model.setQuery(query)
            self.TableView.resizeRowsToContents()

    def tableViewRemoveRow(self, index):
        tip = MessageBox('删除', '', self)
        tip.contentLabel.hide()
        if tip.exec():
            logging.info(f'删除维修-{self.model.index(index.row(), 1).data()} - {self.model.index(index.row(), 2).data()}')
            self.parent().parent().parent().dormitoryReportInterface.loadText()
            self.model.removeRow(index.row())
            self.model.submitAll()
            self.model.select()
            self.clearInput()
            InfoBar.success(title='删除成功', content="", isClosable=False, position=InfoBarPosition.TOP, duration=2000, parent=self)

    def showDialog(self, dormitory_name):
        w = CustomMessageBox(self)
        self.dormitoryCompleter(w.LocationLineEdit)
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
                logging.info(f'新增维修 - {w.LocationLineEdit.text()} - {w.ItmeLineEdit.text()}')
                self.parent().parent().parent().dormitoryReportInterface.loadText()
                InfoBar.success(title='新增成功', content="", isClosable=False, position=InfoBarPosition.TOP, duration=2000, parent=self)
                self.queryStudents()