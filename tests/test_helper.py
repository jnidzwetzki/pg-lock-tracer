#!/usr/bin/env python3

import unittest

from src.pg_lock_tracer.helper import PostgreSQLLockHelper


class UNITTests(unittest.TestCase):
    def test_encode_locks(self):
        """
        Test the encoding of locks
        """
        my_locks = [
            "NoLock",
            "AccessShareLock",
            "ShareRowExclusiveLock",
            "AccessExclusiveLock",
        ]

        my_locks_numeric = list(map(PostgreSQLLockHelper.lock_type_to_int, my_locks))

        # Test conversion was ok
        self.assertListEqual([0, 1, 6, 8], my_locks_numeric)

    def encode_and_decode_locks(self, locks):
        """
        Decode and encode the list of locks and test for errors
        """

        # Convert into numeric values
        my_locks_numeric = list(map(PostgreSQLLockHelper.lock_type_to_int, locks))

        # Encode and decode into single value
        single_value = PostgreSQLLockHelper.encode_locks_into_value(my_locks_numeric)
        decoded_locks = PostgreSQLLockHelper.decode_locks_from_value(single_value)

        decoded_my_locks = list(
            map(PostgreSQLLockHelper.lock_type_to_str, decoded_locks)
        )
        self.assertListEqual(locks, decoded_my_locks)

    def test_parse_lock_decoding_and_encoding0(self):
        """
        Test encoding and decoding of locks into a single value
        """

        my_locks = [
            "AccessExclusiveLock",
        ]

        self.encode_and_decode_locks(my_locks)

    def test_parse_lock_decoding_and_encoding1(self):
        """
        Test encoding and decoding of locks into a single value
        """

        my_locks = [
            "NoLock",
            "AccessShareLock",
            "ShareRowExclusiveLock",
            "AccessExclusiveLock",
        ]

        self.encode_and_decode_locks(my_locks)

    def test_parse_lock_decoding_and_encoding2(self):
        """
        Test encoding and decoding of locks into a single value
        """

        my_locks = ["NoLock"]

        self.encode_and_decode_locks(my_locks)

    def test_parse_lock_decoding_and_encoding3(self):
        """
        Test encoding and decoding of locks into a single value
        """

        my_locks = []

        self.encode_and_decode_locks(my_locks)

    def test_parse_lock_decoding_and_encoding_dup(self):
        """
        Test encoding and decoding with duplicates
        """

        my_locks = [
            "AccessShareLock",
            "AccessShareLock",
            "AccessShareLock",
            "ShareRowExclusiveLock",
            "ShareRowExclusiveLock",
        ]

        my_locks_numeric = list(map(PostgreSQLLockHelper.lock_type_to_int, my_locks))

        # Encode and decode into single value
        single_value = PostgreSQLLockHelper.encode_locks_into_value(my_locks_numeric)
        decoded_locks = PostgreSQLLockHelper.decode_locks_from_value(single_value)

        decoded_my_locks = list(
            map(PostgreSQLLockHelper.lock_type_to_str, decoded_locks)
        )

        # Only unique values are present
        self.assertListEqual([my_locks[0], my_locks[4]], decoded_my_locks)
