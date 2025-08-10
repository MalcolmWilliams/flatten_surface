import numpy as np


def compute_deformation(vertices, faces, unwrap):
    original_edges = vertices[faces[:, [1, 2, 0]]] - vertices[faces[:, [0, 1, 2]]]
    unfolded_edges = unwrap[faces[:, [1, 2, 0]]] - unwrap[faces[:, [0, 1, 2]]]

    # original_lengths = np.linalg.norm(original_edges, axis=2)
    # unfolded_lengths = np.linalg.norm(unfolded_edges, axis=2)

    # length_ratios = unfolded_lengths / original_lengths
    #
    # original_angles = np.arccos(np.clip(np.sum(original_edges[:, 0] * original_edges[:, 1], axis=1) /
    #                                     (np.linalg.norm(original_edges[:, 0], axis=1) * np.linalg.norm(
    #                                         original_edges[:, 1], axis=1)), -1.0, 1.0))
    # unfolded_angles = np.arccos(np.clip(np.sum(unfolded_edges[:, 0] * unfolded_edges[:, 1], axis=1) /
    #                                     (np.linalg.norm(unfolded_edges[:, 0], axis=1) * np.linalg.norm(
    #                                         unfolded_edges[:, 1], axis=1)), -1.0, 1.0))

    original_areas = np.linalg.norm(np.cross(original_edges[:, 0], original_edges[:, 1]), axis=1)
    unfolded_areas = np.abs(np.cross(unfolded_edges[:, 0], unfolded_edges[:, 1]))
    area_2d = np.sum(unfolded_areas)
    area_3d = np.sum(original_areas)

    area_diff = area_3d - area_2d

    print(f"3D Area: {area_3d} mm²")
    print(f"2D Area: {area_2d} mm²")
    print(f"Diff Area: {area_diff} mm²")

    # Calculate percentage area change: positive = stretching, negative = compression
    area_change_percent = (unfolded_areas - original_areas) / original_areas * 100

    return area_change_percent


def compute_overall_distortion(area_distortion):
    """
    Compute a single scalar metric representing overall distortion across the mesh.
    Uses RMS (Root Mean Square) to give more weight to high distortion areas.
    
    Args:
        area_distortion: Array of per-triangle area distortions
        
    Returns:
        float: Overall distortion metric (lower is better)
    """
    rms_distortion = np.sqrt(np.mean(area_distortion ** 2))
    return rms_distortion
