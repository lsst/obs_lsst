import pickle
import argparse
import os
import glob

from lsst.obs.lsst.lsstCamMapper import LsstCamMapper
mapper = LsstCamMapper()
cam = mapper.camera

parser = argparse.ArgumentParser(description='Update raft description.')
parser.add_argument('picklefile', type=str,
                    help='Path to pickle file to use')
parser.add_argument('raft_name', type=str,
                    help='Name of raft to update')
parser.add_argument('sensor_type', type=str,
                    help='Either E2V or ITL')
parser.add_argument('out_file', type=str,
                    help='Name of file to write to')

args = parser.parse_args()

print(args.raft_name, '----------------')
installed_raft = args.raft_name
with open(args.picklefile, mode='rb') as fh:
    raft = pickle.load(fh)
    noise = pickle.load(fh)
    ccd_list = pickle.load(fh)
    file_list = pickle.load(fh)
    fw = pickle.load(fh)
    gains = pickle.load(fh)

sensors = ['S00', 'S01', 'S02', 'S10', 'S11', 'S12', 'S20', 'S21', 'S22']
amps = ['C10', 'C11', 'C12', 'C13', 'C14', 'C15', 'C16', 'C17',
        'C07', 'C06', 'C05', 'C04', 'C03', 'C02', 'C01', 'C00']

file_tmpl = '''%s :
  detectorType : %s
  raftSerial : %s

  ccdSerials :
%s

  geometryWithinRaft:
%s

  amplifiers :
%s'''

serial_tmpl = '    %s : %s'
geom_tmpl = '''    %s : {
      offset : [0.0, 0.0],
      yaw : 0.0,
    }'''
amps_tmpl = '''    %s :
%s'''
amp_tmpl = '      %s : { gain : %f, readNoise : %f, saturation : %f }'
serialstrs = []
geomstrs = []
sensorstrs = []
for i, sensor in enumerate(sensors):
    serial = None
    for f in ccd_list:
        if sensor in f:
            serial = f[0]
    ampstrs = []
    for j, amp in enumerate(amps):
        ampstrs.append(amp_tmpl%(amp, gains[serial][j], noise[serial][j], fw[serial][j]))

    serialstrs.append(serial_tmpl%(sensor, serial))
    geomstrs.append(geom_tmpl%(sensor))
    sensorstrs.append(amps_tmpl%(sensor, "\n".join(ampstrs)))

with open(args.out_file, 'w') as fh:
    fh.write(file_tmpl%(installed_raft, args.sensor_type, raft, "\n".join(
        serialstrs), "\n".join(geomstrs), "\n".join(sensorstrs))+"\n")


# deal with the QE curves nows, we need to copy them over from ts8 camera
# Based on instructions at https://jira.lsstcorp.org/browse/DM-22824

# Make directories for the curves to go into:
for i in range(len(sensors)):
    my_folder = f"{os.environ['OBS_LSST_DATA_DIR']}/lsstcam/qe_curves/\
{installed_raft.lower()}_{sensors[i].lower()}"
    if not os.path.exists(my_folder):
        # print('creating %s'%my_folder)
        os.makedirs(my_folder)

rtmname = raft[-7:]

# Now we can edit the files to update the metadata.
# There are only a few things that need to be updated:
# 1. INSTRUME: TS8 --> LSSTCAM
# 2. DETECTOR: This needs to be set to the corresponding
#    integer in the list above.
# 3. CALIB_ID: raftName needs to be changed from the RTM number to
#    the actual raft name. detector, ccd and ccdnum need to be set to
#    the same thing as DETECTOR.

for i in range(len(sensors)):
    srcDir = f"{os.environ['OBS_LSST_DATA_DIR']}/ts8/qe_curve/{rtmname.lower()}_{sensors[i].lower()}"
    destDir = f"{os.environ['OBS_LSST_DATA_DIR']}/lsstcam/qe_curve/\
{installed_raft.lower()}_{sensors[i].lower()}"
    srcList = glob.glob('%s/*'%srcDir)
    assert len(srcList) == 1
    srcName = srcList[0]
    destName = os.path.join(destDir, os.path.split(srcName)[-1])
    rid = open(srcName, 'r')
    wid = open(destName, 'w')
    detectorId = cam[f'{installed_raft}_{sensors[i]}'].getId()
    for line in rid:
        if 'TS8' in line:
            wid.write('# - {INSTRUME: LSSTCAM}\n')
        elif 'DETECTOR' in line:
            wid.write('# - {DETECTOR: %d}\n'%detectorId)
        elif 'CALIB_ID' in line:
            oldRaftName = line.split(' ')[3][1:]
            oldDector = line.split(' ')[5]
            oldCcd = line.split(' ')[7]
            oldCcdnum = line.split(' ')[8]
            line = line.replace(oldRaftName, 'raftName=%s'%installed_raft)
            line = line.replace(oldDector, 'detector=%d'%detectorId)
            line = line.replace(oldCcd, 'ccd=%d'%detectorId)
            line = line.replace(oldCcdnum, 'ccdnum=%d'%detectorId)
            wid.write(line)
        else:
            wid.write(line)
    rid.close()
    wid.close()
print('DONE')
