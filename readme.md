# djdxer

Use a MIDI DJ controller to use computer controlled amateur radio rig.

This is a work in progress so not all features are documented on this readme.

## Install

This software requires python & rigctld to be installed.

## Configuration

Configuration is provided with yaml file. Example:

```yaml
debug: True
input: 0
output: 1
hamlib:
  model: 2
  device: localhost:4532

inputs: 
  - note_id: 1
    data1: 1 
    data2: 1
    data3: 1
    name: TX on
    execute:
      type: hamlib
      command: T 1
```

### debug

`true | false`

Print debug logging. Useful to check contoller codes.

### input
Input MIDI device id.

You can list available devices with `-l` parameter.

### output
Output MIDI device id.

### hamlib

#### hamlib.model
Radio model id.

#### hamlib.device
Radio device.

### inputs
List of input handlers. Input handler is matched using `note_id`, `data1`, `data2` & `data3`.
Handler is used if all provided values are matched.

#### inputs.note_id
MIDI note id. Usually id of the pressed button or button group.

#### inputs.data1
First data value. Useful if more than one button provides same note_id.

#### inputs.data2
Second data value. Useful to get direction of jog wheel or if you want to execute command
on specific potentiometer value.

#### inputs.name
Optional name for input handler.

#### inputs.delay
Wait x seconds before executing command.

#### inputs.thottle
Wait x seconds before next (command with throttled option set) command is executed.
Inputs during this period are ignored.

#### inputs.normalize_value
Normalize input values of 1-127 to scale of 1-100.

#### inputs.execute
Command to execute. Possible execute types are `noop`, `shell`, `hamlib`, `vfoup`, `vfodown`.

```yaml
type: noop
```
Does nothing.

```yaml
type: shell
command: ~/script.sh $VALUE
```
Runs shell command on input. You can use value of `data2` with $VALUE

```yaml
type: hamlib
command: T 0
```
Runs hamlib command with `rigctld`.

```yaml
type: vfoup
step: 100
```
Moves vfo up.

```yaml
type: vfoup
step: 100
```
Moves vfo down.

#### inputs.led
Sets controller led.

```yaml
led:
  channel: 0
  note_id: 28
  value: 0
```
