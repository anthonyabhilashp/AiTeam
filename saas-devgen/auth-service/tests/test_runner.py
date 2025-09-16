#!/usr/bin/env python3
"""Test Runner for Auth Service."""
import subprocess
import sys
import os
from pathlib import Path


def run_tests(test_type="all", verbose=False, coverage=False):
    """Run the specified type of tests."""
    base_dir = Path(__file__).parent
    os.chdir(base_dir)

    # Set Python path to include the workspace root
    workspace_root = base_dir.parent.parent.parent  # Go up to AiTeam directory
    env = os.environ.copy()
    env['PYTHONPATH'] = str(workspace_root)

    # Base pytest command
    cmd = ["python", "-m", "pytest"]

    if verbose:
        cmd.append("-v")

    if coverage:
        cmd.extend([
            "--cov=../main.py",
            "--cov-report=html",
            "--cov-report=term-missing"
        ])

    # Test selection based on type
    if test_type == "unit":
        cmd.extend(["-m", "not integration and not security"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    elif test_type == "security":
        cmd.extend(["-m", "security"])
    elif test_type == "auth":
        cmd.append("tests/test_auth.py")
    elif test_type == "user":
        cmd.append("tests/test_user.py")
    elif test_type == "performance":
        cmd.extend(["-m", "performance", "--durations=10"])
    else:
        # Run all tests
        cmd.append("tests/")

    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False, env=env)

    return result.returncode == 0


def run_specific_test(test_file, test_name=None):
    """Run a specific test."""
    base_dir = Path(__file__).parent
    os.chdir(base_dir)

    # Set Python path to include the workspace root
    workspace_root = base_dir.parent.parent.parent  # Go up to AiTeam directory
    env = os.environ.copy()
    env['PYTHONPATH'] = str(workspace_root)

    cmd = ["python", "-m", "pytest", test_file, "-v"]

    if test_name:
        cmd.extend(["-k", test_name])

    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False, env=env)

    return result.returncode == 0


def show_help():
    """Show help information."""
    help_text = """
Auth Service Test Runner

Usage: python test_runner.py [command] [options]

Commands:
    all                 Run all tests (default)
    unit                Run unit tests only
    integration         Run integration tests only
    security            Run security tests only
    auth                Run authentication tests only
    user                Run user management tests only
    performance         Run performance tests only
    test <file> [name]  Run specific test file or test function

Options:
    -v, --verbose       Verbose output
    -c, --coverage      Generate coverage report
    -h, --help          Show this help

Examples:
    python test_runner.py all -v
    python test_runner.py unit --coverage
    python test_runner.py test tests/test_auth.py
    python test_runner.py test tests/test_auth.py test_login_success
    """
    print(help_text)


def main():
    """Main entry point."""
    args = sys.argv[1:]

    if not args or args[0] in ["-h", "--help"]:
        show_help()
        return

    command = args[0]
    verbose = "-v" in args or "--verbose" in args
    coverage = "-c" in args or "--coverage" in args

    # Remove flags from args
    test_args = [arg for arg in args if arg not in ["-v", "--verbose", "-c", "--coverage"]]

    if command == "test" and len(test_args) >= 2:
        test_file = test_args[1]
        test_name = test_args[2] if len(test_args) > 2 else None
        success = run_specific_test(test_file, test_name)
    elif command in ["all", "unit", "integration", "security", "auth", "user", "performance"]:
        success = run_tests(command, verbose, coverage)
    else:
        print(f"Unknown command: {command}")
        show_help()
        return

    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
