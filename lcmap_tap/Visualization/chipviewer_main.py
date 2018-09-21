# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ChipViewer_main.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!
import pkg_resources
from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow_chipviewer(object):
    def setupUi(self, MainWindow_chipviewer):
        MainWindow_chipviewer.setObjectName("MainWindow_chipviewer")
        MainWindow_chipviewer.resize(653, 757)

        icon = QtGui.QIcon(QtGui.QPixmap(pkg_resources.resource_filename("lcmap_tap",
                                                                         "/".join(("Auxiliary", "icon.PNG")))))
        MainWindow_chipviewer.setWindowIcon(icon)

        self.Widget_central = QtWidgets.QWidget(MainWindow_chipviewer)
        self.Widget_central.setObjectName("Widget_central")
        self.gridLayout = QtWidgets.QGridLayout(self.Widget_central)
        self.gridLayout.setObjectName("gridLayout")
        self.ScrollArea_viewer = QtWidgets.QScrollArea(self.Widget_central)
        self.ScrollArea_viewer.setWidgetResizable(True)
        self.ScrollArea_viewer.setObjectName("ScrollArea_viewer")
        self.Widget_ScrollAreaContents = QtWidgets.QWidget()
        self.Widget_ScrollAreaContents.setGeometry(QtCore.QRect(0, 0, 633, 612))
        self.Widget_ScrollAreaContents.setObjectName("Widget_ScrollAreaContents")
        self.ScrollArea_viewer.setWidget(self.Widget_ScrollAreaContents)
        self.gridLayout.addWidget(self.ScrollArea_viewer, 0, 0, 1, 1)
        self.HBoxLayout_controls = QtWidgets.QHBoxLayout()
        self.HBoxLayout_controls.setObjectName("HBoxLayout_controls")
        self.VBoxLayout_enable = QtWidgets.QVBoxLayout()
        self.VBoxLayout_enable.setObjectName("VBoxLayout_enable")
        self.RadioButton_plot = QtWidgets.QRadioButton(self.Widget_central)
        self.RadioButton_plot.setObjectName("RadioButton_plot")
        self.VBoxLayout_enable.addWidget(self.RadioButton_plot)
        self.QLable_rightclick = QtWidgets.QLabel(self.Widget_central)
        self.QLable_rightclick.setObjectName("QLable_rightclick")
        self.VBoxLayout_enable.addWidget(self.QLable_rightclick, 0, QtCore.Qt.AlignLeft)
        self.QLabel_leftclick = QtWidgets.QLabel(self.Widget_central)
        self.QLabel_leftclick.setObjectName("QLabel_leftclick")
        self.VBoxLayout_enable.addWidget(self.QLabel_leftclick, 0, QtCore.Qt.AlignLeft)
        self.QLabel_zoom = QtWidgets.QLabel(self.Widget_central)
        self.QLabel_zoom.setObjectName("QLabel_zoom")
        self.VBoxLayout_enable.addWidget(self.QLabel_zoom, 0, QtCore.Qt.AlignLeft)
        self.HBoxLayout_controls.addLayout(self.VBoxLayout_enable)
        self.VBoxLayout_update = QtWidgets.QVBoxLayout()
        self.VBoxLayout_update.setObjectName("VBoxLayout_update")
        self.PushButton_update = QtWidgets.QPushButton(self.Widget_central)
        self.PushButton_update.setMinimumSize(QtCore.QSize(100, 0))
        self.PushButton_update.setMaximumSize(QtCore.QSize(100, 16777215))
        self.PushButton_update.setObjectName("PushButton_update")
        self.VBoxLayout_update.addWidget(self.PushButton_update, 0, QtCore.Qt.AlignHCenter)
        self.HBoxLayout_controls.addLayout(self.VBoxLayout_update)
        self.VBoxLayout_zoom = QtWidgets.QVBoxLayout()
        self.VBoxLayout_zoom.setObjectName("VBoxLayout_zoom")
        self.PushButton_zoom = QtWidgets.QPushButton(self.Widget_central)
        self.PushButton_zoom.setMinimumSize(QtCore.QSize(100, 0))
        self.PushButton_zoom.setMaximumSize(QtCore.QSize(100, 16777215))
        self.PushButton_zoom.setObjectName("PushButton_zoom")
        self.VBoxLayout_zoom.addWidget(self.PushButton_zoom, 0, QtCore.Qt.AlignHCenter)
        self.HBoxLayout_controls.addLayout(self.VBoxLayout_zoom)
        self.gridLayout.addLayout(self.HBoxLayout_controls, 1, 0, 1, 1)
        MainWindow_chipviewer.setCentralWidget(self.Widget_central)
        self.menubar = QtWidgets.QMenuBar(MainWindow_chipviewer)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 653, 21))
        self.menubar.setObjectName("menubar")
        MainWindow_chipviewer.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow_chipviewer)
        self.statusbar.setObjectName("statusbar")
        MainWindow_chipviewer.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow_chipviewer)
        QtCore.QMetaObject.connectSlotsByName(MainWindow_chipviewer)

    def retranslateUi(self, MainWindow_chipviewer):
        _translate = QtCore.QCoreApplication.translate
        MainWindow_chipviewer.setWindowTitle(_translate("MainWindow_chipviewer", "ARD Viewer"))
        self.RadioButton_plot.setText(_translate("MainWindow_chipviewer", "Enable Plot on Click"))
        self.QLable_rightclick.setText(_translate("MainWindow_chipviewer", "Right Click - Toggle Pan On/Off"))
        self.QLabel_leftclick.setText(_translate("MainWindow_chipviewer", "Left Click - Return Point Location"))
        self.QLabel_zoom.setText(_translate("MainWindow_chipviewer", "Wheel  - Zoom In/Out"))
        self.PushButton_update.setText(_translate("MainWindow_chipviewer", "Update"))
        self.PushButton_zoom.setText(_translate("MainWindow_chipviewer", "Zoom to Point"))

