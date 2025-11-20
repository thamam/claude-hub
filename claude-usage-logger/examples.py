#!/usr/bin/env python3
"""
Example usage patterns for the Claude Code Usage Logger
"""

import sys
from pathlib import Path

# Add logger to path
sys.path.insert(0, str(Path(__file__).parent))

from logger import (
    UsageLogger,
    log_tool_usage,
    log_skill,
    log_subagent,
    log_web_search,
    log_bash,
    log_file_operation,
    log_web_fetch
)


def example_basic_logging():
    """Example 1: Basic logging with global logger."""
    print("=" * 70)
    print("Example 1: Basic Logging")
    print("=" * 70)

    # Log various tool usages
    log_tool_usage("test_tool", test_param="value")
    log_skill("rapid-prototype")
    log_subagent("general-purpose")
    log_web_search("how to use Claude Code")
    log_bash("ls -la")
    log_file_operation("read", "/path/to/file.py")
    log_web_fetch("https://example.com")

    print("✓ Logged 7 events using global logger")
    print()


def example_custom_logger():
    """Example 2: Using a custom logger instance."""
    print("=" * 70)
    print("Example 2: Custom Logger Instance")
    print("=" * 70)

    # Create a custom logger instance
    logger = UsageLogger()

    print(f"Using backend: {'SQLite' if logger.use_sqlite else 'JSONL'}")
    print(f"Session ID: {logger._session_id}")
    print()

    # Log with the custom instance
    logger.log_skill("data-analyzer", dataset_size=1000)
    logger.log_subagent("Explore", thoroughness="medium")

    print("✓ Logged 2 events with custom logger")
    print()


def example_session_tracking():
    """Example 3: Session tracking with explicit names."""
    print("=" * 70)
    print("Example 3: Session Tracking")
    print("=" * 70)

    logger = UsageLogger()
    session_name = "Feature Development: User Authentication"

    # Log a series of related actions
    logger.log_file_operation("read", "auth.py", session_name=session_name)
    logger.log_bash("pytest tests/test_auth.py", session_name=session_name)
    logger.log_file_operation("write", "auth.py", session_name=session_name)
    logger.log_bash("git commit -m 'Add auth'", session_name=session_name)

    print(f"✓ Logged 4 events for session: {session_name}")
    print()


def example_metadata_logging():
    """Example 4: Logging with additional metadata."""
    print("=" * 70)
    print("Example 4: Metadata Logging")
    print("=" * 70)

    logger = UsageLogger()

    # Log with rich metadata
    logger.log_tool_usage(
        "code_review",
        files_reviewed=5,
        issues_found=3,
        time_spent_seconds=120,
        language="python"
    )

    logger.log_web_search(
        "best practices for error handling",
        context="debugging production issue",
        urgency="high"
    )

    print("✓ Logged 2 events with custom metadata")
    print()


def example_error_handling():
    """Example 5: Graceful error handling."""
    print("=" * 70)
    print("Example 5: Error Handling")
    print("=" * 70)

    logger = UsageLogger()

    # Even if logging fails, your code continues
    try:
        # Simulate some work
        result = perform_important_task()

        # Try to log it
        logger.log_tool_usage(
            "important_task",
            result=result,
            success=True
        )

        print("✓ Task completed and logged successfully")

    except Exception as e:
        # Log the error
        logger.log_tool_usage(
            "important_task",
            error=str(e),
            success=False
        )
        print(f"✗ Task failed: {e}")

    print()


def perform_important_task():
    """Simulate an important task."""
    return "Task completed successfully"


def example_workflow_integration():
    """Example 6: Integration into a workflow."""
    print("=" * 70)
    print("Example 6: Workflow Integration")
    print("=" * 70)

    logger = UsageLogger()
    session_name = "Daily Standup Automation"

    # Workflow step 1: Gather data
    logger.log_bash("git log --since=yesterday", session_name=session_name)
    logger.log_file_operation("read", "tasks.json", session_name=session_name)

    # Workflow step 2: Process
    logger.log_tool_usage(
        "data_processor",
        session_name=session_name,
        records_processed=25
    )

    # Workflow step 3: Generate report
    logger.log_file_operation("write", "standup_report.md", session_name=session_name)

    # Workflow step 4: Send notification
    logger.log_tool_usage(
        "notification",
        session_name=session_name,
        channel="slack",
        recipients=5
    )

    print(f"✓ Completed workflow: {session_name}")
    print("  - Logged 5 events tracking the entire process")
    print()


def main():
    """Run all examples."""
    print("\n")
    print("*" * 70)
    print("CLAUDE CODE USAGE LOGGER - EXAMPLES")
    print("*" * 70)
    print("\n")

    example_basic_logging()
    example_custom_logger()
    example_session_tracking()
    example_metadata_logging()
    example_error_handling()
    example_workflow_integration()

    print("=" * 70)
    print("All examples completed!")
    print("=" * 70)
    print()
    print("View the logged data:")
    print("  Phase 1 (JSONL): python3 ~/claude-usage-logger/stats_poc.py")
    print("  Phase 2 (SQLite): python3 ~/claude-usage-logger/stats.py")
    print()


if __name__ == "__main__":
    main()
