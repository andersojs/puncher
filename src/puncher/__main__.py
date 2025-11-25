import argparse
import logging
from logging import StreamHandler
import cairosvg
import io
from pathlib import Path
import os
import sys

from puncher.puncher import PunchcardSVG, writepng, writesvg

logger = logging.getLogger('puncher')

def _console_message(message : str):
    print(f"[\x1b[38;2;0;128;0mPUNCHER\x1b[0m] {message}",file=sys.stderr)
    logger.info(message)

def _switches(args : argparse.Namespace) -> str:
    switches = []
    
    for switch in ['flatten','cellboundaries','punchboundaries','printpunch']:
        switches.append( "+" + switch if getattr(args,switch) else "-" + switch )
    return ','.join(switches)

def _create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog = "puncher.py",
        description = "Punchcard creator utility",
        prefix_chars="+-")

    parser.add_argument('--out',required=True)
    parser.add_argument('--form', choices=['svg','png'], action="append", default=['svg'])
    
    cg = parser.add_mutually_exclusive_group(required=True)
    cg.add_argument("--cstring", action="store", help="String to print on the card", required=False)
    cg.add_argument("--testpattern", action="store_true", help="Print a test pattern", required=False)
    
    parser.add_argument("+flatten",action="store_true", help="Do flatten printed material to a raster image")
    parser.add_argument("-flatten",action="store_false", help="Don't Flatten printed material to a raster image")
    parser.add_argument("+cellboundaries",action="store_true", help="Do print all the character cell boundaries")
    parser.add_argument("-cellboundaries",action="store_false", help="Don't print all the character cell boundaries")
    parser.add_argument("+punchboundaries",action="store_true", help="Do print all the punch hole location boundaries")
    parser.add_argument("-punchboundaries",action="store_false", help="Don't print all the punch hole location boundaries")
    parser.add_argument("+printpunch",action="store_true", help="Do print boxes for punch holes")
    parser.add_argument("-printpunch",action="store_false", help="Don't print boxes for punch holes")
    return parser

def main():
    parser = _create_parser()
    
    debug_level = os.getenv("PUNCHER_DEBUG",None)
    if debug_level:
        print(f"STDERR Debug logging set to level={debug_level}" , file=sys.stderr)
        ch = StreamHandler(stream=sys.stderr)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        logger.setLevel(debug_level)

    args = parser.parse_args()

    logger.info("puncher start")
    if args.testpattern:
        content = "&-0123456789ABCDEFGHIJKLMNOPQR/STUVWXYZ:#@'=\"[.<(+|]$*);^\\,%_>?"
    else: 
        content = args.cstring
    _console_message(f"creating punchcard with content: \"{content}\", switches={_switches(args)} ")
     
    logger.debug(f"puncher with arguments: {str(args)}")

    ps = PunchcardSVG(content)
    svg_content = ps.makesvg(flatten_printed_material=args.flatten,
                             print_cellboundaries=args.cellboundaries,
                             print_punchboundaries=args.punchboundaries,
                             print_punchboxes=args.printpunch,)

    if 'svg' in args.form:
        _console_message(f"writing SVG to: {args.out}.svg")
        writesvg(svg_content=svg_content,path=Path('.'), stem=args.out)


    if 'png' in args.form:
        _console_message(f"writing PNG to: {args.out}.png")
        writepng(svg_content=svg_content,path=Path('.'), stem=args.out)

if __name__ == "__main__":
    sys.exit(main())