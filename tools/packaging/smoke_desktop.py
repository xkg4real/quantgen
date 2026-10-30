"""Installed optional native desktop smoke, outside checkout, no providers/stores."""
import os
from pathlib import Path
import sys
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def guard(event,args):
    if event == 'socket.connect': raise AssertionError('Desktop smoke is offline')
    if event == 'open' and isinstance(args[0],(str,bytes,os.PathLike)):
        parts=Path(os.fsdecode(args[0])).parts
        if any(p.startswith('.env') or p in ('holdout','frozen','paper_live','grokteam','.nextgen','_backup') for p in parts):
            raise AssertionError('Protected path refused')
        if ('asset_expansion' in parts and 'cache' in parts) or str(args[0]).endswith('.jsonl'):
            raise AssertionError('Protected cache/ledger refused')


sys.addaudithook(guard)
import dotenv
with patch.object(dotenv,'load_dotenv',return_value=False):
    import quantgen_desktop.app as desktop
from PyQt6.QtWidgets import QApplication
if 'site-packages' not in Path(desktop.__file__).parts:
    raise AssertionError('Imported checkout instead of installed wheel')
app=QApplication([])
window=desktop.ResearchWindow(auto_refresh=False)
window.show();app.processEvents()
assert window.stack.count()==6
assert not window.windowIcon().isNull()
assert not window.grab().isNull()
window.close()
print('PASS: installed native PyQt6 shell, resources, six workspaces; no engine/provider/ledger start')
