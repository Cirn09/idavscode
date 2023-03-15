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
    "timeout": 3000,                                    // timeout for connect
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

See [Known Issues](https://github.com/Cirn09/idavscode/blob/master/README_en.md#Known_Issues)
