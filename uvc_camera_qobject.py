import numpy as np
from PyQt6 import QtCore
import cv2
from config import WIDTH, HEIGHT, FPS


class Worker(QtCore.QThread):
    imageChanged = QtCore.pyqtSignal(np.ndarray, int, int, int)

    def __init__(self, cap):
        super().__init__()
        self.cap = cap
        self.paused = False

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    @QtCore.pyqtSlot()
    def run(self):
        while not self.paused:
            self.acquire_callback()

    def acquire_callback(self):
        ret = self.cap.grab()
        if ret:
            ret, img = self.cap.retrieve()
            if ret:
                width = img.shape[1]
                height = img.shape[0]
                stride = img.shape[1]
                self.imageChanged.emit(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), img.shape[1], img.shape[0], img.shape[1])


class UVCCamera(QtCore.QObject):

    exposureChanged = QtCore.pyqtSignal(float)
    autoExposureModeChanged = QtCore.pyqtSignal(bool)
    acquisitionModeChanged = QtCore.pyqtSignal(bool)
    imageChanged = QtCore.pyqtSignal(np.ndarray, int, int, int)
    snapshotCompleted = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, device, parent=None):
        super().__init__(parent)
        self.cap = cv2.VideoCapture(device, 0)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
        self.cap.set(cv2.CAP_PROP_FPS, FPS)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
        self.cap.set(cv2.CAP_PROP_EXPOSURE, -11)
        self.cap.set(cv2.CAP_PROP_AUTO_WB, 1.0)
        self.cap.set(cv2.CAP_PROP_WB_TEMPERATURE, 6000)
        self.cap.set(cv2.CAP_PROP_TEMPERATURE, 3000)

        
        self.worker = None

    def callback(self, d, w, h, s):
        self.currentFrame = d
        self.imageChanged.emit(d, w, h, s)

    def snapshot(self):
        self.snapshotCompleted.emit(self.currentFrame)
        


    def enableCallback(self):
        print("enableCallback")
        #self.worker.resume()

    def disableCallback(self):
        print("disableCallback")
        #self.worker.pause()

    def begin(self):
        self.worker = Worker(self.cap)
        self.worker.imageChanged.connect(self.callback, QtCore.Qt.DirectConnection)
        self.worker.start()

    def end(self):
        self.worker.terminate()
        self.worker = None
        self.cap.release()

    # @QtCore.pyqtProperty(str, notify=acquisitionModeChanged)
    # def acquisitionMode(self):
    #     return self.camera.AcquisitionMode.ToString()

    # @acquisitionMode.setter
    # def acquisitionMode(self, acquisitionMode):
    #     node_acquisition_mode = PySpin.CEnumerationPtr(self.nodemap.GetNode('AcquisitionMode'))
    #     acquisitionMode_value = node_acquisition_mode.GetEntryByName(acquisitionMode).GetValue()
    #     if acquisitionMode_value == node_acquisition_mode.GetIntValue(): return
    #     node_acquisition_mode.SetIntValue(acquisitionMode_value)
    #     self.acquisitionModeChanged.emit(node_acquisition_mode.GetIntValue()) 



    # @QtCore.pyqtProperty(bool)#, notify=autoExposureModeChanged)
    # def autoExposureMode(self):
    #     try:
    #         node_autoExposure_mode = PySpin.CEnumerationPtr(self.nodemap.GetNode('ExposureAuto'))    
    #         currentValue = node_autoExposure_mode.GetIntValue()
    #         if currentValue == PySpin.ExposureAuto_Off: returnValue= False
    #         elif currentValue == PySpin.ExposureAuto_Continuous: returnValue= True
    #         return returnValue
    #     except:
    #         import traceback
    #         traceback.print_exc()

    # @autoExposureMode.setter
    # def autoExposureMode(self, autoExposureMode):
    #     currentValue = self.camera.ExposureAuto.GetValue()
    #     if autoExposureMode is False:
    #         if currentValue is PySpin.ExposureAuto_Off: return
    #         self.camera.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)

    #     elif autoExposureMode is True:
    #         if currentValue is PySpin.ExposureAuto_Continuous: return
    #         self.camera.ExposureAuto.SetValue(PySpin.ExposureAuto_Continuous)

    #     currentValue = self.camera.ExposureAuto.GetValue()

    #     if currentValue == PySpin.ExposureAuto_Off: returnValue= False
    #     elif currentValue == PySpin.ExposureAuto_Continuous: returnValue= True
    #     self.autoExposureModeChanged.emit(returnValue) 

    # @QtCore.pyqtProperty(float, notify=exposureChanged)
    # def exposure(self):
    #     return self.camera.ExposureTime.GetValue()

    # @exposure.setter
    # def exposure(self, exposure):
    #     print("Autoexposure value:",  self.camera.ExposureAuto.GetValue())
    #     if exposure == self.camera.ExposureTime.GetValue():
    #         return
    #     self.camera.ExposureTime.SetValue(exposure)
    #     self.exposureChanged.emit(self.camera.ExposureTime.GetValue()) 
        


