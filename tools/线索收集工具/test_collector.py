import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import collector as c


def video(**changes):
    return {"platform": "douyin", "kind": "video", "video_id": "123456789", "text": "模拟线索，仅测试", **changes}


def response(items, cursor=0, more=False, code=0):
    return {"data": {"error_code": code, "list": items, "cursor": cursor, "has_more": more}}


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="clue-collector-test-")
        self.base = Path(self.temp.name)
        self.store = c.Store(self.base / "private")

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def read_export(self):
        path, _ = self.store.export()
        return json.loads(path.read_text())

    def import_rows(self, rows, **envelope):
        path = self.base / "input.json"
        path.write_text(json.dumps({"records": rows, **envelope}), encoding="utf-8")
        return c.import_file(self.store, path)

    def test_normalize_dedup_tracks_observations_and_omits_profile(self):
        rows = [video(video_id="000123456789", avatar="test-avatar", nickname="test-name", phone="00000"),
                {"platform": "douyin", "source_url": "https://www.douyin.com/video/123456789?utm_source=test", "text": "模拟更新"}]
        result = self.import_rows(rows)
        self.assertEqual((result["record_count"], result["new_record_count"]), (2, 1))
        exported = self.read_export()
        row = exported["records"][0]
        self.assertEqual(row["source_url"], "https://www.douyin.com/video/123456789")
        self.assertEqual(row["observation_count"], 2)
        self.assertEqual(row["verification_status"], "unverified")
        dump = json.dumps(exported)
        self.assertNotIn("test-avatar", dump)
        self.assertNotIn("test-name", dump)
        self.assertNotIn("00000", dump)
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM observations").fetchone()[0], 2)

    def test_comment_parent_link_and_reply(self):
        self.import_rows([video(sec_item_id="opaque/+="),
            {"platform": "douyin", "kind": "comment", "sec_item_id": "opaque/+=", "comment_id": "c1", "content": "模拟评论"},
            {"platform": "douyin", "kind": "comment", "video_id": "123456789", "comment_id": "c2", "parent_comment_id": "c1"}])
        rows = {r["record_key"]: r for r in self.read_export()["records"]}
        self.assertEqual(rows["douyin:comment:c1"]["parent_video_key"], "douyin:video:123456789")
        self.assertEqual(rows["douyin:comment:c1"]["source_url"], "https://www.douyin.com/video/123456789")
        self.assertEqual(rows["douyin:comment:c2"]["missing_parent_records"], [])

    def test_conflicting_id_rejects_entire_import(self):
        with self.assertRaises(c.IntakeError):
            self.import_rows([video(), video(source_url="https://www.douyin.com/video/99")])
        self.assertEqual(self.read_export()["records"], [])

    def test_conflicting_comment_parent_rolls_back(self):
        self.import_rows([{**video(), "kind": "comment", "comment_id": "c1"}])
        with self.assertRaises(c.IntakeError):
            self.import_rows([video(), {**video(video_id="987"), "kind": "comment", "comment_id": "c1"}])
        self.assertEqual(len(self.read_export()["records"]), 1)

    def test_conflicting_public_id_under_same_alias_rolls_back(self):
        self.import_rows([video(sec_item_id="same-opaque-id")])
        with self.assertRaises(c.IntakeError):
            self.import_rows([video(video_id="999", sec_item_id="same-opaque-id")])
        self.assertEqual(self.read_export()["records"][0]["source_ids"]["video_id"], "123456789")

    def test_missing_parents_and_source_url_explicit(self):
        self.import_rows([{"platform": "douyin", "kind": "comment", "sec_item_id": "opaque", "comment_id": "c1", "parent_comment_id": "c0"}])
        row = self.read_export()["records"][0]
        self.assertEqual(len(row["missing_parent_records"]), 2)
        self.assertTrue(row["missing_source_url"])

    def test_bilibili_url_and_comment_fragment(self):
        row = c.normalize({"platform": "bilibili", "kind": "comment", "source_url": "https://m.bilibili.com/video/BV1xx411c7mD/?spm_id_from=test#reply456", "content": {"message": "模拟"}})
        self.assertEqual(row["source_ids"]["comment_id"], "456")
        self.assertEqual(row["source_url"], "https://www.bilibili.com/video/BV1xx411c7mD#reply456")
        self.assertEqual(row["text"], "模拟")

    def test_bilibili_av_ids_and_cross_platform_dedup(self):
        self.import_rows([video(), {"platform": "bilibili", "video_id": "av000123"}, {"platform": "bilibili", "aid": 123}])
        self.assertEqual(len(self.read_export()["records"]), 2)

    def test_unsupported_url_and_short_link_require_id(self):
        for url in ("https://douyin.com.evil.test/video/123", "file:///video/123", "https://u:p@www.douyin.com/video/123"):
            with self.assertRaises(c.IntakeError):
                c.normalize(video(source_url=url))
        with self.assertRaises(c.IntakeError):
            c.normalize({"platform": "douyin", "source_url": "https://v.douyin.com/abc/"})
        self.assertEqual(c.normalize(video(source_url="https://v.douyin.com/abc/?x=1"))["source_url"], "https://v.douyin.com/abc/")

    def test_jsonl_platform_and_capture_time(self):
        path = self.base / "input.jsonl"
        path.write_text('\ufeff' + json.dumps({"video_id": "123", "captured_at": "2026-10-08T12:00:00+08:00"}) + '\n\n')
        c.import_file(self.store, path, "douyin")
        self.assertEqual(self.read_export()["records"][0]["captured_at"], "2026-10-08T04:00:00+00:00")
        with self.assertRaises(c.IntakeError):
            c.normalize(video(captured_at="2026-10-08T12:00:00"))

    def test_source_published_at_iso_epoch_missing_and_invalid(self):
        source = c.normalize(video(source_published_at="2026-10-08T12:00:00+08:00", captured_at="2026-10-08T13:00:00+08:00"))
        self.assertEqual(source["source_published_at"], "2026-10-08T04:00:00+00:00")
        self.assertNotEqual(source["source_published_at"], source["captured_at"])
        self.assertEqual(c.normalize(video(create_time=1609459200))["source_published_at"], "2021-01-01T00:00:00+00:00")
        self.assertIsNone(c.normalize(video())["source_published_at"])
        for value in ("not-a-timestamp", "2026-10-08T12:00:00"):
            with self.assertRaises(c.IntakeError):
                c.normalize(video(source_published_at=value))
        for value in (True, "invalid", -1, 1609459200000):
            with self.assertRaises(c.IntakeError):
                c.normalize(video(create_time=value))

    def test_duplicate_preserves_published_time_and_comment_locator(self):
        common = {"platform": "douyin", "kind": "comment", "video_id": "123456789", "comment_id": "987"}
        self.import_rows([{**common, "source_url": "https://www.douyin.com/video/123456789?comment_id=987", "create_time": 1609459200}])
        self.import_rows([common])
        row = self.read_export()["records"][0]
        self.assertEqual(row["source_published_at"], "2021-01-01T00:00:00+00:00")
        self.assertEqual(row["source_url_scope"], "comment_locator")
        self.assertTrue(row["source_url"].endswith("?comment_id=987"))

    def test_pagination_unknown_and_declared_complete(self):
        result = self.import_rows([video()])
        self.assertFalse(result["complete"])
        result = self.import_rows([video()], pagination={"complete": True, "has_more": True})
        self.assertFalse(result["complete"])
        result = self.import_rows([video()], pagination={"complete": True, "has_more": False})
        self.assertTrue(result["complete"])
        self.assertEqual(result["completeness_basis"], "user_provided_not_independently_verified")

    def test_private_output_location_and_modes(self):
        with self.assertRaises(c.IntakeError):
            c.private_path(c.WORKSPACE / "概念展示站" / "review.json")
        path, _ = self.store.export()
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.store.directory.stat().st_mode & 0o777, 0o700)

    def test_export_cannot_overwrite_database_or_hardlink(self):
        self.import_rows([video()])
        alias = self.base / "database-hardlink.json"
        os.link(self.store.database_path, alias)
        for target in (self.store.database_path, alias, Path(str(self.store.database_path) + "-wal")):
            with self.assertRaises(c.IntakeError):
                self.store.export(target)
        self.assertEqual(len(self.read_export()["records"]), 1)

    def test_douyin_pagination_spacing_and_tokens_not_persisted(self):
        calls, sleeps = [], []
        def transport(endpoint, params, token):
            calls.append((endpoint, params, token))
            return response([{"sec_item_id": "opaque", "share_url": "https://www.douyin.com/video/123", "title": "模拟"}], 7, len(calls) == 1)
        adapter = c.OfficialDouyin(1, transport=transport, sleep=sleeps.append, clock=lambda: 0)
        rows, meta = adapter.collect("search", {"keyword": "模拟已审核业务关键词", "open_id": "fake-open-id", "count": 10}, "FAKE_TOKEN")
        self.store.add_run(rows, meta)
        self.assertTrue(meta["complete"])
        self.assertEqual([x[1]["cursor"] for x in calls], [0, 7])
        self.assertEqual(sleeps, [1])
        self.assertNotIn("FAKE_TOKEN", json.dumps(self.read_export()))
        self.assertNotIn("fake-open-id", json.dumps(self.read_export()))

    def test_page_and_request_caps_preserve_incomplete(self):
        for pages, requests, reason in ((1, 3, "page_cap"), (3, 1, "request_cap")):
            api = c.OfficialDouyin(transport=lambda *a: response([], 9, True))
            rows, meta = api.collect("comments", {"sec_item_id": "fake", "count": 10}, "fake", pages=pages, max_requests=requests)
            self.assertFalse(meta["complete"])
            self.assertEqual(meta["stop_reason"], reason)
            self.assertEqual(meta["next_cursor"], 9)

    def test_repeated_cursor_stop_and_error_stop(self):
        for payload, reason in ((response([], 0, True), "repeated_cursor"), (response([], code=1), "error"), ({"data": {}}, "error")):
            api = c.OfficialDouyin(transport=lambda *a: payload)
            rows, meta = api.collect("comments", {"sec_item_id": "fake", "count": 10}, "fake")
            self.assertFalse(meta["complete"])
            self.assertEqual(meta["stop_reason"], reason)
            self.assertEqual(meta["request_count"], 1)

    def test_partial_error_preserves_successful_page(self):
        payloads = iter([response([{"comment_id": "c1", "content": "模拟"}], 5, True), {"data": {"error_code": 1, "description": "FAKE_TOKEN"}}])
        api = c.OfficialDouyin(transport=lambda *a: next(payloads), sleep=lambda x: None)
        rows, meta = api.collect("comments", {"sec_item_id": "opaque", "count": 10}, "FAKE_TOKEN")
        self.assertEqual(len(rows), 1)
        self.assertEqual(meta["pages_fetched"], 1)
        self.assertEqual(meta["stop_reason"], "error")
        self.assertNotIn("FAKE_TOKEN", json.dumps(meta))

    def test_token_kind_selection_cli_and_missing_credentials(self):
        with patch.dict(os.environ, {}, clear=True), contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(c.main(["--store", str(self.base / "missing"), "douyin-search", "--keyword", "模拟"]), 2)
        self.assertIn("令牌", err.getvalue())
        self.assertFalse((self.base / "missing").exists())
        seen = []
        def collect(self, endpoint, params, token, **limits):
            seen.append((endpoint, token, params))
            return [], {"stop_reason": "has_more_false", "complete": True}
        with patch.dict(os.environ, {"DOUYIN_USER_ACCESS_TOKEN": "user-fake", "DOUYIN_CLIENT_ACCESS_TOKEN": "client-fake", "DOUYIN_OPEN_ID": "open-fake"}), patch.object(c.OfficialDouyin, "collect", collect), contextlib.redirect_stdout(io.StringIO()):
            c.main(["--store", str(self.base / "cli"), "douyin-search", "--keyword", "模拟"])
            c.main(["--store", str(self.base / "cli"), "douyin-comments", "--sec-item-id", "opaque"])
        self.assertEqual([x[1] for x in seen], ["user-fake", "client-fake"])
        self.assertNotIn("open_id", seen[1][2])

    def test_network_builder_fixed_endpoint_encoding_no_proxy_redirect(self):
        captured = {}
        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit): return b'{"data":{}}'
        class FakeOpener:
            def open(self, request, timeout):
                captured["request"] = request
                return FakeResponse()
        def build(*handlers):
            captured["handlers"] = handlers
            return FakeOpener()
        with patch.object(c.urllib.request, "build_opener", build):
            c.OfficialDouyin._http("comments", {"sec_item_id": "x/+=", "cursor": 0, "count": 10}, "FAKE_TOKEN")
        req = captured["request"]
        self.assertTrue(req.full_url.startswith(c.ENDPOINTS["comments"] + "?"))
        self.assertIn("sec_item_id=x%2F%2B%3D", req.full_url)
        self.assertEqual(req.get_header("Access-token"), "FAKE_TOKEN")
        self.assertNotIn("FAKE_TOKEN", req.full_url)
        self.assertEqual(captured["handlers"][0].proxies, {})
        with self.assertRaises(c.IntakeError):
            captured["handlers"][1].redirect_request(None, None, 302, None, None, "https://example.com")

    def test_limits_and_opaque_ids(self):
        with self.assertRaises(c.IntakeError):
            c.OfficialDouyin(interval=0.1)
        api = c.OfficialDouyin(transport=lambda *a: self.fail("network should not be called"))
        with self.assertRaises(c.IntakeError):
            api.collect("search", {"keyword": "x", "open_id": "y", "count": 10}, "fake", pages=11)
        row = c.normalize({"platform": "douyin", "item_id": "opaque", "share_url": "https://www.douyin.com/video/123"})
        self.assertEqual(row["source_ids"]["item_id"], "opaque")


if __name__ == "__main__":
    unittest.main()
