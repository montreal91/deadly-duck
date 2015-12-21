import sys

from PySide.QtCore                  import Slot
from PySide.QtGui                   import QWidget, QApplication

from gui.widgets.title_window_ui    import Ui_JTitleWindow


qt_app = QApplication(sys.argv)

class JMainInterface(QWidget):
    def __init__(self):
        super(JMainInterface, self).__init__()
        self.title_window = Ui_JTitleWindow( )
        self.title_window.setupUi( self )
        self._SetUpEvents()

    @Slot()
    def _Close(self):
        self.close()

    def Run( self ):
        self.show()
        qt_app.exec_()

    def _SetUpEvents(self):
        self.title_window.quit_btn.clicked.connect(self._Close)