#!/usr/bin/env python3
"""Package the validated historical panel and selection metadata for CI issuance."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import pandas as pd


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path,
                        help='Inputs directory from a finalized daily forecast bundle')
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError('Output already exists; choose a new template directory')

    source_manifest_path = args.source / 'manifest.json'
    source_manifest = json.loads(source_manifest_path.read_text())
    for name, expected in source_manifest['files'].items():
        if sha(args.source / name) != expected:
            raise ValueError(f'Source input hash mismatch: {name}')
    if source_manifest.get('espn', {}).get('status') != 'disabled_public_data_only':
        raise ValueError('Template must come from a public-only forecast release')

    required = ['config', 'selected_on_validation', 'best_process']
    missing = [name for name in required if name not in source_manifest]
    if missing:
        raise ValueError('Template source is missing model metadata: ' + ', '.join(missing))

    panel_path = args.source / 'validated_player_seasons.csv'
    panel = pd.read_csv(panel_path)
    keys = ['player_id', 'season_id']
    if panel[keys].isna().any().any() or panel.duplicated(keys).any():
        raise ValueError('Historical player-season panel has invalid or duplicate keys')
    target_season = int(source_manifest['config']['target_season'])
    panel = panel[panel.season_id.lt(target_season)].copy()

    args.out.mkdir(parents=True)
    panel.to_csv(args.out / panel_path.name, index=False)
    shutil.copyfile(source_manifest_path, args.out / 'source_manifest.json')
    manifest = {
        'template_version': 1,
        'source_bundle_date': source_manifest.get('current_season_source', {}).get('before_date'),
        'source_manifest_sha256': sha(source_manifest_path),
        'source_manifest_file': 'source_manifest.json',
        'source_panel_sha256': sha(panel_path),
        'config': source_manifest['config'],
        'selected_on_validation': source_manifest['selected_on_validation'],
        'best_process': source_manifest['best_process'],
        'files': {
            panel_path.name: sha(args.out / panel_path.name),
            'source_manifest.json': sha(args.out / 'source_manifest.json'),
        },
    }
    (args.out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (args.out / 'README.md').write_text(
        '# Daily forecast model template\n\n'
        f"Prepared from the validated forecast inputs dated {manifest['source_bundle_date']}. "
        'Contains the historical player-season panel and model-selection metadata needed '
        'to issue daily forecasts. NHL current-season rows are excluded by the issuer before '
        'the new date is rebuilt.\n\n'
        'The source manifest records the NHL public API acquisitions, validation settings, '
        'and code hashes used for this model snapshot. This compact artifact is an issuance '
        'input; it is not a new model fit.\n')
    print('Forecast template:', args.out)
    print('Historical player-season rows:', len(panel))


if __name__ == '__main__':
    main()
