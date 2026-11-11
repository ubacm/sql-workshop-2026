"""
Run the test suite for queries.py:
    python check_all.py              # test everything
    python check_all.py songs        # only tests whose function name contains "songs"
Instructors can verify the answer key with:
    python check_all.py --solutions
"""

import sys

import checker
import db
import seed
from feature_tests import TESTS

if "--solutions" in sys.argv:
    import solutions as student_module
else:
    import queries as student_module

name_filters = [arg for arg in sys.argv[1:] if not arg.startswith("--")]

ICONS = {"pass": "✅", "fail": "❌", "todo": "⬜", "error": "💥"}

if not db.DEFAULT_DB_PATH.exists():
    seed.build_database()

results = []
current_page = None
for test in TESTS:
    if name_filters and not any(name in test["function"] for name in name_filters):
        continue

    if test["page"] != current_page:
        current_page = test["page"]
        print(f"\n{current_page}")

    result = checker.run_test(test, student_module)
    results.append(result["status"])

    args = ", ".join(repr(arg) for arg in test["args"])
    print(f"  {ICONS[result['status']]} {test['function']}({args})")
    if result["status"] in ("fail", "error"):
        for line in result["message"].splitlines():
            print(f"       {line}")

passing = results.count("pass")
todo = results.count("todo")
print(f"\n{passing}/{len(results)} passing" + (f"  ({todo} not written yet)" if todo else ""))
