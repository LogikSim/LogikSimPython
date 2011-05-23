'''
Created on Apr 26, 2011

@author: Christian
'''

from PySide import QtGui, QtCore

from helper.timeit_mod import timeit


class ScrollSchematicCanvas(QtGui.QAbstractScrollArea):
    def __init__(self, *args, **kargs):
        QtGui.QAbstractScrollArea.__init__(self, *args, **kargs)
        
        # grid vars
        self._scale = 0.1
        self._size = QtCore.QSize(200000, 100000)
        # mouse vars
        self._mouse_mid_last_pos = None
        
        # setup widget
        self.setupBars(QtCore.QPoint(50000, 50000))
        self.setFrameShape(QtGui.QFrame.NoFrame)
        #self.viewport().setBackgroundRole(QtGui.QPalette.NoRole)
    
    def windowToLogicPos(self, m_pos):
        return self.getLogicPaintArea().topLeft() + m_pos / self._scale
    
    def getLogicPaintArea(self):
        return QtCore.QRect(QtCore.QPoint(self.horizontalScrollBar().value(), 
                self.verticalScrollBar().value()), 
                self.viewport().size() / self._scale)
    
    def setupBars(self, topleft=None):
        """
        when topleft is None the topleft is not changed
        """
        vb = self.verticalScrollBar()
        hb = self.horizontalScrollBar()
        logic_size = self.viewport().size() / self._scale
        # range
        hb.setRange(0, self._size.width() - logic_size.width())
        vb.setRange(0, self._size.height() - logic_size.height())
        # position
        if topleft is not None:
            hb.setSliderPosition(topleft.x())
            vb.setSliderPosition(topleft.y())
        # single step
        hb.setSingleStep(100)
        vb.setSingleStep(100)
        # page step
        hb.setPageStep(logic_size.width())
        vb.setPageStep(logic_size.height())
        # workaround to immediately apply changes
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.viewport().update()
    
    def resizeEvent(self, event):
        self.setupBars()
    
    @timeit
    def paintEvent(self, event):
        painter = QtGui.QPainter(self.viewport())
        # set logical coordinate system
        logicArea = self.getLogicPaintArea()
        painter.setWindow(logicArea)
        # draw background
        painter.setBrush(QtCore.Qt.black)
        painter.setPen(QtCore.Qt.black)
        painter.drawRect(0, 0, self._size.width(), self._size.height())
        # draw grid
        pen_minor = QtGui.QPen((QtGui.QColor(23, 23, 23)))
        pen_major = QtGui.QPen((QtGui.QColor(30, 30, 30)))
        w, h = self._size.width(), self._size.height()
        step = 100 if self._scale > 0.033 else 500
        def set_pen(z):
            painter.setPen(pen_major if z % 500 == 0 else pen_minor)
        for x in range(0, w, step):
            set_pen(x)
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, step):
            set_pen(y)
            painter.drawLine(0, y, w, y)
        
        # draw simple element
        painter.setPen(QtCore.Qt.white)
        painter.drawRect(50000 + 1000, 50000 + 500, 300, 600)
    
    def wheelEvent(self, event):
        if event.orientation() is QtCore.Qt.Horizontal or \
                event.modifiers() != QtCore.Qt.NoModifier:
            # scroll
            fake_evt = QtGui.QWheelEvent(event.pos(), 
                    event.globalPos(), event.delta(), event.buttons(), 
                    event.modifiers() &~(QtCore.Qt.ControlModifier), 
                    event.orientation())
            QtGui.QAbstractScrollArea.wheelEvent(self, fake_evt)
        else:
            # scale
            new_scale = self._scale * 1.1**(event.delta()/60)
            if  0.0075 < new_scale < 5:
                old_pos = self.windowToLogicPos(event.pos())
                self._scale = new_scale
                new_pos = self.windowToLogicPos(event.pos())
                new_topleft = self.getLogicPaintArea().topLeft() - \
                        (new_pos - old_pos)
                self.setupBars(new_topleft)
    
    def mousePressEvent(self, event):
        if event.button() is QtCore.Qt.MiddleButton:
            self._mouse_mid_last_pos = self.windowToLogicPos(event.pos())
    
    def mouseMoveEvent(self, event):
        # mid mouse pressed -> drag grid
        if event.buttons() & QtCore.Qt.MiddleButton:
            # remember _mouse_mid_last_pos is float, but slider can only
            # change in discrete steps
            curr_pos = self.windowToLogicPos(event.pos())
            desired_slider_pos = self.getLogicPaintArea().topLeft() - \
                    (curr_pos - self._mouse_mid_last_pos)
            self.horizontalScrollBar().setSliderPosition(desired_slider_pos.x())
            self.verticalScrollBar().setSliderPosition(desired_slider_pos.y())

def main():
    import sys
    app = QtGui.QApplication(sys.argv)
    
    view = ScrollSchematicCanvas()
    view.show()
    
    app.exec_()

 
if __name__ == '__main__':
    main()
