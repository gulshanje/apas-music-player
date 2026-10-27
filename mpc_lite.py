import sys
import os
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QLabel, QFileDialog, QStyle
)


class VideoPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MPC-Lite")
        self.resize(960, 600)
        self.setAcceptDrops(True)

        # --- Qt media player ---
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)
        self.audio.setVolume(0.8)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background-color: black;")
        self.video_widget.setMinimumSize(320, 240)
        self.player.setVideoOutput(self.video_widget)
        layout.addWidget(self.video_widget, stretch=1)

        controls = QWidget()
        controls.setStyleSheet("background-color: #1e1e1e; color: white;")
        ctrl = QHBoxLayout(controls)
        ctrl.setContentsMargins(8, 4, 8, 4)

        st = self.style()
        self.btn_open = QPushButton(st.standardIcon(QStyle.SP_DialogOpenButton), "")
        self.btn_play = QPushButton(st.standardIcon(QStyle.SP_MediaPlay), "")
        self.btn_stop = QPushButton(st.standardIcon(QStyle.SP_MediaStop), "")
        for b in (self.btn_open, self.btn_play, self.btn_stop):
            b.setFixedSize(36, 36)
            b.setFlat(True)
            ctrl.addWidget(b)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)
        ctrl.addWidget(self.slider, stretch=1)

        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("color: #ddd; padding: 0 8px;")
        ctrl.addWidget(self.time_label)

        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(80)
        self.vol_slider.setFixedWidth(90)
        ctrl.addWidget(self.vol_slider)

        layout.addWidget(controls)

        # --- Connections ---
        self.btn_open.clicked.connect(self.open_file)
        self.btn_play.clicked.connect(self.toggle_play)
        self.btn_stop.clicked.connect(self.player.stop)
        self.slider.sliderMoved.connect(self.player.setPosition)
        self.vol_slider.valueChanged.connect(lambda v: self.audio.setVolume(v / 100))
        self.player.positionChanged.connect(self.on_position)
        self.player.durationChanged.connect(self.on_duration)
        self.player.playbackStateChanged.connect(self.on_state)
        self.player.errorOccurred.connect(
            lambda err, msg: print("Player error:", err, msg))

        self.build_menu()

    def build_menu(self):
        file_menu = self.menuBar().addMenu("&File")
        act_open = QAction("&Open File...", self)
        act_open.setShortcut(QKeySequence.Open)
        act_open.triggered.connect(self.open_file)
        file_menu.addAction(act_open)
        file_menu.addSeparator()
        act_quit = QAction("&Quit", self)
        act_quit.setShortcut(QKeySequence.Quit)
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_quit)

    # ---------- Actions ----------
    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Media", "",
            "Media Files (*.mp4 *.mkv *.avi *.mov *.webm *.mp3 *.flac *.wav *.ogg);;All Files (*)"
        )
        if path:
            self.load(path)

    def load(self, path):
        self.player.setSource(QUrl.fromLocalFile(path))
        self.player.play()
        self.setWindowTitle(f"MPC-Lite — {os.path.basename(path)}")

    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    # ---------- UI updates ----------
    def on_position(self, pos):
        if not self.slider.isSliderDown():
            self.slider.setValue(pos)
        self.time_label.setText(f"{self.fmt(pos)} / {self.fmt(self.player.duration())}")

    def on_duration(self, dur):
        self.slider.setRange(0, dur)

    def on_state(self, state):
        icon = (QStyle.SP_MediaPause if state == QMediaPlayer.PlayingState
                else QStyle.SP_MediaPlay)
        self.btn_play.setIcon(self.style().standardIcon(icon))

    @staticmethod
    def fmt(ms):
        s = ms // 1000
        return f"{s // 60:02d}:{s % 60:02d}"

    # ---------- Drag & Drop ----------
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        urls = e.mimeData().urls()
        if urls:
            self.load(urls[0].toLocalFile())

    # ---------- Keyboard ----------
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Space:
            self.toggle_play()
        elif e.key() == Qt.Key_Left:
            self.player.setPosition(max(0, self.player.position() - 5000))
        elif e.key() == Qt.Key_Right:
            self.player.setPosition(self.player.position() + 5000)
        elif e.key() == Qt.Key_F:
            self.showNormal() if self.isFullScreen() else self.showFullScreen()
        elif e.key() == Qt.Key_Escape and self.isFullScreen():
            self.showNormal()
        else:
            super().keyPressEvent(e)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MPC-Lite")
    win = VideoPlayer()
    win.show()
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        win.load(sys.argv[1])
    sys.exit(app.exec())


if __name__ == "__main__":
    main()