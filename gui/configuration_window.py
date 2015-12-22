from PySide.QtCore                          import Slot
from PySide.QtGui                           import QWidget

from gui.widgets.league_configuration_ui    import Ui_JConfigurationWindow

class JConfigurationWindow(QWidget):
    def __init__(self):
        super(JConfigurationWindow, self).__init__()
        self.working_window = Ui_JConfigurationWindow()
        self.working_window.setupUi(self)

        self._SetUpEvents()

    @Slot()
    def _DefaultSlot(self):
        self.working_window.days_sb.setValue(20)
        self.working_window.divs_sb.setValue(2)
        self.working_window.inside_sb.setValue(4)

    @Slot()
    def _DivSbValueSlot(self):
        if self.working_window.divs_sb.value() > 1:
            self.working_window.outside_sb.setEnabled(True)
        else:
            self.working_window.outside_sb.setEnabled(False)

    def _SetUpEvents(self):
        self.working_window.default_btn.clicked.connect(self._DefaultSlot)
        self.working_window.divs_sb.valueChanged.connect(self._DivSbValueSlot)
