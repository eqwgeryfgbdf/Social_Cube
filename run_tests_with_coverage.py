#!/usr/bin/env python
"""
Script to run tests with coverage reporting for specific modules.
"""
import argparse
import os
import sys
import subprocess
from pathlib import Path


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run tests with coverage for specified modules')
    parser.add_argument(
        '--modules', '-m',
        nargs='+',
        default=['utils', 'dashboard.utils'],
        help='Modules to test (default: utils dashboard.utils)'
    )
    parser.add_argument(
        '--html', '-html',
        action='store_true',
        help='Generate HTML coverage report'
    )
    parser.add_argument(
        '--xml', '-xml',
        action='store_true',
        help='Generate XML coverage report'
    )
    parser.add_argument(
        '--output', '-o',
        default='coverage_reports',
        help='Output directory for coverage reports (default: coverage_reports)'
    )
    parser.add_argument(
        '--min-coverage', '-c',
        type=float,
        default=80.0,
        help='Minimum required coverage percentage (default: 80.0)'
    )
    return parser.parse_args()


def run_tests_with_coverage(modules, html=False, xml=False, output_dir='coverage_reports', min_coverage=80.0):
    """Run tests with coverage for the specified modules."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Build the command
    cmd = [
        sys.executable, '-m', 'pytest',
        f'--cov={",".join(modules)}',
        '--cov-report', 'term-missing',
    ]
    
    # Add report formats
    if html:
        cmd.extend(['--cov-report', f'html:{os.path.join(output_dir, "html")}'])
    
    if xml:
        cmd.extend(['--cov-report', f'xml:{os.path.join(output_dir, "coverage.xml")}'])
    
    # Add minimum coverage requirement
    cmd.extend(['--cov-fail-under', str(min_coverage)])
    
    # Add test files and modules
    for module in modules:
        module_path = module.replace('.', '/')
        cmd.append(module_path)
    
    # Print the command being run
    print(f"Running: {' '.join(cmd)}")
    
    # Run the command
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Print output
    print(result.stdout)
    if result.stderr:
        print(f"Errors:\n{result.stderr}", file=sys.stderr)
    
    # Generate summary report
    report_path = os.path.join(output_dir, 'coverage_summary.txt')
    with open(report_path, 'w') as f:
        f.write("Coverage Summary\n")
        f.write("===============\n\n")
        f.write(f"Date: {os.popen('date').read().strip()}\n\n")
        f.write("Modules tested:\n")
        for module in modules:
            f.write(f"- {module}\n")
        f.write("\n")
        
        # Extract coverage summary from output
        coverage_lines = [line for line in result.stdout.split('\n') if 'TOTAL' in line]
        if coverage_lines:
            f.write("Coverage Results:\n")
            f.write(coverage_lines[0] + '\n\n')
        
        # Add pass/fail status
        f.write(f"Minimum required coverage: {min_coverage}%\n")
        f.write(f"Result: {'PASSED' if result.returncode == 0 else 'FAILED'}\n")
    
    print(f"\nCoverage summary written to {report_path}")
    
    if html:
        print(f"HTML report generated in {os.path.join(output_dir, 'html')}")
    
    if xml:
        print(f"XML report generated at {os.path.join(output_dir, 'coverage.xml')}")
    
    return result.returncode


def main():
    """Main entry point."""
    args = parse_args()
    exit_code = run_tests_with_coverage(
        modules=args.modules,
        html=args.html,
        xml=args.xml,
        output_dir=args.output,
        min_coverage=args.min_coverage
    )
    sys.exit(exit_code)


if __name__ == '__main__':
    main()