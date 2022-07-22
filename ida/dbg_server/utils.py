import re, os, sys
import ida_kernwin

PYTHON_DEFAULT_ENCODING = os.getenv('PYTHONIOENCODING', 'utf-8')


def execfile(path: str, cwd=None, argv=[], env={}, encoding=None) -> None:
    if encoding is None:
        with open(path, 'rb') as f:
            raw = f.read()

        encoding = PYTHON_DEFAULT_ENCODING
        encoding_pat = re.compile(r'\s*#.*coding[:=]\s*([-\w.]+).*')
        for line in raw.decode(encoding, errors='replace').split("\n"):
            match = encoding_pat.match(line)
            if match:
                encoding = match.group(1)
                break

        code_text = raw.decode(encoding)
    else:
        with open(path, 'r', encoding=encoding) as f:
            code_text = f.read()

    globals = {'__name__': '__main__', '__file__': path}

    # patch
    orig_argv = sys.argv
    sys.argv = argv
    orig_env = os.environ.copy()
    os.environ.update(env)
    orig_cwd = os.getcwd()
    if not cwd:
        cwd = os.path.split(os.path.abspath(path))[0]
    os.chdir(cwd)
    orig_modules = sys.modules.copy()

    prapare_code = '''
import debugpy
debugpy.debug_this_thread()
debugpy.wait_for_client()

import ida_kernwin
ida_kernwin.refresh_idaview_anyway()
    '''
    prapare = compile(prapare_code, '', 'exec')

    ida_kernwin.execute_sync(lambda: exec(prapare), ida_kernwin.MFF_WRITE)

    code = compile(code_text, path, 'exec', optimize=0)
    ida_kernwin.execute_sync(lambda: exec(code, globals),
                             ida_kernwin.MFF_WRITE)

    # restore
    sys.argv = orig_argv
    os.environ = orig_env
    os.chdir(orig_cwd)
    for k in list(sys.modules.keys()):
        if k not in orig_modules:
            # https://docs.python.org/3/reference/import.html#the-module-cache
            del sys.modules[k]