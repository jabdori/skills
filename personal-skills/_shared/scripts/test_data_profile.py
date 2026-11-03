import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from data_profile import profile_folder


SCRIPT = Path(__file__).with_name('data_profile.py')


class DataProfileTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def csv(self, name, columns, rows):
        with (self.folder / name).open('w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(columns)
            writer.writerows(rows)

    def test_rows_missing_values_relations_and_one_record(self):
        self.csv('warehouses.csv', ['warehouse_id', 'name'], [('W1', '북쪽'), ('W2', '')])
        self.csv('stock.csv', ['warehouse_id', 'work_date', 'units'],
                 [('W1', '2027-01-01', 8), ('W1', '2027-01-02', 7), ('W2', '2027-01-01', 4)])
        self.csv('orders.csv', ['order_id', 'warehouse_id', 'work_date', 'shift'],
                 [('O1', 'W1', '2027-01-01', 'morning'), ('O2', 'W1', '2027-01-01', 'morning')])
        self.csv('crews.csv', ['crew_id', 'start_warehouse', 'work_date', 'shift'],
                 [('C1', 'W1', '2027-01-01', 'morning'), ('C2', 'W1', '2027-01-01', 'morning')])

        report = profile_folder(self.folder)

        self.assertEqual(report['files']['warehouses.csv']['rows'], 2)
        self.assertEqual(report['files']['warehouses.csv']['columns']['name']['empty'], 1)
        self.assertEqual(report['files']['stock.csv']['columns']['warehouse_id']['distinct'], 2)
        self.assertTrue(any(
            {relation['left_file'], relation['right_file']} == {'warehouses.csv', 'stock.csv'}
            and relation['cardinality'] == '1:N' for relation in report['relationships']))
        self.assertTrue(any(
            {relation['left_file'], relation['right_file']} == {'orders.csv', 'crews.csv'}
            and len(relation['left_columns']) == 2
            and set(relation['left_columns']) == {'work_date', 'shift'}
            for relation in report['relationships']))
        self.assertEqual(set(report['example']['rows']), set(report['files']))
        self.assertEqual(report['example']['coverage'], 4)
        self.assertTrue(all('line' in record and 'row' in record
                            for record in report['example']['rows'].values()))
        example = {name: item['row'] for name, item in report['example']['rows'].items()}
        self.assertEqual(example['stock.csv']['work_date'], example['crews.csv']['work_date'])

    def test_cli_outputs_json_and_disconnected_file(self):
        self.csv('items.csv', ['item_id'], [('I1',)])
        self.csv('unrelated.csv', ['code'], [('Z9',)])

        result = subprocess.run([sys.executable, str(SCRIPT), str(self.folder)],
                                text=True, capture_output=True)

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(len(report['files']), 2)
        self.assertEqual(report['example']['coverage'], 1)

    def test_example_keeps_route_and_approved_request_consistent(self):
        self.csv('warehouses.csv', ['warehouse_id', 'gas_code'], [('W1', 'G'), ('W2', 'G')])
        self.csv('orders.csv', ['order_id', 'target_id', 'gas_code'],
                 [('O1', 'T1', 'G'), ('O2', 'T2', 'G')])
        self.csv('permissions.csv', ['order_id', 'work_date', 'shift', 'permission_state'],
                 [('O1', '2027-01-01', 'morning', 'withdrawn'),
                  ('O2', '2027-01-01', 'morning', 'approved')])
        self.csv('crews.csv', ['crew_id', 'start_warehouse', 'work_date', 'shift', 'available'],
                 [('C1', 'W2', '2027-01-01', 'morning', 'yes')])
        self.csv('moves.csv', ['from_site', 'to_site', 'minutes'],
                 [('W1', 'W2', 2), ('W1', 'T1', 3), ('W2', 'T2', 4)])

        report = profile_folder(self.folder)
        rows = {name: item['row'] for name, item in report['example']['rows'].items()}

        self.assertEqual(report['example']['coverage'], 5)
        self.assertEqual(rows['permissions.csv']['permission_state'], 'approved')
        self.assertEqual(rows['moves.csv']['from_site'], rows['crews.csv']['start_warehouse'])
        self.assertEqual(rows['moves.csv']['to_site'], rows['orders.csv']['target_id'])

    def test_date_and_shift_form_a_composite_key(self):
        self.csv('requests.csv', ['request_id', 'date', 'shift'],
                 [('R1', '2027-01-01', 'A'), ('R2', '2027-01-02', 'B')])
        self.csv('workers.csv', ['worker_id', 'date', 'shift'],
                 [('W1', '2027-01-01', 'A'), ('W2', '2027-01-02', 'B')])

        report = profile_folder(self.folder)

        self.assertTrue(any(set(link['left_columns']) == {'date', 'shift'}
                            and set(link['right_columns']) == {'date', 'shift'}
                            for link in report['relationships']))

    def test_low_cardinality_code_and_semicolon_license_are_conditions(self):
        self.csv('orders.csv', ['order_id', 'gas_code', 'work_date', 'shift', 'state'],
                 [('O1', 'G-A', '2027-01-01', 'A', 'withdrawn'),
                  ('O2', 'G-B', '2027-01-01', 'A', 'approved')])
        self.csv('cabinets.csv', ['cabinet_id', 'gas_code'], [('W1', 'G-A'), ('W2', 'G-B')])
        self.csv('crews.csv', ['crew_id', 'start_cabinet', 'gas_licenses', 'work_date', 'shift'],
                 [('C1', 'W1', 'G-A', '2027-01-01', 'A'),
                  ('C2', 'W2', 'G-A;G-B', '2027-01-01', 'A')])

        report = profile_folder(self.folder)
        conditions = report['conditions']
        self.assertTrue(any({c['left_file'], c['right_file']} == {'orders.csv', 'cabinets.csv'}
                            and c['operator'] == 'equals' and 'G-B' in c['shared_values']
                            for c in conditions))
        self.assertTrue(any(c['left_file'] == 'orders.csv' and c['right_file'] == 'crews.csv'
                            and c['operator'] == 'contains' and 'G-B' in c['shared_values']
                            for c in conditions))
        self.assertFalse(any('gas_code' in c['left_columns'] or 'gas_code' in c['right_columns']
                             for c in report['relationships']))
        rows = {name: item['row'] for name, item in report['example']['rows'].items()}
        self.assertEqual(report['example']['coverage'], 3)
        self.assertEqual(rows['orders.csv']['gas_code'], rows['cabinets.csv']['gas_code'])
        self.assertIn(rows['orders.csv']['gas_code'], rows['crews.csv']['gas_licenses'].split(';'))


if __name__ == '__main__':
    unittest.main()
