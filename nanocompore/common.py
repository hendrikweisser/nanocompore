# -*- coding: utf-8 -*-

#~~~~~~~~~~~~~~IMPORTS~~~~~~~~~~~~~~#
# Standard library imports
import os
from tqdm import tqdm, tqdm_notebook

#~~~~~~~~~~~~~~CUSTOM EXCEPTION CLASS~~~~~~~~~~~~~~#
class NanocomporeError (Exception):
    """ Basic exception class for nanocompore module """
    pass

#~~~~~~~~~~~~~~FUNCTIONS~~~~~~~~~~~~~~#
def mkdir (fn):
    """Create directory recursivelly. Raise IO error if path exist or if error at creation
    """
    if os.path.isdir (fn):
        raise NanocomporeError ("The output folder specified already exists")
    else:
        try:
            os.makedirs (fn)
        except:
            raise NanocomporeError ("Error creating output folder {}".format(fn))

def access_file (fn, **kwargs):
    """Check if the file is readable
    """
    return os.path.isfile (fn) and os.access (fn, os.R_OK)

def counter_to_str (c):
    """Transform a counter dict to a tabulated str"""
    m = ""
    for i, j in c.most_common():
        m += "\t{}: {:,}".format(i, j)
    return m

def combine_pvalues_hou(pvalues, weights, cor_mat):
    """ Hou's method for the approximation for the distribution of the weighted
        combination of non-independent or independent probabilities.
        https://doi.org/10.1016/j.spl.2004.11.028
        
        pvalues: list of pvalues to be combined
        weights: the weights of the pvalues
        cor_mat: a matrix containing the correlation coefficients between pvalues
        
        Test: when weights are equal and cor=0, hou is the same as Fisher
        print(combine_pvalues([0.1,0.02,0.1,0.02,0.3], method='fisher')[1])
        print(hou([0.1,0.02,0.1,0.02,0.3], [1,1,1,1,1], np.zeros((5,5))))
    """
    # Covariance estimation as in Kost and McDermott (eq:8)
    # https://doi.org/10.1016/S0167-7152(02)00310-3
    cov = lambda r: (3.263*r)+(0.710*r**2)+(0.027*r**3)

    k=len(pvalues)
    cov_sum=0
    sw_sum=0
    w_sum=0
    tau=0
    for i in range(k):
        for j in range(i+1,k):
            cov_sum += weights[i]*weights[j]*cov(cor_mat[i][j])
        sw_sum += weights[i]**2
        w_sum += weights[i]
        # Calculate the weighted Fisher's combination statistic
        tau += weights[i] * (-2*np.log(pvalues[i]))

    # Correction factor
    c = (2*sw_sum+cov_sum) / (2*w_sum)
    # Degrees of freedom
    f = (4*w_sum**2) / (2*sw_sum+cov_sum)

    combined_p = 1-chi2.cdf(tau/c,f)
    return(combined_p)

def cross_corr_matrix(pvalues_vector, context=2):
    """Calculate the cross correlation matrix of the 
        pvalues for a given context.
    """
    matrix=[]
    s=pvalues_vector.size
    for i in range(-context,context+1):
        row=[]
        for j in range(-context,context+1):
            row.append(np.corrcoef((np.roll(pvalues_vector,i)[context:s-context]), (np.roll(pvalues_vector,j)[context:s-context]))[0][1])
        matrix.append(row)
    return(np.array(matrix))
