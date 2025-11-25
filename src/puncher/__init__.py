try:
    import cairosvg
except OSError as e:
    print(f"An OS error occurred during import: {e}, please make sure CairoSVG is installed and on the dynamic library path.")
    # You can add specific handling logic here,
    # such as providing a fallback or logging the error.
except ImportError as e:
    print(f"An import error occurred: {e}")
    # Handle cases where the module simply isn't found
except Exception as e:
    print(f"An unexpected error occurred during import: {e}")
    # Catch any other unforeseen exceptions