import argparse
import colorama
from colorama import Fore, Style
import logging
from logging import StreamHandler
import io
from pathlib import Path
import os
import sys


logger = logging.getLogger('puncher')
colorama.init()

def test_cairosvg() -> bool:
    try:
        import cairosvg
    except OSError as e:
        print(f"\nAn OS error occurred during import: {e}, please make sure CairoSVG is installed and on the dynamic library path.", file=sys.stderr)
        print(f"\n\nOn Mac with cairosvg installed using Homebrew, I need:\nexport DYLD_LIBRARY_PATH=/opt/homebrew/lib", file=sys.stderr)
        # You can add specific handling logic here,
        # such as providing a fallback or logging the error.
        return False
    except ImportError as e:
        print(f"An import error occurred: {e}")
        # Handle cases where the module simply isn't found
        return False
    except Exception as e:
        print(f"An unexpected error occurred during import: {e}")
        # Catch any other unforeseen exceptions
        return False
    return True


def _console_message(message : str, type="PUNCHER"):
    if type == "PUNCHER":
        color = Fore.GREEN
    elif type == "ERROR":
        color = Fore.RED
    else:
        color = Fore.WHITE

    print("["+color+type+Style.RESET_ALL+f"] {message}",file=sys.stderr)
    logger.info(message)

def _switches(args : argparse.Namespace) -> str:
    switches = []
    
    for switch in ['flatten','cellboundaries','punchboundaries','printpunch']:
        switches.append( "+" + switch if getattr(args,switch) else "-" + switch )
    return ','.join(switches)

def _create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog = "puncher.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description = """Punchcard creator utility\n\n
This utility creates an image of an IBM 80-column punchcard, and in SVG output a version suitable
to print using a cutting machine like a Cricut or Silhoutte Cameo.

EXAMPLES:

  Generate the first line of a TLE and output both SVG and PNG forms to iss_tle_1.[png,svg]
  $ puncher --form svg --form png --out iss_tle_1 \
    --cstring "1 25544U 98067A   25324.86734766  .00014275  00000-0  26737-3 0  9990"

  Generate the first line of a TLE and output SVG to iss_tle_1.svg, flattening printed material to raster
  $ puncher --form svg --out iss_tle_1_flat +flatten \
    --cstring "1 25544U 98067A   25324.86734766  .00014275  00000-0  26737-3 0  9990"

DEPENDENCIES:

  libcairo2 - puncher needs to be able to find libcairo2 on the library search path.

""",
        prefix_chars="+-")

    parser.add_argument('--out',
                        required=True,
                        help="Output path stem, .svg or .png will be appended depending on --form setting")
    parser.add_argument('--form', 
                        choices=['svg','png'], 
                        action="append", 
                        default=['svg'],
                        help="specify output file form(s) and extensions, options are PNG and SVG")
    
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

    if not test_cairosvg():
        _console_message("Failure loading cairosvg library", type='ERROR')

    logger.info("puncher start")
    if args.testpattern:
        content = "&-0123456789ABCDEFGHIJKLMNOPQR/STUVWXYZ:#@'=\"[.<(+|]$*);^\\,%_>?"
    else: 
        content = args.cstring
    _console_message(f"creating punchcard with content: \"{content}\", switches={_switches(args)} ")
     
    logger.debug(f"puncher with arguments: {str(args)}")

    from puncher.puncher import PunchcardSVG, writepng, writesvg
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