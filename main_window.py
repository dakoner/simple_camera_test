import os
import time
from PyQt6 import QtGui, QtCore, QtWidgets
from PyQt6.uic import loadUi
from PyQt6.QtWidgets import QFileDialog
import cv2
import numpy as np

import gige_camera_qobject
from config import CAMERA


class ImageWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = None
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)

    def set_image(self, img):
        if img is None:
            return
        s = img.shape
        if len(s) == 2:
            s = (s[0], s[1], 1)

        if s[2] == 1:
            format = QtGui.QImage.Format.Format_Grayscale8
        elif s[2] == 3:
            format = QtGui.QImage.Format.Format_BGR888
        else:
            # Unsupported format
            return

        image = QtGui.QImage(img.data, s[1], s[0], s[1] * s[2], format)
        self.image = image
        self.update()

    def paintEvent(self, event):
        if self.image and not self.image.isNull():
            painter = QtGui.QPainter(self)
            pixmap = QtGui.QPixmap.fromImage(self.image)
            scaled_pixmap = pixmap.scaled(self.size(), QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
            x = (self.width() - scaled_pixmap.width()) / 2
            y = (self.height() - scaled_pixmap.height()) / 2
            painter.drawPixmap(int(x), int(y), scaled_pixmap)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi("microscope_controller.ui", self)

        self.frame_count = 0
        self.fps = 0.0
        self.fps_timer = QtCore.QTimer()
        self.fps_timer.timeout.connect(self.update_fps_status)
        self.fps_timer.start(1000)  # Update every second

        self.camera = gige_camera_qobject.GigECamera()
        self.camera.imageChanged.connect(self.imageChanged)
        self.camera.begin()
        self.camera.camera_play()

        self.autoRadioButton.toggled.connect(self.enableAuto)

        if isinstance(self.camera, gige_camera_qobject.GigECamera):
            self.AeTargetSlider_3.valueChanged.connect(self.AeTargetChanged)
            self.AeTargetLabel_3.setText(str(self.camera.AeTarget))
            self.AeTargetSlider_3.setMinimum(self.camera.cap.sExposeDesc.uiTargetMin)
            self.AeTargetSlider_3.setMaximum(self.camera.cap.sExposeDesc.uiTargetMax)
            self.camera.AeTargetChanged.connect(self.AeTargetChangedCallback)


            self.exposureTimeSlider_3.valueChanged.connect(self.exposureTimeSpinBox.setValue)
            self.exposureTimeSpinBox.valueChanged.connect(self.exposureTimeSlider_3.setValue)
            self.exposureTimeSlider_3.valueChanged.connect(self.ExposureTimeChanged)
            
            exposure_min = int(self.camera.cap.sExposeDesc.uiExposeTimeMin*self.camera.ExposureLineTime)
            exposure_max = int(self.camera.cap.sExposeDesc.uiExposeTimeMax*self.camera.ExposureLineTime)
            
            self.exposureTimeMinLabel.setText(str(exposure_min))
            self.exposureTimeMaxLabel.setText(str(exposure_max))
            
            self.exposureTimeSlider_3.setMinimum(exposure_min)
            self.exposureTimeSlider_3.setMaximum(exposure_max)
            self.exposureTimeSpinBox.setMinimum(exposure_min)
            self.exposureTimeSpinBox.setMaximum(exposure_max)

            self.exposureTimeSlider_3.setValue(exposure_min)
            self.camera.ExposureTimeChanged.connect(self.ExposureTimeChangedCallback)


            self.autoSettingsGroupBox.setEnabled(True)
            self.manualSettingsGroupBox.setEnabled(False)

            self.analogGainSlider_3.valueChanged.connect(self.analogGainSpinBox.setValue)
            self.analogGainSpinBox.valueChanged.connect(self.analogGainSlider_3.setValue)
            self.analogGainSlider_3.valueChanged.connect(self.AnalogGainChanged)

            gain_min = self.camera.cap.sExposeDesc.uiAnalogGainMin
            gain_max = self.camera.cap.sExposeDesc.uiAnalogGainMax
            
            self.analogGainMinLabel.setText(str(gain_min))
            self.analogGainMaxLabel.setText(str(gain_max))
            
            self.analogGainSlider_3.setMinimum(gain_min)
            self.analogGainSlider_3.setMaximum(gain_max)
            self.analogGainSpinBox.setMinimum(gain_min)
            self.analogGainSpinBox.setMaximum(gain_max)
            self.camera.AnalogGainChanged.connect(self.AnalogGainChangedCallback)

        # Recording controls
        self.is_recording = False
        self.recorded_frames = []

        record_group_box = QtWidgets.QGroupBox("Recording")
        record_layout = QtWidgets.QVBoxLayout()

        self.recordButton = QtWidgets.QPushButton("Record")
        self.recordButton.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPlay))
        self.recordButton.clicked.connect(self.start_recording)
        record_layout.addWidget(self.recordButton)

        self.stopButton = QtWidgets.QPushButton("Stop")
        self.stopButton.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaStop))
        self.stopButton.clicked.connect(self.stop_recording)
        self.stopButton.setEnabled(False)
        record_layout.addWidget(self.stopButton)

        self.recordingStatusLabel = QtWidgets.QLabel("Not Recording")
        record_layout.addWidget(self.recordingStatusLabel)

        record_group_box.setLayout(record_layout)

        self.dockWidgetContents_2.layout().addWidget(record_group_box)


    def AnalogGainChanged(self, analog_gain):
        print("AnalogGainChanged", analog_gain)
        self.camera.AnalogGain = analog_gain

    def AnalogGainChangedCallback(self, analog_gain):
        print("AnalogGainChangedCallback", analog_gain)
        self.analogGainSlider_3.blockSignals(True)
        self.analogGainSpinBox.blockSignals(True)
        self.analogGainSlider_3.setValue(int(analog_gain))
        self.analogGainSpinBox.setValue(int(analog_gain))
        self.analogGainSlider_3.blockSignals(False)
        self.analogGainSpinBox.blockSignals(False)

    def enableAuto(self, value):
        print("enableAuto", value)
        self.autoSettingsGroupBox.setEnabled(value)
        self.manualSettingsGroupBox.setEnabled(not value)
        self.camera.AeState = value

    def AeTargetChanged(self, target):
        print("AeTargetChanged", target)
        self.camera.AeTarget = target

    def AeTargetChangedCallback(self, value):
        print("AeTargetChangedCallback", value)
        self.AeTargetSlider_3.blockSignals(True)
        self.AeTargetSlider_3.setValue(int(value))
        self.AeTargetLabel_3.setText(str(int(value)))
        self.AeTargetSlider_3.blockSignals(False)

    def ExposureTimeChanged(self, exposure):
        print("ExposureTimeChanged: ", exposure)
        self.camera.ExposureTime = exposure
        

    def ExposureTimeChangedCallback(self, exposure):
        print("ExposureTimeChangedCallback: ", exposure)
        self.exposureTimeSlider_3.blockSignals(True)
        self.exposureTimeSpinBox.blockSignals(True)
        self.exposureTimeSlider_3.setValue(int(exposure))
        self.exposureTimeSpinBox.setValue(int(exposure))
        self.exposureTimeSlider_3.blockSignals(False)
        self.exposureTimeSpinBox.blockSignals(False)

    def start_recording(self):
        self.is_recording = True
        self.recorded_frames = []
        self.recordButton.setEnabled(False)
        self.stopButton.setEnabled(True)
        self.recordingStatusLabel.setText("Recording...")
        self.recording_start_time = time.time()

    def stop_recording(self):
        self.is_recording = False
        self.recordButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.recordingStatusLabel.setText("Not Recording")

        if not self.recorded_frames:
            print("No frames recorded.")
            return

        duration = time.time() - self.recording_start_time

        # Ask for file name
        options = QFileDialog.Option.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self, "Save Video", "", "AVI Files (*.avi);;All Files (*)", options=options)

        if fileName:
            self.save_video(fileName, duration)

    def save_video(self, filename, duration):
        if not self.recorded_frames:
            return

        if duration > 0:
            fps = max(1, int(round(len(self.recorded_frames) / duration)))
        else:
            fps = 30.0
        
        first_frame = self.recorded_frames[0]
        
        s = first_frame.shape
        if len(s) == 2:
            # Grayscale
            height, width = s
        elif len(s) == 3:
            # Color
            height, width, _ = s
        else:
            print("Unsupported frame shape")
            return

        size = (width, height)

        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        # Always create a grayscale video writer
        out = cv2.VideoWriter(filename, fourcc, fps, size, isColor=False)

        for frame in self.recorded_frames:
            # Ensure frame is 2D grayscale for the writer
            if frame.ndim == 3:
                if frame.shape[2] == 3:
                    # If the frame is color, convert it to grayscale.
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                elif frame.shape[2] == 1:
                    # If it's a 3D grayscale image, convert to 2D
                    frame = frame[:, :, 0]
            
            # Now frame should be 2D grayscale, ready to be written.
            out.write(frame)

        out.release()
        print(f"Video saved to {filename}")
        QtWidgets.QMessageBox.information(self, "Recording", f"Video saved to {filename}")
        self.recorded_frames = [] # Clear memory

    # def onMessage2Changed(self, *args):
    #     print('message2 changed', args)

    def imageChanged(self, img):
        self.frame_count += 1
        if self.is_recording:
            self.recorded_frames.append(img.copy())
        self.image_view.set_image(img)

    def update_fps_status(self):
        self.fps = self.frame_count
        self.frame_count = 0
        self.statusBar().showMessage(f"FPS: {self.fps}")
