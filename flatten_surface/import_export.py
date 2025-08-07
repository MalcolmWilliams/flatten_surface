import numpy as np
import svgwrite
import trimesh
import ezdxf


def load(path):
    mesh = trimesh.load_mesh(path)
    return (
        np.array(mesh.vertices, dtype=np.float64),
        np.array(mesh.faces, dtype=np.int64)
    )


def export_svg(unwrap, bounds, path_svg):
    contours = [unwrap[bound] for bound in bounds]

    min_x = float("inf")
    min_y = float("inf")
    max_x = float("-inf")
    max_y = float("-inf")

    for i, contour in enumerate(contours):
        x, y = contour.T
        min_x = min(min_x, np.min(x))
        min_y = min(min_y, np.min(y))
        max_x = max(max_x, np.max(x))
        max_y = max(max_y, np.max(y))

    # Normalize contours
    for i, contour in enumerate(contours):
        x, y = contour.T
        x -= min_x
        y -= min_y
        contours[i] = np.array([x, y]).T

    # Calculate dimensions after normalization
    width = max_x - min_x
    height = max_y - min_y
    
    # Add small margin
    margin = max(width, height) * 0.05
    width += 2 * margin
    height += 2 * margin

    # Create SVG with proper dimensions and viewBox
    dwg = svgwrite.Drawing(path_svg, size=(f'{width}mm', f'{height}mm'), 
                          viewBox=f'0 0 {width} {height}', profile='tiny')
    
    for contour in contours:
        # Apply margin offset
        adjusted_contour = contour + margin
        path_data = "M" + " L".join(f"{x},{y}" for x, y in adjusted_contour) + " Z"
        dwg.add(dwg.path(d=path_data, fill='none', stroke='black', stroke_width='0.1'))
    
    dwg.save()


def export_dxf(unwrap, bounds, path_dxf):
    """
    Export the flattened surface as DXF file for CAD import.
    
    Args:
        unwrap: 2D coordinates of all vertices
        bounds: List of boundary loops
        path_dxf: Output DXF file path
    """
    contours = [unwrap[bound] for bound in bounds]
    
    # Normalize coordinates to start from origin
    min_x = float("inf")
    min_y = float("inf")
    
    for contour in contours:
        x, y = contour.T
        min_x = min(min_x, np.min(x))
        min_y = min(min_y, np.min(y))
    
    # Create DXF document
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Add each boundary as a polyline
    for i, contour in enumerate(contours):
        # Normalize coordinates
        x, y = contour.T
        x -= min_x
        y -= min_y
        
        # Create points for polyline (add z=0 for 3D compatibility)
        points = [(float(x[j]), float(y[j]), 0.0) for j in range(len(x))]
        
        # Add closed polyline
        polyline = msp.add_lwpolyline(points, close=True)
        polyline.dxf.layer = f"BOUNDARY_{i+1}"
    
    # Save DXF file
    doc.saveas(path_dxf)
