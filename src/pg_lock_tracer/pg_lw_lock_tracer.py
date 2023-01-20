#!/usr/bin/env python3
#
# PostgreSQL LW lock tracer. To use this script, PostgreSQL has to be
# compiled with '--enable-dtrace'.
#
# See https://www.postgresql.org/docs/current/dynamic-trace.html
#
# List all available USDT probes
# sudo bpftrace -l "usdt:/home/jan/postgresql-sandbox/bin/REL_15_1_DEBUG/bin/postgres:*"
###############################################

import sys
import argparse

from bcc import BPF, USDT
from prettytable import PrettyTable

EXAMPLES = """examples:
# Trace the LW locks of the PID 1234
pg_lw_lock_tracer -p 1234

# Trace the LW locks of the PIDs 1234 and 5678
pg_lw_lock_tracer -p 1234 -p 5678

# Trace the LW locks of the PID 1234 and be verbose
pg_lw_lock_tracer -p 1234 -v

# Trace the LW locks of the PID 1234 and collect statistics
pg_lw_lock_tracer -p 1234 -v --statistics
"""

parser = argparse.ArgumentParser(
    description="",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=EXAMPLES,
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
    required=True,
)
parser.add_argument(
    "-d",
    "--dry-run",
    action="store_true",
    help="compile and load the BPF program but exit afterward",
)
parser.add_argument("--statistics", action="store_true", help="print lock statistics")

BPF_PROGRAM = """
// https://github.com/postgres/postgres/blob/a4adc31f6902f6fc29d74868e8969412fc590da9/src/include/storage/lwlock.h#L39
struct LWLock_t
{
	u16 tranche;		/* tranche ID */
	u32 state;		/* state of exclusive/nonexclusive lockers */
};

// https://github.com/postgres/postgres/blob/a4adc31f6902f6fc29d74868e8969412fc590da9/src/include/storage/lwlock.h#L110
typedef enum LWLockMode
{
     LW_EXCLUSIVE,
     LW_SHARED,
     LW_WAIT_UNTIL_FREE          /* A special mode used in PGPROC->lwWaitMode,
                                  * when waiting for lock to become free. Not
                                  * to be used as LWLockAcquire argument */
} LWLockMode;

#define LOCK_EVENT 0
#define UNLOCK_EVENT 1

struct LockEvent_t
{
        u32 pid;
        u64 timestamp;
        u32 event_type;

        /* LWLock_t fields */
        u16 tranche;
        u32 state;

        /* LWLockMode */
        u32 mode;
};

BPF_PERF_OUTPUT(lockevents);

int lwlock_acquire(struct pt_regs *ctx) {
    struct LWLock_t data = {};
    struct LockEvent_t event = {};
    LWLockMode mode;
    bpf_usdt_readarg(1, ctx, &data);
    bpf_usdt_readarg(2, ctx, &mode);

    event.pid = bpf_get_current_pid_tgid();
    event.timestamp = bpf_ktime_get_ns();
    event.tranche = data.tranche;
    event.state = data.state;
    event.event_type = LOCK_EVENT;
    event.mode = mode;

    lockevents.perf_submit(ctx, &event, sizeof(event));
    return 0;
}

int lwlock_release(struct pt_regs *ctx) {
    struct LWLock_t data = {};
    struct LockEvent_t event = {};
    bpf_usdt_readarg(1, ctx, &data);

    event.pid = bpf_get_current_pid_tgid();
    event.timestamp = bpf_ktime_get_ns();
    event.tranche = data.tranche;
    event.state = data.state;
    event.event_type = UNLOCK_EVENT;

    // sudo cat /sys/kernel/debug/tracing/trace_pipe
    // bpf_trace_printk("Unlock: %d %d\\n", data.tranche, data.state);
    
    lockevents.perf_submit(ctx, &event, sizeof(event));
    return 0;
}
"""


class PGLWLockTracer:
    def __init__(self, prog_args):
        self.bpf_instance = None
        self.usdts = None
        self.prog_args = prog_args
        self.locks_per_tranche = {}
        self.lock_types = {}

    def print_lock_event(self, _cpu, data, _size):
        """
        Print a new lock event.
        """
        event = self.bpf_instance["lockevents"].event(data)

        if event.event_type == 0:
            lock_mode = ""
            if event.mode == 0:  # LW_EXCLUSIVE,
                lock_mode = "LW_EXCLUSIVE"
            elif event.mode == 1:  # LW_SHARED
                lock_mode = "LW_SHARED"
            elif event.mode == 2:  # LW_WAIT_UNTIL_FREE
                lock_mode = "LW_WAIT_UNTIL_FREE"
            else:
                raise Exception(f"Unknown event type {event.event_type}")
            print(f"[{event.pid}] Locking {event.tranche} / mode {lock_mode}")

            # Update lock tranche statistics
            locks = self.locks_per_tranche.get(event.tranche, 0)
            locks += 1
            self.locks_per_tranche[event.tranche] = locks

            # Update lock type statistics
            locks = self.lock_types.get(lock_mode, 0)
            locks += 1
            self.lock_types[lock_mode] = locks

        elif event.event_type == 1:
            print(f"[{event.pid}] Unlocking {event.tranche}")
        else:
            raise Exception("Unknown event type {event.event_type}")

    def init(self):
        """
        Compile and load the BPF program
        """
        print(f"==> Attaching to PIDs {self.prog_args.pids}")
        self.usdts = list(map(lambda pid: USDT(pid=pid), self.prog_args.pids))

        for usdt in self.usdts:
            usdt.enable_probe("lwlock__acquire", "lwlock_acquire")
            usdt.enable_probe("lwlock__release", "lwlock_release")

        if self.prog_args.verbose:
            print("=======")
            print("\n".join(map(lambda u: u.get_text(), self.usdts)))
            print("=======")

        if self.prog_args.verbose:
            print(BPF_PROGRAM)

        self.bpf_instance = BPF(text=BPF_PROGRAM, usdt_contexts=self.usdts)

        self.bpf_instance["lockevents"].open_perf_buffer(
            self.print_lock_event, page_cnt=64
        )

    def print_statistics(self):
        """
        Print lock statistics
        """
        print("\nLock statistics:\n================")

        # Tranche lock statistics
        print("\nLocks per tranche")
        table = PrettyTable(["Tranche Name", "Requests"])

        for key in sorted(self.locks_per_tranche):
            locks = self.locks_per_tranche[key]
            table.add_row([key, locks])

        print(table)

        # Type lock statistics
        print("\nLocks per type")
        table = PrettyTable(["Lock type", "Requests"])

        for key in sorted(self.lock_types):
            locks = self.lock_types[key]
            table.add_row([key, locks])

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
                if self.prog_args.statistics:
                    self.print_statistics()
                sys.exit(0)


def main():
    """
    Entry point for the BPF based PostgreSQL LW lock tracer.
    """
    args = parser.parse_args()

    pg_lock_tracer = PGLWLockTracer(args)
    pg_lock_tracer.init()

    if not args.dry_run:
        pg_lock_tracer.run()


if __name__ == "__main__":
    main()
