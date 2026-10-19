"""Run the opaque public CLI with bounded stdlib boundary fault instrumentation."""
import errno
import fcntl
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import threading
import time

script=sys.argv[1]
sys.argv=sys.argv[1:]
marker=os.environ.get('REVIEW_FAULT_MARKER')
if marker:
    for name in ('replace','rename'):
        original=getattr(os,name)
        def intercepted(source,destination,*args,_original=original,**kwargs):
            if os.path.basename(os.fspath(destination))=='review-state.json':
                Path(marker).write_text('reached manifest publication boundary')
                raise OSError(errno.EIO,'SYNTHETIC_SECRET_FILESYSTEM /private/fixture/account')
            return _original(source,destination,*args,**kwargs)
        setattr(os,name,intercepted)

executable=os.environ.get('REVIEW_FAKE_PI_EXECUTABLE')
control=os.environ.get('REVIEW_FAKE_PI_CONTROL')
if executable and control and os.environ.get('REVIEW_SATURATE_OWNED_PIPE')=='1':
    original_popen=subprocess.Popen
    def intercepted_popen(command,*args,**kwargs):
        process=original_popen(command,*args,**kwargs)
        if isinstance(command,(list,tuple)) and os.path.realpath(shutil.which(os.fspath(command[0])) or os.fspath(command[0]))==os.path.realpath(executable):
            def saturate():
                deadline=time.monotonic()+10
                while not Path(control+'.stalled').exists() and time.monotonic()<deadline:
                    time.sleep(.01)
                if not Path(control+'.stalled').exists():
                    return
                descriptor=process.stdin.fileno()
                original_flags=fcntl.fcntl(descriptor,fcntl.F_GETFL)
                total=0
                try:
                    fcntl.fcntl(descriptor,fcntl.F_SETFL,original_flags|os.O_NONBLOCK)
                    while total<1024*1024:
                        try:
                            total+=os.write(descriptor,b'{"id":"synthetic-fill","type":"get_state"}\n'*100)
                        except BlockingIOError:
                            Path(control+'.saturated').write_text(str(total))
                            return
                finally:
                    fcntl.fcntl(descriptor,fcntl.F_SETFL,original_flags)
            threading.Thread(target=saturate,daemon=True).start()
        return process
    subprocess.Popen=intercepted_popen
runpy.run_path(script,run_name='__main__')
