from yaml import load as _load_yml, dump

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


DEFAULT_CFG_PATH = 'config.yml'


def load(path=DEFAULT_CFG_PATH):
    return read_yaml(path)


def read_yaml(path):
    with open(path, 'r') as f:
        return _load_yml(f, Loader=Loader)


def write_yaml(path, content):
    with open(path, 'w') as f:
        f.write(dump(content, Dumper=Dumper))
