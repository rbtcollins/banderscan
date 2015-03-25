#!/usr/bin/python
import argparse
import json
import os.path
import Queue as queue
from multiprocessing import Process, Queue, Event, Pool
import pprint
import tarfile
import tempfile
import zipfile

from fixtures import TempDir

def yield_packages(root):
    for dirpath, dirnames, filenames in os.walk(root):
        if not filenames:
            continue
        filenames.sort()
        if '.tar.gz' not in filenames[-1] and '.zip' not in filenames[-1]:
            continue
        yield os.path.join(dirpath, filenames[-1])


def extract_setup_py_cfg(path):
    try:
        if path.endswith('.tar.gz'):
            t = tarfile.open(name=path, mode='r')
            try:
                ti = t.next()
                while ti:
                    # Issue 14160 appears to still be around in some form.
                    if not ti.issym():
                        name = os.path.basename(ti.name)
                        if name in ('setup.py', 'setup.cfg'):
                            content = t.extractfile(ti)
                            if content:
                                yield name, content.read()
                    ti = t.next()
            finally:
                t.close()
        elif path.endswith('.zip'):
            z = zipfile.ZipFile(path, 'r')
            try:
                for n in ('setup..py', 'setup.cfg'):
                    try:
                        yield n, z.open(n).read()
                    except:
                        pass
            finally:
                z.close()
        else:
            yield 'failed', 'Cannot handle path %s' % path
    except Exception as e:
        yield 'failed', str(e)


def analyse_sdist(path):
    setup_py = None
    setup_cfg = None
    error = None
    setup_requires = False
    for name, contents in extract_setup_py_cfg(path):
        if name == 'setup.py':
            setup_py = contents.decode('utf8', 'replace')
            if 'setup_requires' in setup_py:
                setup_requires = True
        elif name == 'setup.cfg':
            setup_cfg = contents.decode('utf8', 'replace')
            # As d2to1 doesn't support setup-requires, we don't analyze
            # setup.cfg today.
        else:
            error = contents
    return path, {'setup.py': setup_py,
                  'setup.cfg': setup_cfg,
                  'error': error,
                  'has_setup_requires': setup_requires}


def main():
    parser = argparse.ArgumentParser(description='Analyze a bandersnatch mirror.')
    parser.add_argument('--json',
                       help='save raw data to a json file',
                       default=None)
    args = parser.parse_args()
    concurrency = 8
    root = "/var/spool/pypi/web/packages/source/"
    p = Pool()
    results = {}
    try:
        try:
            for path, result in \
                p.imap_unordered(analyse_sdist, yield_packages(root)):
                results[path] = result
            p.close()
        except:
            p.terminate()
            raise
    finally:
        p.join()
    if args.json:
        with open(args.json, 'wb') as f:
            f.write(json.dumps(results))
    pprint.pprint(results)


if __name__ == '__main__':
    main()
