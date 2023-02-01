#!/usr/bin/env python3

import sys
import os
import argparse
import subprocess
import textwrap

def run_command(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    while True:
        output = process.stdout.readline().decode()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())
    rc = process.poll()
    return rc

def make_wide(formatter, w=120, h=36):
    """Return a wider HelpFormatter, if possible.
    Credit: https://stackoverflow.com/a/57655311/1114453
    """
    try:
        # https://stackoverflow.com/a/5464440
        # beware: "Only the name of this class is considered a public API."
        kwargs = {'width': w, 'max_help_position': h}
        formatter(None, **kwargs)
        return lambda prog: formatter(prog, **kwargs)
    except TypeError:
        warnings.warn("argparse help formatter failed, falling back.")
        return formatter


parser = argparse.ArgumentParser(description='Run artic pipeline', formatter_class=make_wide(argparse.HelpFormatter, w=80))
parser.add_argument('--sample-sheet', '-s', help='Tab-separated file of samples, barcodes, and other sample-specific options. See online doumentation for details [required]', required=True)
parser.add_argument('--output', '-o', help='Output directory [%(default)s]', default='artic-out')
parser.add_argument('--fast5-dir', '-f5', help='Directory of fast5 file. Typically the Nanopore run directory')
parser.add_argument('--fastq-dir', '-fq', help='Input alternative to fastq5-dir: Directory of demultiplexed fastq files. fastq-dir contains subdirectories named after the sample barcodes and containing the respective fastq files')
parser.add_argument('--genome-name', '-g', help='Name for consensus genome [%(default)s]', default='genome')
parser.add_argument('--guppy-config', help='For fast5 input: Configuration for guppy_basecaller [%(default)s]', default='dna_r9.4.1_450bps_fast.cfg')
parser.add_argument('--guppy-barcode-kit', help='For fast5 input: Barcode kit passed to guppy_barcoder [%(default)s]', default='EXP-NBD104')
parser.add_argument('--guppy-basecaller-opts', help='Additional options passed to guppy_basecaller as a string with leading space e.g. " --num_caller 10" [%(default)s]', default='')
parser.add_argument('--guppy-path', help='Full path to guppy bin directory. Leave empty if guppy is already on your search PATH [%(default)s]', default='')
parser.add_argument('--min-length', '-L', help='Ignore reads less than min-length [%(default)s]', default=350, type=int)
parser.add_argument('--medaka-model', help='Model to use for medaka [%(default)s]', default='r941_min_fast_g303')
parser.add_argument('--medaka-scheme-directory', '-sd', help='Path to scheme directory [%(default)s]', default='primer-schemes')
parser.add_argument('--medaka-scheme', help='Scheme for medaka [%(default)s]', default='rabv_ea/V1')
parser.add_argument('--jobs', '-j', help='Number of jobs to run in parallel [%(default)s]', default=1, type=int)
parser.add_argument('--dry-run', '-n', help='Run pipeline dry-run mode', action='store_true')
parser.add_argument('--snakemake-opts', '-smk', help='Additional options to snakemake as a string with leading space e.g. " --rerun-incomplete -k" [%(default)s]', default='')
parser.add_argument('--version', '-v', action='version', version='%(prog)s 0.1.0')

if __name__ == '__main__':
    args = parser.parse_args()

    sample_sheet = os.path.abspath(args.sample_sheet)
    medaka_scheme_directory = os.path.abspath(args.medaka_scheme_directory)
    
    if args.fast5_dir is not None and args.fastq_dir is not None:
        sys.stderr.write('Please provide fast5 or fastq input, not both\n')
        sys.exit(1)
    elif args.fast5_dir is not None:
        fastx_dir="fast5_dir='%s'" % os.path.abspath(args.fast5_dir)
    elif args.fastq_dir is not None:
        fastx_dir="fastq_dir='%s'" % os.path.abspath(args.fastq_dir)
    else:
        fastx_dir=''
    
    if args.guppy_path.strip() != '':
        guppy_path = os.path.abspath(args.guppy_path)
    else:
        guppy_path = ''

    if args.dry_run:
        dryrun = '--dry-run'
    else:
        dryrun = ''

    smk_cmd = f"""
    snakemake --printshellcmds {dryrun} \\
        --jobs {args.jobs} \\
        --directory {args.output} \\
        --config sample_sheet={sample_sheet} \\
           guppy_path='{guppy_path}' \\
           guppy_config={args.guppy_config} \\
           guppy_barcode_kit={args.guppy_barcode_kit} \\
           guppy_extra_opts='{args.guppy_basecaller_opts}' \\
           min_length={args.min_length} \\
           medaka_scheme_directory={medaka_scheme_directory} \\
           medaka_scheme={args.medaka_scheme} \\
           medaka_model={args.medaka_model} \\
           genome_name={args.genome_name} \\
           {fastx_dir} \\
           {args.snakemake_opts} 1>&2
    """
    smk_cmd = smk_cmd.strip().rstrip('\\')

    sys.stderr.write('\033[36m' + textwrap.dedent(smk_cmd) + '\033[0m' + '\n' )

    rc = run_command(smk_cmd)
