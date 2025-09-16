"""Test Runner for Gateway Service."""
import pytest
import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import main
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_tests():
    """Run all tests for the gateway service."""
    print("🚀 Running Gateway Service Tests")
    print("=" * 50)

    # Test arguments
    args = [
        "-v",  # verbose output
        "--tb=short",  # shorter traceback format
        "--strict-markers",  # strict marker validation
        "--disable-warnings",  # disable warnings
        "tests/"  # test directory
    ]

    # Run pytest
    exit_code = pytest.main(args)

    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code: {exit_code}")

    return exit_code

def run_tests_with_coverage():
    """Run tests with coverage report."""
    print("📊 Running Gateway Service Tests with Coverage")
    print("=" * 50)

    args = [
        "-v",
        "--tb=short",
        "--cov=.",
        "--cov-report=html",
        "--cov-report=term-missing",
        "tests/"
    ]

    exit_code = pytest.main(args)

    if exit_code == 0:
        print("\n✅ All tests passed!")
        print("📄 Coverage report generated in htmlcov/index.html")
    else:
        print(f"\n❌ Tests failed with exit code: {exit_code}")

    return exit_code

def run_specific_test(test_file):
    """Run a specific test file."""
    print(f"🎯 Running specific test: {test_file}")
    print("=" * 50)

    args = ["-v", f"tests/{test_file}"]
    exit_code = pytest.main(args)

    return exit_code

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "coverage":
            sys.exit(run_tests_with_coverage())
        elif sys.argv[1] == "specific":
            if len(sys.argv) > 2:
                sys.exit(run_specific_test(sys.argv[2]))
            else:
                print("Usage: python test_runner.py specific <test_file>")
                sys.exit(1)
        else:
            print("Usage: python test_runner.py [coverage|specific <test_file>]")
            sys.exit(1)
    else:
        sys.exit(run_tests())
