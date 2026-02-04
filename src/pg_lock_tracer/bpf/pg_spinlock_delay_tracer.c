#include <uapi/linux/ptrace.h>

#define MAX_STR_LEN 128

typedef struct SpinDelayStatus_t {
  int spins;
  int delays;
  int cur_delay;
  const char *file;
  int line;
  const char *func;
} SpinDelayStatus;

typedef struct SpinDelayEvent_t {
  u32 pid;
  u64 timestamp;
  int spins;
  int delays;
  int cur_delay;
  int line;
  char file[MAX_STR_LEN];
  char func[MAX_STR_LEN];
} SpinDelayEvent;

BPF_PERF_OUTPUT(lockevents);

int spin_delay(struct pt_regs *ctx) {
  SpinDelayEvent event = {};
  SpinDelayStatus status = {};
  SpinDelayStatus *status_ptr = (SpinDelayStatus *)PT_REGS_PARM1(ctx);

  event.pid = bpf_get_current_pid_tgid();
  event.timestamp = bpf_ktime_get_ns();

  if (!status_ptr) {
    lockevents.perf_submit(ctx, &event, sizeof(SpinDelayEvent));
    return 0;
  }

  bpf_probe_read_user(&status, sizeof(status), status_ptr);

  event.spins = status.spins;
  event.delays = status.delays;
  event.cur_delay = status.cur_delay;
  event.line = status.line;

  if (status.file) {
    bpf_probe_read_user_str(&event.file, sizeof(event.file), status.file);
  }

  if (status.func) {
    bpf_probe_read_user_str(&event.func, sizeof(event.func), status.func);
  }

  lockevents.perf_submit(ctx, &event, sizeof(SpinDelayEvent));
  return 0;
}
