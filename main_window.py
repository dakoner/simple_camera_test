import os
import time
from PyQt6 import QtGui, QtCore, QtWidgets
from PyQt6.uic import loadUi

import gige_camera_qobject
import uvc_camera_qobject
from config import CAMERA


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi("microscope_controller.ui", self)

        self.frame_count = 0
        self.fps = 0.0
        self.fps_timer = QtCore.QTimer()
        self.fps_timer.timeout.connect(self.update_fps_status)
        self.fps_timer.start(1000)  # Update every second

        if CAMERA == 'uvc': 
            self.camera = uvc_camera_qobject.UVCCamera(2)
        elif CAMERA == 'gige':
            self.camera = gige_camera_qobject.GigECamera()
        else:
            print("Unsupported camera type", CAMERA)
            raise
        self.camera.imageChanged.connect(self.imageChanged)
        self.camera.begin()
        self.camera.camera_play()

        self.autoRadioButton.toggled.connect(self.enableAuto)


        self.AeTargetSlider_3.valueChanged.connect(self.AeTargetChanged)
        self.AeTargetLabel_3.setText(str(self.camera.AeTarget))
        self.AeTargetSlider_3.setMinimum(self.camera.cap.sExposeDesc.uiTargetMin)
        self.AeTargetSlider_3.setMaximum(self.camera.cap.sExposeDesc.uiTargetMax)
        #self.camera.AeTargetChanged.connect(self.AeTargetChangedCallback)


        self.exposureTimeSlider_3.valueChanged.connect(self.ExposureTimeChanged)
        self.exposureTimeSlider_3.valueChanged.connect( lambda value: self.exposureTimeLabel_3.setText(f"{value}"))
        self.exposureTimeSlider_3.setMinimum(int(self.camera.cap.sExposeDesc.uiExposeTimeMin*self.camera.ExposureLineTime))
        self.exposureTimeSlider_3.setMaximum(int(self.camera.cap.sExposeDesc.uiExposeTimeMax*self.camera.ExposureLineTime))
        self.exposureTimeSlider_3.setValue(int(self.camera.cap.sExposeDesc.uiExposeTimeMin*self.camera.ExposureLineTime))
        #self.camera.ExposureTimeChanged.connect(self.ExposureTimeChangedCallback)


        self.autoSettingsGroupBox.setEnabled(True)
        self.manualSettingsGroupBox.setEnabled(False)

        self.analogGainSlider_3.valueChanged.connect(self.AnalogGainChanged)
        self.analogGainLabel_3.setText(str(self.camera.AnalogGain))
        self.analogGainSlider_3.setMinimum(self.camera.cap.sExposeDesc.uiAnalogGainMin)
        self.analogGainSlider_3.setMaximum(self.camera.cap.sExposeDesc.uiAnalogGainMax)
        #self.camera.AnalogGainChanged.connect(self.AnalogGainChangedCallback)


    def AnalogGainChanged(self, analog_gain):
        print("AnalogGainChanged", analog_gain)
        self.camera.AnalogGain = analog_gain

    def AnalogGainChangedCallback(self, analog_gain):
        print("AnalogGainChangedCallback", analog_gain)
        self.analogGainSlider_3.setValue(int(analog_gain))
        self.analogGainLabel_3.setText(str(int(analog_gain)))

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
        self.AeTargetSlider_3.setValue(int(value))
        self.AeTargetLabel_3.setText(str(int(value)))

    def ExposureTimeChanged(self, exposure):
        print("ExposureTimeChanged: ", exposure)
        self.camera.ExposureTime = exposure
        

    def ExposureTimeChangedCallback(self, exposure):
        print("ExposureTimeChangedCallback: ", exposure)
        #self.camera.ExposureTime = exposure
        #self.exposureTimeSlider_3.setValue(int(exposure/self.camera.ExposureLineTime))
        #self.exposureTimeLabel_3.setText(str(int(exposure/self.camera.ExposureLineTime)))

    # def onMessage2Changed(self, *args):
    #     print('message2 changed', args)

    def imageChanged(self, img):
        self.frame_count += 1
        s = img.shape
        if s[2] == 1:
            format = QtGui.QImage.Format.Format_Grayscale8
        elif s[2] == 3:
            format = QtGui.QImage.Format.Format_BGR888
        image = QtGui.QImage(img, s[1], s[0], format)
        image = image.mirrored(horizontal=False, vertical=False)
        self.curr_image = image
        pixmap = QtGui.QPixmap.fromImage(image)
        pixmap = pixmap.scaled(self.image_view.size(), QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
        self.image_view.setPixmap( pixmap )

    def update_fps_status(self):
        self.fps = self.frame_count
        self.frame_count = 0
        self.statusBar().showMessage(f"FPS: {self.fps}")
