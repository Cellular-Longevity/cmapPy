import argparse
import os
import sys
import glob
import logging
import numpy
import pandas as pd

import cmapPy.pandasGEXpress.GCToo as GCToo
import cmapPy.pandasGEXpress.setup_GCToo_logger as setup_logger
import cmapPy.pandasGEXpress.subset_gctoo as subset_gctoo
import cmapPy.pandasGEXpress.concat as concat
import cmapPy.pandasGEXpress.parse as parse
import cmapPy.pandasGEXpress.write_gct as write_gct
import cmapPy.pandasGEXpress.write_gctx as write_gctx

# sys.exit('CONCAT NOT IMPLEMENTED FOR METHYLATION MATRICES YET')

__author__ = "David Tingley"
__email__ = "davidtingley2@gmail.com"

logger = logging.getLogger(setup_logger.LOGGER_NAME)


def merge(gctoos,how='inner'):
    """ merge gctoos.

    Args:
        gctoos (list of gctoo objects)
        how - only 'inner', expand to outer/left/right in future

        
    Return:
        inner merged (gctoo object)
    """

    idx = set(gctoos[0].row_metadata_df['id'].values)
    [idx.intersection_update(set(y.row_metadata_df['id'].values)) for y in gctoos[1:]]
    idx = list(idx)

    gsubList = []

    for g in gctoos:
        i, ridx, b = numpy.intersect1d(g.row_metadata_df['id'].values,idx,return_indices=True)
        
        gsub = subset_gctoo.subset_gctoo(g,ridx=ridx.tolist())
        # concat.do_reset_ids(gsub.row_metadata_df,gsub.meth_df,gsub.cov_df,'vert')
        gsubList.append(gsub)

    gctx = concat.hstack(gsubList)


    return gctx



def do_reset_ids(concatenated_meta_df, meth_df, cov_df, concat_direction):
    """ Reset ids in concatenated metadata and data dfs to unique integers and
    save the old ids in a metadata column.

    Note that the dataframes are modified in-place.

    Args:
        concatenated_meta_df (pandas df)
        meth_df (pandas df)
        cov_df (pandas df)
        concat_direction (string): 'horiz' or 'vert'

    Returns:
        None (dfs modified in-place)

    """
    if concat_direction == "horiz":

        # Make sure cids agree between data_df and concatenated_meta_df
        assert concatenated_meta_df.index.equals(meth_df.columns), (
            "cids in concatenated_meta_df do not agree with cids in data_df.")
        assert concatenated_meta_df.index.equals(cov_df.columns), (
            "cids in concatenated_meta_df do not agree with cids in data_df.")
        # Reset cids in concatenated_meta_df
        reset_ids_in_meta_df(concatenated_meta_df)

        # Replace cids in data_df with the new ones from concatenated_meta_df
        # (just an array of unique integers, zero-indexed)
        meth_df.columns = pd.Index(concatenated_meta_df.index.values)
        cov_df.columns = pd.Index(concatenated_meta_df.index.values)

    elif concat_direction == "vert":

        # Make sure rids agree between data_df and concatenated_meta_df
        assert concatenated_meta_df.index.equals(meth_df.index), (
            "rids in concatenated_meta_df do not agree with rids in data_df.")
        assert concatenated_meta_df.index.equals(cov_df.index), (
            "rids in concatenated_meta_df do not agree with rids in data_df.")
        # Reset rids in concatenated_meta_df
        reset_ids_in_meta_df(concatenated_meta_df)

        # Replace rids in data_df with the new ones from concatenated_meta_df
        # (just an array of unique integers, zero-indexed)
        meth_df.index = pd.Index(concatenated_meta_df.index.values)
        cov_df.index = pd.Index(concatenated_meta_df.index.values)

def reset_ids_in_meta_df(meta_df):
    """ Meta_df is modified inplace. """

    # Record original index name, and then change it so that the column that it
    # becomes will be appropriately named
    original_index_name = meta_df.index.name
    meta_df.index.name = "old_id"

    # Reset index
    meta_df.reset_index(inplace=True)

    # Change the index name back to what it was
    meta_df.index.name = original_index_name