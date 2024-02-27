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

            # Warmup cache
            self.fetch_all_oids()
        except psycopg2.OperationalError as error:
            print(f"Unable to connect to the database {self.connection_url}")
            print(f"{error}")
            sys.exit(1)

    def disconnect(self):
        """
        Close the database connection.
        """
        if self.cur:
            self.cur.close()
            self.cur = None

        if self.connection:
            self.connection.close()
            self.connection = None

    def fetch_all_oids(self):
        """
        Fetch all Oid mappings from the catalog and cache them. This
        is done because:

        (1) Cache Oid cache lookups have to be fast and we want
            a warm cache.

        (2) Operations such as DROP delete objects from the database.
            Fetching the oid mapping afterwards is not possible.
        """

        select_stmt = """
        SELECT n.nspname, c.relname, c.oid 
        FROM pg_namespace n
        JOIN pg_class c ON n.oid = c.relnamespace
        """

        self.cur.execute(select_stmt)

        oids = self.cur.fetchall()

        for result_row in oids:
            oid = result_row[2]
            name = f"{result_row[0]}.{result_row[1]}"
            self.cache[oid] = name

    def fetch_oid_from_db(self, oid):
        """
        Resolve the given OID into a name
        """

        select_stmt = """
        SELECT n.nspname, c.relname
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

            # Unable to get name, return Oid instead
            if result_row is None:
                return f"Oid {oid}"

            name = f"{result_row[0]}.{result_row[1]}"

            # Cache result
            self.cache[oid] = name

            return name
        except psycopg2.Error as error:
            print(f"Error while executing SQL statement: {error}")
            print(f"pgerror: {error.pgerror}")
            print(f"pgcode: {error.pgcode}")
            return ""

    def resolve_oid(self, oid):
        """
        Resolve the given OID into a name.
        """

        # OID cache hit
        if oid in self.cache:
            return self.cache[oid]

        # OID cache miss
        return self.fetch_oid_from_db(oid)
