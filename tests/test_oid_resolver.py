#!/usr/bin/env python3

import unittest
from unittest import mock

from pg_lock_tracer.oid_resolver import OIDResolver


class OIDResolverTests(unittest.TestCase):
    def create_resolver(self):
        """
        Create an OID resolver backed by a mocked database connection
        """
        with mock.patch("pg_lock_tracer.oid_resolver.psycopg2.connect") as connect:
            cursor = connect.return_value.cursor.return_value
            cursor.fetchall.return_value = [("public", "warm_table", 1000)]
            resolver = OIDResolver("psql://user@localhost/db")

        return resolver, cursor

    def test_resolve_warm_cache(self):
        """
        OIDs fetched during the cache warmup are resolved without a query
        """
        resolver, cursor = self.create_resolver()
        cursor.execute.reset_mock()

        self.assertEqual("public.warm_table", resolver.resolve_oid(1000))
        cursor.execute.assert_not_called()

    def test_resolve_caches_fetched_oid(self):
        """
        An OID fetched from the database is cached under the same key
        that is used for the lookup
        """
        resolver, cursor = self.create_resolver()
        cursor.execute.reset_mock()
        cursor.fetchone.return_value = ("public", "new_table")

        self.assertEqual("public.new_table", resolver.resolve_oid(2000))
        self.assertEqual("public.new_table", resolver.resolve_oid(2000))
        cursor.execute.assert_called_once()
