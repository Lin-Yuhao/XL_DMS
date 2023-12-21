# coding: utf-8
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QApplication, QFrame, QHBoxLayout
from qfluentwidgets import NavigationItemPosition, FluentWindow, SplashScreen, SubtitleLabel, setFont
from qfluentwidgets import FluentIcon as FIF
from .dormitory_interface import DormitoryManage
from .moveinto_interface import MoveIntoManage
from .moveout_interface import MoveOutManage
from .report_interface import ReportInterface
from .repair_interface_2 import RepairManage
from .setting_interface import SettingInterface
from ..common.config import cfg
from ..common.icon import Icon
from ..common.signal_bus import signalBus
from ..common.translator import Translator
from ..common import resource


class Widget(QFrame):
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = SubtitleLabel(text, self)
        self.hBoxLayout = QHBoxLayout(self)
        setFont(self.label, 24)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignmentFlag.AlignCenter)
        self.setObjectName(text.replace(' ', '-'))


class MainWindow(FluentWindow):

    def __init__(self):
        super().__init__()
        self.initWindow()

        self.dormitoryManageInterface = DormitoryManage(self)
        self.moveIntoInterface = MoveIntoManage(self)
        self.moveOutInterface = MoveOutManage(self)
        self.dormitoryReportInterface = ReportInterface(self)
        self.repairManageInterface = RepairManage()
        self.settingInterface = SettingInterface(self)

        self.navigationInterface.setAcrylicEnabled(True)
        self.navigationInterface.setExpandWidth(130)

        self.connectSignalToSlot()
        self.initNavigation()
        self.splashScreen.finish()

    def connectSignalToSlot(self):
        signalBus.micaEnableChanged.connect(self.setMicaEffectEnabled)
        # signalBus.switchToSampleCard.connect(self.switchToSample)

    def initNavigation(self):
        t = Translator()
        self.addSubInterface(self.moveIntoInterface, FIF.PEOPLE, self.tr('入住管理'))
        self.addSubInterface(self.moveOutInterface, FIF.EMBED, self.tr('退宿管理'))
        self.addSubInterface(self.repairManageInterface, FIF.BRUSH, self.tr('维修管理'))
        self.navigationInterface.addSeparator()
        self.addSubInterface(self.dormitoryManageInterface, FIF.HOME, self.tr('宿舍管理'))
        self.addSubInterface(self.dormitoryReportInterface, FIF.PIE_SINGLE, self.tr('宿舍报表'))
        self.addSubInterface(self.settingInterface, FIF.SETTING, self.tr('设置'), NavigationItemPosition.BOTTOM)

    def initWindow(self):
        self.resize(900, 600)
        self.setMinimumWidth(760)
        self.setWindowTitle('新龙中学宿舍管理系统')

        self.setMicaEffectEnabled(cfg.get(cfg.micaEnabled))
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(106, 106))
        self.splashScreen.raise_()

        desktop = QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)
        self.show()
        QApplication.processEvents()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, 'splashScreen'):
            self.splashScreen.resize(self.size())