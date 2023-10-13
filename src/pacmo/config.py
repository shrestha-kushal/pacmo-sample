"""
The `pacmo.config` module contains python object definitions
that are essential to the processing of configurable
parameters in the application registry file and the user
input file. They ensure `pacmo.common.Pipeline` objects are
configured correctly during application runtime.
"""


import importlib
import os
import pkgutil
import re
from collections import namedtuple
import yaml
from .error import ApplicationRegistryError
from .error import GlobalsRegistryError
from .error import UserConfigurationError
from .error import IncorrectArgumentType
from .error import PipelinesRegistryError
from .error import StepsRegistryError
from .error import StepNotFoundError
from .error import ElementsRegistryError
from .error import ElementPrefixError
import logging
import inspect


INPUT_FILENAME = "user_input.yaml"
"""
`INPUT_FILENAME` is a module level constant of type str
that specifies the accepted name of the input file for
the application.
"""
WORK_DIRECTORY = os.getcwd()
"""
`WORK_DIRECTORY` is a module level constant of type str
that specifies the path of the working directory during
execution of the application.
"""
REGISTRY_FILENAME = "registry.yaml"
"""
`REGISTRY_FILENAME` is a module level constant of type str
that specifies the accepted name of the application 
registry file.
"""
CHECKPOINT_FILENAME = "pipeline.pickle"
"""
The `CHECKPOINT_FILENAME` module level constant is currently
not in use.
"""
mod_log = logging.getLogger(__name__)
mod_log.addHandler(logging.NullHandler())


class InputReader(object):
    """
    Objects of type `InputReader` read in a yaml file named
    `INPUT_FILENAME` in the `WORK_DIRECTORY` as a python
    dictionary and make this dictionary available to other
    objects.
    """

    def __init__(self):
        _user_config_path = os.path.join(WORK_DIRECTORY, INPUT_FILENAME)
        self._user_input_map = load_yaml(_user_config_path)

    def get_user_input_map(self):
        """
        This method returns a dictionary object that represents the
        contents of file `INPUT_FILENAME`.

        ### Returns:
        - [`dict`][1] object

        [1]: https://docs.python.org/3/tutorial/datastructures.html#dictionaries
        """
        return self._user_input_map


class RegistryReader(object):
    """
    `RegistryReader` instances read in the application registry file
    named `REGISTRY_FILENAME` and make the contents of the global
    parameters registry, the pipelines registry, and the steps
    registry available to other objects.
    """

    def __init__(self, registry_module, external_modules):
        """
        ### Raises:
        - `pacmo.error.ApplicationRegistryError`: this exception's
         message will describe errors relating to the content of
         the application registry file, `REGISTRY_FILENAME`, as it
         relates to parsing and general node structure of the registry
         nodes in that file.
        """
        self._registry_module = registry_module
        self._registry_yaml_map = self._get_registry_map()
        self._external_modules = external_modules
        self._external_maps = self._get_external_registries()
        self._pipelines_map = self._get_pipelines_map()
        self._steps_map = self._get_steps_map()
        self._augment_steps_map()
        self._global_vars_map = self._get_globalvars_map()
        self._elements_map = self._get_elements_map()
        self._augment_elements_map()

    def get_global_vars_map(self):
        """
        Returns a dictionary of global parameters

        ### Returns:
        - [`dict`][1] object

        [1]: https://docs.python.org/3/tutorial/datastructures.html#dictionaries
        """
        return self._global_vars_map

    def get_pipelines_map(self):
        """
        This method makes the pipeline registry available as a
        nested built-in data types useful for further processing.

        ### Returns:
        - [`list`][2] of [`dict`][1]s

        [1]: https://docs.python.org/3/tutorial/datastructures.html#dictionaries
        [2]: https://docs.python.org/3/library/stdtypes.html#list
        """
        return self._pipelines_map

    def get_steps_map(self):
        """
        This method makes the steps registry available to other
        objects as a [`list`][2] of nested, built-in data types
        that is useful for further processing.

        ### Returns:
        - [`list`][2] of [`dict`][1]s

        [1]: https://docs.python.org/3/tutorial/datastructures.html#dictionaries
        [2]: https://docs.python.org/3/library/stdtypes.html#list
        """
        return self._steps_map

    def get_elements_map(self):
        """
        This method returns the state elements registry as a
        [`dict`][1] object.

        ### Returns:
        - [`dict`][1] object; deserialized elements registry

        [1]: https://docs.python.org/3/tutorial/datastructures.html#dictionaries
        """
        return self._elements_map

    def _get_registry_map(self):
        if not inspect.ismodule(self._registry_module):
            raise ApplicationRegistryError(
                'Object "' + str(self._registry_module) +
                '" is not a module instance.')
        registry_map = self._read_yaml_registry(self._registry_module)
        return registry_map

    @staticmethod
    def _read_yaml_registry(module):
        filename = REGISTRY_FILENAME
        try:
            file_bytes = pkgutil.get_data(module.__name__, filename)
        except Exception:
            raise ApplicationRegistryError(
                "registry file \"" + filename + "\" not found.")
        try:
            yaml_map = yaml.load(file_bytes, Loader=yaml.FullLoader)
        except Exception:
            raise ApplicationRegistryError(
                "unable to load \"" + filename + "\" into memory.")
        return yaml_map

    def _get_external_registries(self):
        if not type(self._external_modules) is list:
            raise ApplicationRegistryError(
                'External registry modules must be supplied ' +
                'as a list object.')
        registries = []
        for module in self._external_modules:
            if not inspect.ismodule(module):
                raise ApplicationRegistryError(
                    'Object "' + str(module) +
                    '" is not a module instance.')
            registry_map = self._read_yaml_registry(module)
            registries.append(registry_map)
        return registries

    def _get_pipelines_map(self):
        try:
            pipeline_maps = self._registry_yaml_map["pipelines_registry"]
        except Exception:
            raise ApplicationRegistryError(
                "pipeline registry not found")
        if type(pipeline_maps) is not dict:
            raise ApplicationRegistryError(
                "pipeline_registry must a mapping node")
        if len(pipeline_maps) == 0:
            raise ApplicationRegistryError(
                "no pipelines in pipeline registry")
        return pipeline_maps

    def _get_steps_map(self):
        try:
            steps_map = self._registry_yaml_map["steps_registry"]
        except Exception:
            raise ApplicationRegistryError(
                "step registry not found")
        if type(steps_map) is not dict:
            raise ApplicationRegistryError(
                "\"steps_registry\" node must be a mapping node")
        if len(steps_map) == 0:
            raise ApplicationRegistryError(
                "no steps in step registry")
        for step_name in steps_map:
            steps_map[step_name]['element_prefix_4dc58d02'] = ''
        return steps_map

    def _augment_steps_map(self):
        for i, registry_map in enumerate(self._external_maps):
            try:
                steps_map = registry_map["steps_registry"]
            except Exception:
                raise ApplicationRegistryError(
                    'step registry not found in external registry')
            if type(steps_map) is not dict:
                raise ApplicationRegistryError(
                    '"steps_registry" node in external registry ' +
                    ' must be a mapping node')
            if len(steps_map) == 0:
                raise ApplicationRegistryError(
                    "no steps in external step registry")
            for step_name in steps_map:
                if type(step_name) is not str:
                    raise StepsRegistryError(
                        "Every step name in external step registry must of type str")
                new_step_name = self._external_modules[i].__name__ + '.' + step_name
                if new_step_name in list(self._steps_map.keys()):
                    raise ApplicationRegistryError(
                        'Step name "' + new_step_name +
                        '" occurs more than once. Step names must be unique.')
                step_map = steps_map[step_name]
                step_map: dict
                step_map.update(
                    {'element_prefix_4dc58d02': self._external_modules[i].__name__ + '.'}
                )
                self._steps_map[new_step_name] = step_map

    def _get_globalvars_map(self):
        try:
            param_map = self._registry_yaml_map["global_parameters"]
        except Exception:
            raise ApplicationRegistryError(
                "Global parameters node not found in registry yaml file")
        return param_map

    def _get_elements_map(self):
        try:
            elements_map = self._registry_yaml_map["element_containers_registry"]
        except Exception:
            raise ApplicationRegistryError(
                '"state_elements" mapping node missing in application ' +
                'registry file')
        if type(elements_map) is not dict:
            raise ApplicationRegistryError(
                'The value of a the "state_elements" key in the ' +
                'application registry file must be a mapping node.')
        return elements_map

    def _augment_elements_map(self):
        for i, registry_map in enumerate(self._external_maps):
            try:
                elements_map = registry_map["element_containers_registry"]
            except Exception:
                raise ApplicationRegistryError(
                    '"state_elements" mapping node missing in application ' +
                    'registry file')
            if type(elements_map) is not dict:
                raise ApplicationRegistryError(
                    'The value of a the "state_elements" key in the ' +
                    'application registry file must be a mapping node.')
            for element_name in elements_map:
                if type(element_name) is not str:
                    raise ElementsRegistryError(
                        'All keys in external state element registry must be of type str')
                new_element_name = self._external_modules[i].__name__ + '.' + element_name
                if new_element_name in list(self._elements_map.keys()):
                    raise ApplicationRegistryError(
                        'Element name "' + new_element_name +
                        '" occurs more than once. Element names must be unique.')
                element_value = elements_map[element_name]
                self._elements_map[new_element_name] = element_value


class GlobalVarProvider(object):
    """
    Object of type `GlobalVarProvider` make global variables
    declared in the application registry file with file name
    `REGISTRY_FILENAME` to other objects.
    """

    def __init__(self, global_vars_map):
        """
        ### Arguments:
        - `global_vars_map`:  [`dict`][1] object containing global
        parameters for the application usually acquired from an
        instance of `RegistryReader`.

        ### Raises:
        - `pacmo.error.GlobalsRegistryError`: this exception is raised by
        instances of this class when they catch errors in the content of
        the global parameters registry in the application registry file
        with name `REGISTRY_FILENAME`.

        [1]: https://docs.python.org/3/tutorial/datastructures.html#dictionaries
        """
        self._vars_map = global_vars_map
        self._check_vars_map()
        self._init_vars_map()

    def _check_vars_map(self):
        if self._vars_map is None:
            raise GlobalsRegistryError(
                '"global_parameters" node must not be undefined')
        if type(self._vars_map) is not dict:
            raise GlobalsRegistryError(
                "\"global_parameters\" node must be a mapped node or None object")
        param_names = list(self._vars_map.keys())
        for param_name in param_names:
            if type(param_name) is not str:
                raise GlobalsRegistryError(
                    "global parameter names in registry must be of type str")
            param_value = self._vars_map[param_name]
            if param_value is None:
                raise GlobalsRegistryError(
                    "global parameter value in registry cannot be undefined")
            if type(param_value) is dict:
                raise GlobalsRegistryError(
                    "global parameter value cannot be a structured node")
            if type(param_value) is list:
                for list_elem in param_value:
                    if type(list_elem) is dict:
                        raise GlobalsRegistryError(
                            'sequence global parameters must not have ' +
                            'nested mapped nodes.')
        if not {'output_file', 'error_file'}.issubset(set(param_names)):
            raise GlobalsRegistryError(
                'Global parameters "output_file" and ' +
                '"input_file" must be defined')

    def _init_vars_map(self):
        if self._vars_map is None:
            self._vars_map = {}

    def get_var_names(self):
        """
        Returns global variable names.

        ### Returns:
        - [`list`][2] of `str` objects

        [2]: https://docs.python.org/3/library/stdtypes.html#list
        """
        return [key for key in self._vars_map]

    def get_global_var(self, var_name):
        """
        Returns the object that represents the global variable with
        name `var_name`.

        ### Arguments:
        - `var_name`: `str` object

        ### Returns:
        - a python object that represents the global parameter OR
        `None` if global parameter with name `var_name` is not
        found
        """
        if var_name in list(self._vars_map.keys()):
            value = self._vars_map[var_name]
        else:
            value = None
        return value


class UserDelegate(object):
    """
    Objects of type `UserDelegate` make user input from the
    input yaml file with name, `INPUT_FILENAME`, available to
    other objects.
    """

    def __init__(self, user_input_map, primary_registry, external_registries):
        """
        ### Arguments:
        - `user_input_map`: a [`dict`][1] containing user input
        usually obtained from an instance of `InputReader`.

        ### Raises:
        - `pacmo.error.UserConfigurationError` : the message of
        this exception will attempt to point out errors in the
        content of the user input yaml file named `INPUT_FILENAME`.

        [1]: https://docs.python.org/3/tutorial/datastructures.html#dictionaries
        """
        self._user_input = user_input_map
        self._defined_nodes = self._get_defined_nodes()
        self._pipeline_pick, self._chk_flag = self._parse_essentials()
        self._restart_flag, self._restart_step,\
            self._restart_ordinal, self._restart_path = self._parse_restart()
        self._globals_map = self._parse_global_config()
        self._pipeline_params_map = self._parse_pipeline_config()
        self._add_ordinals()
        self._primary_registry = primary_registry
        self._external_registries = external_registries

    def _get_defined_nodes(self):
        if type(self._user_input) is not dict:
            raise UserConfigurationError(
                "input file must only contain mapped nodes")
        defined_nodes = list(self._user_input.keys())
        for node in defined_nodes:
            if type(node) is not str:
                raise UserConfigurationError(
                    "all keys in input file must be of type str")
        return defined_nodes

    def _parse_essentials(self):
        try:
            pipeline = self._user_input["chosen_pipeline"]
        except Exception:
            raise UserConfigurationError(
                "input file must contain \"chosen_pipeline\" node")
        if type(pipeline) is not str:
            raise UserConfigurationError(
                "chosen pipeline value in input file must be of type str")
        # Disabling this feature as the idea is not mature yet
        self._user_input["checkpoint"] = False
        try:
            checkpoint = self._user_input["checkpoint"]
        except Exception:
            raise UserConfigurationError(
                "Input file must contain \"checkpoint\" node")
        if type(checkpoint) is not bool:
            raise UserConfigurationError(
                "\"checkpoint\" node only accepts boolean values")
        return pipeline, checkpoint

    # this method is called but currently not in use
    def _parse_restart(self):
        if "restart" in self._defined_nodes:
            restart_map = self._user_input["restart"]
            if type(restart_map) is not dict:
                raise UserConfigurationError(
                    "\"restart\" node must have sub nodes")
            try:
                restart_flag = restart_map["flag"]
            except Exception:
                raise UserConfigurationError(
                    "\"restart\" node must have \"flag\" sub node")
            if type(restart_flag) is not bool:
                raise UserConfigurationError(
                    "\"flag\" must be mapped to boolean")
            restart_keys = list(restart_map.keys())
            try:
                restart_path = restart_map["path"]
            except Exception:
                raise UserConfigurationError(
                    "restart path must be provided when restart flag is set")
            if type(restart_path) is not str:
                raise UserConfigurationError(
                    "restart path must be of type str")
            restart_path = os.path.abspath(restart_path)
            if not os.path.exists(restart_path):
                raise UserConfigurationError(
                    "restart path does not point to a valid directory")
            if "step" in restart_keys:
                restart_step = restart_map["step"]
                if type(restart_step) is not str:
                    raise UserConfigurationError(
                        "restart step in input file must be of type str")
                try:
                    restart_ordinal = restart_map["ordinal"]
                except Exception:
                    raise UserConfigurationError(
                        "\"step\" and \"ordinal\" must appear together in restart node")
                if type(restart_ordinal) is not int:
                    raise UserConfigurationError(
                        "restart step ordinal must be of type int")
                if restart_ordinal < 1:
                    raise UserConfigurationError(
                        "restart step ordinal must be greater than or equal to 1")
            else:
                restart_step = None
                restart_ordinal = None
        else:
            restart_flag = False
            restart_step = None
            restart_ordinal = None
            restart_path = None
        return restart_flag, restart_step, restart_ordinal, restart_path

    def _parse_global_config(self):
        if "global_config" in self._defined_nodes:
            global_config_map = self._user_input["global_config"]
            if type(global_config_map) is not dict:
                raise UserConfigurationError(
                    "\"global_config\" node in input file must have sub nodes")
            try:
                global_param_map = global_config_map["parameters"]
            except Exception:
                raise UserConfigurationError(
                    "\"global_config\" node in input" +
                    " file must contain \"parameters\" sub node")
            if type(global_param_map) is not dict:
                raise UserConfigurationError(
                    "parameters value for global_config in" +
                    " input file must be a mapped sub node")
            if type(global_param_map) is dict:
                for global_param_name in global_param_map.keys():
                    if type(global_param_name) is not str:
                        raise UserConfigurationError(
                            "global parameter names in input file must be of type str")
                    global_param = global_param_map[global_param_name]
                    if type(global_param) is dict:
                        raise UserConfigurationError(
                            "global parameter in input file cannot be a mapped node")
                    if type(global_param) is list:
                        raise UserConfigurationError(
                            "global parameter in input file cannot be a sequence node")
        else:
            global_param_map = {}
        return global_param_map

    def _parse_pipeline_config(self):
        if "pipeline_config" in self._defined_nodes:
            all_step_names = []
            pipeline_params_map = {}
            pipeline_config_list = self._user_input["pipeline_config"]
            if type(pipeline_config_list) is not list:
                raise UserConfigurationError(
                    "\"pipeline_config\" node value must be a sequence node")
            pipeline_step_maps = [item for item in pipeline_config_list if item is not None]
            if len(pipeline_step_maps) == 0:
                raise UserConfigurationError(
                    "at least one step must be configured in \"pipeline_config\" node")
            for step_config_map in pipeline_step_maps:
                if type(step_config_map) is not dict:
                    raise UserConfigurationError(
                        "pipeline step configuration nodes must be mapped nodes")
                step_name_list = [key for key in step_config_map.keys()]
                if len(step_name_list) != 1:
                    raise UserConfigurationError(
                        "steps in input file must only have one name")
                step_name = step_name_list[0]
                if type(step_name) is not str:
                    raise UserConfigurationError(
                        "step names in input file must be of type str")
                all_step_names.append(step_name)
                if len(set(all_step_names)) < len(all_step_names):
                    raise UserConfigurationError(
                        "Duplicate step \""+step_name+"\" found in input file")
                try:
                    step_param_map = step_config_map[step_name]["parameters"]
                except Exception:
                    raise UserConfigurationError(
                        'step "' + step_name + '" must have \"parameters\" node')
                other_configs = [key for key in step_config_map[step_name] if key != "parameters"]
                if len(other_configs) != 0:
                    raise UserConfigurationError(
                        "only \"parameters\" sub node allowed " +
                        "in input file for step configurations")
                if type(step_param_map) is not dict:
                    raise UserConfigurationError(
                        'Value of "parameters" key for a step must be ' +
                        'a mapping node')
                for param_name in step_param_map.keys():
                    if type(param_name) is not str:
                        raise UserConfigurationError(
                            "step parameter names in input file must be of type str")
                    param_value = step_param_map[param_name]
                    if param_value is None:
                        raise UserConfigurationError(
                            "step parameters in input file must not have empty or None value")
                    if type(param_value) is list:
                        for sub_param in param_value:
                            if type(sub_param) is dict:
                                raise UserConfigurationError(
                                    "Sequenced sub parameter values in input file cannot be mapped nodes")
                    if type(param_value) is dict:
                        occurrence_labels = list(param_value.keys())
                        if len(occurrence_labels) == 0:
                            raise UserConfigurationError(
                                "mapped node parameter values in input" +
                                " file must provide execution labels")
                        if len(set(occurrence_labels)) < len(occurrence_labels):
                            raise UserConfigurationError(
                                "execution labels for a given parameter cannot be duplicated")
                        for occurrence_label in occurrence_labels:
                            if type(occurrence_label) is not str:
                                raise UserConfigurationError(
                                    "execution labels for step parameters" +
                                    " in input file must be of type str")
                            if not re.match(r'^execution_(\d{1,4}|others)$', occurrence_label.strip()):
                                raise UserConfigurationError(
                                    'incorrect string "' + occurrence_label +
                                    '" for execution label in input file step parameter')
                            occurrence_ordinal = occurrence_label.split('_')[1]
                            if occurrence_ordinal != 'others':
                                occurrence_ordinal = int(occurrence_ordinal)
                                if occurrence_ordinal < 1:
                                    raise UserConfigurationError(
                                        'incorrect string "' + occurrence_label +
                                        '" for execution label in input file step parameter')
                            occurrence_value = param_value[occurrence_label]
                            if occurrence_value is None:
                                raise UserConfigurationError(
                                    "parameter execution label value in input" +
                                    " file must not be blank or None object")
                            if type(occurrence_value) is dict:
                                raise UserConfigurationError(
                                    "parameter execution label values cannot be mapped nodes")
                            if type(occurrence_value) is list:
                                for sub_value in occurrence_value:
                                    if type(sub_value) is dict:
                                        raise UserConfigurationError(
                                            "sequenced sub execution label value cannot be a mapped node")
                pipeline_params_map[step_name] = step_param_map
        else:
            pipeline_params_map = {}
        return pipeline_params_map

    def _add_ordinals(self):
        for step_name in self._pipeline_params_map:
            step_params_map = self._pipeline_params_map[step_name]
            for param_name in step_params_map:
                if type(step_params_map[param_name]) is dict:
                    params_dict = {}
                    exec_map = step_params_map[param_name]
                    for exec_label in exec_map:
                        ordinal_str = exec_label.split("_")[1]
                        param_value = exec_map[exec_label]
                        if ordinal_str == "others":
                            params_dict[ordinal_str] = param_value
                        else:
                            params_dict[int(ordinal_str)] = param_value
                else:
                    params_dict = {"others": step_params_map[param_name]}
                self._pipeline_params_map[step_name][param_name] = params_dict

    def convey_global_parameter(self, parameter_name):
        """
        This method returns the object associated with the global
        parameter with name `parameter_name` that was supplied in
        the user input yaml file.

        ### Arguments:
        - `parameter_name`: `str` object

        ### Returns:
        - the parameter object OR `None` if the global parameter
        with name `parameter_name` was not found
        """
        if parameter_name in list(self._globals_map.keys()):
            parameter = self._globals_map[parameter_name]
        else:
            parameter = None
        return parameter

    def convey_global_parameters(self):
        """
        Returns a [`list`][2] of all the global parameters that were
        modified in the user input yaml file.

        ### Returns:
        - [`list`][2]

        [2]: https://docs.python.org/3/library/stdtypes.html#list
        """
        return list(self._globals_map.keys())

    def convey_chosen_pipeline(self):
        """
        This method provides the name of the pipeline chosen by
        the user in the user input yaml file.

        ### Returns:
        - `str` object
        """
        return self._pipeline_pick

    def convey_checkpoint_flag(self):
        """
        This method is not ready for use.
        """
        return self._chk_flag

    def convey_restart_flag(self):
        """
        This method is not ready for use.
        """
        return self._restart_flag

    def convey_restart_step(self):
        """
        This method is not ready for use.
        """
        return self._restart_step

    def convey_restart_ordinal(self):
        """
        This method is not ready for use.
        """
        return self._restart_ordinal

    def convey_restart_path(self):
        """
        This method is not ready for use.
        """
        return self._restart_path

    def convey_step_parameter(self, step_name: str, parameter_name: str, ordinal: int):
        """
        This method returns a step parameter that was provided by
        the use in the user input yaml file.

        ### Arguments:
        - `step_name`: `str` object; name of the step
        - `parameter_name`: `str` object; name of the parameter
        - `ordinal`: `int`; execution ordinal number of the step

        ### Returns:
        - if the parameter was supplied in user input, then returns
        the parameter object, else returns `None`

        ### Raises:
        - `pacmo.error.IncorrectArgumentType`: Bad argument types for
        convey_step_parameters function
        """
        if not (type(step_name) is str
                and type(parameter_name) is str
                and type(ordinal) is int):
            raise IncorrectArgumentType(
                "Bad argument types for convey_step_parameters function")
        steps = list(self._pipeline_params_map.keys())
        if step_name not in steps:
            return None
        params = self._pipeline_params_map[step_name]
        parameters = list(params.keys())
        if parameter_name not in parameters:
            return None
        param_dict = params[parameter_name]
        ordinals = [label for label in param_dict.keys() if label != 'others']
        if ordinal in ordinals:
            return param_dict[ordinal]
        elif 'others' in list(param_dict.keys()):
            return param_dict['others']
        else:
            return None

    def convey_steps(self):
        """
        This method returns a [`list`][2] of steps that were
        configured by the user in the user input yaml file.

        ### Returns:
        - [`list`][2] of step names

        [2]: https://docs.python.org/3/library/stdtypes.html#list
        """
        return list(self._pipeline_params_map.keys())

    def convey_step_parameters(self, step_name):
        """
        This method returns a [`list`][2] of step parameter names
        that were configured by the user for step `step_name`
        in the user input yaml file.

        ### Arguments:
        - `step_name`: `str` object; name of step

        ### Returns:
         - [`list`][2] of `str` objects; parameter names

        [2]: https://docs.python.org/3/library/stdtypes.html#list
        """
        steps = list(self._pipeline_params_map.keys())
        if step_name not in steps:
            return []
        params = self._pipeline_params_map[step_name]
        parameters = list(params.keys())
        return parameters

    def convey_external_registries(self):
        return self._external_registries

    def convey_primary_registry(self):
        return self._primary_registry


class PipelinesRegistrar(object):
    """
    Objects of type `PipelineRegistrar` make the pipeline definitions
    that are declared in the pipeline registry section of the application
    registry file with name `REGISTRY_FILENAME` available to other
    objects through convenience methods.
    """

    def __init__(self, pipelines_map):
        """
        ### Arguments:
        - `pipeline_maps_list`: [`list`][2] of [`dict`][1]s containing
        pipelines definitions; usually obtained from an instance of
        `RegistryReader`

        ### Raises:
        - `pacmo.error.PipelinesRegistryError`: exceptions generally pertain
        to errors that were encountered within the content of
        `pipeline_maps_list` and indirectly inform about errors in the pipelines
        registry section of the applications registry file

        [1]: https://docs.python.org/3/tutorial/datastructures.html#dictionaries
        [2]: https://docs.python.org/3/library/stdtypes.html#list
        """
        self._pipeline_registry = pipelines_map
        self._pipelines_map, self._input_elements = self._parse_pipelines_map()
        self._pipeline_names = list(self._pipelines_map.keys())
        self._init_ordinals()
        self._update_element_providers()

    # TODO: refactor this method to smaller methods
    def _parse_pipelines_map(self):
        pipeline_names = []
        pipelines_map = {}
        all_input_elements = []
        for pipeline_name in self._pipeline_registry:
            # constraint 1
            if type(pipeline_name) is not str:
                raise PipelinesRegistryError(
                    "A registered pipeline name must be of type str")
            pipeline_names.append(pipeline_name)
            # constraint 3
            if len(set(pipeline_names)) < len(pipeline_names):
                raise PipelinesRegistryError(
                    "Duplicate pipeline name \"" + pipeline_name + "\" found in pipeline registry")
            # constraint 4
            try:
                pipeline_steps = self._pipeline_registry[pipeline_name]["steps"]
            except Exception:
                raise PipelinesRegistryError(
                    "A registered pipeline must have \"steps\" sequence node")
            # constraint 5
            if type(pipeline_steps) is not list:
                raise PipelinesRegistryError(
                    "Steps in the pipeline registry must be a sequence node")
            valid_pipeline_steps = [step for step in pipeline_steps if step is not None]
            # constraint 6
            if len(valid_pipeline_steps) == 0:
                raise PipelinesRegistryError(
                    "A registered pipeline must have at least one step")
            steps_list = []
            for step_obj in valid_pipeline_steps:
                # constraint 7
                if type(step_obj) is not str and type(step_obj) is not dict:
                    raise PipelinesRegistryError(
                        "A step in the pipeline registry must be a string scalar node or a mapping node")
                if type(step_obj) is dict:
                    step_keys = list(step_obj.keys())
                    # constraint 8
                    if len(step_keys) != 1:
                        raise PipelinesRegistryError(
                            "A step mapping node in the pipeline registry must not " +
                            "have any sibling key value pairs")
                    step_name = step_keys[0]
                    # constraint 9
                    if type(step_name) is not str:
                        raise PipelinesRegistryError(
                            'Pipeline step declarations that are mapping nodes must ' +
                            'have one key of type str: the name of the step')
                    # constraint 10
                    if type(step_obj[step_name]) is not dict:
                        raise PipelinesRegistryError(
                            "A step that is a mapping node must not have an empty value")
                    # constraint 11
                    if len(step_obj[step_name]) > 2 or len(step_obj[step_name]) == 0:
                        raise PipelinesRegistryError(
                            "Steps that are mapping nodes in the pipeline registry are " +
                            "only allowed to have at most 1 sub node that is a mapping " +
                            'node with at most 2 keys: "parameters" and "element_providers".')
                    step_keys = list(step_obj[step_name].keys())
                    # constraint 12
                    if not set(step_keys).issubset({'parameters', 'element_providers'}):
                        raise PipelinesRegistryError(
                            'The value of a step entry that is a mapping node must be ' +
                            'a mapping node with only the following keys: "parameters" ' +
                            'and "element_providers"')
                    if 'parameters' in step_keys:
                        step_parameters_map = step_obj[step_name]["parameters"]
                        # constraint 13
                        if type(step_parameters_map) is not dict:
                            raise PipelinesRegistryError(
                                "Any pipeline registry step parameter node must be a mapped node")
                        # constraint 14
                        if None in list(step_parameters_map.values()):
                            raise PipelinesRegistryError(
                                "All step parameters declared in pipeline" +
                                " registry must be assigned a valid value")
                        parameter_name_list = []
                        for parameter_name in step_parameters_map:
                            # constraint 15
                            if type(parameter_name) is not str:
                                raise PipelinesRegistryError(
                                    "Parameter names in pipeline registry must be of type str")
                            parameter_name_list.append(parameter_name)
                            # constraint 16
                            if len(set(parameter_name_list)) < len(parameter_name_list):
                                raise PipelinesRegistryError(
                                    "A step parameter cannot be duplicated in a registered pipeline")
                            step_parameter = step_parameters_map[parameter_name]
                            # constraint 17
                            if type(step_parameter) is dict:
                                raise PipelinesRegistryError(
                                    "A step parameter cannot be a mapped node.")
                    else:
                        step_obj[step_name]['parameters'] = {}
                    if "element_providers" in step_keys:
                        step_providers_map = step_obj[step_name]['element_providers']
                        # constraint 19
                        if type(step_providers_map) is not dict:
                            raise PipelinesRegistryError(
                                'A mapping node with key "element_providers" must have ' +
                                'a value that is a mapping node and not a scalar node ' +
                                'or a sequence node.')
                        for provider_step_name in step_providers_map:
                            # constraint 20
                            if type(provider_step_name) is not str:
                                raise PipelinesRegistryError(
                                    'The element provider name must be of type str')
                            provided_element = step_providers_map[provider_step_name]
                            # constraint 21
                            if type(provided_element) is not str and type(provided_element) is not dict:
                                raise PipelinesRegistryError(
                                    'The value of element provider keys must be either ' +
                                    'a string scalar node or a mapping node')
                            element_names_list = []
                            if type(provided_element) is dict:
                                occurrence_labels = list(provided_element.keys())
                                # constraint 22
                                if len(occurrence_labels) == 0:
                                    raise PipelinesRegistryError(
                                        "A mapping node that is mapped to an element" +
                                        " provider cannot have 0 key-value pairs")
                                # constraint 23
                                if len(set(occurrence_labels)) < len(occurrence_labels):
                                    raise PipelinesRegistryError(
                                        "execution labels for a given element provider cannot be duplicated")
                                for occurrence_label in provided_element:
                                    # constraint 24
                                    if type(occurrence_label) is not str:
                                        raise PipelinesRegistryError(
                                            "execution labels for element providers" +
                                            " must be of type str")
                                    # constraint 25
                                    if not re.match(r'^execution_\d{1,4}$', occurrence_label.strip()):
                                        raise UserConfigurationError(
                                            'incorrect string "' + occurrence_label +
                                            '" for execution label for element provider')
                                    occurrence_value = provided_element[occurrence_label]
                                    # constraint 26
                                    if occurrence_value is None:
                                        raise PipelinesRegistryError(
                                            "element provider execution label value in pipeline " +
                                            "registry must not be blank or None object")
                                    # constraint 27
                                    if type(occurrence_value) is dict:
                                        raise PipelinesRegistryError(
                                            "element provider execution label values cannot be mapping nodes")
                                    if type(occurrence_value) is list:
                                        for sub_value in occurrence_value:
                                            # constraint 28
                                            if type(sub_value) is not str:
                                                raise PipelinesRegistryError(
                                                    'execution label values in pipeline ' +
                                                    'registry must be a string scalar nodes ' +
                                                    'or a sequence node of string scalar nodes')
                                            element_names_list.append(sub_value)
                                    else:
                                        # constraint 29
                                        if type(occurrence_value) is not str:
                                            raise PipelinesRegistryError(
                                                'execution label values in pipeline ' +
                                                'registry must be a string scalar nodes ' +
                                                'or a sequence node of string scalar nodes')
                                        element_names_list.append(occurrence_value)
                            else:
                                element_names_list.append(provided_element)
                            # constraint 30
                            if len(set(element_names_list)) < len(element_names_list):
                                raise PipelinesRegistryError(
                                    'Input elements for step "' + step_name +
                                    '" in pipeline "' + pipeline_name +
                                    '" cannot be repeated')
                            all_input_elements.extend(element_names_list)
                    else:
                        step_obj[step_name]['element_providers'] = {}
                    step_obj[step_name]['ordinal'] = -1
                    steps_list.append(step_obj)
                else:
                    step_name = step_obj
                    steps_list.append({step_name: {'parameters': {}, 'element_providers': {}, 'ordinal': -1}})
            pipelines_map[pipeline_name] = steps_list
            all_input_elements = list(set(all_input_elements))
        return pipelines_map, all_input_elements

    def _init_ordinals(self):
        for step_maps_list in self._pipelines_map.values():
            step_names_list = []
            for step_map in step_maps_list:
                step_name = list(step_map.keys())[0]
                step_names_list.append(step_name)
                ordinal = step_names_list.count(step_name)
                step_map[step_name]['ordinal'] = ordinal

    def _update_element_providers(self):
        for pipeline_name, step_maps_list in self._pipelines_map.items():
            step_names = [list(step_map.keys())[0] for step_map in step_maps_list]
            steps_list = []
            for step_map in step_maps_list:
                step_name = list(step_map.keys())[0]
                steps_list.append(step_name)
                providers_map = step_map[step_name]['element_providers']
                updated_map = {}
                for provider_step in providers_map:
                    if provider_step not in step_names:
                        raise PipelinesRegistryError(
                            'Step "' + str(provider_step) + '" ' +
                            'has not been declared in pipeline "' +
                            pipeline_name + '", but it is listed ' +
                            'as an element provider.')
                    if provider_step not in steps_list:
                        raise PipelinesRegistryError(
                            'Step "' + provider_step + '" ' +
                            'cannot be declared as an element ' +
                            'provider before it has been declared for ' +
                            'execution in pipeline "' + pipeline_name +
                            '"')
                    n_execs = step_names.count(provider_step)
                    element_node = providers_map[provider_step]
                    if type(element_node) is str:
                        if n_execs != 1:
                            raise PipelinesRegistryError(
                                'Step "' + provider_step +
                                '" is run more than once in pipeline "' +
                                pipeline_name + '". You must use execution ' +
                                'labels when using this step as an element ' +
                                'provider.')
                        provider_ordinal = 1
                        in_element_map = {
                            element_node: {
                                'provider': provider_step,
                                'ordinal': provider_ordinal
                            }
                        }
                        updated_map.update(in_element_map)
                    else:
                        elements_map = element_node
                        for exec_label in elements_map:
                            provider_ordinal = int(exec_label.split('_')[1])
                            if provider_ordinal > steps_list.count(provider_step):
                                raise PipelinesRegistryError(
                                    'Invalid execution label for element ' +
                                    'provider "' + provider_step + '" in pipeline "' +
                                    pipeline_name + '": ' + 'Provider step with the ' +
                                    'provided ordinal number won\'t have been executed' +
                                    'at this point in the pipeline.')
                            element_obj = elements_map[exec_label]
                            if type(element_obj) is list:
                                in_element_map = {}
                                for element in element_obj:
                                    in_element_map[element] = {
                                        'provider': provider_step,
                                        'ordinal': provider_ordinal
                                    }
                            else:
                                in_element_map = {
                                    element_obj: {
                                        'provider': provider_step,
                                        'ordinal': provider_ordinal
                                    }
                                }
                            updated_map.update(in_element_map)
                step_map[step_name]['element_providers'] = updated_map

    def report_pipelines(self):
        """
        This method returns the names of the pipelines that are
        registered in the pipeline registry section of the application
        registry file.

        ### Returns:
        - [`list`][2] of `str` objects


        [2]: https://docs.python.org/3/library/stdtypes.html#list
        """
        return self._pipeline_names

    def is_registered_pipeline(self, pipeline_name):
        """
        This method determines if a pipeline with name
        `pipeline_name` is registered in the pipeline
        registry.

        ### Arguments:
        - `pipeline_name`: `str` object

        ### Returns:
        - `True` if registered, `False` otherwise
        """
        is_registered = pipeline_name in self._pipeline_names
        return is_registered

    def report_step_parameters(self, pipeline_name, step_name, ordinal):
        """
        This method reports any step parameters for step `step_name` in
        pipeline `pipeline_name` with step execution ordinal `ordinal` that
        have been modified in the pipeline registry.

        ### Arguments:
        - `pipeline_name`: `str` object; name of pipeline
        - `step_name`: `str` object; name of step
        - `ordinal`: `int` object; step execution ordinal number

        ### Returns:
        - [`list`][2] of `str` objects; parameter names; the returned object
        can be an empty [`list`][2] if no parameter modifications are
        declared for the step

        [2]: https://docs.python.org/3/library/stdtypes.html#list
        """
        parameters = []
        for step_map in self._pipelines_map[pipeline_name]:
            registered_name = list(step_map.keys())[0]
            step_ordinal = step_map[registered_name]['ordinal']
            if registered_name == step_name and step_ordinal == ordinal:
                parameters_map = step_map[step_name]['parameters']
                parameters.extend(list(parameters_map.keys()))
        return parameters

    def report_step_parameter(self, pipeline_name, step_name, parameter_name, ordinal):
        """
        This method reports a step parameter `parameter_name` in step
        `step_name` within pipeline `pipeline_name` with step execution
        ordinal number `ordinal` that has been modified in the pipeline
        registry.

        ### Arguments:
        - `pipeline_name`: `str` object; name of pipeline
        - `step_name`: `str` object; name of step
        - `parameter_name`: `str` object; parameter name
        - `ordinal`: `int` object; step execution ordinal number

        ### Returns:
        - a python object that represents the value of the parameter
        with name `parameter_name`; a `None` is returned if modifications
        for parameter `parameter_name` is not declared in the pipeline
        registry
        """
        parameter = None
        for step_map in self._pipelines_map[pipeline_name]:
            registered_name = list(step_map.keys())[0]
            step_ordinal = step_map[registered_name]['ordinal']
            if registered_name == step_name and step_ordinal == ordinal:
                parameters_map = step_map[step_name]['parameters']
                if parameter_name in list(parameters_map.keys()):
                    parameter = step_map[step_name]['parameters'][parameter_name]
                else:
                    parameter = None
        return parameter

    def report_steps(self, pipeline_name):
        """
        This method returns the name of all of the steps that
        are specified for a pipeline that is declared in the
        pipeline registry.

        ### Arguments:
        - `pipeline_name`: `str` object; name of pipeline

        ### Returns:
        - [`list`][2] of `str` objects; names of steps in the
        pipeline `pipeline_name`

        [2]: https://docs.python.org/3/library/stdtypes.html#list
        """
        step_names_list = [list(step_map.keys())[0] for step_map in self._pipelines_map[pipeline_name]]
        return step_names_list

    def report_input_elements(self, pipeline_name, step_name, ordinal):
        """
        This method returns the names of the input elements for
        step `step_name` in pipeline `pipeline_name` with ordinal
        `ordinal`. The method will return an empty [`list`][2] if
        `pipeline_name` or `step_name` with ordinal `ordinal` is
        not found in the pipeline registry.

        ### Arguments:
        - `step_name`: `str` object; name of step
        - `pipeline_name`: `str` object: name of pipeline
        - `ordinal`: `int`; execution ordinal of step

        ### Returns:
        -  [`list`][2] of `str` objects; names of input elements

        [2]: https://docs.python.org/3/library/stdtypes.html#list
        """
        elements = []
        if pipeline_name not in self._pipeline_names:
            return elements
        step_maps = self._pipelines_map[pipeline_name]
        for step_map in step_maps:
            registered_name = list(step_map.keys())[0]
            registered_ordinal = step_map[registered_name]['ordinal']
            if step_name == registered_name and ordinal == registered_ordinal:
                elements.extend(list(step_map[step_name]['element_providers'].keys()))
        return elements

    def report_provider_info(self, pipeline_name, step_name, ordinal, element_name):
        """
        This method returns the element provider name and the execution ordinal of
        the step that is declared as the element provider. Returns None if not found.

        ### Arguments:
        - `pipeline_name`: `str` object; name of pipeline
        - `step_name`: `str` object; name of step
        - `ordinal`: `int`; execution ordinal of step
        - `element_name`: `str` object;

        ### Returns:
        - [`dict`][1] object:
        ```
        {
            'provider': provider, # str obj; name of provider step
            'ordinal': ordinal # int obj; execution ordinal of provider step
        }
        ```

        [1]: https://docs.python.org/3/tutorial/datastructures.html#dictionaries
        """
        info = None
        if pipeline_name not in self._pipeline_names:
            return info
        step_maps = self._pipelines_map[pipeline_name]
        for step_map in step_maps:
            registered_name = list(step_map.keys())[0]
            registered_ordinal = step_map[step_name]['ordinal']
            if step_name == registered_name and ordinal == registered_ordinal:
                info = step_map['element_providers'][element_name]
        return info

    def report_elements_map(self, pipeline_name, step_name, ordinal):
        """
        This method returns a [`dict`][1] that contains element provider
        information for the step `step_name` with ordinal `ordinal`
        within pipeline `pipeline_name`.

        ### Arguments:
        - `pipeline_name`: `str` object; name of pipeline
        - `step_name`: `str` object; name of step
        - `ordinal`: `int`; execution ordinal of step

        ### Returns:
        - `None` if not found, else returns [`dict`][1] object where the
        keys are the input element names and the values are [`dicts`][1]
        shown below:
        ```
        {
            'provider': provider, # str obj; name of provider step
            'ordinal': ordinal # int obj; execution ordinal of provider step
        }
        ```

        [1]: https://docs.python.org/3/tutorial/datastructures.html#dictionaries
        """
        provider_map = None
        if pipeline_name not in self._pipeline_names:
            return provider_map
        step_maps = self._pipelines_map[pipeline_name]
        for step_map in step_maps:
            registered_name = list(step_map.keys())[0]
            registered_ordinal = step_map[registered_name]['ordinal']
            if step_name == registered_name and ordinal == registered_ordinal:
                provider_map = step_map[step_name]['element_providers']
        return provider_map

    def report_all_elements(self):
        """
        This method returns all input elements that appear in the
        pipeline registry.

        ### Returns:
        - [`list`][2] of `str` objects; names of input elements

        [2]: https://docs.python.org/3/library/stdtypes.html#list
        """
        return self._input_elements


class StepsRegistrar(object):
    """
    Objects of type `StepsRegistrar` make step definitions from the
    steps registry section of the application registry file,
    `REGISTRY_FILENAME`, available to other objects through convenience
    methods.
    """

    def __init__(self, steps_map):
        """
        ### Arguments:
        - `step_maps_list`: [`list`][2] of [`dict`][1]s that represents
        the serialized yaml content of the steps registry section;
        usually obtained from an instance of `RegistryReader`

        ### Raises:
         - `pacmo.error.StepsRegistryError`: raised exceptions generally
         pertain to errors in the content of `step_maps_list` and indirectly
         inform on errors in the content of the steps registry section of
         the application registry file, `REGISTRY_FILENAME`

        [1]: https://docs.python.org/3/tutorial/datastructures.html#dictionaries
        [2]: https://docs.python.org/3/library/stdtypes.html#list
        """
        from .common import Step
        self._proto_step = Step
        self._step_registry = steps_map
        self._step_names, self._steps_map = self._parse_steps_registry()
        self._steps_registry = self._make_steps_tuple()

    def _parse_steps_registry(self):
        step_names = []
        step_classes = []
        input_element_names = []
        output_element_names = []
        steps_map = {}
        for step_name in self._step_registry:
            # constraint 1
            if type(step_name) is not str:
                raise StepsRegistryError(
                    "Every step name in the step registry must of type str")
            step_names.append(step_name)
            # constraint 3
            if len(set(step_names)) < len(step_names):
                raise StepsRegistryError(
                    "Duplicate step name \"" + step_name + "\" found in step registry")
            registered_step_map = self._step_registry[step_name]
            # constraint 4
            if type(registered_step_map) is not dict:
                raise StepsRegistryError(
                    "A registered step must have subnodes")
            # constraint 5
            try:
                step_class_str = registered_step_map["class"]
            except Exception:
                raise StepsRegistryError(
                    "Registered steps must has a \"class\" sub node")
            # constraint 6
            if type(step_class_str) is not str:
                raise StepsRegistryError(
                    "Value of class node must be of type str")
            # constraint 7
            try:
                class_module = '.'.join(step_class_str.split(".")[:-1])
                class_name = step_class_str.split(".")[-1]
                module_obj = importlib.import_module(class_module)
                class_obj = getattr(module_obj, class_name)
            except Exception:
                raise StepsRegistryError(
                    "Object not found: " + step_class_str)
            # constraint 8
            if not isinstance(class_obj, type):
                raise StepsRegistryError(
                    '"class" node value is not an object of type "type"')
            # constraint 9
            if class_obj == self._proto_step:
                raise StepsRegistryError(
                    '"class" node value must not be the parent class "Step"')
            # constraint 10
            if not issubclass(class_obj, self._proto_step):
                raise StepsRegistryError(
                    '"class" node value must be a subclass of class "Step"')
            step_classes.append(class_obj)
            # constraint 11
            if len(set(step_classes)) < len(step_classes):
                raise StepsRegistryError(
                    "Single class implementation " + str(class_obj) +
                    " cannot be registered as two different steps.")
            registered_step_map['class_obj'] = class_obj
            step_sub_keys = list(registered_step_map.keys())
            if "parameters" in step_sub_keys:
                parameters_map = registered_step_map["parameters"]
                # constraint 12
                if type(parameters_map) is not dict:
                    raise StepsRegistryError(
                        "the \"parameters\" sub node for a registered step must be a mapped node")
                parameter_names_list = []
                for step_parameter_name in parameters_map.keys():
                    # constraint 13
                    if type(step_parameter_name) is not str:
                        raise StepsRegistryError(
                            "step parameter names must be of type str")
                    parameter_names_list.append(step_parameter_name)
                    # constraint 14
                    if len(set(parameter_names_list)) < len(parameter_names_list):
                        raise StepsRegistryError(
                            "Parameter names for a registered step must be unique")
                    step_parameter = parameters_map[step_parameter_name]
                    # constraint 15
                    if type(step_parameter) is dict:
                        raise StepsRegistryError(
                            "step parameter values cannot be mapped nodes")
                    # constraint 16
                    if type(step_parameter) is list:
                        for sub_parameter in step_parameter:
                            if type(sub_parameter) is dict:
                                raise StepsRegistryError(
                                    "step parameter sequenced values cannot be mapped nodes")
            else:
                registered_step_map["parameters"] = {}
            if "output_elements" in step_sub_keys:
                elements_list = registered_step_map["output_elements"]
                # constraint 17
                if type(elements_list) is not list:
                    raise StepsRegistryError(
                        "output elements sub node for a registered step" +
                        " must reference node sequence")
                element_names = []
                for element_name in elements_list:
                    # constraint 18
                    if type(element_name) is not str:
                        raise StepsRegistryError(
                            "output element names for a registered step" +
                            " must be of type string")
                    new_out_name = registered_step_map['element_prefix_4dc58d02'] + element_name
                    element_names.append(new_out_name)
                    # constraint 19
                    if len(set(element_names)) != len(element_names):
                        raise StepsRegistryError(
                            "output element names for a registered step " +
                            "must not be repeated")
                registered_step_map["output_elements"] = element_names
                output_element_names.extend(element_names)
            else:
                registered_step_map["output_elements"] = []
            if "input_elements" in step_sub_keys:
                in_elements_list = registered_step_map["input_elements"]
                # constraint 20
                if type(in_elements_list) is not list:
                    raise StepsRegistryError("\"input_elements\" node must map a node sequence")
                in_element_names = []
                for in_element_name in in_elements_list:
                    # constraint 21
                    if type(in_element_name) is not str:
                        raise StepsRegistryError(
                            "Prerequisite steps in the steps registry must be of type str")
                    new_in_name = registered_step_map['element_prefix_4dc58d02'] + in_element_name
                    in_element_names.append(new_in_name)
                    # constraint 22
                    if len(set(in_element_names)) != len(in_element_names):
                        raise StepsRegistryError(
                            'For a given step, all input elements must have unique names.')
                registered_step_map["input_elements"] = in_element_names
                input_element_names.extend(in_element_names)
            else:
                registered_step_map["input_elements"] = []
            steps_map[step_name] = registered_step_map# constraint 23
        if not set(input_element_names).issubset(set(output_element_names)):
            raise StepsRegistryError(
                'The set of all input elements in the steps registry must ' +
                'must be a subset of the set of all output elements in the ' +
                'steps registry')
        return step_names, steps_map

    def is_registered_step(self, step_name: str):
        """
        This method determines if `step_name` is the name of a registered
        step in the steps registry.

        ### Arguments:
        - `step_name`: `str` object; name of registered step

        ### Returns:
        - `True` if registered, `False` otherwise
        """
        is_registered = step_name in self._step_names
        return is_registered

    def report_step_parameters(self, step_name: str):
        """
        This method reports the step parameter names of a registered
        step with name `step_name`.

        ### Arguments:
        - `step_name`: `str` object; name of registered step

        ### Returns:
        - ` [`list`][2] of `str` objects; parameter names

        ### Raises:
        - `pacmo.error.StepNotFoundError`: Step with name "*step name*"
        not found in step registry.

        [2]: https://docs.python.org/3/library/stdtypes.html#list
        """
        try:
            parameters = list(self._steps_map[step_name]['parameters'].keys())
        except Exception:
            raise StepNotFoundError(
                'Step with name "' + str(step_name) +
                '" not found in step registry.')
        return parameters

    def report_parameter_value(self, step_name: str, parameter_name: str):
        """
        This method reports the parameter value of parameter, `parameter_name`,
        for step, `step_name` that is declared in the steps registry.

        ### Arguments:
        - `step_name`: `str` object; name of registered step
        - `parameter_name`: `str` object; name of parameter

        ### Returns:
        - a python object that represents the value of parameter,
        `parameter_name`
        """
        parameter = self._steps_map[step_name]['parameters'][parameter_name]
        return parameter

    def report_input_elements(self, step_name: str):
        """
        This method reports the names of the input state elements
        for a registered step with name `step_name`

        ### Arguments:
        - `step_name`: `str` object; name of registered step

        ### Returns:
        - [`list`][2] of `str` objects; input element names.

        [2]: https://docs.python.org/3/library/stdtypes.html#list
        """
        input_elements = self._steps_map[step_name]['input_elements']
        return input_elements

    def report_output_elements(self, step_name: str):
        """
        This method reports the declared output element names for
        a step that is registered in the steps registry.

        ### Arguments:
        - `step_name`: `str` object; name of registered step

        ### Returns:
        - [`list`][2] of `str` objects; state element names

        [2]: https://docs.python.org/3/library/stdtypes.html#list
        """
        output_elements = self._steps_map[step_name]['output_elements']
        return output_elements

    def get_class_object(self, step_name: str):
        """
        This method returns the class object of a step that is
        registered in the steps registry.

        ### Arguments:
        - `step_name`: `str` object; name of registered step

        ### Returns:
        - a [class object][3]; class implementation of step

        [3]: https://docs.python.org/3/reference/datamodel.html#object.__new__
        """
        class_obj = self._steps_map[step_name]['class_obj']
        return class_obj

    def _make_steps_tuple(self):
        steps_registry = tuple(self._step_names)
        return steps_registry

    def report_steps_registry(self):
        """
        This method reports all of the steps that are registered in
        the steps registry as a [`collections.namedtuple`][4] where the
        attribute names are set to the the name of the steps.

        ### Returns:
        - [`collections.namedtuple`][4]; represents steps registry

        [4]: https://docs.python.org/3/library/collections.html#collections.namedtuple
        """
        return self._steps_registry

    def report_name_from_class(self, cls):
        """
        This method reports the name of a step when given the
        [class object][3] implementation of that step.

        ### Arguments:
        - `cls`: instance of `type` object; registered step class object

        ### Returns:
        - `str` object; name of registered step

        [3]: https://docs.python.org/3/reference/datamodel.html#object.__new__
        """
        name = None
        for step_name in self._steps_map:
            step_cls = self._steps_map[step_name]['class_obj']
            if cls == step_cls:
                name = step_name
        return name


class ElementsRegistrar(object):
    """
    Objects of type `ElementsRegistrar` make state elements registered
    in the state elements registry availble to other objects via
    convenience methods.
    """

    def __init__(self, elements_map):
        """
        ### Arguments:
        - `elements_map`: [`dict`][1] obj; deserialized state element registry;
        usually acquired from `RegistryReader` objects.
        """
        from .common import ElementContainer
        self._proto_class = ElementContainer
        self._elements_map = elements_map
        self._element_cls_map = self._parse_elements_map()

    def _parse_elements_map(self):
        element_names = []
        element_classes = []
        element_cls_map = {}
        for element_name in self._elements_map:
            if type(element_name) is not str:
                raise ElementsRegistryError(
                    'All keys in state element registry must be of type str')
            element_names.append(element_name)
            if len(set(element_names)) < len(element_names):
                raise ElementsRegistryError(
                    'All element names in state element registry must be unique')
            element_class_str = self._elements_map[element_name]
            if type(element_class_str) is not str:
                raise StepsRegistryError(
                    "Value of element mapping node must be of type str")
            try:
                class_module = '.'.join(element_class_str.split(".")[:-1])
                class_name = element_class_str.split(".")[-1]
                module_obj = importlib.import_module(class_module)
                class_obj = getattr(module_obj, class_name)
            except Exception:
                raise StepsRegistryError(
                    "Object not found: " + element_class_str)
            if not isinstance(class_obj, type):
                raise StepsRegistryError(
                    'Value of element mapping node does not refer to an object of type "type"')
            if class_obj == self._proto_class:
                raise StepsRegistryError(
                    'Value of element mapping node must not refer to the parent class "ElementContainer"')
            if not issubclass(class_obj, self._proto_class):
                raise StepsRegistryError(
                    'Value of element mapping node must refer to a subclass of class "ElementContainer"')
            element_classes.append(class_obj)
            if len(set(element_classes)) < len(element_classes):
                raise StepsRegistryError(
                    "Single class implementation " + str(class_obj) +
                    " cannot be registered as two different elements.")
            element_cls_map[element_name] = class_obj
        return element_cls_map

    def report_all_elements(self):
        """
        This method returns the names of all registered state elements.

        ### Returns:
        - [`list`][2] of `str` objects

         [2]: https://docs.python.org/3/library/stdtypes.html#list
        """
        return list(self._element_cls_map.keys())

    def is_registered(self, element_name):
        """
        This method determines if an element with name `element_name` is
        registered in the state elements registry.

        ### Arguments:
        - `element_name`: `str` object; name of input state element

        ### Returns:
        - `True` if registered, `False` other wise
        """
        return element_name in list(self._element_cls_map.keys())

    def report_element_cls(self, element_name):
        """
        This method returns the implemented class object that
        represents a state element.

        ### Arguments:
        - `element_name`: `str` object; name of the state element

        ### Returns:
        - class object that represents the state element. Returns
        `None` if element is not found.
        """
        if element_name in list(self._element_cls_map.keys()):
            return self._element_cls_map[element_name]
        else:
            return None


# TODO: refactor! refactor! refactor!
class NewModelBuilder(object):
    """
    Objects of type `NewModelBuilder` build instances of
    `pacmo.common.PipelineModel`.
    """

    def __init__(self, user_delegate: UserDelegate):
        """
        ### Arguments:
        - `user_delegate`: instance of `UserDelegate`
        """
        from .common import Step
        self._proto_step_cls = Step
        self._user_delegate = user_delegate
        self._reader = self._get_reg_reader()
        self._var_clerk, self._pipelines_clerk, self._steps_clerk, \
            self._elements_clerk = self._get_clerks()
        self._chosen_pipeline = self._user_delegate.convey_chosen_pipeline()

    def _get_reg_reader(self):
        return RegistryReader(
            self._user_delegate.convey_primary_registry(),
            self._user_delegate.convey_external_registries()
        )

    def _get_clerks(self):
        var_clerk = GlobalVarProvider(self._reader.get_global_vars_map())
        pipelines_clerk = PipelinesRegistrar(self._reader.get_pipelines_map())
        steps_clerk = StepsRegistrar(self._reader.get_steps_map())
        elements_clerk = ElementsRegistrar(self._reader.get_elements_map())
        return var_clerk, pipelines_clerk, steps_clerk, elements_clerk

    def create_pipeline_model(self):
        """
        This method returns a new instance of `pacmo.common.PipelineModel`.

        ### Returns:
        - a new `pacmo.common.PipelineModel` instance

        ### Raises:
        - `pacmo.error.UserConfigurationError`: Pipeline "*pipeline name*"
        is not a registered pipeline
        """
        from .common import PipelineModel
        pipeline_name = self._chosen_pipeline
        checkpoint_flag = self._user_delegate.convey_checkpoint_flag()
        if not self._pipelines_clerk.is_registered_pipeline(pipeline_name):
            raise UserConfigurationError(
                "Pipeline \"" + pipeline_name +
                "\" is not a registered pipeline")
        step_models = []
        step_names = []
        steps_registry = self._steps_clerk.report_steps_registry()
        self._check_user_steps()
        global_vars = self._make_vars_tuple()
        for step_name in self._pipelines_clerk.report_steps(pipeline_name):
            step_names.append(step_name)
            ordinal = step_names.count(step_name)
            step_model = self._build_step_model(pipeline_name,
                                                step_name,
                                                steps_registry,
                                                global_vars,
                                                ordinal)
            step_models.append(step_model)
        pipeline_model = PipelineModel(pipeline_name, step_models, checkpoint_flag)
        return pipeline_model

    def _check_user_steps(self):
        registered_steps = set(self._steps_clerk.report_steps_registry())
        user_steps = set(self._user_delegate.convey_steps())
        if not user_steps.issubset(registered_steps):
            raise UserConfigurationError('Unknown set of steps found in ' +
                                         'user input file :' +
                                         str(user_steps.difference(registered_steps)))

    def _build_step_model(self, pipeline_name, step_name,
                          steps_registry, global_vars, ordinal):
        from .common import StepModel
        if not self._steps_clerk.is_registered_step(step_name):
            raise PipelinesRegistryError(
                "Step \"" + step_name + "\" is not a registered step")
        operator_id = step_name
        step_cls = self._steps_clerk.get_class_object(step_name)
        in_elements = self._get_final_in_elements(step_cls)
        out_elements = self._get_final_out_elements(step_cls)
        element_prefix = self._get_element_prefix(
            step_name, in_elements, out_elements)
        elements_directory = self._get_providers(
            pipeline_name, step_name, ordinal)
        output_cls_map = self._get_outputs_map(out_elements)
        step_params_map = self._build_final_params_map(step_cls)
        self._parameters_validation(
            pipeline_name, step_name, step_params_map, ordinal)
        params_tuple = self._make_params_tuple(
            step_name, step_params_map, ordinal)
        step_model = StepModel(ordinal, operator_id, steps_registry,
                               params_tuple, global_vars, step_cls, output_cls_map,
                               step_name, elements_directory, element_prefix)
        return step_model

    @staticmethod
    def _get_element_prefix(step_name, in_elements, out_elements):
        prefixes = ['.'.join(step_name.split('.')[:-1])]
        for element_name in in_elements:
            prefixes.append('.'.join(element_name.split('.')[:-1]))
        for element_name in out_elements:
            prefixes.append('.'.join(element_name.split('.')[:-1]))
        if len(set(prefixes)) != 1:
            raise ElementPrefixError(
                'More than one element prefix found for step "' +
                step_name + '": ' + str(set(prefixes)))
        prefix = list(set(prefixes))[0]
        if prefix != '':
            prefix = prefix + '.'
        return prefix

    def _get_outputs_map(self, output_elements: list):
        output_cls_map = {}
        for element_name in output_elements:
            element_cls = self._elements_clerk.report_element_cls(element_name)
            output_cls_map[element_name] = element_cls
        return output_cls_map

    def _get_providers(self, pipeline_name, step_name, ordinal):
        input_elements = self._pipelines_clerk.report_input_elements(
            pipeline_name, step_name, ordinal)
        ref_in_elements = self._steps_clerk.report_input_elements(step_name)
        if set(input_elements) != set(ref_in_elements):
            raise PipelinesRegistryError(
                'Unrecognized input elements defined for step "' +
                step_name + '" in pipeline "' + pipeline_name +
                '"')
        element_directory = self._pipelines_clerk.report_elements_map(
            pipeline_name, step_name, ordinal)
        return element_directory

    def _validate_elements(self, elements_list):
        for element_name in elements_list:
            if not self._elements_clerk.is_registered(element_name):
                raise ElementsRegistryError(
                    'Element "' + element_name + '" ' +
                    'is not registered in the elements registry')

    def _get_final_in_elements(self, step_cls):
        class_list = list(step_cls.__mro__)
        class_list.reverse()
        subclass_list = []
        for cls in class_list:
            if cls != self._proto_step_cls:
                if issubclass(cls, self._proto_step_cls):
                    subclass_list.append(cls)
        all_in_elements = []
        for sub_cls in subclass_list:
            step_name = self._steps_clerk.report_name_from_class(sub_cls)
            in_elements = self._steps_clerk.report_input_elements(step_name)
            all_in_elements.extend(in_elements)
        current_step_name = self._steps_clerk.report_name_from_class(step_cls)
        current_in_elements = self._steps_clerk.report_input_elements(current_step_name)
        if not set(all_in_elements) == set(current_in_elements):
            raise StepsRegistryError('All inherited input elements must be ' +
                                     'redeclared by the inheriting step in the ' +
                                     'steps registry')
        final_in_elements = list(set(current_in_elements))
        return final_in_elements

    def _get_final_out_elements(self, step_cls):
        class_list = list(step_cls.__mro__)
        class_list.reverse()
        subclass_list = []
        for cls in class_list:
            if cls != self._proto_step_cls:
                if issubclass(cls, self._proto_step_cls):
                    subclass_list.append(cls)
        all_out_elements = []
        for sub_cls in subclass_list:
            step_name = self._steps_clerk.report_name_from_class(sub_cls)
            element_names = self._steps_clerk.report_output_elements(step_name)
            all_out_elements.extend(element_names)
        current_step_name = self._steps_clerk.report_name_from_class(step_cls)
        current_out_elements = self._steps_clerk.report_output_elements(current_step_name)
        if not set(all_out_elements) == set(current_out_elements):
            raise StepsRegistryError('All inherited output elements must be ' +
                                     'redeclared by the inheriting step "' +
                                     current_step_name + '" in the steps registry')
        final_out_elements = list(set(current_out_elements))
        self._validate_elements(final_out_elements)
        return final_out_elements

    def _build_final_params_map(self, step_cls):
        class_list = list(step_cls.__mro__)
        class_list.reverse()
        subclass_list = []
        for cls in class_list:
            if cls != self._proto_step_cls:
                if issubclass(cls, self._proto_step_cls):
                    subclass_list.append(cls)
        params_map = {}
        for sub_cls in subclass_list:
            step_name = self._steps_clerk.report_name_from_class(sub_cls)
            param_names = self._steps_clerk.report_step_parameters(
                step_name)
            for param_name in param_names:
                params_map[param_name] = self._steps_clerk.report_parameter_value(
                    step_name, param_name)
        return params_map

    def _parameters_validation(self, pipeline_name, step_name, step_params, ordinal):
        step_params_set = set(step_params.keys())
        user_params_set = set(self._user_delegate.convey_step_parameters(step_name))
        pipeline_params_set = set(self._pipelines_clerk.report_step_parameters(
            pipeline_name, step_name, ordinal))
        if not user_params_set.issubset(step_params_set):
            non_members = user_params_set.difference(step_params_set)
            raise UserConfigurationError(
                "Unregistered user input parameters found: \n" + str(non_members))
        if not pipeline_params_set.issubset(step_params_set):
            non_members = pipeline_params_set.difference(step_params_set)
            raise PipelinesRegistryError(
                "Unregistered pipeline step parameters found: \n" + str(non_members))

    def _make_params_tuple(self, step_name, step_params_map, ordinal):
        step_params_list = list(step_params_map.keys())
        values_list = []
        for param_name in step_params_list:
            user_value = self._user_delegate.convey_step_parameter(
                step_name, param_name, ordinal)
            pipeline_registry_value = self._pipelines_clerk.report_step_parameter(
                self._chosen_pipeline, step_name, param_name, ordinal)
            step_registry_value = step_params_map[param_name]
            if user_value is not None:
                param_value = user_value
            elif pipeline_registry_value is not None:
                param_value = pipeline_registry_value
            else:
                param_value = step_registry_value
            values_list.append(param_value)
        StepConfiguration = namedtuple('StepConfiguration', step_params_list)
        step_config = StepConfiguration(*tuple(values_list))
        return step_config

    def _make_vars_tuple(self):
        var_names = self._var_clerk.get_var_names()
        var_values = []
        for var_name in var_names:
            user_value = self._user_delegate.convey_global_parameter(var_name)
            registry_value = self._var_clerk.get_global_var(var_name)
            if user_value:
                var_values.append(user_value)
            else:
                var_values.append(registry_value)
        GlobalVariables = namedtuple('GlobalVariables', var_names)
        global_vars = GlobalVariables(*tuple(var_values))
        return global_vars


def load_yaml(file_path):
    """
    This function returns the deserialized contents of the yaml
    file with file path `file_path`.

    ### Arguments:
    - `file_path`: `str` object; path of yaml file

    ### Returns:
    - a python object; see [pyyaml documentation][5]

    [5]: https://pyyaml.org/wiki/PyYAMLDocumentation
    """
    if not os.path.isfile(file_path):
        print("File \"" + file_path + "\" not found")
        raise Exception()
    try:
        file_obj = open(file_path, 'rb')
    except Exception as e:
        print("Unable to open file \"" + file_path + "\"")
        raise e
    try:
        file_bytes = file_obj.read()
        yaml_map = yaml.load(file_bytes, Loader=yaml.FullLoader)
    except Exception as e:
        file_obj.close()
        print("unable to load \"" + file_path + "\" into memory.")
        raise e
    return yaml_map
