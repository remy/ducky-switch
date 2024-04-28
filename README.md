# MacOS Ducky Switcher

I kept running into trouble running the official ducky switcher, but found that python could control the device directly, so I wrote my own switcher.

I've limited experience with python (so of course the code is a mess), but hopefully these instructions are good enough to follow to repeat elsewhere.

## Install

Download this code and drop it into a local working directory (I'll assume it's called `ducky-switch` for now).

From the command line, run:

```sh
$ python3 -m venv p
$ p/bin/pip3 install -U PyObjC
$ p/bin/pip3 install hidapi
```

## Configuration

The config is very simplistic. A call named `config.json` should be saved in the working directory (i.e. `ducky-switch`).

The contents is an array of strings, each string represents the title of the app you want to match to, and it's position in the array represents the profile number.

For example, if the string `"code"` is in the array at position 1 (the second position as the array starts at zero), this would match my "VS Code" software and switch to Profile 2 (since DuckyPad profiles start from 1 onwards).

If you want to match different application titles to the same profile, simply comma separate them. Such as `"chrome,firefox,safari"` at array position 0 will match my apps "Google Chrome Canary", "Firefox" and "Safari" - notice that the strings are case _insensitive_.

### Example

```json
["firefox,chrome", "code", "slack", "fusion"]
```

This is my own config. `"firefox,chrome"` matches Profile 1, `"code"` to Profile 2 and so on.

## Running

Note that to access the device, you'll need to run with `sudo`. To run in the foreground (i.e. to test with or to stop with ctrl+c):

```sh
$ sudo python switcher.py
```

To run in the background:

```sh
$ nohup sudo p/bin/python switcher.py &
```

You can then close the terminal and it will continue to run.

## Issues

I originally tried to daemonize this process but couldn't get it to work (see previous comment about python experience). I also tried to use launchd, but even though the script was called from a .plist in `/Library/LaunchDaemons`, _and_ the user was `root`, it still didn't have permission to open the USB port. I don't know why.

## Licence

- [MIT](https://rem.mit-license.org/)
