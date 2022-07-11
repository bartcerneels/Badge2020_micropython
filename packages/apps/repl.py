import hardware_setup
from gui.core.writer import CWriter

# Font for CWriter
import gui.fonts.font10 as font
from gui.core.colors import *

ssd = hardware_setup.ssd

wri = CWriter(ssd, font, YELLOW, BLACK, verbose=False)

display = hardware_setup.disp

def run():
    print("REPL is running.")
    display.print_centred(wri, ssd.width//2, ssd.height//2, 'REPL running on USB serial.')

    display.print_centred(wri, ssd.width//2, ssd.height-20, 'Hold boot 5 seconds to recover.')

    ssd.show()

run()
