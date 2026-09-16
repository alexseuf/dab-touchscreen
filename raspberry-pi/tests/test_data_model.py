import unittest
from datetime import datetime, timedelta, timezone
import yaml
from src.data.model import DataModel

class DataModelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open('config/topics.yaml', encoding='utf-8') as handle:
            cls.defs=yaml.safe_load(handle)['signals']
    def test_all_required_signals_present(self):
        required={'grid_voltage_l1','grid_voltage_l2','grid_voltage_l3','grid_current_l1','grid_current_l2','grid_current_l3','grid_power_l1','grid_power_l2','grid_power_l3','grid_frequency','input_power','dc_link_voltage','output_voltage','output_current','output_power','temp_pfc','temp_dab_primary','temp_dab_secondary','temp_inductor','temp_transformer'}
        self.assertEqual(required,set(self.defs))
    def test_valid_invalid_and_stale(self):
        m=DataModel(self.defs,1);topic=self.defs['output_voltage']['topic']
        self.assertEqual(m.update_topic(topic,b'401.2').quality,'valid')
        self.assertEqual(m.update_topic(topic,b'broken').quality,'invalid')
        m.update_topic(topic,b'400',datetime.now(timezone.utc)-timedelta(seconds=2))
        self.assertEqual(m.get('output_voltage').quality,'stale')
    def test_unknown_topic_is_ignored(self): self.assertIsNone(DataModel(self.defs).update_topic('unknown',b'1'))

if __name__=='__main__':unittest.main()
