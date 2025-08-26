#!/usr/bin/env python3
"""
Comprehensive test runner for Pollinexus API.

This module provides a complete test suite runner with:
- Unit tests
- Integration tests
- Security tests
- Performance tests
- API endpoint tests
- Database tests
"""

import sys
import os
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List, Any
import argparse
import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pollinexus.core.logging import logger, log_info, log_error
from pollinexus.core.config import settings


class TestRunner:
    """Comprehensive test runner for Pollinexus API."""
    
    def __init__(self, test_type: str = "all", verbose: bool = False, coverage: bool = True):
        self.test_type = test_type
        self.verbose = verbose
        self.coverage = coverage
        self.results = {}
        self.start_time = time.time()
        
        # Test categories
        self.test_categories = {
            "unit": "Unit tests for individual components",
            "integration": "Integration tests for component interactions",
            "api": "API endpoint tests",
            "security": "Security and vulnerability tests",
            "performance": "Performance and load tests",
            "database": "Database and data persistence tests",
            "cli": "Command-line interface tests",
            "all": "All test categories"
        }
    
    def run_tests(self) -> Dict[str, Any]:
        """Run the specified test suite."""
        log_info("Starting Pollinexus test suite", test_type=self.test_type, verbose=self.verbose)
        
        try:
            if self.test_type == "all":
                return self._run_all_tests()
            elif self.test_type in self.test_categories:
                return self._run_category_tests(self.test_type)
            else:
                raise ValueError(f"Unknown test type: {self.test_type}")
                
        except Exception as e:
            log_error("Test suite failed", error=str(e), test_type=self.test_type)
            raise
    
    def _run_all_tests(self) -> Dict[str, Any]:
        """Run all test categories."""
        log_info("Running all test categories")
        
        all_results = {}
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        
        for category in ["unit", "integration", "api", "security", "performance", "database", "cli"]:
            if category == "all":
                continue
                
            log_info(f"Running {category} tests")
            category_results = self._run_category_tests(category)
            all_results[category] = category_results
            
            total_passed += category_results.get("passed", 0)
            total_failed += category_results.get("failed", 0)
            total_skipped += category_results.get("skipped", 0)
        
        # Overall results
        all_results["overall"] = {
            "passed": total_passed,
            "failed": total_failed,
            "skipped": total_skipped,
            "total": total_passed + total_failed + total_skipped,
            "success_rate": (total_passed / (total_passed + total_failed)) * 100 if (total_passed + total_failed) > 0 else 0
        }
        
        return all_results
    
    def _run_category_tests(self, category: str) -> Dict[str, Any]:
        """Run tests for a specific category."""
        log_info(f"Running {category} tests")
        
        # Build pytest command
        cmd = self._build_pytest_command(category)
        
        # Run tests
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        end_time = time.time()
        
        # Parse results
        results = self._parse_pytest_output(result.stdout, result.stderr, result.returncode)
        results["execution_time"] = end_time - start_time
        results["category"] = category
        
        log_info(f"{category} tests completed", 
                passed=results.get("passed", 0),
                failed=results.get("failed", 0),
                execution_time=results["execution_time"])
        
        return results
    
    def _build_pytest_command(self, category: str) -> List[str]:
        """Build pytest command for the specified category."""
        cmd = ["python", "-m", "pytest"]
        
        # Add test path based on category
        if category == "unit":
            cmd.extend(["test/test_*.py", "-m", "unit"])
        elif category == "integration":
            cmd.extend(["test/test_*.py", "-m", "integration"])
        elif category == "api":
            cmd.extend(["test/test_api_*.py"])
        elif category == "security":
            cmd.extend(["test/test_security_*.py", "test/test_api_*.py", "-m", "security"])
        elif category == "performance":
            cmd.extend(["test/test_performance_*.py", "-m", "performance"])
        elif category == "database":
            cmd.extend(["test/test_database_*.py", "-m", "database"])
        elif category == "cli":
            cmd.extend(["test/test_cli_*.py", "-m", "cli"])
        else:
            cmd.extend(["test/"])
        
        # Add options
        if self.verbose:
            cmd.append("-v")
        
        if self.coverage:
            cmd.extend(["--cov=pollinexus", "--cov-report=term-missing", "--cov-report=html"])
        
        # Add additional options
        cmd.extend([
            "--tb=short",
            "--strict-markers",
            "--disable-warnings"
        ])
        
        return cmd
    
    def _parse_pytest_output(self, stdout: str, stderr: str, return_code: int) -> Dict[str, Any]:
        """Parse pytest output to extract test results."""
        results = {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "total": 0,
            "return_code": return_code,
            "stdout": stdout,
            "stderr": stderr
        }
        
        # Parse summary line
        lines = stdout.split('\n')
        for line in lines:
            if "passed" in line and "failed" in line:
                # Extract numbers from summary
                import re
                numbers = re.findall(r'(\d+)', line)
                if len(numbers) >= 3:
                    results["passed"] = int(numbers[0])
                    results["failed"] = int(numbers[1])
                    results["skipped"] = int(numbers[2])
                    results["total"] = results["passed"] + results["failed"] + results["skipped"]
                break
        
        # Calculate success rate
        if results["total"] > 0:
            results["success_rate"] = (results["passed"] / results["total"]) * 100
        else:
            results["success_rate"] = 0
        
        return results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive test report."""
        report = []
        report.append("=" * 80)
        report.append("POLLINEXUS API TEST SUITE REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Test Type: {self.test_type}")
        report.append(f"Execution Time: {time.time() - self.start_time:.2f} seconds")
        report.append("")
        
        if self.test_type == "all":
            # Overall summary
            overall = results.get("overall", {})
            report.append("OVERALL SUMMARY")
            report.append("-" * 40)
            report.append(f"Total Tests: {overall.get('total', 0)}")
            report.append(f"Passed: {overall.get('passed', 0)}")
            report.append(f"Failed: {overall.get('failed', 0)}")
            report.append(f"Skipped: {overall.get('skipped', 0)}")
            report.append(f"Success Rate: {overall.get('success_rate', 0):.1f}%")
            report.append("")
            
            # Category breakdown
            report.append("CATEGORY BREAKDOWN")
            report.append("-" * 40)
            for category, category_results in results.items():
                if category == "overall":
                    continue
                    
                report.append(f"{category.upper()}:")
                report.append(f"  Passed: {category_results.get('passed', 0)}")
                report.append(f"  Failed: {category_results.get('failed', 0)}")
                report.append(f"  Skipped: {category_results.get('skipped', 0)}")
                report.append(f"  Success Rate: {category_results.get('success_rate', 0):.1f}%")
                report.append(f"  Execution Time: {category_results.get('execution_time', 0):.2f}s")
                report.append("")
        else:
            # Single category results
            category_results = results
            report.append(f"{self.test_type.upper()} TEST RESULTS")
            report.append("-" * 40)
            report.append(f"Total Tests: {category_results.get('total', 0)}")
            report.append(f"Passed: {category_results.get('passed', 0)}")
            report.append(f"Failed: {category_results.get('failed', 0)}")
            report.append(f"Skipped: {category_results.get('skipped', 0)}")
            report.append(f"Success Rate: {category_results.get('success_rate', 0):.1f}%")
            report.append(f"Execution Time: {category_results.get('execution_time', 0):.2f}s")
            report.append("")
        
        # Security summary
        if self.test_type in ["all", "security"]:
            report.append("SECURITY ASSESSMENT")
            report.append("-" * 40)
            security_results = results.get("security", {})
            if security_results.get("failed", 0) == 0:
                report.append("✅ All security tests passed")
            else:
                report.append(f"❌ {security_results.get('failed', 0)} security tests failed")
            report.append("")
        
        # Performance summary
        if self.test_type in ["all", "performance"]:
            report.append("PERFORMANCE ASSESSMENT")
            report.append("-" * 40)
            performance_results = results.get("performance", {})
            if performance_results.get("failed", 0) == 0:
                report.append("✅ All performance tests passed")
            else:
                report.append(f"❌ {performance_results.get('failed', 0)} performance tests failed")
            report.append("")
        
        # Recommendations
        report.append("RECOMMENDATIONS")
        report.append("-" * 40)
        
        overall_failed = 0
        if self.test_type == "all":
            overall_failed = results.get("overall", {}).get("failed", 0)
        else:
            overall_failed = results.get("failed", 0)
        
        if overall_failed == 0:
            report.append("✅ All tests passed successfully!")
            report.append("✅ The application is ready for deployment.")
        else:
            report.append(f"❌ {overall_failed} tests failed.")
            report.append("❌ Please fix the failing tests before deployment.")
            report.append("❌ Review the test output for specific issues.")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def save_report(self, results: Dict[str, Any], output_file: str = None):
        """Save test results to file."""
        if output_file is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_file = f"test_results_{timestamp}.json"
        
        # Save JSON results
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Save human-readable report
        report_file = output_file.replace('.json', '.txt')
        report = self.generate_report(results)
        with open(report_file, 'w') as f:
            f.write(report)
        
        log_info("Test results saved", json_file=output_file, report_file=report_file)
        return output_file, report_file


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(description="Pollinexus API Test Runner")
    parser.add_argument(
        "--type", "-t",
        choices=["all", "unit", "integration", "api", "security", "performance", "database", "cli"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Disable coverage reporting"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file for results"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick tests only (skip slow tests)"
    )
    
    args = parser.parse_args()
    
    # Initialize test runner
    runner = TestRunner(
        test_type=args.type,
        verbose=args.verbose,
        coverage=not args.no_coverage
    )
    
    try:
        # Run tests
        results = runner.run_tests()
        
        # Generate and display report
        report = runner.generate_report(results)
        print(report)
        
        # Save results
        if args.output:
            runner.save_report(results, args.output)
        else:
            runner.save_report(results)
        
        # Exit with appropriate code
        if args.type == "all":
            overall_failed = results.get("overall", {}).get("failed", 0)
        else:
            overall_failed = results.get("failed", 0)
        
        if overall_failed > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        log_error("Test runner failed", error=str(e))
        print(f"❌ Test runner failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 