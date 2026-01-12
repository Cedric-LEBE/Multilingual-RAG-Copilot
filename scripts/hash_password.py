from __future__ import annotations

import sys
from passlib.hash import argon2

def main() -> int:
    if len(sys.argv) != 2:
        print('Usage: python scripts/hash_password.py "your_password"')
        return 1
    print(argon2.hash(sys.argv[1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
