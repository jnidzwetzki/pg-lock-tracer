"""
Helper classes
"""

import os

from pathlib import Path

from bcc import BPF


class PostgreSQLLockHelper:
    """
    # Defines taken from: src/include/storage/lockdefs.h
    #
    # NoLock is not a lock mode, but a flag value meaning "don't get a lock"
    # define NoLock                  0
    #
    # define AccessShareLock         1   /* SELECT */
    # define RowShareLock            2   /* SELECT FOR UPDATE/FOR SHARE */
    # define RowExclusiveLock        3   /* INSERT, UPDATE, DELETE */
    # define ShareUpdateExclusiveLock 4  /* VACUUM (non-FULL), ANALYZE, CREATE
    #                                    * INDEX CONCURRENTLY */
    # define ShareLock               5   /* CREATE INDEX (WITHOUT CONCURRENTLY) */
    # define ShareRowExclusiveLock   6   /* like EXCLUSIVE MODE, but allows ROW
    #                                    * SHARE */
    # define ExclusiveLock           7   /* blocks ROW SHARE/SELECT...FOR UPDATE */
    # define AccessExclusiveLock     8   /* ALTER TABLE, DROP TABLE, VACUUM FULL,
    #                                    * and unqualified LOCK TABLE */
    """

    locks = {}
    locks["NoLock"] = 0
    locks["AccessShareLock"] = 1
    locks["RowShareLock"] = 2
    locks["RowExclusiveLock"] = 3
    locks["ShareUpdateExclusiveLock"] = 4
    locks["ShareLock"] = 5
    locks["ShareRowExclusiveLock"] = 6
    locks["ExclusiveLock"] = 7
    locks["AccessExclusiveLock"] = 8

    @staticmethod
    def encode_locks_into_value(locks):
        """
        Encode a list of lock types into a single value
        """
        result = 0

        for lock in locks:
            lock_value = 1 << int(lock)
            result |= lock_value

        return result

    @staticmethod
    def decode_locks_from_value(encoded_value):
        """
        Decode a value of locks into a list of locks
        """
        result = []

        for lock in range(0, 9):
            lock_value = 1 << int(lock)

            if encoded_value & lock_value == lock_value:
                result.append(lock)

        return result

    @staticmethod
    def lock_type_to_str(lock_type):
        """
        Return the name of a lock based on the numeric value
        """
        for lock_name, lock_numeric_value in PostgreSQLLockHelper.locks.items():
            if lock_numeric_value == lock_type:
                return lock_name

        raise ValueError(f"Unsupported lock type {lock_type}")

    @staticmethod
    def lock_type_to_int(lock_name):
        """
        Return the numeric value of a lock based on the name
        """

        if lock_name not in PostgreSQLLockHelper.locks:
            raise ValueError(f"Unknown lock type {lock_name}")

        return PostgreSQLLockHelper.locks[lock_name]


class BPFHelper:
    # The size of the kernel ring buffer
    page_cnt = 2048

    @staticmethod
    def enum_to_defines(enum_instance, prefix):
        """
        Convert a IntEnum into C '#define' statements
        """
        result = ""

        for instance in enum_instance:
            result += f"#define {prefix}_{instance.name} {instance.value}\n"

        return result

    @staticmethod
    def read_bpf_program(program_name):
        """
        Load the BPF program from a file and return it as a string.
        """
        program_file = Path(__file__).parent / "bpf" / program_name

        if not os.path.exists(program_file):
            raise ValueError(f"BPF program file not found {program_file}")

        with program_file.open("r") as bpf_program:
            return bpf_program.read()

    @staticmethod
    def check_pid_exe(pids, executable):
        """
        Do the given PIDs belong to the executable
        """
        if not pids:
            return

        for pid in pids:
            if not os.path.isdir(f"/proc/{pid}"):
                raise ValueError(
                    f"/proc entry for pid {pid} not found, does the process exist?"
                )

            binary = os.readlink(f"/proc/{pid}/exe")

            if binary != executable:
                raise ValueError(
                    f"Pid {pid} does not belong to binary {executable}. Executable is {binary}"
                )

    @staticmethod
    def register_ebpf_probe(
        path, bpf_instance, function_regex, bpf_fn_name, verbose, probe_on_enter=True
    ):
        """
        Register a BPF probe
        """
        addresses = set()
        func_and_addr = BPF.get_user_functions_and_addresses(path, function_regex)

        if not func_and_addr:
            raise ValueError(f"Unable to locate function {function_regex}")

        # Handle address duplicates
        for function, address in func_and_addr:
            if address in addresses:
                continue
            addresses.add(address)

            if probe_on_enter:
                bpf_instance.attach_uprobe(name=path, sym=function, fn_name=bpf_fn_name)
                if verbose:
                    print(f"Attaching to {function} at address {address} on enter")
            else:
                bpf_instance.attach_uretprobe(
                    name=path, sym=function, fn_name=bpf_fn_name
                )
                if verbose:
                    print(f"Attaching to {function} at address {address} on return")
