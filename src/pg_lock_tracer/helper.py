"""
Helper classes
"""


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

        raise Exception(f"Unsupported lock type {lock_type}")

    @staticmethod
    def lock_type_to_int(lock_name):
        """
        Return the numeric value of a lock based on the name
        """

        if lock_name not in PostgreSQLLockHelper.locks:
            raise Exception(f"Unknown lock type {lock_name}")

        return PostgreSQLLockHelper.locks[lock_name]
