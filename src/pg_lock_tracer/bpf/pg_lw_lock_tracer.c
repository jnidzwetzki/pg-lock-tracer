// https://github.com/postgres/postgres/blob/a4adc31f6902f6fc29d74868e8969412fc590da9/src/include/storage/lwlock.h#L110

typedef enum LWLockMode {
  LW_EXCLUSIVE,
  LW_SHARED,
  LW_WAIT_UNTIL_FREE /* A special mode used in PGPROC->lwWaitMode,
                      * when waiting for lock to become free. Not
                      * to be used as LWLockAcquire argument */
} LWLockMode;

/* Placeholder for auto generated defines */
__DEFINES__

typedef struct LockEvent_t {
  u32 pid;
  u64 timestamp;
  u32 event_type;

  /* LWLock tranche name (see T_NAME / GetLWTrancheName()
   * in lwlock.c) */
  char tranche[255];

  /* LWLockMode */
  u32 mode;
} LockEvent;

BPF_PERF_OUTPUT(lockevents);

static void fill_and_submit(struct pt_regs *ctx, LockEvent *event,
                            uint64_t tranche_addr) {
  bpf_probe_read_user_str(event->tranche, sizeof(event->tranche),
                          (void *)tranche_addr);
  event->pid = bpf_get_current_pid_tgid();
  event->timestamp = bpf_ktime_get_ns();

  // sudo cat /sys/kernel/debug/tracing/trace_pipe
  // bpf_trace_printk("LW lock event for trance: %s\\n", tranche);

  lockevents.perf_submit(ctx, event, sizeof(LockEvent));
}

/*
 * Acquire a LW Lock
 * Arguments: TRACE_POSTGRESQL_LWLOCK_ACQUIRE(T_NAME(lock), mode)
 */
int lwlock_acquire(struct pt_regs *ctx) {
  uint64_t tranche_addr = 0;
  LWLockMode mode;

  LockEvent event = {.event_type = EVENT_LOCK};

  // The usdt does not support using bpf_usdt_readarg outside the main probe
  // function See: https://github.com/iovisor/bcc/issues/2265
  bpf_usdt_readarg(1, ctx, &tranche_addr);
  bpf_usdt_readarg(2, ctx, &mode);

  event.mode = mode;

  fill_and_submit(ctx, &event, tranche_addr);
  return 0;
}

/*
 * Release a LW Lock
 * Arguments: TRACE_POSTGRESQL_LWLOCK_RELEASE(T_NAME(lock))
 */
int lwlock_release(struct pt_regs *ctx) {
  uint64_t tranche_addr = 0;

  LockEvent event = {.event_type = EVENT_UNLOCK};

  bpf_usdt_readarg(1, ctx, &tranche_addr);

  fill_and_submit(ctx, &event, tranche_addr);
  return 0;
}

/*
 * Wait for a LW Lock
 * Arguments: TRACE_POSTGRESQL_LWLOCK_WAIT_START(T_NAME(lock), mode)
 */
int lwlock_wait_start(struct pt_regs *ctx) {
  uint64_t tranche_addr = 0;
  LWLockMode mode;

  LockEvent event = {.event_type = EVENT_WAIT_START};

  // The usdt does not support using bpf_usdt_readarg outside the main probe
  // function. See: https://github.com/iovisor/bcc/issues/2265
  bpf_usdt_readarg(1, ctx, &tranche_addr);
  bpf_usdt_readarg(2, ctx, &mode);

  event.mode = mode;

  fill_and_submit(ctx, &event, tranche_addr);
  return 0;
}

/*
 * Wait for a LW Lock is done
 * Arguments: TRACE_POSTGRESQL_LWLOCK_WAIT_DONE(T_NAME(lock), mode)
 */
int lwlock_wait_done(struct pt_regs *ctx) {
  uint64_t tranche_addr = 0;
  LWLockMode mode;

  LockEvent event = {.event_type = EVENT_WAIT_DONE};

  bpf_usdt_readarg(1, ctx, &tranche_addr);
  bpf_usdt_readarg(2, ctx, &mode);

  event.mode = mode;

  fill_and_submit(ctx, &event, tranche_addr);
  return 0;
}

/*
 * LWLock was successfully acquired when the caller specified no waiting
 * Arguments: TRACE_POSTGRESQL_LWLOCK_CONDACQUIRE(T_NAME(lock), mode)
 */
int lwlock_condacquire(struct pt_regs *ctx) {
  uint64_t tranche_addr = 0;
  LWLockMode mode;

  LockEvent event = {.event_type = EVENT_COND_ACQUIRE};

  bpf_usdt_readarg(1, ctx, &tranche_addr);
  bpf_usdt_readarg(2, ctx, &mode);

  event.mode = mode;

  fill_and_submit(ctx, &event, tranche_addr);
  return 0;
}

/*
 * LWLock was successfully acquired when the caller specified no waiting
 * Arguments: TRACE_POSTGRESQL_LWLOCK_CONDACQUIRE_FAIL(T_NAME(lock), mode)
 */
int lwlock_condacquire_fail(struct pt_regs *ctx) {
  uint64_t tranche_addr = 0;
  LWLockMode mode;

  LockEvent event = {.event_type = EVENT_COND_ACQUIRE_FAIL};

  bpf_usdt_readarg(1, ctx, &tranche_addr);
  bpf_usdt_readarg(2, ctx, &mode);

  event.mode = mode;

  fill_and_submit(ctx, &event, tranche_addr);
  return 0;
}

/*
 * Acquire a LWLock or wait if already locked see LWLockAcquireOrWait
 * Arguments: TRACE_POSTGRESQL_LWLOCK_ACQUIRE_OR_WAIT(T_NAME(lock), mode);
 */
int lwlock_acquire_or_wait(struct pt_regs *ctx) {
  uint64_t tranche_addr = 0;
  LWLockMode mode;

  LockEvent event = {.event_type = EVENT_LOCK_OR_WAIT};

  bpf_usdt_readarg(1, ctx, &tranche_addr);
  bpf_usdt_readarg(2, ctx, &mode);

  event.mode = mode;

  fill_and_submit(ctx, &event, tranche_addr);
  return 0;
}

/*
 * Acquire a LWLock or wait if already locked (failed) see LWLockAcquireOrWait
 * Arguments: TRACE_POSTGRESQL_LWLOCK_ACQUIRE_OR_WAIT_FAIL(T_NAME(lock), mode);
 */
int lwlock_acquire_or_wait_fail(struct pt_regs *ctx) {
  uint64_t tranche_addr = 0;
  LWLockMode mode;

  LockEvent event = {.event_type = EVENT_LOCK_OR_WAIT_FAIL};

  bpf_usdt_readarg(1, ctx, &tranche_addr);
  bpf_usdt_readarg(2, ctx, &mode);

  event.mode = mode;

  fill_and_submit(ctx, &event, tranche_addr);
  return 0;
}