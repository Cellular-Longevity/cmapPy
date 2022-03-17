import h5py

__author__ = "David Tingley"
__email__ = "davidtingley2@gmail.com"

def view(filename,printing=True,filter=None):
    '''
    cmapPy equivalent to h5ls
    Input
        filename - name of HDF5 file
        printing - boolean to print list out
        filter - substring to filter on (i.e. "DATA" or "META")
    Output
        nodeNames - names of H5 nodes returned
    '''
    h5ls = H5ls()
    # this will now visit all objects inside the hdf5 file and store datasets in h5ls.names
    df = h5py.File(filename,'r')
    df.visititems(h5ls) 
    df.close()
    if printing:
        [print(name) for name in h5ls.names]

    if filter is not None:
        return [name for name in h5ls.names if filter in name]
    else:
        return h5ls.names

class H5ls:
    def __init__(self):
        # Store an empty list for dataset names
        self.names = []

    def __call__(self, name, h5obj):
        if hasattr(h5obj,'dtype') and not name in self.names:
            self.names += [name]

