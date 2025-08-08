import os
import random
import tkinter as tk
from tkinter import filedialog

from .display import plot
from .igl_api import init_unfold, unfold, get_all_bounds
from .import_export import load, export_svg, export_dxf
from .score import compute_deformation, compute_overall_distortion


def optimize_initial_points(vertices, faces, max_attempts=50, verbose=True):
    """
    Optimize initial fixed points selection to minimize overall distortion.
    
    Args:
        vertices: Mesh vertices array
        faces: Mesh faces array  
        max_attempts: Maximum number of optimization attempts
        verbose: Print progress information
        
    Returns:
        dict: {
            'best_face_id': int,
            'best_distortion': float, 
            'default_distortion': float,
            'improvement_percent': float,
            'optimization_history': list of (face_id, distortion) tuples
        }
    """
    if verbose:
        print(f"Optimizing initial points over {max_attempts} attempts...")
    
    num_faces = len(faces)
    optimization_history = []
    best_face_id = 0
    best_distortion = float('inf')
    default_distortion = None
    
    # Generate candidate face IDs - mix of random and boundary-biased selection
    candidate_faces = set()
    
    # Add some random faces
    random_faces = random.sample(range(num_faces), min(max_attempts // 2, num_faces))
    candidate_faces.update(random_faces)
    
    # Add boundary faces (if we can detect them easily)
    bounds = get_all_bounds(faces)
    boundary_vertices = set()
    for loop in bounds:
        boundary_vertices.update(loop)
    
    # Find faces that have vertices on boundaries
    boundary_faces = []
    for i, face in enumerate(faces):
        if any(v in boundary_vertices for v in face):
            boundary_faces.append(i)
    
    # Add some boundary faces to candidates
    if boundary_faces:
        boundary_sample = random.sample(boundary_faces, min(max_attempts // 2, len(boundary_faces)))
        candidate_faces.update(boundary_sample)
    
    # Ensure we have exactly max_attempts candidates (pad with more random if needed)
    while len(candidate_faces) < max_attempts and len(candidate_faces) < num_faces:
        candidate_faces.add(random.randint(0, num_faces - 1))
    
    candidate_faces = list(candidate_faces)[:max_attempts]
    
    for attempt, face_id in enumerate(candidate_faces):
        try:
            init_points_ids, init_points_pos, plan = init_unfold(vertices, faces, face_id)
            unwrap = unfold(vertices, faces, init_points_ids, init_points_pos)
            area_distortion = compute_deformation(vertices, faces, unwrap)
            overall_distortion = compute_overall_distortion(area_distortion)
            
            optimization_history.append((face_id, overall_distortion))
            
            # Track default (face_id=0) performance
            if face_id == 0:
                default_distortion = overall_distortion
            
            # Track best result
            if overall_distortion < best_distortion:
                best_distortion = overall_distortion
                best_face_id = face_id
                
            if verbose and attempt % 10 == 0:
                print(f"  Attempt {attempt + 1}/{max_attempts}: face_id={face_id}, distortion={overall_distortion:.4f}")
                
        except Exception as e:
            if verbose:
                print(f"  Attempt {attempt + 1} failed with face_id={face_id}: {e}")
            optimization_history.append((face_id, float('inf')))
    
    # Calculate default distortion if not already computed
    if default_distortion is None:
        try:
            init_points_ids, init_points_pos, plan = init_unfold(vertices, faces, 0)
            unwrap = unfold(vertices, faces, init_points_ids, init_points_pos)
            area_distortion = compute_deformation(vertices, faces, unwrap)
            default_distortion = compute_overall_distortion(area_distortion)
        except:
            default_distortion = float('inf')
    
    improvement_percent = ((default_distortion - best_distortion) / default_distortion) * 100 if default_distortion > 0 else 0
    
    if verbose:
        print(f"Optimization complete!")
        print(f"  Default distortion (face_id=0): {default_distortion:.4f}")
        print(f"  Best distortion (face_id={best_face_id}): {best_distortion:.4f}")
        print(f"  Improvement: {improvement_percent:.1f}%")
    
    return {
        'best_face_id': best_face_id,
        'best_distortion': best_distortion,
        'default_distortion': default_distortion,
        'improvement_percent': improvement_percent,
        'optimization_history': optimization_history
    }


def main(path_stl=None, path_svg=None, path_dxf=None, vertice_init_id=0, 
         optimize_initial_points_flag=False, max_optimization_attempts=50, skip_display=False):
    """
    Main function to flatten an STL surface.
    
    Args:
        path_stl: Path to STL file
        path_png: Path for output PNG visualization
        path_svg: Path for output SVG file
        path_dxf: Path for output DXF file
        vertice_init_id: Face ID to use for initial points (ignored if optimization enabled)
        optimize_initial_points_flag: Enable optimization of initial points
        max_optimization_attempts: Number of optimization attempts
        skip_display: Skip showing the visualization window (still saves PNG)
    """
    if not path_stl:
        root = tk.Tk()
        root.withdraw()
        path_stl = filedialog.askopenfilename(
            initialdir=os.path.join(os.path.dirname(__file__), "..", "data"),
            title="Please select a STL file having surface (Not volume) to unfold",
            filetypes=(("STL surface", "*.stl"), ("STL surface", "*.STL"))
        )
    if path_svg is None:
        path_svg = os.path.join(os.path.dirname(path_stl), ".".join(os.path.basename(path_stl).split(".")[:-1]) + ".svg")
    if path_dxf is None:
        path_dxf = os.path.join(os.path.dirname(path_stl), ".".join(os.path.basename(path_stl).split(".")[:-1]) + ".dxf")
    
    # Load mesh
    vertices, faces = load(path_stl)
    bounds = get_all_bounds(faces)
    
    # Initialize optimization results (will remain None if optimization is disabled)
    optimization_results = None
    
    # Optimize initial points if requested
    if optimize_initial_points_flag:
        optimization_results = optimize_initial_points(vertices, faces, max_optimization_attempts)
        # Use the optimized face ID
        vertice_init_id = optimization_results['best_face_id']
    
    # Perform the unfolding with the selected (or optimized) initial points
    init_points_ids, init_points_pos, plan = init_unfold(vertices, faces, vertice_init_id)
    unwrap = unfold(vertices, faces, init_points_ids, init_points_pos)
    deformation = compute_deformation(vertices, faces, unwrap)
    
    # Generate visualization and export
    if not skip_display:
        plot(vertices, faces, unwrap, init_points_pos, plan, init_points_ids, bounds, deformation, optimization_results)

    # Always export both svg and dxf by default
    export_svg(unwrap, bounds, path_svg)
    export_dxf(unwrap, bounds, path_dxf)
    
    # Return results for programmatic use
    return {
        'vertices': vertices,
        'faces': faces,
        'unwrap': unwrap,
        'deformation': deformation,
        'optimization_results': optimization_results,
        'face_id_used': vertice_init_id
    }
