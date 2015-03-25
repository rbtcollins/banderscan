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


def analyse_setup((sdist, data)):
    if not data['has_setup_requires']:
        return sdist, None
    return sdist, data['setup.py']
    return path, {'setup.py': setup_py,
                  'setup.cfg': setup_cfg,
                  'error': error,
                  'has_setup_requires': setup_requires}


def main():
    parser = argparse.ArgumentParser(description='Analyze a saved json file.')
    parser.add_argument('json',
                       help='load raw data from a json file',
                       default=None)
    args = parser.parse_args()
    with open(args.json, 'rb') as f:
        data = json.loads(f.read())
    p = Pool()
    results = {}
    try:
        try:
            for path, result in p.imap_unordered(analyse_setup, data.items()):
                if result:
                    results[path] = result
            p.close()
        except:
            p.terminate()
            raise
    finally:
        p.join()
    pprint.pprint(results)
    print "total setup.py's", len(data)
    print "setup_requires", len(results)


if __name__ == '__main__':
    main()
