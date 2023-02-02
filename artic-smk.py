#!/usr/bin/env python3

import sys
import os
import argparse
import subprocess
import textwrap
import colorama

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


parser = argparse.ArgumentParser(description='Run artic pipeline', formatter_class=make_wide(argparse.HelpFormatter, w=100))
parser.add_argument('targets', help='Target file(s) to create or rule(s) to execute [%(default)s]', nargs='*', default='all')

io = parser.add_argument_group('Main input/output options')
guppy = parser.add_argument_group('Options for guppy (for fast5 input only)')
minion = parser.add_argument_group('Options for artic minion/medaka')
misc = parser.add_argument_group('Miscellanea')
snakemake = parser.add_argument_group('Workflow management options passed to snakemake')

io.add_argument('--sample-sheet', '-s', help='Tabular file of samples and barcodes. See online docs for details [required]', required=True, metavar='FILE')
io.add_argument('--fast5-dir', '-f5', help='Directory of fast5 files', metavar='DIR')
io.add_argument('--fastq-dir', '-fq', help='Directory of demultiplexed fastq files. fast5-dir OR fastq-dir is required', metavar='DIR')
io.add_argument('--output', '-o', help='Output directory [%(default)s]', default='artic-out', metavar='DIR')

guppy.add_argument('--guppy-config', help='Configuration for guppy_basecaller [%(default)s]', default='dna_r9.4.1_450bps_fast.cfg', metavar='STR')
guppy.add_argument('--guppy-barcode-kit', help='Barcode kit [%(default)s]', default='EXP-NBD104', metavar='STR')
guppy.add_argument('--guppy-path', help='Full path to guppy bin directory. Leave empty if guppy is on your search PATH [%(default)s]', default='', metavar='DIR')
guppy.add_argument('--guppy-basecaller-opts', help='Additional options passed to guppy_basecaller as a string with leading space e.g. " --num_callers 10" [%(default)s]', default='', metavar='STR')

minion.add_argument('--medaka-model', help='Model for medaka [%(default)s]', default='r941_min_fast_g303', metavar='STR')
default_scheme_directory = 'primer-schemes'
minion.add_argument('--medaka-scheme-directory', '-sd', help=f'Path to scheme directory [{default_scheme_directory}]', default=None, metavar='DIR')
minion.add_argument('--medaka-scheme', help='Scheme for medaka [%(default)s]', default='rabv_ea/V1', metavar='DIR')
minion.add_argument('--normalise', help='Normalise down to moderate coverage to save runtime [%(default)s]', default=200, type=int, metavar='N')

misc.add_argument('--genome-name', '-g', help='Name for consensus genome [%(default)s]', default='genome', metavar='STR')
misc.add_argument('--min-length', '-L', help='Ignore reads less than min-length [%(default)s]', default=350, type=int, metavar='N')

snakemake.add_argument('--jobs', '-j', help='Number of jobs to run in parallel [%(default)s]', default=1, type=int, metavar='N')
snakemake.add_argument('--dry-run', '-n', help='Only show what would be executed', action='store_true')
snakemake.add_argument('--snakefile', help='Snakefile of the pipeline. The directory "lib" is expected to be in the same directory as this file [%(default)s]', default='Snakefile', metavar='FILE')
snakemake.add_argument('--snakemake-opts', '-smk', help='Additional options to snakemake as a string with leading space e.g. " --rerun-incomplete -k" [%(default)s]', default='--rerun-incomplete', metavar='STR')

parser.add_argument('--version', '-v', action='version', version='%(prog)s 0.1.0')

if __name__ == '__main__':
    args = parser.parse_args()

    sample_sheet = os.path.abspath(args.sample_sheet)
    
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

    libdir = os.path.dirname(args.snakefile)
    utils = os.path.join(libdir, 'lib/utils.py')
    if not os.path.isfile(utils):
        sys.stderr.write('The directory containing the snakefile ("%s") does not contain the lib directory\n' % libdir)
        sys.exit(1)
    
    medaka_scheme_directory = args.medaka_scheme_directory
    if medaka_scheme_directory is None:
        medaka_scheme_directory = os.path.join(libdir, default_scheme_directory)
    medaka_scheme_directory = os.path.abspath(medaka_scheme_directory)

    if args.targets == []:
        targets = ''
    elif type(args.targets) == str:
        targets = '-- %s' % args.targets
    else:
        targets = '-- %s' % ' '.join(args.targets) 

    smk_cmd = f"""
    snakemake --snakefile {args.snakefile} \\
        --printshellcmds {dryrun} \\
        --jobs {args.jobs} \\
        --directory {args.output} \\
        --config sample_sheet={sample_sheet} \\
           guppy_path='{guppy_path}' \\
           guppy_config={args.guppy_config} \\
           guppy_barcode_kit={args.guppy_barcode_kit} \\
           guppy_basecaller_opts='{args.guppy_basecaller_opts}' \\
           min_length={args.min_length} \\
           medaka_scheme_directory={medaka_scheme_directory} \\
           medaka_scheme={args.medaka_scheme} \\
           medaka_model={args.medaka_model} \\
           normalise={args.normalise} \\
           genome_name={args.genome_name} \\
           {fastx_dir} \\
           {args.snakemake_opts} {targets} 1>&2
    """
    smk_cmd = smk_cmd.strip().rstrip('\\')

    sys.stderr.write(colorama.Fore.BLUE + textwrap.dedent(smk_cmd) + colorama.Style.RESET_ALL + '\n' )

    rc = run_command(smk_cmd)
