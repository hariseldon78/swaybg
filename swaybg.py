import sys
import json
import subprocess
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QFileDialog,
    QTextEdit,
    QLabel,
    QPushButton,
    QComboBox,
)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QDragEnterEvent, QDropEvent


class WallpaperSetter(QWidget):
    def __init__(self):
        super().__init__()
        self.commands = {}
        self.files = {}
        self.modes = {}
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Sway Wallpaper Setter")
        self.setLayout(QVBoxLayout())

        self.command_output = QTextEdit()
        self.command_output.setReadOnly(True)
        self.layout().addWidget(self.command_output)

        self.screens_layout = QHBoxLayout()
        self.layout().addLayout(self.screens_layout)

        # Fetch screen names
        output = subprocess.run(
            "swaymsg -t get_outputs", shell=True, capture_output=True, text=True
        )
        screens = json.loads(output.stdout)
        sorted_screens = sorted(screens, key=lambda x: x["rect"]["x"])
        self.panels = {}

        for screen in sorted_screens:
            screen = screen.get("name")
            if screen:
                panel_layout = QVBoxLayout()

                panel = QLabel(f"Drop Image for {screen}")
                panel.setAlignment(Qt.AlignCenter)
                panel.setAcceptDrops(True)
                panel.setStyleSheet("border: 1px solid black; height: 100px;")
                panel.dragEnterEvent = self.dragEnterEvent
                panel.dropEvent = lambda event, name=screen: self.dropEvent(event, name)

                combo = QComboBox()
                combo.addItems(["fit", "fill", "stretch", "center", "tile"])
                combo.setCurrentText("fit")
                combo.currentTextChanged.connect(
                    lambda mode, name=screen: self.changeMode(mode, name)
                )

                panel_layout.addWidget(panel)
                panel_layout.addWidget(combo)

                self.screens_layout.addLayout(panel_layout)
                self.panels[screen] = panel
                self.modes[screen] = "fit"

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    @pyqtSlot(QDropEvent)
    def dropEvent(self, event: QDropEvent, name: str):
        url = event.mimeData().urls()[0].toLocalFile()
        self.files[name] = url
        self.setWallpaper(name)

    def changeMode(self, mode, screen):
        self.modes[screen] = mode
        # Reapply the wallpaper with the new mode
        if screen in self.files:
            self.setWallpaper(screen)

    def setWallpaper(self, screen, mode="fit"):
        mode = self.modes.get(screen, mode)
        cmd = f'swaymsg output {screen} bg "{self.files[screen]}" {mode}'
        subprocess.run(cmd, shell=True)

        # Update command for this screen
        self.commands[screen] = cmd

        # Update the textbox
        self.command_output.clear()
        for command in self.commands.values():
            self.command_output.append(command)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WallpaperSetter()
    window.show()
    sys.exit(app.exec_())
