def render_3d_views(shapes, output_folder=None):
    """
    Render 3D views headlessly for CLI report generation.
    Saves images to ResourceFiles/images/ relative to cwd.
    """
    try:
        from OCC.Display.OCCViewer import OffscreenRenderer
    except ImportError:
        print("[WARNING] OffscreenRenderer not available")
        return {}

    import os
    from pathlib import Path

    # Save to where the report expects: cwd/ResourceFiles/images/
    if output_folder is None:
        output_folder = Path(os.path.abspath(".")) / "ResourceFiles" / "images"
    
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    renderer = OffscreenRenderer()

    # Display shapes
    if isinstance(shapes, list):
        for shape in shapes:
            if shape is not None:
                try:
                    renderer.DisplayShape(shape, update=True)
                except Exception as e:
                    print(f"[OffscreenRenderer] Shape display error: {e}")
    elif shapes is not None:
        try:
            renderer.DisplayShape(shapes, update=True)
        except Exception as e:
            print(f"[OffscreenRenderer] Shape display error: {e}")

    renderer.FitAll()
    images = {}

    # Save as PNG (report expects .png)
    views = {
        "3d.png":    ("View_Iso",   "3D View"),
        "top.png":   ("View_Top",   "Top View"),
        "front.png": ("View_Front", "Front View"),
        "side.png":  ("View_Right", "Side View"),
    }

    for filename, (view_method, label) in views.items():
        try:
            getattr(renderer, view_method)()
            renderer.FitAll()
            path = str(output_folder / filename)
            renderer.ExportToImage(path)
            images[label] = path
            print(f"[OffscreenRenderer] Saved {label}: {path}")
        except Exception as e:
            print(f"[OffscreenRenderer] Failed {label}: {e}")

    import glob
    import os

    # Clean up auto-generated capture files from OffscreenRenderer
    for capture_file in glob.glob(str(Path(os.path.abspath(".")) / "capture-*.jpeg")):
        try:
            os.remove(capture_file)
        except Exception:
            pass

    return images