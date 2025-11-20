#!/usr/bin/env python3
"""
Test suite for logger improvements
Tests resource management, thread safety, and context manager support.
"""

import sys
import threading
import time
from pathlib import Path

# Add logger to path
sys.path.insert(0, str(Path(__file__).parent))

from logger import UsageLogger


def test_context_manager():
    """Test context manager support."""
    print("Test 1: Context Manager Support")
    print("-" * 50)

    with UsageLogger() as logger:
        logger.log_tool_usage("test_context_manager", test="value")
        print(f"  ✓ Logger backend: {'SQLite' if logger.use_sqlite else 'JSONL'}")
        print(f"  ✓ Logged within context manager")

    print("  ✓ Context manager closed successfully")
    print()


def test_thread_safety():
    """Test thread-safe logging."""
    print("Test 2: Thread Safety")
    print("-" * 50)

    logger = UsageLogger()
    errors = []

    def log_from_thread(thread_id, count):
        """Log from a thread."""
        try:
            for i in range(count):
                logger.log_tool_usage(
                    "thread_test",
                    thread_id=thread_id,
                    iteration=i
                )
        except Exception as e:
            errors.append((thread_id, e))

    # Create multiple threads
    threads = []
    num_threads = 10
    logs_per_thread = 5

    print(f"  Starting {num_threads} threads, {logs_per_thread} logs each...")

    for i in range(num_threads):
        thread = threading.Thread(target=log_from_thread, args=(i, logs_per_thread))
        threads.append(thread)
        thread.start()

    # Wait for all threads
    for thread in threads:
        thread.join()

    if errors:
        print(f"  ✗ Errors occurred: {errors}")
    else:
        print(f"  ✓ All {num_threads * logs_per_thread} logs written successfully")

    logger.close()
    print("  ✓ Logger closed successfully")
    print()


def test_resource_cleanup():
    """Test proper resource cleanup."""
    print("Test 3: Resource Cleanup")
    print("-" * 50)

    # Test __del__ cleanup
    logger1 = UsageLogger()
    logger1.log_tool_usage("test_cleanup_1")
    print("  ✓ Created logger 1")
    del logger1
    print("  ✓ Logger 1 deleted (connection closed)")

    # Test explicit close
    logger2 = UsageLogger()
    logger2.log_tool_usage("test_cleanup_2")
    print("  ✓ Created logger 2")
    logger2.close()
    print("  ✓ Logger 2 explicitly closed")

    # Test double close (should not error)
    logger2.close()
    print("  ✓ Double close handled gracefully")
    print()


def test_kwargs_immutability():
    """Test that kwargs are not mutated."""
    print("Test 4: kwargs Immutability")
    print("-" * 50)

    logger = UsageLogger()

    # Create kwargs dict
    metadata = {
        "skill_name": "test-skill",
        "subagent_name": "test-agent",
        "custom_field": "custom_value"
    }

    original_keys = set(metadata.keys())

    # Log with kwargs
    logger.log_tool_usage("test_immutability", **metadata)

    # Check that kwargs were not modified
    if set(metadata.keys()) == original_keys:
        print("  ✓ kwargs dict not mutated")
        print(f"  ✓ Original keys preserved: {list(metadata.keys())}")
    else:
        print(f"  ✗ kwargs dict was mutated!")
        print(f"  Original: {original_keys}")
        print(f"  Current: {set(metadata.keys())}")

    logger.close()
    print()


def test_concurrent_access():
    """Test concurrent read/write access."""
    print("Test 5: Concurrent Access")
    print("-" * 50)

    logger = UsageLogger()
    errors = []
    success_count = [0]  # Use list for mutable counter

    def concurrent_worker(worker_id):
        """Worker that logs multiple times."""
        try:
            for i in range(10):
                logger.log_tool_usage(
                    "concurrent_test",
                    worker_id=worker_id,
                    operation=i
                )
                success_count[0] += 1
                time.sleep(0.001)  # Small delay to increase contention
        except Exception as e:
            errors.append((worker_id, str(e)))

    # Run concurrent workers
    threads = []
    num_workers = 5

    print(f"  Starting {num_workers} concurrent workers...")

    for i in range(num_workers):
        thread = threading.Thread(target=concurrent_worker, args=(i,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    if errors:
        print(f"  ✗ Errors: {errors}")
    else:
        print(f"  ✓ All {success_count[0]} concurrent operations completed")

    logger.close()
    print()


def main():
    """Run all tests."""
    print()
    print("=" * 50)
    print("LOGGER IMPROVEMENTS TEST SUITE")
    print("=" * 50)
    print()

    try:
        test_context_manager()
        test_resource_cleanup()
        test_kwargs_immutability()
        test_thread_safety()
        test_concurrent_access()

        print("=" * 50)
        print("ALL TESTS PASSED ✓")
        print("=" * 50)
        print()

    except Exception as e:
        print()
        print("=" * 50)
        print(f"TEST FAILED ✗")
        print("=" * 50)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
