import sys
from PyQt6.QtWidgets import QApplication
from qtawesome.icon_browser import IconBrowser

app = QApplication(sys.argv)

browser = IconBrowser()
browser.show()

sys.exit(app.exec_())