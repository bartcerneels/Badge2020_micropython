from machine import Pin, PWM

# all buttons are logic low except sw_b
sw_up = Pin(39, Pin.IN) # Hardware pull-up
sw_left = Pin(26, Pin.IN, Pin.PULL_UP)
sw_down = Pin(15, Pin.IN, Pin.PULL_UP)
sw_right = Pin(0, Pin.IN, Pin.PULL_UP)
sw_center = Pin(34, Pin.IN) # Hardware pull-up

sw_start = Pin(32, Pin.IN, Pin.PULL_UP)
sw_select = Pin(36, Pin.IN) # Hardware pull-up, shared with 

sw_a = Pin(13, Pin.IN)
sw_b = Pin(12, Pin.IN, Pin.PULL_UP)

def test_buttons():
    import time

    def clear():
        print("\x1B\x5B2J", end="")
        print("\x1B\x5BH", end="")

    while(1):
        print('up:\t{}'.format(sw_up.value()))
        print('left:\t{}'.format(sw_left.value()))
        print('down:\t{}'.format(sw_down.value()))
        print('right:\t{}'.format(sw_right.value()))
        print('center:\t{}'.format(sw_center.value()))
        print('A:\t{}'.format(sw_a.value()))
        print('B:\t{}'.format(sw_b.value()))
        print('Start:\t{}'.format(sw_start.value()))
        print('Select:\t{}'.format(sw_select.value()))

        time.sleep_ms(300)

        clear()


def test_buzzer():
    buzzer = PWM(Pin(25))
    buzzer.freq(500)
    buzzer.duty(256) # 25%
