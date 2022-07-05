import re, os, sys

PYTHON_DEFAULT_ENCODING = os.getenv('PYTHONIOENCODING', 'utf-8')


def execfile(path: str,
             cwd=None,
             argv=[],
             env={},
             globals={},
             encoding=None) -> None:
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

    globals['__name__'] = '__main__'
    globals['__file__'] = path

    # patch
    orig_argv = sys.argv
    sys.argv = argv
    orig_env = os.environ.copy()
    os.environ.update(env)
    orig_cwd = os.getcwd()
    if not cwd:
        cwd = os.path.split(os.path.abspath(path))[0]
    os.chdir(cwd)


    code = compile(code_text, path, 'exec')

    exec(code, globals)

    # restore
    sys.argv = orig_argv
    os.environ = orig_env
    os.chdir(orig_cwd)