# coding:utf-8
from PyQt6.QtSql import QSqlTableModel, QSqlDatabase, QSqlQuery
from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import QFrame, QHeaderView
from qfluentwidgets import setFont, InfoBarPosition, InfoBar, MessageBox, CalendarPicker
from qfluentwidgets import FluentIcon as FIF
from ..UI.MoveOutManage import Ui_Frame


class MoveOutManage(Ui_Frame, QFrame):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.setObjectName('moveoutinterface')
        self.scrollAreaWidgetContents.parent().parent().setStyleSheet("background-color: rgba(0,0,0,0);border: none;")

        self.db = QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName('./xldb.db')

        self.__inteWindow()

    def __inteWindow(self):
        setFont(self.SearchLineEdit_Name, 16)
        setFont(self.SearchLineEdit_Dormitory, 16)
        setFont(self.CalendarPicker, 16)

        # 表格模型
        self.model = QSqlTableModel(self)
        self.model.setTable('students_out')
        self.queryStudents()
        for section, header in enumerate(['学生姓名', '学生电话', '家长姓名', '家长电话', '班级', '宿舍号', '', '入住日期', '退宿日期', '入住天数']):
            self.model.setHeaderData(section, Qt.Orientation.Horizontal, header)

        self.TableView.setModel(self.model)
        self.TableView.setColumnWidth(1, 20)
        self.TableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.TableView.setBorderVisible(True)
        self.TableView.verticalHeader().hide()
        self.TableView.setBorderRadius(8)
        self.TableView.hideColumn(6)

        # 表单验证
        chvalidator = QRegularExpressionValidator()
        regex = QRegularExpression("^[\u4e00-\u9fa5]{6}")
        chvalidator.setRegularExpression(regex)

        intvalidator = QRegularExpressionValidator()
        regex = QRegularExpression("^\d{20}$")
        intvalidator.setRegularExpression(regex)

        chiintvalidator = QRegularExpressionValidator()
        regex = QRegularExpression("^([\u4e00-\u9fa5]|\d){10}$")
        chiintvalidator.setRegularExpression(regex)

        self.SearchLineEdit_Name.setValidator(chvalidator)
        self.SearchLineEdit_Class.setValidator(chiintvalidator)
        self.SearchLineEdit_Dormitory.setValidator(intvalidator)
        self.PrimaryPushButton.clicked.connect(self.clearInput)

        self.SearchLineEdit_Name.textChanged.connect(self.queryStudents)
        self.SearchLineEdit_Class.textChanged.connect(self.queryStudents)
        self.SearchLineEdit_Dormitory.textChanged.connect(self.queryStudents)
        self.CalendarPicker.dateChanged.connect(self.queryStudents)

    #     self.TableView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    #     self.TableView.customContextMenuRequested.connect(self.showCustomContextMenu)
    #
    # def showCustomContextMenu(self, position):
    #     index = self.TableView.indexAt(position)
    #     if not index.isValid(): return
    #
    #     menu = RoundMenu(self)
    #     menu.addActions([Action(FIF.ADD_TO, '入住')])
    #     self.TableView.setCurrentIndex(index)
    #     menu.actions()[0].triggered.connect(lambda: self.moveInto(index))
    #     menu.exec(self.TableView.mapToGlobal(position), aniType=MenuAnimationType.DROP_DOWN)

    def moveInto(self, index):
        """ transfer -> delete -> update """
        tip = MessageBox('学生入住', '', self)
        tip.contentLabel.hide()
        if tip.exec():
            student_id = self.model.index(index.row(), 6).data()
            transfer_query = QSqlQuery()
            transfer_query.prepare("""
                        INSERT INTO students (name, phone, gender, class, dormitory_id, bed_number, address, arrival_date)
                        SELECT name, phone, gender, class, dormitory_id, bed_number, address, arrival_date
                        FROM students_out
                        WHERE id = :student_id;
                    """)
            transfer_query.bindValue(":student_id", student_id)
            if transfer_query.exec():
                delete_query = QSqlQuery()
                delete_query.prepare("DELETE FROM students_out WHERE id = :student_id;")
                delete_query.bindValue(":student_id", student_id)
                if delete_query.exec():
                    update_query = QSqlQuery(self.db)
                    update_query.prepare('''
                                            UPDATE dormitories
                                            SET num_students = COALESCE((
                                                SELECT COUNT(*)
                                                FROM students
                                                WHERE students.dormitory_id = dormitories.dormitory_name
                                            ), 0)
                                            WHERE dormitory_name = ?
                                        ''')
                    update_query.addBindValue(index.model().index(index.row(), 3).data())
                    if update_query.exec():
                        dormitoryManageInterface = self.parent().parent().parent().dormitoryManageInterface
                        dormitoryManageInterface.iconView.initWidget()
                    else:
                        InfoBar.warning(title='更新宿舍学生数量失败', content="", isClosable=False,
                                        position=InfoBarPosition.TOP, duration=4000, parent=self)
                    moveIntoInterface = self.parent().parent().parent().moveIntoInterface
                    self.parent().parent().parent().switchTo(moveIntoInterface)
                    moveIntoInterface.queryStudents()
        self.model.submitAll()
        self.model.select()

    def clearInput(self):
        self.SearchLineEdit_Name.clear()
        self.SearchLineEdit_Class.clear()
        self.SearchLineEdit_Dormitory.clear()
        CalendarPicker_Casual = CalendarPicker()
        self.SimpleCardWidget.layout().replaceWidget(self.CalendarPicker, CalendarPicker_Casual)
        self.CalendarPicker.deleteLater()
        self.CalendarPicker = CalendarPicker_Casual
        self.CalendarPicker.setText('退宿日期')
        self.CalendarPicker.dateChanged.connect(self.queryStudents)
        self.queryStudents()

    def queryStudents(self):
        query = QSqlQuery(self.db)
        query.prepare("""
                    SELECT name, phone, parent_name, parent_phone, class, dormitory_id, id, arrival_date, check_out_date, stayDays
                    FROM students_out
                    WHERE name LIKE :name
                    AND class LIKE :class
                    AND dormitory_id LIKE :dormitory_id
                    AND check_out_date LIKE :check_out_date
        """)
        query.bindValue(":name", f'%{self.SearchLineEdit_Name.text()}%')
        query.bindValue(":class", f'%{self.SearchLineEdit_Class.text()}%')
        query.bindValue(":dormitory_id", f'%{self.SearchLineEdit_Dormitory.text()}%')
        query.bindValue(":check_out_date", f'%{self.CalendarPicker.date.toString("yyyy-MM-dd")}%')
        if query.exec():
            self.model.setQuery(query)
            self.TableView.resizeRowsToContents()

