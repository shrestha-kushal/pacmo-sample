html header: <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/9.15.10/styles/a11y-light.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/9.15.10/highlight.min.js"></script>
    <script>hljs.initHighlightingOnLoad();</script>
    <link rel="stylesheet" href="./styles/docstyles.css">
Base Header Level: 2

# Documentation for PACMO: A {++P++}ython {++A++}pplication for {++C++}omputational {++M++}odules {++O++}rchestration

## {++Table of Contents++}: [toc]
1. [Overview][overview]
2. [Installation Guide](./installation.md)
3. [User Documentation](./userdoc.md)
4. [Developer Documentation](./developerdoc.md)
5. [API Documentation]()

---

# {++Overview++}: [overview]

PACMO is a small python framework for driving computational workflows that are common to scientific computing in science-driven industries. The framework's aim is to encourage computational software developers to refashion one-off computer programs that do a specific computational task into easily *parameterized* and *reusable* computational modules. PACMO provides a framework for making such modules available for use when designing various computational workflows. 

Any workflow that is composed of multiple computational steps and requires the sequential use of a number of scripts or computer programs to successfully transform a given input to the desired output may be re-implemented within the framework provided by PACMO. PACMO provides a simple abstraction for a modularized, sequentially executing, computational workflow as a "**pipeline**" that is completely defined by its configuration expressed in [YAML](https://yaml.org). Developers may implement their own computational modules as Python classes and make them available to all designers of and ultimately users of pipelines. Throughout this documentation, such reusable, computational modules are referred to as "pipeline steps" or simply as "**steps**." 

PACMO itself is made available to users as a Python Conda package for use on Linux AMD64 systems. Computational software developers that wish to contribute to the [PACMO project]() should contact [Kushal Shrestha]() .

\[[Table of Contents][toc]\]

---
