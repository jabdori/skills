#!/usr/bin/env python3
"""CSV 폴더의 열 통계, 연결 후보, 여러 파일을 잇는 실제 행을 읽기 전용으로 출력한다."""

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


CONTEXT = ('work_date', 'date', 'shift', 'period', 'day')
POSITIVE = {'approved', 'active', 'open', 'valid', 'yes', 'true'}
NEGATIVE = {'withdrawn', 'cancelled', 'canceled', 'closed', 'no', 'false'}


class Table:
    def __init__(self, path):
        self.name = path.name
        self.columns = []
        self.rows = []
        self.counts = {}
        with path.open(newline='', encoding='utf-8-sig') as source:
            reader = csv.DictReader(source)
            self.columns = reader.fieldnames or []
            if len(self.columns) != len(set(self.columns)):
                raise ValueError(f'중복 열 이름: {path}')
            self.counts = {column: Counter() for column in self.columns}
            for row in reader:
                values = tuple((row.get(column) or '').strip() for column in self.columns)
                self.rows.append((reader.line_num, values))
                for column, value in zip(self.columns, values):
                    self.counts[column][value] += 1
        self.positions = {column: index for index, column in enumerate(self.columns)}
        self.values = {column: set(counts) - {''} for column, counts in self.counts.items()}

    def key(self, row_index, columns):
        values = self.rows[row_index][1]
        return tuple(values[self.positions[column]] for column in columns)

    def output(self):
        columns = {}
        for column in self.columns:
            counts = self.counts[column]
            nonempty = {value: count for value, count in counts.items() if value}
            values = {'empty': counts.get('', 0), 'distinct': len(nonempty),
                      'sample': next(iter(nonempty), '')}
            if len(nonempty) <= 12:
                values['value_counts'] = dict(sorted(nonempty.items()))
            columns[column] = values
        return {'rows': len(self.rows), 'columns': columns}


def key_column(column):
    return (column.endswith(('_id', '_code')) or column in {'id', 'from_site', 'to_site'}
            or column.startswith(('from_', 'to_', 'start_', 'end_'))
            and not column.endswith(('_date', '_at', '_time')))


def name_similarity(left, right):
    if left == right:
        return 1.0
    stop = {'id', 'code', 'from', 'to', 'start', 'end'}
    a = set(left.split('_')) - stop
    b = set(right.split('_')) - stop
    return len(a & b) / len(a | b) if a and b else 0.0


def relation(left, right, left_columns, right_columns, bonus=0.0):
    left_counts = Counter(left.key(index, left_columns) for index in range(len(left.rows)))
    right_counts = Counter(right.key(index, right_columns) for index in range(len(right.rows)))
    left_counts.pop(tuple('' for _ in left_columns), None)
    right_counts.pop(tuple('' for _ in right_columns), None)
    common = left_counts.keys() & right_counts.keys()
    if not common:
        return None
    overlap = len(common) / min(len(left_counts), len(right_counts))
    similarity = sum(name_similarity(a, b) for a, b in zip(left_columns, right_columns)) / len(left_columns)
    if overlap < (0.5 if similarity >= 0.8 else 0.8):
        return None
    if len(common) == 1 and similarity < 0.8:
        return None
    left_unique = max(left_counts[key] for key in common) == 1
    right_unique = max(right_counts[key] for key in common) == 1
    if left_unique and right_unique:
        cardinality = '1:1'
    elif left_unique:
        cardinality = '1:N'
    elif right_unique:
        cardinality = 'N:1'
    else:
        cardinality = 'N:M'
    score = round(overlap * 2 + similarity * 1.5 + bonus
                  + (0.25 if left_unique or right_unique else 0), 3)
    result = {'left_file': left.name, 'left_columns': list(left_columns),
              'right_file': right.name, 'right_columns': list(right_columns),
              'cardinality': cardinality, 'matched_keys': len(common),
              'left_coverage': round(len(common) / len(left_counts), 3),
              'right_coverage': round(len(common) / len(right_counts), 3),
              'score': score, 'candidate': True}
    if cardinality == 'N:1':
        result['left_file'], result['right_file'] = result['right_file'], result['left_file']
        result['left_columns'], result['right_columns'] = result['right_columns'], result['left_columns']
        result['left_coverage'], result['right_coverage'] = result['right_coverage'], result['left_coverage']
        result['cardinality'] = '1:N'
    return result


def relationships(tables):
    names = sorted(tables)
    found = []
    for first, left_name in enumerate(names):
        left = tables[left_name]
        for right_name in names[first + 1:]:
            right = tables[right_name]
            pair = []
            for a in left.columns:
                if not key_column(a):
                    continue
                for b in right.columns:
                    if not key_column(b):
                        continue
                    values_a, values_b = left.values[a], right.values[b]
                    if not values_a or not values_b:
                        continue
                    if min(len(values_a), len(values_b)) > 5000 and name_similarity(a, b) < 0.5:
                        continue
                    if len(values_a & values_b) / min(len(values_a), len(values_b)) < 0.5:
                        continue
                    candidate = relation(left, right, (a,), (b,), 0.2 if a.endswith('_id') or b.endswith('_id') else 0)
                    if candidate:
                        pair.append(candidate)
                        shared = [column for column in CONTEXT if column in left.positions and column in right.positions]
                        date = next((column for column in ('work_date', 'date', 'day') if column in shared), None)
                        if date:
                            composite = relation(left, right, (a, date), (b, date), 0.5)
                            if composite:
                                pair.append(composite)
            shared = [column for column in CONTEXT if column in left.positions and column in right.positions]
            date = next((column for column in ('work_date', 'date', 'day') if column in shared), None)
            if date and 'shift' in shared:
                candidate = relation(left, right, (date, 'shift'), (date, 'shift'), 0.5)
                if candidate:
                    pair.append(candidate)
            pair.sort(key=lambda item: (-item['score'], -len(item['left_columns']), item['left_columns']))
            kept = []
            for candidate in pair:
                if any(candidate['left_columns'] == old['left_columns'] and
                       candidate['right_columns'] == old['right_columns'] and
                       candidate['left_file'] == old['left_file'] for old in kept):
                    continue
                kept.append(candidate)
                if len(kept) == 3:
                    break
            found.extend(kept)
    return sorted(found, key=lambda item: (-item['score'], item['left_file'], item['right_file']))


def positive(row):
    values = set(row[1])
    return len(values & POSITIVE) - len(values & NEGATIVE)


def example_rows(tables, links):
    indexes = {}

    def matching(table_name, columns, key):
        identity = (table_name, tuple(columns))
        if identity not in indexes:
            index = defaultdict(set)
            table = tables[table_name]
            for number in range(len(table.rows)):
                value = table.key(number, columns)
                if all(value):
                    index[value].add(number)
            indexes[identity] = index
        return indexes[identity].get(key, set())

    def trace(start_name, start_row):
        selected = {start_name: start_row}
        via = {}
        while len(selected) < len(tables):
            choices = []
            for target in tables.keys() - selected.keys():
                groups = defaultdict(set)
                reasons = {}
                linked_sources = set()
                specificity = {}
                for link in links:
                    if link['left_file'] == target and link['right_file'] in selected:
                        source = link['right_file']
                        key = tables[source].key(selected[source], link['right_columns'])
                        matches = matching(target, link['left_columns'], key)
                    elif link['right_file'] == target and link['left_file'] in selected:
                        source = link['left_file']
                        key = tables[source].key(selected[source], link['left_columns'])
                        matches = matching(target, link['right_columns'], key)
                    else:
                        continue
                    linked_sources.add(source)
                    if matches:
                        size = len(link['left_columns'])
                        if size > specificity.get(source, 0):
                            groups[source] = set(matches)
                            reasons[source] = (source, link)
                            specificity[source] = size
                        elif size == specificity[source]:
                            groups[source].update(matches)
                if not groups or set(groups) != linked_sources:
                    continue
                candidates = set.intersection(*groups.values())
                if not candidates:
                    continue
                chosen = min(candidates, key=lambda number: (-positive(tables[target].rows[number]), number))
                choices.append((len(groups), -len(candidates), target, chosen, reasons))
            if not choices:
                break
            _, _, target, chosen, reasons = max(choices, key=lambda item: (item[0], item[1], item[2]))
            selected[target] = chosen
            source, link = next(iter(reasons.values()))
            via[target] = {'from_file': source,
                           'left_file': link['left_file'], 'left_columns': link['left_columns'],
                           'right_file': link['right_file'], 'right_columns': link['right_columns']}
        return selected, via

    seeds = []
    for name, table in tables.items():
        front = list(range(min(20, len(table.rows))))
        good = [i for i, row in enumerate(table.rows) if positive(row) > 0][:10]
        seeds.extend((name, index) for index in dict.fromkeys(front + good))
    seeds.sort(key=lambda item: (
        -positive(tables[item[0]].rows[item[1]]),
        -int(any(column.endswith(('_state', '_status')) or column in {'state', 'status'}
                 for column in tables[item[0]].columns)), item[0], item[1]))
    best = ({}, {})
    for name, index in seeds[:90]:
        candidate = trace(name, index)
        def score(selection):
            return (len(selection[0]), sum(positive(tables[file].rows[row]) for file, row in selection[0].items()))
        if score(candidate) > score(best):
            best = candidate
    selected, via = best
    output = {}
    for name, index in selected.items():
        table = tables[name]
        line, values = table.rows[index]
        output[name] = {'line': line, 'row': dict(zip(table.columns, values))}
        if name in via:
            output[name]['via'] = via[name]
    return {'coverage': len(output), 'anchor': next(iter(selected), None), 'rows': output}


def profile_folder(folder):
    paths = sorted(folder.glob('*.csv'))
    if not paths:
        raise ValueError(f'CSV 파일이 없습니다: {folder}')
    tables = {path.name: Table(path) for path in paths}
    links = relationships(tables)
    return {'files': {name: table.output() for name, table in tables.items()},
            'relationships': links, 'example': example_rows(tables, links)}


def main():
    parser = argparse.ArgumentParser(description='CSV 폴더를 읽어 관계 후보와 실제 연결 예시를 JSON으로 출력합니다.')
    parser.add_argument('folder', type=Path)
    args = parser.parse_args()
    try:
        report = profile_folder(args.folder)
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(1, f'{error}\n')
    json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == '__main__':
    main()
