import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
from datetime import datetime, timezone, timedelta

spec = importlib.util.spec_from_file_location('scheduled', Path(__file__).parents[1] / 'scripts/daily_review_scheduled.py')
scheduled = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scheduled)
TZ = timezone(timedelta(hours=8))


class EveningReviewTests(unittest.TestCase):
    def has_activity(self, records, source='Codex'):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'session.jsonl'
            path.write_text('\n'.join(json.dumps(r) for r in records), encoding='utf-8')
            return scheduled.file_has_activity(path, source, datetime(2026, 10, 10, 18, 5, tzinfo=TZ), datetime(2026, 10, 10, 23, 50, tzinfo=TZ))

    def event(self, ts, payload):
        return dict(timestamp=f'2026-10-10T{ts}+08:00', type='response_item', payload=payload)

    def test_cutoff_and_metadata_do_not_trigger(self):
        self.assertFalse(self.has_activity([
            self.event('18:05:00', dict(type='function_call', name='exec')),
            dict(timestamp='2026-10-10T22:00:00+08:00', type='event_msg', payload=dict(type='token_count'))]))

    def test_old_session_new_user_message_triggers(self):
        self.assertTrue(self.has_activity([
            self.event('10:00:00', dict(type='message', role='user', content=[dict(type='input_text', text='早上工作')])),
            self.event('18:05:01', dict(type='message', role='user', content=[dict(type='input_text', text='继续修复')])),
        ]))

    def test_tool_and_assistant_trigger(self):
        for payload in [dict(type='function_call', name='exec'), dict(type='message', role='assistant', content=[dict(type='output_text', text='完成修复')])]:
            with self.subTest(payload=payload):
                self.assertTrue(self.has_activity([self.event('22:00:00', payload)]))

    def test_internal_codex_session_ignored(self):
        self.assertFalse(self.has_activity([dict(type='session_meta', payload=dict(source=dict(subagent='review'))), self.event('22:00:00', dict(type='function_call'))]))

    def test_claude_background_and_sidechain_ignored(self):
        self.assertFalse(self.has_activity([dict(timestamp='2026-10-10T22:00:00+08:00', type='progress'), dict(timestamp='2026-10-10T22:00:00+08:00', type='assistant', isSidechain=True, message=dict(content=[dict(type='tool_use', name='Edit')]))], 'Claude'))

    def test_claude_work_triggers(self):
        self.assertTrue(self.has_activity([dict(timestamp='2026-10-10T22:00:00+08:00', type='assistant', message=dict(content=[dict(type='tool_use', name='Edit')]))], 'Claude'))

    def test_no_new_work_skips_entire_generation(self):
        review = SimpleNamespace(iter_claude_files=lambda day: [], iter_codex_files=lambda day: [], main=Mock())
        self.assertEqual(scheduled.run(review, datetime(2026, 10, 10, 23, 50, tzinfo=TZ)), 0)
        review.main.assert_not_called()

    def test_daytime_unchanged_and_evening_full_title(self):
        review = SimpleNamespace(main=Mock(return_value=0), dingtalk_push=Mock(), rss_push=Mock())
        self.assertEqual(scheduled.run(review, datetime(2026, 10, 10, 18, 5, tzinfo=TZ)), 0)
        review.main.assert_called_once()
        push = Mock(return_value=True)
        scheduled.full_day_push(push)('每日工作日报', '# 每日工作日报\n\n全天内容')
        push.assert_called_once_with('每日工作日报（全日版）', '# 每日工作日报（全日版）\n\n全天内容')

    def test_evening_runs_original_full_day_generator(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'session.jsonl'
            path.write_text(json.dumps(self.event('22:00:00', dict(type='function_call', name='exec'))), encoding='utf-8')
            ding, rss = Mock(return_value=True), Mock(return_value=True)
            review = SimpleNamespace(iter_claude_files=lambda day: [], iter_codex_files=lambda day: [path], dingtalk_push=ding, rss_push=rss)
            def generate():
                review.dingtalk_push('日报', '# 日报\n全天内容')
                review.rss_push('日报', '# 日报\n全天内容')
                return 0
            review.main = Mock(side_effect=generate)
            self.assertEqual(scheduled.run(review, datetime(2026, 10, 10, 23, 50, tzinfo=TZ)), 0)
            review.main.assert_called_once_with()
            ding.assert_called_once_with('日报（全日版）', '# 日报（全日版）\n全天内容')
            rss.assert_called_once_with('日报（全日版）', '# 日报（全日版）\n全天内容')


if __name__ == '__main__':
    unittest.main()
