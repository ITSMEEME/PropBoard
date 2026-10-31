"""Download pinned upstream Betaflight and build the real x86 SITL target."""
import os,subprocess
from pathlib import Path
REV='024f8e13d4e642eb6a380308685b9ea3aa3ef1a2'
ROOT=Path(__file__).resolve().parents[2]
SOURCE=Path(os.environ.get('BF_SOURCE_DIR',str(ROOT/'.cfd-tools/betaflight')))
def run(*args):subprocess.run(args,check=True)
if not (SOURCE/'.git').exists():
    SOURCE.parent.mkdir(parents=True,exist_ok=True)
    run('git','clone','--depth','1','--branch','4.5.2','https://github.com/betaflight/betaflight.git',str(SOURCE))
actual=subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip()
if actual!=REV:raise SystemExit('Unexpected Betaflight revision; refusing to reset existing source')
header=SOURCE/'src/main/flight/servos.h'
old='#define MAX_SERVO_RULES (2 * MAX_SUPPORTED_SERVOS)'
new='#define MAX_SERVO_RULES (4 * MAX_SUPPORTED_SERVOS) // PropBoard SITL: six swash servos, 18 PID rules'
text=header.read_text()
if old in text:header.write_text(text.replace(old,new))
elif new not in text:raise SystemExit('Unexpected mixer header; inspect source')
target=SOURCE/'src/main/target/SITL/target.h'
text=target.read_text()
if '#define USE_SERVOS' not in text:target.write_text(text.replace('#define USE_PWM_OUTPUT','#define USE_SERVOS // PropBoard SITL: enable upstream servo subsystem\n#define USE_PWM_OUTPUT',1))
# SITL.mk clears ARM_SDK_PREFIX and uses host gcc. The existing /usr directory
# avoids the premature ARM-only SDK check in tools.mk; no ARM compiler is used.
run('make','-C',str(SOURCE),'TARGET=SITL','ARM_SDK_DIR=/usr','-j4')
print('Betaflight 4.5.2 SITL:',SOURCE/'obj/main/betaflight_SITL.elf')
