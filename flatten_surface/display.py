import os

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
from .score import compute_overall_distortion


def plot(vertices, faces, unwrap, init_points_pos, plan, init_points_ids, bounds, deformation, optimization_results=None):

    a, b, c, d = plan
    grid = np.meshgrid(
        np.linspace(min(vertices[:, 0]), max(vertices[:, 0]), 10),
        np.linspace(min(vertices[:, 1]), max(vertices[:, 1]), 10))

    # Determine figure layout based on whether optimization was performed
    if optimization_results is not None:
        fig = plt.figure(figsize=(18, 6))
        subplot_layout = (1, 3, 1)
    else:
        fig = plt.figure(figsize=(12, 6))
        subplot_layout = (1, 2, 1)

    # Original 3D mesh plot
    ax1 = fig.add_subplot(*subplot_layout, projection='3d')
    ax1.plot_trisurf(vertices[:, 0], vertices[:, 1], vertices[:, 2], triangles=faces, edgecolor='k', alpha=0.7, linewidth=0.1)
    ax1.plot_surface(grid[0], grid[1], (d - a * grid[0] - b * grid[1]) / c, alpha=0.5, rstride=100, cstride=100)
    ax1.scatter(*vertices[init_points_ids].T, color="red")
    [ax1.plot(*vertices[bound].T, color="green") for bound in bounds]
    ax1.set_title('Original 3D Mesh')
    ax1.set_xlabel('X')
    ax1.set_ylabel('Y')
    ax1.set_zlabel('Z')
    ax1.axis('equal')

    # 2D parameterized mesh plot
    subplot_layout = (1, 3 if optimization_results is not None else 2, 2)
    ax2 = fig.add_subplot(*subplot_layout)
    sc = ax2.tripcolor(unwrap[:, 0], unwrap[:, 1], faces, edgecolors='k', facecolors=deformation, cmap=cm.RdBu_r, linewidth=0.1)
    cbar = fig.colorbar(sc, ax=ax2)
    cbar.set_label('Area Change (%)', rotation=270, labelpad=20)
    ax2.scatter(*init_points_pos.T, color="red")
    [ax2.plot(*unwrap[bound].T, color="green") for bound in bounds]
    ax2.set_aspect('equal')
    
    # Calculate overall distortion percentage
    overall_distortion_pct = compute_overall_distortion(deformation)
    
    # Update title to show optimization results if available
    if optimization_results is not None:
        title = f'Parameterized 2D Mesh\nOverall distortion: {overall_distortion_pct:.1f}%\nRed=Stretch, Blue=Shrink'
    else:
        title = f'Parameterized 2D Mesh (LSCM)\nOverall distortion: {overall_distortion_pct:.1f}%\nRed=Stretch, Blue=Shrink'
    ax2.set_title(title)
    ax2.set_xlabel('U')
    ax2.set_ylabel('V')
    ax2.axis('equal')

    # Optimization convergence plot (if optimization was performed)
    if optimization_results is not None:
        ax3 = fig.add_subplot(1, 3, 3)
        
        # Extract optimization history
        history = optimization_results['optimization_history']
        attempts = range(1, len(history) + 1)
        distortions = [dist if dist != float('inf') else np.nan for _, dist in history]
        
        # Plot all attempts
        ax3.scatter(attempts, distortions, alpha=0.6, color='lightblue', s=20, label='All attempts')
        
        # Highlight best result
        best_idx = next(i for i, (_, dist) in enumerate(history) if dist == optimization_results['best_distortion'])
        ax3.scatter([best_idx + 1], [optimization_results['best_distortion']], 
                   color='red', s=100, marker='*', label=f'Best (attempt {best_idx + 1})')
        
        # Show default performance if different from best
        if optimization_results['default_distortion'] != optimization_results['best_distortion']:
            ax3.axhline(y=optimization_results['default_distortion'], 
                       color='orange', linestyle='--', alpha=0.7, label='Default (face_id=0)')
        
        # Add running minimum line
        running_min = []
        current_min = float('inf')
        for _, dist in history:
            if dist != float('inf'):
                current_min = min(current_min, dist)
            running_min.append(current_min if current_min != float('inf') else np.nan)
        
        ax3.plot(attempts, running_min, color='green', linewidth=2, alpha=0.8, label='Running minimum')
        
        ax3.set_xlabel('Optimization Attempt')
        ax3.set_ylabel('RMS Area Distortion')
        ax3.set_title(f'Optimization Convergence\nImprovement: {optimization_results["improvement_percent"]:.1f}%')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Set reasonable y-axis limits (exclude extreme outliers)
        valid_distortions = [d for d in distortions if not np.isnan(d)]
        if valid_distortions:
            y_range = max(valid_distortions) - min(valid_distortions)
            ax3.set_ylim(min(valid_distortions) - 0.1 * y_range, 
                        max(valid_distortions) + 0.1 * y_range)

    plt.tight_layout()
    plt.show()
