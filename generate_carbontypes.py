#!/usr/bin/env python

################################################################################
##
## generate_carbontypes.py
## Author: Satoshi Takahama (satoshi.takahama@epfl.ch)
## Jul. 2017
##
## -----------------------------------------------------------------------------
##
## This file is part of APRL-SSP
##
## APRL-SSP is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## APRL-SSP is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with APRL-SSP.  If not, see <http://www.gnu.org/licenses/>.
##
################################################################################

import os
import re
import pandas as pd
from argparse import ArgumentParser, RawTextHelpFormatter

## -----------------------------------------------------------------------------

## Define command-line arguments

parser = ArgumentParser(description='''
============================================================
Generate functional group and carbon type matrices (from aprl-carbontypes; adapted to python). Example usage:

$ python generate_carbontypes.py -i apinene_MCMgroups_atomfulltable.csv -o apinene

''',formatter_class=RawTextHelpFormatter)

## Arguments

parser.add_argument('-i','--inputfile',type=str,
                    help='file generated by substructure_generate_fulltable.py; csv format')
parser.add_argument('-o','--outputprefix',type=str,default='output',
                    help='output prefix')

## -----------------------------------------------------------------------------

if __name__=='__main__':

    ## parse arguments

    args = parser.parse_args()
    filename = args.inputfile
    prefix = args.outputprefix
    
    ## -------------------------------------------------------------------------

    ## read file

    fulltable = pd.read_csv(filename)

    ## -------------------------------------------------------------------------

    ## x is a pandas Series

    label_ctype = lambda x: '({})'.format(', '.join(x.astype(str)))

    ## -------------------------------------------------------------------------

    ## to be used for creation of Y and Theta matrix

    wf = (
        fulltable
        .loc[fulltable['type'].str.contains('^C|c')]
        .groupby(['compound','atom','type','group'])['match'].count()
        .unstack(level='group', fill_value=0)
        )

    fgvars = wf.columns
    wf['ctype'] = wf.apply(label_ctype, axis=1)

    ## -------------------------------------------------------------------------

    xmat = (
        fulltable[['compound', 'match', 'group']].drop_duplicates()
        .groupby(['compound', 'group'])['match'].count()
        .unstack(level='group', fill_value=0)
        )

    ymat = (
        wf.reset_index()[['compound', 'atom', 'ctype']]
        .groupby(['compound', 'ctype'])['atom'].count()
        .unstack(level='ctype', fill_value=0)
        )

    theta = wf[fgvars].drop_duplicates()
    theta.index = theta.apply(label_ctype, axis=1)
    theta.index.name = 'ctype'

    ## -------------------------------------------------------------------------

    ## export

    xmat.to_csv('{}_carbontypes_X.csv'.format(prefix))
    ymat.to_csv('{}_carbontypes_Y.csv'.format(prefix))
    theta.to_csv('{}_carbontypes_Theta.csv'.format(prefix))
