#!/usr/bin/env python3
"""Local reviewed-data export. No networking, credentials, scraping or uploads."""
import argparse
import csv
import hashlib
import io
import json
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
FIELDS = {'id', 'name', 'alias', 'region', 'city', 'summary', 'verification',
          'originalVerification', 'sourceTypes', 'sources', 'capturedAt',
          'operatingStatus', 'version', 'regionNote', 'isSource', 'materials', 'stories'}
MEDIA_FIELDS = {'id', 'title', 'source_url', 'rights', 'redistribution',
                'privacy_reviewed', 'sha256', 'bytes', 'storage_relative', 'mirrors'}
ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}\Z')
EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.mp4', '.webm', '.pdf', '.txt'}
NOTICE = '来源目录，待本站核对；收录不代表违法认定、机构仍在运营或主体已确认。'


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('Expected a regular JSON file')
    return json.loads(path.read_text(encoding='utf-8-sig'))


def public_url(value, allow_http=False):
    if not isinstance(value, str):
        raise ValueError('URL must be text')
    u = urlsplit(value)
    if u.scheme not in ({'https', 'http'} if allow_http else {'https'}) or not u.hostname or u.username or u.password:
        raise ValueError('Expected a public web URL without credentials')
    # Do not accept common temporary credentials as permanent public mirrors.
    if re.search(r'(token|signature|credential|password|authorization|access_key)=', u.query, re.I):
        raise ValueError('Temporary credential URL is not a public mirror')
    return value


def validate_record(record):
    if not isinstance(record, dict) or set(record) - FIELDS:
        raise ValueError('Unexpected public record fields; export stopped')
    if not ID.fullmatch(record.get('id', '')) or not record.get('name'):
        raise ValueError('Record needs a stable ASCII ID and a name')
    for key, value in record.items():
        if key in {'sources', 'sourceTypes', 'materials', 'stories'}:
            if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
                raise ValueError('Expected a text list')
        elif key == 'isSource':
            if not isinstance(value, bool):
                raise ValueError('isSource must be boolean')
        elif not isinstance(value, str):
            raise ValueError('Expected a text field')
    if not record.get('sources'):
        raise ValueError('Record needs a public source')
    for url in record['sources']:
        public_url(url, allow_http=True)
    if record.get('materials', []) or record.get('stories', []):
        raise ValueError('This exporter handles directory records; stories use separate review')


def validate_media(media):
    if not isinstance(media, dict) or set(media) != MEDIA_FIELDS:
        raise ValueError('Media metadata fields do not match the public whitelist')
    if not ID.fullmatch(media['id']) or media['redistribution'] != 'allowed' or media['privacy_reviewed'] is not True:
        raise ValueError('Media requires an ID, redistribution permission and privacy review')
    if not isinstance(media['rights'], str) or not media['rights'].strip():
        raise ValueError('Media needs explicit rights/attribution text')
    if not isinstance(media['title'], str) or not isinstance(media['storage_relative'], str):
        raise ValueError('Media title and relative storage key must be text')
    public_url(media['source_url'])
    if not re.fullmatch(r'[0-9a-f]{64}', media['sha256']):
        raise ValueError('Media needs a SHA256')
    if type(media['bytes']) is not int or media['bytes'] < 1:
        raise ValueError('Media needs a positive byte size')
    if not isinstance(media['mirrors'], list):
        raise ValueError('Mirrors must be a list')
    for url in media['mirrors']:
        public_url(url)
    relative = Path(media['storage_relative'])
    if relative.is_absolute() or '..' in relative.parts or '\\' in media['storage_relative']:
        raise ValueError('Unsafe relative media storage key')
    if relative.suffix.lower() not in EXTENSIONS:
        raise ValueError('Unsupported public media extension')


def review_hash(entry):
    return digest(encoded({'public': entry['public'], 'media': entry.get('media', [])}))


def new_external(path):
    path = Path(path).expanduser().absolute()
    resolved = path.resolve()
    if resolved.is_relative_to(ROOT) or path.exists() or path.is_symlink():
        raise ValueError('Choose a new destination outside the public repository')
    return resolved


def init(args):
    dest = new_external(args.destination)
    source = read_json(args.from_public)
    if source.get('format') != 'jiewangyin-source-catalog-v1' or not args.accept_existing_public:
        raise ValueError('Only an explicitly accepted existing public catalog can be seeded')
    entries, seen = [], set()
    for record in source['institutions']:
        validate_record(record)
        if record['id'] in seen:
            raise ValueError('Duplicate record ID')
        seen.add(record['id'])
        entry = {'public': record, 'media': [], 'private': {},
                 'review': {'status': 'approved', 'scope': 'directory',
                            'reviewer': 'existing-public-baseline', 'date': args.date}}
        entry['review']['content_sha256'] = review_hash(entry)
        entries.append(entry)
    dest.mkdir(parents=True, mode=0o700)
    data = {'format': 'jiewangyin-private-index-v1', 'updated_at': args.date,
            'entries': entries}
    (dest / 'records.json').write_bytes(encoded(data))
    (dest / 'records.json').chmod(0o600)
    (dest / '.gitignore').write_text('vault/\noriginals/\nreceipts/\n.env*\n*.sqlite*\n*.db\n*.mp4\n*.webm\n*.jpg\n*.png\n*.zip\n', encoding='utf-8')
    (dest / 'README.md').write_text(
        '# 戒网瘾机构观察 · 私有整理索引\n\n'
        '当前仅以已公开目录初始化，不含原始私人库、真实投稿或视频原件。\n'
        'records.json保存稳定编号、待公开字段及审核状态。私有库先整理、更频繁更新；公有库仅接收审核导出。\n'
        '现有记录approved只表示原目录已公开的字段范围；verification仍为待核对。新增记录默认pending。\n'
        '修改public或media后需重新审核并绑定content_sha256；不能直接复用旧审核。\n'
        '公开工具与操作说明：https://github.com/linyoulinhai/jiewangyin-observer/blob/main/docs/replicable-workflow.md\n\n'
        '此仓库不是端到端加密保险库。真实原件、回执、联系方式与授权文件另存在本地加密归档，'
        '这里只登记不带个人身份的内部编号；请勿公开本仓库、邀请无关人员或把它整体同步到公有库。\n', encoding='utf-8')
    print(json.dumps({'seeded_public_records': len(entries), 'private_originals_imported': False}))


def approve(args):
    path = Path(args.source).resolve()
    if path.is_relative_to(ROOT):
        raise ValueError('Approval must operate on an external private index')
    data = read_json(path)
    found = [e for e in data['entries'] if e['public']['id'] == args.id]
    if len(found) != 1:
        raise ValueError('Approval requires one unique record ID')
    entry = found[0]
    validate_record(entry['public'])
    for media in entry.get('media', []):
        validate_media(media)
    entry['review'] = {'status': 'approved', 'scope': 'directory', 'reviewer': args.reviewer,
                       'date': args.date, 'content_sha256': review_hash(entry)}
    data['updated_at'] = args.date
    # This command records a human decision; it does not decide the facts or consent.
    temp = path.with_suffix('.next.json')
    if temp.exists():
        raise ValueError('Temporary approval file already exists')
    try:
        temp.write_bytes(encoded(data))
        temp.chmod(0o600)
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)
    print(json.dumps({'approved': args.id, 'review_bound_to_content': True}))


def media_file(root, relative):
    if root is None:
        raise ValueError('Public media requires --media-root containing approved derivatives')
    root = Path(root).resolve()
    current = root
    for part in Path(relative).parts:
        current /= part
        if current.is_symlink():
            raise ValueError('Symlink media is forbidden')
    if not current.resolve().is_relative_to(root) or not current.is_file():
        raise ValueError('Media must be a regular file inside approved derivative storage')
    return current


def write_zip(path, members):
    with zipfile.ZipFile(path, 'x', zipfile.ZIP_STORED) as archive:
        for name, file in sorted(members):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            with archive.open(info, 'w', force_zip64=True) as output, file.open('rb') as input_file:
                shutil.copyfileobj(input_file, output)


def export(args):
    dest = new_external(args.output)
    if not ID.fullmatch(args.version):
        raise ValueError('Use a short ASCII release version')
    data = read_json(args.source)
    if data.get('format') != 'jiewangyin-private-index-v1':
        raise ValueError('Wrong private index format')
    entries, ids, media_ids = [], set(), set()
    for entry in data['entries']:
        rid = entry['public']['id']
        if rid in ids:
            raise ValueError('Duplicate stable ID in private index')
        ids.add(rid)
        review = entry.get('review', {})
        if review.get('status') != 'approved':
            continue
        if review.get('scope') != 'directory' or not review.get('reviewer') or not review.get('date'):
            raise ValueError('Incomplete human review')
        if review.get('content_sha256') != review_hash(entry):
            raise ValueError('Reviewed content changed; review again before publishing')
        validate_record(entry['public'])
        for m in entry.get('media', []):
            validate_media(m)
            if m['id'] in media_ids:
                raise ValueError('Duplicate media ID')
            media_ids.add(m['id'])
        entries.append(entry)
    records = sorted((e['public'] for e in entries), key=lambda r: r['id'])
    previous = read_json(Path(args.previous) / 'source-catalog.json') if args.previous else {'institutions': []}
    before = {r['id']: r for r in previous['institutions']}
    after = {r['id']: r for r in records}
    changes = {'version': args.version, 'added': sorted(after.keys() - before.keys()),
               'changed': sorted(k for k in after.keys() & before.keys() if after[k] != before[k]),
               'removed': sorted(before.keys() - after.keys()),
               'notice': 'removed只指不在当前公开版中；请更新副本，旧下载文件无法保证撤回。'}
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='reviewed-export-', dir=dest.parent) as temp:
        out = Path(temp)
        for folder in ['licenses', 'media', 'packages']:
            (out / folder).mkdir()
        for name in ['SOURCE-LICENSES.txt', 'NCT-LICENSE.txt', 'PanDefense-LICENSE.txt']:
            shutil.copyfile(ROOT / 'dist' / name, out / 'licenses' / name)
        shutil.copyfile(ROOT / 'LICENSE', out / 'licenses' / 'CODE-LICENSE.txt')
        shutil.copyfile(ROOT / 'ACKNOWLEDGEMENTS.md', out / 'ACKNOWLEDGEMENTS.md')
        shutil.copyfile(ROOT / 'docs/project-providers.json', out / 'source-providers.json')
        catalog = {'format': 'jiewangyin-source-catalog-v1', 'version': args.version,
                   'notice': NOTICE, 'stats': {'records': len(records), 'version': args.version,
                   'scope': '当前公开来源记录数量，不是已核实独立机构数'}, 'institutions': records}
        (out / 'source-catalog.json').write_bytes(encoded(catalog))
        safe_js = json.dumps(catalog, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e')
        (out / 'source-catalog.js').write_text('window.KANJIAN_SOURCE_CATALOG=' + safe_js + ';\n', encoding='utf-8')
        table = io.StringIO(newline='')
        writer = csv.writer(table)
        writer.writerow(['资料编号', '名称', '别名记录', '来源地区', '来源城市', '核对状态', '来源入口', '版本'])
        for r in records:
            # Protect spreadsheet consumers from formula injection; JSON stays lossless.
            row = [r.get(k, '') for k in ['id', 'name', 'alias', 'region', 'city', 'verification']]
            row += ['; '.join(r['sources']), r.get('version', '')]
            writer.writerow(["'" + s if s.lstrip().startswith(('=', '+', '-', '@')) else s for s in row])
        (out / 'source-catalog.csv').write_bytes(table.getvalue().encode('utf-8-sig'))
        (out / 'changes.json').write_bytes(encoded(changes))
        media_index, volume, total, number = [], [], 0, 1
        limit = args.volume_mb * 1024 * 1024
        if limit < 1024 * 1024:
            raise ValueError('Volume target must be at least 1 MiB')
        for entry in sorted(entries, key=lambda e: e['public']['id']):
            for m in sorted(entry.get('media', []), key=lambda m: m['id']):
                file = media_file(args.media_root, m['storage_relative'])
                # ZIP headers/manifest take space too. Large files must be split first.
                if m['bytes'] + 65536 > limit:
                    raise ValueError('Media exceeds volume target; create playable derivative segments first')
                sha = hashlib.sha256()
                with file.open('rb') as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                        sha.update(chunk)
                if file.stat().st_size != m['bytes'] or sha.hexdigest() != m['sha256']:
                    raise ValueError('Media bytes/hash differ from reviewed metadata')
                name = 'media/' + m['id'] + file.suffix.lower()
                shutil.copyfile(file, out / name)
                if (out / name).stat().st_size != m['bytes'] or digest((out / name).read_bytes()) != m['sha256']:
                    raise ValueError('Media changed during export; retry from a stable derivative')
                if volume and total + m['bytes'] + 65536 > limit:
                    write_zip(out / 'packages' / f'media-{number:03d}.zip', volume)
                    volume, total, number = [], 0, number + 1
                volume.append((name, out / name)); total += m['bytes'] + 1024
                public = {k: v for k, v in m.items() if k not in {'storage_relative', 'privacy_reviewed'}}
                public.update(record_id=entry['public']['id'], path=name, package=f'packages/media-{number:03d}.zip')
                media_index.append(public)
        if volume:
            write_zip(out / 'packages' / f'media-{number:03d}.zip', volume)
        (out / 'media-index.json').write_bytes(encoded({'version': args.version, 'media': media_index}))
        (out / '先读我.txt').write_text(
            f'戒网瘾机构观察 · 可接力公开资料版 {args.version}\n\n'
            '手机读者：公开CSV可用表格软件查找；JSON为无损数据源；视频图片按media-index中的资料编号与分包另存。\n'
            '完整转交：保留本目录、出处、作者署名、许可与SHA256SUMS.txt；不要只转发一个网盘链接。\n'
            '本目录是可导入现有静态站的数据包，替换三个source-catalog文件后重打公开站；不是完整论坛或APP。\n'
            '更新：changes.json记录与指定上一版相比的新增、修改和移除编号；本版JSON是完整快照。\n'
            '许可证在licenses，媒体许可在media-index；散列仅校验文件一致性，不能证明指控真实或作者身份。\n'
            '提供资料走私人收件；传播者不得擅自公开投稿人身份或扩大发布范围。更正后请更新你的副本。\n', encoding='utf-8')
        files = sorted(p for p in out.rglob('*') if p.is_file())
        manifest = {'format': 'jiewangyin-reviewed-release-v1', 'version': args.version,
                    'records': len(records), 'media': len(media_index), 'files': []}
        for file in files:
            manifest['files'].append({'path': file.relative_to(out).as_posix(),
                                      'bytes': file.stat().st_size, 'sha256': digest(file.read_bytes())})
        (out / 'release-manifest.json').write_bytes(encoded(manifest))
        files.append(out / 'release-manifest.json')
        (out / 'SHA256SUMS.txt').write_text(''.join(digest(f.read_bytes()) + '  ' + f.relative_to(out).as_posix() + '\n' for f in sorted(files)), encoding='utf-8')
        # Commit output only after every check, without partial published folders.
        if dest.exists():
            raise ValueError('Output appeared during export')
        out.rename(dest)
    print(json.dumps({'public_records': len(records), 'public_media': len(media_index), 'version': args.version}))


def verify(args):
    directory = Path(args.directory).resolve()
    expected = {}
    for line in (directory / 'SHA256SUMS.txt').read_text().splitlines():
        sha, name = line.split('  ', 1)
        if name in expected or not re.fullmatch('[0-9a-f]{64}', sha):
            raise ValueError('Invalid checksum listing')
        expected[name] = sha
        path = media_file(directory, name)
        if digest(path.read_bytes()) != sha:
            raise ValueError('Checksum mismatch')
    actual = {p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file()}
    if actual != set(expected) | {'SHA256SUMS.txt'}:
        raise ValueError('Missing or unexpected files in public copy')
    print(json.dumps({'verified_files': len(expected), 'notice': 'Checks consistency, not origin authenticity'}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('init')
    p.add_argument('--from-public', required=True); p.add_argument('--destination', required=True)
    p.add_argument('--date', required=True); p.add_argument('--accept-existing-public', action='store_true')
    p.set_defaults(run=init)
    p = commands.add_parser('approve')
    p.add_argument('--source', required=True); p.add_argument('--id', required=True)
    p.add_argument('--reviewer', required=True); p.add_argument('--date', required=True)
    p.set_defaults(run=approve)
    p = commands.add_parser('export')
    p.add_argument('--source', required=True); p.add_argument('--output', required=True)
    p.add_argument('--version', required=True); p.add_argument('--previous'); p.add_argument('--media-root')
    p.add_argument('--volume-mb', type=int, default=200); p.set_defaults(run=export)
    p = commands.add_parser('verify')
    p.add_argument('directory'); p.set_defaults(run=verify)
    args = parser.parse_args()
    try:
        args.run(args)
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
        parser.exit(1, 'Export/verification stopped: ' + str(exc) + '\n')


if __name__ == '__main__':
    main()
