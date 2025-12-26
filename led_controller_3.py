import sys
import time
import math
from array import array
from esp32 import RMT
from machine import Pin, PWM, reset, Timer

PIN0 = 6
PIN1 = 7

class Program:
    def __init__(self):
        self.pins = {}
        self.timers = {}
        self.x_timer = None
        self.x_pwm = None
        self.x_pin = -1
        self.x_duty = 0
        self.x_direction = 1

        self.sine_buf = array('B', [int(127.5 + 127.5 * math.sin(2 * math.pi * i / 128)) for i in range(128)])
        print(self.sine_buf)
        self.a_timer = None
        self.a_pin = -1
        self.a_dac = None
        self.a_step = 0


        # # # # Camera trigger
        # self.trigger = Pin(TRIGGER_PIN, Pin.OUT, Pin.PULL_DOWN)
        # self.trigger.off()

        # # # # Camera strobe
        # self.strobe = Pin(STROBE_PIN, Pin.IN)
        # self.strobe.irq(trigger=Pin.IRQ_RISING|Pin.IRQ_FALLING, handler=self.handle)


    # def cb(self, timer):
    #     self.led.off()

    # def handle(self, pin):
    #     if pin.value():
    #        self.led.off()
    #        print("rising")
    #     else:
    #        self.led.on()
    #        print("falling")
     #self.tim0.init(period=1000, mode=Timer.ONE_SHOT, callback=self.cb)
        # if not pin.value():
        #     self.rmt = esp32.RMT(0, pin=self.led, clock_div=64) # 1 time unit = 3 us
        #     self.rmt.write_pulses((32767,), 1)  # Send HIGH for 32767 * 100ns = 3ms
        # else:
        #     self.rmt.deinit()

           
    def handle_a_command(self, line):
        from machine import DAC

        s = line.split(' ')

        if self.a_timer is not None:
            print(f"Stopping sine wave on pin {self.a_pin}.")
            self.a_timer.deinit()
            self.a_timer = None
            if self.a_pin in self.pins:
                if self.pins[self.a_pin] is self.a_dac:
                    del self.pins[self.a_pin]
            self.a_dac = None
            self.a_pin = -1

        if len(s) < 2:
            return

        pin_num = int(s[1])
        freq = 1
        if len(s) > 2:
            freq = float(s[2])

        if pin_num not in [25, 26]:
            print("Error: DAC is only available on pins 25 and 26.")
            return

        print(f"Starting sine wave on pin {pin_num} at {freq} Hz.")

        if pin_num in self.pins and isinstance(self.pins[pin_num], DAC):
            dac = self.pins[pin_num]
        else:
            if pin_num in self.pins and hasattr(self.pins[pin_num], 'deinit'):
                self.pins[pin_num].deinit()
                del self.pins[pin_num]
            dac = DAC(Pin(pin_num))
            self.pins[pin_num] = dac
        
        self.a_dac = dac
        self.a_pin = pin_num
        self.a_step = 0

        update_freq = freq * len(self.sine_buf)
        
        self.a_timer = Timer(2)
        try:
            self.a_timer.init(freq=int(update_freq), mode=Timer.PERIODIC, callback=self.update_a_dac)
        except ValueError as e:
            print(f"Error starting timer: {e}. Desired sine freq {freq}Hz may be too high.")
            # cleanup
            if self.a_pin in self.pins:
                if self.pins[self.a_pin] is self.a_dac:
                    del self.pins[self.a_pin]
            self.a_dac = None
            self.a_pin = -1


    def update_a_dac(self, timer):
        self.a_dac.write(self.sine_buf[self.a_step])
        self.a_step = (self.a_step + 1) % len(self.sine_buf)

    def update_x_pwm(self, timer):
        duty_step = 1024 # 65536 / 1024 = 64 steps. at 1280Hz, this is 50ms.

        # Calculate new duty
        new_duty = self.x_duty + self.x_direction * duty_step

        # Check boundaries and change direction
        if new_duty >= 65535:
            new_duty = 65535
            self.x_direction = -1
        elif new_duty <= 0:
            new_duty = 0
            self.x_direction = 1
        
        self.x_duty = new_duty
        self.x_pwm.duty_u16(self.x_duty)

    def handle_x_command(self, line):
        # If called with 'X' only, it stops the running instance.
        s = line.split(' ')
        
        if self.x_timer is not None:
            print(f"Stopping X mode on pin {self.x_pin}.")
            self.x_timer.deinit()
            self.x_timer = None
            if self.x_pwm:
                self.x_pwm.deinit()
            if self.x_pin in self.pins:
                # Make sure it's the PWM from X mode
                if self.pins[self.x_pin] is self.x_pwm:
                     del self.pins[self.x_pin]
            self.x_pwm = None
            self.x_pin = -1

        # if only "X" is sent, we just stop. If "X pin" is sent, we start on new pin.
        if len(s) < 2:
            return

        pin_num = int(s[1])
        print(f"Starting X mode on pin {pin_num}.")
        
        # Setup PWM on pin_num
        if pin_num in self.pins:
            if hasattr(self.pins[pin_num], 'deinit'):
                self.pins[pin_num].deinit()
        
        pin_obj = Pin(pin_num, Pin.OUT)
        pwm = PWM(pin_obj)
        self.pins[pin_num] = pwm
        
        pwm.freq(10000)
        
        self.x_pwm = pwm
        self.x_pin = pin_num
        self.x_duty = 0
        self.x_direction = 1
        self.x_pwm.duty_u16(self.x_duty)

        # Setup timer
        self.x_timer = Timer(1) 
        self.x_timer.init(freq=1280, mode=Timer.PERIODIC, callback=self.update_x_pwm)


    def handle_l_command(self, line):
        s = line.split(' ')
        pin_num = int(s[1])
        val = bool(int(s[2]))

        if pin_num in self.pins:
            del self.pins[pin_num]
        print(f"Creating new Pin {pin_num}")
        self.pins[pin_num] = Pin(pin_num, Pin.OUT)

        pin = self.pins[pin_num]
        if isinstance(pin, PWM):
            print(f"Re-initializing Pin {pin_num} from PWM to OUT")
            pin = Pin(pin_num, Pin.OUT)
            self.pins[pin_num] = pin
        
        if val:
            print(f"Pin {pin_num} on")
            pin.on()
        else:
            print(f"Pin {pin_num} off")
            pin.off()

    def handle_p_command(self, line):
        s = line.split(' ')
        pin_num = int(s[1])
        freq = int(s[2])
        duty = int(s[3])

        if pin_num in self.pins:
            del self.pins[pin_num]
        print(f"Creating new PWM for Pin {pin_num}")
        pin_obj = Pin(pin_num, Pin.OUT)
        self.pins[pin_num] = PWM(pin_obj)

        pwm = self.pins[pin_num]
        pwm.freq(freq)
        pwm.duty_u16(duty)
        print(f"Set Pin {pin_num} to PWM: freq={freq}, duty={duty}")
        print(pwm)

    def handle_r_command(self, line):
        reset()

    def handle_q_command(self, line):
        print("Start rmt") 
        s = line.split(' ')
        clock_div = int(s[1])
        pulse_time = int(s[2])
        one_shot = bool(int(s[3]))
        pin0 = int(s[4])
        pin1 = int(s[5])


        if pin0 in self.pins:
            del self.pins[pin0]
            print(f"Creating new RMT for Pin {pin0}")


        if pin1 in self.pins:
            del self.pins[pin1]
            print(f"Creating new RMT for Pin {pin1}")


        print(f"Using pulse time: {pulse_time}")
        print(f"One shot: {one_shot}")
        self.pins[pin0] = RMT(0, pin=Pin(pin0), clock_div=clock_div)
        self.pins[pin1] = RMT(1, pin=Pin(pin1), clock_div=clock_div)
        if not one_shot:
            self.pins[pin0].loop(-1)
            self.pins[pin1].loop(-1)
         

        self.pins[pin0].write_pulses(pulse_time, [1,0,0,0])
        self.pins[pin1].write_pulses(pulse_time, [0,0,1,0])

        print("Started rmt")

    def cb(self, timer):
        pin = self.timers[timer]
        pin_obj = self.pins[pin]
        pin_obj.toggle()
        
    def handle_f_command(self, line):
        s = line.split(' ')
        pin_num = int(s[1])
        freq = int(s[2])

        if pin_num in self.timers:
            self.timers[pin_num].deinit()
            del self.timers[pin_num]

        if pin_num in self.pins:
            del self.pins[pin_num]
        
        print(f"Creating new Pin {pin_num} for toggling")
        pin = Pin(pin_num, Pin.OUT)

        print(f"Setting up timer for Pin {pin_num} at {freq} Hz")
        timer = Timer(0)
        self.pins[pin_num] = pin
        timer.init(freq=freq, mode=Timer.PERIODIC, callback=self.cb)       
        print(f"Pin {pin_num} is now toggling at {freq} Hz")
        self.timers[timer] = pin_num

    def handle_u_command(self, line):
        s = line.split(' ')
        pin_num = int(s[1])
        pulse_len_us = int(s[2])

        if pin_num in self.pins:
            pin_obj = self.pins[pin_num]
            if hasattr(pin_obj, 'deinit'):
                pin_obj.deinit()
            del self.pins[pin_num]
        
        pin = Pin(pin_num, Pin.OUT)
        self.pins[pin_num] = pin

        print(f"Pulsing Pin {pin_num} for {pulse_len_us} us")
        pin.on()
        time.sleep_us(pulse_len_us)
        pin.off()
        print(f"Pin {pin_num} pulse finished.")
         # elif line.startswith('Q'):
                #     rmt = esp32.RMT(0, pin=Pin(LED_PIN), clock_div=1) # 1 time unit = 3 us
                #     rmt.write_pulses((10,), 1)
                #     rmt.wait_done()
                #     rmt.deinit()
 elif line.startswith('C'):
                    s = line.split(' ')
                    self.trigger.off()
                    utime.sleep_ms(10)
                    delay = int(s[1])
                    print("trigger camera for", delay)
                    self.trigger.on()
                    #utime.sleep_us(delay)
                    utime.sleep_ms(delay)
                    self.trigger.off()
 # elif line.startswith('N'):
                #     s = line.split(' ')
                #     b = bool(int(s[1]))
                #     if b:
                #         print("trigger on")
                #         self.trigger.on()
                #     else:
                #         print("trigger off")
                #         self.trigger.off()
            else:
                
    def loop(self):
        command_map = {
            'A': self.handle_a_command,
            'X': self.handle_x_command,
            'L': self.handle_l_command,
            'P': self.handle_p_command,
            'R': self.handle_r_command,
            'Q': self.handle_q_command,
            'F': self.handle_f_command,
            'U': self.handle_u_command,
        }
        while True:
            try:
                sys.stdout.write('controller:> ')
                line = input()
                if line == 'exit':
                    break
                command = line[0]
                if command in command_map:
                    command_map[command](line)
                else:
                    print("Unknown command")
            except Exception as e:
                print(str(e))

p = Program()
print("Version 0.4")
p.loop()
