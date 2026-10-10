"""Scheduled daily review: after 18:05, send only when real work continued."""
from datetime import datetime, time, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import sys

BEIJING = timezone(timedelta(hours=8))
REVIEW_PATH = Path('F:/personal-projects/daily-review/daily_review.py')


def file_has_activity(path, source, cutoff, now):
    with Path(path).open(encoding='utf-8', errors='replace') as stream:
        for line in stream:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(entry, dict):
                continue
            payload = entry.get('payload') or {}
            if not isinstance(payload, dict):
                payload = {}
            if source == 'Codex' and entry.get('type') == 'session_meta':
                origin = payload.get('source') or {}
                if 'subagent' in origin or str(payload.get('thread_source', '')).endswith('review'):
                    return False
            try:
                stamp = datetime.fromisoformat(str(entry.get('timestamp', '')).replace('Z', '+00:00'))
                if stamp.tzinfo is None:
                    stamp = stamp.replace(tzinfo=BEIJING)
            except ValueError:
                continue
            if not cutoff < stamp <= now:
                continue
            if source == 'Claude':
                if entry.get('isSidechain') or entry.get('type') not in ('user', 'assistant'):
                    continue
                message = entry.get('message') or {}
                if not isinstance(message, dict):
                    continue
                content = message.get('content') or []
                if isinstance(content, str):
                    content = [{'type': 'text', 'text': content}]
                for item in content:
                    if not isinstance(item, dict):
                        continue
                    if item.get('type') == 'tool_use' or (item.get('type') == 'text' and meaningful_text(item.get('text', ''))):
                        return True
            elif entry.get('type') == 'response_item':
                if payload.get('type') in ('function_call', 'custom_tool_call', 'local_shell_call'):
                    return True
                if payload.get('type') == 'message' and payload.get('role') in ('user', 'assistant'):
                    for item in payload.get('content') or []:
                        if isinstance(item, dict) and item.get('type') in ('input_text', 'output_text', 'text') and meaningful_text(item.get('text', '')):
                            return True
    return False


def meaningful_text(text):
    text = str(text).strip()
    return bool(text) and not text.startswith(('<', '[', '# AGENTS.md', 'Base directory for this skill', 'This session is being continued', 'System prompt', 'API Error', 'Caveat:'))


def full_day_push(push):
    def wrapped(title, body):
        lines = body.split('\n', 1)
        if lines[0].startswith('# '):
            lines[0] += '（全日版）'
        return push(title + '（全日版）', '\n'.join(lines))
    return wrapped


def run(review, now):
    now = now.astimezone(BEIJING)
    cutoff = datetime.combine(now.date(), time(18, 5), BEIJING)
    # The same job has two cron times. Allow daytime execution and its retries.
    if now.time() >= time(23, 50):
        active = any(file_has_activity(path, source, cutoff, now)
                     for source, paths in [('Claude', review.iter_claude_files(now.date())),
                                           ('Codex', review.iter_codex_files(now.date()))]
                     for path in paths)
        if not active:
            print('18:05 后没有新增工作记录，跳过晚间日报生成和推送。')
            return 0
        print('18:05 后有新增工作记录，生成全天日报（全日版）。')
        review.dingtalk_push = full_day_push(review.dingtalk_push)
        review.rss_push = full_day_push(review.rss_push)
    return review.main()


def main():
    spec = importlib.util.spec_from_file_location('daily_review', REVIEW_PATH)
    review = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = review
    spec.loader.exec_module(review)
    return run(review, datetime.now(BEIJING))


if __name__ == '__main__':
    sys.exit(main())
