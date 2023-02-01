from importlib.machinery import SourceFileLoader
utils = SourceFileLoader('utils.py', os.path.join(workflow.basedir, 'lib', 'utils.py')).load_module()

ss = utils.read_sample_sheet(config['sample_sheet'])
config = utils.get_config(config)

wildcard_constraints:
    sample='|'.join([re.escape(x) for x in ss['sample']]),
    barcode='|'.join([re.escape(x) for x in ss['barcode']]),
    genome_name=re.escape(config['genome_name']),


rule all:
    input:
        'mafft/{genome_name}.aln.fasta'.format(genome_name=config['genome_name']),


rule guppy_basecaller:
    input:
        fast5=config['fast5_dir'],
    output:
        outdir=directory('guppy_basecaller'),
    params:
        config=config['guppy_config'],
        device=utils.guppy_device_opt(config['guppy_device']), # This is the `-x` option
        extra_opts=config['guppy_extra_opts'],
        guppy_export_cmd=lambda wc: config['guppy_export_cmd'],
    shell:
        r"""
        {params.guppy_export_cmd}
        guppy_basecaller --recursive {params.extra_opts} \
            {params.device} \
            -c {params.config} \
            -i {input.fast5} \
            -s {output.outdir}
        """


rule guppy_barcoder:
    input:
        fastq_dir='guppy_basecaller',
    output:
        fastq_dir=directory(expand('fastq/{barcode}', barcode=ss['barcode'])),
    params:
        barcode_kit=config['guppy_barcode_kit'],
        guppy_export_cmd=lambda wc: config['guppy_export_cmd'],
    shell:
        r"""
        {params.guppy_export_cmd}
        guppy_barcoder --recursive \
            --require_barcodes_both_ends \
            -i {input.fastq_dir} \
            -s fastq \
            --barcode_kits {params.barcode_kit}
        """


rule read_filtering:
    input:
        fastq_dir='fastq/{barcode}',
    output:
        fastq='guppyplex/{sample}_{barcode}.fastq',
    params:
        min_length=config['min_length'],
        barcode=lambda wc: ss[ss['sample'] == wc.sample].barcode.iloc[0],
    shell:
        r"""
        artic guppyplex --skip-quality-check \
            --min-length {params.min_length} \
            --directory {input.fastq_dir} \
            --prefix guppyplex/{wildcards.sample}
        """


rule medaka:
    input:
        fastq=lambda wc: 'guppyplex/{sample}_%s.fastq' % ss[ss['sample'] == wc.sample].barcode.iloc[0],
        medaka_scheme_directory=config['medaka_scheme_directory']
    output:
        cons='medaka/{sample}.consensus.fasta',
    params:
        medaka_model=config['medaka_model'],
        scheme=config['medaka_scheme']
    shell:
        r"""
        artic minion --medaka \
            --medaka-model {params.medaka_model} \
            --normalise 200 \
            --threads 8 \
            --scheme-directory {input.medaka_scheme_directory} \
            --read-file {input.fastq} \
            {params.scheme} medaka/{wildcards.sample}
        """


rule consensus:
    input:
        fasta=expand('medaka/{sample}.consensus.fasta', sample=sorted(list(set(ss['sample'])))),
    output:
        fasta='consensus/{genome_name}.fasta',
    shell:
        r"""
        cat {input.fasta} > {output.fasta}
        """


rule mafft:
    input:
        fasta='consensus/{genome_name}.fasta',
    output:
        fasta='mafft/{genome_name}.aln.fasta',
    shell:
        r"""
        mafft --thread 1 {input.fasta} > {output.fasta}
        """


onsuccess:
    if os.path.isdir('dummy_fast5'):
        os.rmdir('dummy_fast5')
