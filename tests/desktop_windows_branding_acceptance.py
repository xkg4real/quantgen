"""A Python-launched Windows app gets native QUANTGEN icons, without shortcuts."""
import os
from pathlib import Path
import subprocess
import sys
import unittest


class WindowsBrandingTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform == 'win32', 'Native Explorer/Win32 contract')
    def test_python_process_has_app_identity_and_both_hwnd_icons(self):
        # The suite uses offscreen Qt; a separate process selects real Windows
        # handles and leaves the suite's QApplication/platform untouched.
        program = r'''
import ctypes
from ctypes import wintypes
from pathlib import Path
from PyQt6.QtWidgets import QApplication,QWidget
from quantgen_desktop.windows_branding import APP_ID,set_app_identity,bind_window_icons
assert set_app_identity()
app=QApplication([])
window=QWidget();window.show();app.processEvents()
binding=bind_window_icons(window,Path('assets/icon.ico').resolve())
assert binding is not None
getid=ctypes.windll.shell32.GetCurrentProcessExplicitAppUserModelID
getid.argtypes=[ctypes.POINTER(ctypes.c_void_p)];getid.restype=ctypes.c_long
value=ctypes.c_void_p()
assert getid(ctypes.byref(value))==0
assert ctypes.wstring_at(value)==APP_ID
free=ctypes.windll.ole32.CoTaskMemFree;free.argtypes=[ctypes.c_void_p];free(value)
send=ctypes.windll.user32.SendMessageW
send.argtypes=[wintypes.HWND,wintypes.UINT,ctypes.c_size_t,ctypes.c_ssize_t]
send.restype=ctypes.c_ssize_t
for kind in (0,1):assert send(int(window.winId()),0x7F,kind,0)!=0  # WM_GETICON
window.hide();window.show();app.processEvents()
for kind in (0,1):assert send(int(window.winId()),0x7F,kind,0)!=0
from PyQt6 import sip
sip.delete(window)
print('QUANTGEN native identity and small/large window icons verified')
'''
        env=dict(os.environ,QT_QPA_PLATFORM='windows')
        result=subprocess.run([sys.executable,'-X','utf8','-c',program],env=env,
                              cwd=Path(__file__).resolve().parents[1],capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)


if __name__=='__main__':unittest.main()
