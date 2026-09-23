#!/usr/bin/env python3
"""Compatibility entry point for the bundled offline routing evaluator."""
from pathlib import Path
import runpy

_source = Path(__file__).resolve().parent.parent / 'plugin/portable/scripts/evaluate_routing.py'
_namespace = runpy.run_path(str(_source), run_name='_guildhall_evaluator')
globals().update({k: v for k, v in _namespace.items() if not k.startswith('__')})
if __name__ == '__main__':
    raise SystemExit(main())
