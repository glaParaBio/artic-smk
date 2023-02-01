<!-- vim-markdown-toc GFM -->

* [Description](#description)
* [Setup](#setup)
    * [Set up Guppy](#set-up-guppy)
    * [Set up conda environment](#set-up-conda-environment)
* [Usage](#usage)
* [Devel](#devel)

<!-- vim-markdown-toc -->

# Description

# Setup

## Set up Guppy

Download the appropriate version of guppy from [Oxford
Nanopore](https://community.nanoporetech.com/downloads) (requires registration,
which is free), e.g. `ont-guppy_6.4.2_linux64.tar.gz` (GPU) or
`ont-guppy-cpu_6.4.2_linux64.tar.gz` (CPU). 

Or get it from 

```
# CPU
wget https://mirror.oxfordnanoportal.com/software/analysis/ont-guppy-cpu_6.4.2_linux64.tar.gz
wget https://mirror.oxfordnanoportal.com/software/analysis/ont-guppy-gpu_6.4.2_linux64.tar.gz
```

Extract files: 

```
tar zxvf ont-guppy_6.4.2_linux64.tar.gz
```

and add the `bin` directory to your `PATH` variable:

```
export PATH=/full/path/to/ont-guppy_6.4.2_linux64/bin:$PATH
```

To permanently have guppy available on your PATH, add the command above to the
file `~/.bashrc`.

## Set up conda environment

* Install
[conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html),
[mamba](https://github.com/mamba-org/mamba), and configure for
[bioconda](https://bioconda.github.io/).

* Create a dedicated environment for this pipeline

```
conda create --yes -n artic-smk
conda activate artic-smk
mamba install --yes --file requirements.txt -n artic-smk
```

# Usage

```
```

# Devel
