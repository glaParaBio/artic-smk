#!/usr/bin/env python3

import unittest
import sys
import shutil
import os
import subprocess as sp

class Test(unittest.TestCase):

    def setUp(self):
        sys.stderr.write('\n' + self.id().split('.')[-1] + ' ') # Print test name
        if os.path.exists('test_out'):
            shutil.rmtree('test_out')
        os.mkdir('test_out')

    def tearDown(self):
        if os.path.exists('test_out'):
            shutil.rmtree('test_out')

    def testGuppyBasecaller(self):
        cmd = r"""
        ./artic-smk.py -s test/data/sample_sheet.tsv -f5 test/data/fast5 -j 4 \
                --guppy-basecaller-opts ' --num_callers 20'  \
                --guppy-path ont-guppy/ont-guppy-cpu_6.4.2_linux64/bin \
                -smk ' -- guppy_basecaller'
        """
        p = sp.Popen(cmd, shell=True, stdout= sp.PIPE, stderr= sp.PIPE)
        stdout, stderr = p.communicate()
        self.assertEqual(0, p.returncode)

    def testGuppyBarcoder(self):
        cmd = r"""
        export PATH=$PWD/ont-guppy/ont-guppy-cpu_6.4.2_linux64/bin:$PATH

        snakemake -p -j 1 \
                -d test_out \
                -C sample_sheet=$PWD/test/data/sample_sheet.tsv \
                   guppy_extra_opts='--num_callers 10' \
                   guppy_config=dna_r9.4.1_450bps_fast.cfg \
                   guppy_barcode_kit=EXP-NBD104 \
                   fast5_dir=$PWD/test/data/fast5 \
                   -- guppy_barcoder
        """
        p = sp.Popen(cmd, shell=True, stdout= sp.PIPE, stderr= sp.PIPE)
        stdout, stderr = p.communicate()
        self.assertEqual(0, p.returncode)

    def test_all(self):
        cmd = r"""
        export PATH=$PWD/ont-guppy/ont-guppy-cpu_6.4.2_linux64/bin:$PATH

        snakemake -p -j 1 \
                -d test_out \
                -C sample_sheet=$PWD/test/data/sample_sheet.tsv \
                   guppy_extra_opts='--num_callers 10' \
                   guppy_config=dna_r9.4.1_450bps_fast.cfg \
                   guppy_barcode_kit=EXP-NBD104 \
                   fast5_dir=$PWD/test/data/fast5 \
                   genome_name=my_genome
        """
        p = sp.Popen(cmd, shell=True, stdout= sp.PIPE, stderr= sp.PIPE)
        stdout, stderr = p.communicate()
        self.assertEqual(0, p.returncode)

    def testDemultiplexedFastqEntry(self):
        cmd = r"""
        snakemake -p -j 1 -n \
                -d test_out \
                -C sample_sheet=$PWD/test/data/sample_sheet.tsv \
                   guppy_extra_opts='--num_callers 10' \
                   guppy_config=dna_r9.4.1_450bps_fast.cfg \
                   guppy_barcode_kit=EXP-NBD104 \
                   fastq_dir=$PWD/test/data/fastq \
                   genome_name=my_genome
        """

if __name__ == '__main__':
    unittest.main()
