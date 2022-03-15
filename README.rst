|install with bioconda|

.. |install with bioconda| image:: https://img.shields.io/badge/install%20with-bioconda-brightgreen.svg?style=flat-square
   :target: http://bioconda.github.io/recipes/cmappy/README.html
   
.. image:: https://badge.fury.io/py/cmapPy.svg
    :target: https://badge.fury.io/py/cmapPy

.. image:: https://travis-ci.org/cmap/cmapPy.svg?branch=master
    :target: https://travis-ci.org/cmap/cmapPy

.. image:: https://readthedocs.org/projects/cmappy/badge/?version=latest
    :target: http://cmappy.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

**cmapPy:** Tools for interacting with .gctx and .gct files, and other Connectivity Map resources
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
**Connectivity Map, Broad Institute of MIT and Harvard**

Documentation: `<https://clue.io/cmapPy/index.html>`_

For questions/problems, please add an issue (that includes code/files that reproduce your problem) to the repository. 

Installation (Python 3)
====================

.. code-block::

   conda create -n cmapPy3 python=3 scikit-learn scipy numpy seaborn matplotlib statsmodels pandas jupyter sympy h5py jupyter-lab

   git clone https://github.com/Cellular-Longevity/cmapPy

   cd cmapPy

   conda activate cmapPy3

   python setup.py install
   
   conda install -c conda-forge jupyterlab
   
   


Contributing
====================

We welcome contributors! For your pull requests, please include the following:

* Sample code/file that reproducibly causes the bug/issue
* Documented code providing fix
* Unit tests evaluating added/modified methods. 
 

Citation
====================

If you use cmapPy and/or GCTx for your research, please cite `Enache et al.`_

.. _Enache et al.: https://academic.oup.com/bioinformatics/article/35/8/1427/5094509
