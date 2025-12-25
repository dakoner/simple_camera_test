import time
import signal
import sys
import numpy as np
import pdb
from PyQt6 import QtCore
import mvsdk

class GigECamera(QtCore.QObject):
    imageChanged = QtCore.pyqtSignal(np.ndarray)
    ExposureTimeChanged = QtCore.pyqtSignal(float)
    GammaChanged = QtCore.pyqtSignal(float)
    ContrastChanged = QtCore.pyqtSignal(float)
    SharpnessChanged = QtCore.pyqtSignal(float)
    TriggerModeChanged = QtCore.pyqtSignal(float)
    AnalogGainChanged = QtCore.pyqtSignal(float)
    HMirrorChanged = QtCore.pyqtSignal(float)
    VMirrorChanged = QtCore.pyqtSignal(float)
    AeStateChanged = QtCore.pyqtSignal(float)
    AeTargetChanged = QtCore.pyqtSignal(float)

    snapshotCompleted = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, parent=None):
        super().__init__(parent)

        DevList = mvsdk.CameraEnumerateDevice()
        nDev = len(DevList)
        if nDev < 1:
            print("No camera was found!")
            return
            
        for i, DevInfo in enumerate(DevList):
            print("{}: {} {}".format(i, DevInfo.GetFriendlyName(), DevInfo.GetPortType()))
        i = 0 if nDev == 1 else int(input("Select camera: "))
        DevInfo = DevList[i]

        
        self.hCamera = 0
        try:
            self.hCamera = mvsdk.CameraInit(DevInfo, -1, -1)
        except mvsdk.CameraException as e:
            print("CameraInit Failed({}): {}".format(e.error_code, e.message) )
            return


    @QtCore.pyqtProperty(int, notify=GammaChanged)
    def Gamma(self):
        return mvsdk.CameraGetGamma(self.hCamera)

    @Gamma.setter
    def Gamma(self, gamma):
        if gamma == mvsdk.CameraGetGamma(self.hCamera):
            return
        mvsdk.CameraSetGamma(self.hCamera, gamma)
        self.GammaChanged.emit(mvsdk.CameraGetGamma(self.hCamera)) 


    @QtCore.pyqtProperty(int, notify=ContrastChanged)
    def Contrast(self):
        return mvsdk.CameraGetContrast(self.hCamera)

    @Contrast.setter
    def Contrast(self, contrast):
        if contrast == mvsdk.CameraGetContrast(self.hCamera):
            return
        mvsdk.CameraSetContrast(self.hCamera, contrast)
        self.ContrastChanged.emit(mvsdk.CameraGetContrast(self.hCamera)) 

    @QtCore.pyqtProperty(int, notify=SharpnessChanged)
    def Sharpness(self):
        return mvsdk.CameraGetSharpness(self.hCamera)

    @Sharpness.setter
    def Sharpness(self, sharpness):
        if sharpness == mvsdk.CameraGetSharpness(self.hCamera):
            return
        mvsdk.CameraSetSharpness(self.hCamera, sharpness)
        self.SharpnessChanged.emit(mvsdk.CameraGetSharpness(self.hCamera)) 

    @QtCore.pyqtProperty(int, notify=AnalogGainChanged)
    def AnalogGain(self):
        return mvsdk.CameraGetAnalogGain(self.hCamera)

    @AnalogGain.setter
    def AnalogGain(self, gain):
        if gain == mvsdk.CameraGetAnalogGain(self.hCamera):
            return
        mvsdk.CameraSetAnalogGain(self.hCamera, gain)
        self.AnalogGainChanged.emit(mvsdk.CameraGetAnalogGain(self.hCamera)) 


    @QtCore.pyqtProperty(int, notify=VMirrorChanged)
    def VMirror(self):
        return mvsdk.CameraGetMirror(self.hCamera, 1)

    @VMirror.setter
    def VMirror(self, mode):
        if mode == mvsdk.CameraGetMirror(self.hCamera, 1):
            return
        mvsdk.CameraSetMirror(self.hCamera, 1, mode)
        self.VMirrorChanged.emit(mvsdk.CameraGetMirror(self.hCamera, 1)) 

    @QtCore.pyqtProperty(int, notify=HMirrorChanged)
    def HMirror(self):
        return mvsdk.CameraGetMirror(self.hCamera, 0)

    @HMirror.setter
    def HMirror(self, mode):
        if mode == mvsdk.CameraGetMirror(self.hCamera, 0):
            return
        mvsdk.CameraSetMirror(self.hCamera, 0, mode)
        self.HMirrorChanged.emit(mvsdk.CameraGetMirror(self.hCamera, 0)) 




    @QtCore.pyqtProperty(int, notify=TriggerModeChanged)
    def TriggerMode(self):
        return mvsdk.CameraGetTriggerMode(self.hCamera)

    @TriggerMode.setter
    def TriggerMode(self, trigger_mode):
        if trigger_mode == mvsdk.CameraGetTriggerMode(self.hCamera):
            return
        mvsdk.CameraSetTriggerMode(self.hCamera, trigger_mode)
        self.TriggerModeChanged.emit(mvsdk.CameraGetTriggerMode(self.hCamera)) 


    @QtCore.pyqtProperty(int, notify=AeStateChanged)
    def AeState(self):
        return mvsdk.CameraGetAeState(self.hCamera)

    @AeState.setter
    def AeState(self, state):
        if state == mvsdk.CameraGetAeState(self.hCamera):
            return
        mvsdk.CameraSetAeState(self.hCamera, state)
        self.AeStateChanged.emit(mvsdk.CameraGetAeState(self.hCamera)) 

    @QtCore.pyqtProperty(float, notify=AeTargetChanged)
    def AeTarget(self):
        return mvsdk.CameraGetAeTarget(self.hCamera)

    @AeTarget.setter
    def AeTarget(self, target):
        if target == mvsdk.CameraGetAeTarget(self.hCamera):
            return
        mvsdk.CameraSetAeTarget(self.hCamera, target)
        self.AeTargetChanged.emit(mvsdk.CameraGetAeTarget(self.hCamera)) 

    @QtCore.pyqtProperty(float, notify=ExposureTimeChanged)
    def ExposureTime(self):
        return mvsdk.CameraGetExposureTime(self.hCamera)

    @ExposureTime.setter
    def ExposureTime(self, exposure):
        if exposure == mvsdk.CameraGetExposureTime(self.hCamera):
            return
        mvsdk.CameraSetExposureTime(self.hCamera, exposure)
        self.ExposureTimeChanged.emit(mvsdk.CameraGetExposureTime(self.hCamera)) 

    @mvsdk.method(mvsdk.CAMERA_SNAP_PROC)
    def callback(self, hCamera, pRawData, pFrameHead, pContext):
        FrameHead = pFrameHead[0]
        pFrameBuffer = self.pFrameBuffer

        mvsdk.CameraImageProcess(hCamera, pRawData, pFrameBuffer, FrameHead)
        mvsdk.CameraReleaseImageBuffer(hCamera, pRawData)

        frame_data = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(pFrameBuffer)
        frame = np.frombuffer(frame_data, dtype=np.uint8)
        frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth, 1 if FrameHead.uiMediaType == mvsdk.CAMERA_MEDIA_TYPE_MONO8 else 3) )

        self.imageChanged.emit(frame)

    def snapshot(self):
        pRawData, FrameHead = mvsdk.CameraGetImageBuffer(self.hCamera, 200)
        pFrameBuffer = self.pFrameBuffer

        mvsdk.CameraImageProcess(self.hCamera, pRawData, pFrameBuffer, FrameHead)
        mvsdk.CameraReleaseImageBuffer(self.hCamera, pRawData)

        frame_data = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(pFrameBuffer)
        frame = np.frombuffer(frame_data, dtype=np.uint8)
        frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth, 1 if FrameHead.uiMediaType == mvsdk.CAMERA_MEDIA_TYPE_MONO8 else 3) )
        self.snapshotCompleted.emit(frame)
        
    def begin(self):
        self.cap = mvsdk.CameraGetCapability(self.hCamera)

        monoCamera = (self.cap.sIspCapacity.bMonoSensor != 0)
        if monoCamera:
            mvsdk.CameraSetIspOutFormat(self.hCamera, mvsdk.CAMERA_MEDIA_TYPE_MONO8)

        self.FrameBufferSize = self.cap.sResolutionRange.iWidthMax * self.cap.sResolutionRange.iHeightMax * (1 if monoCamera else 3)
        self.pFrameBuffer = mvsdk.CameraAlignMalloc(self.FrameBufferSize, 16)

        print("td", mvsdk.CameraGetTriggerDelayTime(self.hCamera))
        mvsdk.CameraSetStrobeMode(self.hCamera, 1)
        print("sm ", mvsdk.CameraGetStrobeMode(self.hCamera))
               
        mvsdk.CameraSetStrobeDelayTime(self.hCamera, 0)
        print("sd", mvsdk.CameraGetStrobeDelayTime(self.hCamera))
        mvsdk.CameraSetStrobePulseWidth(self.hCamera, 50000)
        print("sw", mvsdk.CameraGetStrobePulseWidth(self.hCamera))
        print("sp", mvsdk.CameraGetStrobePolarity(self.hCamera))
        mvsdk.CameraSetExtTrigSignalType(self.hCamera, 1)
        print("et", mvsdk.CameraGetExtTrigSignalType(self.hCamera))
        print("et", mvsdk.CameraGetExtTrigDelayTime(self.hCamera))
        print("etj", mvsdk.CameraGetExtTrigJitterTime(self.hCamera))
        print("tc", mvsdk.CameraGetTriggerCount(self.hCamera))


        self.ExposureTime = 10
        self.ExposureLineTime = mvsdk.CameraGetExposureLineTime(self.hCamera)
        print("ex", mvsdk.CameraGetExposureTime(self.hCamera))
        print("extrig", mvsdk.CameraGetExtTrigSignalType(self.hCamera))
        #self.ExposureTime = 0
        self.Gamma = mvsdk.CameraGetGamma(self.hCamera)
        self.Contrast = mvsdk.CameraGetContrast(self.hCamera)
        self.Sharpness = mvsdk.CameraGetSharpness(self.hCamera)
        self.AnalogGain = mvsdk.CameraGetAnalogGain(self.hCamera)

        self.VMirror = mvsdk.CameraGetMirror(self.hCamera, 1)
        self.HMirror = mvsdk.CameraGetMirror(self.hCamera, 0)
        self.TriggerMode = mvsdk.CameraGetTriggerMode(self.hCamera)
        self.AeState = mvsdk.CameraGetAeState(self.hCamera)
        self.AeState = True
        self.AeTarget = mvsdk.CameraGetAeTarget(self.hCamera)
        self.enableCallback()

    def enableCallback(self):
        mvsdk.CameraSetCallbackFunction(self.hCamera, self.callback, 0)
    def disableCallback(self):
        mvsdk.CameraSetCallbackFunction(self.hCamera, None, 0)


    def end(self):
        self.disableCallback()
        
        mvsdk.CameraUnInit(self.hCamera)
        mvsdk.CameraAlignFree(self.pFrameBuffer) 


    def camera_play(self):
        return mvsdk.CameraPlay(self.hCamera)


    def camera_stop(self):
        return mvsdk.CameraStop(self.hCamera)


    def getFrameStatistic(self):
        return mvsdk.CameraGetFrameStatistic(self.hCamera)

    def cameraSoftTrigger(self):
        return mvsdk.CameraSoftTrigger(self.hCamera)
