from .convert_qe_curve import convert_qe_curve

amp_name_map = {'AMP01': 'C00', 'AMP02': 'C01', 'AMP03': 'C02', 'AMP04': 'C03', 'AMP05': 'C04',
                'AMP06': 'C05', 'AMP07': 'C06', 'AMP08': 'C07', 'AMP09': 'C10', 'AMP10': 'C11',
                'AMP11': 'C12', 'AMP12': 'C13', 'AMP13': 'C14', 'AMP14': 'C15', 'AMP15': 'C16',
                'AMP16': 'C17'}

filename = '/project/bxin/cam_as_built/R10/ITL-3800C-207_QE.fits'
with open(filename,'rb') as fh:
    raft_name=pickle.load(f)
    res=pickle.load(f)
    cd_list=pickle.load(f)
    file_list=pickle.load(f)
    fw=pickle.load(f)
    gains=pickle.load(f)


