# -*- coding: utf-8 -*-

# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from typing import Optional

from google.auth import credentials as auth_credentials
from google.cloud.aiplatform import base
from google.cloud.aiplatform import initializer
from google.cloud.aiplatform import (
    PipelineJob,
)
from google.cloud.aiplatform import utils
from google.cloud.aiplatform.compat.types import (
    schedule_v1beta1 as gca_schedule,
)
from google.cloud.aiplatform.preview.constants import (
    schedules as schedule_constants,
)
from google.cloud.aiplatform.preview.schedule.schedules import _Schedule

# TODO(b/283318141): Remove imports once PipelineJobSchedule is GA.
from google.cloud.aiplatform_v1.types import (
    pipeline_job as gca_pipeline_job_v1,
)
from google.cloud.aiplatform_v1beta1.types import (
    pipeline_job as gca_pipeline_job_v1beta1,
)


_LOGGER = base.Logger(__name__)

# Pattern for valid names used as a Vertex resource name.
_VALID_NAME_PATTERN = schedule_constants._VALID_NAME_PATTERN

# Pattern for an Artifact Registry URL.
_VALID_AR_URL = schedule_constants._VALID_AR_URL

# Pattern for any JSON or YAML file over HTTPS.
_VALID_HTTPS_URL = schedule_constants._VALID_HTTPS_URL

_READ_MASK_FIELDS = schedule_constants._PIPELINE_JOB_SCHEDULE_READ_MASK_FIELDS


class PipelineJobSchedule(
    _Schedule,
):
    def __init__(
        self,
        pipeline_job: PipelineJob,
        display_name: str,
        credentials: Optional[auth_credentials.Credentials] = None,
        project: Optional[str] = None,
        location: Optional[str] = None,
    ):
        """Retrieves a PipelineJobSchedule resource and instantiates its
        representation.
        Args:
            pipeline_job (PipelineJob):
                Required. PipelineJob used to init the schedule.
            display_name (str):
                Required. The user-defined name of this PipelineJobSchedule.
            credentials (auth_credentials.Credentials):
                Optional. Custom credentials to use to create this PipelineJobSchedule.
                Overrides credentials set in aiplatform.init.
            project (str):
                Optional. The project that you want to run this PipelineJobSchedule in.
                If not set, the project set in aiplatform.init will be used.
            location (str):
                Optional. Location to create PipelineJobSchedule. If not set,
                location set in aiplatform.init will be used.
        """
        if not display_name:
            display_name = self.__class__._generate_display_name()
        utils.validate_display_name(display_name)

        super().__init__(credentials=credentials, project=project, location=location)

        self._parent = initializer.global_config.common_location_path(
            project=project, location=location
        )

        # TODO(b/283318141): Remove temporary logic once PipelineJobSchedule is GA.
        runtime_config = gca_pipeline_job_v1beta1.PipelineJob.RuntimeConfig.deserialize(
            gca_pipeline_job_v1.PipelineJob.RuntimeConfig.serialize(
                pipeline_job.runtime_config
            )
        )
        create_pipeline_job_request = {
            "parent": self._parent,
            "pipeline_job": {
                "runtime_config": runtime_config,
                "pipeline_spec": {"fields": pipeline_job.pipeline_spec},
            },
        }
        pipeline_job_schedule_args = {
            "display_name": display_name,
            "create_pipeline_job_request": create_pipeline_job_request,
        }

        self._gca_resource = gca_schedule.Schedule(**pipeline_job_schedule_args)

    def create(
        self,
        cron_expression: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        allow_queueing: bool = False,
        max_run_count: Optional[int] = None,
        max_concurrent_run_count: int = 1,
        service_account: Optional[str] = None,
        network: Optional[str] = None,
        create_request_timeout: Optional[float] = None,
    ) -> None:
        """Create a PipelineJobSchedule.

        Args:
            cron_expression (str):
                Required. Time specification (cron schedule expression) to launch scheduled runs.
                To explicitly set a timezone to the cron tab, apply a prefix: "CRON_TZ=${IANA_TIME_ZONE}" or "TZ=${IANA_TIME_ZONE}".
                The ${IANA_TIME_ZONE} may only be a valid string from IANA time zone database.
                For example, "CRON_TZ=America/New_York 1 * * * *", or "TZ=America/New_York 1 * * * *".
            start_time (str):
                Optional. Timestamp after which the first run can be scheduled.
                If unspecified, it defaults to the schedule creation timestamp.
            end_time (str):
                Optional. Timestamp after which no more runs will be scheduled.
                If unspecified, then runs will be scheduled indefinitely.
            allow_queueing (bool):
                Optional. Whether new scheduled runs can be queued when max_concurrent_runs limit is reached.
            max_run_count (int):
                Optional. Maximum run count of the schedule.
                If specified, The schedule will be completed when either started_run_count >= max_run_count or when end_time is reached.
            max_concurrent_run_count (int):
                Optional. Maximum number of runs that can be started concurrently for this PipelineJobSchedule.
            service_account (str):
                Optional. Specifies the service account for workload run-as account.
                Users submitting jobs must have act-as permission on this run-as account.
            network (str):
                Optional. The full name of the Compute Engine network to which the job
                should be peered. For example, projects/12345/global/networks/myVPC.
                Private services access must already be configured for the network.
                If left unspecified, the network set in aiplatform.init will be used.
                Otherwise, the job is not peered with any network.
            create_request_timeout (float):
                Optional. The timeout for the create request in seconds.
        """
        network = network or initializer.global_config.network

        self._create(
            cron_expression=cron_expression,
            start_time=start_time,
            end_time=end_time,
            allow_queueing=allow_queueing,
            max_run_count=max_run_count,
            max_concurrent_run_count=max_concurrent_run_count,
            service_account=service_account,
            network=network,
            create_request_timeout=create_request_timeout,
        )

    def _create(
        self,
        cron_expression: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        allow_queueing: bool = False,
        max_run_count: Optional[int] = None,
        max_concurrent_run_count: int = 1,
        service_account: Optional[str] = None,
        network: Optional[str] = None,
        create_request_timeout: Optional[float] = None,
    ) -> None:
        """Helper method to create the PipelineJobSchedule.

        Args:
            cron_expression (str):
                Required. Time specification (cron schedule expression) to launch scheduled runs.
                To explicitly set a timezone to the cron tab, apply a prefix: "CRON_TZ=${IANA_TIME_ZONE}" or "TZ=${IANA_TIME_ZONE}".
                The ${IANA_TIME_ZONE} may only be a valid string from IANA time zone database.
                For example, "CRON_TZ=America/New_York 1 * * * *", or "TZ=America/New_York 1 * * * *".
            start_time (str):
                Optional. Timestamp after which the first run can be scheduled.
                If unspecified, it defaults to the schedule creation timestamp.
            end_time (str):
                Optional. Timestamp after which no more runs will be scheduled.
                If unspecified, then runs will be scheduled indefinitely.
            allow_queueing (bool):
                Optional. Whether new scheduled runs can be queued when max_concurrent_runs limit is reached.
            max_run_count (int):
                Optional. Maximum run count of the schedule.
                If specified, The schedule will be completed when either started_run_count >= max_run_count or when end_time is reached.
            max_concurrent_run_count (int):
                Optional. Maximum number of runs that can be started concurrently for this PipelineJobSchedule.
            service_account (str):
                Optional. Specifies the service account for workload run-as account.
                Users submitting jobs must have act-as permission on this run-as account.
            network (str):
                Optional. The full name of the Compute Engine network to which the job
                should be peered. For example, projects/12345/global/networks/myVPC.
                Private services access must already be configured for the network.
                If left unspecified, the network set in aiplatform.init will be used.
                Otherwise, the job is not peered with any network.
            create_request_timeout (float):
                Optional. The timeout for the create request in seconds.
        """
        if cron_expression:
            self._gca_resource.cron = cron_expression
        if start_time:
            self._gca_resource.start_time = start_time
        if end_time:
            self._gca_resource.end_time = end_time
        if allow_queueing:
            self._gca_resource.allow_queueing = allow_queueing
        if max_run_count:
            self._gca_resource.max_run_count = max_run_count
        if max_concurrent_run_count:
            self._gca_resource.max_concurrent_run_count = max_concurrent_run_count

        network = network or initializer.global_config.network

        if service_account:
            self._gca_resource.create_pipeline_job_request.pipeline_job.service_account = (
                service_account
            )

        if network:
            self._gca_resource.create_pipeline_job_request.pipeline_job.network = (
                network
            )

        _LOGGER.log_create_with_lro(self.__class__)

        self._gca_resource = self.api_client.create_schedule(
            parent=self._parent,
            schedule=self._gca_resource,
            timeout=create_request_timeout,
        )

        _LOGGER.log_create_complete_with_getter(
            self.__class__, self._gca_resource, "schedule"
        )

        _LOGGER.info("View Schedule:\n%s" % self._dashboard_uri())
