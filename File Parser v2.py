import sys
import random
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QCheckBox, QMainWindow, QFrame
)
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl, QThread, pyqtSignal, Qt
import pyqtgraph as pg


# Simulated background thread to update graphs
class GraphUpdateThread(QThread):
    update_signal = pyqtSignal(int, list)  # Sends updated data to the UI

    def run(self):
        while True:
            self.msleep(500)  # Update every 500ms
            for i in range(10):  # Simulating data for 10 graphs
                data = np.cumsum(np.random.randn(50)).tolist()  # Random cumulative data
                self.update_signal.emit(i, data)


class VideoGraphApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video + Fast PyQtGraph Sync")
        self.setGeometry(100, 100, 1200, 700)

        # Main layout
        main_layout = QHBoxLayout()

        # Left panel (Video Player)
        self.video_widget = QVideoWidget()
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)

        video_controls = QVBoxLayout()
        video_controls.addWidget(self.video_widget)

        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.toggle_video)
        video_controls.addWidget(self.play_button)

        main_layout.addLayout(video_controls, 2)

        # Right panel (Graph Controls & Graphs)
        right_panel = QVBoxLayout()

        # Toggle Buttons for Graphs
        self.graph_checkboxes = []
        self.graph_frames = []
        self.graph_widgets = []

        for i in range(10):
            checkbox = QCheckBox(f"Graph {i + 1}")
            checkbox.setChecked(True)  # Default all graphs ON
            checkbox.stateChanged.connect(self.toggle_graph)
            self.graph_checkboxes.append(checkbox)
            right_panel.addWidget(checkbox)

        # Scrollable Graph Display
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        scroll_widget = QWidget()
        self.graph_layout = QVBoxLayout(scroll_widget)

        for i in range(10):
            plot_widget = pg.PlotWidget()
            plot_widget.setBackground("w")
            plot_widget.plot([], pen=pg.mkPen(color="b", width=2))

            frame = QFrame()
            frame.setLayout(QVBoxLayout())
            frame.layout().addWidget(plot_widget)

            self.graph_widgets.append(plot_widget)
            self.graph_frames.append(frame)
            self.graph_layout.addWidget(frame)

        self.scroll_area.setWidget(scroll_widget)
        right_panel.addWidget(self.scroll_area)

        main_layout.addLayout(right_panel, 3)

        # Central widget setup
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Start Background Thread for Graph Updates
        self.graph_thread = GraphUpdateThread()
        self.graph_thread.update_signal.connect(self.update_graph)
        self.graph_thread.start()

    def toggle_video(self):
        """Play/Pause the video."""
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            video_path = ("5-8 run12.MP4")  # Replace with actual video path
            self.player.setSource(QUrl.fromLocalFile(video_path))
            self.player.play()

    def toggle_graph(self):
        """Show/Hide graphs based on toggle checkboxes."""
        for i, checkbox in enumerate(self.graph_checkboxes):
            self.graph_frames[i].setVisible(checkbox.isChecked())

    def update_graph(self, graph_index, new_data):
        """Update the graph with new data."""
        self.graph_widgets[graph_index].clear()
        self.graph_widgets[graph_index].plot(new_data, pen=pg.mkPen(color="b", width=2))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoGraphApp()
    window.show()
    sys.exit(app.exec())
