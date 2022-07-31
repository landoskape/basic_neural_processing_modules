import numpy as np
from numba import njit
import sys
import re
import hashlib

def estimate_array_size(array=None, numel=None, input_shape=None, bitsize=64, units='GB'):
    '''
    Estimates the size of a hypothetical array based on shape or number of 
    elements and the bitsize
    RH 2021

    Args:
        numel (int): 
            number of elements in the array. If None, then 'input_shape'
            is used instead
        input_shape (tuple of ints):
            shape of array. Output of array.shape . Used if numel is None
        bitsize (int):
            bit size / width of the hypothetical data. eg:
                'float64'=64
                'float32'=32
                'uint8'=8
        units (str):
            units of the output. eg:
                'GB'=gigabytes
                'MB'=megabytes
                'KB'=kilobytes
                'B'=bytes
    
    Returns:
        size_estimate_in_bytes (int):
            size, in bytes, of hypothetical array. Doesn't include metadata,
            but for numpy arrays, this is usually very small (~128 bytes)

    '''
    if array is not None:
        input_shape = array.shape
        numel = np.product(input_shape)
        bitsize = array.dtype.itemsize*8
    elif numel is None:
        numel = np.product(input_shape)
    
    bytes_per_element = bitsize/8
    
    size_estimate_in_bytes = numel * bytes_per_element
    size_out = convert_size(size_estimate_in_bytes, units)
    return size_out


def get_vars(globals, size_thresh=0, var_type=None, return_vars_pref=False):
    '''
    Returns variable info that matches defined criteria.
    RH 2021

    Args:
        globals:
            `globals()` must be passed here
        size_thresh (scalar):
            Minimum size, in MB of variables you'd like returned
        var_type (type obj):
            Class type you'd like returned
        return_vars_pref (bool):
            Whether or not you'd like the outputs returned

    Returns:
        var_names (np.array of str):
            Names of variables sorted by size
        var_sizes (np.array of float64):
            Sizes of variables sorted by size
        var_types (np.array of type objects):
            Types of variables sorted by size

    Demo:
        var_names, var_sizes, var_types = get_vars(globals(), size_thresh=0.1, var_type=np.ndarray, return_vars_pref=True)
    '''
    var_info = []
    for ii, (name, var) in enumerate(globals.items()):
        var_info.append((name, sys.getsizeof(var), type(var)))

    var_names = np.array(var_info)[:,0]
    var_sizes = np.float64(np.array(var_info)[:,1])
    var_types = np.array(var_info)[:,2]

    sort_idx = np.flip(np.argsort(var_sizes))
    var_types = var_types[sort_idx]
    var_names = var_names[sort_idx]
    var_sizes = var_sizes[sort_idx]

    idx_toInclude = []
    for ii, (name, size, val_type) in enumerate(zip(var_names, var_sizes, var_types)):
        if var_type is not None:
            if size > size_thresh*1000000 and (val_type==var_type):
                idx_toInclude.append(ii)
                print(f'{name}, {size/1000000} MB, type: {val_type}')
        else:
            if size > size_thresh*1000000:
                idx_toInclude.append(ii)
                print(f'{name}, {size/1000000} MB, type: {val_type}')
    
    if return_vars_pref:
        return var_names[idx_toInclude], var_sizes[idx_toInclude], var_types[idx_toInclude]


def recursive_for_loop(final_ndim, func, data, loop_depth=0):
# def recursive_for_loop(n_loops, func, data, loop_depth=0, **kwargs):
    '''
    A cute recursive function for running an operation (func) on
     the last n dimensions (final_ndim) of a high dimensional
     array.
    RH 2021
    '''
    if data.ndim > final_ndim:
        output = [ [] for _ in range(len(data))]
        for ii, i_data in enumerate(data):
#             output[ii] = recursive_for_loop(n_loops, func, i_data, loop_depth=loop_depth+1, **kwargs)
            output[ii] = recursive_for_loop(final_ndim, func, i_data, loop_depth=loop_depth+1)
#     return func(data, **kwargs)
    else:
        return func(data)
    return output


def get_nums_from_str(str_in, dtype_out=np.float64):
    """
    Returns a list of numbers from a string.
    Numbers can be negative and decimals.
    RH 2022

    Args:
        str_in (str):
            String to be parsed.
            Should contain numbers separated by spaces, commas,
             letters, or most other characters.
        dtype_out (type obj):
            dtype of output.

    Returns:
        nums (np.array):
            List of numbers found in the string.

    """
    return np.array([float(i) for i in re.findall(r'\-?\d+\.?\d*', str_in)], dtype=dtype_out)


def hash_file(path, type_hash='MD5', buffer_size=65536):
    """
    Based on: https://stackoverflow.com/questions/22058048/hashing-a-file-in-python
    RH 2022

    Args:
        path (str):
            Path to file to be hashed.
        type_hash (str):
            Type of hash to use. Can be:
                'MD5'
                'SHA1'
                'SHA256'
                'SHA512'
        buffer_size (int):
            Buffer size for reading file.
            65536 corresponds to 64KB.

    Returns:
        hash (str):
            Hash of file.
    """

    if type_hash == 'MD5':
        hasher = hashlib.md5()
    elif type_hash == 'SHA1':
        hasher = hashlib.sha1()
    elif type_hash == 'SHA256':
        hasher = hashlib.sha256()
    elif type_hash == 'SHA512':
        hasher = hashlib.sha512()
    else:
        raise ValueError(f'{type_hash} is not a valid hash type.')

    with open(path, 'rb') as f:
        while True:
            data = f.read(buffer_size)
            if not data:
                break
            hasher.update(data)

    hash = hasher.hexdigest()
        
    return hash



#########################################################
############ INTRA-MODULE HELPER FUNCTIONS ##############
#########################################################

def convert_size(size, return_size='GB'):
    """
    Convert size to GB, MB, KB, from B.
    RH 2021

    Args:
        size (int or float):
            Size in bytes.
        return_size (str):
            Size unit to return.
            Options: 'TB', 'GB', 'MB', or 'KB'
        
    Returns:
        out_size (float):
            Size in specified unit.      
    """

    if return_size == 'TB':
        out_size = size / 1000000000000
    elif return_size == 'GB':
        out_size = size / 1000000000
    elif return_size == 'MB':
        out_size = size / 1000000
    elif return_size == 'KB':
        out_size = size / 1000
    elif return_size == 'B':
        out_size = size / 1

    return out_size
