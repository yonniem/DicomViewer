# import base64
# import json
# import os
# import redis
# import itk
# from vtkmodules.vtkCommonCore import vtkCommand
# from vtkmodules.vtkFiltersCore import vtkThresholdPoints, vtkMaskPoints
# from vtkmodules.vtkWebCore import vtkWebInteractionEvent, vtkWebApplication
# from loguru import logger
# from pathlib import Path
# import SimpleITK as sitk
# import vtkmodules.vtkRenderingOpenGL2
# import vtkmodules.vtkRenderingVolumeOpenGL2
# from vtkmodules.vtkIOImage import vtkJPEGWriter
# from vtkmodules.vtkCommonDataModel import vtkPiecewiseFunction
# from vtkmodules.vtkIOImage import vtkImageImport
# from vtkmodules.vtkImagingCore import vtkImageFlip
# from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
# from vtkmodules.vtkRenderingCore import vtkRenderWindowInteractor, vtkRenderWindow, vtkCamera, vtkRenderer, vtkVolume, \
#     vtkColorTransferFunction, vtkVolumeProperty, vtkWindowToImageFilter
# from vtkmodules.vtkRenderingVolume import vtkFixedPointVolumeRayCastMapper, vtkGPUVolumeRayCastMapper
#
# redis_conn = redis.Redis(host='127.0.0.1', port=6379, password='', db=10)
#
#
# def WindowRender(renderWindow, event):
#     w2if = vtkWindowToImageFilter()
#     w2if.SetInput(renderWindow)
#     w2if.SetInputBufferTypeToRGB()
#     w2if.ReadFrontBufferOff()
#     w2if.Update()
#     writer = vtkJPEGWriter()
#     fileName = "D:/c-get/1.jpg"
#     writer.SetFileName(fileName)
#     writer.SetInputConnection(w2if.GetOutputPort())
#     writer.Write()
#     # with open("D:/c-get/1.jpg", "rb") as f:  # 打开01.png图片
#     #     # b64encode是编码，b64decode是解码
#     #     base64_data = base64.b64encode(f.read())  # 读取图片转换的二进制文件，并给赋值
#     #     # base64.b64decode(base64data)
#     #     # print(base64_data)
#     #     redis_conn.set(fileName, base64_data)
#     # os.remove(fileName)
#
#
# def test(volumeMapper, e):
#     print(volumeMapper.GetProgress())
#
#
# def readerProgress(reader, e):
#     print(reader.GetProgress())
#
#
# def ShowDicomVtk3D(dicompath):
#     logger.info("开始读取")
#     # global file_reader
#     file_reader = sitk.ImageSeriesReader()
#     file_reader.AddCommand(sitk.sitkProgressEvent, lambda: print(file_reader.GetProgress()))
#     file_reader.SetGlobalDefaultNumberOfThreads(10)
#     dicom_names = file_reader.GetGDCMSeriesFileNames(dicompath)
#     logger.info("获取文件名")
#     file_reader.SetFileNames(dicom_names)
#     logger.info("设置文件名")
#     sitkImage = file_reader.Execute()
#     logger.info("结束读取")
#     logger.info("开始转化")
#     # print(sitkImage)
#     # print(sitkImage.GetHeight())
#     # print(sitkImage.GetWidth())
#     # print(sitkImage.GetDepth())
#     # print(dir(sitkImage))
#     # print(sitk.GetArrayFromImage(sitkImage))
#     arrBytes = sitk.GetArrayViewFromImage(sitkImage).tobytes()
#     # base64_data = base64.b64encode(arrBytes)
#     # # print(base64_data)
#     # # redis_conn.expire('test', 60)
#     #
#     # redis_conn.set("arrBytes", base64_data)
#     # redis_conn.hset("test", "Spacing", sitkImage.GetSpacing())
#     # redis_conn.hset("test", "Origin", sitkImage.GetOrigin())
#     # redis_conn.hset("test", "Height", sitkImage.GetHeight())
#     # redis_conn.hset("test", "Width", sitkImage.GetWidth())
#     # redis_conn.hset("test", "Depth", sitkImage.GetDepth())
#     # redis_conn.hset("test", "Direction", sitkImage.GetDirection())
#
#     reader = vtkImageImport()
#     # reader.CopyImportVoidPointer(arrBytes, len(arrBytes))
#     reader.SetDataSpacing(sitkImage.GetSpacing())
#     # reader.AddObserver(vtkCommand.ProgressEvent, readerProgress)
#     reader.SetDataOrigin(sitkImage.GetOrigin())
#     reader.SetWholeExtent(0, sitkImage.GetHeight() - 1, 0, sitkImage.GetWidth() - 1, 0, sitkImage.GetDepth() - 1)
#     reader.SetDataExtentToWholeExtent()
#     # reader.SetDataScalarTypeToUnsignedChar()
#     reader.SetDataScalarTypeToShort()
#     reader.SetNumberOfScalarComponents(1)
#     reader.SetDataDirection(sitkImage.GetDirection())
#     reader.SetImportVoidPointer(arrBytes, 0)
#     reader.Update()
#
#     print(reader.GetInformation())
#
#     print(reader.GetImportVoidPointer())
#
#     # 图像翻转
#     flipYFilter = vtkImageFlip()
#     flipYFilter.SetInputData(reader.GetOutput())
#     flipYFilter.SetFilteredAxes(1)
#     flipYFilter.Update()
#     flipZFilter = vtkImageFlip()
#     flipZFilter.SetInputData(flipYFilter.GetOutput())
#     flipZFilter.SetFilteredAxes(2)
#     flipZFilter.Update()
#
#     # arrayData = sitk.GetArrayFromImage(image)
#     # itkimage = itk.image_from_array(arrayData)
#     # vtkimage = itk.vtk_image_from_image(itkimage)
#     # IMAGE_DIMENSION = 3
#     # itkImage = itk.GetImageFromArray(sitk.GetArrayFromImage(sitkImage),
#     #                                  is_vector=sitkImage.GetNumberOfComponentsPerPixel() > 1)
#     # itkImage.SetOrigin(sitkImage.GetOrigin())
#     # itkImage.SetSpacing(sitkImage.GetSpacing())
#     # itkImage.SetDirection(itk.GetMatrixFromArray(
#     #     np.reshape(np.array(sitkImage.GetDirection()), [IMAGE_DIMENSION] * 2)))
#     # vtkimage = itk.vtk_image_from_image(itkImage)
#     logger.info("结束转化")
#
#     volumeMapper = vtkFixedPointVolumeRayCastMapper()
#     volumeMapper.AddObserver(vtkCommand.ProgressEvent, test)
#     volumeMapper.SetInputConnection(flipZFilter.GetOutputPort())
#
#     # 设置光线采样距离
#     volumeMapper.SetSampleDistance(0.5)
#     # 设置光线采样步长
#     volumeMapper.SetImageSampleDistance(1.5)
#     # 关闭自动设置
#     volumeMapper.AutoAdjustSampleDistancesOff()
#     # reader = vtkDICOMImageReader()
#     # reader.SetDataByteOrderToLittleEndian()
#     # reader.SetDirectoryName(dicompath)
#     # reader.Update()
#     # volumeMapper = vtkGPUVolumeRayCastMapper()
#     # volumeMapper.SetInputConnection(reader.GetOutputPort())
#
#     volumeProperty = vtkVolumeProperty()
#     volumeProperty.SetInterpolationTypeToLinear()  # 设置体绘制的属性设置，决定体绘制的渲染效果
#     volumeProperty.ShadeOn()  # 打开或者关闭阴影
#     volumeProperty.SetAmbient(0.2)
#     volumeProperty.SetDiffuse(0.7)  # 漫反射
#     volumeProperty.SetSpecular(0.4)  # 镜面反射
#     volumeProperty.SetSpecularPower(8.0)
#
#     source_path = Path(os.path.join(os.getcwd(), "Presets.json"))
#     document = json.loads(source_path.read_text(encoding='utf-8'))
#     presets = [c for c in document[0]['Children'] if c['Name'] == '默认'][0]
#     # 设置不透明度
#     ofun = vtkPiecewiseFunction()
#     opacityPoints = presets['OpacityPoints']
#     for o in range(0, len(opacityPoints), 2):
#         ofun.AddPoint(opacityPoints[o], opacityPoints[o + 1])
#     volumeProperty.SetScalarOpacity(ofun)  # 设置不透明度
#     # 设置色彩
#     color = vtkColorTransferFunction()
#     RGBPoints = presets['RGBPoints']
#     for r in range(0, len(RGBPoints), 4):
#         color.AddRGBPoint(RGBPoints[r], RGBPoints[r + 1], RGBPoints[r + 2], RGBPoints[r + 3])
#     volumeProperty.SetColor(color)
#
#     # 体绘制
#     volume = vtkVolume()
#     volume.SetMapper(volumeMapper)
#     volume.SetProperty(volumeProperty)
#
#     renderer = vtkRenderer()
#     renderer.SetBackground(0.0, 0.0, 0.0)
#     renderer.AddVolume(volume)
#
#     # 摄像机设置
#     camera = vtkCamera()
#     camera.SetViewUp(0, 0, -1)
#     camera.SetPosition(0, 1, 0)
#     camera.SetFocalPoint(0, 0, 0)
#     camera.ComputeViewPlaneNormal()
#     camera.Dolly(1.5)
#
#     # 设置活动摄像机
#     renderer.SetActiveCamera(camera)
#     # 重置摄像机
#     renderer.ResetCamera()
#     # 开启灯光跟随摄像机
#     renderer.LightFollowCameraOn()
#
#     renderWindow = vtkRenderWindow()
#     renderWindow.AddRenderer(renderer)
#     renderWindow.SetSize(640, 800)
#     renderWindow.AddObserver(vtkCommand.RenderEvent, WindowRender)
#     # 渲染
#     renderWindow.Render()
#     # 关闭显示窗口
#     renderWindow.ShowWindowOff()
#     renderWindow.SetOffScreenRendering(1)
#
#     renderWindowInteractor = vtkRenderWindowInteractor()
#     style = vtkInteractorStyleTrackballCamera()
#
#     renderWindowInteractor.SetInteractorStyle(style)
#     renderWindowInteractor.SetRenderWindow(renderWindow)
#
#     renderWindowInteractor.Initialize()
#     logger.info("结束")
#     # zoom(renderWindow, 1)
#     # zoom(renderWindow, 1)
#     # zoom(renderWindow, 1)
#     # event = {
#     #     "action": "down",
#     #     "x": 0.5005220243673852,
#     #     "y": 0.6125933831376734,
#     #     "buttonLeft": 1,
#     #     "buttonMiddle": 0,
#     #     "buttonRight": 0,
#     #     "shiftKey": 0,
#     #     "altKey": 0,
#     #     "ctrlKey": 0,
#     #     "metaKey": 0,
#     #     "view": 1
#     # }
#     # mouseInteraction(renderWindow, event)
#     # event2 = {
#     #     "action": "up",
#     #     "x": 0.59914526710403,
#     #     "y": 0.6125933831376734,
#     #     "buttonLeft": 0,
#     #     "buttonMiddle": 0,
#     #     "buttonRight": 0,
#     #     "shiftKey": 0,
#     #     "altKey": 0,
#     #     "ctrlKey": 0,
#     #     "metaKey": 0,
#     #     "view": 1
#     # }
#     # mouseInteraction(renderWindow, event2)
#     # print(renderWindow.GetInteractor())
#     # renderWindowInteractor.SetEventInformation()
#     # renderWindowInteractor.EnableRenderOn()
#     renderWindowInteractor.Start()
#
#
# def zoom(renderWindow, spin):
#     zoomFactor = 1.0 - spin / 10.0
#
#     camera = renderWindow.GetRenderers().GetFirstRenderer().GetActiveCamera()
#     fp = camera.GetFocalPoint()
#     pos = camera.GetPosition()
#     delta = [fp[i] - pos[i] for i in range(3)]
#     camera.Zoom(zoomFactor)
#
#     pos2 = camera.GetPosition()
#     camera.SetFocalPoint([pos2[i] + delta[i] for i in range(3)])
#     renderWindow.Modified()
#
#
# # def HandleInteractionEvent(view, event):
# #     iren = view.GetInteractor()
# #     viewSize = view.GetSize()
# #     ctrlKey = event["ctrlKey"]
# #     shiftKey = event["shiftKey"]
# #     posX = math.floor(viewSize[0] * event["x"] + 0.5)
# #     posY = math.floor(viewSize[1] * event["y"] + 0.5)
# #     iren.SetEventInformation(posX, posY, ctrlKey, shiftKey, "35", 1)
# #     iren.MouseMoveEvent()
#
# # def startViewAnimation():
# #     print("11111111111")
# #
# #
# # def stopViewAnimation():
# #     print("222222222222222")
# #
# # def pushRender():
#
#
# def mouseInteraction(view, event):
#     """
#     RPC Callback for mouse interactions.
#     """
#     # view = getView(event["view"])
#
#     buttons = 0
#     if event["buttonLeft"]:
#         buttons |= vtkWebInteractionEvent.LEFT_BUTTON
#     if event["buttonMiddle"]:
#         buttons |= vtkWebInteractionEvent.MIDDLE_BUTTON
#     if event["buttonRight"]:
#         buttons |= vtkWebInteractionEvent.RIGHT_BUTTON
#
#     modifiers = 0
#     if event["shiftKey"]:
#         modifiers |= vtkWebInteractionEvent.SHIFT_KEY
#     if event["ctrlKey"]:
#         modifiers |= vtkWebInteractionEvent.CTRL_KEY
#     if event["altKey"]:
#         modifiers |= vtkWebInteractionEvent.ALT_KEY
#     if event["metaKey"]:
#         modifiers |= vtkWebInteractionEvent.META_KEY
#
#     pvevent = vtkWebInteractionEvent()
#     pvevent.SetButtons(buttons)
#     pvevent.SetModifiers(modifiers)
#     if "x" in event:
#         pvevent.SetX(event["x"])
#     if "y" in event:
#         pvevent.SetY(event["y"])
#     if "scroll" in event:
#         pvevent.SetScroll(event["scroll"])
#     if event["action"] == "dblclick":
#         pvevent.SetRepeatCount(2)
#     # pvevent.SetKeyCode(event["charCode"])
#     application = vtkWebApplication()
#     application.SetImageEncoding(0)
#     # observerCallback =  lambda *args, **kwargs: pushRender()
#     # startCallback = lambda *args, **kwargs: startViewAnimation()
#     # stopCallback = lambda *args, **kwargs: stopViewAnimation()
#     # application.AddObserver("UpdateEvent", observerCallback)
#     # application.AddObserver("StartInteractionEvent", startCallback)
#     # application.AddObserver("EndInteractionEvent", stopCallback)
#     retVal = application.HandleInteractionEvent(view, pvevent)
#     iren = view.GetInteractor()
#
#     print(retVal)
#     del pvevent
#
#     if event["action"] == "down":
#         application.InvokeEvent("StartInteractionEvent")
#         iren.MouseMoveEvent()
#         iren.LeftButtonPressEvent()
#
#     if event["action"] == "up":
#         application.InvokeEvent("EndInteractionEvent")
#         iren.LeftButtonReleaseEvent()
#
#     if retVal:
#         application.InvokeEvent("UpdateEvent")
#
#     return retVal
#
#
# if __name__ == '__main__':
#     ShowDicomVtk3D("D:\\CT112\\")
