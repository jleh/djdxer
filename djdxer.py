import pygame.midi
import pygame.time
import argparse
import subprocess
import math
import yaml
import re

from datetime import datetime, timedelta
from time import sleep


def print_devices():
    for n in range(pygame.midi.get_count()):
        print(n, pygame.midi.get_device_info(n))


def read_settings():
    with open('settings.yaml', 'r') as stream:
        settings = yaml.safe_load(stream)

    return settings

def listen_device(input_device, output_device, settings, hamlibClient):
    debug = 'debug' in settings and settings['debug'] == True

    state = {
        'Compressor': False,
        'Rit': False
    }

    throttled_command = datetime.now()

    def get_input_event_handler(event, input):
        note_match = event[0] == input['note_id']
        data1_match = True if 'data1' not in input else input['data1'] == event[1]
        data2_match = True if 'data2' not in input else input['data2'] == event[2]
        data3_match = True if 'data3' not in input else input['data3'] == event[3]

        return note_match and data1_match and data2_match and data3_match

    def call_hamlib(command):
        hamlibClient.stdin.write((command + '\n').encode('ascii'))
        hamlibClient.stdin.flush()

    def get_hamlib_number_response(command):
        hamlibClient.stdin.write((command + '\n').encode('ascii'))
        hamlibClient.stdin.flush()
        output = hamlibClient.stdout.readline().decode('ascii')
        return int(re.findall(r'\d+', output)[0])

    def execute_hamlib_command(handler):
        command = handler['execute']['command']

        print('Execute hamlib command: ' + command)
        call_hamlib(command)

    def execute_shell_command(event, handler):
        value = event[2]

        if 'normalize_value' in handler:
            value = '{0:03d}'.format(math.floor(event[2] / 1.27))
            if debug: print(value)

        if 'state' in handler:
            state[handler['name']] = not state[handler['name']]
            index = 0 if state[handler['name']] == True else 1
            command = handler['execute']['command'][index]
        else:
            command = handler['execute']['command'].replace('$VALUE', str(value))

        subprocess.run(command, shell=True)

    def switch_leds(handler):
        led = handler['led']

        if 'others' in led:
            for note in range(5):
                output_device.note_on(note, led['others'], led['channel'])

        if 'state' in handler:
            index = 0 if state[handler['name']] == True else 1
            output_device.note_on(led['note_id'], led['value'][index], led['channel'])
        else:
            output_device.note_on(led['note_id'], led['value'], led['channel'])

    # Main loop
    while True:
        if input_device.poll():
            event = input_device.read(1)[0][0]

            if debug:
                print(event)

            event_handlers = list(filter(lambda x: get_input_event_handler(event, x), settings['inputs']))

            for handler in event_handlers:
                if 'throttle' in handler and throttled_command > datetime.now():
                    print('throttled')
                    continue

                if 'name' in handler:
                    print(handler['name'])

                if 'delay' in handler:
                    sleep(handler['delay'])

                if handler['execute']['type'] == 'vfoup':
                    step = handler['execute']['step']
                    current_freq = get_hamlib_number_response('f')
                    call_hamlib('F ' + str(current_freq + step))

                if handler['execute']['type'] == 'vfodown':
                    step = handler['execute']['step']
                    current_freq = get_hamlib_number_response('f')
                    call_hamlib('F ' + str(current_freq - step))

                if handler['execute']['type'] == 'shell':
                    execute_shell_command(event, handler)

                if handler['execute']['type'] == 'hamlib':
                    execute_hamlib_command(handler)

                # if handler['execute']['type'] == 'state':
                #    if handler['state'] in state:
                #        current_state = state[handler['state']]

                if 'led' in handler:
                    switch_leds(handler)

                if 'throttle' in handler:
                    throttled_command = datetime.now() + timedelta(seconds=handler['throttle'])
        
        else:
            # Prevent 100 % CPU utilization
            pygame.time.wait(10)


def start():
    pygame.midi.init()

    settings = read_settings()

    # Start hamlib client subprocess
    rig_model = str(settings['hamlib']['model'])
    rig_device = settings['hamlib']['device']

    hamlibClient = subprocess.Popen(
        ['rigctl', '-m', rig_model, '-r', rig_device], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    midi_input = pygame.midi.Input(settings['input'])
    midi_output = pygame.midi.Output(settings['output'])

    print('Started')

    # Enter main loop
    listen_device(midi_input, midi_output, settings, hamlibClient)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--list-devices', action='store_true', help='List available MIDI devices')
    args = parser.parse_args()

    if args.list_devices:
        print()
        pygame.midi.init()
        print_devices()
    else:
        start()
