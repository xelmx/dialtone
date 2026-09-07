"""`python -m dialtone` - same as the `dialtone` console script.

Useful where the venv's launcher stubs can't run (Windows Smart App Control
blocks uv's unsigned `.venv/Scripts/*.exe` trampolines on some machines) but
the interpreter itself can.
"""

from .cli import main

main()
