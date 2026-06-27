# Windows fix: recovery->restore hotplug event never fires (libusb has no hotplug
# on Windows), so the device DOES enter restore (re-run sees mode=4) but the in-run
# wait never wakes. Fix: actively POLL restore_check_mode() like a fresh run does.
def read(p): return open(p,encoding="utf-8").read()
def write(p,s): open(p,"w",encoding="utf-8",newline="\n").write(s)
NL=chr(92)+"n"
M='client->mode?client->mode->string:"(null)"'

IDR="external/idevicerestore/src/idevicerestore.c"
REC="external/idevicerestore/src/recovery.c"
FR="src/futurerestore.cpp"

# 1) surface every device-event callback
s=read(IDR); n=s.count('debug("%s: device %016" PRIx64')
s=s.replace('debug("%s: device %016" PRIx64','info("%s: device %016" PRIx64')
write(IDR,s); print("IDR callbacks debug->info:",n)

# 2) recovery.c: replace the single event-wait with an active POLL loop
s=read(REC)
a='cond_wait_timeout(&client->device_event_cond, &client->device_event_mutex, 30000);'
assert a in s, "REC anchor missing"
poll=('info("[INSTR] enter_restore: POLLING for RESTORE (Windows hotplug workaround)...'+NL+'"); '
 '{ int _p; for (_p=0; _p<300 && client->mode==MODE_RECOVERY && !(client->flags & FLAG_QUIT); _p++) { '
   'cond_wait_timeout(&client->device_event_cond, &client->device_event_mutex, 100); '
   'if (client->mode != MODE_RECOVERY) break; '
   'mutex_unlock(&client->device_event_mutex); '
   'int _rc = restore_check_mode(client); '
   'mutex_lock(&client->device_event_mutex); '
   'if (_rc == 0) { client->mode = MODE_RESTORE; info("[INSTR] POLL: detected RESTORE at iter %d'+NL+'", _p); break; } '
 '} } '
 'info("[INSTR] enter_restore: poll done, mode=%s'+NL+'", '+M+');')
s=s.replace(a, poll, 1)
write(REC,s); print("REC active-poll fix: OK")

# 3) futurerestore.cpp: keep guard + log on outer wait
s=read(FR)
a='cond_wait_timeout(&client->device_event_cond, &client->device_event_mutex, 180000);'
assert a in s, "FR anchor missing"
s=s.replace(a,'info("[INSTR] outer-wait BEFORE: mode=%s'+NL+'", '+M+'); if (client->mode != MODE_RESTORE) { '+a+' } info("[INSTR] outer-wait AFTER: mode=%s'+NL+'", '+M+');',1)
write(FR,s); print("FR outer-wait guard+log: OK")
print("instrumentation+fix done")
