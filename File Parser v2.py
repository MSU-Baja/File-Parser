import sys
import random
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QCheckBox, QMainWindow, QFrame, QSlider
)
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl, QThread, pyqtSignal, Qt
import pyqtgraph as pg


# Simulated background thread to update graphs
class GraphUpdateThread(QThread):
    update_signal = pyqtSignal(int, list)  # Sends updated data to the UI
    headers_signal = pyqtSignal(list)  # Sends column names to UI

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self.running = False
        self.pause_flag = False
        self.headers = []
        self.data = self.load_data()  # Load all data into memory
        self.current_index = 0

    def load_data(self):
        """Reads the text file and parses it into graph data."""
        data_dict = {i: [] for i in range(10)}  # Store data for 10 graphs
        try:
            with open(self.file_path, "r") as file:
                lines = file.readlines()

                self.headers = lines[0].strip().split()  # Extract column names from the first row

                for line in lines[3:]:  # Skip first 3 lines (headers + units)
                    values = line.strip().split()
                    if len(values) == 10:
                        for i in range(10):
                            data_dict[i].append(float(values[i]))  # Convert to float

        except Exception as e:
            print(f"Error loading file: {e}")

        return data_dict

    def start_thread(self):
        """Start the graph updates."""
        if not self.isRunning():
            self.running = True
            self.pause_flag = False
            self.start()

    def stop(self):
        """Stop the graph updates immediately."""
        self.running = False
        self.pause_flag = True
        self.quit()
        self.wait()

    def run(self):
        """Continuously updates the graphs unless stopped."""
        self.headers_signal.emit(self.headers)  # Send headers after thread starts

        index = 0
        while self.running and index < len(next(iter(self.data.values()), [])):
            if self.pause_flag:
                return  # Stop immediately when video pauses

            self.msleep(500)  # Update every 500ms
            for i in range(10):
                self.update_signal.emit(i, self.data[i][:self.current_index])  # Send slice of real data
            self.current_index += 1




class VideoGraphApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video + Fast PyQtGraph Sync")
        self.setGeometry(100, 100, 1200, 700)

        # Video Setup
        self.video_widget = QVideoWidget()
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)

        self.video_path = "C:/Users/matth/File-Parser/5-8-2024_Runs/Video/Run2.MP4"      #       CHANGE VIDEO        #
        self.data_file_path = "C:/Users/matth/File-Parser/5-8-2024_Runs/Data/5-8 Run 2.TXT"         #       CHANGE DATA         #

        self.player.setSource(QUrl.fromLocalFile(self.video_path))

        # Play/Pause Button
        self.play_button = QPushButton("Play / Pause")
        self.play_button.clicked.connect(self.toggle_video)

        # Time Slider


        # Layout
        main_layout = QHBoxLayout()
        video_controls = QVBoxLayout()
        video_controls.addWidget(self.video_widget)
        video_controls.addWidget(self.play_button)
        main_layout.addLayout(video_controls, 2)

        # Right panel (Graph Controls & Graphs)
        right_panel = QVBoxLayout()

        # Graph Setup
        self.graph_checkboxes = []
        self.graph_frames = []
        self.graph_widgets = []
        self.graph_titles = ["Longitudinal Force", "Lateral Force",
                             "Vertical Force", "Camber Moment",
                             "Wheel Torque", "Steer Torque",
                             "RPM", "Degrees",
                             "Longitudinal Acceleration", "Vertical Acceleration"]  # Data Titles

        for i in range(10):
            checkbox = QCheckBox(self.graph_titles[i])  # Default labels before headers load
            checkbox.setChecked(True)
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
            plot_widget.setTitle(self.graph_titles[i])  # Set default title

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
        self.graph_thread = GraphUpdateThread(self.data_file_path)
        self.graph_thread.update_signal.connect(self.update_graph)
        self.graph_thread.headers_signal.connect(self.update_graph_titles)  # Listen for column names
        self.graph_thread.start()

        # Connect Video Playback to Graph Updates
        self.player.playbackStateChanged.connect(self.sync_graph_with_video)

    def update_graph_titles(self, titles):
        """Update graph and checkbox titles based on column names from file."""
        if len(titles) == 10:
            for i in range(10):
                self.graph_widgets[i].setTitle(titles[i])  # Update graph title
                self.graph_checkboxes[i].setText(titles[i])  # Update checkbox label

            self.repaint()  # Force UI refresh to ensure labels update

    def toggle_video(self):
        """Play/Pause the video and sync graphs."""
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def sync_graph_with_video(self, state):
        """Start/Stop graph updates based on video state."""
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.graph_thread.start_thread()
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.graph_thread.stop()

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

#this is a test for changing the file in github