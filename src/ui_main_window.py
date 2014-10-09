# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'main_window.ui'
#
# Created: Fri Oct 10 00:03:26 2014
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.central_widget = QtGui.QWidget(MainWindow)
        self.central_widget.setObjectName("central_widget")
        self.verticalLayout = QtGui.QVBoxLayout(self.central_widget)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tab_widget = QtGui.QTabWidget(self.central_widget)
        self.tab_widget.setTabShape(QtGui.QTabWidget.Rounded)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setObjectName("tab_widget")
        self.verticalLayout.addWidget(self.tab_widget)
        MainWindow.setCentralWidget(self.central_widget)
        self.menu_bar = QtGui.QMenuBar(MainWindow)
        self.menu_bar.setGeometry(QtCore.QRect(0, 0, 800, 21))
        self.menu_bar.setObjectName("menu_bar")
        self.menu_file = QtGui.QMenu(self.menu_bar)
        self.menu_file.setObjectName("menu_file")
        self.menu_view = QtGui.QMenu(self.menu_bar)
        self.menu_view.setObjectName("menu_view")
        self.menu_edit = QtGui.QMenu(self.menu_bar)
        self.menu_edit.setObjectName("menu_edit")
        MainWindow.setMenuBar(self.menu_bar)
        self.status_bar = QtGui.QStatusBar(MainWindow)
        self.status_bar.setObjectName("status_bar")
        MainWindow.setStatusBar(self.status_bar)
        self.tool_bar = QtGui.QToolBar(MainWindow)
        self.tool_bar.setObjectName("tool_bar")
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.tool_bar)
        self.history_dock_widget = QtGui.QDockWidget(MainWindow)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.history_dock_widget.sizePolicy().hasHeightForWidth())
        self.history_dock_widget.setSizePolicy(sizePolicy)
        self.history_dock_widget.setMinimumSize(QtCore.QSize(176, 300))
        self.history_dock_widget.setFloating(True)
        self.history_dock_widget.setObjectName("history_dock_widget")
        self.history_widget = QtGui.QWidget()
        self.history_widget.setObjectName("history_widget")
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.history_widget)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.action_stack_view = ActionStackView(self.history_widget)
        self.action_stack_view.setObjectName("action_stack_view")
        self.verticalLayout_2.addWidget(self.action_stack_view)
        self.history_dock_widget.setWidget(self.history_widget)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(2), self.history_dock_widget)
        self.action_exit = QtGui.QAction(MainWindow)
        self.action_exit.setObjectName("action_exit")
        self.action_redo = QtGui.QAction(MainWindow)
        self.action_redo.setEnabled(False)
        self.action_redo.setObjectName("action_redo")
        self.action_undo = QtGui.QAction(MainWindow)
        self.action_undo.setEnabled(False)
        self.action_undo.setObjectName("action_undo")
        self.menu_file.addAction(self.action_exit)
        self.menu_bar.addAction(self.menu_file.menuAction())
        self.menu_bar.addAction(self.menu_edit.menuAction())
        self.menu_bar.addAction(self.menu_view.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QObject.connect(self.action_exit, QtCore.SIGNAL("triggered()"), MainWindow.close)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "LogikSim", None, QtGui.QApplication.UnicodeUTF8))
        self.menu_file.setTitle(QtGui.QApplication.translate("MainWindow", "&File", None, QtGui.QApplication.UnicodeUTF8))
        self.menu_view.setTitle(QtGui.QApplication.translate("MainWindow", "&View", None, QtGui.QApplication.UnicodeUTF8))
        self.menu_edit.setTitle(QtGui.QApplication.translate("MainWindow", "&Edit", None, QtGui.QApplication.UnicodeUTF8))
        self.tool_bar.setWindowTitle(QtGui.QApplication.translate("MainWindow", "toolBar", None, QtGui.QApplication.UnicodeUTF8))
        self.history_dock_widget.setWindowTitle(QtGui.QApplication.translate("MainWindow", "History", None, QtGui.QApplication.UnicodeUTF8))
        self.action_exit.setText(QtGui.QApplication.translate("MainWindow", "&Exit", None, QtGui.QApplication.UnicodeUTF8))
        self.action_redo.setText(QtGui.QApplication.translate("MainWindow", "&Redo", None, QtGui.QApplication.UnicodeUTF8))
        self.action_undo.setText(QtGui.QApplication.translate("MainWindow", "&Undo", None, QtGui.QApplication.UnicodeUTF8))

from actions.action_stack_view import ActionStackView
