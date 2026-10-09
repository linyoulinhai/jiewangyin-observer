#!/usr/bin/env python3
"""Bounded private evidence intake. Python 3.9+ standard library only."""
import argparse
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

WORKSPACE = Path(__file__).resolve().parents[2]
DEFAULT_STORE = Path.home() / ".local/share/jiewangyin-clues"
MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_RECORDS = 10000
ENDPOINTS = {
    "search": "https://open.douyin.com/video/search/",
    "comments": "https://open.douyin.com/video/search/comment/list/",
}
NOTICE = "PRIVATE REVIEW / 未核验；来源陈述不等于事实；含可关联来源 ID，不是匿名数据；禁止自动公开。"


class IntakeError(Exception):
    pass


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def timestamp(value=None, field="captured_at"):
    if value is None:
        return now()
    if not isinstance(value, str):
        raise IntakeError(field + " 必须是带时区的 ISO 时间")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError()
        return parsed.astimezone(dt.timezone.utc).isoformat(timespec="seconds")
    except ValueError:
        raise IntakeError(field + " 必须是带时区的 ISO 时间") from None


def published_time(row):
    value = row.get("source_published_at")
    if value is not None and value != "":
        return timestamp(value, "source_published_at")
    value = row.get("create_time")
    if value is None or value == "":
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int)) or not re.fullmatch(r"[0-9]+", str(value)):
        raise IntakeError("create_time 必须是有效的 Unix 秒时间；不接受毫秒或猜测值")
    try:
        return dt.datetime.fromtimestamp(int(value), dt.timezone.utc).isoformat(timespec="seconds")
    except (ValueError, OverflowError, OSError):
        raise IntakeError("create_time 超出有效时间范围") from None


def ident(value):
    if value is None or value == "":
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise IntakeError("来源 ID 必须为字符串或整数")
    result = str(value).strip()
    if len(result) > 512 or not result or any(ord(c) < 32 for c in result):
        raise IntakeError("来源 ID 无效")
    return result


def first(row, *keys):
    return next((row[k] for k in keys if row.get(k) is not None and row[k] != ""), None)


def public_video_id(platform, value):
    value = ident(value)
    if not value:
        return None
    if platform == "douyin":
        if not re.fullmatch(r"[0-9]+", value):
            raise IntakeError("抖音公开 video_id 必须为数字；加密 ID 请放 sec_item_id")
        return str(int(value))
    if re.fullmatch(r"[Bb][Vv][A-Za-z0-9]{10}", value):
        return "BV" + value[2:]
    if re.fullmatch(r"(?:[Aa][Vv])?[0-9]+", value):
        return "av" + str(int(re.sub(r"^[Aa][Vv]", "", value)))
    raise IntakeError("B站 video_id 必须是 BV 号或 av 号")


def clean_url(platform, value):
    if not value:
        return None, None, None
    if not isinstance(value, str) or len(value) > 4096:
        raise IntakeError("source_url 无效")
    try:
        url = urllib.parse.urlsplit(value.strip())
        host = (url.hostname or "").lower()
        allowed = ({"www.douyin.com", "douyin.com", "www.iesdouyin.com", "iesdouyin.com", "v.douyin.com"}
                   if platform == "douyin" else {"www.bilibili.com", "bilibili.com", "m.bilibili.com", "b23.tv"})
        if url.scheme not in ("https", "http") or host not in allowed or url.username or url.password or url.port not in (None, 80, 443):
            raise ValueError()
        query = urllib.parse.parse_qs(url.query)
        video_match = re.search(r"/(?:share/)?video/([0-9]+)(?:/|$)", url.path) if platform == "douyin" else re.search(r"/video/((?:BV|bv)[A-Za-z0-9]{10}|(?:av|AV)[0-9]+)(?:/|$)", url.path)
        video = public_video_id(platform, video_match.group(1)) if video_match else None
        comment = first({k: v[0] for k, v in query.items()}, "comment_id", "commentid") if platform == "douyin" else first({k: v[0] for k, v in query.items()}, "rpid")
        if platform == "bilibili" and not comment:
            match = re.fullmatch(r"reply([0-9]+)", url.fragment)
            comment = match.group(1) if match else None
        if video:
            base = video_url(platform, video)
            if comment and platform == "bilibili" and re.fullmatch(r"reply[0-9]+", url.fragment):
                base += "#" + url.fragment
            elif comment:
                # Preserve a supplied comment locator; never invent a deep-link format.
                suffix = urllib.parse.urlencode({"comment_id" if platform == "douyin" else "rpid": ident(comment)})
                base += "?" + suffix
            return base, video, ident(comment)
        # Short links remain offline references. No redirects or resolution requests.
        return urllib.parse.urlunsplit(("https", host, url.path, "", "")), None, ident(comment)
    except (ValueError, TypeError):
        raise IntakeError("source_url 必须是对应平台的公开链接") from None


def video_url(platform, video_id):
    return ("https://www.douyin.com/video/" if platform == "douyin" else "https://www.bilibili.com/video/") + video_id


def key(platform, kind, source_id):
    return platform + ":" + kind + ":" + source_id


def normalize(row, default_platform=None, captured=None):
    if not isinstance(row, dict):
        raise IntakeError("每条记录必须是 JSON 对象")
    platform = row.get("platform", default_platform)
    kind = row.get("kind", row.get("type", "video"))
    if platform not in ("douyin", "bilibili") or kind not in ("video", "comment"):
        raise IntakeError("platform 应为 douyin/bilibili；kind 应为 video/comment")
    source_url, url_video, url_comment = clean_url(platform, first(row, "source_url", "share_url", "url"))
    ids = row.get("source_ids", {})
    if not isinstance(ids, dict):
        raise IntakeError("source_ids 必须为对象")
    source = {**ids, **row}
    raw_video = first(source, "video_id", "aweme_id", "bvid", "aid")
    item_id = ident(source.get("item_id"))
    sec_id = ident(source.get("sec_item_id"))
    # Douyin item_id may be opaque. Retain it without fabricating a public URL.
    if raw_video is None and item_id and item_id.isascii() and item_id.isdecimal():
        raw_video = item_id
    video_id = public_video_id(platform, raw_video) if raw_video is not None else url_video
    if video_id and url_video and video_id != url_video:
        raise IntakeError("video_id 与来源链接冲突；请核对记录")
    video_identity = video_id or ("sec:" + sec_id if sec_id else "item:" + item_id if item_id else None)
    if not video_identity:
        raise IntakeError("缺少视频 ID；短链接需人工提供 video_id，不会联网解析")
    comment_id = ident(first(source, "comment_id", "cid", "rpid")) or url_comment
    if comment_id and url_comment and comment_id != url_comment:
        raise IntakeError("comment_id 与来源链接冲突")
    if kind == "comment" and not comment_id:
        raise IntakeError("评论需要 comment_id/rpid 和所属视频 ID")
    parent = ident(first(source, "parent_comment_id", "reply_to_comment_id", "parent"))
    if parent in ("0", comment_id):
        parent = None
    text_value = first(row, "text", "content", "message", "title", "desc") or ""
    if isinstance(text_value, dict):
        text_value = text_value.get("message", "")
    if not isinstance(text_value, str) or len(text_value) > 100000:
        raise IntakeError("正文必须是长度不超过 100000 的字符串")
    source_ids = {k: v for k, v in {"video_id": video_id, "sec_item_id": sec_id, "item_id": item_id,
                  "comment_id": comment_id if kind == "comment" else None, "parent_comment_id": parent,
                  "source_author_id": ident(first(source, "source_author_id", "comment_user_id", "author_id"))}.items() if v}
    video_key = key(platform, "video", video_identity)
    record_key = video_key if kind == "video" else key(platform, "comment", comment_id)
    aliases = [record_key]
    if kind == "video":
        aliases += [key(platform, "video", "sec:" + sec_id)] if sec_id else []
        aliases += [key(platform, "video", "item:" + item_id)] if item_id else []
    return {"record_key": record_key, "platform": platform, "kind": kind,
            "source_ids": source_ids, "source_url": source_url or (video_url(platform, video_id) if video_id else None),
            "source_url_scope": "comment_locator" if url_comment else "video" if source_url or video_id else "unavailable",
            "text": text_value, "captured_at": timestamp(row.get("captured_at", captured)),
            "source_published_at": published_time(row),
            "parent_video_key": video_key if kind == "comment" else None,
            "parent_comment_key": key(platform, "comment", parent) if kind == "comment" and parent else None,
            "verification_status": "unverified", "publication_status": "private_review_only",
            "source_claim_is_fact": False, "_aliases": sorted(set(aliases))}


def private_path(value):
    path = Path(value).expanduser().resolve()
    if path == WORKSPACE or WORKSPACE in path.parents:
        raise IntakeError("私有数据和导出须放在本项目目录之外，不能进入公开站点或发布包")
    return path


class Store:
    def __init__(self, directory):
        self.directory = private_path(directory)
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.directory, 0o700)
        self.database_path = self.directory / "intake.sqlite3"
        self.db = sqlite3.connect(self.database_path)
        os.chmod(self.database_path, 0o600)
        self.db.executescript("CREATE TABLE IF NOT EXISTS records (k TEXT PRIMARY KEY, body TEXT);"
                             "CREATE TABLE IF NOT EXISTS aliases (alias TEXT PRIMARY KEY, k TEXT);"
                             "CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, body TEXT);"
                             "CREATE TABLE IF NOT EXISTS observations (run_id TEXT, record_key TEXT, body TEXT);")

    def close(self):
        self.db.close()

    def add_run(self, records, metadata):
        run_id = uuid.uuid4().hex
        added = 0
        with self.db:
            for incoming in records:
                record = dict(incoming)
                aliases = record.pop("_aliases")
                matches = {r[0] for alias in aliases for r in self.db.execute("SELECT k FROM aliases WHERE alias=?", (alias,))}
                if len(matches) > 1:
                    raise IntakeError("来源 ID 对应多个已有记录；需人工处理，未写入本次数据")
                target = next(iter(matches), record["record_key"])
                old = self.db.execute("SELECT body FROM records WHERE k=?", (target,)).fetchone()
                previous = json.loads(old[0]) if old else None
                if previous and previous["source_ids"].get("video_id") and record["source_ids"].get("video_id") and previous["source_ids"]["video_id"] != record["source_ids"]["video_id"]:
                    raise IntakeError("同一来源别名的公开视频 ID 冲突；未写入本次数据")
                if previous and record["kind"] == "comment" and previous["parent_video_key"] != record["parent_video_key"]:
                    # Compare canonical aliases before rejecting an inconsistent parent.
                    def resolved(k):
                        result = self.db.execute("SELECT k FROM aliases WHERE alias=?", (k,)).fetchone()
                        return result[0] if result else k
                    if resolved(previous["parent_video_key"]) != resolved(record["parent_video_key"]):
                        raise IntakeError("同一评论 ID 的所属视频冲突；未写入本次数据")
                record["record_key"] = target
                self.db.execute("INSERT INTO observations VALUES (?,?,?)", (run_id, target, json.dumps(record, ensure_ascii=False)))
                if previous:
                    record["source_ids"] = {**previous["source_ids"], **record["source_ids"]}
                    precision = {"unavailable": 0, "video": 1, "comment_locator": 2}
                    if not record["source_url"] or precision[previous["source_url_scope"]] > precision[record["source_url_scope"]]:
                        record["source_url"], record["source_url_scope"] = previous["source_url"], previous["source_url_scope"]
                    record["source_published_at"] = record["source_published_at"] or previous.get("source_published_at")
                    record["parent_comment_key"] = record["parent_comment_key"] or previous["parent_comment_key"]
                    first_seen = min(previous["first_captured_at"], record["captured_at"])
                    last_seen = max(previous["last_captured_at"], record["captured_at"])
                    if record["captured_at"] < previous["captured_at"]:
                        record["text"] = previous["text"]
                        record["captured_at"] = previous["captured_at"]
                    record.update(first_captured_at=first_seen, last_captured_at=last_seen,
                                  observation_count=previous["observation_count"] + 1)
                else:
                    added += 1
                    record.update(first_captured_at=record["captured_at"], last_captured_at=record["captured_at"], observation_count=1)
                self.db.execute("INSERT OR REPLACE INTO records VALUES (?,?)", (target, json.dumps(record, ensure_ascii=False)))
                for alias in aliases:
                    self.db.execute("INSERT OR REPLACE INTO aliases VALUES (?,?)", (alias, target))
            metadata = {**metadata, "run_id": run_id, "record_count": len(records), "new_record_count": added}
            self.db.execute("INSERT INTO runs VALUES (?,?)", (run_id, json.dumps(metadata, ensure_ascii=False)))
        return metadata

    def export(self, destination=None):
        target = private_path(destination or self.directory / "review-queue.json")
        protected = [Path(str(self.database_path) + suffix) for suffix in ("", "-wal", "-shm", "-journal")]
        if any(target == path or (target.exists() and path.exists() and target.samefile(path)) for path in protected):
            raise IntakeError("导出目标不能覆盖私有数据库或其辅助文件")
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        records = [json.loads(r[0]) for r in self.db.execute("SELECT body FROM records ORDER BY k")]
        aliases = dict(self.db.execute("SELECT alias,k FROM aliases"))
        record_map = {r["record_key"]: r for r in records}
        known = set(record_map)
        for row in records:
            for field in ("parent_video_key", "parent_comment_key"):
                if row[field]:
                    row[field] = aliases.get(row[field], row[field])
            row["missing_parent_records"] = [row[f] for f in ("parent_video_key", "parent_comment_key") if row[f] and row[f] not in known]
            if not row["source_url"] and row["parent_video_key"] in known:
                parent = record_map[row["parent_video_key"]]
                row["source_url"] = parent["source_url"]
                row["source_url_scope"] = "video" if row["source_url"] else "unavailable"
            row["missing_source_url"] = not bool(row["source_url"])
        payload = {"schema_version": 1, "notice": NOTICE, "exported_at": now(), "records": records,
                   "collection_runs": [json.loads(r[0]) for r in self.db.execute("SELECT body FROM runs ORDER BY rowid")]}
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent, prefix=".review-", suffix=".tmp", delete=False) as handle:
                temporary = Path(handle.name)
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, target)
        finally:
            if temporary and temporary.exists():
                temporary.unlink()
        return target, len(records)


def import_file(store, filename, platform=None):
    path = Path(filename)
    if path.stat().st_size > MAX_FILE_BYTES:
        raise IntakeError("导入文件超过 10 MiB 限制")
    raw = path.read_bytes()
    try:
        if path.suffix.lower() == ".jsonl":
            data = [json.loads(line) for line in raw.decode("utf-8-sig").splitlines() if line.strip()]
        else:
            data = json.loads(raw.decode("utf-8-sig"))
    except (ValueError, UnicodeError):
        raise IntakeError("文件不是有效的 UTF-8 JSON/JSONL") from None
    pagination = {}
    if isinstance(data, dict):
        pagination = data.get("pagination", {})
        data = data.get("records")
    if not isinstance(data, list) or not isinstance(pagination, dict) or len(data) > MAX_RECORDS:
        raise IntakeError("需要 JSON 记录数组或 records 数组；最多 10000 条")
    if pagination.get("complete") not in (None, True, False) or pagination.get("has_more") not in (None, True, False):
        raise IntakeError("pagination.complete/has_more 必须是布尔值")
    captured = now()
    normalized = []
    for index, row in enumerate(data, 1):
        try:
            normalized.append(normalize(row, platform, captured))
        except IntakeError as exc:
            raise IntakeError("记录 %d: %s" % (index, exc)) from None
    return store.add_run(normalized, {"origin": "local_import", "captured_at": captured,
        "input_sha256": hashlib.sha256(raw).hexdigest(), "complete": pagination.get("complete") is True and pagination.get("has_more") is not True,
        "stop_reason": "provided_export", "completeness_basis": "user_provided_not_independently_verified",
        "pagination": {k: pagination[k] for k in ("complete", "has_more", "next_cursor", "pages_fetched") if k in pagination}})


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise IntakeError("official_api_redirect_blocked")


class OfficialDouyin:
    def __init__(self, interval=1.0, transport=None, sleep=time.sleep, clock=time.monotonic):
        if not math.isfinite(interval) or interval < 1.0 or interval > 60:
            raise IntakeError("请求间隔须在 1 至 60 秒之间")
        self.interval, self.sleep, self.clock = interval, sleep, clock
        self.last_request = None
        self.transport = transport or self._http

    @staticmethod
    def _http(endpoint, params, token):
        # Fixed endpoints only; no environment proxy, redirects, cookies or sessions.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        request = urllib.request.Request(ENDPOINTS[endpoint] + "?" + urllib.parse.urlencode(params),
                    headers={"access-token": token, "Content-Type": "application/json"}, method="GET")
        try:
            with opener.open(request, timeout=30) as response:
                body = response.read(MAX_FILE_BYTES + 1)
            if len(body) > MAX_FILE_BYTES:
                raise IntakeError("official_api_response_too_large")
            return json.loads(body.decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise IntakeError("official_api_http_%d" % exc.code) from None
        except (urllib.error.URLError, OSError, ValueError):
            raise IntakeError("official_api_network_or_json_error") from None

    def collect(self, endpoint, params, token, *, pages=2, max_requests=2):
        if endpoint not in ENDPOINTS or not 1 <= pages <= 10 or not 1 <= max_requests <= 50:
            raise IntakeError("接口或请求上限无效；pages 1–10，max_requests 1–50")
        if not token or any(c in token for c in "\r\n"):
            raise IntakeError("缺少有效环境变量令牌；不会保存或输出令牌")
        if not 1 <= params.get("count", 0) <= 20:
            raise IntakeError("本工具 count 限制为 1–20")
        if endpoint == "search" and (not params.get("keyword") or not params.get("open_id")):
            raise IntakeError("搜索必须指定 keyword 和 open_id")
        if endpoint == "comments" and not params.get("sec_item_id"):
            raise IntakeError("评论必须指定搜索返回的 sec_item_id")
        cursor, seen, rows, requests, fetched = 0, {0}, [], 0, 0
        meta = {"origin": "douyin_official_api", "stream": endpoint, "captured_at": now(), "complete": False,
                "scope_of_completeness": "this_endpoint_result_only; excludes replies, unavailable and historical content",
                "keyword": params.get("keyword"), "sec_item_id": params.get("sec_item_id")}
        while True:
            if requests >= max_requests:
                meta["stop_reason"] = "request_cap"
                break
            if fetched >= pages:
                meta["stop_reason"] = "page_cap"
                break
            if self.last_request is not None:
                self.sleep(max(0.0, self.interval - (self.clock() - self.last_request)))
            self.last_request = self.clock()
            requests += 1
            try:
                response = self.transport(endpoint, {**params, "cursor": cursor}, token)
                data = response.get("data") if isinstance(response, dict) else None
                extra = response.get("extra", {}) if isinstance(response, dict) else {}
                if not isinstance(data, dict) or data.get("error_code") not in (0, "0") or (isinstance(extra, dict) and extra.get("error_code", 0) not in (0, "0")):
                    raise IntakeError("official_api_error")
                items, more, next_cursor = data.get("list"), data.get("has_more"), data.get("cursor")
                if not isinstance(items, list) or type(more) not in (bool, int) or more not in (True, False, 0, 1):
                    raise IntakeError("official_api_invalid_pagination")
                if len(items) > params["count"]:
                    raise IntakeError("official_api_item_count_exceeded")
                if isinstance(next_cursor, bool) or not re.fullmatch(r"[0-9]+", str(next_cursor)):
                    raise IntakeError("official_api_invalid_cursor")
                next_cursor = int(next_cursor)
                page = []
                for item in items:
                    if not isinstance(item, dict):
                        raise IntakeError("official_api_invalid_record")
                    if endpoint == "search":
                        row = {**item, "platform": "douyin", "kind": "video"}
                    else:
                        row = {**item, "platform": "douyin", "kind": "comment", "sec_item_id": params["sec_item_id"]}
                    page.append(normalize(row, captured=now()))
                rows.extend(page)
                fetched += 1
                if not more:
                    cursor = next_cursor
                    meta.update(complete=True, stop_reason="has_more_false")
                    break
                if next_cursor in seen:
                    cursor = next_cursor
                    meta["stop_reason"] = "repeated_cursor"
                    break
                seen.add(next_cursor)
                cursor = next_cursor
            except IntakeError as exc:
                # Error text is generated locally. Never store provider descriptions or payloads.
                meta.update(stop_reason="error", error_category=str(exc) if str(exc).startswith("official_api_") else "invalid_record")
                break
        meta.update(pages_fetched=fetched, request_count=requests, next_cursor=cursor, finished_at=now())
        return rows, meta


def main(argv=None):
    parser = argparse.ArgumentParser(description=NOTICE)
    parser.add_argument("--store", default=str(DEFAULT_STORE), help="私有数据目录；必须在项目外")
    commands = parser.add_subparsers(dest="command", required=True)
    imp = commands.add_parser("import", help="导入自行合法取得的本地 JSON/JSONL")
    imp.add_argument("file")
    imp.add_argument("--platform", choices=("douyin", "bilibili"))
    exp = commands.add_parser("export", help="导出 PRIVATE REVIEW 队列")
    exp.add_argument("--output", help="默认写入私有目录 review-queue.json")
    for command in ("douyin-search", "douyin-comments"):
        api = commands.add_parser(command, help="可选官方接口；需要自行获得相应权限")
        api.add_argument("--count", type=int, default=10)
        api.add_argument("--pages", type=int, default=2)
        api.add_argument("--max-requests", type=int, default=2)
        api.add_argument("--interval", type=float, default=1.0)
        if command == "douyin-search":
            api.add_argument("--keyword", required=True)
        else:
            api.add_argument("--sec-item-id", required=True)
    args = parser.parse_args(argv)
    # New private files, including SQLite journals, are owner-only.
    os.umask(0o077)
    store = None
    try:
        if args.command == "import":
            store = Store(args.store)
            result = import_file(store, args.file, args.platform)
        elif args.command == "export":
            store = Store(args.store)
            target, count = store.export(args.output)
            print("PRIVATE REVIEW：已导出 %d 条至 %s" % (count, target))
            return 0
        else:
            endpoint = "search" if args.command == "douyin-search" else "comments"
            token = os.environ.get("DOUYIN_USER_ACCESS_TOKEN" if endpoint == "search" else "DOUYIN_CLIENT_ACCESS_TOKEN", "")
            params = {"count": args.count}
            if endpoint == "search":
                params.update(keyword=args.keyword, open_id=os.environ.get("DOUYIN_OPEN_ID", ""))
            else:
                params["sec_item_id"] = args.sec_item_id
            # Validate destination before making any network request.
            private_path(args.store)
            rows, result = OfficialDouyin(args.interval).collect(endpoint, params, token, pages=args.pages, max_requests=args.max_requests)
            store = Store(args.store)
            result = store.add_run(rows, result)
        print("PRIVATE REVIEW：本次 %d 条，新增 %d 条，完整=%s，停止原因=%s" %
              (result["record_count"], result["new_record_count"], result["complete"], result["stop_reason"]))
        return 2 if result["stop_reason"] in ("error", "repeated_cursor") else 0
    except (IntakeError, OSError, sqlite3.Error) as exc:
        # OS/SQLite errors can contain input paths; do not emit raw exceptions.
        print("错误：" + (str(exc) if isinstance(exc, IntakeError) else "本地文件或数据库操作失败"), file=sys.stderr)
        return 2
    finally:
        if store:
            store.close()


if __name__ == "__main__":
    sys.exit(main())
