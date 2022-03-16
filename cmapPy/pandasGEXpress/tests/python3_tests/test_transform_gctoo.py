
import unittest
import logging
import pandas
import cmapPy.pandasGEXpress.setup_GCToo_logger as setup_logger
import cmapPy.pandasGEXpress.GCToo as GCToo
import cmapPy.pandasGEXpress.transform_gctoo as tg

logger = logging.getLogger(setup_logger.LOGGER_NAME)


class TestSubset(unittest.TestCase):
    def test_transpose(self):
        meth_df = pandas.DataFrame({"a":range(2,5), "b":range(7,10)})
        logger.debug("happy path - meth_df:\n{}".format(meth_df))

        row_metadata_df = pandas.DataFrame({"rm1":range(3)}, index=meth_df.index)
        logger.debug("row_metadata_df:\n{}".format(row_metadata_df))

        col_metadata_df = pandas.DataFrame({"cm1":range(2), "cm2":range(3,5)}, index=meth_df.columns)
        logger.debug("col_metadata_df:\n{}".format(col_metadata_df))

        my_gctoo = GCToo.GCToo(meth_df, meth_df, row_metadata_df=row_metadata_df, col_metadata_df=col_metadata_df)
        logger.debug("my_gctoo:\n{}".format(my_gctoo))

        r = tg.transpose(my_gctoo)
        logger.debug("result r:\n{}".format(r))

        logger.debug("r.meth_df:\n{}".format(r.meth_df))
        self.assertTrue(meth_df.equals(r.meth_df.T))

        logger.debug("r.row_metadata_df:\n{}".format(row_metadata_df))
        self.assertTrue(col_metadata_df.equals(r.row_metadata_df))

        logger.debug("r.col_metadata_df:\n{}".format(r.col_metadata_df))
        self.assertTrue(row_metadata_df.equals(r.col_metadata_df))


if __name__ == '__main__':
    setup_logger.setup(verbose=True)
    unittest.main()
