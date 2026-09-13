"""Seed only model assets from a runner-local approved cache, never camera data."""
import json
import os
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]

def main():
    depot=Path(os.environ['TANAKACAP_MODEL_DEPOT']).resolve()
    config=json.loads((ROOT/'release/config.json').read_text(encoding='utf-8'))
    sources=[Path(name)/'model.onnx' for name in config['models']]+[Path(name) for name in config['root_models']]
    for relative in sources:
        source=depot/relative
        target=ROOT/'models'/relative
        if not source.is_file():raise FileNotFoundError(source)
        target.parent.mkdir(parents=True,exist_ok=True)
        if source.resolve()!=target.resolve():shutil.copy2(source,target)
        receipt=source.with_suffix('.receipt.json')
        receipt_target=target.with_suffix('.receipt.json')
        if receipt.exists() and receipt.resolve()!=receipt_target.resolve():shutil.copy2(receipt,receipt_target)

if __name__=='__main__':main()
