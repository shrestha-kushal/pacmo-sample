"""
The `pacmo.common` module contains python object definitions
that are essential to the creation and processing of
computational pipelines during application runtime.
"""

from operator import attrgetter
from inspect import signature
import pickle
import os
import subprocess
from .error import IncorrectArgumentType
from .error import StateElementNotFound
from .error import OperationOutOfOrder
from .error import IncorrectCallerObject
from .error import IncorrectArgumentSignature
from .error import IncorrectClassDefinition
from .error import IncorrectInitialization
from .error import InputElementError
from .error import OutputElementError
import abc
from typing import Dict
from .error import EnvironmentFetchError
from typing import NamedTuple
import logging


mod_log = logging.getLogger(__name__)
mod_log.addHandler(logging.NullHandler())


class State(object):
    """
    `State` instances are simple containers for all
    instances of `StateElement`s that are produced by
    `Step` instances in a given `Pipeline` instance.
    """
    def __init__(self, state_elements: list):
        """
        ### Arguments:
        - `state_elements`: [list](https://docs.python.org/3/library/stdtypes.html#list)
        of `StateElement` instances

        ### Raises:
        - `pacmo.error.IncorrectArgumentType`: Argument elements must be
            of type list.
        - `pacmo.error.IncorrectArgumentType`: Argument elements must be
            a list of `pacmo.common.StateElement` instances.
        """
        self.elements = state_elements
        """
        `State.elements` is a [list](https://docs.python.org/3/library/stdtypes.html#list)
         of objects of type `StateElement`.
        """
        self._check_args()

    def _check_args(self):
        try:
            assert type(self.elements) is list
        except AssertionError:
            raise IncorrectArgumentType(
                "Argument elements must be of type list")
        for element in self.elements:
            try:
                assert isinstance(element, StateElement)
            except AssertionError:
                raise IncorrectArgumentType(
                    "Argument elements must be a list of " +
                    "pacmo.common.StateElement instances.")


class StateElement(object):
    """
    Objects of type `StateElement` serve as simple containers for
    any python object that `Step` instances make available to other
    `Step` instances in a given `Pipeline` instance. `Step` instances
    generally retrieve the objects contained in `pacmo.common.StateElement`
    using helper methods (see `Step.from_step`) and post their own
    python objects into `StateElement` instances also using helper
    methods (see `Step.post_element`). Directly getting and setting
    attributes of `StateElement` instances are handled instead by
    `ElementCourier` instances.
    """

    def __init__(self, owner, name: str, obj, ordinal: int):
        """
        ### Arguments:
        - `owner`: any python object that support the `==` operator
        - `name`: str
        - `obj`: any python object
        - `ordinal`: int

        ### Raises:
        - `pacmo.error.IncorrectArgumentType`: State element names must be of type str
        - `pacmo.error.IncorrectArgumentType`: State element ordinal must be of type int
        """
        self.owner = owner
        """
        The `StateElement.owner` instance variable should be of type str
        and represents the identity of the "owner" of a `StateElement` 
        instance. In the context of the `Pipeline` instances, 
        the owner of a `StateElement` instance will be an instance of 
        `Step` from `Pipeline.steps`.
        """
        self.ordinal = ordinal
        """
        The `StateElement.ordinal` instance variable should be 
        of type int. It is a second identifier that "owners" of 
        `StateElement` instances can use to distinguish from 
        other owners in case there exists two "owner" objects of the same
        type.
        """
        self.name = name
        """
        The `StateElement.name` instance variable represents an 
        an identifying name of `StateElement.object`.
        """
        self.object = obj
        """
        `StateElement.object` instance variable dereferences 
        objects that `Step` instances make available to other
        `Step` instances within a given `Pipeline` instance.
        """
        self._check_input()

    def _check_input(self):
        try:
            assert type(self.name) is str
        except AssertionError:
            raise IncorrectArgumentType(
                "State element names must be of type str")
        try:
            assert type(self.ordinal) is int
        except AssertionError:
            raise IncorrectArgumentType(
                "State element ordinal must be of type int")


class PlaceHolder:
    """
    Generic object type meant to be used as a placeholder
    object for `StateElement.object` during
    initialization of `Pipeline` instances.
    """
    pass


class ElementCourier(object):
    """
    Objects of type `ElementCourier` fetch a list
    of matching elements from the `State` instance passed
    in during initialization via the `ElementCourier.fetch_elements`
    method.
    """

    def __init__(self, state):
        """
        ### Arguments:
        - `state`: instance of `State`

        ### Raises:
        - `pacmo.error.IncorrectArgumentType`: Argument state must be of type `State`
        """
        self._state = state
        self._element_owner = None
        self._check_args()

    def _check_args(self):
        try:
            assert isinstance(self._state, State)
        except AssertionError:
            raise IncorrectArgumentType(
                "Argument state must be of type pacmo.common.State")

    def assign_owner(self, owner):
        """
        Assigns a state element owner to the `ElementCourier`
        instance used for element lookups.

        ### Arguments:
        - `owner`: python object that allows equivalence checking via
        the `==` operator
        """
        self._element_owner = owner

    def fetch_elements(self, element_name):
        """
        Given argument `element_name` `ElementCourier.fetch_elements` will return
        a list of `StateElement` instances for which `StateElement.name` `== element_name` .

        ### Arguments:
        - `element_name`: str

        ### Returns:
        - [list](https://docs.python.org/3/library/stdtypes.html#list) of objects
        of type `StateElement`

        ### Raises:
        - `pacmo.error.StateElementNotFound`: Owner `"owner"` has no state element
        saved with name `"name"`.
        """
        matched_elements = []
        for element in self._state.elements:
            if element.owner == self._element_owner and element.name == element_name:
                matched_elements.append(element)
        if len(matched_elements) == 0:
            raise StateElementNotFound('Owner "' +
                                       str(self._element_owner) +
                                       '" has no state element ' +
                                       'saved with name "' +
                                       element_name + '".')
        matched_elements.sort(key=attrgetter('ordinal'))
        return matched_elements


class ElementFetcher(ElementCourier):
    """
    Objects of type `ElementFetcher` fetch discrete instances of
    `StateElements` from `State` instances via `ElementFetcher.fetch_element`.
    """
    def __init__(self, state):
        """
        ### Arguments:
        - `state`: instance of `State`
        """
        super().__init__(state)

    def fetch_element(self, element_name, ordinal=-1):
        """
        Fetches a single instance of `StateElement` given a state element name
        and an ordinal number.

        ### Arguments:
        - `element_name`: name of the state element (see `StateElement.name`)
        - `ordinal`: an ordinal number that uniquely identifies a `Step` instance
        in a `Pipeline` instance (see `Step.ordinal`)

        ### Returns:
        - a `StateElement` instance object

        ### Raises:
        - `pacmo.error.StateElementNotFound`: Owner "*owner*" has no state element
        with name "*name*" and ordinal number *number*.
        """
        matched_elements = self.fetch_elements(element_name)
        if ordinal != -1:
            element_index = ordinal - 1
        else:
            element_index = ordinal
        try:
            element_obj = matched_elements[element_index]
        except (IndexError, TypeError):
            raise StateElementNotFound(
                'Owner "' + str(self._element_owner) +
                '" has no state element ' + "with name \"" +
                element_name + "\" and " +
                "ordinal number " + str(ordinal))
        return element_obj


class StepOutputFetcher(ElementFetcher):
    """
    Objects of type `StepOutputFetcher` fetch a single `StateElement.object`
    given a state element name and an ordinal number.
    """

    def __init__(self, state):
        """
        ### Arguments:
        - `state`: instance of `State`
        """
        super().__init__(state)
        self._step_is_set = False

    def from_step(self, step_ref):
        """
        Records `step_ref` as the owner value for subsequent state element lookups.

        ### Arguments:
        - `step_ref` : object that allows equivalence checking via the `==` operator

        ### Returns:
        - `StepOutputFetcher` instance: returns a reference to the object to which
        this function is bound.
        """
        self.assign_owner(step_ref)
        self._step_is_set = True
        return self

    def fetch_element(self, element_name, ordinal=-1):
        """
        Given a state element name (`StateElement.name`) and an ordinal number
        (`Step.ordinal`), `StepOutputFetcher.fetch_element` returns the matching
        `StateElement.object`.

        ### Arguments:
        - `element_name`: str
        - `ordinal`: int

        ### Returns:
        - an object referenced by a `StateElement.object` instance variable

        ### Raises:
        - `pacmo.error.OperationOutOfOrder`: call `StepOutputFetcher.from_step`
        method before calling `StepOutputFetcher.fetch_element` method
        """
        if not self._step_is_set:
            raise OperationOutOfOrder(
                "call from_step method before calling fetch_element method")
        element_obj = super().fetch_element(element_name, ordinal)
        self._step_is_set = False
        return element_obj.object


class ElementSaver(ElementCourier):
    """
    `ElementSaver` is a type of `ElementCourier` that can update the
    `StateElement.object` instance variable.
    """

    def __init__(self, state):
        """
        ### Arguments:
        - `state`: Instance of `State`
        """
        super().__init__(state)

    def save_element(self, element_name, element_obj, ordinal=-1):
        """
        Updates `StateElement.object` with `element_obj` for a state element
        where `StateElement.name` == `element_name` and `StateElement.ordinal`
        == `ordinal`.

        ### Arguments:
        - `element_name`: str
        - `element_obj`: a python object
        - `ordinal`: int

        ### Raises:
        - `pacmo.error.StateElementNotFound`: Owner "*owner*" has no state element
        with name "*name*" and ordinal number *int* initialized.
        """
        matched_elements = self.fetch_elements(element_name)
        if ordinal != -1:
            element_index = ordinal - 1
        else:
            element_index = ordinal
        try:
            matched_elements[element_index]
        except (IndexError, TypeError):
            raise StateElementNotFound(
                'Owner "' + str(self._element_owner) +
                '" has no state element with name "' +
                element_name + '" and ordinal number ' +
                str(ordinal) + " initialized")
        matched_elements[element_index].object = element_obj


class StepOutputSaver(ElementSaver):
    """
    `StepOutputSaver` is a type of `ElementSaver` that updates
    `StateElement.object` instance variables on behalf of `Step`
    instances.
    """

    def __init__(self, state):
        """
        ### Arguments:
        - `state`: Instance of `State`
        """
        super().__init__(state)
        self._step_is_set = False

    def for_step(self, step_ref):
        """
        Saves `step_ref` to use as the state element owner upon subsequent
        lookups of `StateElement`.

        ### Arguments:
        - `step_ref`: object that allows equivalence checking via the `==` operator

        ### Returns:
        - Returns the `StepOutputSaver` instance to which this function is bound
        """
        self.assign_owner(step_ref)
        self._step_is_set = True
        return self

    def save_element(self, element_name, element_obj, ordinal=-1):
        """
        Updates `StateElement.object` instance variable with `element_obj`
        for state elements with `StateElement.name` == `element_name` and
        `StateElement.ordinal` == `ordinal` after `StepOutputSaver.for_step`
        has been called.

        ### Arguments:
        - `element_name`: str
        - `element_obj`: a python object
        - `ordinal`: int

        ### Raises:
        - `pacmo.error.OperationOutOfOrder`: Call `StepOutputSaver.for_step`
        method before calling `StepOutputSaver.save_element` method.
        """
        if not self._step_is_set:
            raise OperationOutOfOrder(
                "Call from_step method before calling save_element method.")
        super().save_element(element_name, element_obj, ordinal)
        self._step_is_set = False


class ElementContainer(abc.ABC):
    """
    `ElementContainer` is the abstract base class for classes that
    will serve as containers for state element objects created by
    creators of `Step`s.
    """

    def __init__(self, element_object):
        """
        ### Argument:
        - `element_object`: any python object
        """
        self.element_object = element_object

    @abc.abstractmethod
    def validate_contents(self):
        pass

    def get_element(self):
        return self.element_object


class Pipeline(object):
    """
    `Pipeline` instances are objects that are stateful in-memory representations
    of sequential, computational workflows. They are attributed with a name,
    a `State` instance object, and a [list][1] of `Step` instance objects. While
    `Pipeline` instances could be configured manually, it would be impractical to
    do so. They should be generated by a `PipelineFactory` instance.
    [1]: https://docs.python.org/3/library/stdtypes.html#list
    """

    def __init__(self, name, state, steps, global_vars, checkpoint=False):
        """
        ### Arguments:
        - `name`: str object that represents the name of the pipeline
        - `state`: instance of `State`
        - `steps`: [list][1]
        of `Step` instances
        - `checkpoint`: optional boolean, defaults to False, currently
        not in use

        ### Raises:
        - `pacmo.error.IncorrectArgumentType`: Argument `name` must be of type str
        - `pacmo.error.IncorrectArgumentType`: Argument `state` must be an instance of `State`
        - `pacmo.error.IncorrectArgumentType`: Argument `steps` must be a [list][1]
        - `pacmo.error.IncorrectArgumentType`: Argument `steps` must be a [list][1] of
        `Step` instances

        [1]: https://docs.python.org/3/library/stdtypes.html#list
        """
        self.name = name
        """
        str object that represents the name of the `Pipeline` instances. A
        list of pipeline names can be found in the `pacmo.config.REGISTRY_FILENAME` file.
        """
        self.state = state
        """
        `State` instance that `Step` instances in the `Pipeline` instance read or modify.
        """
        self.steps = steps
        """
        [list][1] of `Step` instances that fully comprise the computational work
        in a given `Pipeline` instance
        [1]: https://docs.python.org/3/library/stdtypes.html#list
        """
        self.global_vars = global_vars
        """
        named tuple containing global variables
        """
        self._checkpoint = checkpoint

    # TODO: check for state and step types
    def _check_init(self):
        if type(self.name) is not str:
            raise IncorrectArgumentType(
                "Argument name must of be type str")
        if not isinstance(self.state, State):
            raise IncorrectArgumentType(
                "Argument state must be of type pacmo.common.State")
        if type(self.steps) is not list:
            raise IncorrectArgumentType(
                "Argument steps must be of type list")
        for step in self.steps:
            if not isinstance(step, Step):
                raise IncorrectArgumentType(
                    "Argument steps must be a list of pacmo.common.Step instances")


class StepModel(object):
    """
    Objects of type `StepModel` are precursors to `Step` objects.
    Public attributes of `StepModel` instances are useful for
    initializing public attributes of `Step` instances. Instances
    of `pacmo.config.NewModelBuilder` make use of this class of objects
    to build instances of `PipelineModel`. It is not recommended that
    instances of `StepModel` be prepared manually.
    """

    def __init__(self, ordinal: int, operator_id, step_registry,
                 parameters, global_parameters, cls,
                 output_cls_map: dict, step_name: str,
                 elements_directory: dict, element_prefix: str):
        """
        ### Arguments:
        - `ordinal`: `int`
        - `operator_id`: object that allows equivalence checking via
        the `==` operator`
        - `step_registry`:  [`collections.namedtuple`][2] where the attribute
        names are step names in `pacmo.config.REGISTRY_FILENAME` and the
        corresponding values are str objects representations of step names.
        - `parameters`: [collections.namedtuple][2] where the attribute
        names are parameter names in `pacmo.config.REGISTRY_FILENAME` for a step
        with name `step_name`.
        - `global_parameters`: [`collections.namedtuple`][2] where the attribute
        names are global parameter names in `pacmo.config.REGISTRY_FILENAME` and
         the corresponding values are actual values for those parameters.
        - `cls`: Class object of the step with name `step_name`
        - `output_cls_map`: `dict` of names of output state elements for step
        with name `step_name` mapped to the corresponding state element classes
        - `step_name`: str object that is the name of a step found in
        `pacmo.config.REGISTRY_FILENAME`
        - `elements_directory`: `dict` containing provider steps for input
        state elements

        ### Raises:
        - `pacmo.error.IncorrectArgumentType`: `StepModel.prerequisite_steps` must
        be of type [list][1]
        - `pacmo.error.IncorrectArgumentType`: `StepModel.ordinal` must be of type int

        [1]: https://docs.python.org/3/library/stdtypes.html#list
        [2]: https://docs.python.org/3/library/collections.html#collections.namedtuple
        """
        self.step_name = step_name
        """
        name of a step in `pacmo.config.REGISTRY_FILENAME`
        """
        self.ordinal = ordinal
        """
        int (see `Step.ordinal`)
        """
        self.operator_id = operator_id
        """
        any python object that allows use of `==` operator
        """
        self.step_registry = step_registry
        """
        [`collections.namedtuple`][2] of str objects that represents 
        steps in `pacmo.config.REGISTRY_FILENAME`

        [2]: https://docs.python.org/3/library/collections.html#collections.namedtuple
        """
        self.parameters = parameters
        """
        [`collections.namedtuple`][2] of parameter values for step with
        name `StepModel.step_name`

        [2]: https://docs.python.org/3/library/collections.html#collections.namedtuple
        """
        self.global_parameters = global_parameters
        """
        [`collections.namedtuple`][2] of global parameter values for the
        application

        [2]: https://docs.python.org/3/library/collections.html#collections.namedtuple
        """
        self.step_cls = cls
        """
        [Class object][3] for the step with name `StepModel.step_name`

        [3]: https://docs.python.org/3/reference/datamodel.html#object.__new__
        """
        self.output_cls_map = output_cls_map
        """
        `dict` of output state element names to state element classes

        [1]: https://docs.python.org/3/library/stdtypes.html#list
        """
        self.elements_directory = elements_directory
        """
        `dict` containing input element provider info
        """
        self.element_prefix = element_prefix
        self._check_init()

    def _check_init(self):
        if type(self.ordinal) is not int:
            raise IncorrectArgumentType(
                "pacmo.common.StepModel.ordinal must be of type int")


class PipelineModel(object):
    """
    Objects of type `PipelineModel` are precursors to objects of
    type `Pipeline`. They are generally used by `Pipeline` instance
    builder classes like `NewPipelineCreator`.
    """

    def __init__(self, name, step_models, checkpoint_flag=False):
        """
        ### Arguments:
        - `name`: str
        - `step_models`: [list][1] of `StepModel` instances
        - `checkpoint_flag`: optional boolean argument; currently not in use

        ### Raises:
        - `pacmo.error.IncorrectArgumentType`: argument `name` must be of
        type str
        - `pacmo.error.IncorrectArgumentType`: argument `step_models`
        must be of type [list][1]
        - `pacmo.error.IncorrectArgumentType`: argument `step_models`
        must only contain instances of `StepModel`

        [1]: https://docs.python.org/3/library/stdtypes.html#list
        """
        self.name = name
        """
        str object that represents name of a pipeline in `pacmo.config.REGISTRY_FILENAME`
        """
        self.step_models = step_models
        """
        [`list`][1] of instances of `StepModel`

        [1]: https://docs.python.org/3/library/stdtypes.html#list
        """
        self.checkpoint_flag = checkpoint_flag
        """
        bool that is currently not used for anything
        """

    def _check_init(self):
        if type(self.name) is not str:
            raise IncorrectArgumentType(
                "argument name must be of type str")
        if type(self.step_models) is not list:
            raise IncorrectArgumentType(
                "argument step_models must be a list")
        for step_model in self.step_models:
            if not isinstance(step_model, StepModel):
                raise IncorrectArgumentType(
                    "argument step_models must only contain" +
                    " instances of StepModel")


class StateBuilder(object):
    """
    Currently not in use.
    """

    def __init__(self):
        pass


# TODO: use state to carry init attributes for Step
class NewStateCreator(object):
    """
    Given an instance of `PipelineModel`, an object of type
    `NewStateCreator` is capable of creating a new instance
    of state and create the instances of `StepElement`s
    declared by steps in `pacmo.config.REGISTRY_FILENAME`. The
    `StateElement` instances initialized within the newly created
    `State` instance will have the `StateElement.object` instance
    variables set to instances of `PlaceHolder`.
    """

    def __init__(self, pipeline_model: PipelineModel):
        """
        ### Arguments:
        - `pipeline_model`: instance of `PipelineModel`
        """
        self._pipeline_model = pipeline_model

    def create_state(self):
        """
        Creates a new instance of `State` initialized with
        `StateElements` declared by steps in `pacmo.config.REGISTRY_FILENAME`

        ### Returns:
        - instance of `State`
        """
        state_elements = []
        step_model: StepModel
        for step_model in self._pipeline_model.step_models:
            owner = step_model.operator_id
            ordinal = step_model.ordinal
            output_elements = list(step_model.output_cls_map.keys())
            for element_name in output_elements:
                state_element = StateElement(owner, element_name,
                                             PlaceHolder(), ordinal)
                state_elements.append(state_element)
        state = State(state_elements)
        return state


class StateImporter(StateBuilder):
    """
    Currently not in use
    """

    def __init__(self):
        super().__init__()


class StateFactory(object):
    """
    Currently not in use
    """

    def __init__(self, builder):
        self._builder = builder


class PipelineBuilder(abc.ABC):
    """
    Abstract base class for all `PipelineBuilder` instances. The goal
    of objects of this type is singular: the goal is to product a
    new instance of `Pipeline` via `PipelineBuilder.build`.
    """

    def __init__(self):
        pass

    @abc.abstractmethod
    def build(self):
        """
        Abstract method for building `Pipeline` instances. Subclasses
        must implement this method.
        """


# TODO: add step model contents to state as "init_package"
# TODO: add logic to add scribe and logger to steps
class NewPipelineCreator(PipelineBuilder):
    """
    `NewPipelineCreator` is type of `PipelineBuilder` that uses
    `pacmo.config.REGISTRY_FILENAME` in conjunction with user_input.yaml
    to build instances of `Pipeline`. Instance objects will first
    build a `PipelineModel` upon instantiation and use that
    `PipelineModel` instances to create a new `Pipeline` instance
    object with every call to `NewPipelineCreator.build`.
    """

    def __init__(self, user_delegate):
        """
        ### Arguments:
        - `user_delegate`: instance of `pacmo.config.UserDelegate`
        """
        super().__init__()
        self._user_delegate = user_delegate
        self._pipeline_model = self._get_pipeline_model()
        self._pipeline_state = self._get_pipeline_state()

    def _get_pipeline_model(self):
        from .config import NewModelBuilder
        model_builder = NewModelBuilder(self._user_delegate)
        pipeline_model = model_builder.create_pipeline_model()
        return pipeline_model

    def _get_pipeline_state(self):
        state_builder = NewStateCreator(self._pipeline_model)
        pipeline_state = state_builder.create_state()
        return pipeline_state

    def build(self):
        """
        Build a new instance of `Pipeline` for the pipeline that is
        chosen in user_input.yaml

        ### Returns:
        - a new `Pipeline` instance object
        """
        steps = []
        step_model: StepModel
        global_params = None
        if self._pipeline_model.step_models:
            global_params = self._pipeline_model.step_models[0].global_parameters
        for step_model in self._pipeline_model.step_models:
            step: Step
            step = step_model.step_cls(self._pipeline_state)
            step.name = step_model.step_name
            step.ordinal = step_model.ordinal
            step.parent_app = step_model.global_parameters
            step.config = step_model.parameters
            step.parent_registry = step_model.step_registry
            step.operator_id = step_model.operator_id
            step.element_directory = step_model.elements_directory
            step.output_cls_map = step_model.output_cls_map
            step.element_prefix = step_model.element_prefix
            step_logger = logging.getLogger(step.name)
            step_logger.addHandler(logging.NullHandler())
            step.logger = step_logger
            steps.append(step)
        pipeline = Pipeline(self._pipeline_model.name,
                            self._pipeline_state, steps,
                            global_params,
                            self._pipeline_model.checkpoint_flag)
        return pipeline


# Not ready for use
class PipelineImporter(PipelineBuilder):
    """
    This class is currently not ready for use.
    """

    def __init__(self, user_delegate):
        super().__init__()
        self._user_delegate = user_delegate
        raise NotImplementedError(
            "pacmo.common.PipelineImporter is not ready for use.")

    def build(self):
        pipeline = self._import_pipeline()
        self._revise_pipeline(pipeline)
        return pipeline

    def _import_pipeline(self):
        from .config import CHECKPOINT_FILENAME
        restart_path = self._user_delegate.convey_restart_path()
        checkpoint_path = os.path.join(restart_path, CHECKPOINT_FILENAME)
        if not os.path.exists(checkpoint_path):
            print("Pickled pipeline not found in " + restart_path)
            raise Exception()
        try:
            with open(checkpoint_path, 'rb') as fo:
                pipeline = pickle.load(fo)
        except Exception as e:
            print("Unable to load pickled pipeline")
            raise e
        return pipeline

    def _revise_pipeline(self, pipeline: Pipeline):
        pipeline.checkpoint = self._user_delegate.convey_checkpoint_flag()
        user_steps = self._user_delegate.convey_steps()
        global_params = self._user_delegate.convey_global_parameters()
        restart_step_name = self._user_delegate.convey_restart_step()
        restart_ordinal = self._user_delegate.convey_restart_ordinal()
        overwrite = False
        for step in pipeline.steps:
            if step.name == restart_step_name and step.ordinal == restart_ordinal:
                overwrite = True
            if not overwrite:
                continue
            for parameter_name in global_params:
                try:
                    getattr(step.parent_app, parameter_name)
                except AttributeError:
                    continue
                user_value = self._user_delegate.convey_global_parameter(parameter_name)
                setattr(step.parent_app, parameter_name, user_value)
            if step.name in user_steps:
                user_parameters = self._user_delegate.convey_step_parameters(step.name)
                for param_name in user_parameters:
                    try:
                        getattr(step.config, param_name)
                    except AttributeError:
                        continue
                    user_value = self._user_delegate.convey_step_parameter(
                        step.name, param_name, step.ordinal)
                    setattr(step.config, param_name, user_value)


class PipelineFactory(object):
    """
    `PipelineFactory` is a factory class for creating new instances
    of `Pipeline`. Given an instance of `PipelineBuilder`, `PipelineFactory`
    instances will produce the appropriate `Pipeline` instance.
    """

    def __init__(self, builder: PipelineBuilder):
        """
        ### Arguments:
        - `builder`: an instance of `PipelineBuilder`

        ### Raises:
        - `pacmo.error.IncorrectArgumentType`:  `PipelineFactory` needs an instance
        of `PipelineBuilder`
        """
        self._builder = builder
        self._check_init()

    def _check_init(self):
        if not isinstance(self._builder, PipelineBuilder):
            raise IncorrectArgumentType(
                "PipelineFactory needs an instance of PipelineBuilder")

    def produce_pipeline(self):
        """
        Produces a new instance of `Pipeline` with every call.

        ### Returns:
        - a new instance of `Pipeline`
        """
        return self._builder.build()


class StepMeta(type):
    """
    Meta class for class `Step`. Code standards checks and class
    definition modifications for `Step` subclasses are defined in
    this meta class.

    ### Raises:
    - `pacmo.error.IncorrectArgumentSignature`:  All [Step.execute][4]
    implementations must have the same argument signature, i.e. (self)
    - `pacmo.error.IncorrectClassDefinition`: Subclasses of `Step` must
    adhere to single inheritance
    - `pacmo.error.IncorrectClassDefinition`: `Step`s must have callable
    public attribute "execute"
    - `pacmo.error.IncorrectClassDefinition`: `Step`s must implement method
     "[`execute `][4]"

    [4]: #pacmo.common.Step.execute
    """

    def __new__(mcs, class_name, bases, class_dict):
        mcs._check_step_class(class_name, bases, class_dict)
        class_dict['execute'] = mcs._make_exec(
            mcs._pre_execute, class_dict['execute'],
            mcs._post_execute, class_name)
        return super().__new__(mcs, class_name, bases, class_dict)

    @staticmethod
    def _check_step_class(class_name, bases, class_dict):
        if class_name != 'Step':
            if len(bases) != 1:
                raise IncorrectClassDefinition(
                    "Subclasses of Step must adhere to single inheritance")
        if 'execute' not in list(class_dict.keys()):
            raise IncorrectClassDefinition(
                "Steps must have callable public attribute \"execute\"")
        if not callable(class_dict['execute']):
            raise IncorrectClassDefinition(
                "Steps must implement method \"execute\"")
        step_signature = signature(StepMeta.ref_exec)
        if signature(class_dict['execute']) != step_signature:
            raise IncorrectArgumentSignature(
                "All Step.execute implementations must have the" +
                " same argument signature, i.e. (self)")

    @staticmethod
    def _make_exec(pre_execute, execute, post_execute, owner_name):
        def new_exec(self):
            caller_obj = self
            pre_execute(caller_obj, owner_name)  # owner_name from closure
            if isinstance(caller_obj, Step):
                step_obj = caller_obj
            else:
                step_obj = caller_obj.current_step
            step_obj: Step
            execute(step_obj)
            post_execute(step_obj)
        new_exec.__doc__ = execute.__doc__
        return new_exec

    def _pre_execute(self, owner_name):
        if self.__class__.__name__ == owner_name:
            raise IncorrectCallerObject(
                'Instances of class Step may not call \"execute\" function')
        if not issubclass(self.__class__, Step):
            if not isinstance(self, PipelineWorker):
                raise IncorrectCallerObject(
                    'Only subclass instances of Step and PipelineWorker' +
                    'may call "execute" function')

    def _post_execute(self):
        self: Step
        element_names = list(self.output_cls_map.keys())
        for element_name in element_names:
            element_obj = self.from_step(self.name).fetch_element(
                element_name, self.ordinal)
            if isinstance(element_obj, PlaceHolder):
                raise OutputElementError(
                    'Output state element "' + element_name +
                    '" not set by step "' + self.name + '"')

    def ref_exec(self):
        """
        The argument signature of all [Step.execute][4] implementations
        must match the signature of `StepMeta.ref_exec`
        [4]: #pacmo.common.Step.execute
        """


# TODO: initialize Step through state
class Step(metaclass=StepMeta):
    """
    Objects of type `Step` are python representations of modularized
    computations that are part of a larger sequential computational
    workflow. Any new, modular computation should be represented as
    a `Step` class by subclassing this class, after which they are
    orchestrated by the larger application with ease. Subclassing
    `Step` will give a class access to data that have been declared
    in registry.yaml or user_input.yaml and will
    allow a class to publish its own computational output or retrieve
    the computational output of other `Step` instances during execution
    of sequential computational workflows or "pipelines" that have been
    declared in registry.yaml.
    """

    def __init__(self, state):
        """
        ### Arguments:
        - `state`: instance of `State`; at this time, this object does
        not contribute any attributes or methods to the public API
        """
        self.state = state
        """
        reference to the chosen pipeline's state
        """
        self._fetcher = StepOutputFetcher(self.state)
        self._saver = StepOutputSaver(self.state)
        self.name: str
        self.name = None
        """
        name of the step in registry.yaml
        """
        self.ordinal: int
        self.ordinal = None  # int >0
        """
        This is an integer representation of the ordinal number associated
        with execution of a step in a given pipeline. E.g. the first
        time a particular step is executed by `PipelineWorker` when processing
        a `Pipeline`, the ordinal number is 1. The second time that same step
        is executed with an identical *or* a different configuration, the ordinal
        number is 2, as in *`2`nd* execution. And so on. As such this
        integer must be greater than 0.
        """
        self.parent_app: NamedTuple
        self.parent_app = None  # instance of named tuple
        """
        This is a reference to the application's global variables that are
        declared in registry.yaml. 
        During execution of `pacmo.app.PipelineApplication` global variables
        appear as public attributes of the `self.parent_app` object.
        Dereference global variables with global variable names declared in
        registry.yaml. E.g. if global variable "foo" is 
        declared in registry.yaml, then the value of that 
        variable can be accessed with `self.parent_app.foo`.
        """
        self.config: NamedTuple
        self.config = None  # instance of named tuple
        """
        This instance variable allows access to the step parameters
        declared in registry.yaml. During execution of 
        `pacmo.app.PipelineApplication` a step's parameters appear as 
        public attributes of the `self.config` object. E.g. if step
        parameter "foo" is declared in registry.yaml 
        for a step with name `Step.name`, then the value of that parameter 
        can be accessed with `self.config.foo`.
        """
        self.parent_registry = None  # instance of named tuple
        """
        During execution of `pacmo.app.PipelineApplication` this instance
        variable's public attributes will be the names of steps
        registered in `pacmo.config.REGISTRY_FILENAME`. These attributes 
        can then passed into `Step.from_step` one at a time to fetch 
        state elements that may have been published by other steps. 
        E.g. if a step named "foo" with state element "bar" was declared 
        in `pacmo.config.REGISTRY_FILENAME`, then `self.parent_registry` 
        will have a public attribute called `self.parent_registry.foo`, 
        and state element "bar" can be retrieved with 
        `self.from_step(self.parent_registry.foo).fetch_element('bar')`.
        """
        self.operator_id = None  # element owner key for state elements
        """
        This identifier is any object that supports equivalence checking
        with the `==` operator. During execution of `pacmo.app.PipelineApplication`,
        this identifier will be set to the `StateElement.owner` instance 
        variable and can be used to identify which `StateElement` instances
        in `Pipeline.state` "belong" to which `Step` instances.
        """
        self.logger: logging.Logger
        self.logger = None
        """
        Reference to an instance of the python
        [Logger class](https://docs.python.org/3/library/logging.html#logger-objects).
        `Step.logger` can be used to output logs to the log file specified in registry.yaml.
        """
        self.scribe = object()
        """
        Reference to the output generator object for application.
        Not yet implemented.
        """
        self.element_directory: Dict[str, Dict[str, object]]
        self.element_directory = None
        """
        A dictionary object that contains input element provider steps
        """
        self.output_cls_map = None
        """
        A map type where the keys are output element names for the step and
        the values are references to the corresponding class implementations
        of state element containers
        """
        self.element_prefix = None

    def pre_check(self):
        """
        Checks to see if any public attributes are None.

        ### Raises:
        - `pacmo.error.IncorrectInitialization`: `Step` instance
        not properly initialized
        """
        if None in (self.parent_app, self.config,
                    self.parent_registry, self.operator_id,
                    self.ordinal, self.logger, self.scribe):
            raise IncorrectInitialization(
                "Step instance not properly initialized")

    def execute(self):
        """
        Executes the computational logic for a `Step` instance. This
        instance method may only be run by a super class instance of
        a sub class instance of `Step` where the super class is not
        itself `Step` or internally by the framework. The
        [`Step.execute `][4] method that is bound to the parent class
        `Step` does nothing. Place all execution logic that comprise
        the useful work of a step in the execution path of this method.
        [4]: #pacmo.common.Step.execute
        """
        pass

    def check(self):
        """
        Executes checks that are made before [Step.execute][4]
        methods of any `Step` instance in a `Pipeline` is executed.
        This method is useful for catching errors early. This method
        in the parent class `Step` does nothing. Place all logic that
        comprise that checks for conditions required for proper execution
        of the step in the execution path of this method.
        [4]: #pacmo.common.Step.execute
        """
        pass

    def from_step(self, step_obj):
        """
        Sets `step_obj` as the object to compare with `StateElement.owner`
        during the subsequent lookup of `StateElement` instances.

        ### Arguments:
        - `step_obj`: object that allows equivalence checking via the
        `==` operator

        ### Returns:
        - an instance of `StepOutputFetcher`
        """
        return self._fetcher.from_step(step_obj)

    def fetch_input(self, element_name):
        """
        Returns an instance of `ElementContainer` given the registered
        name of a state element in the state element registry.

        ### Arguments:
        - `element_name`: `str` object; name of input element

        ### Returns:
        - an instance of `ElementContainer`

        ### Raises:
        - `pacmo.error.InputElementError`: input state element "name" not
        a requirement of step "name"
        """
        prefixed_name = self.element_prefix + element_name
        allowed_inputs = list(self.element_directory.keys())
        if prefixed_name not in allowed_inputs:
            raise InputElementError(
                'Input element "' + prefixed_name + '" ' +
                'is not a requirement of step "' + self.name +
                '"')
        provider = self.element_directory[prefixed_name]['provider']
        provider_ordinal = self.element_directory[prefixed_name]['ordinal']
        element_obj = self.from_step(provider).fetch_element(prefixed_name, provider_ordinal)
        return element_obj

    def ship_element(self, element_name, element_container: ElementContainer):
        """
        Updates the `StateElement.object` instance variable with
        `element_obj` for the `StateElement` instance with name
        `element_name` for which the calling object is the state
        element owner.

        ### Arguments:
        - `element_name`: str object
        - `element_obj`: a python object

        ### Raises:
        - `pacmo.error.OutputElementError`: Output state element "name" not
        an output of step "name"
        """
        if not isinstance(element_container, ElementContainer):
            raise OutputElementError(
                'Step instances may only share objects that are ' +
                'instances of ElementContainer')
        output_classes = list(self.output_cls_map.values())
        if element_container.__class__ not in output_classes:
            raise OutputElementError(
                'Output state element ' + str(element_container.__class__) +
                ' not an output of step ' + self.name)
        element_container.validate_contents()
        element_obj = element_container.get_element()
        prefixed_name = self.element_prefix + element_name
        self._saver.for_step(self.operator_id).save_element(
            prefixed_name, element_obj, self.ordinal)

    @staticmethod
    def extend_output(output_str):
        """
        This method extends the output file with str `output_str`
        """
        print(str(output_str))

    @staticmethod
    def get_env(conda_prefix: str, env_name: str):
        """
        This method fetches the conda environment as a dict for the
        environment with prefix `env_name`.

        ### Arguments:
        - `conda_prefix`: `str` object; path to where conda is installed
        - `env_name`: `str` object: name of or path to a conda environment
        """
        return get_environment(conda_prefix, env_name)


class PipelineWorker(object):
    """
    A `PipelineWorker` instance's main objective is to
    execute [`Step.execute() `][4] for all `Step` instances in
    `Pipeline.steps` in sequential order. Prior to fulfilling
    its main objective, a `PipelineWorker` instance will
    execute `Step.check` for all steps in the pipeline. This
    allows `Step` instances to check for errors before the
    computational work for a given pipeline begins to execute.
    [4]: #pacmo.common.Step.execute
    """

    def __init__(self, pipeline: Pipeline):
        """
        ### Arguments:
        - `pipeline`: `Pipeline` instance object
        """
        self.pipeline = pipeline
        """
        The `Pipeline` instance that will be processed
        """
        self.current_step = None
        """
        The `Step` instance that is currently executing
        """
        self._starting_step = pipeline.steps[0]
        # NOTE: checkpoint feature currently not ready for use
        self._checkpoint = False
        from .config import CHECKPOINT_FILENAME
        self._checkpoint_name = CHECKPOINT_FILENAME

    def work(self):
        """
        This method *(1)* checks that the prerequisites of all `Step`
        instances are fulfilled, *(2)* executes `Step.check` for all
        steps, and *(3)* executes [`Step.execute() `][4] for all steps.

        ### Raises:
        - `pacmo.error.InadequatePrerequisiteError`: Prerequisite steps
        for step "*step name*" not fulfilled.
        [4]: #pacmo.common.Step.execute
        """
        self._inspect_pipeline()
        self._process_steps()

    def _inspect_pipeline(self):
        steps = self._get_steps()
        for step in steps:
            step.pre_check()
            step.check()

    def _process_steps(self):
        steps = self._get_steps()
        for step in steps:
            self.current_step = step
            process_step = step.__class__.execute
            process_step(self)

    # Not ready for use
    def _get_steps(self):
        steps = []
        include = False
        for step in self.pipeline.steps:
            if step is self._starting_step:
                include = True
            if include:
                steps.append(step)
        return steps

    # Not ready for use
    def _save_pipeline(self):
        cwd = os.path.abspath(os.getcwd())
        file_path = os.path.join(cwd, self._checkpoint_name)
        temp_path = file_path + ".temp"
        back_path = file_path + ".bak"
        try:
            with open(temp_path, 'wb') as fo:
                pickle.dump(self.pipeline, fo, pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e
        if os.path.exists(file_path):
            if os.path.exists(back_path):
                os.remove(back_path)
            os.rename(file_path, back_path)
        os.rename(temp_path, file_path)

    # Not ready for use
    def _set_step(self, step_name, step_ordinal):
        starting_step = None
        for step in self.pipeline.steps:
            if step.name == step_name and step.ordinal == step_ordinal:
                starting_step = step
                break
        if starting_step is None:
            print("Cannot set start step. Step \""
                  + step_name + "\" with ordinal "
                  + str(step_ordinal) + " not present in pipeline")
            raise Exception()
        self._starting_step = starting_step


EnvironmentMap = Dict[str, str]


def get_environment(conda_prefix:str, env_name: str) -> EnvironmentMap:
    """
    This function returns the conda environment with name `env_name`
    as a python dictionary.

    ### Parameters:
    - `conda_prefix`: str object; path to the where conda is installed
    - `env_name`: str object; name of or path to the conda environment

    ### Returns:
    - dict object; type hint is typing.Dict[str,str]

    ### Raises:
    - `pacmo.error.EnvironmentFetchError`
    """
    bash_commands = """
    source {0}/etc/profile.d/conda.sh &> /dev/null || exit 1
    conda activate {1} &> /dev/null || exit 1
    env --null || exit 1
    """.format(conda_prefix, env_name)
    try:
        cp = subprocess.run(['bash', '-c', bash_commands], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        raise EnvironmentFetchError(
            'Failed to activate environment "' +
            str(env_name) + '"')
    stdout_bytes = cp.stdout
    stdout_bytes: bytes
    pair: bytes
    env_list = [pair.decode(encoding='ascii') for pair in stdout_bytes.strip(b'\x00').split(b'\x00')]
    env_map = {}
    for name_value in env_list:
        nv_list = name_value.split('=', maxsplit=1)
        name = nv_list[0]
        value = nv_list[1]
        env_map[name] = value
    env_map: EnvironmentMap
    return env_map


__pdoc__ = {
    'State': False,
    'StateElement': False,
    'PlaceHolder': False,
    'ElementCourier': False,
    'ElementFetcher': False,
    'StepOutputFetcher': False,
    'ElementSaver': False,
    'StepOutputSaver': False,
    'Pipeline': False,
    'StepModel': False,
    'PipelineModel': False,
    'StateBuilder': False,
    'NewStateCreator': False,
    'StateImporter': False,
    'StateFactory': False,
    'PipelineBuilder': False,
    'NewPipelineCreator': False,
    'PipelineImporter': False,
    'PipelineFactory': False,
    'StepMeta': False,
    'Step.pre_check': False,
    'Step.from_step': False,
    'Step.element_directory': False,
    'Step.operator_id': False,
    'Step.ordinal': False,
    'Step.output_cls_map': False,
    'Step.parent_registry': False,
    'Step.scribe': False,
    'Step.state': False,
    'PipelineWorker': False
}

