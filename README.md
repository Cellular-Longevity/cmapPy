#cmapPy: modified by Loyal

Install this development version in a conda environment
```
# here I use mamba for better env solving
mamba create -n cmappy -c conda-forge scikit-learn scipy numpy seaborn matplotlib statsmodels pandas h5py boto3
conda activate cmappy

git clone https://github.com/Cellular-Longevity/cmapPy
cd cmapPy
pip install -e .

```

## Quickstart
A more detailed tutorial will be developed soon! Here's an example of how to get data from S3 and read it in using the cmapPy pakcage
```
import boto3
import cmapPy.pandasGEXpress.parse_gctx as parse_gctx

# requires a local ~/.aws/credentials file w/ permission
session = boto3.Session(profile_name='default')
s3_client = session.client('s3')

s3_client.download_file(Bucket="bioinformatics-loyal", 
Key="processed_methylation_data/HEALTHSPAN/novogene_pilot_RRBS/matrices_processed/methylation_filtered.gctx", 
Filename="methylation_filtered.gctx")

# parse the gctx
mgct = parse_gctx.parse('methylation_filtered.gctx')

# methylation matrix lives in meth_df
mgct.meth_df.shape

# coverage matrix lives in cov_df
mgct.cov_df.shape

# colummn and row metadata
mgct.col_metadata_df
mgct.row_metadata_df.iloc[1:5,:]


```

## Citation
If you use cmapPy and/or GCTx for your research, please cite Enache et al. https://academic.oup.com/bioinformatics/article/35/8/1427/5094509
