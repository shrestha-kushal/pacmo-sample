#       _         _         _         _         _
#     _( )__    _( )__    _( )__    _( )__    _( )__
#   _|     _| _|     _| _|     _| _|     _| _|     _|
#  (_ P _ (_ (_ A _ (_ (_ C _ (_ (_ M _ (_ (_ O _ (_
#    |_( )__|  |_( )__|  |_( )__|  |_( )__|  |_( )__|

"""
The `pacmo.app` module contains python object definitions that
initialize and execute the application.
"""


from .config import InputReader
from .config import UserDelegate
from .common import NewPipelineCreator
from .common import PipelineFactory
from .common import PipelineWorker
from .config import WORK_DIRECTORY
from .error import NotPrimaryPipelineError
from .error import Error
import os
import sys
from io import IOBase
import logging
import pyaml
from collections import OrderedDict
from copy import deepcopy
from time import sleep
import pkgutil


class PipelineApplication(object):
    """
    Objects of type `PipelineApplication` creates all necessary objects
    that allow for the proper execution of a pipeline chosen with user_input.yaml.

    ### Raises:
    - `pacmo.error.NotPrimaryPipelineError`
    """

    def __init__(
        self,
        registry_module=None,
        external_registries=None,
        primary_pipeline=None
    ):
        self._primary_pipeline = primary_pipeline
        self._primary_registry = registry_module
        if external_registries is None:
            external_registries = []
        self._external_registries = external_registries
        self._input_reader = InputReader()
        self._user_delegate = self._init_delegate()
        self._check_primary_pipeline()
        self._pipeline = None
        self._output = None

    def _init_delegate(self):
        input_map = self._input_reader.get_user_input_map()
        return UserDelegate(
            input_map, self._primary_registry, self._external_registries)

    def get_pipeline(self):
        """
        This method returns a new instance of `pacmo.common.Pipeline`
        with every invocation of this method.

        ### Returns:
        - `pacmo.common.Pipeline` instance
        """
        builder = NewPipelineCreator(self._user_delegate)
        factory = PipelineFactory(builder)
        pipeline = factory.produce_pipeline()
        return pipeline

    def _check_primary_pipeline(self):
        if self._primary_pipeline is None:
            return
        chosen_pipeline = self._user_delegate.convey_chosen_pipeline()
        if chosen_pipeline != self._primary_pipeline:
            raise NotPrimaryPipelineError(
                'The user requested pipeline "' + chosen_pipeline +
                '" is not the primary pipeline that was expected. ' +
                'Expected pipeline: "' + str(self._primary_pipeline) +
                '".')

    def _init_io(self):
        from .common import Pipeline
        self._pipeline: Pipeline
        output_file = self._pipeline.global_vars.output_file
        error_file = self._pipeline.global_vars.error_file
        try:
            from mpi4py import MPI
        except Exception:
            # case where MPI.cpython-3[X]-x86_64-linux-gnu.so fails to load
            # because the MPI client libraries are not found in the
            # environment. Will assume that pipeline is to be run
            # sequentially or with slurm job array. Pipelines that rely
            # on MPI will eventually raise an exception, but pipelines
            # that don't will run normally.
            if _in_job_array():
                _check_slurm()
                self._init_slurm_io(output_file, error_file)
            else:
                self._init_io_files(output_file, error_file)
        else:
            comm = MPI.COMM_WORLD
            rank = comm.Get_rank()
            size = comm.Get_size()
            if _in_job_array():
                _check_slurm()
                if size != 1:
                    output_file = self._slurmed_file_name(output_file)
                    error_file = self._slurmed_file_name(error_file)
                    if rank == 0:
                        self._init_io_files(output_file, error_file)
                    comm.Barrier()
                else:
                    self._init_slurm_io(output_file, error_file)
            else:
                if rank == 0:
                    self._init_io_files(output_file, error_file)
                comm.Barrier()
        self._output = open(output_file, 'a')
        self._error = open(error_file, 'a')
        sys.stdout = self._output
        sys.stderr = self._error
        logging.basicConfig(filename=error_file, filemode='a', level=logging.DEBUG)

    def _init_slurm_io(self, output_file, error_file):
        task_id = int(os.environ['SLURM_ARRAY_TASK_ID'])
        lock_file = os.path.join(os.getcwd(), '.pacmo_lock')
        if task_id == 0:
            with open(lock_file, 'w') as fo:
                fo.write('locked')
            self._init_io_files(output_file, error_file)
            with open(lock_file, 'w') as fo:
                fo.write('unlocked')
        else:
            self._slurm_barrier(lock_file)

    def _init_io_files(self, output_file, error_file):
        open(output_file, 'w').close()
        self._splash(output_file)
        open(error_file, 'w').close()

    @staticmethod
    def _slurm_barrier(lock_file):
        locked = True
        elapsed = 0.0
        interval = 0.3
        max_time = 400.0
        while locked:
            sleep(interval)
            elapsed += interval
            if os.path.exists(lock_file):
                break
            if elapsed > max_time:
                raise SlurmError(
                    'Timed out while setting up IO ' +
                    'for SLURM job array feature.')
        elapsed = 0.0
        while locked:
            sleep(interval)
            elapsed += interval
            with open(lock_file, 'r') as fo:
                unlock = fo.read().strip().lower()
            if unlock == 'unlocked':
                break
            if elapsed > max_time:
                raise SlurmError(
                    'Timed out while setting up IO ' +
                    'for SLURM job array feature.')

    @staticmethod
    def _slurmed_file_name(filename):
        task_id = int(os.environ['SLURM_ARRAY_TASK_ID'])
        suffix = str(10000000 + task_id)[1:]
        if len(filename.split('.')) > 1:
            ext = filename.split('.')[-1]
            prefix = ''.join(filename.split('.')[:-1])
        else:
            prefix = filename
            ext = ''
        slurmed_name = prefix + '_' + suffix + '.' + ext
        return slurmed_name

    def _splash(self, output_file):
        with open(output_file, 'w') as fo:
            banner = self._get_banner()
            fo.write(banner)
        with open(output_file, 'a') as fo:
            p_config = pyaml.dumps(
                self._get_pipeline_config(),
                string_val_style='"',
                vspacing=[1, 1],
                force_embed=True)
            p_config = p_config + \
                b'\n-------------------***BEGIN-----EXECUTION***-------------------\n\n'
            fo.write(p_config.decode(encoding='ascii'))

    def _get_pipeline_config(self):
        return _get_pipeline_config(self._pipeline)

    def _get_banner(self):
        file_bytes: bytes
        file_bytes = pkgutil.get_data(self.__class__.__module__, 'banner.txt')
        return file_bytes.decode(encoding='ascii')

    def run_single_pipeline(self):
        """
        This method executes all logic within all `pacmo.common.Step`s
        for a chosen pipeline.
        """
        self._pipeline = self.get_pipeline()
        self._init_io()
        worker = PipelineWorker(self._pipeline)
        worker.work()
        self._output: IOBase
        self._error: IOBase
        self._output.close()
        self._error.close()


def _get_pipeline_config(pipeline):
    """
    This function returns the configuration of `pipeline` as
    a `dict`.

    ### Arguments:
    - `pipeline`: instance of `pacmo.common.Pipeline`

    ### Returns:
    - `str` object that represents the pipeline configuration
    """
    from .common import Pipeline, Step
    pipeline: Pipeline
    config = OrderedDict()
    config['GLOBAL_VARIABLES'] = pipeline.global_vars
    config['PIPELINE_NAME'] = pipeline.name
    step_configs = []
    step: Step
    for i, step in enumerate(pipeline.steps):
        step_label = "STEP_" + str(i + 1)
        step_config = OrderedDict()
        step_config["STEP_NAME"] = step.name
        step_config["STEP_CLASS"] = step.__class__.__module__ + '.' + step.__class__.__name__
        step_config["STEP_PARAMETERS"] = step.config
        step_config["INPUT_ELEMENTS"] = step.element_directory
        out_elem_map = deepcopy(step.output_cls_map)
        for elem in out_elem_map:
            elem_cls = out_elem_map[elem]
            out_elem_map[elem] = elem_cls.__module__ + '.' + elem_cls.__name__
        step_config["OUTPUT_ELEMENTS"] = out_elem_map
        step_configs.append({step_label: step_config})
    config['PIPELINE_CONFIGURATION'] = step_configs
    return config


def _in_job_array():
    is_in = False
    needed_vars = {
        'SLURM_ARRAY_TASK_MIN',
        'SLURM_ARRAY_TASK_MAX',
        'SLURM_ARRAY_TASK_ID',
        'SLURM_ARRAY_TASK_COUNT',
        'SLURM_ARRAY_TASK_STEP'
    }
    provided_vars = []
    for env_var in os.environ:
        if env_var in needed_vars:
            provided_vars.append(env_var)
    if set(provided_vars) == needed_vars:
        is_in = True
    return is_in


def _check_slurm():
    if _in_job_array():
        try:
            n_task = int(os.environ['SLURM_ARRAY_TASK_COUNT'])
            min_tid = int(os.environ['SLURM_ARRAY_TASK_MIN'])
            max_tid = int(os.environ['SLURM_ARRAY_TASK_MAX'])
            task_step = int(os.environ['SLURM_ARRAY_TASK_STEP'])
            task_id = int(os.environ['SLURM_ARRAY_TASK_ID'])
        except Exception:
            raise SlurmError(
                'Slurm job array feature enabled but job array ' +
                'environmental variables failed to convert to ' +
                'Python int.')
        if task_step != 1:
            raise SlurmError(
                '"SLURM_ARRAY_TASK_STEP" must be 1.')
        if min_tid != 0:
            raise SlurmError(
                '"SLURM_ARRAY_TASK_MIN" must be 0.')
        if max_tid != n_task - 1:
            raise SlurmError(
                '"SLURM_ARRAY_TASK_MAX" must be ' +
                '"SLURM_ARRAY_TASK_COUNT" - 1.')
        if task_id not in range(min_tid, n_task):
            raise SlurmError(
                '"SLURM_ARRAY_TASK_ID" must be within ' +
                'range(SLURM_ARRAY_TASK_MIN, SLURM_ARRAY_TASK_MAX)')


class SlurmError(Error):
    """
    This exception is appropriate to raise when the SLURM job array
    feature is used but configured incorrectly.
    """


__pdoc__ = {
    'SlurmError': False,
    'PipelineApplication.get_pipeline': False
}

