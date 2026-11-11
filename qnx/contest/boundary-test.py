import json,subprocess,time,socket,pathlib,os,signal
base=pathlib.Path('/home/dominik/projekty/qnx8-development/vm/official/output')
out=pathlib.Path('/tmp/toretto-qnx-boundary');out.mkdir(exist_ok=True)
sock=out/'com2.sock';log=out/'console.log'
if sock.exists():sock.unlink()
cmd=['qemu-system-x86_64','-machine','pc','-accel','tcg,thread=multi','-cpu','max','-smp','2','-m','2048','-display','none','-serial','stdio','-serial',f'unix:{sock},server=on,wait=off','-monitor','none','-no-reboot','-nic','none','-kernel',str(base/'ifs-serial-stream.bin'),'-drive',f'file={base}/test-disk/disk-qemu.vmdk,if=ide,format=vmdk']
with log.open('wb') as f:
 p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT)
 try:
  for i in range(150):
   if b'TORETTO_STREAM_PID=' in log.read_bytes():break
   if p.poll() is not None:raise RuntimeError('QNX exited')
   time.sleep(.2)
  else:raise RuntimeError('QNX boot timeout')
  payloads=[b'not-json\n',b'{"event":"other"}\n',b'{"event":"ble_window","identity_observations":[]}\n']
  for i in range(70):
   payloads.append((json.dumps({'event':'ble_window','identity_observations':[{'fingerprint':'boundary','address':f'AA:BB:CC:DD:EE:{i:02X}','scan_id':i+1}]},separators=(',',':'))+'\n').encode())
  for raw in payloads:
   with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
    s.connect(str(sock))
    for pos in range(0,len(raw),64):s.sendall(raw[pos:pos+64]);time.sleep(.012)
   time.sleep(.035)
  for _ in range(200):
   events=[]
   for line in log.read_text(errors='replace').splitlines():
    if '{\"engine\":\"toretto-qnx-live\"' in line:
     line=line[line.index('{\"engine\":\"toretto-qnx-live\"'):] 
     try:
      j=json.loads(line)
      if j.get('engine')=='toretto-qnx-live':events.append(j)
     except ValueError:pass
   if len(events)>=71:break
   time.sleep(.15)
  assert len(events)==71,(len(events),log)
  last=events[-1]
  assert last['windows']==71 and last['total_observations']==70,last
  assert last['shared_payload_groups']==1,last
  print('QNX_BOUNDARY_PASS',json.dumps(last,sort_keys=True))
 finally:
  p.terminate()
  try:p.wait(timeout=5)
  except subprocess.TimeoutExpired:p.kill();p.wait()
