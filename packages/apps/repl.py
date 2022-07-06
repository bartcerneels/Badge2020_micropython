import hardware_setup
from gui.core.ugui import Screen, ssd, Window
from gui.widgets import Label, Button, CloseButton
from gui.core.writer import CWriter

# Font for CWriter
import gui.fonts.font10 as font
from gui.core.colors import *

import system

import uasyncio as asyncio

wri = CWriter(ssd, font, YELLOW, BLACK, verbose=False)

class BaseScreen(Screen):
    def __init__(self):
        super().__init__()

        row = (ssd.height//2)
        col = 2
        l = Label(wri, row, col, text='REPL running on USB serial.')
        print(l.row, l.width)
        row = ssd.height - 30
        print(Label(wri, row, 10, 'Hold boot 5 seconds to recover.').width)
        CloseButton(wri)

async def shutdown():
    await asyncio.sleep(5)
    BaseScreen.shutdown()

def run():
    print("REPL is running.")
    asyncio.create_task(shutdown())
    Screen.change(BaseScreen)

run()
