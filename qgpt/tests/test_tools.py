"""Host tool protocol: a closed list of three read-and-calculate tools."""
import ast
import json
import re
import unittest

from _path import ROOT

from quantgpt import tools
from quantgpt.tools import protocol

ALLOWED = frozenset({"sharpe", "drawdown"})
# Word stems that must not appear in any name this package defines for a model to call.
BANNED = ("order", "trade", "buy", "sell", "submit", "execute", "account", "balance", "position", "holding",
          "transfer", "withdraw", "deposit", "key", "secret", "token", "credential", "password", "login",
          "주문", "매수", "매도", "계좌", "잔고", "이체")


class FakeHost:
    def __init__(self):
        self.calls = []

    def run_calc(self, name, params):
        self.calls.append(("run_calc", name, params))
        return {"name": name, "value": 0.42}

    def get_card(self, card_id):
        self.calls.append(("get_card", card_id))
        return {"card_id": card_id, "kind": "strategy"}

    def list_cards(self, kind=None):
        self.calls.append(("list_cards", kind))
        return [{"card_id": "S_X1_demo", "kind": kind or "strategy", "decision": "REJECT"}]


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.host = FakeHost()

    def test_the_list_is_exactly_three_tools(self):
        self.assertEqual(sorted(protocol.TOOLS), ["get_card", "list_cards", "run_calc"])
        self.assertEqual([d["name"] for d in tools.tool_definitions()], ["run_calc", "get_card", "list_cards"])
        members = sorted(n for n in vars(protocol.HostTools) if not n.startswith("_"))
        self.assertEqual(members, ["get_card", "list_cards", "run_calc"])
        self.assertIsInstance(self.host, protocol.HostTools)
        for definition in tools.tool_definitions():
            self.assertFalse(definition["input_schema"]["additionalProperties"])
            json.dumps(definition)

    def test_allowed_calls_reach_the_host(self):
        out = tools.dispatch(self.host, {"tool": "run_calc", "arguments": {"name": "sharpe", "params": {"w": 63}}},
                             allowed_calcs=ALLOWED)
        self.assertEqual(out, {"tool": "run_calc", "result": {"name": "sharpe", "value": 0.42}})
        tools.dispatch(self.host, {"tool": "get_card", "arguments": {"card_id": "S_E1_trend_krx"}},
                       allowed_calcs=ALLOWED)
        tools.dispatch(self.host, {"tool": "list_cards", "arguments": {}}, allowed_calcs=ALLOWED)
        tools.dispatch(self.host, {"tool": "list_cards", "arguments": {"kind": "model"}}, allowed_calcs=ALLOWED)
        self.assertEqual([c[0] for c in self.host.calls], ["run_calc", "get_card", "list_cards", "list_cards"])

    def test_calls_outside_the_list_are_refused_before_the_host_sees_them(self):
        refused = [
            {"tool": "place_order", "arguments": {"symbol": "AAA", "side": "buy", "qty": 1}},
            {"tool": "get_account", "arguments": {}},
            {"tool": "get_balance", "arguments": {}},
            {"tool": "get_api_key", "arguments": {"name": "KIS"}},
            {"tool": "read_file", "arguments": {"path": ".env"}},
            {"tool": "run_calc", "arguments": {"name": "send_order", "params": {}}},        # not an allowed calc
            {"tool": "run_calc", "arguments": {"name": "sharpe"}},                          # params missing
            {"tool": "run_calc", "arguments": {"name": "sharpe", "params": {}, "then": "place_order"}},
            {"tool": "run_calc", "arguments": {"name": "../secrets", "params": {}}},
            {"tool": "get_card", "arguments": {"card_id": "../../.env"}},
            {"tool": "get_card", "arguments": {"card_id": "S_X1_demo", "write": True}},
            {"tool": "list_cards", "arguments": {"kind": "orders"}},
            {"tool": "RUN_CALC", "arguments": {"name": "sharpe", "params": {}}},
            {"tool": "run_calc"},
            {"tool": "run_calc", "arguments": {"name": "sharpe", "params": {}}, "also": {"tool": "place_order"}},
            ["run_calc"], "run_calc", None,
        ]
        for call in refused:
            with self.subTest(call=str(call)[:60]), self.assertRaises(tools.ToolRefused):
                tools.dispatch(self.host, call, allowed_calcs=ALLOWED)
        self.assertEqual(self.host.calls, [])

    def test_an_empty_allowed_list_refuses_every_calculation(self):
        with self.assertRaises(tools.ToolRefused):
            tools.dispatch(self.host, {"tool": "run_calc", "arguments": {"name": "sharpe", "params": {}}},
                           allowed_calcs=frozenset())

    def test_a_host_result_that_is_not_strict_json_is_refused(self):
        class Bad(FakeHost):
            def run_calc(self, name, params):
                return {"value": float("nan")}

            def get_card(self, card_id):
                return {"blob": "x" * (protocol.MAX_RESULT_BYTES + 1)}
        with self.assertRaises(tools.ToolRefused):
            tools.dispatch(Bad(), {"tool": "run_calc", "arguments": {"name": "sharpe", "params": {}}},
                           allowed_calcs=ALLOWED)
        with self.assertRaises(tools.ToolRefused):
            tools.dispatch(Bad(), {"tool": "get_card", "arguments": {"card_id": "S_X1_demo"}},
                           allowed_calcs=ALLOWED)


class NoOrderAccountOrKeyNameTests(unittest.TestCase):
    """The names do not exist: nothing to switch on, nothing to call by mistake."""

    def defined_names(self):
        names = set()
        for path in (ROOT / "quantgpt").rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    names.add(node.name)
        return names

    def test_no_function_or_class_in_the_package_is_named_for_orders_accounts_or_keys(self):
        names = self.defined_names()
        self.assertIn("dispatch", names)
        for name in names:
            parts = set(re.split(r"_+|(?<=[a-z])(?=[A-Z])", name.lower())) - {""}
            hits = [stem for stem in BANNED if any(part.startswith(stem) for part in parts)]
            self.assertEqual(hits, [], name)

    def test_no_tool_name_argument_or_description_mentions_them(self):
        blob = json.dumps(tools.tool_definitions(), ensure_ascii=False).lower()
        for stem in BANNED:
            self.assertNotIn(stem, blob)

    def test_the_tools_package_imports_no_network_or_process_module(self):
        tree = ast.parse((ROOT / "quantgpt/tools/protocol.py").read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                imported.add((node.module or "").split(".")[0])
        self.assertEqual(imported - {"__future__", "dataclasses", "typing"}, set())


if __name__ == "__main__":
    unittest.main()
