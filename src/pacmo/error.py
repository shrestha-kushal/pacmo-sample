"""
The `pacmo.error` module contains python object definitions
that comprise the application-level exception hierarchy.
"""


class Error(Exception):
    """
    This is the base Exception class for the project. All
    handled exceptions within this project should inherit from
    `pacmo.error.Error`
    """


class IncorrectArgumentType(Error):
    """
    This exception is appropriate to raise when an input argument
    object to a callable type is not of the expected object type.
    """


class StateElementNotFound(Error):
    """
    This exception is appropriate to raise when there are no matching
    state elements in the state of a pipeline given a state element
    request by a `pacmo.common.Step` instance.
    """


class OperationOutOfOrder(Error):
    """
    This exception is appropriate to raise when an operation has been
    executed out of its intended order.
    """


class IncorrectCallerObject(Error):
    """
    This exception is appropriate to raise when the object that calls
    a callable object is not the intended caller object.
    """


class IncorrectArgumentSignature(Error):
    """
    This exception is appropriate to raise when the argument
    signature of a callable object is not the intended argument
    signature.
    """


class IncorrectClassDefinition(Error):
    """
    This exception is appropriate to raise when a class definition
    does not follow the intended coding conventions.
    """


class IncorrectInitialization(Error):
    """
    This exception is appropriate to raise when public attributes of
    objects have not been initialized as intended.
    """


class StepExecutionError(Error):
    """
    This is the base exception class for exceptions that are raised
    during execution of [`Step.execute `][1].
    [1]: ./common.html#pacmo.common.Step.execute
    """


class InadequatePrerequisiteError(Error):
    """
    This exception is appropriate to raise when prerequisite conditions
    for proper execution is not met.
    """


class StepCheckError(Error):
    """
    This is the base exception class for exceptions that are raised
    during execution of the `pacmo.common.Step.check` method.
    """


class UnknownStepParameter(Error):
    """
    This exception should be raised when a parameter that is not
    registered of any `pacmo.common.Step` is supplied to the application.
    """


class ConfigurationError(Error):
    """
    This is the base exception class for all exceptions that arise
    during the initial configuration of the application.
    """


class ApplicationRegistryError(ConfigurationError):
    """
    This exception is appropriate to raise when errors are encountered
    during the parsing of the application registry file.
    """


class GlobalsRegistryError(ConfigurationError):
    """
    This exception is appropriate to raise when errors are encountered
    within the global parameters registry section of the application
    registry file.
    """


class UserConfigurationError(ConfigurationError):
    """
    This exception is appropriate to raise when errors are encountered
    with the user level configuration provided in the user input yaml
    file.
    """


class PipelinesRegistryError(ConfigurationError):
    """
    This exception is appropriate to raise when errors are encountered
    in the pipelines registry section of the application registry
    file.
    """


class ElementsRegistryError(ConfigurationError):
    """
    This exception is appropriate to raise when errors are encountered
    in the elements registry section of the application registry file.
    """


class StepsRegistryError(ConfigurationError):
    """
    This exception is appropriate to raise when errors are encountered
    in the steps registry section of the application registry file.
    """


class StepNotFoundError(Error):
    """
    This exception is appropriate to raise when information is requested
    about a step that is not registered in the step registry section of
    the application registry file.
    """


class OutputElementError(StepExecutionError):
    """
    This exception is appropriate to raise when a step carries out
    operations with output elements in an unexpected manner.
    """


class InputElementError(StepExecutionError):
    """
    This exception is appropriate to raise when a step carries out
    operations with input elements in an unexpected manner
    """


class EnvironmentFetchError(Error):
    """
    This exception is appropriate to raise when a requested Conda
    environment is not found or the mechanism to fetch the environment
    encounters an error.
    """


class InputParameterError(StepCheckError):
    """
    This exception is appropriate to raise when an input parameter
    is not what is expected by the consumer of the parameter.
    """


class ElementValidationError(StepExecutionError):
    """
    This exception is appropriate to raise when the state
    element passed into an element container fails validation
    tests.
    """


class NotPrimaryPipelineError(Error):
    """
    This exception is appropriate to raise when a pipeline requested
    by the user is not the primary pipeline that was intended to be
    executed by the application.
    """


class ElementPrefixError(ConfigurationError):
    """
    This exception is appropriate to raise when an appropriate prefix to
    an element name cannot be determined.
    """