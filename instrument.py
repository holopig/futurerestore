# Build-time instrumentation: surface device-event transitions and apply the
# restore-mode-wait guard, so we can see exactly what happens around line 1477.
def read(p): return open(p,encoding="utf-8").read()
def write(p,s): open(p,"w",encoding="utf-8",newline="\n").write(s)

IDR="external/idevicerestore/src/idevicerestore.c"
REC="external/idevicerestore/src/recovery.c"
FR="src/futurerestore.cpp"

# 1) idevicerestore.c: make EVERY device-event callback log always (debug->info)
s=read(IDR); n=s.count('debug("%s: device %016" PRIx64')
s=s.replace('debug("%s: device %016" PRIx64','info("%s: device %016" PRIx64')
write(IDR,s); print("IDR callbacks debug->info:",n)

# 2) recovery.c: log mode around the 30s restore-mode wait (the line-1477 path)
s=read(REC)
a='cond_wait_timeout(&client->device_event_cond, &client->device_event_mutex, 30000);'
assert a in s, "REC anchor missing"
s=s.replace(a,
 'info("[INSTR] enter_restore BEFORE 30s wait: mode=%s\n", client->mode?client->mode->string:"(null)"); '
 +a+
 ' info("[INSTR] enter_restore AFTER 30s wait: mode=%s\n", client->mode?client->mode->string:"(null)");',1)
write(REC,s); print("REC 30s-wait logging: OK")

# 3) futurerestore.cpp: apply guard + log around the 180s outer wait
s=read(FR)
a='cond_wait_timeout(&client->device_event_cond, &client->device_event_mutex, 180000);'
assert a in s, "FR anchor missing"
s=s.replace(a,
 'info("[INSTR] outer-wait BEFORE: mode=%s\n", client->mode?client->mode->string:"(null)"); '
 'if (client->mode != MODE_RESTORE) { '+a+' } '
 'info("[INSTR] outer-wait AFTER: mode=%s\n", client->mode?client->mode->string:"(null)");',1)
write(FR,s); print("FR outer-wait guard+log: OK")
print("instrumentation done")
