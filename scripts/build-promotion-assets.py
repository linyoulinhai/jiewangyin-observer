#!/usr/bin/env python3
"""Render editable SVG and phone-share PNG cards locally. No remote uploads."""
from pathlib import Path
from xml.sax.saxutils import escape
import argparse, hashlib, json
from PIL import Image, ImageDraw, ImageFont
import qrcode

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/promotion-kit'
SITE = 'https://kanjian-archive-concept.chengbiliu3.chatgpt.site/'
WIDTH, HEIGHT = 1080, 1440
INK, BLUE, MUTED, PAPER, LINE = '#18243b', '#165ad5', '#5b6879', '#f8f6f0', '#dddcd5'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--font', default='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
parser.add_argument('--bold-font', default='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')
parser.add_argument('--font-index', type=int, default=2, help='SC face in the default Noto TTC')
args = parser.parse_args()
for path in [args.font, args.bold_font]:
    if not Path(path).is_file(): parser.error('Supply a local CJK font: ' + path)

qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4)
qr.add_data(SITE); qr.make(fit=True)
matrix = qr.get_matrix()
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'cards').mkdir(exist_ok=True)
qr.make_image(fill_color='black', back_color='white').save(OUT / 'site-qr.png')

class Card:
    def __init__(self):
        self.image = Image.new('RGB', (WIDTH, HEIGHT), PAPER)
        self.draw = ImageDraw.Draw(self.image)
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
                    '<title>戒网瘾机构观察 · 手机宣传卡</title>',
                    '<desc>公开来源待核对；原站二维码与作者署名。自制排版，不含真实机构指控或个人影像。</desc>',
                    f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{PAPER}"/>']
    def rect(self, x, y, w, h, fill, radius=0):
        self.draw.rounded_rectangle((x,y,x+w,y+h), radius=radius, fill=fill)
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}"/>')
    def text(self, x, y, text, size=32, color=INK, bold=False):
        path = args.bold_font if bold else args.font
        font = ImageFont.truetype(path, size, index=args.font_index if path.endswith('.ttc') else 0)
        box = self.draw.textbbox((0,0),text,font=font,anchor='lt')
        if x+box[2]>WIDTH-52 or y+box[3]>HEIGHT-28: raise ValueError('Text exceeds card: '+text)
        self.draw.text((x,y),text,font=font,fill=color,anchor='lt')
        self.svg.append(f'<text x="{x}" y="{y}" dominant-baseline="text-before-edge" font-family="Noto Sans CJK SC,Microsoft YaHei,sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}">{escape(text)}</text>')
    def line(self,x1,y1,x2,y2,color=LINE,width=2):
        self.draw.line((x1,y1,x2,y2), fill=color, width=width)
        self.svg.append(f'<path d="M{x1} {y1}L{x2} {y2}" fill="none" stroke="{color}" stroke-width="{width}"/>')
    def qr(self,x,y,module=5):
        for row, values in enumerate(matrix):
            for col, dark in enumerate(values):
                self.rect(x+col*module,y+row*module,module,module,'#000' if dark else '#fff')
    def save(self, name):
        self.image.save(OUT/'cards'/(name+'.png'), optimize=True)
        (OUT/'cards'/(name+'.svg')).write_text('\n'.join(self.svg+['</svg>']))

def header(c, number, title, subtitle):
    # The project-owned building/person symbol, redrawn as native primitives.
    c.rect(64,56,64,64,BLUE,12)
    c.line(80,105,80,72,'#fff',3);c.line(80,72,105,72,'#fff',3)
    c.line(105,72,105,105,'#fff',3);c.line(105,72,116,78,'#fff',3)
    c.line(116,78,116,105,'#fff',3)
    c.rect(88,82,8,8,'#fff',4);c.line(87,101,87,96,'#fff',3)
    c.line(87,96,98,96,'#fff',3);c.line(98,96,98,101,'#fff',3)
    c.text(150,66,'戒网瘾机构观察',36,bold=True)
    c.text(64,152,f'{number} / 03    公开资料 · 手机查阅 · 接力保存',25,MUTED)
    for i, row in enumerate(title):c.text(64,225+i*82,row,64,bold=True)
    for i,row in enumerate(subtitle):c.text(64,414+i*44,row,30,MUTED)

def row(c, n, y, title, body):
    c.line(64,y,1016,y)
    c.text(64,y+30,n,32,BLUE,bold=True)
    c.text(145,y+26,title,38,bold=True)
    for i,part in enumerate(body):c.text(145,y+83+i*40,part,29,MUTED)

def footer(c):
    c.line(64,1012,1016,1012)
    c.qr(64,1040)
    c.text(310,1050,'打开原站，先看出处',36,BLUE,bold=True)
    c.text(310,1110,'完整网址（两行连续）：',24,MUTED)
    c.text(310,1150,'https://kanjian-archive-concept.',25)
    c.text(310,1188,'chengbiliu3.chatgpt.site/',25)
    c.text(64,1272,'来源记录仍待核对，收录不等于违法认定。',26,MUTED)
    c.text(64,1318,'目录基础：FunctionSir/PanDefenseProject',24,MUTED)
    c.text(64,1355,'goodpsychologistclaw/nct-archive 及公开资料贡献者',24,MUTED)
    c.text(64,1387,'2026-10-09 · promotion-1 · 完整署名与许可随下载包保存',20,MUTED)

c=Card()
header(c,'01',['让资料留下来，','让需要的人找到。'],['关注戒网瘾、特训与封闭矫正相关机构。','一起保存资料，也支持经历这些的人。'])
row(c,'01',525,'查找机构，回到出处',['按名称、别名或地区查看公开来源。'])
row(c,'02',680,'下载公开资料，留一份副本',['表格、导读与网站包，保存后可以转交。'])
row(c,'03',835,'补充线索，参与经历互助',['个人信息走私人收件，保存自己的回执。'])
footer(c);c.save('01-introduction')

c=Card()
header(c,'02',['找到机构以后，','先看它的来源。'],['1251份待核对来源记录，不等于独立机构数。','这是一份可以补充、核对和更正的目录。'])
row(c,'01',525,'先找名称、别名与地区',['同名记录先保留，不自动认定同一主体。'])
row(c,'02',680,'查看出处、日期与核对状态',['回到原始材料，记录具体待补问题。'])
row(c,'03',835,'有新资料，再补充与更正',['不把评论或目录收录直接当作事实结论。'])
footer(c);c.save('02-sources')

c=Card()
header(c,'03',['链接会变，','保存的副本可以接力。'],['不必会写代码，也能保存和转交公开资料。','每份副本保留版本、出处与许可。'])
row(c,'01',525,'下载，另存到手机文件目录',['只收藏网页，还没有保存资料文件。'])
row(c,'02',680,'保留导读、来源与作者署名',['公开小包转交；个人资料不夹进公开包。'])
row(c,'03',835,'另一台设备，再留一份副本',['更新或更正以后，通知接力者换新版本。'])
footer(c);c.save('03-save-and-share')

artifacts = [OUT/'site-qr.png'] + sorted((OUT/'cards').glob('*'))
manifest = {'version':'2026-10-09-promotion-1','qr_url':SITE,'qr_error_correction':'M',
            'cards':[{'path':p.relative_to(OUT).as_posix(),'bytes':p.stat().st_size,
                      'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in artifacts],
            'notice':'Local code-rendered layout; no social posts or cloud uploads.'}
(OUT/'visual-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print(json.dumps({'cards':3,'editable_svg':3,'qr_url':SITE,'output':str(OUT)},ensure_ascii=False))
