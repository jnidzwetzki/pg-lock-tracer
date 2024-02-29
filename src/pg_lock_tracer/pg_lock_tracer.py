#!/usr/bin/env python3
#
# PostgreSQL lock tracer
#
# This tool traces the lock operations that PostgreSQL performs.
#
# Unfortunately, PostgreSQL does not provide USDT probes for
# these locks. Therefore BPF, UProbes, and parameter parsing
# is used to trace these events.
###############################################

import os
import sys
import json
import argparse

from abc import ABC
from enum import IntEnum, auto, unique
from bcc import BPF
from prettytable import PrettyTable

from pg_lock_tracer import __version__
from pg_lock_tracer.oid_resolver import OIDResolver
from pg_lock_tracer.helper import PostgreSQLLockHelper, BPFHelper

EXAMPLES = """

usage examples:
# Trace use binary '/home/jan/postgresql-sandbox/bin/REL_15_1_DEBUG/bin/postgres' for tracing and trace pid 1234
pg_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_15_1_DEBUG/bin/postgres -p 1234

# Trace two PIDs
pg_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_15_1_DEBUG/bin/postgres -p 1234 -p 5678

# Be verbose
pg_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_15_1_DEBUG/bin/postgres -p 1234 -v 

# Use the given db connection to access the catalog of PID 1234 to resolve OIDs
pg_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_15_1_DEBUG/bin/postgres -p 1234 -r 1234:psql://jan@localhost/test2

# Output in JSON format
pg_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_15_1_DEBUG/bin/postgres -p 1234 -j

# Print stacktrace on deadlock
pg_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_15_1_DEBUG/bin/postgres -p 1234 -s DEADLOCK

# Print stacktrace for locks and deadlocks
pg_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_15_1_DEBUG/bin/postgres -p 1234 -s LOCK DEADLOCK

# Trace only Transaction and Query related events
pg_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_15_1_DEBUG/bin/postgres -p 1234 -t TRANSACTION QUERY

# Write the output into file 'trace'
pg_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_15_1_DEBUG/bin/postgres -p 1234 -o trace

# Show statistics about locks
pg_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_15_1_DEBUG/bin/postgres -p 1234 --statistics
"""


class TraceEvents(IntEnum):
    """
    Events to trace
    """

    TRANSACTION = auto()
    QUERY = auto()
    TABLE = auto()
    LOCK = auto()
    INVALIDATION = auto()
    ERROR = auto()


parser = argparse.ArgumentParser(
    description="",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=EXAMPLES,
)
parser.add_argument(
    "-V",
    "--version",
    action="version",
    version=f"{parser.prog} ({__version__})",
)
parser.add_argument("-v", "--verbose", action="store_true", help="be verbose")
parser.add_argument(
    "-j", "--json", action="store_true", help="generate output as JSON data"
)
parser.add_argument(
    "-p",
    "--pid",
    type=int,
    nargs="+",
    action="extend",
    dest="pids",
    metavar="PID",
    help="the pid(s) to trace",
)
parser.add_argument(
    "-x",
    "--exe",
    type=str,
    required=True,
    dest="path",
    metavar="PATH",
    help="path to binary",
)
parser.add_argument(
    "-r",
    "--oid-resolver",
    type=str,
    action="extend",
    default=[],
    nargs="*",
    dest="oid_resolver_urls",
    metavar="OIDResolver",
    help="OID resolver for a PID. The resolver has to be specified in format <PID:database-url>",
)
parser.add_argument(
    "-s",
    "--stacktrace",
    type=str,
    dest="stacktrace",
    action="extend",
    default=None,
    nargs="*",
    choices=["DEADLOCK", "LOCK", "UNLOCK"],
    help="print stacktrace on every of these events",
)
parser.add_argument(
    "-t",
    "--trace",
    type=str,
    dest="trace",
    action="extend",
    default=None,
    nargs="*",
    choices=[event.name for event in TraceEvents],
    help="events to trace (default: All events are traced)",
)
parser.add_argument(
    "-o",
    "--output",
    type=str,
    dest="output_file",
    default=None,
    help="write the trace into output file",
)
parser.add_argument("--statistics", action="store_true", help="print lock statistics")
parser.add_argument(
    "-d",
    "--dry-run",
    action="store_true",
    help="compile and load the BPF program but exit afterward",
)


@unique
class Events(IntEnum):
    TABLE_OPEN = 1
    TABLE_OPEN_RV = 2
    TABLE_OPEN_RV_EXTENDED = 3
    TABLE_CLOSE = 4
    ERROR = 5
    QUERY_BEGIN = 20
    QUERY_END = 21
    LOCK_RELATION_OID = 30
    LOCK_RELATION_OID_END = 31
    UNLOCK_RELATION_OID = 32
    LOCK_GRANTED = 33
    LOCK_GRANTED_FASTPATH = 34
    LOCK_GRANTED_LOCAL = 35
    LOCK_UNGRANTED = 36
    LOCK_UNGRANTED_FASTPATH = 37
    LOCK_UNGRANTED_LOCAL = 38
    TRANSACTION_BEGIN = 40
    TRANSACTION_COMMIT = 41
    TRANSACTION_ABORT = 42
    INVALIDATION_MESSAGES_ACCEPT = 50
    # Events over 1000 are handled regardless of any pid filter
    GLOBAL = 1000
    DEADLOCK = 1001


# From elog.h
@unique
class PGError(IntEnum):
    ERROR = 21
    FATAL = 22
    PANIC = 23


class LockStatisticsEntry:
    def __init__(self) -> None:
        # The number of requested locks
        self._lock_count = 0

        # The total time spend for lock requests
        self._lock_time_ns = 0

        # A list with the requested locks
        self._requested_locks = []

    @property
    def lock_count(self):
        return self._lock_count

    @lock_count.setter
    def lock_count(self, value):
        self._lock_count = value

    @property
    def lock_time_ns(self):
        return self._lock_time_ns

    @lock_time_ns.setter
    def lock_time_ns(self, value):
        self._lock_time_ns = value

    @property
    def requested_locks(self):
        return self._requested_locks

    @requested_locks.setter
    def requested_locks(self, lock_type):
        self._requested_locks.append(lock_type)


class PGLockTraceOutput(ABC):
    def __init__(self) -> None:
        super().__init__()
        self.statistics = {}
        self.bpf_instance = None
        self.bpf_stacks = None
        self.output_file = None
        self.oid_resolvers = None
        self.pids = None
        # Variables for lock timing
        self.last_lock_request_time = {}
        self.last_lock_relation = {}

    def set_context(
        self, bpf_instance, bpf_stacks, output_file, oid_resolvers, pids
    ) -> None:
        """
        Set the needed context variables
        """
        self.bpf_instance = bpf_instance
        self.bpf_stacks = bpf_stacks
        self.output_file = output_file
        self.oid_resolvers = oid_resolvers
        self.pids = pids

    def print_event(self, _cpu, data, _size):
        """
        Handle the output of the given event. Subclasses will implement
        the concrete logic.
        """

    def update_statistics(self, event, oid_value):
        """
        Add the lock call to the statistics and measure lock request time
        """
        if event.event_type == Events.LOCK_RELATION_OID:
            if oid_value not in self.statistics:
                self.statistics[oid_value] = LockStatisticsEntry()

            statistics_entry = self.statistics.get(oid_value)
            statistics_entry.lock_count += 1
            statistics_entry.requested_locks = event.mode

            self.last_lock_request_time[event.pid] = event.timestamp
            self.last_lock_relation[event.pid] = oid_value

        if event.event_type == Events.LOCK_RELATION_OID_END:
            lock_relation = self.last_lock_relation[event.pid]
            statistics_entry = self.statistics.get(lock_relation)
            statistics_entry.lock_time_ns += self.get_lock_wait_time(event)
            self.last_lock_relation[event.pid] = None

    def get_lock_wait_time(self, event):
        """
        Get the last lock wait time (LOCK_RELATION_OID updates
        last_lock_request_time).

        This method should be called on LOCK_RELATION_OID_END.
        """
        if event.event_type != Events.LOCK_RELATION_OID_END:
            return None

        return event.timestamp - self.last_lock_request_time[event.pid]

    def print_statistics(self):
        """
        Print lock statistics
        """
        print("\nLock statistics:\n================")

        # Oid lock statistics
        print("\nLocks per OID")
        table = PrettyTable(["Lock Name", "Requests", "Total Lock Request Time (ns)"])

        sorted_keys = sorted(
            self.statistics.keys(),
            key=lambda key: self.statistics.get(key).lock_count,
            reverse=True,
        )

        for key in sorted_keys:
            statistics = self.statistics[key]
            table.add_row([key, statistics.lock_count, statistics.lock_time_ns])

        print(table)

        # Lock type statistics
        print("\nLock types")
        table = PrettyTable(["Lock Type", "Number of requested locks"])

        # Map: Key = Lock type, Value = Number of requested locks
        requested_locks = {}

        # Gather per lock type statistics
        for statistics in self.statistics.values():
            for lock_type in statistics.requested_locks:
                locks = requested_locks.get(lock_type, 0) + 1
                requested_locks[lock_type] = locks

        # Print statistics
        for lock_type in sorted(requested_locks):
            locks = requested_locks[lock_type]
            lock_name = PostgreSQLLockHelper.lock_type_to_str(lock_type)
            table.add_row([lock_name, locks])

        print(table)

    def handle_output_line(self, line):
        """
        Handle a output line
        """
        if self.output_file:
            self.output_file.write(line + "\n")
        else:
            print(line)


class PGLockTraceOutputHuman(PGLockTraceOutput):
    # pylint: disable=too-many-branches, too-many-statements
    def print_event(self, _cpu, data, _size):
        """
        Print event in a human readable format
        """
        event = self.bpf_instance["lockevents"].event(data)

        if (
            self.pids
            and event.pid not in self.pids
            and event.event_type < Events.GLOBAL
        ):
            return

        print_prefix = f"{event.timestamp} [Pid {event.pid}]"

        # Resolve the OID to a name
        if event.object > 0:
            tablename = event.object

        # Resolve the OID to a table name
        if event.pid in self.oid_resolvers and event.object:
            resolver = self.oid_resolvers[event.pid]
            oid_value = resolver.resolve_oid(event.object)
            tablename = f"{tablename} ({oid_value})"
            self.update_statistics(event, oid_value)
        else:
            self.update_statistics(event, event.object)

        output = None
        if event.event_type == Events.TABLE_OPEN:
            lock_type = PostgreSQLLockHelper.lock_type_to_str(event.mode)
            output = f"{print_prefix} Table open {tablename} {lock_type}"
        elif event.event_type in (Events.TABLE_OPEN_RV, Events.TABLE_OPEN_RV_EXTENDED):
            # Table is opened using a (string) range value
            lock_type = PostgreSQLLockHelper.lock_type_to_str(event.mode)
            schema = event.payload_str1.decode("utf-8")
            table = event.payload_str2.decode("utf-8")
            tablename = f"{schema}.{table}"
            output = (
                f"{print_prefix} Table open (by range value) {tablename} {lock_type}"
            )
        elif event.event_type == Events.TABLE_CLOSE:
            lock_type = PostgreSQLLockHelper.lock_type_to_str(event.mode)
            output = f"{print_prefix} Table close {tablename} {lock_type}"
        elif event.event_type == Events.LOCK_RELATION_OID:
            lock_type = PostgreSQLLockHelper.lock_type_to_str(event.mode)
            output = f"{print_prefix} Lock object {tablename} {lock_type}"
        elif event.event_type == Events.LOCK_RELATION_OID_END:
            lock_time = self.get_lock_wait_time(event)
            output = f"{print_prefix} Lock was acquired in {lock_time} ns"
        elif event.event_type == Events.UNLOCK_RELATION_OID:
            lock_type = PostgreSQLLockHelper.lock_type_to_str(event.mode)
            output = f"{print_prefix} Unlock relation {tablename} {lock_type}"
        elif event.event_type == Events.LOCK_GRANTED:
            lock_type = PostgreSQLLockHelper.lock_type_to_str(event.mode)
            output = (
                f"{print_prefix} Lock granted {tablename} {lock_type} "
                f"(Requested locks {event.requested})"
            )
        elif event.event_type == Events.LOCK_GRANTED_FASTPATH:
            lock_type = PostgreSQLLockHelper.lock_type_to_str(event.mode)
            output = f"{print_prefix} Lock granted (fastpath) {tablename} {lock_type}"
        elif event.event_type == Events.LOCK_GRANTED_LOCAL:
            lock_type = PostgreSQLLockHelper.lock_type_to_str(event.mode)
            output = (
                f"{print_prefix} Lock granted (local) {tablename} {lock_type} "
                f"(Already hold local {event.lock_local_hold})"
            )
        elif event.event_type == Events.LOCK_UNGRANTED:
            lock_type = PostgreSQLLockHelper.lock_type_to_str(event.mode)
            output = (
                f"{print_prefix} Lock ungranted {tablename} {lock_type} "
                f"(Requested locks {event.requested})"
            )
        elif event.event_type == Events.LOCK_UNGRANTED_FASTPATH:
            lock_type = PostgreSQLLockHelper.lock_type_to_str(event.mode)
            output = f"{print_prefix} Lock ungranted (fastpath) {tablename} {lock_type}"
        elif event.event_type == Events.LOCK_UNGRANTED_LOCAL:
            lock_type = PostgreSQLLockHelper.lock_type_to_str(event.mode)
            output = (
                f"{print_prefix} Lock ungranted (local) {tablename} {lock_type} "
                f"(Hold local {event.lock_local_hold})"
            )
        elif event.event_type == Events.INVALIDATION_MESSAGES_ACCEPT:
            output = f"{print_prefix} Accept invalidation messages"
        elif event.event_type == Events.ERROR:
            pgerror_value = PGError(event.mode).name
            output = f"{print_prefix} Error occurred servity: {pgerror_value}"
        elif event.event_type == Events.QUERY_BEGIN:
            query = event.payload_str1.decode("utf-8")
            output = f"{print_prefix} Query begin '{query}'"
        elif event.event_type == Events.QUERY_END:
            output = f"{print_prefix} Query done\n"
        elif event.event_type == Events.TRANSACTION_BEGIN:
            output = f"{print_prefix} Transaction begin"
        elif event.event_type == Events.TRANSACTION_COMMIT:
            output = f"{print_prefix} Transaction commit"
        elif event.event_type == Events.TRANSACTION_ABORT:
            output = f"{print_prefix} Transaction abort"
        elif event.event_type == Events.DEADLOCK:
            output = f"{print_prefix} DEADLOCK DETECTED"
        else:
            raise ValueError(f"Unsupported event type {event.event_type}")

        self.handle_output_line(output)
        self.print_stacktace_if_available(event)

    def print_stacktace_if_available(self, event):
        """
        Print the stacktrace of an event if available
        """
        if event.stackid == 0 or self.bpf_stacks is None:
            return

        if event.stackid < 0:
            print(
                "Error stack is missing. Try to increase BPF_STACK_TRACE buffer size."
            )
        else:
            for frame in self.bpf_stacks.walk(event.stackid):
                line = self.bpf_instance.sym(
                    frame, event.pid, show_offset=True, show_module=True
                )
                line = line.decode("utf-8")
                # Get line with: 'gdb info line *(symbol+0x1111)'
                print(f"\t{line}")


class PGLockTraceOutputJSON(PGLockTraceOutput):
    def print_event(self, _cpu, data, _size):
        """
        Print event in JSON format
        """
        event = self.bpf_instance["lockevents"].event(data)

        if (
            self.pids
            and event.pid not in self.pids
            and event.event_type < Events.GLOBAL
        ):
            return

        output = {}
        output["timestamp"] = event.timestamp
        output["pid"] = event.pid
        output["event"] = Events(event.event_type).name

        if event.event_type in (
            Events.TABLE_OPEN,
            Events.TABLE_OPEN_RV,
            Events.TABLE_OPEN_RV_EXTENDED,
            Events.TABLE_CLOSE,
            Events.LOCK_RELATION_OID,
            Events.UNLOCK_RELATION_OID,
            Events.LOCK_GRANTED,
            Events.LOCK_GRANTED_FASTPATH,
            Events.LOCK_GRANTED_LOCAL,
            Events.LOCK_UNGRANTED,
            Events.LOCK_UNGRANTED_FASTPATH,
            Events.LOCK_UNGRANTED_LOCAL,
        ):
            output["lock_type"] = PostgreSQLLockHelper.lock_type_to_str(event.mode)

        # Resolve OID to tablename
        if event.pid in self.oid_resolvers and event.object:
            resolver = self.oid_resolvers[event.pid]
            oid_value = resolver.resolve_oid(event.object)
            output["table"] = oid_value
            self.update_statistics(event, oid_value)
        else:
            self.update_statistics(event, event.object)

        # Resolve the OID to a name
        if event.object:
            output["oid"] = event.object

        if event.event_type == Events.ERROR:
            pgerror_value = PGError(event.mode).name
            output["servity"] = pgerror_value
        elif event.event_type == Events.QUERY_BEGIN:
            output["query"] = event.payload_str1.decode("utf-8")
        elif event.event_type in (Events.TABLE_OPEN_RV, Events.TABLE_OPEN_RV_EXTENDED):
            # Table is opened using a (string) range value
            schema = event.payload_str1.decode("utf-8")
            table = event.payload_str2.decode("utf-8")
            output["table"] = f"{schema}.{table}"
        elif event.event_type == Events.LOCK_GRANTED_LOCAL:
            output["lock_local_hold"] = event.lock_local_hold
        elif event.event_type == Events.LOCK_RELATION_OID_END:
            lock_time = self.get_lock_wait_time(event)
            output["lock_time"] = lock_time

        self.add_stacktrace_if_available(output, event)

        self.handle_output_line(json.dumps(output))

    def add_stacktrace_if_available(self, output, event):
        """
        Add a stacktrace to the JSON structure if available
        """
        if event.stackid == 0 or self.bpf_stacks is None:
            return

        if event.stackid < 0:
            output["stacktrace"] = "MISSING"
        else:
            lines = []

            # Get stacktrace symbol with module
            for frame in self.bpf_stacks.walk(event.stackid):
                line = self.bpf_instance.sym(
                    frame, event.pid, show_offset=True, show_module=True
                )
                lines.append(line.decode("utf-8"))

            # Merge lines into a single string
            stacktrace = ", ".join(lines)
            output["stacktrace"] = stacktrace


class PGLockTracer:
    def __init__(self, prog_args):
        self.bpf_instance = None
        self.bpf_stacks = None
        self.output_file = None
        self.output_class = None
        self.args = prog_args

        # A map of OID resolvers. One resolver per PID is needed
        # because the Oid depend on the catalog of the database.
        self.oid_resolvers = {}

        for oid_resolver_url in self.args.oid_resolver_urls:
            if ":" not in oid_resolver_url:
                raise ValueError(
                    f"Resolver URL has to be in format: 'PID:URL' ({oid_resolver_url} was provided)"
                )

            split_url = oid_resolver_url.split(":", 1)
            resolver_pid = int(split_url[0])
            database_url = split_url[1]

            if resolver_pid not in self.args.pids:
                print(
                    f"Specified resolver for PID {resolver_pid}, but PID is not monitored"
                )
                sys.exit(1)

            if self.args.verbose:
                print(f"Add resolver for PID {resolver_pid} with URL {database_url}")

            oid_resolver = OIDResolver(database_url)
            self.oid_resolvers[resolver_pid] = oid_resolver

        # Belong the processes to the binary?
        BPFHelper.check_pid_exe(self.args.pids, self.args.path)

        # Does the output file already exists?
        if self.args.output_file and os.path.exists(self.args.output_file):
            raise ValueError(f"Output file {self.args.output_file} already exists")

    @staticmethod
    def generate_c_defines(stacktrace_events, verbose):
        """
        Create C defines from python enums
        """
        enum_defines = BPFHelper.enum_to_defines(Events, "EVENT")
        error_defines = BPFHelper.enum_to_defines(PGError, "PGERROR")
        defines = enum_defines + error_defines

        # Print stacktrace for each lock
        if stacktrace_events and "LOCK" in stacktrace_events:
            defines += "#define STACKTRACE_LOCK\n"
            if verbose:
                print("Print stacktrace on each lock event")

        # Print stacktrace for each unlock
        if stacktrace_events and "UNLOCK" in stacktrace_events:
            defines += "#define STACKTRACE_UNLOCK\n"
            if verbose:
                print("Print stacktrace on each unlock event")

        # Print stacktrace on deadlock
        if stacktrace_events and "DEADLOCK" in stacktrace_events:
            defines += "#define STACKTRACE_DEADLOCK\n"
            if verbose:
                print("Print stacktrace on each deadlock")

        return defines

    def init(self):
        """
        Init the PostgreSQL lock tracer
        """

        defines = PGLockTracer.generate_c_defines(
            self.args.stacktrace, self.args.verbose
        )
        bpf_program = BPFHelper.read_bpf_program("pg_lock_tracer.c")
        bpf_program_final = bpf_program.replace("__DEFINES__", defines)

        if self.args.verbose:
            print(bpf_program_final)

        # Disable warnings like
        # 'warning: '__HAVE_BUILTIN_BSWAP32__' macro redefined [-Wmacro-redefined]'
        bpf_cflags = ["-Wno-macro-redefined"] if not self.args.verbose else []

        print("===> Compiling BPF program")
        self.bpf_instance = BPF(text=bpf_program_final, cflags=bpf_cflags)

        print("===> Attaching BPF probes")
        self.attach_probes()

        # Stack traces requested?
        if self.args.stacktrace:
            self.bpf_stacks = self.bpf_instance.get_table("stacks")

        # Open file for output if provided
        if self.args.output_file:
            # pylint: disable=consider-using-with
            self.output_file = open(self.args.output_file, "w", encoding="utf-8")
            if not self.output_file.writable():
                raise ValueError(
                    f"Output file {self.args.output_file} is not writeable"
                )

        # Output as human readable text or as json?
        self.output_class = (
            PGLockTraceOutputJSON() if self.args.json else PGLockTraceOutputHuman()
        )

        # Init the output class
        self.output_class.set_context(
            self.bpf_instance,
            self.bpf_stacks,
            self.output_file,
            self.oid_resolvers,
            self.args.pids,
        )

        # Open the event queue
        self.bpf_instance["lockevents"].open_perf_buffer(
            self.output_class.print_event, page_cnt=BPFHelper.page_cnt
        )

    def attach_probes(self):
        """
        Attach BPF probes
        """
        # Transaction probes
        if self.args.trace is None or TraceEvents.TRANSACTION.name in self.args.trace:
            BPFHelper.register_ebpf_probe(
                self.args.path,
                self.bpf_instance,
                "^StartTransaction$",
                "bpf_transaction_begin",
                self.args.verbose,
            )
            BPFHelper.register_ebpf_probe(
                self.args.path,
                self.bpf_instance,
                "^CommitTransaction$",
                "bpf_transaction_commit",
                self.args.verbose,
            )
            BPFHelper.register_ebpf_probe(
                self.args.path,
                self.bpf_instance,
                "^AbortTransaction$",
                "bpf_transaction_abort",
                self.args.verbose,
            )
            BPFHelper.register_ebpf_probe(
                self.args.path,
                self.bpf_instance,
                "^DeadLockReport$",
                "bpf_deadlock",
                self.args.verbose,
            )

        # Query probes
        if self.args.trace is None or TraceEvents.QUERY.name in self.args.trace:
            BPFHelper.register_ebpf_probe(
                self.args.path,
                self.bpf_instance,
                "^exec_simple_query$",
                "bpf_query_begin",
                self.args.verbose,
            )
            BPFHelper.register_ebpf_probe(
                self.args.path,
                self.bpf_instance,
                "^exec_simple_query$",
                "bpf_query_end",
                self.args.verbose,
                False,
            )

        # Table probes
        if self.args.trace is None or TraceEvents.TABLE.name in self.args.trace:
            BPFHelper.register_ebpf_probe(
                self.args.path,
                self.bpf_instance,
                "^table_open$",
                "bpf_table_open",
                self.args.verbose,
            )
            BPFHelper.register_ebpf_probe(
                self.args.path,
                self.bpf_instance,
                "^table_openrv$",
                "bpf_table_openrv",
                self.args.verbose,
            )
            BPFHelper.register_ebpf_probe(
                self.args.path,
                self.bpf_instance,
                "^table_openrv_extended$",
                "bpf_table_openrv_extended",
                self.args.verbose,
            )
            BPFHelper.register_ebpf_probe(
                self.args.path,
                self.bpf_instance,
                "^table_close$",
                "bpf_table_close",
                self.args.verbose,
            )

        # Lock probes
        if self.args.trace is None or TraceEvents.LOCK.name in self.args.trace:
            BPFHelper.register_ebpf_probe(
                self.args.path,
                self.bpf_instance,
                "^LockRelationOid$",
                "bpf_lock_relation_oid",
                self.args.verbose,
            )
            BPFHelper.register_ebpf_probe(
                self.args.path,
                self.bpf_instance,
                "^LockRelationOid$",
                "bpf_lock_relation_oid_end",
                self.args.verbose,
                False,
            )
            BPFHelper.register_ebpf_probe(
                self.args.path,
                self.bpf_instance,
                "^UnlockRelationOid$",
                "bpf_unlock_relation_oid",
                self.args.verbose,
            )
            BPFHelper.register_ebpf_probe(
                self.args.path,
                self.bpf_instance,
                "^GrantLock$",
                "bpf_lock_grant",
                self.args.verbose,
            )
            BPFHelper.register_ebpf_probe(
                self.args.path,
                self.bpf_instance,
                "^FastPathGrantRelationLock$",
                "bpf_lock_fastpath_grant",
                self.args.verbose,
            )
            BPFHelper.register_ebpf_probe(
                self.args.path,
                self.bpf_instance,
                "^GrantLockLocal$",
                "bpf_lock_local_grant",
                self.args.verbose,
            )
            BPFHelper.register_ebpf_probe(
                self.args.path,
                self.bpf_instance,
                "^UnGrantLock$",
                "bpf_lock_ungrant",
                self.args.verbose,
            )
            BPFHelper.register_ebpf_probe(
                self.args.path,
                self.bpf_instance,
                "^FastPathUnGrantRelationLock$",
                "bpf_lock_fastpath_ungrant",
                self.args.verbose,
            )
            BPFHelper.register_ebpf_probe(
                self.args.path,
                self.bpf_instance,
                "^RemoveLocalLock$",
                "bfp_local_lock_ungrant",
                self.args.verbose,
            )

        # Invalidation messages probes
        if self.args.trace is None or TraceEvents.INVALIDATION.name in self.args.trace:
            BPFHelper.register_ebpf_probe(
                self.args.path,
                self.bpf_instance,
                "^AcceptInvalidationMessages$",
                "bpf_accept_invalidation_messages",
                self.args.verbose,
            )

        # Error probes
        if self.args.trace is None or TraceEvents.ERROR.name in self.args.trace:
            BPFHelper.register_ebpf_probe(
                self.args.path,
                self.bpf_instance,
                "^errstart$",
                "bpf_errstart",
                self.args.verbose,
            )

    def run(self):
        """
        Run the BPF program and read results
        """

        print("===> Ready to trace queries")
        while True:
            try:
                self.bpf_instance.perf_buffer_poll()
            except KeyboardInterrupt:
                if self.output_file:
                    self.output_file.close()

                if self.args.statistics:
                    self.output_class.print_statistics()
                sys.exit(0)


def main():
    """
    Entry point for the BPF based PostgreSQL lock tracer.
    """
    args = parser.parse_args()

    pg_lock_tracer = PGLockTracer(args)
    pg_lock_tracer.init()

    if not args.dry_run:
        pg_lock_tracer.run()


if __name__ == "__main__":
    main()
