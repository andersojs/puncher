import argparse
import logging
import cairosvg
import io
from pathlib import Path

from puncher.puncher import PunchcardSVG, writepng, writesvg

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger('puncher')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog = "puncher.py",
        description = "Punchcard creator utility",
        prefix_chars="+-")

    logger.info("puncher start")

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


    args = parser.parse_args()

    if args.testpattern:
        content = "&-0123456789ABCDEFGHIJKLMNOPQR/STUVWXYZ:#@'=\"[.<(+|]$*);^\\,%_>?"
    else: 
        content = args.cstring
    logger.info(f"creating punchcard with content: \"{content}\"")
    
    logger.debug(f"puncher with arguments:\n{str(args)}")

    ps = PunchcardSVG(content)
    svg_content = ps.makesvg(flatten_printed_material=args.flatten,
                             print_cellboundaries=args.cellboundaries,
                             print_punchboundaries=args.punchboundaries,
                             print_punchboxes=args.punchboundaries,)

    if 'svg' in args.form:
        writesvg(svg_content=svg_content,path=Path('.'), stem=args.out)

    if 'png' in args.form:
        writepng(svg_content=svg_content,path=Path('.'), stem=args.out)