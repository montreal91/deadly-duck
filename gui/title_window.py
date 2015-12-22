import sys

from PySide.QtCore                      import Slot
from PySide.QtGui                       import QWidget, QApplication

from gui.widgets.title_window_ui        import Ui_JTitleWindow
from gui.configuration_window           import JConfigurationWindow

qt_app = QApplication(sys.argv)

class JApplication( QWidget ):
    def __init__(self):
        super( JApplication, self ).__init__( )
        self.title_window = Ui_JTitleWindow( )
        self.title_window.setupUi( self )
        self._configuration = dict()

        self.config_window = JConfigurationWindow()

        self._SetUpEvents()

    @Slot()
    def _CloseSlot( self ):
        self.close()

    @Slot()
    def _ShowConfigWindowSlot( self ):
        self.hide()
        self.config_window.show()

    @Slot()
    def _CloseConfigWindowSlot(self):
        self.config_window.close()
        self.show()

    @Slot()
    def _OkConfigWindowSlot(self):
        self.config_window.close()
        self._configuration["teams"]    = self.config_window.working_window.days_sb.value()
        self._configuration["divs"]     = self.config_window.working_window.divs_sb.value()
        self._configuration["in_div"]   = self.config_window.working_window.inside_sb.value()
        self._configuration["oit_div"]  = self.config_window.working_window.outside_sb.value()


    def Run( self ):
        self.show()
        qt_app.exec_()

    def _SetUpEvents(self):
        self.title_window.quit_btn.clicked.connect( self._CloseSlot )
        self.title_window.new_game_btn.clicked.connect( self._ShowConfigWindowSlot )
        self.config_window.working_window.back_btn.clicked.connect(self._CloseConfigWindowSlot)
        self.config_window.working_window.ok_btn.clicked.connect(self._OkConfigWindowSlot)
