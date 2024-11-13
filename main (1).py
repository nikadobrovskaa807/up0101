from PySide6.QtWidgets import QApplication
from up import MasterApp

app = QApplication([])
window = MasterApp()
window.show()
app.exec()
