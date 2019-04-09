import pytest
from nanocompore.TxComp import *
from scipy.stats import combine_pvalues
import numpy as np
from unittest import mock
from nanocompore.SimReads import SimReads, parse_mod_pos_file
from nanocompore.SampComp import SampComp
import hashlib
import sys
import random

@pytest.fixture(scope="module")
def fasta_file(tmpdir_factory):
    fasta_file = tmpdir_factory.mktemp("fasta").join("reference.fa")
    random.seed(42)
    with open(fasta_file, 'w') as f:
        for n in range(0,1):
            f.write('>Ref_00{}\n'.format(n))
            f.write("".join([random.choice("ACGT") for _ in range(0,random.randint(100, 2000))])+"\n")    
    return(str(fasta_file))

@pytest.fixture(scope="module")
def nanopolishcomp_test_files(tmpdir_factory, fasta_file):
    """ Generate simulated data with SimReads() """
    tmp_path=tmpdir_factory.mktemp("generated_data")
    data_rand_seed=869
    fn_dict={'S1':{}, 'S2':{}}
    for rep in [1,2,3,4]:
        SimReads (
            fasta_fn=fasta_file,
            outpath=str(tmp_path),
            outprefix="control_rep"+str(rep),
            run_type = "RNA",
            intensity_mod_loc=0,
            intensity_mod_scale=0,
            dwell_mod_loc=0,
            dwell_mod_scale=0,
            mod_reads_freq=0,
            mod_bases_freq=0,
            mod_bases_type="A",
            mod_extend_context=False,
            pos_rand_seed=66,
            data_rand_seed=data_rand_seed+rep,
            not_bound=True,
            log_level="debug",
            overwrite=True)

        SimReads (
            fasta_fn=fasta_file,
            outpath=str(tmp_path),
            outprefix="mod_rep"+str(rep),
            run_type = "RNA",
            intensity_mod_loc=10,
            dwell_mod_loc=0.05,
            mod_reads_freq=0.5,
            mod_bases_freq=0.25,
            mod_bases_type="A",
            mod_extend_context=False,
            pos_rand_seed=66,
            data_rand_seed=data_rand_seed+rep,
            not_bound=True,
            log_level="debug",
            overwrite=True)
        fn_dict['S1']['R'+str(rep)]="{}/control_rep{}.tsv".format(str(tmp_path), rep)
        fn_dict['S2']['R'+str(rep)]="{}/mod_rep{}.tsv".format(str(tmp_path), rep)

    return((fasta_file, fn_dict, str(tmp_path)))

@pytest.mark.parametrize("method", ["GMM", "KS", "TT", "MW", "GMM,KS,TT,MW"])
@pytest.mark.parametrize("context", [2,3])
@pytest.mark.parametrize("context_weight", ["uniform", "harmonic"])
def test_sig_sites(nanopolishcomp_test_files, method, context, context_weight):
    fasta_file, fn_dict, tmp_path = nanopolishcomp_test_files
    s = SampComp(eventalign_fn_dict=fn_dict,
            outpath=tmp_path,
            outprefix="nanocompore",
            fasta_fn=fasta_file,
            comparison_methods = method,
            logit = True,
            allow_warnings = False,
            sequence_context = context,
            sequence_context_weights = context_weight,
            downsample_high_coverage = None,
            nthreads=6,
            overwrite=True)
    db = s()
    db.save_report("{}/report_{}_{}_{}.txt".format(tmp_path, method, context, context_weight))
    # Load the expected modified positions from the files generated by SimReads()
    expected_pos = parse_mod_pos_file(tmp_path+"/mod_rep1_pos.tsv")

    # Assert that the modified positions identified by SampComp match the expected ones
    for ref in db.ref_id_list:
        for test in [t for t in db._metadata["pvalue_tests"] if "context" not in t]:
            sig=db.list_significant_positions(ref_id=ref, test=test, thr=0.05)
            assert expected_pos[ref] == sig

def test_deterministic_behaviour(nanopolishcomp_test_files):
    fasta_file, fn_dict, tmp_path = nanopolishcomp_test_files
    s = SampComp(eventalign_fn_dict=fn_dict,
            outpath=tmp_path,
            outprefix="nanocompore",
            comparison_methods="GMM,KS,TT,MW",
            sequence_context=2,
            fasta_fn=fasta_file,
            allow_warnings=False,
            downsample_high_coverage = None,
            nthreads=6,
            overwrite=True)
    db = s()
    db.save_report(tmp_path+"/report1.txt")

    np.random.seed(seed=None)

    s = SampComp(eventalign_fn_dict=fn_dict,
            outpath=tmp_path,
            outprefix="nanocompore",
            comparison_methods="GMM,KS,TT,MW",
            sequence_context=2,
            fasta_fn=fasta_file,
            allow_warnings=False,
            downsample_high_coverage = None,
            nthreads=6,
            overwrite=True)
    db = s()
    db.save_report(tmp_path+"/report2.txt")
    assert hash_file(tmp_path+"/report1.txt") == hash_file(tmp_path+"/report2.txt")

def hash_file(file):
    """
    Returns the sha1 checksum of a file reading
    it in chuncks.
    """
    BUF_SIZE = 102400
    sha1 = hashlib.sha1()
    with open(file, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha1.update(data)
    return(sha1.hexdigest())
