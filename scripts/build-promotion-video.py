#!/usr/bin/env python3
"""Render a 30-second silent card preview with local FFmpeg (no uploads)."""
from pathlib import Path
import argparse, shutil, subprocess, tempfile, json
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True)
args=parser.parse_args();output=Path(args.output).expanduser().resolve()
if output.is_relative_to(ROOT):parser.error('Output must be outside repository')
if output.exists():parser.error('Output exists; choose a new path')
ffmpeg=shutil.which('ffmpeg')
if not ffmpeg:parser.error('Install official FFmpeg locally before rendering')
cards=[ROOT/'docs/promotion-kit/cards'/name for name in ['01-introduction.png','02-sources.png','03-save-and-share.png']]
if not all(p.is_file() and not p.is_symlink() for p in cards):parser.error('Generate cards first')
def quote(p):return str(p).replace("'", "'\\''")
output.parent.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='jiewangyin-promotion-') as folder:
 concat=Path(folder)/'cards.txt'
 concat.write_text(''.join("file '"+quote(p)+"'\nduration 10\n" for p in cards)+"file '"+quote(cards[-1])+"'\n")
 subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-n','-f','concat','-safe','0','-i',str(concat),
                 '-vf','scale=720:960,pad=720:1280:0:160:color=0xf8f6f0,format=yuv420p,tpad=stop_mode=clone:stop_duration=1,fps=15',
                 '-t','30','-r','15','-c:v','libx264','-preset','medium','-crf','22','-an',
                 '-movflags','+faststart',str(output)],check=True)
print(json.dumps({'video':str(output),'bytes':output.stat().st_size,'notice':'Silent self-made card preview, no recorded experiences or social publication'},ensure_ascii=False))
