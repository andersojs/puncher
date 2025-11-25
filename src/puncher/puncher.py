from pydoc import text
import svg 
import logging
from typing import Callable
from textwrap import dedent
from pathlib import Path
import io

try:
    import cairosvg
except OSError as e:
    print(f"An OS error occurred during import: {e}")
    # You can add specific handling logic here,
    # such as providing a fallback or logging the error.
except ImportError as e:
    print(f"An import error occurred: {e}")
    # Handle cases where the module simply isn't found
except Exception as e:
    print(f"An unexpected error occurred during import: {e}")
    # Catch any other unforeseen exceptions
    
import base64


# https://homepage.divms.uiowa.edu/~jones/cards/codes.html

logger = logging.getLogger("puncher")


def escape(text: str) -> str:
    """Make the text safe to use in SVG/HTML.
    """
    text = text.replace("&", "&amp;")
    text = text.replace(">", "&gt;")
    text = text.replace("<", "&lt;")
    return text

class PunchcardSVG():
    # EIA RS-292 standard punchcard size
    CARD_DIM_WIDTH_IN = 7.0 + (3.0 / 8.0)
    CARD_DIM_LENGTH_IN = 3.0 + (1.0 / 4.0)
    CARD_DIM_THICKNESS_IN = 0.007

    # Card printing dimensions
    CARD_LINES_PER_INCH = 8.0     # this is basically line printer standard, punchcards set up to punch rows every other printable line
    CARD_INCHES_PER_LINE = 1.0 / CARD_LINES_PER_INCH
    CARD_INCHES_PER_COLUMN = 0.087
    CARD_COLUMNS_PER_INCH = 1.0 / CARD_INCHES_PER_COLUMN
    CARD_LEFT_MARGIN_IN = (CARD_DIM_WIDTH_IN - (CARD_INCHES_PER_COLUMN * 80)) / 2.0
    CARD_TOP_MARGIN_IN = 0.0

    # These are margins around the card itself, for the SVG or output document
    DOCUMENT_MARGIN_LEFT_IN = 0.5
    DOCUMENT_MARGIN_RIGHT_IN = 0.5
    DOCUMENT_MARGIN_TOP_IN = 0.5
    DOCUMENT_MARGIN_BOTTOM_IN = 0.5

    # These are the dimensions of the entire document, with the card itself in the center 
    # surrounded by the DOCUMENT_MARGINs 
    DOCUMENT_WIDTH_IN = DOCUMENT_MARGIN_LEFT_IN + CARD_DIM_WIDTH_IN + DOCUMENT_MARGIN_RIGHT_IN
    DOCUMENT_HEIGHT_IN = DOCUMENT_MARGIN_TOP_IN + CARD_DIM_LENGTH_IN + DOCUMENT_MARGIN_BOTTOM_IN

    # Stroke weight computation - need to do this in "user units" which is "inches"
    DPI_GUESS = 300
    STROKE_WEIGHT_1PT_IN = 1.0 / DPI_GUESS

    # Style information
    STROKE_COLOR_CUTLINES = "red"
    STROKE_COLOR_HOLE_BOUNDARIES = "grey"

    # Text labels for punchchard punch locations - 80 columns and 12 rows (0-9 + 11, 12)
    CARD_HOLE_ROW_NUMBERING = ['12','11','0', '1', '2','3','4','5','6', '7','8','9' ]
    CARD_HOLE_COLUMN_NUMBERING = [str(x) for x in list(range(1,81))]
    CARD_PUNCH_HOLE_ROWHEIGHT_IN = 0.07
    CARD_PUNCH_HOLE_COLWIDTH_IN = 0.04

    EBCD_PUNCH_RULES = {
        ' ' : [],
        '&' : ['12'],
        '-' : ['11'],
        '0' : ['0'],
        '1': ['1'],
        '2': ['2'],
        '3': ['3'],
        '4' : ['4'],
        '5': ['5'],
        '6': ['6'],
        '7': ['7'],
        '8': ['8'],
        '9': ['9'],
        'A': ['12','1'],
        'B': ['12','2'],
        'C': ['12','3'],
        'D': ['12','4'],
        'E': ['12','5'],
        'F': ['12','6'],
        'G': ['12','7'],
        'H': ['12','8'],
        'I': ['12','9'],
        'J': ['11','1'],
        'K': ['11','2'],
        'L': ['11','3'],
        'M': ['11','4'],
        'N': ['11','5'],
        'O': ['11','6'],
        'P': ['11','7'],
        'Q': ['11','8'],
        'R': ['11','9'],
        '/': ['0','1'],
        'S': ['0','2'],
        'T': ['0','3'],
        'U': ['0','4'],
        'V': ['0','5'],
        'W': ['0','6'],
        'X': ['0','7'],
        'Y': ['0','8'],
        'Z': ['0','9'],
        ':': ['2','8'],
        '#': ['3','8'],
        '@': ['4','8'],
        "'": ['5','8'],
        '=': ['6','8'],
        "\"": ['7','8'],
        "[": ['12','2','8'],
        ".": ['12','3','8'],
        "<": ['12','4','8'],
        '(': ['12','5','8'],
        '+': ['12','6','8'],
        '|': ['12','7','8'],
        ']': ['11','2','8'],
        '$': ['11','3','8'],
        '*': ['11','4','8'],
        ')': ['11','5','8'],
        ';': ['11','6','8'],
        '^': ['11','7','8'],
        "\\": ['0','2','8'],
        ',': ['0','3','8'],
        '%': ['0','4','8'],
        '_': ['0','5','8'],
        '>': ['0','6','8'],
        '?': ['0','7','8'],
    }

   
    def _character_cell_size(self) -> tuple[float, float]:
        cell_x_size = 1.0 / PunchcardSVG.CARD_COLUMNS_PER_INCH
        cell_y_size = 1.0 / PunchcardSVG.CARD_LINES_PER_INCH
        return (cell_x_size, cell_y_size)

    def _character_cell_location(self, column: int, row: int) -> tuple[float, float]:
        cell_x_location = PunchcardSVG.CARD_LEFT_MARGIN_IN + (column * PunchcardSVG.CARD_INCHES_PER_COLUMN)
        cell_y_location = PunchcardSVG.CARD_TOP_MARGIN_IN + ((row + 1) * PunchcardSVG.CARD_INCHES_PER_LINE)
        return (cell_x_location, cell_y_location)

    def _character_cell_center_location(self, column: int, row: int) -> tuple[float, float]:
        cell_x_location, cell_y_location = self._character_cell_location(column, row)
        return (cell_x_location + PunchcardSVG.CARD_INCHES_PER_COLUMN / 2.0, 
                cell_y_location - PunchcardSVG.CARD_INCHES_PER_LINE / 2.0)

    def _character_cell_location_for_punch(self, column : str, row : str) -> tuple[int, int]:
        punch_column = PunchcardSVG.CARD_HOLE_COLUMN_NUMBERING.index(column)
        punch_row = PunchcardSVG.CARD_HOLE_ROW_NUMBERING.index(row)
        
        punch_column_character_cell = punch_column
        punch_row_character_cell = punch_row * 2 + 1
        return (punch_column_character_cell, punch_row_character_cell)

    def _draw_character_cell_box(self, text_column, text_row, cell_bottomleftcorner_x, cell_bottomleftcorner_y) -> svg.Element:
        # Callable[[int, int, float, float], svg.Element]
        (cell_width, cell_height) = self._character_cell_size()
        return svg.Rect(
                x=cell_bottomleftcorner_x, 
                y=cell_bottomleftcorner_y - cell_height,
                width=cell_width, 
                height=cell_height,
                rx=0, ry=0,
                stroke="grey",
                stroke_dasharray="3 1",
                fill="transparent",
                stroke_width=PunchcardSVG.STROKE_WEIGHT_1PT_IN,
                id=f"cell_box_{text_column}_{text_row}"
            )

    def _draw_punchcard_character_grid(self, drawfunc : Callable[[int, int, float, float], svg.Element] ) -> svg.G:
        """ Calls a function for each location in the element grid,
            passing in the row/column index and the x,y location of the character cell origin.
        """
        elements : list[svg.Element] = []
        for row in range(25):
            for col in range(80):
                (x, y) = self._character_cell_location(col, row)
                element = drawfunc(text_column=col, text_row = row, cell_bottomleftcorner_x=x, cell_bottomleftcorner_y=y)
                elements.append(element)
        logger.debug(f"Character grid has {len(elements)} elements")
        return svg.G(elements=elements, 
                    id=f"character_grid_{drawfunc.__name__}" 
                    # id=f"character_grid" 
                    )    
    def _draw_character_grid(self):
        self._card_character_cells_g = self._draw_punchcard_character_grid(self._draw_character_cell_box)
        logger.debug(f"_draw_character_grid: _card_character_cells_g is a group with {len(self._card_character_cells_g.elements)}")

    def _draw_cardpunch_hole_by_holecoord(self, 
                                          hole_coord_x, 
                                          hole_coord_y,
                                          class_ : str | None = None, 
                                          fill : str = "transparent", 
                                          stroke : str | None = None) -> svg.Element:
        # print(f" row {row} index {rindex}, col {col}, index {cindex}")
        # we draw the cardpunch hole at the bottom left coordinate of the character cell
        col_location, row_location = self._character_cell_location_for_punch(hole_coord_x, hole_coord_y)
        
        # This is the lower-left cell location
        x_center, y_center = self._character_cell_center_location(col_location, row_location)
        # print(f" row {row:3} ({rindex:3}), col {col:3} ({cindex:3}) origin=({x_location:3.2f},{y_location:3.2f})in")
        punch_rectangle = svg.Rect(
                x=x_center - PunchcardSVG.CARD_PUNCH_HOLE_COLWIDTH_IN / 2.0, 
                y=y_center - PunchcardSVG.CARD_PUNCH_HOLE_ROWHEIGHT_IN / 2.0,
                width=PunchcardSVG.CARD_PUNCH_HOLE_COLWIDTH_IN, 
                height=PunchcardSVG.CARD_PUNCH_HOLE_ROWHEIGHT_IN,
                rx=0, ry=0,
                class_=class_,
                stroke=stroke,
                fill=fill,
                stroke_width=PunchcardSVG.STROKE_WEIGHT_1PT_IN,
            ) 
        return punch_rectangle

    def _define_card_style(self) -> svg.Style:
        # #996633; is IBM punchcard printed brown
        self._card_style = svg.Style(
                text=dedent(f"""
                    svg {{ background-color: #ffffff; }}
                    .collabel {{ font-size: 0.004em; font-family: monospace; fill: #996633; }}
                    .numlabel {{ font-size: 0.007em; font-family: monospace; fill: #996633; }}
                    .cardchar {{ font-size: 0.007em; font-family: monospace; fill: black; }}
                    .card_manufacturer_label  {{ font-size: 0.004em; font-family: sans-serif; fill: green;}}
                    .cardnotes {{ font-size: 0.004em; font-family: sans-serif; fill: green;}}
                    .cardpunch_boundary {{ stroke: {PunchcardSVG.STROKE_COLOR_CUTLINES}; fill: transparent; stroke-width: {PunchcardSVG.STROKE_WEIGHT_1PT_IN}; }}
                    .cardpunch_hole_boundary {{ stroke: {PunchcardSVG.STROKE_COLOR_HOLE_BOUNDARIES}; fill: transparent; stroke-width: {PunchcardSVG.STROKE_WEIGHT_1PT_IN}; }}
                """
                ),
            )

    def _draw_card_boundary(self) -> svg.G:
        box_points = [  
            [ 0, PunchcardSVG.CARD_INCHES_PER_LINE],
            [ PunchcardSVG.CARD_INCHES_PER_COLUMN, 0 ],
            [ PunchcardSVG.CARD_DIM_WIDTH_IN, 0],
            [ PunchcardSVG.CARD_DIM_WIDTH_IN, PunchcardSVG.CARD_DIM_LENGTH_IN],
            [ 0, PunchcardSVG.CARD_DIM_LENGTH_IN],    
        ]
        box_points_string = [ f"{x}, {y} " for [x,y] in box_points ]
        self._card_boundary_g = svg.G(id="cardpunch_boundary",                    
                    elements=[
                        svg.Polygon(stroke = PunchcardSVG.STROKE_COLOR_CUTLINES,
                                    stroke_width = PunchcardSVG.STROKE_WEIGHT_1PT_IN,
                                    points=box_points_string,
                                    class_="cardpunch_boundary")])

    def _draw_punchhole_boundaries(self) -> None:
        """Placeholder for drawing punch-hole boundary guides."""
        card_holes : list[svg.Element] = []
        for rindex, row in enumerate(PunchcardSVG.CARD_HOLE_ROW_NUMBERING):
            for cindex, col in enumerate(PunchcardSVG.CARD_HOLE_COLUMN_NUMBERING):
                # logger.debug(f"Drawing punchcard row={row} rindex={rindex} col={col}, colindex={cindex}")
                card_holes.append(self._draw_cardpunch_hole_by_holecoord(col, row, class_="cardpunch_hole_boundary"))
                
        self._card_punch_boundaries_g  = svg.G(id="cardpunch_hole_boundary", elements=card_holes) 

    def _draw_punchcard_column_label(self, row : int, col : int) -> svg.Element:
        colnumber = col + 1
        (x, y) = self._character_cell_location(col, row)
        (x_center, y_center) = (x + PunchcardSVG.CARD_INCHES_PER_COLUMN / 2.0, y - PunchcardSVG.CARD_INCHES_PER_LINE / 2.0)
        return svg.Text(x=x_center, y=y_center, text=str(colnumber), class_="collabel",text_anchor="middle", dominant_baseline="central")

    def _draw_column_number_labels(self) -> None:
        """Placeholder for drawing column number labels."""
        elements : list[svg.Element] = []
        for row in [6, 24]:
            for col in range(80):
                elements.append(self._draw_punchcard_column_label(row, col))
        self._card_column_number_labels = svg.G(id="column_number_labels", elements=elements)

    def _draw_punchcard_row_label(self, row : str, col : int) -> svg.Element:
        colnumber = col + 1
        col_location, row_location = self._character_cell_location_for_punch(column=str(colnumber), row=row)
        (x, y) = self._character_cell_location(col_location, row_location)
        (x_center, y_center) = (x + PunchcardSVG.CARD_INCHES_PER_COLUMN / 2.0, y - PunchcardSVG.CARD_INCHES_PER_LINE / 2.0)
        return svg.Text(x=x_center, y=y_center, text=str(row), class_="numlabel", text_anchor="middle", dominant_baseline="central")

    def _draw_row_number_labels(self) -> svg.G:
        """Placeholder for drawing row number labels."""
        elements : list[svg.Element] = []
        for row in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
            for col in range(80):
                elements.append(self._draw_punchcard_row_label(row, col))
        self._card_row_number_labels = svg.G(id="row_number_labels", elements = elements)
    
    def _draw_cardpunch_printedlabel(self, character : str, columname : str) -> list[svg.Element]:
    # elements : list[svg.Element] = []
        col = PunchcardSVG.CARD_HOLE_COLUMN_NUMBERING.index(columname)
        (x, y) = self._character_cell_location(col, 0)
        (x_center, y_center) = (x + PunchcardSVG.CARD_INCHES_PER_COLUMN / 2.0, y - PunchcardSVG.CARD_INCHES_PER_LINE / 2.0)
        
        text = escape(character)

        # logger.debug(__name__ + f"character is {character} -> {text}")
        return [svg.Text(x=x_center, y=y_center, text=text, class_="cardchar",text_anchor="middle", dominant_baseline="central")]
    
    def _draw_cardpunch_column_labels(self, character : str, columnname : str) -> list[svg.Element]:
        column_elements : list[svg.Element] = []
        column_elements.append(self._draw_cardpunch_printedlabel(character=character,columname=columnname))
        return column_elements

    def _draw_cardpunch_printblock(self, rowname : str, columnname: str) -> list[svg.Element]:
        return [self._draw_cardpunch_hole_by_holecoord(columnname, rowname, fill="blue", stroke="blue")]

    def _draw_cardpunch_cutboundary(self, rowname : str, columnname: str) -> list[svg.Element]:
        return [self._draw_cardpunch_hole_by_holecoord(columnname, rowname, class_="cardpunch_boundary", fill="transparent", stroke="blue")]


    def _draw_cardpunch_column_punches(self, character : str, columnname : str) -> list[svg.Element]:
        punch_rows = PunchcardSVG.EBCD_PUNCH_RULES.get(character, [])        
        column_elements : list[svg.Element] = []

        for rowname in punch_rows:
            column_elements.extend(self._draw_cardpunch_cutboundary(rowname, columnname))
            #column_elements.extend(self._draw_cardpunch_printblock(rowname, columnname))
            
        return column_elements

    def _draw_cardpunch_content_punches(self) -> None:
        card_holes : list[svg.Element] = []
        for index, col in enumerate(range(1,len(self.card_content)+1)):
            elements = self._draw_cardpunch_column_punches(self.card_content[index], str(col))
            card_holes.extend(elements)
        self._punched_holes_g = svg.G(id="cardpunches", elements = card_holes) 

    def _draw_cardpunch_content_labels(self) -> svg.G:
        labels = [ ]
        for index, col in enumerate(range(1,len(self.card_content)+1)):
            elements = self._draw_cardpunch_column_labels(self.card_content[index], str(col))
            labels.extend(elements)
        self._card_content_column_labels =  svg.G(id="cardpunchlabels", elements = labels) 

    def _draw_manufacturer_labeltext(self) -> svg.G:
        x_start_baseline = PunchcardSVG.CARD_LEFT_MARGIN_IN
        y_start_baseline = PunchcardSVG.CARD_DIM_LENGTH_IN - 0.03
        text = svg.Text(x=x_start_baseline, 
                        y=y_start_baseline, 
                        text=self.card_manufacturer_string, 
                        class_="card_manufacturer_label")
        self._card_manufacturer_label = svg.G(elements = [text], id="card_manufacturer_label")

    def _makesvg_content(self):
        self._define_card_style()

        # Cutlines - including the card boundary, plus any punched holes
        self._draw_card_boundary()
        self._draw_cardpunch_content_punches()
    
        # Card structure and notes (not printed by default)9
        self._draw_character_grid()
        self._draw_punchhole_boundaries()

        # Card printed Material
        self._draw_row_number_labels()
        self._draw_column_number_labels()
        self._draw_cardpunch_content_labels()
        self._draw_manufacturer_labeltext()

    def __init__(self, 
                 card_content : str, 
                 card_manufacturer_string : str = "IBM UNITED STATES LIMITED                  3081 IBM UBM JABMS WE ALL BM FOR IBM",
                 enable_document_margins : bool = True,
                 enable_punchhole_printed_cutlines : bool = False):
        
        self.card_content = card_content
        
        if card_manufacturer_string:
            self.card_manufacturer_string = card_manufacturer_string
        self.enable_document_margins = enable_document_margins

        self._card_style : svg.Style = None

        # Cutlines - including the card boundary, plus any punched holes
        self._card_boundary_g : svg.G = None
        self._punched_holes_g : svg.G = None
    
        # Card structure and notes (not printed by default)9
        self._card_character_cells_g : svg.G = None
        self._card_punch_boundaries_g : svg.G = None

        # Card printed Material
        self._card_row_number_labels : svg.G = None
        self._card_column_number_labels : svg.G = None
        self._card_content_column_labels : svg.G = None
        self._card_manufacturer_label : svg.G = None
        self._makesvg_content()

    def makesvg(self, 
                flatten_printed_material : bool = False,
                print_cellboundaries : bool = False,
                print_punchboundaries: bool = False,
                print_punchboxes : bool = True ) -> svg.SVG:
        """ Build and SVG of the punchcard with options.
        """
        logger.debug(f"Building a punchcard SVG with: "+
                     f"\n\tcard_content = \"{self.card_content}\""+
                     f"\n\tprint_cellboundaries = \"{print_cellboundaries}\""+
                     f"\n\tprint_punchboundaries = \"{print_punchboundaries}\"")
        
        # We will construct the SVG in groups representing layers

        card_layers = []
        card_layers.append(self._card_style)

        document_transform = f"translate({PunchcardSVG.DOCUMENT_MARGIN_LEFT_IN}, {PunchcardSVG.DOCUMENT_MARGIN_TOP_IN})"

        cut_lines_elements = []
        cut_lines_elements.append(self._card_boundary_g)
        cut_lines_elements.append(self._punched_holes_g)
        cut_lines_g = svg.G(id="card_cutlines",
                            transform=document_transform, 
                            elements=cut_lines_elements)
        
        structure_elements = []
        if print_cellboundaries: 
            logger.debug(f"makesvg: including _card_character_cells_g is a group with {len(self._card_character_cells_g.elements)}")
            structure_elements.append(self._card_character_cells_g)
        if print_punchboundaries: structure_elements.append(self._card_punch_boundaries_g) 
        
        print_elements = []
        print_elements.append(self._card_row_number_labels)
        print_elements.append(self._card_column_number_labels)
        print_elements.append(self._card_content_column_labels)
        print_elements.append(self._card_manufacturer_label)

        if flatten_printed_material:
            card_structure_and_notes_g : svg.G = svg.G(
                id="punchcard_structure", 
                elements=structure_elements)
            
            card_printed_material_g = svg.G( 
                id="card_printed", 
                elements=print_elements)
                        
            printsvg = svg.SVG(width=str(PunchcardSVG.CARD_DIM_WIDTH_IN) +"in", 
                height=str(PunchcardSVG.CARD_DIM_LENGTH_IN) +"in",
                elements=[self._card_style, card_printed_material_g,card_structure_and_notes_g],
                viewBox=svg.ViewBoxSpec(0, 0, 
                                        PunchcardSVG.CARD_DIM_WIDTH_IN, 
                                        PunchcardSVG.CARD_DIM_LENGTH_IN))
            svg_stream = io.StringIO(printsvg.as_str())
            png_bytes = cairosvg.svg2png(file_obj=svg_stream, 
                                        background_color="white",
                                        scale = 5)
            png_base64_bytes = base64.b64encode(png_bytes)
            png_base64_string = png_base64_bytes.decode('utf-8')
            flattened_image = svg.Image(
                width=PunchcardSVG.CARD_DIM_WIDTH_IN, 
                height=PunchcardSVG.CARD_DIM_LENGTH_IN,
                id="flattened_print",
                href="data:image/png;base64,"+png_base64_string
            )
            flattened_g = svg.G(
                transform=document_transform, 
                id="card_printed_flattened", 
                elements=[flattened_image])
            card_layers.append(flattened_g)
        else:
            card_structure_and_notes_g : svg.G = svg.G(
                transform=document_transform, 
                id="punchcard_structure", 
                elements=structure_elements)
            card_printed_material_g = svg.G(
                transform=document_transform, 
                id="card_printed", 
                elements=print_elements)

            card_layers.append(card_printed_material_g)
            card_layers.append(card_structure_and_notes_g)

        card_layers.append(cut_lines_g)

        return svg.SVG(width=str(PunchcardSVG.DOCUMENT_WIDTH_IN) +"in", 
                      height=str(PunchcardSVG.DOCUMENT_HEIGHT_IN) +"in",
                      elements=card_layers,
                      viewBox=svg.ViewBoxSpec(0, 0, PunchcardSVG.DOCUMENT_WIDTH_IN, PunchcardSVG.DOCUMENT_HEIGHT_IN)
                      )
    
def writesvg(svg_content : svg.SVG, path : Path, stem : str) -> None:
    """ Write an svg.SVG to an svg file, at the path specified, 
        with the name [stem].svg
    """
    svg_filename = path / (stem + ".svg")
    logger.info(f"writing to \"{svg_filename}\"")

    with open(svg_filename, "w") as svg_file:
        print(svg_content, file=svg_file)

def writepng(svg_content : svg.SVG, path : Path, stem : str, dpi : float = 600):
    """ Write an svg.SVG to a PNG file using cairosvg
    """
    png_filename = path / (stem + ".png")
    logger.info(f"writing to \"{png_filename}\"")
    svg_stream = io.StringIO(svg_content.as_str())
    cairosvg.svg2png(file_obj=svg_stream, 
                     write_to=str(png_filename),
                     background_color="white",
                     scale = 5)