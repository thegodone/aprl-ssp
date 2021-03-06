#!/usr/bin/env python


################################################################################
##
## validation_triple.py
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
import numpy as np
import matplotlib.pyplot as plt
from argparse import ArgumentParser, RawTextHelpFormatter

## -----------------------------------------------------------------------------

## Define command-line arguments

parser = ArgumentParser(description='''
============================================================
Perform validation described by aprl-carbontypes. Supercedes validation_atoms.R. Example usage:

$ python validation_triple.py -f apinene_MCMgroups_atomfulltable.csv -a apinene_commonatoms.csv -o apinene

''',formatter_class=RawTextHelpFormatter)

## Arguments

parser.add_argument('-f','--atomfulltable',type=str,
                    help='file generated by substructure_generate_fulltable.py; csv format')
parser.add_argument('-a','--atomcommon',type=str,
                    help='file generated by substructure_seach.py with common_atoms.csv patterns; csv format')
parser.add_argument('-o','--outputprefix',type=str,default='output',
                    help='output prefix')


if __name__=='__main__':

    ## -------------------------------------------------------------------------

    ## parse arguments

    # args = parser.parse_args('-f ssp/apinene_MCMgroups_atomfulltable.csv -a ssp/apinene_commonatoms.csv -o apinene'.split())
    args = parser.parse_args()

    filename = {
     'fulltable':args.atomfulltable,
     'atoms':args.atomcommon
        }

    prefix = args.outputprefix

    ## -------------------------------------------------------------------------

    ## read

    atype = lambda x: x[0].upper()
    
    atoms = pd.read_csv(filename['atoms']).set_index('compound')
    atoms.columns = atoms.columns.map(atype)

    fulltable = pd.read_csv(filename['fulltable'])
    fulltable['atype'] = (
        fulltable['type'].map(atype)
        .astype('category', categories=atoms.columns)
        )

    ## -------------------------------------------------------------------------

    ## atom completeness (atoms in matched groups per compound)
    
    ismatched = ~fulltable['match'].isnull() # this is critical

    atomsv = (
        fulltable
        .loc[ismatched, ['compound', 'atom', 'atype']]
        .drop_duplicates()
        .groupby(['compound', 'atype'])['atom'].count()
        .unstack(level='atype', fill_value=0)
        )

    ## -------------------------------------------------------------------------

    ## FG specificity (groups per atom)

    groupv = (
        fulltable.groupby(['compound', 'atom', 'atype'])['match'].count()
        .reset_index('atype')
        )

    ## relevel
    groupv['atype'] = pd.Categorical(groupv['atype'], categories=groupv['atype'].unique().categories)

    ## -------------------------------------------------------------------------

    ## carbon specificity

    carbonv = (
        fulltable.loc[fulltable['atype']=='C']
        .groupby(['compound', 'group', 'match'])['atom'].count()
        .reset_index('group')
        )

    carbonv['group'] = carbonv['group'].astype('category')

    ## -------------------------------------------------------------------------

    ## export

    # plt.ion()

    def plotframe(ax, mx):
        
        dx = 1 if mx < 5 else 2 # just a heuristic for tick interval
        ticks = np.arange(0, mx+1, dx)
        lim = np.array([0, mx]) + np.array([-1, 1]) * 0.04 * mx
        ##
        ax.set_autoscale_on(False)    
        ax.set_xlim(lim)
        ax.set_ylim(lim)
        #
        ax.set_xticks(ticks)
        ax.set_yticks(ticks)
        ##
        ax.plot(lim, lim)    

    def jitterplot(ax, x, y, seed = 1):

        np.random.seed(seed)
        jitter = np.random.normal(0, .05, [len(x), 2])

        if len(y.unique())==1:
            jitter[:,1] = 0

        ax.scatter(x.cat.codes + jitter[:,0], y + jitter[:,1])
        ax.set_xticks(np.arange(len(x.cat.categories)))
        ax.set_xticklabels(x.cat.categories)
        ax.set_yticks(np.arange(y.min(), y.max()+1))

    # atoms
    plt.close()
    fig = plt.figure()
    ncol = len(atomsv.columns)
    for i, x in enumerate(atomsv.columns):
        ax = fig.add_subplot(1, ncol, i+1)
        plotframe(ax, atoms[x].max())
        ax.scatter(atoms[x], atomsv.loc[atoms.index,x])
        ax.set_title(x)        
    fig.text(0.5, 0.04, 'True atom count by compound', ha='center')
    fig.text(0.04, 0.5, 'Matched atom count by compound', va='center', rotation='vertical')
    fig.set_size_inches((12,5))
    fig.savefig('{}_validation_completeness.pdf'.format(prefix))

    # groups
    plt.close()
    fig, ax = plt.subplots()
    jitterplot(ax, groupv['atype'], groupv['match'], 1)
    ax.set_xlabel('Element')
    ax.set_ylabel('Matched atom count per group')
    fig.savefig('{}_validation_specificity_FG.pdf'.format(prefix))

    # carbon
    plt.close()
    fig, ax = plt.subplots()
    jitterplot(ax, carbonv['group'], carbonv['atom'], 2)
    ax.set_xlabel('Group')
    ax.set_ylabel('Matched C per group')
    plt.xticks(rotation = 90)
    fig.subplots_adjust(bottom=0.35)
    fig.savefig('{}_validation_specificity_carbon.pdf'.format(prefix))

    ## -------------------------------------------------------------------------
