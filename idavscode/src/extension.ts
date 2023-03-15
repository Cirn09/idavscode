// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';
import { WorkspaceFolder, DebugConfiguration, ProviderResult, CancellationToken } from 'vscode';
import * as WebSocket from 'ws';

const enum MessageType {
	startDebugServer = 'startDebugServer',
	stopDebugServer = 'stopDebugServer',
	stopServer = 'stopServer',
	executeScript = 'executeScript',

	serverReady = 'serverReady',
	debugServerReady = 'debugServerReady',
	debugFinished = 'debugFinished',
	error = 'error'
}

// this method is called when your extension is activated
// your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
	// context.subscriptions.push(vscode.commands.registerCommand('idacode.connectToIDA', connectToIDA));
	const provider = new IDAPythonConfigurationProvider();
	context.subscriptions.push(vscode.debug.registerDebugConfigurationProvider('idapython', provider));
}

// this method is called when your extension is deactivated
export function deactivate() { }



class IDAPythonConfigurationProvider implements vscode.DebugConfigurationProvider {

	provideDebugConfigurations?(folder: WorkspaceFolder | undefined, token?: CancellationToken): ProviderResult<DebugConfiguration[]> {
		return [
			{
				"name": "IDAPython debug",
				"type": "idapython",
				"request": "launch",
				"program": "${file}",
				"host": "localhost",
				"port": 5677,
				"timeout": 3000,
				"pythonPath": "${command:python.interpreterPath}",
				"logFile": "",
				"debugConfig": {
					"type": "python",
					"request": "attach",
					"justMyCode": true,
					"connect": {
						"port": 5678
					},
					"cwd": "${workspaceFolder}"
				}
			}
		];
	}

	/**
	 * Massage a debug configuration just before a debug session is being launched,
	 * e.g. add all missing attributes to the debug configuration.
	 */

	resolveDebugConfiguration(folder: WorkspaceFolder | undefined, config: DebugConfiguration, token?: CancellationToken): ProviderResult<DebugConfiguration> {
		if (!config.host || !config.port || !config.debugConfig || !config.debugConfig.connect || !config.debugConfig.connect.port) {
			return vscode.window.showInformationMessage("complete the debug config").then(_ => {
				return undefined;	// abort launch
			});
		}

		if (!config.program) { config.program = '${file}'; }
		if (!config.pythonPath) { config.pythonPath = '${command:python.interpreterPath}'; }
		if (config.timeout === undefined) { config.timeout = 3000; }
		config.debugConfig.type = 'python';
		config.debugConfig.request = 'attach';
		config.debugConfig.redirectOutput = true;
		config.debugConfig.showReturnValue = true;
		config.debugConfig.debugOptions = ["RedirectOutput", "ShowReturnValue"];
		if (!config.debugConfig.cwd) { config.debugConfig.cwd = '${workspaceFolder}'; }
		if (!config.debugConfig.connect.host) { config.debugConfig.connect.host = config.host; }

		return config;
	}

	resolveDebugConfigurationWithSubstitutedVariables(folder: WorkspaceFolder | undefined, config: DebugConfiguration, token?: CancellationToken): ProviderResult<DebugConfiguration> {

		return remoteIDAPythonExec(config);
	}
}


async function remoteIDAPythonExec(config: DebugConfiguration): Promise<DebugConfiguration | undefined> {
	try {
		await _remoteIDAPythonExec(config);
		vscode.commands.executeCommand('workbench.debug.action.focusRepl');
		return config.debugConfig;
	}
	catch (e: Error | string | any) {
		vscode.window.showErrorMessage(e);
		return undefined;	// abort launch
	}
}

function _remoteIDAPythonExec(config: DebugConfiguration): Promise<string> {
	let socket = new WebSocket(`ws://${config.host}:${config.port}/`);
	let timer: NodeJS.Timeout | undefined = undefined;

	const clearTimer = () => {
		if (timer) {
			clearTimeout(timer);
			timer = undefined;
		}
	};

	return new Promise((resolve, reject) => {

		timer = setTimeout(() => {
			socket.close();
			reject(new Error(`WebSocket connection timeout after ${config.timeout} ms`));
		}, config.timeout);

		socket.on('open', () => {
			clearTimer();
			socket.send(JSON.stringify({
				'type': MessageType.startDebugServer,
				'host': config.debugConfig.connect.host,
				'port': config.debugConfig.connect.port,
				'logfile': config.logFile,
				'pythonPath': config.pythonPath
			}));
		});

		socket.on('message', (data: WebSocket.Data) => {
			const json = JSON.parse(data.toString());
			switch (json.type) {
				case MessageType.debugServerReady:
					socket.send(JSON.stringify({
						'type': MessageType.executeScript,
						'path': config.program,
						'cwd': config.debugConfig.cwd,
						'argv': config.debugConfig.args,
						'env': config.debugConfig.env,
						// 'encoding': config.encoding
						// sadly, vscode seem to not provide api to get file encoding
					}));
					break;

				case MessageType.serverReady:
					resolve('ok');
					socket.close();
					break;

				case MessageType.debugFinished:
					socket.close();
					vscode.debug.stopDebugging();
					break;

				case MessageType.error:
					reject(json.info);
					socket.close();
					break;
			}
		});

		socket.on('error', (err) => {
			clearTimer();
			reject(err);
		});
	});
}