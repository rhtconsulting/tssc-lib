"""
Step Implementer for the container-image-static-compliance-scan step for OpenSCAP.
"""

from tssc import TSSCFactory
from tssc import StepImplementer
from tssc import DefaultSteps

DEFAULT_ARGS = {}

class OpenSCAP(StepImplementer):
    """
    StepImplementer for the container-image-static-compliance-scan step for OpenSCAP.
    """

    def __init__(self, config, results_dir, results_file_name, work_dir_path):
        super().__init__(config, results_dir, results_file_name, work_dir_path, DEFAULT_ARGS)

    @classmethod
    def step_name(cls):
        return DefaultSteps.CONTAINER_IMAGE_STATIC_COMPLIANCE_SCAN

    def _validate_step_config(self, step_config):
        """
        Function for implementers to override to do custom step config validation.

        Parameters
        ----------
        step_config : dict
            Step configuration to validate.
        """

    def _run_step(self, runtime_step_config):
        results = {
        }

        return results

# register step implementer
TSSCFactory.register_step_implementer(OpenSCAP)
