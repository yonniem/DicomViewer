import sys

from cx_Freeze import setup, Executable

include_files = ['config.ini', 'presetsV2.json']
# include_files = []
build_exe_options = {'optimize': 2,
                     'packages': ['uvicorn', 'anyio', 'vtk', 'arrow', 'pydicom', 'pylibjpeg', 'numpy', 'redis'],
                     'excludes': [],
                     'include_files': include_files}
base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

setup(name='runFastApi-OPENGL',
      version='0.1',
      description='三维重建与AI服务',
      options={'build_exe': build_exe_options},
      executables=[Executable('main.py')])
