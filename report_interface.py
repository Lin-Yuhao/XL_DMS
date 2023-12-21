# coding:utf-8
from PyQt6.QtSql import QSqlDatabase, QSqlQuery
from PyQt6.QtCore import Qt, QFile
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtWidgets import QFrame, QMessageBox, QFileDialog
from openpyxl.styles import Font, Side, Border, Alignment, PatternFill
from qfluentwidgets import FlowLayout, PushButton, MessageBox
from qfluentwidgets import FluentIcon as FIF
from ..UI.DormitoryReport import Ui_Frame
from openpyxl import Workbook


class ReportInterface(Ui_Frame, QFrame):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.setObjectName('reportinterface')
        self.scrollAreaWidgetContents.parent().parent().setStyleSheet("background-color: rgba(0,0,0,0);border: none;")

        self.db = QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName('./xldb.db')
        if not self.db.open():
            QMessageBox.critical(self, 'Database Connection', self.db.lastError().text())

        self.flowLayout = FlowLayout(self.SimpleCardWidget_2, needAni=False)

        studentForm = PushButton(self)
        studentForm.setText('导出学生列表')
        studentForm.clicked.connect(self.__onStudentForm)

        # bedListForm = PushButton(self)
        # bedListForm.setText('导出宿舍列表')
        # bedListForm.clicked.connect(self.__onBedListForm)

        self.flowLayout.addWidget(studentForm)
        # self.flowLayout.addWidget(bedListForm)

        self.__inteWindow()

    def __onStudentForm(self):
        folder = QFileDialog.getSaveFileName(self, "文件保存", "./app/download/学生列表", "Excel工作簿 (*.xlsx)")
        if folder[0] != '':
            query = QSqlQuery(self.db)
            wb = Workbook()
            ws = wb.active

            ws.column_dimensions['A'].width = 8
            ws.column_dimensions['B'].width = 20
            ws.column_dimensions['C'].width = 25
            ws.column_dimensions['D'].width = 20
            ws.column_dimensions['E'].width = 25
            ws.column_dimensions['F'].width = 8
            ws.column_dimensions['G'].width = 12
            ws.column_dimensions['H'].width = 12
            ws.column_dimensions['I'].width = 12
            ws.column_dimensions['J'].width = 25
            ws.column_dimensions['K'].width = 15

            ws.merge_cells('A1:K1')
            ws.append(["序号", "学生姓名", "学生电话", "家长姓名", "家长电话", "性别", "班级", "宿舍号", "床位", "地址", "入住日期"])

            if query.exec("SELECT * FROM students"):
                while query.next():
                    ws.append([query.value("id"),
                               query.value("name"),
                               query.value("phone"),
                               query.value("parent_name"),
                               query.value("parent_phone"),
                               query.value("gender"),
                               query.value("class"),
                               query.value("dormitory_id"),
                               query.value("bed_number"),
                               query.value("address"),
                               query.value("arrival_date")])

            for row in ws.iter_rows():
                for cell in row:
                    cell.font = Font(name='Calibri', size=14, bold=True)
                    cell.alignment = Alignment(horizontal='center', vertical='center')
                    cell.border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
                    cell.fill = PatternFill(start_color='FFFF00', end_color='FFFF00', fill_type='solid')
            ws['A1'] = '花名册'
            ws['A1'].font = Font(name='Calibri', size=28, bold=True)
            ws.row_dimensions[1].height = 50

            try:
                wb.save(folder[0])
            except:
                while True:
                    w = MessageBox('文件无法处理', '请关闭文件后重试', self)
                    w.yesButton.setText('重试')
                    if w.exec():
                        try:
                            wb.save(folder[0])
                            break
                        except:
                            w.exec()
                    else:
                        break

    def __onBedListForm(self):
        folder = QFileDialog.getSaveFileName(self, "文件保存", "床位列表", "Excel工作簿 (*.xlsx)")
        if folder[0] != '':
            query = QSqlQuery(self.db)
            wb = Workbook()
            ws = wb.active
            if query.exec("SELECT * FROM students"):
                while query.next():
                    ws.append([query.value("id"),
                               query.value("name"),
                               query.value("phone"),
                               query.value("parent_name"),
                               query.value("parent_phone"),
                               query.value("gender"),
                               query.value("class"),
                               query.value("dormitory_id"),
                               query.value("bed_number"),
                               query.value("address"),
                               query.value("arrival_date")])

            for row in ws.iter_rows():
                for cell in row:
                    cell.font = Font(name='Calibri', size=14, bold=True)
                    cell.alignment = Alignment(horizontal='center', vertical='center')
                    cell.border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
                    cell.fill = PatternFill(start_color='FFFF00', end_color='FFFF00', fill_type='solid')
            ws['A1'] = '花名册'
            ws['A1'].font = Font(name='Calibri', size=28, bold=True)
            ws.row_dimensions[1].height = 50

            try:
                wb.save(folder[0])
            except:
                while True:
                    w = MessageBox('文件无法处理', '请关闭文件后重试', self)
                    w.yesButton.setText('重试')
                    if w.exec():
                        try:
                            wb.save(folder[0])
                            break
                        except:
                            w.exec()
                    else:
                        break

    def __inteWindow(self):
        self.PixmapLabel_Room.setPixmap(QPixmap(':/gallery/images/Room.png').scaled(
            50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.PixmapLabel_Bed.setPixmap(QPixmap(':/gallery/images/Bed.png').scaled(
            50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.PixmapLabel_Personnel.setPixmap(QPixmap(':/gallery/images/Student.png').scaled(
            50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.PixmapLabel_Vacant.setPixmap(QPixmap(':/gallery/images/None.png').scaled(
            50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

        dcolor = QColor(127, 127, 127)
        self.TitleLabel_Room.setTextColor(dcolor, dcolor)
        self.TitleLabel_Bed.setTextColor(dcolor, dcolor)
        self.TitleLabel_Personnel.setTextColor(dcolor, dcolor)
        self.TitleLabel_Vacant.setTextColor(dcolor, dcolor)

        self.updateReport()
        self.loadText()

    def updateReport(self):
        query = QSqlQuery(self.db)

        if query.exec("SELECT COUNT(*) FROM students;"):
            query.next()
            self.TitleLabel_PersonnelNub.setText(str(query.value(0)))

        if query.exec("SELECT COUNT(*) FROM dormitories;"):
            query.next()
            self.TitleLabel_RoomNub.setText(str(query.value(0)))

        if query.exec("SELECT SUM(bed_number) FROM dormitories;"):
            query.next()
            if query.value(0) != '':
                self.TitleLabel_BedNub.setText(str(query.value(0)))
            else:
                self.TitleLabel_BedNub.setText('0')

        if query.exec("SELECT COUNT(*) FROM students WHERE dormitory_id IS NULL OR dormitory_id = ''"):
            query.next()
            Occupancy = int(self.TitleLabel_PersonnelNub.text()) - int(query.value(0))
            if self.TitleLabel_BedNub.text() != '' and int(self.TitleLabel_BedNub.text()) > Occupancy:
                self.TitleLabel_VacantNub.setText(str(int(self.TitleLabel_BedNub.text()) - Occupancy))
            else:
                self.TitleLabel_VacantNub.setText('0')

    def loadText(self):
        self.updateReport()
        file = QFile('oh.log')
        if file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
            content = file.readAll()
            self.StrongBodyLabel.setText(str(content, 'gbk'))
        else:
            print('Failed to open file')
