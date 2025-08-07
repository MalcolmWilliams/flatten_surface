import argparse
import os

from flatten_surface import flatten_surface


def parse_args():
    parser = argparse.ArgumentParser(
        description="Flatten 3D STL surfaces into 2D patterns using LSCM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                    # Interactive file selection, no optimization
  python main.py --optimize                        # Interactive selection with optimization (50 attempts)
  python main.py --optimize --attempts 100         # Interactive selection with 100 optimization attempts
  python main.py input.stl --optimize              # Optimize specific file
  python main.py input.stl --face-id 25            # Use specific face ID (no optimization)
  python main.py input.stl --no-display            # Skip visualization window
  python main.py input.stl --output-dxf custom.dxf # Custom DXF output path
"""
    )
    
    parser.add_argument(
        'stl_file', 
        nargs='?', 
        default=None,
        help='STL file to process (if not provided, opens file dialog)'
    )
    
    parser.add_argument(
        '--optimize', 
        action='store_true',
        help='Enable optimization of initial fixed points to reduce distortion'
    )
    
    parser.add_argument(
        '--attempts', 
        type=int, 
        default=50,
        metavar='N',
        help='Number of optimization attempts (default: 50, only used with --optimize)'
    )
    
    parser.add_argument(
        '--face-id', 
        type=int, 
        default=0,
        metavar='ID',
        help='Face ID to use for initial fixed points (default: 0, ignored if --optimize is used)'
    )
    
    parser.add_argument(
        '--output-svg',
        metavar='PATH', 
        help='Output path for SVG export (default: same as STL with .svg extension)'
    )
    
    parser.add_argument(
        '--output-dxf',
        metavar='PATH', 
        help='Output path for DXF export (default: same as STL with .dxf extension)'
    )
    
    parser.add_argument(
        '--no-display',
        action='store_true',
        help='Skip showing the visualization window (still saves PNG file)'
    )
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    # Determine STL path
    if args.stl_file:
        stl_path = args.stl_file
        if not os.path.exists(stl_path):
            print(f"Error: STL file '{stl_path}' not found.")
            exit(1)
    else:
        # If no file specified, will trigger file dialog in flatten_surface
        stl_path = None
    
    print(f"STL Surface Flattening Tool")
    print(f"===========================")
    if args.optimize:
        print(f"Optimization: ENABLED ({args.attempts} attempts)")
    else:
        print(f"Optimization: disabled")
        print(f"Using face ID: {args.face_id}")
    print()
    
    # Run the flattening process
    try:
        results = flatten_surface(
            path_stl=stl_path,
            path_svg=args.output_svg,
            path_dxf=args.output_dxf,
            vertice_init_id=args.face_id,
            optimize_initial_points_flag=args.optimize,
            max_optimization_attempts=args.attempts,
            skip_display=args.no_display
        )
        
        print("\nFlattening completed successfully!")
        if args.optimize and results['optimization_results']:
            opt = results['optimization_results']
            print(f"Optimization Results:")
            print(f"  - Default distortion: {opt['default_distortion']:.4f}")
            print(f"  - Optimized distortion: {opt['best_distortion']:.4f}")
            print(f"  - Improvement: {opt['improvement_percent']:.1f}%")
            print(f"  - Best face ID: {opt['best_face_id']}")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        exit(1)
