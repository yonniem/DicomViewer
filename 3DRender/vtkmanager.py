import base64
import json
import os
import time
from pathlib import Path
import vtkmodules.vtkRenderingOpenGL2
import vtkmodules.vtkRenderingVolumeOpenGL2
from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkCommonCore import vtkCommand
from vtkmodules.vtkCommonDataModel import vtkPiecewiseFunction
from vtkmodules.vtkIOImage import vtkDICOMImageReader
from vtkmodules.vtkIOImage import vtkJPEGWriter
from vtkmodules.vtkImagingGeneral import vtkImageGaussianSmooth
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
from vtkmodules.vtkRenderingCore import vtkRenderWindowInteractor, vtkRenderWindow, vtkCamera, vtkRenderer, vtkVolume, \
    vtkColorTransferFunction, vtkVolumeProperty, vtkWindowToImageFilter
from vtkmodules.vtkRenderingVolume import vtkFixedPointVolumeRayCastMapper, vtkGPUVolumeRayCastMapper
from vtkmodules.vtkWebCore import vtkWebInteractionEvent, vtkWebApplication

from _redis import redis_conn
from config import conf


class _VTKProcess:

    def __init__(self):
        # 渲染次数
        self.num = 0
        # 渲染图片存放位置
        self.home = None
        # 客户端ID
        self.client_id = None
        #
        self.document = None
        self.reader = vtkDICOMImageReader()
        self.gaussianSmoothFilter = vtkImageGaussianSmooth()
        # self.reader = ImageSeriesReader()
        # # 将内存数组转换为vtkImageData
        # self.imageImport = vtkImageImport()
        # # 图像翻转来校正Y轴方向
        # self.flipYFilter = vtkImageFlip()
        # # 图像翻转来校正Z轴方向
        # self.flipZFilter = vtkImageFlip()
        # 体数据映射器(光线投射算法, 默认CPU)
        self.volumeMapper = vtkFixedPointVolumeRayCastMapper()
        # 用来设置体绘制的颜色和不透明函数以及阴影等信息
        self.volumeProperty = vtkVolumeProperty()
        # 类似于几何渲染中的vtkActor，用于表示渲染场景中的对象
        self.volume = vtkVolume()
        # 表示渲染器的抽象规范 渲染器怎么工作全部得按照这个来
        self.renderer = vtkRenderer()
        # 摄像机
        self.camera = vtkCamera()
        # 渲染窗口
        self.renderWindow = vtkRenderWindow()
        # 渲染窗口交互器
        self.renderWindowInteractor = vtkRenderWindowInteractor()
        self.w2if = vtkWindowToImageFilter()
        self.w2if.SetInput(self.renderWindow)
        self.w2if.SetInputBufferTypeToRGB()
        # 放大倍数
        self.w2if.SetScale(1)
        self.w2if.ReadFrontBufferOff()
        self.writer = vtkJPEGWriter()
        # 图像质量
        self.writer.SetQuality(100)
        self.writer.SetInputConnection(self.w2if.GetOutputPort())
        self.writer.WriteToMemoryOn()
        self.app = vtkWebApplication()
        self.app.SetImageEncoding(0)

    # 设置摄像机
    def SetCamera(self):
        self.camera.SetViewUp(0, 0, -1)
        self.camera.SetPosition(0, 1, 0)
        self.camera.SetFocalPoint(0, 0, 0)
        self.camera.ComputeViewPlaneNormal()
        self.camera.Dolly(1.5)

    # 开启GPU渲染
    def StartGPURayCastMapper(self):
        self.volumeMapper = vtkGPUVolumeRayCastMapper()

    # 设置图像翻转
    def SetImageFlip(self):
        self.flipYFilter.SetInputData(self.imageImport.GetOutput())
        self.flipYFilter.SetFilteredAxes(1)
        self.flipYFilter.Update()
        self.flipZFilter.SetInputData(self.flipYFilter.GetOutput())
        self.flipZFilter.SetFilteredAxes(2)
        self.flipZFilter.Update()

    # 设置不透明传输、梯度不透明、颜色传输、光照与阴影属性
    def SetVolumeProperty(self, name):
        preset = [c for c in self.document if c['name'] == name][0]
        # 插值类型
        self.volumeProperty.SetInterpolationTypeToLinear()
        # 打开或者关闭阴影
        self.volumeProperty.ShadeOn()
        # 设置环境光系数
        self.volumeProperty.SetAmbient(float(preset['ambient']))
        # 设置散射光系数
        self.volumeProperty.SetDiffuse(float(preset['diffuse']))
        # 设置反射光系数
        self.volumeProperty.SetSpecular(float(preset['specular']))
        # 高光强度系数
        self.volumeProperty.SetSpecularPower(float(preset['specularPower']))

        # 设置不透明度属性
        ofun = vtkPiecewiseFunction()
        scalarOpacity = str(preset['scalarOpacity']).split(' ')
        for s in range(1, int(scalarOpacity[0]), 2):
            ofun.AddPoint(float(scalarOpacity[s]), float(scalarOpacity[s + 1]))
        self.volumeProperty.SetScalarOpacity(0, ofun)

        # 设置梯度不透明属性
        gfun = vtkPiecewiseFunction()
        gradientOpacity = str(preset['gradientOpacity']).split(' ')
        for g in range(1, int(gradientOpacity[0]), 2):
            gfun.AddPoint(float(gradientOpacity[g]), float(gradientOpacity[g + 1]))
        self.volumeProperty.SetGradientOpacity(1, gfun)

        # 设置颜色传输
        color = vtkColorTransferFunction()
        colorTransfer = str(preset['colorTransfer']).split(' ')
        for r in range(1, int(colorTransfer[0]), 4):
            color.AddRGBPoint(float(colorTransfer[r]), float(colorTransfer[r + 1]), float(colorTransfer[r + 2]),
                              float(colorTransfer[r + 3]))
        self.volumeProperty.SetColor(0, color)

    # 添加窗口渲染事件
    def AddRenderWindowRenderObs(self, command):
        self.renderWindow.AddObserver(vtkCommand.RenderEvent, command)

    # 设置窗口大小
    def SetWindowsSize(self, width, height):
        self.renderWindow.SetSize(width, height)
        self.renderWindow.Modified()
        self.renderWindow.Render()

    # 设置输出图像质量
    def SetQuality(self, quality):
        # 图像质量
        self.writer.SetQuality(quality)

    # 窗口渲染事件
    def WindowRender(self, renderWindow, event):
        beginTime = int(round(time.time() * 1000))
        num = str(self.num)
        self.w2if.Modified()
        self.writer.Write()
        vtk_data = self.writer.GetResult()
        data = vtk_to_numpy(vtk_data).tobytes()
        base64_data = base64.b64encode(data).decode('utf8')
        endTime = int(round(time.time() * 1000))
        r = {
            "attachment": {
                "wslink": "1.0",
                "method": "wslink.binary.attachment",
                "args": [
                    "wslink_bin" + num
                ]
            },
            "subscription": {
                "wslink": "1.0",
                "id": "publish:viewport.image.push.subscription:0",
                "result": {
                    # 图像是否正在处理状态
                    "stale": self.app.GetHasImagesBeingProcessed(self.renderWindow),
                    # 最后渲染的时间
                    "mtime": self.w2if.GetMTime(),
                    # 图像窗口大小
                    "size": [self.renderWindow.GetSize()[0], self.renderWindow.GetSize()[1]],
                    # 图像大小
                    "memsize": len(base64_data),
                    "format": "jpeg",
                    "global_id": "-1",
                    # 本地时间
                    "localTime": 0,
                    "image": "wslink_bin" + num,
                    "workTime": endTime - beginTime,
                    "id": "-1"
                }
            },
            "base64_data": base64_data
        }
        redis_conn.rpush(self.client_id + "base64", json.dumps(r))
        self.num += 1

    # 鼠标滚动
    def Zoom(self, spinY):
        zoomFactor = 1.0 - spinY / 10.0

        camera = self.renderWindow.GetRenderers().GetFirstRenderer().GetActiveCamera()
        fp = camera.GetFocalPoint()
        pos = camera.GetPosition()
        delta = [fp[i] - pos[i] for i in range(3)]
        camera.Zoom(zoomFactor)

        pos2 = camera.GetPosition()
        camera.SetFocalPoint([pos2[i] + delta[i] for i in range(3)])
        self.renderWindow.Modified()
        self.renderWindow.Render()

    # 鼠标与键盘操作事件
    def mouseInteraction(self, event):
        """
        RPC Callback for mouse interactions.
        """
        buttons = 0
        if event["buttonLeft"]:
            buttons |= vtkWebInteractionEvent.LEFT_BUTTON
        if event["buttonMiddle"]:
            buttons |= vtkWebInteractionEvent.MIDDLE_BUTTON
        if event["buttonRight"]:
            buttons |= vtkWebInteractionEvent.RIGHT_BUTTON

        modifiers = 0
        if event["shiftKey"]:
            modifiers |= vtkWebInteractionEvent.SHIFT_KEY
        if event["ctrlKey"]:
            modifiers |= vtkWebInteractionEvent.CTRL_KEY
        if event["altKey"]:
            modifiers |= vtkWebInteractionEvent.ALT_KEY
        if event["metaKey"]:
            modifiers |= vtkWebInteractionEvent.META_KEY
        pvevent = vtkWebInteractionEvent()
        pvevent.SetButtons(buttons)
        pvevent.SetModifiers(modifiers)
        if "x" in event:
            pvevent.SetX(event["x"])
        if "y" in event:
            pvevent.SetY(event["y"])
        if "scroll" in event:
            pvevent.SetScroll(event["scroll"])
        if event["action"] == "dblclick":
            pvevent.SetRepeatCount(2)
        # startCallback = lambda *args, **kwargs: self.startViewAnimation()
        # stopCallback = lambda *args, **kwargs: self.stopViewAnimation()
        # application.AddObserver("StartInteractionEvent", startCallback)
        # application.AddObserver("EndInteractionEvent", stopCallback)
        retVal = self.app.HandleInteractionEvent(self.renderWindow, pvevent)
        # iren = view.GetInteractor()
        del pvevent

        if event["action"] == "down":
            self.app.InvokeEvent("StartInteractionEvent")
            self.renderWindowInteractor.LeftButtonPressEvent()

        if event["action"] == "up":
            self.app.InvokeEvent("EndInteractionEvent")
            self.renderWindowInteractor.LeftButtonReleaseEvent()

        if retVal:
            self.app.InvokeEvent("UpdateEvent")

        return retVal

    # 切换VR参数
    def switch_vr(self, name):
        self.SetVolumeProperty(name)
        self.renderWindow.Render()

    # 初始化设置
    def initialize(self, client_id, PatientId, StudyInstanceUID, SeriesInstanceUID):
        self.client_id = client_id
        redis_conn.expire(client_id + "base64", 10)
        # 读取配置文件
        source_path = Path(os.path.join(os.getcwd(), "presetsV2.json"))
        self.document = json.loads(source_path.read_text(encoding='utf-8'))
        # 拼接序列目录
        dir_path = "/".join([conf.get("app", "home"), PatientId, StudyInstanceUID, SeriesInstanceUID])
        if os.path.isdir(dir_path):
            # 读取文件
            self.reader.SetDataByteOrderToLittleEndian()
            self.reader.SetDirectoryName(dir_path)
            self.reader.Update()
            self.gaussianSmoothFilter.SetInputConnection(self.reader.GetOutputPort())
            self.gaussianSmoothFilter.SetDimensionality(3)
            self.gaussianSmoothFilter.SetRadiusFactor(0.7)
            self.gaussianSmoothFilter.Update()
            self.volumeMapper.SetBlendModeToComposite()
            self.volumeMapper.SetInputConnection(self.gaussianSmoothFilter.GetOutputPort())
            # 设置光线采样距离
            # self.volumeMapper.SetSampleDistance(0.5)
            # 设置光线采样步长
            # self.volumeMapper.SetImageSampleDistance(1.5)
            # 关闭自动设置
            # self.volumeMapper.AutoAdjustSampleDistancesOff()
            # 设置不透明传输、梯度不透明、颜色传输、光照与阴影属性
            self.SetVolumeProperty("CT-default")
            # 用于连接体数据映射器
            self.volume.SetMapper(self.volumeMapper)
            # 设置vtkVolumeProperty对象
            self.volume.SetProperty(self.volumeProperty)
            # 添加渲染对象
            self.renderer.AddVolume(self.volume)
            # 设置背景颜色
            self.renderer.SetBackground(0.0, 0.0, 0.0)
            self.SetCamera()
            # 设置活动摄像机
            self.renderer.SetActiveCamera(self.camera)
            # 重置摄像机
            self.renderer.ResetCamera()
            # 开启灯光跟随摄像机
            self.renderer.LightFollowCameraOn()
            # 关闭显示窗口
            self.renderWindow.ShowWindowOff()
            # 添加渲染事件
            self.AddRenderWindowRenderObs(self.WindowRender)
            # 离屏渲染
            self.renderWindow.SetOffScreenRendering(1)
            # 添加渲染器的抽象规范
            self.renderWindow.AddRenderer(self.renderer)
            style = vtkInteractorStyleTrackballCamera()
            self.Zoom(-1)
            self.Zoom(-1)
            self.Zoom(-1)
            self.Zoom(-1)
            self.renderWindowInteractor.SetInteractorStyle(style)
            # self.renderWindowInteractor.SetDesiredUpdateRate(60)
            self.renderWindowInteractor.SetRenderWindow(self.renderWindow)
            # self.renderWindow.Render()
            # 窗口交互器初始化
            self.renderWindowInteractor.Initialize()
            # self.renderWindowInteractor.Start()


if __name__ == '__main__':
    # logger.info("111")
    # p = _VTKProcess()
    # p.initialize("111111111", "111", "2222", "333")
    # print(p)
    # logger.info("2222")
    source_path = Path(os.path.join(os.getcwd(), "presetsV2.json"))
    print(source_path)