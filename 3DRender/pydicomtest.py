# import pydicom
# from pydicom import multival
# files = {}
# ds = pydicom.dcmread("D:\\下载\\1.3.12.2.1107.5.1.4.86191.30000022041906243699600001412.dcm", force=True)
# # print(ds)
# patientName = ds.PatientName
# try:
#     patientName = str(patientName)
#     if 'SpecificCharacterSet' in ds:
#         specificCharacterSet = str(ds.SpecificCharacterSet)
#         if specificCharacterSet == "GB18030" or specificCharacterSet == "ISO_IR 192":
#             None
#         else:
#             b = patientName.encode(encoding="ISO-8859-1")
#             patientName = b.decode(encoding="gbk")
#     else:
#         b = patientName.encode(encoding="ISO-8859-1")
#         patientName = b.decode(encoding="gbk")
# except Exception as e:
#     patientName = ds.PatientName
# files['patientName'] = patientName
# files["StudyInstanceUID"] = str(ds.StudyInstanceUID)
# files["StudyDate"] = str(ds.StudyDate)
# files["StudyTime"] = str(ds.StudyTime)
# files["AccessionNumber"] = str(ds.AccessionNumber)
# files["ReferringPhysicianName"] = str(ds.ReferringPhysicianName)
# files["PatientName"] = str(ds.PatientName)
# files["PatientId"] = str(ds.PatientID)
# files["PatientBirthDate"] = str(ds.PatientBirthDate)
# files["PatientSex"] = str(ds.PatientSex)
# files["StudyID"] = str(ds.StudyID)
# files["StudyDescription"] = str(ds.StudyDescription) if "StudyDescription" in ds else ""
# files["SeriesInstanceUID"] = str(ds.SeriesInstanceUID)
# files["SeriesDescription"] = str(ds.SeriesDescription) if "SeriesDescription" in ds else ""
# files["SeriesDate"] = str(ds.SeriesDate) if "SeriesDate" in ds else ""
# files["SeriesTime"] = str(ds.SeriesTime) if "SeriesTime" in ds else ""
# files["SeriesNumber"] = int(ds.SeriesNumber)
# files["Columns"] = int(ds.Columns)
# files["Rows"] = int(ds.Rows)
# files["InstanceNumber"] = int(ds.InstanceNumber)
# files["Modality"] = str(ds.Modality)
# files["SOPInstanceUID"] = str(ds.SOPInstanceUID)
# files["FrameOfReferenceUID"] = str(ds.FrameOfReferenceUID) if "FrameOfReferenceUID" in ds else ""
# files["PixelSpacing"] = [float(d) for d in ds.PixelSpacing] if "PixelSpacing" in ds else []
# files["ImageOrientationPatient"] = [int(d) for d in
#                                     ds.ImageOrientationPatient] if "ImageOrientationPatient" in ds else []
# files["ImagePositionPatient"] = [float(d) for d in ds.ImagePositionPatient] if "ImagePositionPatient" in ds else []
# files["ImageType"] = [str(d) for d in ds.ImageType] if "ImageType" in ds else []
# files["SamplesPerPixel"] = int(ds.SamplesPerPixel)
# files["AcquisitionNumber"] = int(ds.AcquisitionNumber) if "AcquisitionNumber" in ds else 0
# files["BitsAllocated"] = int(ds.BitsAllocated)
# files["BitsStored"] = int(ds.BitsStored)
# files["HighBit"] = int(ds.HighBit)
#
# if "SamplesPerPixel" in ds:
#     files["SamplesPerPixel"] = int(ds.SamplesPerPixel)
# if "SmallestImagePixelValue" in ds:
#     files["SmallestImagePixelValue"] = int(ds.SmallestImagePixelValue)
# if "LargestImagePixelValue" in ds:
#     files["LargestImagePixelValue"] = int(ds.LargestImagePixelValue)
# if "WindowCenter" in ds:
#     if isinstance(ds.WindowCenter, multival.MultiValue):
#         files["WindowCenter"] = [float(str(d)) for d in ds.WindowCenter]
#     elif isinstance(ds.WindowWidth, float):
#         files["WindowCenter"] = float(str(ds.WindowCenter))
#     else:
#         files["WindowCenter"] = 129
# if "WindowWidth" in ds:
#     if isinstance(ds.WindowWidth, multival.MultiValue):
#         files["WindowWidth"] = [float(str(d)) for d in ds.WindowWidth]
#     elif isinstance(ds.WindowWidth, float):
#         files["WindowWidth"] = float(str(ds.WindowWidth))
#     else:
#         files["WindowWidth"] = 257
# if "WindowCenterWidthExplanation" in ds:
#     files["WindowCenterWidthExplanation"] = str(ds.WindowCenterWidthExplanation)
# if "RescaleIntercept" in ds:
#     files["RescaleIntercept"] = int(ds.RescaleIntercept)
# if "RescaleSlope" in ds:
#     files["RescaleSlope"] = int(ds.RescaleSlope)
# if "RescaleType" in ds:
#     files["RescaleType"] = str(ds.RescaleType)
# if "LossyImageCompression" in ds:
#     files["LossyImageCompression"] = str(ds.LossyImageCompression)
# if "PlanarConfiguration" in ds:
#     if isinstance(ds.PlanarConfiguration, int):
#         files["PlanarConfiguration"] = int(ds.PlanarConfiguration)
# if "PhotometricInterpretation" in ds:
#     if isinstance(ds.PhotometricInterpretation, str):
#         files["PhotometricInterpretation"] = str(ds.PhotometricInterpretation)
# if "PixelRepresentation" in ds:
#     if isinstance(ds.PixelRepresentation, int):
#         files["PixelRepresentation"] = int(ds.PixelRepresentation)
# print(files)