"""Injected responses only: auth, billing, model, transport and privacy boundaries."""
from copy import deepcopy
import unittest
from unittest.mock import Mock, patch

import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    from core.quant import insights
from core.research.ai_connection import OUTPUT_TOKEN_LIMIT, error_message
from requests.exceptions import Timeout, ConnectionError


class ConnectionTests(unittest.TestCase):
    def call(self, status=200, body=None, exception=None):
        http = Mock()
        http.post.return_value.status_code = status
        http.post.return_value.json.return_value = body
        http.post.side_effect = exception
        payload = {'price': 42, 'verdict': 'NOT_RUN', 'holdings': ['private fixture']}
        before = deepcopy(payload)
        with patch.object(insights.config, 'anthropic_key', return_value='fixture-key-secret'), \
             patch.object(insights.config, 'ai_model', return_value='fixture-model'), \
             patch.object(insights, '_requests', http):
            result = insights.deep_analysis('portfolio', payload, question='Explain risk')
        http.post.assert_called_once()  # never auto-retry credentials or billable calls
        self.assertEqual(payload, before)
        sent = http.post.call_args.kwargs
        self.assertEqual(sent['headers']['x-api-key'], 'fixture-key-secret')
        self.assertEqual(sent['json']['model'], 'fixture-model')
        self.assertNotIn('private fixture', str(sent['json']))
        self.assertIn('NOT_RUN', str(sent['json']))
        self.assertNotIn('fixture-key-secret', result.error)
        return result

    def test_http_failures_are_distinct_and_do_not_echo_bodies(self):
        cases = {400:'INVALID_REQUEST',401:'AUTHENTICATION',402:'BILLING',403:'PERMISSION',
                 404:'MODEL_NOT_FOUND',413:'REQUEST_TOO_LARGE',429:'RATE_LIMIT',
                 500:'SERVICE_UNAVAILABLE',529:'SERVICE_UNAVAILABLE',418:'REQUEST_FAILED'}
        for status, code in cases.items():
            with self.subTest(status=status):
                r = self.call(status, {'error': {'message': 'fixture-key-secret raw-private-payload'}})
                self.assertEqual(r.error_code, code); self.assertEqual(r.http_status, status)
                self.assertEqual(r.text, ''); self.assertNotIn('raw-private-payload', r.error)
                self.assertIn(f'HTTP {status}', r.error)
        self.assertIn('ANTHROPIC_API_KEY', self.call(401).error)
        self.assertIn('QUANTGEN_AI_MODEL', self.call(404).error)

    def test_credit_failure_is_not_misdiagnosed_as_key_rejection(self):
        r = self.call(400, {'error': {'type': 'invalid_request_error',
            'message': 'Your credit balance is too low to access the Anthropic API. fixture-key-secret'}})
        self.assertEqual(r.error_code, 'BILLING')
        self.assertIn('separate', r.error)

    def test_malformed_error_body_still_uses_http_status(self):
        for body in (None, [], 'private raw text', {'error': []}, {'error': {'message': 42}}):
            with self.subTest(body=body):
                self.assertEqual(self.call(401, body).error_code, 'AUTHENTICATION')
                self.assertEqual(self.call(400, body).error_code, 'INVALID_REQUEST')

    def test_network_and_timeout_never_echo_exception_or_claim_auth_rejection(self):
        for exc, code in [(Timeout('fixture-key-secret'), 'TIMEOUT'),
                          (ConnectionError('fixture-key-secret'), 'NETWORK'),
                          (ValueError('fixture-key-secret'), 'NETWORK')]:
            with self.subTest(code=code):
                self.assertEqual(self.call(exception=exc).error_code, code)

    def test_success_and_invalid_success_responses(self):
        r = self.call(body={'content':[{'type':'thinking','thinking':'hidden'},
                                      {'type':'text','text':'Fixture explanation'}],
                            'stop_reason': 'end_turn'})
        self.assertEqual(r.text, 'Fixture explanation'); self.assertEqual(r.error_code, '')
        self.assertEqual(r.stop_reason, 'end_turn')
        self.assertIsNotNone(r.number_check)        # advisory; never alters the text
        with patch.object(insights, 'number_check', side_effect=ValueError('fixture')):
            r = self.call(body={'content': [{'type': 'text', 'text': 'Fixture 9.99'}],
                                'stop_reason': 'end_turn'})
        self.assertEqual((r.error_code, r.text, r.stop_reason), ('', 'Fixture 9.99', 'end_turn'))
        self.assertIsNone(r.number_check)
        for body in (None, 'bad', {'content': []}, {'content': {}},
                     {'content': [{'type':'text','text': 42}]}):
            with self.subTest(body=body):
                r = self.call(body=body)
                self.assertEqual(r.error_code, 'INVALID_RESPONSE'); self.assertEqual(r.text, '')

    def test_stop_reason_is_read_after_the_body_and_before_the_text(self):
        thinking = {'type': 'thinking', 'thinking': ''}
        text = {'type': 'text', 'text': 'The figures describe a portfolio whose'}
        ok = self.call(body={'content': [thinking, {'type': 'text', 'text': 'Complete fixture.'}],
                             'stop_reason': 'end_turn'})
        self.assertEqual((ok.error_code, ok.text, ok.stop_reason), ('', 'Complete fixture.', 'end_turn'))
        cases = [
            ({'content': [text], 'stop_reason': 'stop_sequence'}, 'INCOMPLETE_RESPONSE'),
            ({'content': [text], 'stop_reason': 'max_tokens'}, 'OUTPUT_LIMIT'),
            ({'content': [thinking], 'stop_reason': 'max_tokens'}, 'OUTPUT_LIMIT'),
            ({'content': [], 'stop_reason': 'max_tokens'}, 'OUTPUT_LIMIT'),
            ({'content': [text], 'stop_reason': 'refusal',
              'stop_details': {'type': 'refusal', 'category': None,
                               'explanation': 'fixture-key-secret provider explanation'}}, 'REFUSED'),
            ({'content': [], 'stop_reason': 'refusal'}, 'REFUSED'),
            ({'content': [], 'stop_reason': 'end_turn'}, 'INVALID_RESPONSE'),
            ({'content': [{'type': 'text', 'text': 42}], 'stop_reason': 'end_turn'}, 'INVALID_RESPONSE'),
        ]
        for stop in ('pause_turn', 'tool_use', 'model_context_window_exceeded', 'compaction', 'future_value'):
            cases.append(({'content': [text], 'stop_reason': stop}, 'INCOMPLETE_RESPONSE'))
        for body in ({'content': [text]}, {'content': [text], 'stop_reason': None},
                     {'content': [text], 'stop_reason': 42}, {'content': [text], 'stop_reason': []}):
            cases.append((body, 'INVALID_RESPONSE'))
        for body, code in cases:
            with self.subTest(body=body):
                r = self.call(body=body)
                self.assertEqual(r.error_code, code)
                self.assertEqual(r.text, ''); self.assertIsNone(r.http_status)
                self.assertNotIn('HTTP 200', r.error)
                self.assertNotIn('provider explanation', r.error)
                self.assertNotIn('portfolio whose', r.error)

    def test_cut_off_messages_are_bilingual_and_name_the_limit(self):
        limit = f'{OUTPUT_TOKEN_LIMIT:,}'
        for code in ('OUTPUT_LIMIT', 'REFUSED', 'INCOMPLETE_RESPONSE'):
            en, ko = error_message(code, 'en'), error_message(code, 'ko')
            with self.subTest(code=code):
                self.assertNotEqual(en, ko)
                self.assertTrue(any('\uac00' <= c <= '\ud7a3' for c in ko))
                self.assertFalse(any('\uac00' <= c <= '\ud7a3' for c in en))
                self.assertIn('retry', en)
        en, ko = error_message('OUTPUT_LIMIT', 'en'), error_message('OUTPUT_LIMIT', 'ko')
        for message in (en, ko):
            self.assertIn(limit, message); self.assertIn('max_tokens', message)
        self.assertIn('output limit', en); self.assertIn('reasoning', en)
        self.assertIn('출력 한도', ko); self.assertIn('추론', ko)
        http = Mock(); http.post.return_value.status_code = 200
        http.post.return_value.json.return_value = {'content': [{'type': 'text', 'text': 'x'}],
                                                    'stop_reason': 'end_turn'}
        with patch.object(insights.config, 'anthropic_key', return_value='fixture-key'), \
             patch.object(insights, '_requests', http):
            insights.deep_analysis('portfolio', {'price': 42})
        sent = http.post.call_args.kwargs
        self.assertEqual(sent['json']['max_tokens'], OUTPUT_TOKEN_LIMIT)
        for key in ('stop_sequences', 'thinking', 'temperature'):
            self.assertNotIn(key, sent['json'])
        self.assertEqual(sent['timeout'], 60)

    def test_missing_configuration_or_dependency_does_not_send(self):
        http = Mock()
        with patch.object(insights.config,'anthropic_key',return_value=''), \
             patch.object(insights,'_requests',http):
            self.assertEqual(insights.deep_analysis('fx',{}).error_code,'NOT_CONFIGURED')
            self.assertFalse(insights.ai_ready())
        http.post.assert_not_called()
        with patch.object(insights.config,'anthropic_key',return_value='fixture-key'), \
             patch.object(insights,'_requests',None):
            self.assertEqual(insights.deep_analysis('fx',{}).error_code,'DEPENDENCY')

    def test_error_localization_retains_status_and_configuration_names(self):
        for code, status in [('AUTHENTICATION',401),('MODEL_NOT_FOUND',404),('BILLING',400)]:
            en, ko = error_message(code,'en',status), error_message(code,'ko',status)
            self.assertNotEqual(en,ko)
            self.assertIn(f'HTTP {status}',en);self.assertIn(f'HTTP {status}',ko)
        self.assertIn('ANTHROPIC_API_KEY',error_message('AUTHENTICATION','ko'))
        self.assertIn('QUANTGEN_AI_MODEL',error_message('MODEL_NOT_FOUND','ko'))


if __name__ == '__main__':
    unittest.main()
