#include <uapi/linux/ptrace.h>

/* Placeholder for auto generated defines */
__DEFINES__

typedef struct RowLockEvent_t {
  u32 pid;
  u64 timestamp;
  u32 event_type;

  /* See RelFileNode - Oid is u32 */
  u32 tablespace;
  u32 database;
  u32 relation;

  /* LockTupleMode */
  u8 locktuplemode;

  /* LockWaitPolicy */
  u8 lockwaitpolicy;

  /* Locked tuple */
  u32 blockid;
  u16 offset;

  /* TM_Result */
  int lockresult;
} RowLockEvent;

BPF_PERF_OUTPUT(lockevents);

static void fill_and_submit(struct pt_regs *ctx, RowLockEvent *event) {
  event->pid = bpf_get_current_pid_tgid();
  event->timestamp = bpf_ktime_get_ns();

  // sudo cat /sys/kernel/debug/tracing/trace_pipe
  // bpf_trace_printk("LW lock event for trance: %s\\n", tranche);

  lockevents.perf_submit(ctx, event, sizeof(RowLockEvent));
}

/*
 * Acquire a tuple lock
 *
 * Arguments:
 *   1. Relation relation (1st member RelFileNode)
 *   2. ItemPointer tid
 *   3. Snapshot snapshot,
 *   4. TupleTableSlot *slot,
 *   5. CommandId cid,
 *   6. LockTupleMode mode,
 *   7. LockWaitPolicy wait_policy,
 *   8. uint8 flags,
 *   9. TM_FailureData *tmfd
 *
 */
int heapam_tuple_lock(struct pt_regs *ctx) {
  RowLockEvent event = {.event_type = EVENT_LOCK_TUPLE};

  /*
   *    (gdb) ptype /o RelFileNode
   *      0      |       4   Oid spcNode;
   *      4      |       4   Oid dbNode;
   *      8      |       4   Oid relNode;
   */

  char buffer_relation[12];
  bpf_probe_read_user(buffer_relation, sizeof(buffer_relation),
                      (void *)PT_REGS_PARM1(ctx));
  bpf_probe_read_kernel(&(event.tablespace), sizeof(event.tablespace),
                        &(buffer_relation[0]));
  bpf_probe_read_kernel(&(event.database), sizeof(event.database),
                        &(buffer_relation[4]));
  bpf_probe_read_kernel(&(event.relation), sizeof(event.relation),
                        &(buffer_relation[8]));

  /* Locked tuple */
  char buffer_item_pointer[6];
  u16 bi_hi;
  u16 bi_lo;

  bpf_probe_read_user(buffer_item_pointer, sizeof(buffer_item_pointer),
                      (void *)PT_REGS_PARM2(ctx));
  bpf_probe_read_kernel(&(bi_hi), sizeof(bi_hi), &(buffer_item_pointer[0]));
  bpf_probe_read_kernel(&(bi_lo), sizeof(bi_lo), &(buffer_item_pointer[2]));
  bpf_probe_read_kernel(&(event.offset), sizeof(event.offset),
                        &(buffer_item_pointer[4]));

  /* See #define BlockIdGetBlockNumber(blockId) */
  event.blockid = (bi_hi) << 16 | bi_lo;

  /* Locking options */
  bpf_probe_read_kernel(&(event.locktuplemode), sizeof(event.locktuplemode),
                        &(PT_REGS_PARM6(ctx)));

  /* Only the first six function parameters are passed via register. All
   * remaining parameters are stored on the stack.
   *
   * See: System V Application Binary Interface—AMD64 Architecture Processor
   * Supplement.
   */
  void *ptr = 0;
  bpf_probe_read(&ptr, sizeof(ptr), (void *)(PT_REGS_SP(ctx) + (1 * 8)));
  bpf_probe_read_kernel(&(event.lockwaitpolicy), sizeof(event.lockwaitpolicy),
                        &ptr);

  fill_and_submit(ctx, &event);
  return 0;
}

/*
 * Acquire a tuple lock - Function done
 */
int heapam_tuple_lock_end(struct pt_regs *ctx) {
  RowLockEvent event = {.event_type = EVENT_LOCK_TUPLE_END};

  event.lockresult = PT_REGS_RC(ctx);

  fill_and_submit(ctx, &event);
  return 0;
}
