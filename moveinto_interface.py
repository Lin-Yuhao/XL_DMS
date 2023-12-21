# coding:utf-8
from PyQt6.QtSql import QSqlTableModel, QSqlDatabase, QSqlQuery
from PyQt6.QtCore import Qt, QRegularExpression, QDate
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import QFrame, QHeaderView, QCompleter
from qfluentwidgets import setFont, InfoBarPosition, InfoBar, MessageBox, RoundMenu, Action, MenuAnimationType, \
    CalendarPicker, setCustomStyleSheet
from qfluentwidgets import FluentIcon as FIF
from ..UI.MoveIntoManage import Ui_Frame
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename='oh.log',
                    filemode='a')


class MoveIntoManage(Ui_Frame, QFrame):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.setObjectName('moveintointerface')
        self.scrollAreaWidgetContents.parent().parent().setStyleSheet("background-color: rgba(0,0,0,0);border: none;")

        self.db = QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName('./xldb.db')

        self.__inteWindow()

    def __inteWindow(self):

        # 下拉框初始化
        self.ComboBox_Gender.setPlaceholderText('性别')
        self.ComboBox_Gender.addItems(['男', '女'])
        self.ComboBox_Gender.setCurrentIndex(-1)

        setFont(self.LineEdit_Name, 16)
        setFont(self.LineEdit_Phone, 16)
        setFont(self.SearchLineEdit_Class, 16)
        setFont(self.SearchLineEdit_DormitoryId, 16)
        setFont(self.SearchLineEdit_BedNumber, 16)
        setFont(self.TextEdit_Address, 16)

        # 隐藏搜索按钮
        self.SearchLineEdit_DormitoryId.searchButton.hide()
        self.SearchLineEdit_BedNumber.searchButton.hide()
        self.SearchLineEdit_Class.searchButton.hide()

        # 表格模型
        self.model = QSqlTableModel(self)
        self.model.setTable('students')
        self.queryStudents()
        for section, header in enumerate(
                ['学生姓名', '学生电话', '家长姓名', '家长电话', '性别', '班级', '宿舍号', '', '床位', '入住日期']):
            self.model.setHeaderData(section, Qt.Orientation.Horizontal, header)

        self.TableView.setModel(self.model)
        self.TableView.setColumnWidth(1, 20)
        self.TableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.TableView.setBorderVisible(True)
        self.TableView.verticalHeader().hide()
        self.TableView.setBorderRadius(8)
        self.TableView.hideColumn(7)

        # 表单验证
        chvalidator = QRegularExpressionValidator()
        chvalidator.setRegularExpression(QRegularExpression("^[\u4e00-\u9fa5]{6}"))

        intvalidator = QRegularExpressionValidator()
        intvalidator.setRegularExpression(QRegularExpression("^\d{20}$"))

        # chiintvalidator = QRegularExpressionValidator()
        # chiintvalidator.setRegularExpression(QRegularExpression("^([\u4e00-\u9fa5]|\d){10}$"))

        self.LineEdit_Name.setValidator(chvalidator)
        self.LineEdit_Phone.setValidator(intvalidator)
        self.LineEdit_ParentName.setValidator(chvalidator)
        self.LineEdit_ParentPhone.setValidator(intvalidator)
        self.SearchLineEdit_BedNumber.setValidator(intvalidator)

        self.LineEdit_Name.textChanged.connect(self.queryStudents)
        self.SearchLineEdit_Class.textChanged.connect(self.queryStudents)
        self.SearchLineEdit_DormitoryId.textChanged.connect(self.queryStudents)
        self.SearchLineEdit_DormitoryId.textChanged.connect(lambda: self.bedCompleter(self.SearchLineEdit_DormitoryId.text()))
        self.CalendarPicker_Arrival.dateChanged.connect(self.queryStudents)
        self.PushButton.clicked.connect(self.clearInput)
        self.PrimaryPushButton.clicked.connect(self.addStudent)

        self.TableView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.TableView.customContextMenuRequested.connect(self.showCustomContextMenu)

        self.PrimaryPushButton_2.hide()
        qss = '''
        PushButton{background-color: #E53935; border-color: #E53935; color: #FFFFFF}
        PushButton::hover{background-color: #EF5350; border-color: #EF5350}
        '''
        setCustomStyleSheet(self.PrimaryPushButton_2, qss, qss)

        self.dormitoryCompleter()
        self.classCompleter()
        self.bedCompleter(-1)

    def showCustomContextMenu(self, position):
        index = self.TableView.indexAt(position)
        if not index.isValid():
            return
        menu = RoundMenu(self)
        menu.addActions([Action(FIF.DELETE, '删除'), Action(FIF.EDIT, '修改'), Action(FIF.EMBED, '退宿')])

        if len(self.TableView.selectionModel().selectedRows()) <= 1:
            self.TableView.setCurrentIndex(index)
            menu.actions()[0].triggered.connect(lambda: self.tableViewRemoveRow(index))
        else:
            menu.actions()[0].triggered.connect(
                lambda: self.tableViewRemoveRows(self.TableView.selectionModel().selectedRows()))
        menu.actions()[1].triggered.connect(lambda: self.tableViewEdit(index))
        menu.actions()[2].triggered.connect(lambda: self.moveOut(index))
        menu.exec(self.TableView.mapToGlobal(position), aniType=MenuAnimationType.DROP_DOWN)

    def moveOut(self, index):
        tip = MessageBox(f'学生退宿：{self.model.index(index.row(), 0).data()}', '', self)
        CP = CalendarPicker()
        CP.setText('退宿日期')
        tip.yesButton.setEnabled(not CP.date.isNull())
        CP.dateChanged.connect(lambda: tip.yesButton.setEnabled(not CP.date.isNull()))
        tip.textLayout.addWidget(CP)
        tip.textLayout.setSpacing(25)
        tip.contentLabel.hide()

        if tip.exec():
            logging.info(f'学生退宿 - {self.model.index(index.row(), 0).data()} - {self.model.index(index.row(), 6).data()}')
            self.parent().parent().parent().dormitoryReportInterface.loadText()
            student_id = self.model.index(index.row(), 7).data()
            transfer_query = QSqlQuery()
            transfer_query.prepare("""  
                INSERT INTO students_out (name, phone, parent_name, parent_phone, gender, class, dormitory_id, bed_number, address, arrival_date, check_out_date, stayDays)  
                SELECT name, phone, parent_name, parent_phone, gender, class, dormitory_id, bed_number, address, arrival_date, :check_out_date, :stayDays
                FROM students  
                WHERE id = :student_id;
            """)
            transfer_query.bindValue(":student_id", student_id)
            transfer_query.bindValue(":check_out_date", CP.date.toString("yyyy-MM-dd"))
            stayDays = self.model.index(index.row(), 9).data()
            qDateStayDays = QDate.fromString(stayDays, Qt.DateFormat.ISODate).daysTo(CP.getDate())
            transfer_query.bindValue(":stayDays", qDateStayDays)

            if transfer_query.exec():
                delete_query = QSqlQuery()
                delete_query.prepare("DELETE FROM students WHERE id = :student_id;")
                delete_query.bindValue(":student_id", student_id)
                if delete_query.exec():
                    self.updateNumStudents(index.model().index(index.row(), 6).data())
                    self.clearInput()
                    moveOutInterface = self.parent().parent().parent().moveOutInterface
                    self.parent().parent().parent().switchTo(moveOutInterface)
                    moveOutInterface.queryStudents()
        self.model.submitAll()
        self.model.select()

    def tableViewEdit(self, index):
        query = QSqlQuery(self.db)
        querydata = []
        query.prepare(
            "SELECT name, gender, phone, parent_name, parent_phone, class, dormitory_id, bed_number, address, arrival_date, id FROM students WHERE id = ?")
        query.addBindValue(self.model.index(index.row(), 7).data())
        if query.exec():
            query.next()
            for i in range(query.record().count()):
                querydata.append(query.value(i))
        self.LineEdit_Name.setText(querydata[0])
        if querydata[1] == '男':
            self.ComboBox_Gender.setCurrentIndex(0)
        else:
            self.ComboBox_Gender.setCurrentIndex(1)
        self.LineEdit_Phone.setText(querydata[2])
        self.LineEdit_ParentName.setText(querydata[3])
        self.LineEdit_ParentPhone.setText(querydata[4])
        self.SearchLineEdit_Class.setText(querydata[5])
        self.SearchLineEdit_DormitoryId.setText(str(querydata[6]))
        self.SearchLineEdit_BedNumber.setText(str(querydata[7]))
        if not querydata[8] == '':
            self.TextEdit_Address.setPlainText(querydata[8])
        self.CalendarPicker_Arrival.setDate(QDate.fromString(querydata[9], "yyyy-MM-dd"))
        if not self.PrimaryPushButton.isHidden():
            self.PrimaryPushButton.hide()
        if self.PrimaryPushButton_2.isHidden():
            self.PrimaryPushButton_2.show()
        self.PrimaryPushButton_2.disconnect()
        self.PrimaryPushButton_2.clicked.connect(lambda: self.updateStudents(querydata[6], querydata[10]))

    def updateStudents(self, old_value, students_id):
        tip = MessageBox('修改学生数据', '', self)
        tip.contentLabel.hide()
        if tip.exec():
            update_query = QSqlQuery(self.db)
            update_query.prepare('''
                                    UPDATE students
                                    SET name = :name,
                                    gender = :gender,
                                    phone = :phone,
                                    parent_name = :parent_name,
                                    parent_phone = :parent_phone,
                                    class = :class,
                                    dormitory_id = :dormitory_id,
                                    bed_number = :bed_number,
                                    address = :address,
                                    arrival_date = :arrival_date
                                    WHERE id = :students_id
                                ''')
            update_query.bindValue(":name", self.LineEdit_Name.text())
            update_query.bindValue(":gender", self.ComboBox_Gender.text())
            update_query.bindValue(":phone", self.LineEdit_Phone.text())
            update_query.bindValue(":parent_name", self.LineEdit_ParentName.text())
            update_query.bindValue(":parent_phone", self.LineEdit_ParentPhone.text())
            update_query.bindValue(":class", self.SearchLineEdit_Class.text())
            update_query.bindValue(":dormitory_id", self.SearchLineEdit_DormitoryId.text())
            update_query.bindValue(":bed_number", self.SearchLineEdit_BedNumber.text())
            update_query.bindValue(":address", self.TextEdit_Address.toPlainText())
            update_query.bindValue(":arrival_date", self.CalendarPicker_Arrival.text())
            update_query.bindValue(":students_id", students_id)
            if update_query.exec():
                self.model.select()
                self.updateNumStudents(self.SearchLineEdit_DormitoryId.text())
                self.updateNumStudents(old_value)
                logging.info(f'学生修改-{self.LineEdit_Name.text()}-{self.SearchLineEdit_DormitoryId.text()}')
                self.parent().parent().parent().dormitoryReportInterface.loadText()
                self.clearInput()
                InfoBar.success(title='更新成功', content="", isClosable=False, position=InfoBarPosition.TOP,
                                duration=4000, parent=self)
            else:
                InfoBar.error(title='更新失败', content="", isClosable=False, position=InfoBarPosition.TOP,
                              duration=4000, parent=self)

    def tableViewRemoveRow(self, index):
        tip = MessageBox(f'学生删除：{self.model.index(index.row(), 0).data()}', '', self)
        tip.contentLabel.hide()
        if tip.exec():
            logging.info(f'学生删除 - {self.model.index(index.row(), 6).data()} - {self.model.index(index.row(), 0).data()}')
            self.parent().parent().parent().dormitoryReportInterface.loadText()
            dormitory_name = index.model().index(index.row(), 6).data()
            self.model.removeRow(index.row())
            self.model.submitAll()
            self.model.select()
            self.updateNumStudents(dormitory_name)
            self.clearInput()
            InfoBar.success(title='删除成功', content="", isClosable=False, position=InfoBarPosition.TOP, duration=2000,
                            parent=self)

    def tableViewRemoveRows(self, index):
        tip = MessageBox('删除多行', '', self)
        tip.contentLabel.hide()
        if tip.exec():
            dormitory_name = []
            for i in index:
                logging.info(f'学生删除 - {self.model.index(i.row(), 0).data()} - {self.model.index(i.row(), 6).data()}')
                self.parent().parent().parent().dormitoryReportInterface.loadText()
                dormitory_name.append(i.model().index(i.row(), 4).data())
                self.model.removeRow(i.row())
            dormitory_name = list(set(dormitory_name))
            for d in dormitory_name:
                self.updateNumStudents(d)
            self.model.submitAll()
            self.model.select()
            self.clearInput()
            InfoBar.success(title='删除成功', content="", isClosable=False, position=InfoBarPosition.TOP, duration=2000,
                            parent=self)

    def bedCompleter(self, dormitory_name):
        query = QSqlQuery(self.db)
        querydata = []
        bedNub = 0
        query.prepare('''
                        SELECT   
                            d.dormitory_name,
                            d.bed_number,
                            s.bed_number AS bound_bed_number
                        FROM   
                            dormitories AS d   
                        JOIN   
                            students AS s ON d.dormitory_name = s.dormitory_id
                        WHERE   
                            d.dormitory_name = :dormitory_name
                    ''')
        query.bindValue(":dormitory_name", dormitory_name)
        if query.exec():
            while query.next():
                querydata.append(str(query.value(2)))

        query.prepare("SELECT bed_number FROM dormitories WHERE dormitory_name = :dormitory_name")
        query.bindValue(":dormitory_name", dormitory_name)
        if query.exec():
            while query.next():
                bedNub = query.value(0)

        filtered_numbers = [str(num) for num in list(range(1, bedNub + 1)) if str(num) not in querydata]
        completer = QCompleter(filtered_numbers, self.SearchLineEdit_BedNumber)
        self.SearchLineEdit_BedNumber.setCompleter(completer)

        regex = QRegularExpression('|'.join(filtered_numbers))
        validator = QRegularExpressionValidator(regex, self.SearchLineEdit_BedNumber)
        self.SearchLineEdit_BedNumber.setValidator(validator)

        self.SearchLineEdit_BedNumber.clear()
        if not filtered_numbers:
            self.SearchLineEdit_BedNumber.setEnabled(False)
        else:
            self.SearchLineEdit_BedNumber.setEnabled(True)


    def classCompleter(self):
        query = QSqlQuery(self.db)
        querydata = []
        if query.exec("SELECT DISTINCT class FROM students"):
            while query.next():
                querydata.append(str(query.value(0)))
        completer = QCompleter(querydata, self.SearchLineEdit_Class)
        self.SearchLineEdit_Class.setCompleter(completer)

        # regex = QRegularExpression('|'.join(querydata))
        # validator = QRegularExpressionValidator(regex, self.SearchLineEdit_Class)
        # self.SearchLineEdit_Class.setValidator(validator)

    def dormitoryCompleter(self):
        query = QSqlQuery(self.db)
        querydata = []
        if query.exec("SELECT dormitory_name FROM dormitories"):
            while query.next():
                querydata.append(str(query.value(0)))
        completer = QCompleter(querydata, self.SearchLineEdit_DormitoryId)
        self.SearchLineEdit_DormitoryId.setCompleter(completer)

        if len(querydata) > 0:
            regex = QRegularExpression('|'.join(querydata))
            validator = QRegularExpressionValidator(regex, self.SearchLineEdit_DormitoryId)
            self.SearchLineEdit_DormitoryId.setValidator(validator)
            self.SearchLineEdit_DormitoryId.setEnabled(True)
        else:
            self.SearchLineEdit_DormitoryId.setEnabled(False)

    def clearInput(self):
        self.LineEdit_Name.clear()
        self.SearchLineEdit_Class.clear()
        self.LineEdit_Phone.clear()
        self.ComboBox_Gender.setCurrentIndex(-1)
        self.TextEdit_Address.clear()
        self.SearchLineEdit_DormitoryId.setText('')
        self.SearchLineEdit_BedNumber.setText('')

        # 替换时间控件
        CalendarPicker_Casual = CalendarPicker()
        self.SimpleCardWidget.layout().replaceWidget(self.CalendarPicker_Arrival, CalendarPicker_Casual)
        self.CalendarPicker_Arrival.deleteLater()
        self.CalendarPicker_Arrival = CalendarPicker_Casual
        self.CalendarPicker_Arrival.setText('入住日期')
        self.CalendarPicker_Arrival.dateChanged.connect(self.queryStudents)
        self.queryStudents()

        self.PrimaryPushButton.show()
        self.PrimaryPushButton_2.hide()

    def queryStudents(self):
        query = QSqlQuery(self.db)
        query.prepare("""
                    SELECT name, phone, parent_name, parent_phone, gender, class, dormitory_id, id, bed_number, arrival_date
                    FROM students
                    WHERE name LIKE :name
                    AND class LIKE :class
                    AND dormitory_id LIKE :dormitory_id
                    AND arrival_date LIKE :arrival_date
        """)
        query.bindValue(":name", f'%{self.LineEdit_Name.text()}%')
        query.bindValue(":class", f'%{self.SearchLineEdit_Class.text()}%')
        query.bindValue(":dormitory_id", f'%{self.SearchLineEdit_DormitoryId.text()}%')
        query.bindValue(":arrival_date", f'%{self.CalendarPicker_Arrival.date.toString("yyyy-MM-dd")}%')
        if query.exec():
            self.model.setQuery(query)
            self.TableView.resizeRowsToContents()

    def addStudent(self):
        if not self.LineEdit_Name.text():
            InfoBar.error(title='姓名必填', content="", isClosable=False, position=InfoBarPosition.TOP, duration=2000,
                          parent=self)
            return
        elif self.ComboBox_Gender.currentIndex() == -1:
            InfoBar.error(title='性别必填', content="", isClosable=False, position=InfoBarPosition.TOP, duration=2000,
                          parent=self)
            return
        elif not self.SearchLineEdit_DormitoryId.text():
            InfoBar.error(title='宿舍号必填', content="", isClosable=False, position=InfoBarPosition.TOP, duration=2000,
                          parent=self)
            return
        elif not self.CalendarPicker_Arrival.getDate().toString("yyyy-MM-dd"):
            InfoBar.error(title='入住日期必填', content="", isClosable=False, position=InfoBarPosition.TOP,
                          duration=2000, parent=self)
            return

        tip = MessageBox('添加学生', '', self)
        tip.contentLabel.hide()
        if tip.exec():
            query = QSqlQuery(self.db)
            query.prepare('''
                    INSERT INTO students (name, phone, parent_name, parent_phone, gender, class, dormitory_id, bed_number, address, arrival_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''')
            query.addBindValue(self.LineEdit_Name.text())
            query.addBindValue(self.LineEdit_Phone.text())
            query.addBindValue(self.LineEdit_ParentName.text())
            query.addBindValue(self.LineEdit_ParentPhone.text())
            query.addBindValue(self.ComboBox_Gender.text())
            query.addBindValue(self.SearchLineEdit_Class.text())
            query.addBindValue(self.SearchLineEdit_DormitoryId.text())
            query.addBindValue(self.SearchLineEdit_BedNumber.text())
            query.addBindValue(self.TextEdit_Address.toPlainText())
            query.addBindValue(self.CalendarPicker_Arrival.text())

            if query.exec():
                InfoBar.success(title='添加成功', content="", isClosable=False, position=InfoBarPosition.TOP,
                                duration=2000, parent=self)
                logging.info(f'学生添加 - {self.LineEdit_Name.text()} - {self.SearchLineEdit_DormitoryId.text()}')
                self.parent().parent().parent().dormitoryReportInterface.loadText()
                self.updateNumStudents(self.SearchLineEdit_DormitoryId.text())
                self.queryStudents()
                self.clearInput()
                self.classCompleter()
            else:
                InfoBar.warning(title='添加失败', content="", isClosable=False, position=InfoBarPosition.TOP,
                                duration=4000, parent=self)
                self.queryStudents()

    def updateNumStudents(self, dormitory_name):
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
        update_query.addBindValue(dormitory_name)
        if update_query.exec():
            dormitoryManageInterface = self.parent().parent().parent().dormitoryManageInterface
            dormitoryManageInterface.iconView.initWidget()
        else:
            InfoBar.warning(title='更新宿舍学生数量失败', content="", isClosable=False, position=InfoBarPosition.TOP,
                            duration=4000, parent=self)
