import sys 

try:
    import cairosvg
except OSError as e:
    print(f"An OS error occurred during import: {e}, please make sure CairoSVG is installed and on the dynamic library path.", file=sys.stderr)
    print(f"On Mac with cairosvg installed using Homebrew, I need:\nxport DYLD_LIBRARY_PATH=/opt/homebrew/lib", file=sys.stderr)
    # You can add specific handling logic here,
    # such as providing a fallback or logging the error.
    sys.exit(-1)
except ImportError as e:
    print(f"An import error occurred: {e}")
    # Handle cases where the module simply isn't found
except Exception as e:
    print(f"An unexpected error occurred during import: {e}")
    # Catch any other unforeseen exceptions