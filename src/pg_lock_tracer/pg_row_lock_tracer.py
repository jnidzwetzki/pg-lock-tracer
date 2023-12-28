#!/usr/bin/env python3
#
# PostgreSQL row lock tracer.
#
# See https://www.postgresql.org/docs/current/explicit-locking.html#LOCKING-ROWS
#
###############################################

import sys
import argparse

from enum import IntEnum, unique

from bcc import BPF
from prettytable import PrettyTable

from pg_lock_tracer import __version__
from pg_lock_tracer.helper import BPFHelper

EXAMPLES = """examples:
# Trace the row locks of the given PostgreSQL binary
pg_row_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_14_9_DEBUG/bin/postgres

# Trace the row locks of the PID 1234
pg_row_lock_tracer -p 1234 -x /home/jan/postgresql-sandbox/bin/REL_14_9_DEBUG/bin/postgres

# Trace the row locks of the PID 1234 and 5678
pg_row_lock_tracer -p 1234 -p 5678 -x /home/jan/postgresql-sandbox/bin/REL_14_9_DEBUG/bin/postgres

# Trace the row locks of the PID 1234 and be verbose
pg_row_lock_tracer -p 1234 -x /home/jan/postgresql-sandbox/bin/REL_14_9_DEBUG/bin/postgres -v

# Trace the row locks and show statistics
pg_row_lock_tracer -x /home/jan/postgresql-sandbox/bin/REL_14_9_DEBUG/bin/postgres --statistics
"""

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
parser.add_argument("-v", "--verbose", action="store_true", help="Be verbose")
parser.add_argument(
    "-p",
    "--pid",
    type=int,
    nargs="+",
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
    "-d",
    "--dry-run",
    action="store_true",
    help="compile and load the BPF program but exit afterward",
)
parser.add_argument("--statistics", action="store_true", help="print lock statistics")


@unique
class Events(IntEnum):
    LOCK_TUPLE = 0
    LOCK_TUPLE_END = 1


# See lockoptions.h in PostgreSQL
@unique
class TMResult(IntEnum):
    TM_OK = 0
    TM_INVISIBLE = 1
    TM_SELFMODIFIED = 2
    TM_UPDATED = 3
    TM_DELETED = 4
    TM_BEINGMODIFIED = 5
    TM_WOULDBLOCK = 6


# See lockoptions.h in PostgreSQL
@unique
class LockWaitPolicy(IntEnum):
    LOCK_WAIT_BLOCK = 0
    LOCK_WAIT_SKIP = 1
    LOCK_WAIT_ERROR = 2


# See lockoptions.h in PostgreSQL
@unique
class LockTupleMode(IntEnum):
    LOCK_TUPLE_KEYSHARE = 0
    LOCK_TUPLE_SHARE = 1
    LOCK_TUPLE_NOKEYEXCLUSIVE = 2
    LOCK_TUPLE_EXCLUSIVE = 3


class LockStatisticsEntry:
    def __init__(self) -> None:
        # The requested locks
        self._lock_modes = {}

        # The used lock policies
        self._lock_policies = {}

        # The lock results
        self._lock_results = {}

    @property
    def lock_modes(self):
        return self._lock_modes

    @lock_modes.setter
    def lock_modes(self, value):
        self._lock_modes = value

    @property
    def lock_policies(self):
        return self._lock_policies

    @lock_policies.setter
    def lock_policies(self, value):
        self._lock_policies = value

    @property
    def lock_results(self):
        return self._lock_results

    @lock_results.setter
    def lock_results(self, value):
        self._results = value


class PGRowLockTracer:
    def __init__(self, prog_args):
        self.bpf_instance = None
        self.args = prog_args
        self.statistics = {}

        # Variables for lock timing
        self.last_lock_request_time = {}

        # Belong the processes to the binary?
        BPFHelper.check_pid_exe(self.args.pids, self.args.path)

    def get_lock_wait_time(self, event):
        """
        Get the last lock wait time (WAIT_START updates
        last_lock_request_time).
        """
        if event.event_type != Events.LOCK_TUPLE_END:
            return None

        return event.timestamp - self.last_lock_request_time[event.pid]

    def update_statistics(self, event):
        """
        Update the statistics
        """
        if event.pid not in self.statistics:
            self.statistics[event.pid] = LockStatisticsEntry()

        statistics_entry = self.statistics.get(event.pid)

        # Lock requested
        if event.event_type == Events.LOCK_TUPLE:
            lock_wait_policy = LockWaitPolicy(event.lockwaitpolicy)

            if lock_wait_policy in statistics_entry.lock_policies:
                statistics_entry.lock_policies[lock_wait_policy] += 1
            else:
                statistics_entry.lock_policies[lock_wait_policy] = 1

            lock_tuple_mode = LockTupleMode(event.locktuplemode)

            if lock_tuple_mode in statistics_entry.lock_modes:
                statistics_entry.lock_modes[lock_tuple_mode] += 1
            else:
                statistics_entry.lock_modes[lock_tuple_mode] = 1

            return

        # Lock request done
        if event.event_type == Events.LOCK_TUPLE_END:
            lock_result = TMResult(event.lockresult)

            if lock_result in statistics_entry.lock_results:
                statistics_entry.lock_results[lock_result] += 1
            else:
                statistics_entry.lock_results[lock_result] = 1
            return

        return

    def print_lock_event(self, _cpu, data, _size):
        """
        Print a new lock event.
        """
        event = self.bpf_instance["lockevents"].event(data)

        if self.args.pids and event.pid not in self.args.pids:
            return

        print_prefix = f"{event.timestamp} [Pid {event.pid}]"

        self.update_statistics(event)

        if event.event_type == Events.LOCK_TUPLE:
            self.last_lock_request_time[event.pid] = event.timestamp

            locktuplemode = LockTupleMode(event.locktuplemode).name
            lockwaitpolicy = LockWaitPolicy(event.lockwaitpolicy).name

            print(
                f"{print_prefix} LOCK_TUPLE (Tablespace {event.tablespace} "
                f"database {event.database} relation {event.relation}) "
                f"- (Block and offset {event.blockid} {event.offset}) "
                f"- {locktuplemode} {lockwaitpolicy}"
            )
        elif event.event_type == Events.LOCK_TUPLE_END:
            lockresult = TMResult(event.lockresult).name
            needed_time = self.get_lock_wait_time(event)
            print(f"{print_prefix} LOCK_TUPLE_END {lockresult} in {needed_time} ns")
        else:
            raise ValueError(f"Unknown event type {event.event_type}")

    def init(self):
        """
        Init the PostgreSQL lock tracer
        """
        enum_defines = BPFHelper.enum_to_defines(Events, "EVENT")

        bpf_program = BPFHelper.read_bpf_program("pg_row_lock_tracer.c")
        bpf_program_final = bpf_program.replace("__DEFINES__", enum_defines)

        if self.args.verbose:
            print(bpf_program_final)

        # Disable warnings like
        # 'warning: '__HAVE_BUILTIN_BSWAP32__' macro redefined [-Wmacro-redefined]'
        bpf_cflags = ["-Wno-macro-redefined"] if not self.args.verbose else []

        print("===> Compiling BPF program")
        self.bpf_instance = BPF(text=bpf_program_final, cflags=bpf_cflags)

        print("===> Attaching BPF probes")
        self.attach_probes()

        # Open the event queue
        self.bpf_instance["lockevents"].open_perf_buffer(
            self.print_lock_event, page_cnt=BPFHelper.page_cnt
        )

    def attach_probes(self):
        """
        Attach BPF probes
        """
        BPFHelper.register_ebpf_probe(
            self.args.path,
            self.bpf_instance,
            "^heapam_tuple_lock$",
            "heapam_tuple_lock",
            self.args.verbose,
        )
        BPFHelper.register_ebpf_probe(
            self.args.path,
            self.bpf_instance,
            "^heapam_tuple_lock$",
            "heapam_tuple_lock_end",
            self.args.verbose,
            False,
        )

    def print_statistics(self):
        """
        Print lock statistics
        """
        print("\nLock statistics:\n================")

        # Wait policies
        print("\nUsed wait policies:")
        wait_polices = ["PID"]

        for wait_policy in LockWaitPolicy:
            wait_polices.append(wait_policy.name)

        table = PrettyTable(wait_polices)

        for pid in sorted(self.statistics):
            statistics = self.statistics[pid]
            pid_statistics = [pid]
            for wait_policy in LockWaitPolicy:
                pid_statistics.append(statistics.lock_policies.get(wait_policy, 0))
            table.add_row(pid_statistics)
        print(table)

        # Lock modes
        print("\nLock modes:")
        lock_modes = ["PID"]

        for lock_mode in LockTupleMode:
            lock_modes.append(lock_mode.name)

        table = PrettyTable(lock_modes)

        for pid in sorted(self.statistics):
            statistics = self.statistics[pid]
            pid_statistics = [pid]
            for lock_mode in LockTupleMode:
                pid_statistics.append(statistics.lock_modes.get(lock_mode, 0))
            table.add_row(pid_statistics)
        print(table)

        # Lock results
        print("\nLock results:")
        lock_results = ["PID"]

        for lock_result in TMResult:
            lock_results.append(lock_result.name)

        table = PrettyTable(lock_results)

        for pid in sorted(self.statistics):
            statistics = self.statistics[pid]
            pid_statistics = [pid]
            for lock_result in TMResult:
                pid_statistics.append(statistics.lock_results.get(lock_result, 0))
            table.add_row(pid_statistics)
        print(table)

    def run(self):
        """
        Run the BPF program and read results
        """
        print("===> Ready to trace")
        while True:
            try:
                self.bpf_instance.perf_buffer_poll()
            except KeyboardInterrupt:
                if self.args.statistics:
                    self.print_statistics()
                sys.exit(0)


def main():
    """
    Entry point for the BPF based PostgreSQL row lock tracer.
    """
    args = parser.parse_args()

    pg_lock_tracer = PGRowLockTracer(args)
    pg_lock_tracer.init()

    if not args.dry_run:
        pg_lock_tracer.run()


if __name__ == "__main__":
    main()
