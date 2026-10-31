"""Injected responses only: auth, billing, model, transport and privacy boundaries."""
from copy import deepcopy
import unittest
from unittest.mock import Mock, patch

import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    from core.quant import insights
from core.research.ai_connection import error_message
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
                                      {'type':'text','text':'Fixture explanation'}]})
        self.assertEqual(r.text, 'Fixture explanation'); self.assertEqual(r.error_code, '')
        for body in (None, 'bad', {'content': []}, {'content': {}},
                     {'content': [{'type':'text','text': 42}]}):
            with self.subTest(body=body):
                r = self.call(body=body)
                self.assertEqual(r.error_code, 'INVALID_RESPONSE'); self.assertEqual(r.text, '')

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
