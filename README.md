# Puncher

This is a utility that creates IBM 80-column punchcards as SVG files.  It takes a string and produces
a punchcard image in SVG suitable for cutting on a Circut or Sihouette cutting machine.

## Usage

    % uv run python -m puncher --help
    usage: puncher.py [-h] --out OUT [--form {svg,png}] (--cstring CSTRING | --testpattern) [+flatten] [-flatten] [+cellboundaries] [-cellboundaries] [+punchboundaries] [-punchboundaries] [+printpunch] [-printpunch]

    Punchcard creator utility

    options:
    -h, --help         show this help message and exit
    --out OUT
    --form {svg,png}
    --cstring CSTRING  String to print on the card
    --testpattern      Print a test pattern
    +flatten           Do flatten printed material to a raster image
    -flatten           Don't Flatten printed material to a raster image
    +cellboundaries    Do print all the character cell boundaries
    -cellboundaries    Don't print all the character cell boundaries
    +punchboundaries   Do print all the punch hole location boundaries
    -punchboundaries   Don't print all the punch hole location boundaries
    +printpunch        Do print boxes for punch holes
    -printpunch        Don't print boxes for punch holes