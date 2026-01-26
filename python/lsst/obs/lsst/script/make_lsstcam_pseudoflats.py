import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from scipy import integrate
from astropy.table import Table
import argparse

from lsst.daf.butler import Butler
from lsst.utils import getPackageDir
import lsst.afw.cameraGeom
from lsst.afw.image import ExposureF, FilterLabel
from lsst.pipe.tasks.visualizeVisit import (
    VisualizeBinExpConfig,
    VisualizeBinExpTask,
    VisualizeMosaicExpConfig,
    VisualizeMosaicExpTask,
)
from .._instrument import LsstCam


def write_pseudoflats(butler: Butler | None, output_collection: str | None):
    vignetting_coeffs = np.asarray(
        [
            -2.04748298e+12,
            4.62036195e+12,
            -4.55318392e+12,
            2.55519946e+12,
            -8.86592878e+11,
            1.89254514e+11,
            -2.11087631e+10,
            -2.68228152e+08,
            4.87993883e+08,
            -8.03764403e+07,
            6.99808127e+06,
            -3.58577957e+05,
            1.05491604e+04,
            -1.60565953e+02,
            9.96009337e-01,
            9.98941038e-01,
        ],
    )

    lsstcam_instr = LsstCam()
    camera = lsstcam_instr.getCamera()

    filter_dict = {
        "u_24": "u",
        "g_6": "g",
        "r_57": "r",
        "i_39": "i",
        "z_20": "z",
        "y_10": "y",
        "none": "white",
        "empty": "white",
    }

    wavelengths = np.arange(300.0, 1101.0)

    # Read in the throughputs for everything but filter + detector.
    tput_path = os.path.join(getPackageDir("throughputs"), "baseline")

    hw_no_det_filter = np.ones(len(wavelengths))
    for element in ["lens1", "lens2", "lens3", "m1", "m2", "m3", "atmos_std"]:
        edat = Table.read(os.path.join(tput_path, f"{element}.dat"), format="ascii")
        interp = interp1d(edat["col1"], edat["col2"], bounds_error=False, fill_value=0.0)
        hw_no_det_filter *= interp(wavelengths)

    det_tput_path = os.path.join(
        lsstcam_instr.getObsDataPackageDir(),
        lsstcam_instr.policyName,
        "transmission_sensor",
    )
    filter_tput_path = os.path.join(
        lsstcam_instr.getObsDataPackageDir(),
        lsstcam_instr.policyName,
        "transmission_filter_detector",
    )

    visualize_bin_exp_config = VisualizeBinExpConfig()
    visualize_bin_exp_task = VisualizeBinExpTask(config=visualize_bin_exp_config)

    visualize_mosaic_exp_config = VisualizeMosaicExpConfig()
    visualize_mosaic_exp_task = VisualizeMosaicExpTask(config=visualize_mosaic_exp_config)

    for filter_name, band in filter_dict.items():
        print("Generating pseudo-flats for ", band)
        central_values = np.zeros(len(camera))

        for i, detector in enumerate(camera):
            try:
                det_tput = Table.read(
                    os.path.join(det_tput_path, detector.getName().lower(), "19700101T000000.ecsv"),
                    format="ascii.ecsv",
                )
            except FileNotFoundError:
                # This is one of the non-science chips; use detector 4 an
                # arbitrary ITL chip.
                det_tput = Table.read(
                    os.path.join(det_tput_path, "r01_s11", "19700101T000000.ecsv"),
                    format="ascii.ecsv",
                )

            if band != "white":
                filter_tput = Table.read(
                    os.path.join(
                        filter_tput_path,
                        detector.getName().lower(),
                        filter_name,
                        "19700101T000000.ecsv",
                    ),
                    format="ascii.ecsv",
                )

            tput = hw_no_det_filter.copy()

            # All the amps are recorded the same.
            det_tput_use, = np.where(det_tput["amp_name"] == "C00")
            int_func = interp1d(
                det_tput["wavelength"][det_tput_use],
                det_tput["efficiency"][det_tput_use]/100.,
                bounds_error=False,
                fill_value=0.0,
            )
            tput *= int_func(wavelengths)

            if band != "white":
                int_func = interp1d(
                    filter_tput["wavelength"],
                    filter_tput["efficiency"]/100.,
                    bounds_error=False,
                    fill_value=0.0,
                )
                tput *= int_func(wavelengths)

            # Integrate this to get the (unflatscaled) throughput
            central_values[i] = integrate.simpson(y=tput / wavelengths, x=wavelengths)

        # Divide by the central detector.
        central_values /= central_values[94]

        pseudo_flats_binned = []

        # Make a bunch of exposures with individual vignetting.
        for i, detector in enumerate(camera):
            print(f"Generating pseudo-flat for {band} detector {detector.getId()}")
            pseudo_flat = ExposureF(detector.getBBox())
            pseudo_flat.setDetector(detector)
            pseudo_flat.info.setFilter(FilterLabel(physical=filter_name, band=band))
            pseudo_flat.metadata["FLATSRC"] = "PSEUDO"

            # Set to the central value.
            pseudo_flat.image.array[:, :] = central_values[i]

            # Adjust by the vignetting.
            transform = detector.getTransform(
                fromSys=lsst.afw.cameraGeom.PIXELS,
                toSys=lsst.afw.cameraGeom.FOCAL_PLANE,
            )

            nx = detector.getBBox().getWidth()
            ny = detector.getBBox().getHeight()

            x = np.repeat(np.arange(nx, dtype=np.float64), ny)
            y = np.tile(np.arange(ny, dtype=np.float64), nx)
            xy = np.vstack((x, y))
            x2, y2 = np.vsplit(transform.getMapping().applyForward(xy), 2)
            fprad = np.sqrt((x2.ravel()/1000.)**2. + (y2.ravel()/1000.)**2.)

            pseudo_flat.image.array[:, :] *= np.polyval(vignetting_coeffs, fprad).reshape(nx, ny).T
            pseudo_flat.image.array[:, :] = np.clip(pseudo_flat.image.array[:, :], 0.0, None)

            # Set BAD where the flat is < 0.15 (15%) and force to 0.
            bad = (pseudo_flat.image.array[:, :] < 0.15)
            pseudo_flat.mask.array[:, :][bad] |= pseudo_flat.mask.getPlaneBitMask("BAD")
            pseudo_flat.image.array[:, :][bad] = 0.0

            pseudo_flats_binned.append(
                visualize_bin_exp_task.run(inputExp=pseudo_flat, camera=camera).outputExp
            )

            if butler is not None:
                butler.put(
                    pseudo_flat,
                    "flat",
                    instrument="LSSTCam",
                    detector=detector.getId(),
                    physical_filter=filter_name,
                    run=output_collection,
                )

        mosaic = visualize_mosaic_exp_task.run(inputExps=pseudo_flats_binned, camera=camera).outputData

        low, high = np.nanpercentile(mosaic.array.ravel(), [1.0, 95.0])

        plt.clf()
        plt.imshow(mosaic.array, origin="lower", vmin=low, vmax=high)
        plt.colorbar()
        plt.title(f"{band} pseudo-flat")
        plt.savefig(f"pseudo_flat_mosaic_{band}_scale1.png")

        plt.clf()
        plt.imshow(mosaic.array, origin="lower", vmin=0.8, vmax=1.0)
        plt.colorbar()
        plt.title(f"{band} pseudo-flat")
        plt.savefig(f"pseudo_flat_mosaic_{band}_scale2.png")

    if butler is not None:
        print(f"Done outputting flats to {output_collection}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="make_lsstcam_pseudoflats",
        description="Make LSSTCam pseudoflats",
    )

    parser.add_argument("-o", "--do_output", action="store_true", help="Do output?")
    parser.add_argument("-b", "--repo", help="Butler repo", default="/repo/main")
    parser.add_argument("-d", "--rundate", help="Run date", default="20250414a")

    args = parser.parse_args()

    do_output = args.do_output
    repo = args.repo
    rundate = args.rundate

    if do_output:
        with Butler.from_config(repo, instrument="LSSTCam", writeable=True) as butler:
            output_collection = f"LSSTCam/calib/DM-50162/pseudoFlats/pseudoFlatGen.{rundate}/run"
            registered = butler.collections.register(output_collection)

            if not registered:
                raise RuntimeError(f"Output collection {output_collection} already registered.")

            write_pseudoflats(butler, output_collection)
    else:
        write_pseudoflats(None, None)
