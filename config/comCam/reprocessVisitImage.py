#!/usr/bin/env python
import os.path

ObsConfigDir = os.path.dirname(__file__)

config.compute_summary_stats.load(os.path.join(ObsConfigDir, "computeExposureSummaryStats.py"))

config.do_apply_flat_background_ratio = True
