"""Read-only macro sheet and existing local commentary; no overlay mutation."""
from dataclasses import dataclass


@dataclass(frozen=True)
class MacroRequest:
    tool: str = 'sheet'
    source: str = 'auto'

    def validate(self):
        if self.tool not in {'sheet','daily','weekly'} or self.source not in {'auto','fred','synthetic'}:
            raise ValueError('Unknown macro view/source')


@dataclass(frozen=True)
class MacroOutput:
    request: MacroRequest
    sheet: object
    narrative: str


def execute_macro(request, *, sheet_loader=None):
    request.validate()
    from core.ficc import insights
    if sheet_loader is None:
        from core.ficc.macro import macro_sheet
        sheet_loader=macro_sheet
    sheet=sheet_loader(source=request.source)
    narrate={'sheet':insights.narrate_macro,'daily':insights.narrate_daily_brief,'weekly':insights.narrate_weekly_strategy}[request.tool]
    return MacroOutput(request,sheet,narrate(sheet))
