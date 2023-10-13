html header: <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/9.15.10/styles/a11y-light.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/9.15.10/highlight.min.js"></script>
    <script>hljs.initHighlightingOnLoad();</script>
    <link rel="stylesheet" href="./styles/docstyles.css">
Base Header Level: 2

\[[Home](./toc.md)\]

# PACMO Developer Documentation

## {++Topics++}: [topics]
1. [Overview][topic-1]
2. [Running the PACMO framework][topic-2]
     1. [Listing 1. Simple PACMO execution script][topic-2.1]
     2. [Listing 2. PACMO execution script with external registries][topic-2.2]
3. [The PACMO registry file][topic-3]
     1. [Listing 3. Example PACMO registry file with developer notes][topic-3.1]
     2. [Listing 4. Example PACMO registry file without developer notes][topic-3.2]
4. [Implementing pipeline steps][topic-4]
     1. [Listing 5. Example pipeline step implementation: the `AwesomeStep1` class][topic-4.1]
     2. [Listing 6. Example state element container implementation: the `FooCapsule` class][topic-4.1]
     3. [Listing 7. Example pipeline step implementation: the `AwesomeStep2` class][topic-4.3]
     4. [Listing 8. Example state element container implementation: the `BarPackage` class][topic-4.4]
5. [Error Handling within pipeline steps][topic-5]

---

## 1. Overview [topic-1]

Computational developers who wish to drive their computational workflows or pipelines with PACMO will need to be familiar with the public interfaces of PACMO. PACMO provides an application programmable interface (API) for the Python programming language. The API documentation is available [here](). Additionally, because PACMO expects pipelines and their steps to be declared in a file with YAML syntax referred to as the PACMO registry file in this documentation, the framework expects computational developers to adhere to a structured YAML interface that is described in the PACMO documentation.

PACMO tries to follow the semantic versioning specification, so any changes to PACMO that breaks backwards compatibility of the Python and/or YAML public interfaces will be reflected in the version number. Consequently, computational developers of pipelines and pipeline steps may choose to adjust to any breaking changes to public interfaces introduced by new versions of PACMO. Python applications that consume the PACMO public interfaces and execute PACMO to execute their pipelines will be referred to in this documentation as PACMO-based applications.

PACMO-based applications will need three software components to function: (1) A python script that kickstarts the PACMO framework, (2) a computational modules library that implements all of the 'steps' in a given pipeline in the Python programming language, and (3) a PACMO registry python module that contains the PACMO registry file in YAML. PACMO provides a public interface for each of the three components.

\[[Home](./toc.md)\] &nbsp;&nbsp;&nbsp; \[[Topics][topics]\]

---

## 2. Running the PACMO framework [topic-2]

A PACMO-based application can start PACMO using the `PipelineApplication` class defined in the `pacmo` python module. Below is an example of a python script that starts the PACMO framework.

---

### Listing 1. Simple PACMO execution script [topic-2.1]
```python
from pacmo import PipelineApplication
import my_registry_module

myapp = PipelineApplication(registry_module=my_registry_module)
myapp.run_single_pipeline()
```

---

The above script in [Listing 1][topic-2.1] is sufficient to start PACMO an execute a pipeline. The imported module `my_registry_module` should be a python package that contains the primary PACMO registry file, registry.yaml, where all pipelines and steps involved in pipelines have been defined in YAML, and this file also contains references to python implementations of pipeline steps that PACMO will execute. The PACMO registry file will be covered in the [next section][topic-3]. The `registry_module` keyword argument is mandatory and PACMO will raise an exception if it is not provided. The `PipelineApplication` constructor accepts two other keyword arguments as shown in [Listing 2][topic-2.2].

---

### Listing 2. PACMO execution script with external registries [topic-2.2]
```python
from pacmo import PipelineApplication
import my_registry_module
import another_registry_module
import yet_another_registry_module

external_registries = [another_registry_module, yet_another_registry_module]
myapp = PipelineApplication(
            registry_module=my_registry_module,
            external_modules=external_registries,
            primary_pipeline='MyAwesomePipeline')
myapp.run_single_pipeline()
```

---

The `primary_pipeline` keyword argument to `PipelineApplication` configures PACMO to only allow the execution of a pipeline with a name in the PACMO registry file that matches the value assigned to `primary_pipeline`. As such the `primary_pipeline` keyword argument should be assigned data of type `str`. When the `primary_pipeline` keyword argument is set, PACMO will raise an exception if a pipeline not matching the value of`primary_pipeline` is requested by the user in the user input file. 

The `external_modules` keyword argument should, very simply, be a `list` of python modules that, on disk, are python packages that contain valid PACMO registry files. The purpose of providing a `list` of modules that contain PACMO registry files other than the primary, registry-containing module assigned to the `registry_module` argument is to resolve references in the primary registry file to other registry files. PACMO allows registry files to contain references to pipeline steps that are declared in PACMO registry files that are external to the primary registry file of a given PACMO-based application. This feature will be explained within the developer notes in [Listing 3][topic-3.1].

\[[Home](./toc.md)\] &nbsp;&nbsp;&nbsp; \[[Topics][topics]\]

---

## 3. The PACMO registry file [topic-3]

The PACMO registry file is a configuration file implemented in YAML. The file is required for PACMO to function correctly. PACMO requires the registry file to be placed within a python package directory and requires that the registry file be named "registry.yaml." The registry file contains pipeline definitions, global parameters, pipeline step definitions, and references to input and output python objects associated with pipeline steps. Below in [Listing 3][topic-3.1] is the registry file of the example PACMO-based application that can be found in the PACMO source code repository. The example registry file below contains helpful notes in the form of comments that serve as documentation for how a PACMO registry file should be structured and for how authors of pipelines and pipeline steps can use the registry file to declare their pipeline blueprints and step configuration details.

---

### Listing 3. Example PACMO registry file with developer notes [topic-3.1]
```yaml
# APPLICATION REGISTRY FILE

# GLOBAL PARAMETERS REGISTRY
# NOTE:
# The "global_parameters" key in the mapping node
# below is mandatory in all PACMO registry files.
# It represents global parameters that are made
# available to both implementors of pipeline steps
# and to users of PACMO-based applications.
global_parameters:
  # NOTE:
  # Parameters with a global scope in the application can
  # be defined in the manner shown below. The "output_file"
  # and "error_file" global parameters are mandatory for all
  # PACMO registry files.
  ouput_file: pacmo.out
  error_file: pacmo.log


# PIPELINES REGISTRY
# NOTE:
# The "pipelines_registry" key in the mapping node
# below is mandatory in all PACMO registry files.
# The mapping node below represents the collection of
# pipelines that are made available to users. The
# pipeline configurations are declared here in a
# completely self-contained manner for all users of
# pipelines to study and scrutinize.
pipelines_registry:

  # NOTE:
  # Pipeline definitions are key-value pairs where the
  # key represents the name of the pipeline and the
  # value is mapping node that contains details of the
  # definition of the pipeline.
  ExamplePipeline1:
    # NOTE:
    # All pipeline definitions require the nested mapping
    # node shown below with a single key-value pair where
    # the key is the string "steps" and the value is a
    # sequence node containing information about the steps
    # in the pipeline. The steps in the sequence may be
    # represented by a scalar that represents the name of
    # the step or a mapping node with a single key-value
    # pair where the key is the name of the step.
    steps:
      # NOTE:
      # If a step has no input elements and no default
      # parameters are to be overwritten by the pipeline
      # definition, then declare the step with its name
      # as a string scalar in the sequence in the manner
      # shown below:
      - StepA
      # NOTE:
      # If a step has no input elements but default
      # parameters need to be overwritten in the pipeline
      # definition, then declare as shown below:
      - StepE:
          # NOTE:
          # the "parameters" key is mandatory when default
          # parameters of a step are to be overwritten in
          # the pipeline definition
          parameters:
            input_file: ./stepA_output.ascii
            output_file: e_output.dat
            # NOTE:
            # the above key-value pairs will be read
            # in as a mapping object type in Python. DO NOT
            # DUPLICATE keys with differing values! If you
            # do then only the value from the last occurrence
            # the repeated key will be registered by Python.
            # This general rule applies to ALL MAPPING NODES
            # in the PACMO registry.

  ExamplePipeline2:
    steps:
      # NOTE:
      # If the output of one step is to be read in by another
      # step in the pipeline definition via disk IO within the
      # the current working directory, then it could be
      # accomplished by declaring parameters as shown below:
      - StepA:
          parameters:
            step_a_output_file: a_output.dat
      - StepE:
          parameters:
            input_file: a_output.dat
            output_file: e_output.dat

  ExamplePipeline3:
    steps:
      - StepA:
          parameters:
            parameterA2: GATTACA
      # NOTE:
      # If a step requires and input element, then the
      # step that provides that input element can be
      # declared as shown below:
      - StepB:
          # NOTE:
          # The "element_providers" key is mandatory when
          # declaring the providers for input elements.
          element_providers:
            # NOTE:
            # the below key-value pair indicates that step "StepA"
            # in the pipeline should provide state element
            # "Foo" to step "StepB."
            StepA: Foo
      - StepC:
          element_providers:
            StepB: Bar
            # NOTE:
            # Make sure that steps that provide input
            # elements execute before the steps that
            # need those input elements.

  ExamplePipeline4:
    steps:
      - StepA:
          parameters:
            parameterA2: GATTACA
            # NOTE:
            # Sometimes it is useful to "anchor" some scalar nodes
            # (parameter values) so as to be aliased later in
            # the pipeline somewhere. The anchor is represented by an
            # "&" followed immediately by a label like in the manner
            # shown below:
            step_a_output_file: &some_label ./output_A.ascii
      - StepB:
          element_providers:
            StepA: Foo
      - StepC:
          element_providers:
            StepB: Bar
      # NOTE:
      # Below is an example of a step in the pipeline declaration that
      # has a default parameter overwritten and has an input state
      # element provider step defined:
      - StepC:
          parameters:
            step_c_sequence_param:
              - 10.0
              - mL
          element_providers:
            StepB: Bar
      - StepD:
          parameters:
            # NOTE:
            # anchored parameter values from earlier steps can be
            # aliased later in the pipeline (effectively like a
            # copy/paste) as in the manner shown below:
            step_d_input_file: *some_label
          element_providers:
            StepA: Foo
            # NOTE:
            # if the element provider step executes more than once
            # in the pipeline, then make declarations as shown below:
            StepC:
              # NOTE:
              # The execution key string should be "execution_n" where
              # n is the nth execution of the step that is to provide
              # the input element as in the manner shown below:
              execution_1: Spam
              # NOTE:
              # if a particular execution of a provider step is to
              # provide more than one input element, then declare it
              # as shown below:
              execution_2:
                - Eggs
                - Ham
            StepB: Bar
      - StepC:
          element_providers:
            StepD: Bar
      # NOTE:
      # A step may be declared to run one or more times in a
      # pipeline definition as with step "StepE" below.
      - StepE
      - StepE
      - StepE
      - StepE

  ExamplePipeline5:
    steps:
      - StepA
      # NOTE:
      # PACMO allows registries to reference steps from other
      # external registries as long as the external steps are
      # declared in the full python import syntax that clearly
      # indicates the python package that contains the registry
      # file in which the external step is declared. Steps shown
      # below were originally declared in the registry file within
      # the epcA.reg_a python package and are now part of the 
      # "ExamplePipeline5" pipeline.
      - epcA.reg_a.StepA:
          parameters:
            step_a_output_file: output_from_A.dat
      - epcA.reg_a.StepB:
          parameters:
            step_b_input_file: output_from_A.dat
          element_providers:
            # NOTE:
            # As shown below, the same is also true of state elements
            # that are declared in other registries as in the case
            # of epcA.reg_a.Foo below where it appears as
            # the output state element of epcA.reg_a.StepA
            # and as the input element of ecpA.reg_a.StepB
            # in the external registry imported from epcA.reg_a.
            epcA.reg_a.StepA: epcA.reg_a.Foo


# STEPS REGISTRY
# NOTE:
# The "steps_registry" key in the mapping node below is
# mandatory in all PACMO registry files. The mapping node
# below represents the pipeline steps registry where all
# step configurations are declared. 
steps_registry:

  # NOTE:
  # A step is a key-value pair where the key is
  # the string that represents the name that is to
  # identify the step and the value is a mapping
  # node that contains details about the step.
  StepA:
    # NOTE:
    # The key-value pair below is a requirement of
    # the step registry. Make sure that the value of
    # the key, "class," points to the class implementation
    # of the step and that the value follows the python
    # module import syntax rules.
    class: epc.exampleABD.StepA
    # NOTE:
    # parameters for a step are declared with a key-value
    # pair where the key is the string "parameters" and the
    # value is a mapping node containing one or more key-value
    # pairs.
    parameters:
      # NOTE:
      # parameters are represented by a key-value pair where the
      # key is a string that represents the name of the parameter
      # and the value is either a scalar node of a sequence node.
      # Below the parameter "parameterA1" is mapped to an integer.
      parameterA1: 1
      # NOTE:
      # Parameters may be strings.
      parameterA2: TGTAATC
      # NOTE:
      # String values for parameters can be used to specify
      # file paths.
      step_a_output_file: ./stepA_output.ascii
    # NOTE:
    # State elements that are outputs of a step are declared with
    # a key-value pair where the key is the string "output_elements"
    # and the value is a sequence node.
    output_elements:
      # NOTE:
      # The output state element sequence nodes must be composed
      # of string type scalar nodes only. Make sure that any
      # name declared here is mapped to a container class in the
      # element containers registry.
      - Foo

  StepB:
    class: epc.exampleABD.StepB
    parameters:
      # NOTE:
      # Parameters may be floating point numbers.
      step_b_parameter_1: 2.0e-3
      step_b_input_file: ./stepB_input.ascii
    output_elements:
      - Bar
    # NOTE:
    # If a step required state elements as its input, then
    # that requirement can be declared with a key-value
    # pair where the key is the string "input_elements" and
    # the value is a sequence node containing only string
    # type scalar nodes. Make sure that any name declared here
    # is mapped to a container class in the element containers
    # registry.
    input_elements:
      - Foo

  StepC:
    class: epc.exampleCE.StepC
    parameters:
      step_c_int_param: 32
      # NOTE:
      # It is possible to declare that the value of a parameter
      # be a sequence node (list) like in the manner below:
      step_c_sequence_param:
        - 60.0
        - mg
        # NOTE:
        # The ordering of scalar nodes within the above sequence
        # nodes will be preserved.
    input_elements:
      - Bar
    # NOTE:
    # A step may output more than one state element.
    output_elements:
      - Spam
      - Eggs
      - Ham

  StepD:
    # NOTE:
    # A step can be implemented as a subclass of an already
    # existing step class. When this is the case, the
    # child class inherits all of the parameters, input state
    # elements, and output state elements of the parent step
    # class. While parameters don't have to be redeclared in
    # registry entry of the child step, all input and output
    # state elements that are inherited will have to be
    # redeclared in the the child step's registry entry.
    class: epc.exampleABD.StepBChild
    parameters:
      step_b_parameter_1: -3.13
      # NOTE:
      # Sometimes parameter will need to be acquired from the
      # user input file. In these cases, a parameter can be
      # initialized to a string that the step recognizes and
      # that signifies that the parameter has not been
      # initialized by the user. If that string in encountered
      # during runtime, the step can take appropriate action
      # to let the user know.
      step_d_input_file: replace_me
    input_elements:
      - Foo
      - Bar
      - Spam
      - Eggs
      - Ham
    # NOTE:
    # A step may output any state element that is registered
    # in the element container registry, even ones that are
    # inputs to the step.
    output_elements:
      - Foo
      - Bar
      - Spam
      - Eggs
      - Ham

  StepE:
    # NOTE:
    # The name of the step class does not necessarily have to
    # match the name of the step, but there cannot be more than
    # one step name for a step class.
    class: epc.exampleCE.StepDiskIO
    parameters:
      input_file: stepE_input.dat
      output_file: stepE_output.dat


# STATE ELEMENTS REGISTRY
# NOTE:
# The key-value pair in the mapping node below
# represents the element containers registry. Every
# state element object that is produced by any
# step in the step registry requires an associated
# element container class to be implemented.
element_containers_registry:
  # NOTE:
  # The state element to element container class
  # relationships are registered as key-value
  # pairs where the key is a string that represents
  # the name of the state element and the value
  # is a string that represents the element container
  # class for the state element. Make sure that the 
  # values follow the python module import syntax rules.
  # The declaration of the element container registry is
  # mandatory when any step in the steps registry
  # produces state element objects for other steps to
  # consume.
  Foo: epc.elements.example.FooCapsule
  Bar: epc.elements.example.BarPackage
  Spam: epc.elements.example.SpamTin
  Eggs: epc.elements.example.EggCarton
  Ham: epc.elements.example.CanOfHam
```

---

The example registry file above contains five example pipelines that demonstrate the various pipeline designs that are possible with the PACMO framework. Also shown are five pipeline step declarations that can serve as references for computational developers looking to develop their own pipeline steps. An important concept to note from the commented documentation in the registry file above is the concept of a state element. A state element is any python object that steps make available to other steps. PACMO provides pipeline step developers with API methods to read and publish such state state elements during execution within a given pipeline. The concept of state elements are explained in the [next section][topic-4]. The full registry file from [Listing 3][topic-3.1] is re-listed in [Listing 4][topic-3.2] without the commented developer notes for clarity.

\[[Home](./toc.md)\] &nbsp;&nbsp;&nbsp; \[[Topics][topics]\]

---

### Listing 4. Example PACMO registry file without developer notes [topic-3.2]
```yaml
# APPLICATION REGISTRY FILE

# GLOBAL PARAMETERS REGISTRY
global_parameters:
  output_file: pacmo.out
  error_file: pacmo.err


# PIPELINES REGISTRY
pipelines_registry:

  ExamplePipeline1:
    steps:
      - StepA
      - StepE:
          parameters:
            input_file: ./stepA_output.ascii
            output_file: e_output.dat

  ExamplePipeline2:
    steps:
      - StepA:
          parameters:
            step_a_output_file: a_output.dat
      - StepE:
          parameters:
            input_file: a_output.dat
            output_file: e_output.dat

  ExamplePipeline3:
    steps:
      - StepA:
          parameters:
            parameterA2: GATTACA
      - StepB:
          element_providers:
            StepA: Foo
      - StepC:
          element_providers:
            StepB: Bar

  ExamplePipeline4:
    steps:
      - StepA:
          parameters:
            parameterA2: GATTACA
            step_a_output_file: &some_label ./output_A.ascii
      - StepB:
          element_providers:
            StepA: Foo
      - StepC:
          element_providers:
            StepB: Bar
      - StepC:
          parameters:
            step_c_sequence_param:
              - 10.0
              - mL
          element_providers:
            StepB: Bar
      - StepD:
          parameters:
            step_d_input_file: *some_label
          element_providers:
            StepA: Foo
            StepC:
              execution_1: Spam
              execution_2:
                - Eggs
                - Ham
            StepB: Bar
      - StepC:
          element_providers:
            StepD: Bar
      - StepE
      - StepE
      - StepE
      - StepE

  ExamplePipeline5:
    steps:
      - StepA
      - epcA.reg_a.StepA:
          parameters:
            step_a_output_file: output_from_A.dat
      - epcA.reg_a.StepB:
          parameters:
            step_b_input_file: output_from_A.dat
          element_providers:
            epcA.reg_a.StepA: epcA.reg_a.Foo


# STEPS REGISTRY
steps_registry:

  StepA:
    class: epc.exampleABD.StepA
    parameters:
      parameterA1: 1
      parameterA2: TGTAATC
      step_a_output_file: ./stepA_output.ascii
    output_elements:
      - Foo

  StepB:
    class: epc.exampleABD.StepB
    parameters:
      step_b_parameter_1: 2.0e-3
      step_b_input_file: ./stepB_input.ascii
    output_elements:
      - Bar
    input_elements:
      - Foo

  StepC:
    class: epc.exampleCE.StepC
    parameters:
      step_c_int_param: 32
      step_c_sequence_param:
        - 60.0
        - mg
    input_elements:
      - Bar
    output_elements:
      - Spam
      - Eggs
      - Ham

  StepD:
    class: epc.exampleABD.StepBChild
    parameters:
      step_b_parameter_1: -3.13
      step_d_input_file: replace_me
    input_elements:
      - Foo
      - Bar
      - Spam
      - Eggs
      - Ham
    output_elements:
      - Foo
      - Bar
      - Spam
      - Eggs
      - Ham

  StepE:
    class: epc.exampleCE.StepDiskIO
    parameters:
      input_file: stepE_input.dat
      output_file: stepE_output.dat


# STATE ELEMENTS REGISTRY
element_containers_registry:
  Foo: epc.elements.example.FooCapsule
  Bar: epc.elements.example.BarPackage
  Spam: epc.elements.example.SpamTin
  Eggs: epc.elements.example.EggCarton
  Ham: epc.elements.example.CanOfHam
```

\[[Home](./toc.md)\] &nbsp;&nbsp;&nbsp; \[[Topics][topics]\]

---

## 4. Implementing pipeline steps [topic-4]

In the previous section, documentation was provided to show the manner in which a pipeline step may be registered into a PACMO registry file. The class implementation of the pipeline step, the parameters required by the step, the input and output state elements associated with the step were all declared in the PACMO registry file. This section will demonstrate how the python implementation of the pipeline step reflects the declarations made in the registry file.

Pipeline steps are implemented within a computational modules library in the Python programming language. In short, it is just another python package that has a dependency on the python package that contains the relevant registry file and on the PACMO python package. Since PACMO takes on the responsibility of orchestrating and executing all the steps that are defined for a given pipeline definition in the pipeline registry, it is not necessary to implement entire pipelines within a computational modules (or "steps") library. The computational modules library should only be concerned with the implementation of reusable, modularized, pipeline steps using the Python programming language and the public interfaces of PACMO. Authors of the associated registry file must ensure that declarations of parameters, state elements, and location of python classes are all accurately reflected and match the implementation details in the steps library.  

All pipeline steps are ultimately python class objects. PACMO will read the registry file and look for references to python class objects that implement a given pipeline step. Therefore, the first requirement for PACMO to properly recognize and execute a pipeline step is the listing of a python class with proper python module import syntax within the steps registry section of the registry file. The second requirement is for the python class referenced in the registry file to be a child class of the `pacmo.common.Step` class or any of its subclasses. The third requirement is for the inheriting class to call the constructor method (`__init__`) of `pacmo.common.Step`. When the above three requirements are met, PACMO ensures that the python class will inherit useful attributes and methods that will enable its instance objects to function properly within a pipeline. [Listing 5][topic-4.1] below shows an example of a pipeline step implementation.

---

### Listing 5. Example pipeline step implementation: the `AwesomeStep1` class [topic-4.1]
```python
from pacmo.common import Step
from pacmo.error import InputParameterError
from epc.elements.example import FooCapsule

class AwesomeStep1(Step):

    def __init__(self, state):
        super().__init__(state)

    def execute(self):
        self.extend_output('Executing step: ' + self.name)
        self.logger.info(' parameter1: ' + str(self.config.parameter1))
        self.logger.info(' parameter2: ' + str(self.config.parameter2))
        foo = ("state element Foo",)
        self.extend_output('Foo: ' + str(foo))
        capsule = FooCapsule(foo)
        self.ship_element('Foo', capsule)

    def check(self):
        try:
            assert isinstance(self.config.parameter1, str)
            assert isinstance(self.config.parameter2, int)
            assert self.config.parameter2 < 100
            assert len(self.config.parameter1) > 3 
        except AssertionError:
            raise InputParameterError(
                'Incorrect input parameter')
```

---

The class `AwesomeStep1` in the example above is a child class of `pacmo.common.Step` and it calls the constructor of `pacmo.common.Step` with the positional argument `state`. The variable name of this positional argument is not important, and PACMO will make sure that it is a properly initialized instance of `pacmo.common.State`, which is a class from the PACMO framework that allows `pacmo.common.Step` instances to pass references of python objects to each other. Once initialized, `Step` instances will have access to all of the parameters declared in the steps registry section of the associated PACMO registry file through the `Step.config` instance attribute. In the example above, instances of `Step` access the values of parameters declared in the registry file by simply de-referencing them using the name of the parameter from the `Step.config` instance attribute, e.g. `self.config.parameter1` and `self.config.parameter2` in the above example.

`Step` instances can access the registered name of the pipeline step from the PACMO registry file through the `Step.name` instance attribute. `Step` instances can redirect formatted text output to the PACMO output file by calling the `Step.extend_output` instance method and can redirect event logs using the python standard library `logging.Logger` class instance that is made available via the `Step.logger` instance attribute.

The two methods shown in [the above example][topic-4.1], `execute` and `check`, are inherited by `AwesomeStep1` from `pacmo.common.Step` and are overwritten to contain the logic needed to execute the pipeline step. PACMO recognizes only these two methods and will execute them both when processing a given pipeline. Specifically, the `check` methods for all steps in a given pipeline are executed ahead of the `execute` methods for all steps in that pipeline. For this reason, developers of pipeline steps should execute the set of statements that comprises the computational work performed by a pipeline step through the `execute` method and perform all possible error checking through the `check` method so that a pipeline that has been configured incorrectly can fail gracefully before the bulk of the computational work has begun to execute via the `execute` method. In the example above, instances of `AwesomeStep` will raise an exception and halt execution of PACMO if `self.config.parameter1` and `self.config.parameter2` fail the assertions listed in the `check` method given that `AwesomeStep1` is part of the pipeline chosen by the user. This mechanism gives developers of pipeline steps to check for many of the conditions that are required to be present in the application configuration and computing environment for their pipeline steps to execute without error before the pipeline begins executing in earnest. It should be emphasized here that the above example in [Listing 5][topic-4.1] is rudimentary. In practice, pipeline step developers may employ any number of python objects, i.e. class instance methods, module functions, other class instances, other Python libraries etc. through the `check` and `execute` methods to accomplish their computational objectives. 

`Step` instances can choose to make Python objects available to other `Step` instances in a pipeline. In-memory Python objects that pipeline steps share with each other are referred to as "state elements" within the PACMO framework. `Step` instances can share state elements by making use of the `Step.ship_element` instance method. This method accepts two positional arguments. The first argument is the name of the state element that the step intends to share. In [Listing 5][topic-4.1], the state element name is "Foo." The second argument to `Step.ship_element` is an instance of an "element container class" associated with state element "Foo." PACMO requires all state elements to have a subclass of the `pacmo.common.ElementContainer` class associated with them. In the example above, the container class employed by `AwesomeStep1` is `epc.elements.example.FooCapsule`, which inherits from `pacmo.common.ElementContainer`. The element container class and the state element that it should contain should be registered in the state element registry section of the PACMO registry file. The PACMO registry file shown in [Listings 3][topic-3.1] and again in [Listing 4][topic-3.2] contains declarations for state element "Foo" and its container class `epc.elements.Example.FooCapsule`. The implementation of `epc.elements.example.FooCapsule` is shown below in [Listing 6][topic-4.2].

---
 
### Listing 6. Example state element container implementation: the `FooCapsule` class [topic-4.2]
```python
from pacmo.common import ElementContainer
from pacmo.error import ElementValidationError

class FooCapsule(ElementContainer):

    def __init__(self, element_obj):
        super().__init__(element_obj)
        self.foo = self.get_element()

    def validate_contents(self):
        try:
            assert isinstance(self.foo, tuple)
        except AssertionError:
            raise ElementValidationError(
                'element Foo must be an instance of tuple')
```

---

The purpose of using `ElementContainer` instances to share state elements is to give the original author of a given state element a mechanism for validating the data structure of that state element regardless of which `Step` instance subsequently produces or consumes that state element. State element creators can author a subclass of `ElementContainer` for a specific state element, and with it, they can essentially dictate the data structure of that state element via the `ElementContainer.validate_contents` instance method. This ensures homogeneity in the structure of a given state element across all pipelines and pipeline steps driven by PACMO. Subclasses of `ElementContainer` can get a reference to the state element object by calling the `ElementContainer.get_element` instance method and can override the `validate_contents` instance method with validation logic that asserts the intended data structure of the state element. As shown in the [example above][topic-4.2], the element container class `FooCapsule` expects the state element object passed into it to be of type `tuple`, else it will raise an exception and halt all execution. Therefore, `AwesomeStep1` in [Listing 5][topic-4.1], must ensure that the object it uses to instantiate `FooContainer` must be an object of type `tuple`. Only then will `AwesomeStep1` be able to share the object it has assigned to `foo` with other pipeline steps via the `Step.ship_element` instance method.

Pipeline steps can also declare any registered state element as a requirement of its use within a pipeline in the PACMO registry file, e.g. see steps `StepB`, `StepC`, and `StepD` in [Listing 4][topic-3.2] above. Pipeline steps that require state elements as input can get a reference to the state element object that they require for execution using the `Step.fetch_input` instance method. This method accepts one positional argument that is a string representation of the registered state element name. This is illustrated in the Python implementation of `AwesomeStep2`, shown below in [Listing 7][topic-4.3]. The pipeline step `AwesomeStep2` in the example below consumes state element "Foo" as input and produces state element "Bar" for other steps to use. For completeness, the element container class for state element "Bar" is shown in [Listing 8][topic-4.4].

---

### Listing 7. Example pipeline step implementation: the `AwesomeStep2` class [topic-4.3]
```python
from pacmo.common import Step
from epc.elements.example import BarPackage
from pacmo.error import InputParameterError

class AwesomeStep2(Step):

    def __init__(self, state):
        super().__init__(state)

    def execute(self):
        input_foo = self.fetch_input('Foo')
        self.extend_output('Executing step: ' + self.name)
        self.logger.info(' parameterA: ' + str(self.config.parameterA))
        self.logger.info(' parameterB: ' + str(self.config.parameterB))
        self.logger.info(' Foo: ' + str(input_foo))
        bar = {'stepB_output': 200}
        package = BarPackage(bar)
        self.ship_element('Bar', package)

    def check(self):
        try:
            assert isinstance(self.config.parameterA, float)
            assert 2.0 <= self.config.parameterA < 10.0
        except AssertionError:
            raise InputParameterError(
                'Incorrect input parameter')
```

---

### Listing 8. Example state element container implementation: the `BarPackage` class [topic-4.4]
```python
from pacmo.common import ElementContainer
from pacmo.error import ElementValidationError


class BarPackage(ElementContainer):

    def __init__(self, element_obj):
        super().__init__(element_obj)
        self.element = self.get_element()

    def validate_contents(self):
        try:
            assert isinstance(self.element, dict)
        except AssertionError:
            raise ElementValidationError(
                'element Bar must be an instance of dict')
```

\[[Home](./toc.md)\] &nbsp;&nbsp;&nbsp; \[[Topics][topics]\]

---

## Error handling within pipeline steps [topic-5]

PACMO contains a number of exceptions within the `pacmo.error` module that steps can raise when encountering errors during execution. The `pacmo.error.InputParameterError` can be raised if there are errors associated with input parameters to pipeline steps. The generic `pacmo.error.StepExecutionError` and `pacmo.error.StepCheckError` can be raised for errors encountered during the execution of `Step.execute` and `Step.check` methods respectively. Alternatively, computational developers can create their own exceptions classes that inherit from `StepExecutionError` and `StepCheckError`. Creators of element container classes can raise the `pacmo.error.ElementValidationError` if state element objects fail validation assertions. In all cases of errors that are explicitly handled by developers of PACMO-based applications, it is recommended that developers directly raise the following exceptions or custom exceptions that are subclasses of the following exception classes: `pacmo.error.Error`, `pacmo.error.StepExecutionError`, `pacmo.error.StepCheckError`, `pacmo.error.InputParameterError`, and `pacmo.error.ElementValidationError`. Adhering to this convention will make it easier for developers of PACMO and PACMO-based applications to distinguish between anticipated errors and unexpected errors as the unexpected errors will appear as exceptions from the Python standard library.

\[[Home](./toc.md)\] &nbsp;&nbsp;&nbsp; \[[Topics][topics]\]

---
