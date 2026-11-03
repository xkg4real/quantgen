"""UI-only browser preview. Inert engines/builders; no application data access.
Run from the repository root: python tools/ui/preview_home.py
Open http://127.0.0.1:8767. This does not test real analysis engines.
"""
import os,sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,os.getcwd())
# All runtime state and original data views are inert fixtures in this preview.
def audit(event,args):
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=os.fsdecode(args[0]);name=Path(p).name
  if name=='.env' or name.startswith('.env.') or any(s in p for s in ('/docs/asset_expansion/cache/','/paper_live/','/grokteam/','/holdout/','/.nextgen/')) or p.endswith('.jsonl'):
   raise AssertionError('protected path access blocked')
sys.addaudithook(audit)
import dotenv
with patch.object(dotenv,'load_dotenv',return_value=False):
 import main as app
import flet as ft
sys.modules['core.skills.macro_daily']=SimpleNamespace(on_app_start=lambda **k:None)
app.KRXGateway=lambda:object()
app.RuleStore=lambda:object()
app.QuoteFeed=lambda *a:object()
app.EngineRuntime=lambda *a:object()
for key,_,_ in app.NAV:
 name='build_'+{'lab':'strategy_lab','quant':'quant_lab'}.get(key,key)+'_page'
 setattr(app,name,lambda *a,key=key,**kw:ft.Text('Preview: '+key+' (analysis engine disabled)'))
ft.run(app.main,host='127.0.0.1',port=8767,view=None,assets_dir=str(Path.cwd()/'assets'),no_cdn=True)
