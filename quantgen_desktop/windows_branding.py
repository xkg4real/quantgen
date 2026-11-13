"""Brand the native app launched by python.exe, independently of any shortcut.

Qt owns the cross-platform QIcon. Windows additionally receives native small and
large icons for the HWND; keep their handles alive until that window is destroyed.
"""
import ctypes
import sys

APP_ID = "QUANTGEN.Desktop"


def set_app_identity():
    """Call before QApplication/window creation, so Explorer groups us as QUANTGEN."""
    if sys.platform != "win32":
        return True
    setter = ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID
    setter.argtypes = [ctypes.c_wchar_p]
    setter.restype = ctypes.c_long
    return setter(APP_ID) == 0


def bind_window_icons(window, icon_path):
    """Supplement Qt's icon on Windows, with pointer-sized handles on 64-bit Python."""
    if sys.platform != "win32":
        return None
    from PyQt6.QtCore import QObject
    from ctypes import wintypes

    user = ctypes.windll.user32
    load = user.LoadImageW
    load.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT,
                    ctypes.c_int, ctypes.c_int, wintypes.UINT]
    load.restype = wintypes.HANDLE
    send = user.SendMessageW
    send.argtypes = [wintypes.HWND, wintypes.UINT, ctypes.c_size_t, ctypes.c_ssize_t]
    send.restype = ctypes.c_ssize_t
    destroy = user.DestroyIcon
    destroy.argtypes = [wintypes.HICON]
    destroy.restype = wintypes.BOOL
    metric = user.GetSystemMetrics
    metric.argtypes = [ctypes.c_int]
    metric.restype = ctypes.c_int
    handles = []
    for kind, mx, my in ((0, 49, 50), (1, 11, 12)):  # ICON_SMALL/BIG; system icon sizes
        handle = load(None, str(icon_path), 1, metric(mx), metric(my), 0x10)  # IMAGE_ICON, LR_LOADFROMFILE
        if handle:
            handles.append((kind, handle))

    # Called after show(). Do not send WM_SETICON from a Qt icon/WinId event:
    # native icon messages can themselves cause Qt icon events, and destruction
    # emits WinId changes while the underlying QWidget is being torn down.
    binding = QObject(window)
    hwnd=int(window.winId())
    for kind,handle in handles:
        send(hwnd,0x80,kind,handle)  # WM_SETICON

    def release(*_):
        for _kind, handle in handles:
            destroy(handle)
        handles.clear()

    window.destroyed.connect(release)
    return binding
