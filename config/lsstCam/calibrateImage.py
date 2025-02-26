import os.path

config_dir = os.path.dirname(__file__)

config.photometry.applyColorTerms = False
config.photometry.photoCatName = "the_monster_20250219"
config.connections.photometry_ref_cat = "the_monster_20250219"
config.connections.astrometry_ref_cat = "the_monster_20250219"
config.photometry_ref_loader.load(os.path.join(config_dir, "filterMap.py"))
config.compute_summary_stats.load(os.path.join(config_dir, "computeExposureSummaryStats.py"))
