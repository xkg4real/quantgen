"""Repaint cached Flet controls without rebuilding forms or running analyses."""
from dataclasses import fields, is_dataclass, replace
import flet as ft
from core.theme import LIGHT, DARK, token_names


def apply_palette(root, palette):
    colours = {getattr(source, key).lower(): getattr(palette, key)
               for source in (LIGHT, DARK) for key in token_names()}
    visited = set()

    def colour(value):
        if isinstance(value, str): return colours.get(value.lower(), value)
        if isinstance(value, dict): return {key: colour(item) for key, item in value.items()}
        return value

    def visit(value):
        if isinstance(value, list): return [visit(item) for item in value]
        if isinstance(value, tuple): return tuple(visit(item) for item in value)
        if isinstance(value, dict): return {key: visit(item) for key, item in value.items()}
        if not is_dataclass(value) or not type(value).__module__.startswith(('flet.', 'ui.')):
            return value
        if id(value) in visited:return value
        visited.add(id(value))
        if isinstance(value, ft.Control):
            callback = getattr(value, 'render_theme', None)
            if callable(callback): callback(palette)
        changes = {}
        for field in fields(value):
            if field.name.startswith('_') or field.name in {'data', 'value'}:continue
            old = getattr(value, field.name)
            new = colour(old) if 'color' in field.name else visit(old)
            if new is not old: changes[field.name] = new
        if isinstance(value, ft.Control):
            for key, item in changes.items():setattr(value, key, item)
            return value
        return replace(value, **changes) if changes else value

    visit(root)
