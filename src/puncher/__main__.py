import argparse
import logging
import cairosvg
import io
from pathlib import Path

from puncher.puncher import PunchcardSVG, writepng, writesvg

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger('puncher')

if __name__ == "__main__":
    logger.info("puncher start")
    parser = argparse.ArgumentParser(
        prog = "puncher.py",
        description = "Punchcard creator utility")
    parser.add_argument('--out',required=True)
    parser.add_argument('--form', choices=['svg','png'], action="append", default=['svg'])
    cg = parser.add_mutually_exclusive_group(required=True)
    cg.add_argument("--cstring", action="store", help="String to print on the card", required=False)
    cg.add_argument("--testpattern", action="store_true", help="Print a test pattern", required=False)
    args = parser.parse_args()

    if args.testpattern:
        content = "&-0123456789ABCDEFGHIJKLMNOPQR/STUVWXYZ:#@'=\"[.<(+|]$*);^\\,%_>?"
    else: 
        content = args.cstring
    logger.info(f"creating punchcard with content: \"{content}\"")
    
    ps = PunchcardSVG(content)
    svg_content = ps.makesvg()

    if 'svg' in args.form:
        writesvg(svg_content=svg_content,path=Path('.'), stem=args.out)

    if 'png' in args.form:
        writepng(svg_content=svg_content,path=Path('.'), stem=args.out)