"""Local HTTP/UDP/TCP bridge for REAL Betaflight SITL. Python stdlib only.

Serves this checkout and exchanges 18-double FDM / 68-byte raw motor+servo packets.
SITL enables the upstream servo subsystem and 32 instead of 16 mixer rules.
"""
import argparse,json,math,os,signal,socket,struct,subprocess,threading,time
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
REV='024f8e13d4e642eb6a380308685b9ea3aa3ef1a2'
def finite_vector(v,n):return isinstance(v,list) and len(v)==n and all(isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x) for x in v)
class Firmware:
    def __init__(self,source,state):
        self.source=source;self.state=state;state.mkdir(parents=True,exist_ok=True)
        self.clock=0.;self.last_frame=0.;self.last_packet=0.;self.raw=None;self.serial=None;self.serial_lock=threading.Lock();self.lock=threading.Lock();self.stop=False;self.proc=None;self.version=None;self.last_status=0.;self.status={};self.running=False;self.last_rc_clock=-1.;self.msp_buffer=b'';self.fdm_state={};self.controls=({},False,True)
        self.udp=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);self.output=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);self.output.bind(('127.0.0.1',9001));self.output.settimeout(.2)
        self.rx=threading.Thread(target=self.receive,daemon=True);self.rx.start()
        self.start_process();self.ticker=threading.Thread(target=self.tick,daemon=True);self.ticker.start();self.rc_worker=threading.Thread(target=self.rc_tick,daemon=True);self.rc_worker.start()
        try:self.configure()
        except Exception:self.close();raise
    def start_process(self):
        self.log=open(self.state/'firmware.log','a')
        self.proc=subprocess.Popen([str(self.source/'obj/main/betaflight_SITL.elf')],cwd=self.state,stdout=self.log,stderr=self.log)
    def receive(self):
        while not self.stop:
            try:b,_=self.output.recvfrom(2048)
            except socket.timeout:continue
            except OSError:return
            if len(b)==68:
                count=struct.unpack_from('<H',b)[0];values=list(struct.unpack_from('<16f',b,4))
                if count==2 and all(math.isfinite(x) for x in values[:8]):self.raw={'motorCount':count,'motors':values[:2],'servos':values[2:8]};self.last_packet=time.monotonic()
    def send_fdm(self,state):
        dt=state.get('dt',.0025);self.clock+=dt
        q=state.get('q',[1,0,0,0]);w=state.get('w',[0,0,0]);v=state.get('v',[0,0,0]);p=state.get('p',[0,0,0]);acc=state.get('specificForce',[0,0,9.80665])
        # Use the upstream Gazebo quaternion convention without an extra body
        # rotation: sitl.c/imu.c already implement their pitch/gyro sign changes.
        values=[self.clock,*w,-acc[0],acc[1],-acc[2],*q,v[0],-v[1],-v[2],p[0],-p[1],-p[2],101325.]
        self.udp.sendto(struct.pack('<18d',*values),('127.0.0.1',9003))
    def send_rc(self,sticks,armed,angle):
        rc=[1500+500*sticks.get('roll',0),1500+500*sticks.get('pitch',0),1500+500*sticks.get('throttle',-1),1500+500*sticks.get('yaw',0),2000 if armed else 1000,2000 if angle else 1000,1500+150*sticks.get('throttle',-1)]+[1500]*9
        # RC acknowledgements are parsed alongside later status replies.
        self.msp(200,struct.pack('<16H',*[round(max(1000,min(2000,x))) for x in rc]),wait=False)
    def tick(self):
        while not self.stop:
            state=self.fdm_state
            if time.monotonic()-self.last_frame>.15:state={**state,'w':[0,0,0],'v':[0,0,0]}
            try:self.send_fdm(state)
            except OSError:return
            time.sleep(.0025)
    def rc_tick(self):
        while not self.stop:
            if self.running:
                try:
                    self.send_rc(*self.controls if time.monotonic()-self.last_frame<=.15 else ({},False,True))
                    if time.monotonic()-self.last_status>.25:self.read_status()
                except (OSError,RuntimeError):self.status={'armed':False,'armingDisabled':['MSP_LINK_ERROR']}
            time.sleep(.01)
    def connect_serial(self):
        for _ in range(150):
            if self.proc.poll() is not None:raise RuntimeError('SITL exited; inspect '+str(self.state/'firmware.log'))
            try:self.serial=socket.create_connection(('127.0.0.1',5761),timeout=.15);self.serial.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1);self.serial.settimeout(.5);self.msp_buffer=b'';return
            except OSError:time.sleep(.05)
        raise RuntimeError('SITL UART1 did not start')
    def cli(self,line):
        self.serial.sendall((line+'\n').encode());data=b'';deadline=time.monotonic()+2
        while time.monotonic()<deadline:
            try:data+=self.serial.recv(65536)
            except socket.timeout:continue
            if not data or data.endswith(b'# '):break
        text=data.decode(errors='replace')
        if 'ERROR' in text or 'Invalid' in text:raise RuntimeError('Betaflight CLI rejected '+line+': '+text)
        return text
    def configure(self):
        self.connect_serial();self.serial.sendall(b'#')
        banner=b'';deadline=time.monotonic()+5
        while not banner.endswith(b'# ') and time.monotonic()<deadline:
            try:banner+=self.serial.recv(65536)
            except socket.timeout:continue
        if not banner.endswith(b'# '):raise RuntimeError('Betaflight CLI prompt did not arrive')
        version=self.cli('version')
        if '4.5.2' not in version:raise RuntimeError('Unexpected firmware version')
        self.version='Betaflight 4.5.2 / '+REV[:7]+' / native SITL (32 servo rules)'
        commands=subprocess.check_output(['node',str(HERE/'betaflight_mixer.cjs')],text=True)
        (self.state/'mixer.cli').write_text(commands)
        for line in commands.splitlines():self.cli(line)
        self.serial.sendall(b'save\n')
        # Let dyad consume the command before closing the TCP client.
        deadline=time.monotonic()+5
        while self.proc.poll() is None and time.monotonic()<deadline:
            try:
                if not self.serial.recv(65536):break
            except socket.timeout:continue
        self.serial.close();self.serial=None
        self.proc.wait(timeout=5);self.log.close();self.start_process();self.connect_serial();time.sleep(.5)
        actual=None
        for _ in range(5):
            try:actual=self.msp(3);break
            except RuntimeError:time.sleep(.1) # UART may open before the MSP scheduler starts.
        if actual is None:raise RuntimeError('SITL scheduler did not become MSP-ready after reboot')
        if list(actual[:3])!=[4,5,2]:raise RuntimeError('Firmware MSP version verification failed')
        self.running=True
        self.msp(205) # Real firmware accelerometer calibration, with idle FDM ticks.
        time.sleep(2)
        self.read_status()
    def read_status(self):
        data=self.msp(101);extra=data[15]&15
        flags=struct.unpack_from('<I',data,17+extra)[0]
        names=['NOGYRO','FAILSAFE','RXLOSS','NOT_DISARMED','BOXFAILSAFE','RUNAWAY','CRASH','THROTTLE','ANGLE','BOOTGRACE','NOPREARM','LOAD','CALIB','CLI','CMS','BST','MSP','PARALYZE','GPS','RESCUE_SW','DSHOT_TELEM','REBOOT_REQD','DSHOT_BBANG','NO_ACC_CAL','MOTOR_PROTO','ARMSWITCH']
        self.status={'armed':bool(struct.unpack_from('<I',data,6)[0]&1),'armingDisabled':[name for i,name in enumerate(names) if flags&(1<<i)],'attitudeDeg':[v/10 if i<2 else v for i,v in enumerate(struct.unpack('<3h',self.msp(108)))]}
        self.last_status=time.monotonic();return self.status
    def msp(self,cmd,payload=b'',wait=True):
        with self.serial_lock:
            checksum=len(payload)^cmd
            for v in payload:checksum^=v
            packet=b'$M<'+bytes([len(payload),cmd])+payload+bytes([checksum]);self.serial.sendall(packet)
            if not wait:return b''
            deadline=time.monotonic()+1
            while time.monotonic()<deadline:
                while True:
                    start=self.msp_buffer.find(b'$M>')
                    if start<0:self.msp_buffer=self.msp_buffer[-2:];break
                    self.msp_buffer=self.msp_buffer[start:]
                    if len(self.msp_buffer)<6:break
                    n=self.msp_buffer[3];end=6+n
                    if len(self.msp_buffer)<end:break
                    packet=self.msp_buffer[:end];self.msp_buffer=self.msp_buffer[end:]
                    check=n^packet[4]
                    for v in packet[5:-1]:check^=v
                    if check!=packet[-1]:raise RuntimeError('MSP checksum mismatch')
                    if packet[4]==cmd:return packet[5:-1]
                try:
                    part=self.serial.recv(4096)
                    if not part:raise RuntimeError('MSP connection closed')
                    self.msp_buffer+=part
                except socket.timeout:continue
            raise RuntimeError('MSP timeout')
    def frame(self,body):
        state=body.get('state',{});sticks=body.get('sticks',{})
        if not all(finite_vector(state.get(k),n) for k,n in [('q',4),('w',3),('p',3),('v',3),('specificForce',3)]):raise ValueError('Invalid FDM state')
        if not isinstance(state.get('dt'),(int,float)) or not 0<state['dt']<=.01:raise ValueError('Invalid time step')
        if abs(sum(x*x for x in state['q'])-1)>.01:raise ValueError('Quaternion not normalized')
        if not all(isinstance(sticks.get(k), (int,float)) and math.isfinite(sticks[k]) and abs(sticks[k])<=1 for k in ['roll','pitch','yaw','throttle']):raise ValueError('Invalid sticks')
        if type(body.get('armed')) is not bool or type(body.get('angle')) is not bool:raise ValueError('Invalid mode')
        with self.lock:
            before=self.last_packet;self.fdm_state=state;self.controls=(sticks,body['armed'],body['angle']);self.last_frame=time.monotonic()
            end=time.monotonic()+.15
            while self.last_packet<=before and time.monotonic()<end:time.sleep(.0005)
            if self.last_packet<=before:raise RuntimeError('No fresh Betaflight motor/servo packet')
            raw={**self.raw,**self.status};raw['firmware']=self.version;raw['ageMs']=(time.monotonic()-self.last_packet)*1000
            raw['duty']=[max(0,min(.95,(v-1000)/1000)) for v in raw['motors']]
            raw['servoRad']=[max(-.45,min(.45,(v-1500)/500*.45)) for v in raw['servos']]
            return raw
    def close(self):
        self.stop=True
        if self.serial:self.serial.close()
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:self.proc.wait(timeout=3)
            except subprocess.TimeoutExpired:self.proc.kill();self.proc.wait()
        self.output.close();self.udp.close();self.log.close()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--port',type=int,default=8765);ap.add_argument('--source',type=Path,default=Path(os.environ.get('BF_SOURCE_DIR',str(ROOT/'.cfd-tools/betaflight'))));ap.add_argument('--state',type=Path,default=ROOT/'.cfd-tools/betaflight-state');args=ap.parse_args()
    firmware=Firmware(args.source.resolve(),args.state.resolve())
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
        def result(self,status,body):
            data=json.dumps(body,allow_nan=False).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
        def do_GET(self):
            if self.path=='/api/betaflight/status':
                try:self.result(200,{'firmware':firmware.version,'mspVersion':list(firmware.msp(3)),'mixer':'2 motors / 6 servos; nominal P10 Jacobian','realFirmware':True,**firmware.read_status()})
                except Exception as e:self.result(503,{'error':str(e)})
            else:super().do_GET()
        def do_POST(self):
            if self.path!='/api/betaflight/frame':return self.result(404,{'error':'Unknown endpoint'})
            if self.headers.get('Sec-Fetch-Site')=='cross-site':return self.result(403,{'error':'Same-origin requests only'})
            try:
                n=int(self.headers.get('Content-Length','0'))
                if not 0<n<=16384:raise ValueError('Invalid request length')
                self.result(200,firmware.frame(json.loads(self.rfile.read(n))))
            except ValueError as e:self.result(400,{'error':str(e)})
            except Exception as e:self.result(503,{'error':str(e)})
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    def terminate(_sig,_frame):raise KeyboardInterrupt
    signal.signal(signal.SIGTERM,terminate)
    print(firmware.version+'; HTTP port '+str(args.port),flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close();firmware.close()
if __name__=='__main__':main()
