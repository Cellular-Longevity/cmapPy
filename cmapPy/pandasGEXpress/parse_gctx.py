import logging
import cmapPy.pandasGEXpress.setup_GCToo_logger as setup_logger
import os
import numpy as np
import pandas as pd
import h5py
import cmapPy.pandasGEXpress.GCToo as GCToo

__author__ = "Oana Enache"
__email__ = "oana@broadinstitute.org"

# instantiate logger
logger = logging.getLogger(setup_logger.LOGGER_NAME)

version_node = "version"
rid_node = "/0/META/ROW/id"
cid_node = "/0/META/COL/id"
data_node = "/0/DATA/0/matrix"
row_meta_group_node = "/0/META/ROW"
col_meta_group_node = "/0/META/COL"


def parse(gctx_file_path, convert_neg_666=False, rid=None, cid=None,
          ridx=None, cidx=None, row_meta_only=False, col_meta_only=False, make_multiindex=False,
          sort_col_meta = True, sort_row_meta = True):
    """
    Primary method of script. Reads in path to a gctx file and parses into GCToo object.

    Input:
        Mandatory:
        - gctx_file_path (str): full path to gctx file you want to parse.

        Optional:
        - convert_neg_666 (bool): whether to convert -666 values to numpy.nan or not
            (see Note below for more details on this). Default = False.
        - rid (list of strings): list of row ids to specifically keep from gctx. Default=None.
        - cid (list of strings): list of col ids to specifically keep from gctx. Default=None.
        - ridx (list of integers): only read the rows corresponding to this
            list of integer ids. Default=None.
        - cidx (list of integers): only read the columns corresponding to this
            list of integer ids. Default=None.
        - row_meta_only (bool): Whether to load data + metadata (if False), or just row metadata (if True)
            as pandas DataFrame
        - col_meta_only (bool): Whether to load data + metadata (if False), or just col metadata (if True)
            as pandas DataFrame
        - make_multiindex (bool): whether to create a multi-index df combining
            the 3 component dfs
        - sort_col_meta (bool) : whether to sort the column metadata by indexes. Default = True
        - sort_row_meta (bool) : whether to sort the row metadata by indexes. Default = True
    Output:
        - myGCToo (GCToo): A GCToo instance containing content of parsed gctx file. Note: if meta_only = True,
            this will be a GCToo instance where the data_df is empty, i.e. data_df = pd.DataFrame(index=rids,
            columns = cids)

    Note: why does convert_neg_666 exist?
        - In CMap--for somewhat obscure historical reasons--we use "-666" as our null value
        for metadata. However (so that users can take full advantage of pandas' methods,
        including those for filtering nan's etc) we provide the option of converting these
        into numpy.NaN values, the pandas default.
    """
    full_path = os.path.expanduser(gctx_file_path)

    # Verify that the  path exists
    if not os.path.exists(full_path):
        err_msg = "The given path to the gctx file cannot be found. full_path: {}"
        logger.error(err_msg.format(full_path))
        raise Exception(err_msg.format(full_path))
    logger.info("Reading GCTX: {}".format(full_path))

    # open file
    gctx_file = h5py.File(full_path, "r")

    if row_meta_only:
        # read in row metadata
        row_dset = gctx_file[row_meta_group_node]
        row_meta = parse_metadata_df("row", row_dset, convert_neg_666)

        # validate optional input ids & get indexes to subset by
        (sorted_ridx, sorted_cidx) = check_and_order_id_inputs(rid, ridx, cid, cidx, row_meta, None, 
                                                                sort_row_meta = True, sort_col_meta = True)

        gctx_file.close()

        # subset if specified, then return
        row_meta = row_meta.iloc[sorted_ridx]

        if not sort_row_meta:
            (unsorted_ridx, _) = check_and_order_id_inputs(rid, ridx, cid, cidx, row_meta, None,
                                                      sort_row_meta, sort_row_meta)
            row_meta = row_meta.iloc[unsorted_ridx]

        return row_meta
    elif col_meta_only:
        # read in col metadata
        col_dset = gctx_file[col_meta_group_node]
        col_meta = parse_metadata_df("col", col_dset, convert_neg_666)

        # validate optional input ids & get indexes to subset by
        (sorted_ridx, sorted_cidx) = check_and_order_id_inputs(rid, ridx, cid, cidx, None, 
                                                            col_meta, sort_row_meta = True, sort_col_meta = True)

        gctx_file.close()

        # subset if specified, then return
        col_meta = col_meta.iloc[sorted_cidx]

        if not sort_col_meta:
            (_, unsorted_cidx) = check_and_order_id_inputs(rid, ridx, cid, cidx, None, col_meta, 
                                                        sort_row_meta, sort_col_meta)
            col_meta = col_meta.iloc[unsorted_cidx, :]

        return col_meta
    else:
        # read in row metadata
        row_dset = gctx_file[row_meta_group_node]
        row_meta = parse_metadata_df("row", row_dset, convert_neg_666)

        # read in col metadata
        col_dset = gctx_file[col_meta_group_node]
        col_meta = parse_metadata_df("col", col_dset, convert_neg_666)

        # validate optional input ids & get indexes to subset by
        (sorted_ridx, sorted_cidx) = check_and_order_id_inputs(rid, ridx, cid, cidx, row_meta, col_meta, 
                                                                sort_row_meta = True, sort_col_meta = True)

        data_dset = gctx_file[data_node]
        data_df_list = parse_data_df(data_dset, sorted_ridx, sorted_cidx, row_meta, col_meta)
        meth_df = data_df_list[0]
        cov_df = data_df_list[1]
        assert np.nanmax(meth_df) <= 100. , 'it looks like methylation is >100% ?'
        assert all(x.is_integer() for x in cov_df.fillna(0).stack().values), 'coverage matrix failed integer check'

        # (if subsetting) subset metadata
        row_meta = row_meta.iloc[sorted_ridx]
        col_meta = col_meta.iloc[sorted_cidx]

        if not sort_col_meta:
            ## in the subsetted and re-indexed dataframe get where new indexes lie
            (_, unsorted_cidx) = check_and_order_id_inputs(rid, ridx, cid, cidx, row_meta, col_meta, 
                                                        sort_row_meta, sort_col_meta)
            
            meth_df = meth_df.iloc[:,unsorted_cidx]
            cov_df = cov_df.iloc[:,unsorted_cidx]
            col_meta = col_meta.iloc[unsorted_cidx,:]
        
        if not sort_row_meta:
            (unsorted_ridx, _) = check_and_order_id_inputs(rid, ridx, cid, cidx, row_meta, col_meta,
                                                      sort_row_meta, sort_row_meta)
            meth_df = meth_df.iloc[unsorted_ridx,:]
            cov_df = cov_df.iloc[unsorted_ridx,:]
            row_meta = row_meta.iloc[unsorted_ridx,:]

        # get version
        my_version = gctx_file.attrs[version_node]
        if type(my_version) == np.ndarray:
            my_version = my_version[0]

        gctx_file.close()

        # make GCToo instance
        my_gctoo = GCToo.GCToo(meth_df=meth_df, cov_df=cov_df, row_metadata_df=row_meta, col_metadata_df=col_meta,
                               src=full_path, version=my_version, make_multiindex=make_multiindex)
        return my_gctoo


def check_and_order_id_inputs(rid, ridx, cid, cidx, row_meta_df, col_meta_df, sort_row_meta, sort_col_meta):
    """
    Makes sure that (if entered) id inputs entered are of one type (string id or index)
    Input:
        - rid (list or None): if not None, a list of rids
        - ridx (list or None): if not None, a list of indexes
        - cid (list or None): if not None, a list of cids
        - cidx (list or None): if not None, a list of indexes
        - sort_row_meta (bool): boolean indicating whether to return sorted row indexes
        - sort_col_meta (bool): boolean indicating whether to return sorted column indexes
    Output:
        - a tuple of the ordered ridx and cidx
    """
    (row_type, row_ids) = check_id_idx_exclusivity(rid, ridx)
    (col_type, col_ids) = check_id_idx_exclusivity(cid, cidx)


    row_ids = check_and_convert_ids(row_type, row_ids, row_meta_df, sort_col_meta)
    ordered_ridx = get_ordered_idx(row_type, row_ids, row_meta_df, sort_row_meta)

    col_ids = check_and_convert_ids(col_type, col_ids, col_meta_df, sort_col_meta)
    ordered_cidx = get_ordered_idx(col_type, col_ids, col_meta_df, sort_col_meta)
    return (ordered_ridx, ordered_cidx)


def check_id_idx_exclusivity(id, idx):
    """
    Makes sure user didn't provide both ids and idx values to subset by.

    Input:
        - id (list or None): if not None, a list of string id names
        - idx (list or None): if not None, a list of integer id indexes

    Output:
        - a tuple: first element is subset type, second is subset content
    """
    if (id is not None and idx is not None):
        msg = ("'id' and 'idx' fields can't both not be None," +
               " please specify subset in only one of these fields")
        logger.error(msg)
        raise Exception("parse_gctx.check_id_idx_exclusivity: " + msg)
    elif id is not None:
        return ("id", id)
    elif idx is not None:
        return ("idx", idx)
    else:
        return (None, [])


def check_and_convert_ids(id_type, id_list, meta_df, sort_id):
    if meta_df is not None:
        if id_type == "id":
            id_list = convert_ids_to_meta_type(id_list, meta_df)
            check_id_validity(id_list, meta_df)
        else:
            check_idx_validity(id_list, meta_df, sort_id)
        return id_list
    else:
        return None


def check_id_validity(id_list, meta_df):
    id_set = set(id_list)
    meta_set = set(meta_df.index)
    mismatch_ids = id_set - meta_set
    if len(mismatch_ids) > 0:
        msg = "some of the ids being used to subset the data are not present in the metadata for the file being parsed - mismatch_ids:  {}".format(
            mismatch_ids)
        logger.error(msg)
        raise Exception("parse_gctx check_id_validity " + msg)


def check_idx_validity(id_list, meta_df, sort_id):
    if sort_id:
        N = meta_df.shape[0]
        out_of_range_ids = [my_id for my_id in id_list if my_id < 0 or my_id >= N]
        if len(out_of_range_ids):
            msg = "some of indexes being used to subset the data are not valid max N:  {}  out_of_range_ids:  {}".format(N,
                                                                                                     out_of_range_ids)
            logger.error(msg)
            raise Exception("parse_gctx check_idx_validity " + msg)


def convert_ids_to_meta_type(id_list, meta_df):
    try:
        return pd.Series(id_list).astype(meta_df.index.dtype).values
    except ValueError as ve:
        id_list_types = set([type(x) for x in id_list])
        msg = "The type of the id_list (rid or cid) being used to subset the data is not compatible with the metadata id's in the file.  Types found - meta_df.index.dtype:  {}  id_list_types:  {}".format(
            meta_df.index.dtype, id_list_types)
        logger.error(msg)
        raise Exception("parse_gctx check_if_ids_in_meta " + msg + "  ValueError ve:  {}".format(ve))


def get_ordered_idx(id_type, id_list, meta_df, sort_idx):
    """
    Gets index values corresponding to ids to subset and orders them.
    Input:
        - id_type (str): either "id", "idx" or None
        - id_list (list): either a list of indexes or id names
        - meta_df (dataframe): dataframe 
        - sort_idx (bool): boolean indicating whether to return sorted indexes or not
    Output:
        - a sorted list of indexes to subset a dimension by
    """
    if meta_df is not None:
        if id_type is None:
            id_list = range(0, len(list(meta_df.index)))
        elif id_type == "id":
            lookup = {x: i for (i,x) in enumerate(meta_df.index)}
            id_list = [lookup[str(i)] for i in id_list]
        if not sort_idx:
            return [sorted(id_list).index(i) for i in id_list] 
        return sorted(id_list)
    else:
        return None


def parse_metadata_df(dim, meta_group, convert_neg_666):
    """
    Reads in all metadata from .gctx file to pandas DataFrame
    with proper GCToo specifications.
    Input:
        - dim (str): Dimension of metadata; either "row" or "column"
        - meta_group (HDF5 group): Group from which to read metadata values
        - convert_neg_666 (bool): whether to convert "-666" values to np.nan or not
    Output:
        - meta_df (pandas DataFrame): data frame corresponding to metadata fields
            of dimension specified.
    """
    # read values from hdf5 & make a DataFrame
    header_values = {}
    array_index = 0
    for k in meta_group.keys():
        curr_dset = meta_group[k]
        temp_array = np.empty(curr_dset.shape, dtype=curr_dset.dtype)
        curr_dset.read_direct(temp_array)
        # convert all values to str in temp_array so that
        # to_numeric works consistently with gct and gct_x parser
        temp_array = temp_array.astype('str')
        header_values[str(k)] = temp_array
        array_index = array_index + 1


    meta_df = pd.DataFrame.from_dict(header_values)

    # save the ids for later use in the index; we do not want to convert them to
    # numeric
    ids = meta_df["id"].copy()
    del meta_df["id"]

    # Convert metadata to numeric if possible, after converting everything to string first
    # Note: This conversion first to string is to ensure consistent behavior between
    #    the gctx and gct parser (which by default reads the entire text file into a string)
    meta_df = meta_df.apply(lambda x: pd.to_numeric(x, errors="ignore"))

    meta_df.set_index(pd.Index(ids, dtype=str), inplace=True)

    # Replace -666 and -666.0 with NaN; also replace "-666" if convert_neg_666 is True
    meta_df = replace_666(meta_df, convert_neg_666)

    # set index and columns appropriately
    set_metadata_index_and_column_names(dim, meta_df)
    return meta_df


def replace_666(meta_df, convert_neg_666):
    """ Replace -666, -666.0, and optionally "-666".
    Args:
        meta_df (pandas df):
        convert_neg_666 (bool):
    Returns:
        out_df (pandas df): updated meta_df
    """
    if convert_neg_666:
        out_df = meta_df.replace([-666, "-666", -666.0], np.nan)
    else:
        out_df = meta_df.replace([-666, -666.0], "-666")
    return out_df


def set_metadata_index_and_column_names(dim, meta_df):
    """
    Sets index and column names to GCTX convention.
    Input:
        - dim (str): Dimension of metadata to read. Must be either "row" or "col"
        - meta_df (pandas.DataFrame): data frame corresponding to metadata fields
            of dimension specified.
    Output:
        None
    """
    if dim == "row":
        meta_df.index.name = "rid"
        meta_df.columns.name = "rhd"
    elif dim == "col":
        meta_df.index.name = "cid"
        meta_df.columns.name = "chd"


def parse_data_df(data_dset, ridx, cidx, row_meta, col_meta):
    """
    Parses in data_df from hdf5, subsetting if specified.

    Input:
        -data_dset (h5py dset): HDF5 dataset from which to read data_df
        -ridx (list): list of indexes to subset from data_df
            (may be all of them if no subsetting)
        -cidx (list): list of indexes to subset from data_df
            (may be all of them if no subsetting)
        -row_meta (pandas DataFrame): the parsed in row metadata
        -col_meta (pandas DataFrame): the parsed in col metadata
    """
    total_rows = len(row_meta.index)
    total_cols = len(col_meta.index)
    if len(ridx) == total_rows and len(cidx) == total_cols:  # no subset
        data_array = np.empty(data_dset.shape, dtype=np.float32)
        data_dset.read_direct(data_array)
        if data_array.ndim > 2:
            meth_array = data_array[0, :, :].transpose()
            cov_array = data_array[1, :, :].transpose()
        else:
            meth_array = data_array[:, :].transpose()
            cov_array = np.empty(data_array.shape, dtype=np.float32).transpose()
    else:
        # We can only subset on a single dimension at a time with h5py.
        # For the first dimension to use, pick the one that minimizes
        # the size of the intermediate array.
        row_first_count = total_cols * len(ridx)
        col_first_count = total_rows * len(cidx)
        if row_first_count < col_first_count:
            if data_dset.ndim > 2:
                first_subset_meth = data_dset[0, :, ridx].astype(np.float32)
                first_subset_cov = data_dset[1, :, ridx].astype(np.float32)
            else:
                first_subset_meth = data_dset[:, ridx].astype(np.float32)
                first_subset_cov = np.empty(data_dset[:, ridx].shape, dtype=np.float32)
            meth_array = first_subset_meth[cidx, :].transpose()
            cov_array = first_subset_cov[cidx, :].transpose()
        else:
            if data_dset.ndim > 2:
                first_subset_meth = data_dset[0, cidx, :].astype(np.float32)
                first_subset_cov = data_dset[1, cidx, :].astype(np.float32)
            else:
                first_subset_meth = data_dset[cidx, :].astype(np.float32)
                first_subset_cov = np.empty(data_dset[cidx, :].shape, dtype=np.float32)
            meth_array = first_subset_meth[:, ridx].transpose()
            cov_array = first_subset_cov[:, ridx].transpose()

    # make DataFrame instance
    meth_df = pd.DataFrame(meth_array, index=row_meta.index[ridx], columns=col_meta.index[cidx])
    cov_df = pd.DataFrame(cov_array, index=row_meta.index[ridx], columns=col_meta.index[cidx])

    return [meth_df, cov_df]


def get_column_metadata(gctx_file_path, convert_neg_666=True):
    """
    Opens .gctx file and returns only column metadata

    Input:
        Mandatory:
        - gctx_file_path (str): full path to gctx file you want to parse.

        Optional:
        - convert_neg_666 (bool): whether to convert -666 values to num

    Output:
        - col_meta (pandas DataFrame): a DataFrame of all column metadata values.
    """
    full_path = os.path.expanduser(gctx_file_path)
    # open file
    gctx_file = h5py.File(full_path, "r")
    col_dset = gctx_file[col_meta_group_node]
    col_meta = parse_metadata_df("col", col_dset, convert_neg_666)
    gctx_file.close()
    return col_meta


def get_row_metadata(gctx_file_path, convert_neg_666=True):
    """
    Opens .gctx file and returns only row metadata

    Input:
        Mandatory:
        - gctx_file_path (str): full path to gctx file you want to parse.

        Optional:
        - convert_neg_666 (bool): whether to convert -666 values to num

    Output:
        - row_meta (pandas DataFrame): a DataFrame of all row metadata values.
    """
    full_path = os.path.expanduser(gctx_file_path)
    # open file
    gctx_file = h5py.File(full_path, "r")
    row_dset = gctx_file[row_meta_group_node]
    row_meta = parse_metadata_df("row", row_dset, convert_neg_666)
    gctx_file.close()
    return row_meta
