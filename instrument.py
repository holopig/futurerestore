# Build-time instrumentation. Build C newline escapes via chr(92)+'n' so no
# heredoc/escaping mangles them into real newlines.
def read(p): return open(p,encoding="utf-8").read()
def write(p,s): open(p,"w",encoding="utf-8",newline="\n").write(s)
NL=chr(92)+"n"   # literal backslash-n for C string literals
M='client->mode?client->mode->string:"(null)"'

IDR="external/idevicerestore/src/idevicerestore.c"
REC="external/idevicerestore/src/recovery.c"
FR="src/futurerestore.cpp"

# 1) idevicerestore.c: every device-event callback logs always (debug->info)
s=read(IDR); n=s.count('debug("%s: device %016" PRIx64')
s=s.replace('debug("%s: device %016" PRIx64','info("%s: device %016" PRIx64')
write(IDR,s); print("IDR callbacks debug->info:",n)

# 2) recovery.c: log mode around the 30s restore wait (line-1477 path)
s=read(REC)
a='cond_wait_timeout(&client->device_event_cond, &client->device_event_mutex, 30000);'
assert a in s, "REC anchor missing"
before='info("[INSTR] enter_restore BEFORE 30s wait: mode=%s'+NL+'", '+M+'); '
after=' info("[INSTR] enter_restore AFTER 30s wait: mode=%s'+NL+'", '+M+');'
s=s.replace(a, before+a+after, 1)
write(REC,s); print("REC 30s-wait logging: OK")

# 3) futurerestore.cpp: guard + log around the 180s outer wait
s=read(FR)
a='cond_wait_timeout(&client->device_event_cond, &client->device_event_mutex, 180000);'
assert a in s, "FR anchor missing"
before='info("[INSTR] outer-wait BEFORE: mode=%s'+NL+'", '+M+'); if (client->mode != MODE_RESTORE) { '
after=' } info("[INSTR] outer-wait AFTER: mode=%s'+NL+'", '+M+');'
s=s.replace(a, before+a+after, 1)
write(FR,s); print("FR outer-wait guard+log: OK")
print("instrumentation done")
