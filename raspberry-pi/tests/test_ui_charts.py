import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import unittest
from PyQt5 import QtWidgets

from src.ui.main_window import MainWindow


class _Model:
    def __init__(self):
        signal_ids = [
            'grid_voltage_l1','grid_voltage_l2','grid_voltage_l3','dc_link_voltage','output_voltage',
            'grid_current_l1','grid_current_l2','grid_current_l3','output_current',
            'grid_power_l1','grid_power_l2','grid_power_l3','input_power','output_power',
            'temp_pfc','temp_dab_primary','temp_dab_secondary','temp_pcb_primary',
            'temp_pcb_secondary','temp_inductor','temp_transformer',
        ]
        self.definitions = {sid: {'label': sid} for sid in signal_ids}


class ChartSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def test_charts_support_more_signals_than_palette_colors(self):
        window = MainWindow.__new__(MainWindow)
        window.model = _Model()
        root = window._charts()
        self.assertIsNotNone(root)
        self.assertEqual(7, len([
            sid for sid in window.curves
            if sid.startswith('temp_')
        ]))


if __name__ == '__main__':
    unittest.main()
