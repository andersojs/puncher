import argparse
import logging
import cairosvg
import io

from puncher.puncher import PunchcardSVG

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
        svg_filename = args.out + ".svg"
        logger.info(f"writing to \"{svg_filename}\"")

        with open(svg_filename, "w") as svg_file:
            print(svg_content, file=svg_file)

    if 'png' in args.form:
        png_filename = args.out + ".png"
        logger.info(f"writing to \"{png_filename}\"")
        svg_stream = io.StringIO(svg_content.as_str())
        cairosvg.svg2png(file_obj=svg_stream, write_to=png_filename,background_color="white")