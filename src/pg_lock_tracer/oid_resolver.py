"""Resolve PostgreSQL OIDs to names and cache the result"""
import sys

from urllib.parse import urlparse

import psycopg2


class OIDResolver:
    def __init__(self, connection_url):
        self.connection_url = connection_url
        self.cache = {}
        self.connection = None
        self.cur = None
        self.connect()

    def connect(self):
        """
        Open the database connection
        """
        connection_url_parsed = urlparse(self.connection_url)
        username = connection_url_parsed.username
        password = connection_url_parsed.password
        database = connection_url_parsed.path[1:]
        hostname = connection_url_parsed.hostname
        port = connection_url_parsed.port

        try:
            self.connection = psycopg2.connect(
                database=database,
                user=username,
                password=password,
                host=hostname,
                port=port,
            )

            self.cur = self.connection.cursor()
        except psycopg2.OperationalError as error:
            print(f"Unable to connect to the database {self.connection_url}")
            print(f"{error}")
            sys.exit(1)

    def disconnect(self):
        """
        Close the databsae connection.
        """
        if self.cur:
            self.cur.close()
            self.cur = None

        if self.connection:
            self.connection.close()
            self.connection = None

    def fetch_oid_from_db(self, oid):
        """Resolve the given OID into a name"""
        select_stmt = """
        SELECT n.nspname AS schema_name, c.relname AS table_name
        FROM pg_namespace n
        JOIN pg_class c ON n.oid = c.relnamespace
        WHERE c.oid = %s;
        """
        oid = str(oid)

        try:

            self.cur.execute(
                select_stmt,
                [
                    oid,
                ],
            )

            result_row = self.cur.fetchone()

            if result_row is None:
                return ""

            name = f"{result_row[0]}.{result_row[1]}"
            return name
        except psycopg2.Error as error:
            print(f"Error while executing SQL statement: {error}")
            print(f"pgerror: {error.pgerror}")
            print(f"pgcode: {error.pgcode}")
            return ""

    def resolve_oid(self, oid):
        if oid in self.cache:
            return self.cache[oid]

        name = self.fetch_oid_from_db(oid)

        self.cache[oid] = name

        return name
