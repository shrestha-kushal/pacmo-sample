html header: <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/9.15.10/styles/a11y-light.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/9.15.10/highlight.min.js"></script>
    <script>hljs.initHighlightingOnLoad();</script>
    <link rel="stylesheet" href="./styles/docstyles.css">
Base Header Level: 2

\[[Home](./toc.md)\]

# {++Installation Guide++}

## Topics: [topics]
1. [System Requirements][topic-1]
2. [Installing with conda][topic-2]

---

## 1. System Requirements: [topic-1] 

1. Operating System: Linux
2. Instruction Set Architecture: AMD64

PACMO is a python framework that is made available in its most simple form as a Python package. You may obtain an archive of this python package directly from here. Because PACMO has a couple of dependencies on other python libraries, it is also made available as a conda package through the following conda channel: https://my-secret-host.com:8997/nexus/repository/group . Software dependencies are shown below.

Software dependencies:
1. Python 3.7
2. pyyaml
3. pyaml
4. pdoc3

\[[Home](./toc.md)\] &nbsp;&nbsp;&nbsp; \[[Topics][topics]\]

---

## 2. Installing with conda: [topic-2]

The PACMO conda package may be installed into an active conda environment with the following command within the bash shell:

```bash
conda install -k -c conda-forge -c https://my-secret-host.com:8997/nexus/repository/group pacmo
```

Because PACMO is available as a conda package, it may be specified as a dependency when building any other conda package with the conda build utility. This is the recommended distribution strategy for PACMO-based applications.

\[[Home](./toc.md)\] &nbsp;&nbsp;&nbsp; \[[Topics][topics]\]

---

