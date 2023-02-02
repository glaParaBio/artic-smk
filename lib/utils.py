import re
import os
import pandas
import errno
import subprocess
import tempfile
import snakemake

def read_sample_sheet(fn):
    """Read sample sheet in file fn into a DataFrame
    """
    done = False
    for sep in ['\t', ',']:
        ss = pandas.read_csv(fn, sep='\t', comment='#')
        if 'sample' in ss.columns and 'barcode' in ss.columns:
            done = True
        if done:
            break

    for colname in ['sample', 'barcode']:
        if colname not in ss.columns:
            raise Exception(f'Column {colname} not found in sample sheet {fn}')
        x = list(ss[colname])
        if len(x) != len(set(x)):
            raise Exception(f'Duplicates found in column {colname}')
    
    return ss

def select_guppy_device(guppy_path, guppy_basecaller_opts):
    """Some euristics to select the best device option for guppy. Basically,
    construct the `-x` option string
    """
    opts = ' ' + guppy_basecaller_opts + ' '
    opts = re.sub(' --device ', '', ' -x ')
    opts = re.sub(' +', ' ', opts)
    for x in [' -x auto ', ' -xauto ', ' -x cuda:', ' -xcuda:']:
        # If '-x' is already selected as an additional option, respect it and
        # don't set -x again:
        if x in opts:
            return ''
    
    # Make dummy data to test GPU option
    tmp = tempfile.TemporaryDirectory(dir='.')
    bardir = os.path.join(tmp.name, 'barcode99')
    os.makedirs(bardir)
    with open(os.path.join(bardir, 'read.fastq'), 'w') as fq:
        fq.write('@R1\n')
        fq.write('AAAAAAAAAAAAAAAAAAAAAAAAA\n')
        fq.write('+\n')
        fq.write('AAAAAAAAAAAAAAAAAAAAAAAAA\n')

    guppy = os.path.join(os.path.abspath(guppy_path), 'guppy_barcoder')
    cmd = f'{guppy} -x auto -i {bardir} -s {tmp.name}'
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    tmp.cleanup()

    if p.returncode == 0:
        return '-x auto'
    else:
        return ''

def get_config(config):
    """Parse the config dictionary to add defaults and throw friendly errors
    """
    # If you pass an empty string as config, python/snakemake converts it to
    # None so we need to put back the empty string:
    if 'guppy_path' not in config or config['guppy_path'] is None:
        config['guppy_path'] = ''

    if 'guppy_basecaller_opts' not in config or config['guppy_basecaller_opts'] is None:
        config['guppy_basecaller_opts'] = ''

    if config['guppy_path'] == '':
        config['guppy_export_cmd'] = ''
    else:
        config['guppy_export_cmd'] = 'export PATH=%s:${PATH}' % config['guppy_path']

    if 'fast5_dir' in config and 'fastq_dir' in config:
        raise Exception('Provide one of fast5_dir or fastq_dir, not both')

    if 'fastq_dir' in config:
        config['fast5_dir'] = 'dummy_fast5'
        snakemake.shell('mkdir -p dummy_fast5 && touch -d "01/01/2000" dummy_fast5')
        symlink_force(os.path.abspath(config['fastq_dir']), os.path.abspath('fastq'))
        
    return config

def symlink_force(target, link_name):
    # From https://stackoverflow.com/questions/8299386/modifying-a-symlink-in-python
    try:
        os.symlink(target, link_name)
    except FileExistsError as e:
        if e.errno == errno.EEXIST:
            os.remove(link_name)
            os.symlink(target, link_name)
        else:
            raise e
