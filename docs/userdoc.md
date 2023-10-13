html header: <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/9.15.10/styles/a11y-light.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/9.15.10/highlight.min.js"></script>
    <script>hljs.initHighlightingOnLoad();</script>
    <link rel="stylesheet" href="./styles/docstyles.css">
Base Header Level: 2

\[[Home](./toc.md)\]

## {++Topics++}: [topics]
1. [Overview][topic-1]
2. [The user input file: `user_input.yaml`][topic-2]
3. [The `chosen_pipeline` node][topic-3]
     1. [Listing 1. Example of `chosen_pipeline` node][topic-3.1]
4. [The `global_config` node][topic-4]
     1. [Listing 2. Example of the `global_config` node][topic-4.1]
5. [The `pipeline_config` node][topic-5]
     1. [Listing 3. Example `pipeline_config` node][topic-5.1]
6. [Examples of complete `user_input.yaml` files][topic-6]
     1. [Listing 4. Example `user_input.yaml` file][topic-6.1]
     2. [Listing 5. Example `user_input.yaml` file with comments][topic-6.2]

## 1. Overview [topic-1]

Users will generally use PACMO when they use custom Python applications developed by consumers of the PACMO framework. Applications that rely on the PACMO framework to drive their computational workflows or pipelines will be referred to in this document as PACMO-based applications. Users of PACMO-based applications will, therefore, only interact with PACMO indirectly through some aspects of the user input file. 

\[[Home](./toc.md)\] &nbsp;&nbsp;&nbsp; \[[Topics][topics]\]

---

## 2. The user input file: `user_input.yaml` [topic-2]
The user input file is defined by users of any PACMO-based application and is the method by which users can (1) choose a pipeline that is made available by a PACMO-based application, (2) provide user input to a chosen pipeline, and (3) modify the default value of any parameter in the chosen pipeline. The user input file, which is required by PACMO to be named "user_input.yaml" contains specific yaml nodes that are recognized and interpreted by the PACMO framework and by extension any PACMO-based application. PACMO recognizes the following three top level nodes in the user_input.yaml file: (1) chosen_pipeline, (2) global_config, and (3) pipeline_config.

\[[Home](./toc.md)\] &nbsp;&nbsp;&nbsp; \[[Topics][topics]\]

---

## 3. The `chosen_pipeline` node [topic-3]

The chosen_pipeline node is a yaml mapping node with a single key-value pair where the key is the string "chosen_pipeline" and the value is a string scalar that represents the name of the chosen pipeline that is made available by a PACMO-based application. [Listing 1][topic-3.1] shows an example of this node. The chosen_pipeline node is the only node that is mandated by PACMO, and PACMO will raise an exception if this node is not provided in user_input.yaml

---

### Listing 1. Example of `chosen_pipeline` node [topic-3.1]
```yaml
chosen_pipeline: "AwesomePipeline"
```

\[[Home](./toc.md)\] &nbsp;&nbsp;&nbsp; \[[Topics][topics]\]

---

## 4. The `global_config` node [topic-4]

The global_config node can be used to configure global parameters for a given PACMO-based application. The global_config node is a mapping node that contains a single key-value pair where the key is the string "global_config" and value is a nested mapping node. This nested mapping node itself contains a single key-value pair, and PACMO expects the key to be the string "parameters". The value to the "parameters" key is yet another nested mapping node that can contain as many key-value pairs as parameters that users wish to define. [Listing 2][topic-4.1] shows an example of the global_config node. The exact list of global parameters that is available to users to define in user_input.yaml is an implementation detail of a given PACMO-based application. However, PACMO does require PACMO-based applications to make two specific global parameters available. These are the parameters "output_file" and "error_file". Therefore, users can always expect to modify the values of these two parameters in user_input.yaml. The value of the "ouput_file" parameter is the name of the output file of any PACMO-based application, e.g. "pacmo.out" in [Listing 2][topic-4.1]. PACMO-based applications will write formatted text output for the user in this file. The value of the "error_file" is the name of a file where PACMO-based applications will redirect error messages and event logs, e.g. "pacmo.err" in Figure X.

---

### Listing 2. Example of the `global_config` node [topic-4.1]
```yaml
global_config:
  parameters:
    output_file: pacmo.out
    error_file: pacmo.err
    awesome_global_parameter: 42
```

\[[Home](./toc.md)\] &nbsp;&nbsp;&nbsp; \[[Topics][topics]\]

---

## 5. The `pipeline_config` node [topic-5]

The pipeline_config node is a yaml mapping node that contains a single key-value pair where the key is the string "pipeline_config" and the value is a yaml sequence node. This yaml sequence node is where users may provide user-defined inputs and make configuration modifications to steps within their chosen pipeline. PACMO expects each node in this node sequence to have a specific structure. [Listing 3][topic-5.1] shows an example of such a node sequence. As can be seen from the example, the elements of the sequence nodes are all mapping node. The mapping nodes that are nested with the sequence are mapping nodes with a single key-value pair where the key is the name of a step within the chosen pipeline (e.g. "AwesomeStep1", "AwesomeStep2", "AwesomeStep3") and the value is a nested mapping node. The nested mapping node for a given step contains, again, a single key-value pair where the key is the string "parameters" and the value is yet another nested mapping node. The mapping node that is the value of the "parameters" key contains as many key-value pairs as the number of parameters that the user may want to define for a given step, e.g. in [Listing 3][topic-5.1], one key-value pair is defined for step "AwesomeStep1," two for "AwesomeStep2," and two for "AwesomeStep3." The keys for these key-value pairs represent the name of parameter being defined, e.g "awesome_parameter_1" for step "AwesomeStep1", and the values provided for these keys can be any scalar type (like in the case of "awesome_parameter_1", or "awesome_parameter_2", or "awesome_parameter_5"), or a sequence of scalars (like in the case of "awesome_parameter_3"), or a specifically structured mapping node (as in the case of "awesome_parameter_4").

The value of "awesome_parameter_4" requires some explanation. This structure for the value of a parameter key-value pair is necessary when a step, in this case "AwesomeStep3" is executed more than one time in a given pipeline. In such cases, users may need fine-grained control over the definition of parameters for each execution of a step that executes more than one time. To address this need, PACMO recognizes nested mapping nodes for the parameters that are structured like the value of "awesome_parameter_4" in [Listing 3][topic-5.1]. The value of the parameter consists of a set of key-value pairs where the keys are strings of the form "execution_X" where X can either be a representation of an integer or the string "others" and the values are scalar nodes or sequence of scalar nodes that represent the value of parameter. The suffix of the keys, i.e. "X" in "execution_X", bear specific meaning to PACMO. If "X" in "execution_X" is a representation of an integer, then PACMO will take "X" to mean the ordinal number of execution of the step, e.g. the value of execution_1, file1.dat, will be assigned to parameter "awesome_parameter_4" during the 1st execution of step "AwesomeStep3" in the pipeline. If "X" in "execution_X" is the string "others", then PACMO will take "X" to mean all ordinal numbers of execution of the step that is not directly specified, e.g. if step "AwesomeStep3" executed 5 times in the chosen pipeline, then the value of execution_others, file3.dat, will be assigned to parameter "awesome_parameter_4" for the 3rd, 4th, and 5th executions of step "AwesomeStep3." Finally, if the user does not wish to have this level of control but still wishes to define a parameter of a step that executes more than one time in a pipeline, then the user can simply provide a scalar for the parameter (or sequence of scalars depending on what the author of the step expects) and PACMO will assign that scalar or scalar sequence to the parameter for all executions of the step in the pipeline. This is the case for parameter "awesome_parameter_5" in step "AwesomeStep3."

Note that if the chosen pipeline does not explicitly require any user-defined parameters, and the user is content to use the pipeline provided defaults, then it is not necessary to define the pipeline_config node.

---

### Listing 3. Example `pipeline_config` node [topic-5.1]
```yaml
pipeline_config:
  - AwesomeStep1:
      parameters:
        awesome_parameter_1: 3.97e-4
  - AwesomeStep2:
      parameters:
        awesome_parameter_2: 1000
        awesome_parameter_3:
          - 1
          - 2
          - hello
          - world
  - AwesomeStep3:
      parameters:
        awesome_parameter_4:
          execution_1: file1.dat
          execution_2: "file2.dat"
          execution_others: file3.dat
        awesome_parameter_5: GATTACA
```

\[[Home](./toc.md)\] &nbsp;&nbsp;&nbsp; \[[Topics][topics]\]

---

## 6. Examples of complete `user_input.yaml` files [topic-6]

A full `user_input.yaml` file combined from the above Listings is shown below in [Listing 4][topic-6.1] for completeness. Additionally, the `user_input.yaml` file for a pipeline defined in the example PACMO-based application found in the examples directory of the PACMO source code repository is shown below with helpful notes that are commented into the file. The commented notes may serve as supplemental documentation for authors of user_input.yaml files.

---

### Listing 4. Example `user_input.yaml` file [topic-6.1]
```yaml
chosen_pipeline: "AwesomePipeline"

global_config:
  parameters:
    output_file: pacmo.out
    error_file: pacmo.err
    awesome_global_parameter: 42

pipeline_config:
  - AwesomeStep1:
      parameters:
        awesome_parameter_1: 3.97e-4
  - AwesomeStep2:
      parameters:
        awesome_parameter_2: 1000
        awesome_parameter_3:
          - 1
          - 2
          - hello
          - world
  - AwesomeStep3:
      parameters:
        awesome_parameter_4:
          execution_1: file1.dat
          execution_2: "file2.dat"
          execution_others: file3.dat
        awesome_parameter_5: GATTACA
```

---

### Listing 5. Example `user_input.yaml` file with comments [topic-6.2]
```yaml
# NOTE:
# A pipeline is chosen by specifying a key-value
# pair where the key is the string "chosen_pipeline"
# and the value is the string type scalar node that
# represents the name of a registered pipeline
chosen_pipeline: ExamplePipeline4

# NOTE:
# Parameters that have a global scope in the application
# may be overwritten by declaring a key-value pair where
# the key is the string "global_config" and the value is
# a mapping node.
global_config:
  # NOTE:
  # When modifying global parameters, a key-value pair where
  # the key is the string "parameters" is mandatory. The value
  # is a mapping node that contains key value pairs that
  # represent parameters and their corresponding values.
  parameters:
    write_debug: False

# NOTE:
# Parameters for any step can be overwritten by declaring
# a key value pair where the key is the string "pipeline_config"
# and the value is a sequence node.
pipeline_config:
  # NOTE:
  # A steps's parameters can be modified in the manner shown
  # below:
  - StepB:
      # NOTE:
      # The "parameters" key is mandatory.
      parameters:
        # NOTE:
        # A parameter can be set in the manner shown below.
        step_b_parameter_1: 3.97e-4
  - StepC:
      parameters:
        # NOTE:
        # Since the step "StepC" is executed more than once in
        # the chosen pipeline, then parameter "step_c_int_param"
        # will be set to 1000 for every execution of "StepC" in
        # the pipeline if it is assigned in the manner shown below.
        step_c_int_param: 1000
        # NOTE:
        # Parameters that are sequence nodes can also be modified.
        # Whether the user input is allowed to change the size of
        # the sequence node or allowed to change the type of the
        # parameter from a sequence node to a scalar node (and vice versa)
        # or allowed to change the type of the parameter value
        # (e.g from string to integer) is completely up to the rules
        # set forth by the step in question.
        step_c_sequence_param:
          - 1
          - 2
          - 3
          - 4
  - StepE:
      parameters:
        input_file:
          # NOTE:
          # "StepE" is executed 4 times in the chosen pipeline, and
          # any parameter for "StepE" for any execution of "StepE"
          # can be set by using execution label strings "execution_x"
          # as keys where x in "execution_x" is a positive
          # integer >= 1 OR the substring "others". When x is a number
          # it represents the xth execution of the step in the pipeline,
          # and when it is the substring "others", x represents all
          # other executions of the step in the pipeline not explicitly
          # specified by an integer.
          execution_1: file1.dat
          execution_2: file2.dat
          execution_others: file3.dat
```

\[[Home](./toc.md)\] &nbsp;&nbsp;&nbsp; \[[Topics][topics]\]

---
