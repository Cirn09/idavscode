# IDAVSCode

Debug IDAPython in VSCode!

## Features

![](https://raw.githubusercontent.com/cirn09/idavscode/master/idavscode/image/demo.webp)
## Requirements

Install [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python) and [IDA plugin](https://github.com/cirn09/idavscode) first.

## launch.json

```json
{
    "name": "IDAPython debug",
    "type": "idapython",
    "request": "launch",
    "program": "${file}",
    "host": "localhost",                                // control hostname
    "port": 5677,                                       // control port
    "pythonPath": "${command:python.interpreterPath}",  // python path (IDA used)
    "logFile": "",                                      // debug log file
    "debugConfig": {                                    // Python extension debug config
        "type": "python",
        "request": "attach",
        "justMyCode": true,
        "connect": {
            // "host": "localhost",                     // optional, default as seam as control host
            "port": 5678                                // debug port
        },
        "cwd": "${workspaceFolder}"
    }
}
```

## Known Issues

![Known Issues](GITHUB LINK HERE!!!)

## Release Notes

Users appreciate release notes as you update your extension.

### 0.0.1

Initial release
