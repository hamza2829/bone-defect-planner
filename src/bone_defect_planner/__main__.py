import argparse
import json
from pathlib import Path
from .pipeline import run_phantom, run_volume, public_demo


def main():
    parser = argparse.ArgumentParser(description='Learning geometry prototype, not medical software')
    commands = parser.add_subparsers(dest='command', required=True)
    demo = commands.add_parser('demo', help='Generate and evaluate three offline phantom cases')
    demo.add_argument('--output', type=Path, default=Path('artifacts'))
    demo.add_argument('--figures', type=Path, default=Path('docs'))
    volume = commands.add_parser('volume', help='Process an explicitly marked defect on a public volume')
    volume.add_argument('input', type=Path)
    volume.add_argument('--defect-mask', type=Path, required=True)
    volume.add_argument('--threshold', type=float, default=400.)
    volume.add_argument('--output', type=Path, default=Path('artifacts/public-volume'))
    public = commands.add_parser('public-demo', help='Artificially remove a surface ROI from the optional public CT')
    public.add_argument('input', type=Path)
    public.add_argument('--threshold', type=float, default=400.)
    public.add_argument('--output', type=Path, default=Path('artifacts/public-ct'))
    args = parser.parse_args()
    if args.command == 'demo':
        result = run_phantom(args.output,args.figures)
    elif args.command == 'public-demo':
        result = public_demo(args.input,args.output,args.threshold)
    else:
        result = run_volume(args.input,args.defect_mask,args.output,args.threshold)
    if args.command == 'demo':
        for row in result['cases']:
            print(f"{row['case']}: Dice={row['segmentation_dice']:.4f}, bone volume error={row['bone_volume_error_pct']:.2f}%, coverage={row['modules']['coverage_pct']:.2f}%, overshoot={row['modules']['overshoot_pct']:.2f}% ({row['modules']['fit_quality']})")
    else:
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
