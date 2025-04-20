import unittest

#fix for import files in upper directory
import sys
import os
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
import serialUtils

class TestSerial(unittest.TestCase):
    def test_linemodifier_laserAdjust1(self):
        l = "G1 S100"
        jobParams = {}
        jobParams['laserPowerAdjust'] = 50
        result = serialUtils.linemodifier_laserAdjustPower(l, jobParams)
        self.assertEqual(result, "G1 S50")

    def test_linemodifier_laserAdjust2(self):
        l = "G1 S100"
        jobParams = {}
        jobParams['laserPowerAdjust'] = 0
        result = serialUtils.linemodifier_laserAdjustPower(l, jobParams)
        self.assertEqual(result, "G1 S0")

    def test_linemodifier_laserAdjust3(self):
        l = "G1 S100"
        jobParams = {}
        jobParams['laserPowerAdjust'] = 5000
        result = serialUtils.linemodifier_laserAdjustPower(l, jobParams)
        self.assertEqual(result, "G1 S1000")

    def test_linemodifier_laserAdjust4(self):
        l = "G1 Y23S600F1800"
        jobParams = {}
        jobParams['laserSpeedAdjust'] = 50
        result = serialUtils.linemodifier_laserAdjustSpeed(l, jobParams)
        self.assertEqual(result, "G1 Y23S600F900")

    def test_linemodifier_laserAdjust5(self):
        l = "G1 Y23S600F1800"
        jobParams = {}
        jobParams['laserSpeedAdjust'] = 200
        result = serialUtils.linemodifier_laserAdjustSpeed(l, jobParams)
        self.assertEqual(result, "G1 Y23S600F3600")        
        
if __name__ == '__main__':
    unittest.main()