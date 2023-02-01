#!/usr/bin/env python3

import unittest
import sys
import shutil
import os
import subprocess as sp

from importlib.machinery import SourceFileLoader
utils = SourceFileLoader('utils.py', 'lib/utils.py').load_module()

class Test(unittest.TestCase):

    def setUp(self):
        sys.stderr.write('\n' + self.id().split('.')[-1] + ' ') # Print test name
        if os.path.exists('test_out'):
            shutil.rmtree('test_out')
        os.mkdir('test_out')

    def tearDown(self):
        if os.path.exists('test_out'):
            shutil.rmtree('test_out')

    def testLoadCsv(self):
        ss = utils.read_sample_sheet('test/data/sample_sheet.csv')
        self.assertTrue('sample' in ss.columns)
        self.assertTrue('barcode' in ss.columns)

    def testLoadTsv(self):
        ss = utils.read_sample_sheet('test/data/sample_sheet.tsv')
        self.assertTrue('sample' in ss.columns)
        self.assertTrue('barcode' in ss.columns)
        self.assertEqual(len(ss), 4)

    def testHelp(self):
        cmd = r"""
        ./artic-smk.py -h
        """
        p = sp.Popen(cmd, shell=True, stdout= sp.PIPE, stderr= sp.PIPE)
        stdout, stderr = p.communicate()
        self.assertEqual(0, p.returncode)

    def testGuppyBasecaller(self):
        cmd = r"""
        ./artic-smk.py \
            --sample-sheet test/data/sample_sheet.tsv \
            -f5 test/data/fast5 \
            --output test_out \
            --guppy-basecaller-opts ' --num_callers 20'  \
            --guppy-path ont-guppy/ont-guppy-cpu_6.4.2_linux64/bin \
            guppy_basecaller
        """
        p = sp.Popen(cmd, shell=True, stdout= sp.PIPE, stderr= sp.PIPE)
        stdout, stderr = p.communicate()
        self.assertEqual(0, p.returncode)

    def testFastqInput(self):
        cmd = r"""
        ./artic-smk.py \
            --jobs 4 \
            --sample-sheet test/data/sample_sheet.tsv \
            -fq test/data/fastq \
            --genome-name my-genome \
            --output test_out
        """
        p = sp.Popen(cmd, shell=True, stdout= sp.PIPE, stderr= sp.PIPE)
        stdout, stderr = p.communicate()
        self.assertEqual(0, p.returncode)
        self.assertTrue(os.path.isfile('test_out/mafft/my-genome.aln.fasta'))

    def testFast5Input(self):
        cmd = r"""
        ./artic-smk.py \
            --jobs 4 \
            --sample-sheet test/data/sample_sheet.tsv \
            -f5 test/data/fast5 \
            --genome-name my-genome \
            --guppy-path ont-guppy/ont-guppy-cpu_6.4.2_linux64/bin \
            --output test_out
        """
        p = sp.Popen(cmd, shell=True, stdout= sp.PIPE, stderr= sp.PIPE)
        stdout, stderr = p.communicate()
        self.assertEqual(0, p.returncode)
        self.assertTrue(os.path.isfile('test_out/mafft/my-genome.aln.fasta'))

if __name__ == '__main__':
    unittest.main()
