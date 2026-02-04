#!/usr/bin/env python3
#
# PostgreSQL spinlock delay tracer.
#
###############################################

import sys
import argparse

from bcc import BPF

from pg_lock_tracer import __version__
from pg_lock_tracer.helper import BPFHelper

EXAMPLES = """examples:
# Trace spin delays of the given PostgreSQL binary
pg_spinlock_delay_tracer -x /home/jan/postgresql-sandbox/bin/REL_14_9_DEBUG/bin/postgres

# Trace spin delays of the PID 1234
pg_spinlock_delay_tracer -p 1234 -x /home/jan/postgresql-sandbox/bin/REL_14_9_DEBUG/bin/postgres

# Trace spin delays of the PID 1234 and 5678
pg_spinlock_delay_tracer -p 1234 -p 5678 -x /home/jan/postgresql-sandbox/bin/REL_14_9_DEBUG/bin/postgres

# Trace spin delays of the PID 1234 and be verbose
pg_spinlock_delay_tracer -p 1234 -x /home/jan/postgresql-sandbox/bin/REL_14_9_DEBUG/bin/postgres -v
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


class PGSpinDelayTracer:
    def __init__(self, prog_args):
        self.bpf_instance = None
        self.args = prog_args

        # Belong the processes to the binary?
        BPFHelper.check_pid_exe(self.args.pids, self.args.path)

    @staticmethod
    def _decode_field(value):
        return value.decode("utf-8", "replace").rstrip("\x00")

    def print_lock_event(self, _cpu, data, _size):
        """
        Print a new spin delay event.
        """
        event = self.bpf_instance["lockevents"].event(data)

        if self.args.pids and event.pid not in self.args.pids:
            return

        file_name = self._decode_field(event.file) or "(unknown)"
        func_name = self._decode_field(event.func) or "(unknown)"

        print(
            f"{event.timestamp} [Pid {event.pid}] SpinDelay "
            f"spins={event.spins} delays={event.delays} "
            f"cur_delay={event.cur_delay} at {func_name}, {file_name}:{event.line}"
        )

    def init(self):
        """
        Init the PostgreSQL spin delay tracer
        """
        bpf_program = BPFHelper.read_bpf_program("pg_spinlock_delay_tracer.c")

        if self.args.verbose:
            print(bpf_program)

        # Disable warnings like
        # 'warning: '__HAVE_BUILTIN_BSWAP32__' macro redefined [-Wmacro-redefined]'
        bpf_cflags = ["-Wno-macro-redefined"] if not self.args.verbose else []

        print("===> Compiling BPF program")
        self.bpf_instance = BPF(text=bpf_program, cflags=bpf_cflags)

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
            "^perform_spin_delay$",
            "spin_delay",
            self.args.verbose,
        )

    def run(self):
        """
        Run the BPF program and read results
        """
        print("===> Ready to trace")
        while True:
            try:
                self.bpf_instance.perf_buffer_poll()
            except KeyboardInterrupt:
                sys.exit(0)


def main():
    """
    Entry point for the BPF based PostgreSQL spin delay tracer.
    """
    args = parser.parse_args()

    pg_spin_delay_tracer = PGSpinDelayTracer(args)
    pg_spin_delay_tracer.init()

    if not args.dry_run:
        pg_spin_delay_tracer.run()


if __name__ == "__main__":
    main()
