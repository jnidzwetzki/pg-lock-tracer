#include <uapi/linux/ptrace.h>

/*
 * Placeholder for EVENT_* and ERROR_* defines
 *
 * #define EVENT_.... n
 *
 * Will by automatically generated from python Events ENUM
 */
__DEFINES__

typedef struct PostgreSQLEvent {
  u32 pid;
  u64 timestamp;
  u32 event_type;

  u32 object;           // typedef unsigned int Oid;
  int mode;             // typedef int LOCKMODE;
  u32 requested;        // Requested locks
  s64 lock_local_hold;  // Requested local locks

  char payload_str1[127];  // Generic payload string data 1 (e.g., a query / a
                           // schema)
  char payload_str2[127];  // Generic payload string data 2 (e.g., a table)

  int stackid;  // The id of the stack
} PostgreSQLEvent;

BPF_PERF_OUTPUT(lockevents);

#if defined(STACKTRACE_DEADLOCK) || defined(STACKTRACE_LOCK) || \
    defined(STACKTRACE_UNLOCK)
BPF_STACK_TRACE(stacks, 4096);
#endif

static void fill_basic_data(PostgreSQLEvent *event) {
  event->pid = bpf_get_current_pid_tgid();
  event->timestamp = bpf_ktime_get_ns();
}

/*
 * ====================================
 * Table handling
 * ====================================
 */

static void handle_table_event(PostgreSQLEvent *event, struct pt_regs *ctx) {
  fill_basic_data(event);

  bpf_probe_read_kernel(&(event->mode), sizeof(event->mode),
                        &(PT_REGS_PARM2(ctx)));

  // bpf_trace_printk("Event: %d %d\\n", event.object, event.mode);

  lockevents.perf_submit(ctx, event, sizeof(PostgreSQLEvent));
}

/*
 * PostgreSQL: table_open
 * Parameter 1: Oid relationId
 * Parameter 2: LOCKMODE lockmode
 */
int bpf_table_open(struct pt_regs *ctx) {
  PostgreSQLEvent event = {.event_type = EVENT_TABLE_OPEN};
  bpf_probe_read_kernel(&(event.object), sizeof(event.object),
                        &(PT_REGS_PARM1(ctx)));
  handle_table_event(&event, ctx);
  return 0;
}

/*
 *  ptype /o RangeVar
 *  type = struct RangeVar {
 *    0      |     4      NodeTag type;
 * XXX  4-byte hole
 *    8      |     8     char *catalogname;
 *   16      |     8     char *schemaname;
 *   24      |     8     char *relname;
 *   [...]
 */
typedef struct RangeVar {
  u8 enumvalue;
  char *catalogname;
  char *schemaname;
  char *relname;
} RangeVar;

/*
 * PostgreSQL: table_openrv
 * Parameter 1: const RangeVar *relation
 * Parameter 2: LOCKMODE lockmode
 */
int bpf_table_openrv(struct pt_regs *ctx, RangeVar *relation) {
  PostgreSQLEvent event = {.event_type = EVENT_TABLE_OPEN_RV};

  bpf_probe_read_user_str(event.payload_str1, sizeof(event.payload_str1),
                          (void *)relation->schemaname);
  bpf_probe_read_user_str(event.payload_str2, sizeof(event.payload_str2),
                          (void *)relation->relname);

  handle_table_event(&event, ctx);

  return 0;
}

/*
 * PostgreSQL: table_openrv_extended
 * Parameter 1: const RangeVar *relation
 * Parameter 2: LOCKMODE lockmode
 * Parameter 3: bool missing_ok
 */
int bpf_table_openrv_extended(struct pt_regs *ctx, RangeVar *relation) {
  PostgreSQLEvent event = {.event_type = EVENT_TABLE_OPEN_RV_EXTENDED};

  bpf_probe_read_user_str(event.payload_str1, sizeof(event.payload_str1),
                          (void *)relation->schemaname);
  bpf_probe_read_user_str(event.payload_str2, sizeof(event.payload_str2),
                          (void *)relation->relname);

  handle_table_event(&event, ctx);

  return 0;
}

int bpf_table_close(struct pt_regs *ctx) {
  PostgreSQLEvent event = {.event_type = EVENT_TABLE_CLOSE};

  // Param 1 is a Relation struct
  // The Oid rd_id is stored at byte 72 (PG 15.1)

  // gdb: ptype /o Relation
  //
  // type = struct RelationData {
  // /*    0      |    12 */    RelFileNode rd_node;
  // /* XXX  4-byte hole  */
  // /*   16      |     8 */    SMgrRelation rd_smgr;
  // /*   24      |     4 */    int rd_refcnt;
  // /*   28      |     4 */    BackendId rd_backend;
  // /*   32      |     1 */    _Bool rd_islocaltemp;
  // /*   33      |     1 */    _Bool rd_isnailed;
  // /*   34      |     1 */    _Bool rd_isvalid;
  // /*   35      |     1 */    _Bool rd_indexvalid;
  // /*   36      |     1 */    _Bool rd_statvalid;
  // /* XXX  3-byte hole  */
  // /*   40      |     4 */    SubTransactionId rd_createSubid;
  // /*   44      |     4 */    SubTransactionId rd_newRelfilenodeSubid;
  // /*   48      |     4 */    SubTransactionId rd_firstRelfilenodeSubid;
  // /*   52      |     4 */    SubTransactionId rd_droppedSubid;
  // /*   56      |     8 */    Form_pg_class rd_rel;
  // /*   64      |     8 */    TupleDesc rd_att;
  // /*   72      |     4 */    Oid rd_id;
  // [....]

  char buffer[76];
  bpf_probe_read_user(buffer, sizeof(buffer), (void *)PT_REGS_PARM1(ctx));
  bpf_probe_read_kernel(&(event.object), sizeof(event.object), &(buffer[72]));

  // Oid oid;
  // bpf_probe_read_kernel(&oid, sizeof(oid), &(buffer[72]));
  // bpf_probe_read_kernel(&(event.object), sizeof(event.object),
  // &(PT_REGS_PARM1(ctx))); bpf_trace_printk("Oid: %d \\n", oid);

  handle_table_event(&event, ctx);
  return 0;
}

static void fill_basic_data_and_submit(PostgreSQLEvent *event,
                                       struct pt_regs *ctx) {
  fill_basic_data(event);
  lockevents.perf_submit(ctx, event, sizeof(PostgreSQLEvent));
}

/*
 * ====================================
 * Query handling
 * ====================================
 */
int bpf_query_begin(struct pt_regs *ctx) {
  PostgreSQLEvent event = {.event_type = EVENT_QUERY_BEGIN};
  bpf_probe_read_user_str(event.payload_str1, sizeof(event.payload_str1),
                          (void *)PT_REGS_PARM1(ctx));
  fill_basic_data_and_submit(&event, ctx);
  return 0;
}

/*
 * Query return probe
 */
int bpf_query_end(struct pt_regs *ctx) {
  PostgreSQLEvent event = {.event_type = EVENT_QUERY_END};
  fill_basic_data_and_submit(&event, ctx);
  return 0;
}

/*
 * ====================================
 * Error handling
 * ====================================
 */
int bpf_errstart(struct pt_regs *ctx) {
  PostgreSQLEvent event = {.event_type = EVENT_ERROR};
  fill_basic_data(&event);
  bpf_probe_read_kernel(&event.mode, sizeof(event.mode),
                        (void *)&(PT_REGS_PARM1(ctx)));

  if (event.mode >= PGERROR_ERROR) {
    lockevents.perf_submit(ctx, &event, sizeof(PostgreSQLEvent));
  }

  return 0;
}

/*
 * ====================================
 * Lock handling
 * ====================================
 */

/*
 * PSQL: LockRelationOid
 * Parameter 1: Oid
 * Parameter 2: LOCKMODE
 */
int bpf_lock_relation_oid(struct pt_regs *ctx) {
  PostgreSQLEvent event = {.event_type = EVENT_LOCK_RELATION_OID};
  bpf_probe_read_kernel(&(event.object), sizeof(event.object),
                        &(PT_REGS_PARM1(ctx)));

#ifdef STACKTRACE_LOCK
  event.stackid = stacks.get_stackid(ctx, BPF_F_USER_STACK);
#endif

  handle_table_event(&event, ctx);
  return 0;
}

/*
 * PSQL: LockRelationOid - Return probe
 */
int bpf_lock_relation_oid_end(struct pt_regs *ctx) {
  PostgreSQLEvent event = {.event_type = EVENT_LOCK_RELATION_OID_END};
  fill_basic_data_and_submit(&event, ctx);
  return 0;
}

/*
 * PSQL: UnlockRelationOid
 * Parameter 1: Oid
 * Parameter 2: LOCKMODE
 */
int bpf_unlock_relation_oid(struct pt_regs *ctx) {
  PostgreSQLEvent event = {.event_type = EVENT_UNLOCK_RELATION_OID};
  bpf_probe_read_kernel(&(event.object), sizeof(event.object),
                        &(PT_REGS_PARM1(ctx)));
  handle_table_event(&event, ctx);
  return 0;
}

/*
 * Parse the LOCK Structure

 * PG 14.2
 * (gdb) ptype /o lock
 * type = struct LOCK {
 *    0      |    16 *    LOCKTAG tag;
 *   16      |     4 *    LOCKMASK grantMask;
 *   20      |     4 *    LOCKMASK waitMask;
 *   24      |    16 *    SHM_QUEUE procLocks;
 *   40      |    24 *    PROC_QUEUE waitProcs;
 *   64      |    40 *    int requested[10];
 *  104      |     4 *    int nRequested;
 *  108      |    40 *    int granted[10];
 *  148      |     4 *    int nGranted;
 *
 * (gdb) ptype /o LOCKTAG
 * type = struct LOCKTAG {
 *    0      |     4 *    uint32 locktag_field1; // Database OID (see
 SET_LOCKTAG_RELATION)
 *    4      |     4 *    uint32 locktag_field2; // Relation OID (see
 SET_LOCKTAG_RELATION)
 *    8      |     4 *    uint32 locktag_field3;
 *   12      |     2 *    uint16 locktag_field4;
 *   14      |     1 *    uint8 locktag_type;
 *   15      |     1 *    uint8 locktag_lockmethodid;
 */
static void fill_lock_object(PostgreSQLEvent *event, void *param) {
  char buffer[108];
  bpf_probe_read_user(buffer, sizeof(buffer), param);
  bpf_probe_read_kernel(&(event->object), sizeof(event->object), &(buffer[4]));
  bpf_probe_read_kernel(&(event->requested), sizeof(event->requested),
                        &(buffer[104]));
}

/*
 * PSQL: GrantLock
 * Parameter 1 LOCK
 * Parameter 2 PROCLOCK
 * Parameter 3 LOCKMODE
 */
int bpf_lock_grant(struct pt_regs *ctx) {
  PostgreSQLEvent event = {.event_type = EVENT_LOCK_GRANTED};
  bpf_probe_read_kernel(&(event.mode), sizeof(event.mode),
                        &(PT_REGS_PARM3(ctx)));
  fill_lock_object(&event, (void *)PT_REGS_PARM1(ctx));

  if (event.object != 0) fill_basic_data_and_submit(&event, ctx);

  return 0;
}

/*
 * PSQL: FastPathGrantRelationLock
 * Parameter 1 OID
 * Parameter 2 LOCKMODE
 */
int bpf_lock_fastpath_grant(struct pt_regs *ctx) {
  PostgreSQLEvent event = {.event_type = EVENT_LOCK_GRANTED_FASTPATH};
  bpf_probe_read_kernel(&(event.object), sizeof(event.object),
                        &(PT_REGS_PARM1(ctx)));
  bpf_probe_read_kernel(&(event.mode), sizeof(event.mode),
                        &(PT_REGS_PARM2(ctx)));
  fill_basic_data_and_submit(&event, ctx);
  return 0;
}

/*
 * Local lock grant
 * Parameter 1: LOCALLOCK *locallock
 * Parameter 2: ResourceOwner owner
 *
 * PG 14
 *
 *  ptype /o locallock
 *  type = struct LOCALLOCK {
 *    0      |    20 *    LOCALLOCKTAG tag;
 *   20      |     4 *    uint32 hashcode;
 *   24      |     8 *    LOCK *lock;
 *   32      |     8 *    PROCLOCK *proclock;
 *   40      |     8 *    int64 nLocks;
 *   48      |     4 *    int numLockOwners;
 *   52      |     4 *    int maxLockOwners;
 *   56      |     8 *    LOCALLOCKOWNER *lockOwners;
 *   64      |     1 *    _Bool holdsStrongLockCount;
 *   65      |     1 *    _Bool lockCleared;
 * XXX  6-byte padding
 *
 * type = struct LOCALLOCKTAG {
 *    0      |    16 *    LOCKTAG lock; -- See LOCKTAG above
 *   16      |     4 *    LOCKMODE mode;
 *
 */
static void fill_locallock_object(PostgreSQLEvent *event, void *param) {
  char buffer[48];
  bpf_probe_read_user(buffer, sizeof(buffer), param);
  bpf_probe_read_kernel(&(event->object), sizeof(event->object), &(buffer[4]));
  bpf_probe_read_kernel(&(event->lock_local_hold),
                        sizeof(event->lock_local_hold), &(buffer[40]));
  bpf_probe_read_kernel(&(event->mode), sizeof(event->mode), &(buffer[16]));
}

/*
 * PSQL: GrantLockLocal
 * Parameter 1 LOCALLOCK
 * Parameter 2 ResourceOwner
 */
int bpf_lock_local_grant(struct pt_regs *ctx) {
  PostgreSQLEvent event = {.event_type = EVENT_LOCK_GRANTED_LOCAL};
  fill_locallock_object(&event, (void *)PT_REGS_PARM1(ctx));

  if (event.object != 0) fill_basic_data_and_submit(&event, ctx);

  return 0;
}

/*
 * PSQL: UnGrantLock
 * Parameter 1 LOCK
 * Parameter 2 LOCKMODE
 */
int bpf_lock_ungrant(struct pt_regs *ctx) {
  PostgreSQLEvent event = {.event_type = EVENT_LOCK_UNGRANTED};
  bpf_probe_read_kernel(&(event.mode), sizeof(event.mode),
                        &(PT_REGS_PARM2(ctx)));
  fill_lock_object(&event, (void *)PT_REGS_PARM1(ctx));

#ifdef STACKTRACE_UNLOCK
  event.stackid = stacks.get_stackid(ctx, BPF_F_USER_STACK);
#endif

  if (event.object != 0) fill_basic_data_and_submit(&event, ctx);

  return 0;
}

/*
 * PSQL: FastPathUnGrantRelationLock
 * Parameter 1 Oid
 * Parameter 2 LOCKMODE
 */
int bpf_lock_fastpath_ungrant(struct pt_regs *ctx) {
  PostgreSQLEvent event = {.event_type = EVENT_LOCK_UNGRANTED_FASTPATH};
  bpf_probe_read_kernel(&(event.object), sizeof(event.object),
                        &(PT_REGS_PARM1(ctx)));
  bpf_probe_read_kernel(&(event.mode), sizeof(event.mode),
                        &(PT_REGS_PARM2(ctx)));

#ifdef STACKTRACE_UNLOCK
  event.stackid = stacks.get_stackid(ctx, BPF_F_USER_STACK);
#endif

  fill_basic_data_and_submit(&event, ctx);

  return 0;
}

/*
 * PSQL: RemoveLocalLock
 * Parameter 1: LOCALLOCK
 */
int bfp_local_lock_ungrant(struct pt_regs *ctx) {
  PostgreSQLEvent event = {.event_type = EVENT_LOCK_UNGRANTED_LOCAL};
  fill_locallock_object(&event, (void *)PT_REGS_PARM1(ctx));

  if (event.object != 0) fill_basic_data_and_submit(&event, ctx);

  return 0;
}

/*
 * Deadlock detected
 * PSQL: DeadLockReport
 */
int bpf_deadlock(struct pt_regs *ctx) {
  PostgreSQLEvent event = {.event_type = EVENT_DEADLOCK};
#ifdef STACKTRACE_DEADLOCK
  event.stackid = stacks.get_stackid(ctx, BPF_F_USER_STACK);
#endif
  fill_basic_data_and_submit(&event, ctx);
  return 0;
}

/*
 * ====================================
 * Transaction handling
 * ====================================
 */

/*
 * PSQL: StartTransaction
 */
int bpf_transaction_begin(struct pt_regs *ctx) {
  PostgreSQLEvent event = {.event_type = EVENT_TRANSACTION_BEGIN};
  fill_basic_data_and_submit(&event, ctx);
  return 0;
}

/*
 * PSQL: CommitTransaction
 */
int bpf_transaction_commit(struct pt_regs *ctx) {
  PostgreSQLEvent event = {.event_type = EVENT_TRANSACTION_COMMIT};
  fill_basic_data_and_submit(&event, ctx);
  return 0;
}

/*
 * PSQL: AbortTransaction
 */
int bpf_transaction_abort(struct pt_regs *ctx) {
  PostgreSQLEvent event = {.event_type = EVENT_TRANSACTION_ABORT};
  fill_basic_data_and_submit(&event, ctx);
  return 0;
}

/*
 * ====================================
 * Process Invalidation Messages
 * ====================================
 */

/*
 * PSQL: AcceptInvalidationMessages
 */
int bpf_accept_invalidation_messages(struct pt_regs *ctx) {
  PostgreSQLEvent event = {.event_type = EVENT_INVALIDATION_MESSAGES_ACCEPT};
  fill_basic_data_and_submit(&event, ctx);
  return 0;
}