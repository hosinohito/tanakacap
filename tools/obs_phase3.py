"""Local isolated OBS WebSocket verification; credentials stay in ignored config."""
import base64,hashlib,json,os,socket,struct,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class OBS:
 def __init__(self):
  config=json.loads((ROOT/'results/phase3-obs/app/config/obs-studio/plugin_config/obs-websocket/config.json').read_text(encoding='utf-8-sig'))
  self.sock=socket.create_connection(('127.0.0.1',4456),timeout=30);self.file=self.sock.makefile('rb');self.counter=0
  key=base64.b64encode(os.urandom(16)).decode()
  self.sock.sendall(('GET / HTTP/1.1\r\nHost: 127.0.0.1:4456\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: '+key+'\r\nSec-WebSocket-Version: 13\r\n\r\n').encode())
  assert b'101' in self.file.readline()
  while self.file.readline()!=b'\r\n':pass
  hello=self.recv()['d'];identify=dict(rpcVersion=1,eventSubscriptions=0)
  if 'authentication' in hello:
   a=hello['authentication'];secret=base64.b64encode(hashlib.sha256((config['server_password']+a['salt']).encode()).digest()).decode()
   identify['authentication']=base64.b64encode(hashlib.sha256((secret+a['challenge']).encode()).digest()).decode()
  self.send(dict(op=1,d=identify));assert self.recv()['op']==2
 def frame(self,data,opcode=1):
  mask=os.urandom(4);n=len(data);head=bytes([128|opcode,128|(n if n<126 else 126 if n<65536 else 127)])
  if n>=126:head+=struct.pack('!H' if n<65536 else '!Q',n)
  self.sock.sendall(head+mask+bytes(b^mask[i%4] for i,b in enumerate(data)))
 def send(self,obj):self.frame(json.dumps(obj).encode())
 def recv(self):
  pieces=[]
  while True:
   a,b=self.file.read(2);n=b&127
   if n==126:n=struct.unpack('!H',self.file.read(2))[0]
   if n==127:n=struct.unpack('!Q',self.file.read(8))[0]
   if n>32*1024*1024:raise ValueError('Oversized local OBS message')
   mask=self.file.read(4) if b&128 else None;data=self.file.read(n)
   if mask:data=bytes(v^mask[i%4] for i,v in enumerate(data))
   if a&15==8:raise RuntimeError('OBS closed connection')
   if a&15==9:self.frame(data,10);continue
   if a&15==10:continue
   pieces.append(data)
   if a&128:return json.loads(b''.join(pieces))
 def call(self,name,**data):
  self.counter+=1;rid=str(self.counter);self.send(dict(op=6,d=dict(requestType=name,requestId=rid,requestData=data)))
  while True:
   r=self.recv()
   if r['op']==7 and r['d']['requestId']==rid:
    d=r['d']
    if not d['requestStatus']['result']:raise RuntimeError(name+': '+str(d['requestStatus']))
    return d.get('responseData',{})
 def close(self):self.file.close();self.sock.close()
if __name__=='__main__':
 o=OBS();print(o.call('GetVersion'));kinds=o.call('GetInputKindList')['inputKinds'];print('spout kinds',[k for k in kinds if 'spout' in k.lower()])
 for k in kinds:
  if 'spout' in k.lower():print(k,o.call('GetInputDefaultSettings',inputKind=k))
 o.close()
