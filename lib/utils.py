import os
import pandas
import errno
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

def get_config(config):
    """Parse the config dictionary to add defaults and throw friendly errors
    """
    if 'guppy_device' not in config:
        config['guppy_device'] = ''
    if 'guppy_extra_opts' not in config:
        config['guppy_extra_opts'] = ''
    if 'guppy_path' not in config or config['guppy_path'] is None:
        config['guppy_path'] = ''

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

def guppy_device_opt(x):
    """Parse command config option x and return a string suitable for guppy cli
    """
    if x.lower() == 'gpu' or x == '' or x is None:
        return ''
    elif x.lower() == 'auto':
        return '-x auto'
    elif x.startswith('cuda:'):
        return '-x %s' % x
    else:
        raise Exception('Invalid option for guppy device: %s' % x)

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
