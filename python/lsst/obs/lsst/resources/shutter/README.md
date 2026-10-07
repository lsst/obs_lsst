# LSSTCam shutter-plane beam table

`beam_at_L3S1_z9.618_rot0_evaluated.tnt` is the raytraced ray bundle at the shutter plane
(z = 9.618 mm from L3 surface S1), at rotator angle 0. For each field position (CCS mm)
it gives the blade coordinate (CCS-x mm) below which a fraction q of the pixel's beam
flux lies, for q = 0.01 ... 0.99.

- Author: A. Rasmussen (LSST Camera), the method of LCA-20578.
- Source: `/sdf/group/rubin/u/arasmus/shutter-data-20250619/shutterplane_beam_DB/` at USDF;
  also public in lsst-dm/ap_pipe-notebooks (`tickets/DM-50985`, `data/`).
- sha256: `9aa3f0f308b0fb5d59315a408156f9832fd47ba9db52bb1b6d055171eac7de0d` (checked by
  `tests/test_shutterBeam.py`).
- Used by `lsst.ip.isr.shutterTiming` (per-pixel mid-exposure times), via
  `shutterTiming.beamFile` in `config/lsstCam/` overrides.
