import json
import os
from pathlib import Path

from vtkmodules.vtkCommonDataModel import vtkPiecewiseFunction
from vtkmodules.vtkIOImage import vtkDICOMImageReader
from vtkmodules.vtkImagingGeneral import vtkImageGaussianSmooth
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
from vtkmodules.vtkRenderingCore import vtkRenderWindowInteractor, vtkRenderWindow, vtkCamera, vtkRenderer, vtkVolume, \
    vtkColorTransferFunction, vtkVolumeProperty
from vtkmodules.vtkRenderingVolume import vtkFixedPointVolumeRayCastMapper, vtkGPUVolumeRayCastMapper
import vtkmodules.vtkRenderingOpenGL2
import vtkmodules.vtkRenderingVolumeOpenGL2


def ShowDicomVtk3D(dicompath, name):
    reader = vtkDICOMImageReader()
    reader.SetDataByteOrderToLittleEndian()
    reader.SetDirectoryName(dicompath)
    reader.Update()

    gaussianSmoothFilter = vtkImageGaussianSmooth()
    gaussianSmoothFilter.SetInputConnection(reader.GetOutputPort())
    gaussianSmoothFilter.SetDimensionality(3)
    gaussianSmoothFilter.SetRadiusFactor(0.7)
    # gaussianSmoothFilter.SetStandardDeviation(10)
    gaussianSmoothFilter.Update()

    volumeMapper = vtkGPUVolumeRayCastMapper()
    volumeMapper.SetInputConnection(gaussianSmoothFilter.GetOutputPort())
    volumeMapper.SetBlendModeToComposite()
    # 设置光线采样距离
    volumeMapper.SetSampleDistance(0.5)
    # 设置光线采样步长
    volumeMapper.SetImageSampleDistance(1.5)
    # 关闭自动设置
    volumeMapper.AutoAdjustSampleDistancesOff()
    # 读取配置文件
    source_path = Path(os.path.join(os.getcwd(), "presetsV2.json"))
    document = json.loads(source_path.read_text(encoding='utf-8'))
    preset = [c for c in document if c['name'] == name][0]
    volumeProperty = vtkVolumeProperty()
    # 插值类型
    volumeProperty.SetInterpolationTypeToLinear()
    # 打开或者关闭阴影
    volumeProperty.ShadeOn()
    volumeProperty.SetAmbient(float(preset['ambient']))
    volumeProperty.SetDiffuse(float(preset['diffuse']))
    volumeProperty.SetSpecular(float(preset['specular']))
    volumeProperty.SetSpecularPower(float(preset['specularPower']))
    # print(volumeProperty.GetColorChannels())

    # 设置不透明度属性
    ofun = vtkPiecewiseFunction()
    scalarOpacity = str(preset['scalarOpacity']).split(' ')
    for s in range(1, int(scalarOpacity[0]), 2):
        ofun.AddPoint(float(scalarOpacity[s]), float(scalarOpacity[s + 1]))
    volumeProperty.SetScalarOpacity(0, ofun)

    # 设置梯度不透明属性
    gfun = vtkPiecewiseFunction()
    gradientOpacity = str(preset['gradientOpacity']).split(' ')
    for g in range(1, int(gradientOpacity[0]), 2):
        gfun.AddPoint(float(gradientOpacity[g]), float(gradientOpacity[g + 1]))
    volumeProperty.SetGradientOpacity(1, gfun)

    # 设置色彩
    color = vtkColorTransferFunction()
    effectiveRange = str(preset['effectiveRange']).split(' ')
    color.SetRange(float(effectiveRange[0]), float(effectiveRange[1]))
    colorTransfer = str(preset['colorTransfer']).split(' ')
    for r in range(1, int(colorTransfer[0]), 4):
        color.AddRGBPoint(float(colorTransfer[r]), float(colorTransfer[r + 1]), float(colorTransfer[r + 2]),
                          float(colorTransfer[r + 3]))
    volumeProperty.SetColor(0, color)

    # 体绘制
    volume = vtkVolume()
    volume.SetMapper(volumeMapper)
    volume.SetProperty(volumeProperty)

    renderer = vtkRenderer()
    renderer.SetBackground(0.0, 0.0, 0.0)
    renderer.AddVolume(volume)

    # 摄像机设置
    camera = vtkCamera()
    camera.SetViewUp(0, 0, -1)
    camera.SetPosition(0, 1, 0)
    camera.SetFocalPoint(0, 0, 0)
    camera.ComputeViewPlaneNormal()
    camera.Dolly(1.5)

    # 设置活动摄像机
    renderer.SetActiveCamera(camera)
    # 重置摄像机
    renderer.ResetCamera()
    # 开启灯光跟随摄像机
    renderer.LightFollowCameraOn()

    renderWindow = vtkRenderWindow()
    renderWindow.AddRenderer(renderer)
    renderWindow.SetSize(640, 800)

    # 渲染
    renderWindow.Render()
    # 关闭显示窗口
    # renderWindow.ShowWindowOff()

    renderWindowInteractor = vtkRenderWindowInteractor()
    style = vtkInteractorStyleTrackballCamera()

    # renderWindowInteractor.SetDesiredUpdateRate(64)
    renderWindowInteractor.SetInteractorStyle(style)
    renderWindowInteractor.SetRenderWindow(renderWindow)

    renderWindowInteractor.Initialize()
    renderWindowInteractor.Start()


if __name__ == '__main__':
    name = 'CT-Pulmonary-Arteries'
    ShowDicomVtk3D("D://CT112", name)
