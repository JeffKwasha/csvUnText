#!/usr/bin/env python3
import csv
from typing import List, Dict
from pathlib import Path
from argparse import ArgumentParser, Namespace
import locale
import re
import logging
from pprint import pprint

locale.setlocale(locale.LC_ALL, '')


def get_args() -> Namespace:
    ap = ArgumentParser(description="fixups for csv files")
    ap.add_argument('filenames', metavar='N', type=str, nargs="+", help="Files to fix")
    ap.add_argument('--recurse', '-r', action='store_true', help='traverse directories')
    ap.add_argument('--verbose', '-v', action='store_true', help='be loud')
    #ap.add_argument('--simple', '-s', action='store_true', help='Not Implemented')
    ap.add_argument('--skiplines', '-s', type=int, default=2, help='number of lines to skip')
    return ap.parse_args()


def read(filenames: list, skiplines: int = 2) -> List[dict]:
    rv = []
    for fn in filenames:
        name = str(fn)
        try:
            with open(fn, 'rt') as f:
                for _ in range(skiplines):
                    f.readline()
                reader = csv.DictReader(f)
                rv.append({'name': name,
                           'fieldnames': reader.fieldnames,
                           'rows': list(reader)})
        except FileNotFoundError as e:
            rv.append({'name': name,
                       'error': str(e),
                       'fieldnames': None,
                       'rows': None})
    return rv


def to_number(val: str) -> (float, str):
    if not val or val == '--':
        return val, None
    strips = ''.maketrans('', '', '$%')
    _CSN_RE = '[+-]?\s*\d{1,3}(,\d\d\d)*(\.\d\d)?'
    categories = [
        {'test': re.compile(_CSN_RE),
         'cat': 'general',
         'fn': lambda v: locale.atof(v.translate(strips))},
        {'test': re.compile(r'[+-]?\$'+_CSN_RE),
         'cat': 'currency',
         'fn': lambda v: f"${locale.atof(v.translate(strips))}"},
        {'test': re.compile(_CSN_RE+'%'),
         'cat': 'percent',
         'fn': lambda v: str(locale.atof(v.translate(strips)))+'%'},
    ]
    val = val.strip()
    for di in categories:
        if di['test'].fullmatch(val):
            return di['fn'](val), di['cat']
    return val, None


def fixup(name, fields, rows):
    """ find numbers in rows and make them numbers"""
    # FUTURE: remember columns and warn/apply the same
    for row in rows:
        for k in row.keys():
            val, cat = to_number(row[k])
            if val and cat:
                row[k] = val


def save(name: str, fields: List[str], rows: List[dict]):
    path = Path(name)
    with open(path, 'wt') as f:
        writer = csv.DictWriter(f, fields, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = get_args()
    filedatas = read(args.filenames, args.skiplines)
    for d in filedatas:
        if 'error' in d:
            logging.error(f"{d['name']}: {d['error']}")
            continue
        fixup(name=d['name'], fields=d['fieldnames'], rows=d['rows'])
        save(name=d['name'], fields=d['fieldnames'], rows=d['rows'])
    return 0


if __name__ == '__main__':
    logging.basicConfig()
    rc = main()
    exit(rc)
