import time
import signal
import sys
import numpy as np
import pdb
from PyQt5 import QtCore
import PySpin
LOGGING_LEVEL = PySpin.SPINNAKER_LOG_LEVEL_WARN

class LoggingEventHandler(PySpin.LoggingEventHandler):

    def __init__(self):
        super(LoggingEventHandler, self).__init__()

    def OnLogEvent(self, logging_event_data):
        print('Category: %s' % logging_event_data.GetCategoryName())
        print('Priority Value: %s' % logging_event_data.GetPriority())
        print('Priority Name: %s' % logging_event_data.GetPriorityName())
        print('Timestamp: %s' % logging_event_data.GetTimestamp())
        print('NDC: %s' % logging_event_data.GetNDC())
        print('Thread: %s' % logging_event_data.GetThreadName())
        print('Message: %s' % logging_event_data.GetLogMessage())
        print()

class Worker(QtCore.QThread):
    imageChanged = QtCore.pyqtSignal(np.ndarray, int, int, int)

    def __init__(self, camera):
        super().__init__()
        self.camera = camera
        self.finish = False

    def __del__(self):
        print("worker cleanup")

    @QtCore.pyqtSlot()
    def run(self):
        while True:
            if self.finish:
                print("worker done")
                return
            self.acquire_callback()
    
    def stop(self):
        print("stopping")
        self.finish = True

    def acquire_callback(self):
        try:
            image_result = self.camera.GetNextImage(1)
        except:
            #print("no image")
            return
        if image_result.IsIncomplete():
            #print('Image incomplete with image status %d ...' % image_result.GetImageStatus())
            return
        width = image_result.GetWidth()
        height = image_result.GetHeight()
        stride = image_result.GetStride()
        d = np.expand_dims(image_result.GetNDArray(), axis=2)
        image_result.Release()
        self.imageChanged.emit(d, width, height, stride)


class PySpinCamera(QtCore.QObject):
    ExposureTimeChanged = QtCore.pyqtSignal(float)
    ExposureAutoChanged = QtCore.pyqtSignal(bool)
    ExposureModeChanged = QtCore.pyqtSignal(bool)
    AcquisitionModeChanged = QtCore.pyqtSignal(bool)
    TriggerModeChanged = QtCore.pyqtSignal(bool)
    TriggerSelectorChanged = QtCore.pyqtSignal(bool)
    TriggerSourceChanged = QtCore.pyqtSignal(bool)
    TriggerActivationChanged = QtCore.pyqtSignal(bool)
    StreamBufferHandlingModeChanged = QtCore.pyqtSignal(bool)
    imageChanged = QtCore.pyqtSignal(np.ndarray, int, int, int)

    def __init__(self):
        super().__init__()
        self.system = PySpin.System.GetInstance()
        self.cam_list = self.system.GetCameras()
        self.camera = self.cam_list[0]
        # self.logging_event_handler = LoggingEventHandler()
        # self.system.RegisterLoggingEventHandler(self.logging_event_handler)
        # self.system.SetLoggingEventPriorityLevel(LOGGING_LEVEL)
        self.init()
        
    def camera_play(self):
        self.startWorker()

    def init(self):
        self.camera.Init()
        self.nodemap_tldevice = self.camera.GetTLDeviceNodeMap()
        self.nodemap = self.camera.GetNodeMap()
        self.nodemap_stream = self.camera.GetTLStreamNodeMap()
        self.worker = None
        self.AcquisitionMode = 'Continuous'
        self.ExposureAuto = 'Off'
        self.ExposureTime = 39

    def callback(self, d, w, h, s):
        self.imageChanged.emit(d, w, h, s)

    def startWorker(self):
        self.worker = Worker(self.camera)
        self.worker.imageChanged.connect(self.callback, QtCore.Qt.DirectConnection)
        self.worker.start()
    def stopWorker(self):
        self.worker.stop()
        del self.worker

    def begin(self):
        self.camera.BeginAcquisition()

    def end(self):
        self.camera.EndAcquisition()

    @QtCore.pyqtProperty(str, notify=AcquisitionModeChanged)
    def AcquisitionMode(self):
        return self.camera.AcquisitionMode.ToString()

    @AcquisitionMode.setter
    def AcquisitionMode(self, acquisition_mode):
        node_acquisition_mode = PySpin.CEnumerationPtr(self.nodemap.GetNode('AcquisitionMode'))
        AcquisitionMode_entry = node_acquisition_mode.GetEntryByName(acquisition_mode)
        if AcquisitionMode_entry == None:
            print("Invalid acquisition mode", acquisition_mode)
            return
        AcquisitionMode_value = AcquisitionMode_entry.GetValue()
        if AcquisitionMode_value == node_acquisition_mode.GetIntValue():
                return
        node_acquisition_mode.SetIntValue(AcquisitionMode_value)
        self.AcquisitionModeChanged.emit(node_acquisition_mode.GetIntValue()) 


    @QtCore.pyqtProperty(str, notify=TriggerModeChanged)
    def TriggerMode(self):
        return self.camera.TriggerMode.ToString()

    @TriggerMode.setter
    def TriggerMode(self, trigger_mode):
        node_trigger_mode = PySpin.CEnumerationPtr(self.nodemap.GetNode('TriggerMode'))
        TriggerMode_entry = node_trigger_mode.GetEntryByName(trigger_mode)
        if TriggerMode_entry == None:
            print("Invalid trigger mode", trigger_mode)
            return
        TriggerMode_value = TriggerMode_entry.GetValue()
        if TriggerMode_value == node_trigger_mode.GetIntValue():
                return
        node_trigger_mode.SetIntValue(TriggerMode_value)
        self.TriggerModeChanged.emit(node_trigger_mode.GetIntValue()) 


    @QtCore.pyqtProperty(str, notify=TriggerSelectorChanged)
    def TriggerSelector(self):
        return self.camera.TriggerSelector.ToString()

    @TriggerSelector.setter
    def TriggerSelector(self, trigger_selector):
        node_trigger_mode = PySpin.CEnumerationPtr(self.nodemap.GetNode('TriggerSelector'))
        TriggerSelector_entry = node_trigger_mode.GetEntryByName(trigger_selector)
        if TriggerSelector_entry == None:
            print("Invalid trigger mode", trigger_selector)
            return
        TriggerSelector_value = TriggerSelector_entry.GetValue()
        if TriggerSelector_value == node_trigger_mode.GetIntValue():
                return
        node_trigger_mode.SetIntValue(TriggerSelector_value)
        self.TriggerSelectorChanged.emit(node_trigger_mode.GetIntValue()) 


    @QtCore.pyqtProperty(str, notify=TriggerSourceChanged)
    def TriggerSource(self):
        return self.camera.TriggerSource.ToString()

    @TriggerSource.setter
    def TriggerSource(self, trigger_source):
        node_trigger_mode = PySpin.CEnumerationPtr(self.nodemap.GetNode('TriggerSource'))
        TriggerSource_entry = node_trigger_mode.GetEntryByName(trigger_source)
        if TriggerSource_entry == None:
            print("Invalid trigger mode", trigger_source)
            return
        TriggerSource_value = TriggerSource_entry.GetValue()
        if TriggerSource_value == node_trigger_mode.GetIntValue():
                return
        node_trigger_mode.SetIntValue(TriggerSource_value)
        self.TriggerSourceChanged.emit(node_trigger_mode.GetIntValue()) 


    @QtCore.pyqtProperty(str, notify=TriggerActivationChanged)
    def TriggerActivation(self):
        return self.camera.TriggerActivation.ToString()

    @TriggerActivation.setter
    def TriggerActivation(self, trigger_source):
        node_trigger_mode = PySpin.CEnumerationPtr(self.nodemap.GetNode('TriggerActivation'))
        TriggerActivation_entry = node_trigger_mode.GetEntryByName(trigger_source)
        if TriggerActivation_entry == None:
            print("Invalid trigger mode", trigger_source)
            return
        TriggerActivation_value = TriggerActivation_entry.GetValue()
        if TriggerActivation_value == node_trigger_mode.GetIntValue():
                return
        node_trigger_mode.SetIntValue(TriggerActivation_value)
        self.TriggerActivationChanged.emit(node_trigger_mode.GetIntValue()) 

    @QtCore.pyqtProperty(str, notify=StreamBufferHandlingModeChanged)
    def StreamBufferHandlingMode(self):
        return self.camera.StreamBufferHandlingMode.ToString()

    @StreamBufferHandlingMode.setter
    def StreamBufferHandlingMode(self, stream_buffer_handling_mode):
        node_streamBufferHandlingMode = PySpin.CEnumerationPtr(self.nodemap_stream.GetNode('StreamBufferHandlingMode'))
        StreamBufferHandlingMode_entry = node_streamBufferHandlingMode.GetEntryByName(stream_buffer_handling_mode)
        if StreamBufferHandlingMode_entry == None:
            print("Invalid buffer handling mode", stream_buffer_handling_mode)
            return
        StreamBufferHandlingMode_value = StreamBufferHandlingMode_entry.GetValue()
        if StreamBufferHandlingMode_value == node_streamBufferHandlingMode.GetIntValue():
            return
        node_streamBufferHandlingMode.SetIntValue(StreamBufferHandlingMode_value)
        self.StreamBufferHandlingModeChanged.emit(node_streamBufferHandlingMode.GetIntValue()) 


    @QtCore.pyqtProperty(str, notify=ExposureAutoChanged)
    def ExposureAuto(self):
        return self.camera.ExposureAuto.ToString()

    @ExposureAuto.setter
    def ExposureAuto(self, ExposureAuto):
        node_ExposureAuto = PySpin.CEnumerationPtr(self.nodemap.GetNode('ExposureAuto'))
        ExposureAuto_entry = node_ExposureAuto.GetEntryByName(ExposureAuto)
        if ExposureAuto_entry == None:
            print("Invalid auto exposure mode", ExposureAuto)
            return
        ExposureAuto_value = ExposureAuto_entry.GetValue()
        if ExposureAuto_value == node_ExposureAuto.GetIntValue():
            return
        node_ExposureAuto.SetIntValue(ExposureAuto_value)
        self.ExposureAutoChanged.emit(node_ExposureAuto.GetIntValue()) 




    @QtCore.pyqtProperty(str, notify=ExposureModeChanged)
    def ExposureMode(self):
        return self.camera.ExposureMode.ToString()

    @ExposureMode.setter
    def ExposureMode(self, ExposureMode):
        node_ExposureMode = PySpin.CEnumerationPtr(self.nodemap.GetNode('ExposureMode'))
        ExposureMode_entry = node_ExposureMode.GetEntryByName(ExposureMode)
        if ExposureMode_entry == None:
            print("Invalid exposure mode", ExposureMode)
            return
        ExposureMode_value = ExposureMode_entry.GetValue()
        if ExposureMode_value == node_ExposureMode.GetIntValue():
            return
        node_ExposureMode.SetIntValue(ExposureMode_value)
        self.ExposureModeChanged.emit(node_ExposureMode.GetIntValue()) 

    @QtCore.pyqtProperty(float, notify=ExposureTimeChanged)
    def ExposureTime(self):
        return self.camera.ExposureTime.GetValue()

    @ExposureTime.setter
    def ExposureTime(self, exposure):
        print("Autoexposure value:",  self.camera.ExposureTime.GetValue())
        if exposure == self.camera.ExposureTime.GetValue():
            return
        self.camera.ExposureTime.SetValue(exposure)
        self.ExposureTimeChanged.emit(self.camera.ExposureTime.GetValue()) 
        
