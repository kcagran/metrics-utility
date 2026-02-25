"""Collector functions for dashboard metrics.

These collectors use the @register decorator pattern from metrics-utility to
define data collection functions that can be called by metrics-service.

Each collector:
1. Executes SQL queries against the AWX database
2. Processes results to match automation-reports data format
3. Returns JSON-serializable data structures
"""
import decimal
from datetime import datetime
from typing import Any, List, TypedDict

from metrics_utility.base import register
from metrics_utility.library.collectors.dashboard.queries import (
    get_job_host_summaries_query,
    get_job_labels_query,
    get_job_templates_query,
    get_jobs_query
)


class   AWXJobHostSummaryType(TypedDict):
    id: int
    job_id: int
    host_name: str
    changed: int
    dark: int
    failures: int
    ok: int
    processed: int
    skipped: int
    failed: bool
    ignored: int
    rescued: int
    host_id: int | None


class AwxCommonType(TypedDict):
    id: int
    created: datetime | None
    modified: datetime | None


class AwxJobTemplateType(AwxCommonType):
    id: int
    name: str
    description: str | None


class DashboardJobTemplateResultType(TypedDict):
    count: int
    results: List[AwxJobTemplateType]


class AWXJobType(AwxCommonType):
    aap_id: int
    name: str
    status: str
    created: datetime
    modified: datetime
    unified_job_template_id: int
    organization_id: int | None
    started: datetime | None
    finished: datetime | None
    elapsed: decimal.Decimal
    launched_by_id: int | None
    launched_by_username: str | None
    project_id: int | None
    project_name: str | None


class DashboardJobsResultType(TypedDict):
    count: int
    results: List[AWXJobType]


@register('dashboard_job_labels', '1.0', format='json',
          description='Labels used in jobs for automation-reports dashboard')
def dashboard_job_labels(since: datetime, until: datetime, db, **kwargs) -> dict[int, list[int]]:
    """
    Collect job labels for the dashboard.

    This collector retrieves all labels associated with jobs executed within the specified date range.

    Args:
        since: Start of date range (inclusive)
        until: End of date range (exclusive)
        db: Database connection
        **kwargs: Additional parameters

    Returns:
        Dict with keys:
            - unifiedjob_id: list of label IDs associated with the job

    Output format:
    {
        job_id_1: [label_id_1, label_id_2, ...],
        job_id_2: [label_id_3, label_id_4, ...],
        ...
    }
    """

    query = get_job_labels_query(since, until)
    result = {}
    with db.cursor() as cursor:
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        for row in cursor.fetchall():
            data = dict(zip(columns, row))
            job_id = data['unifiedjob_id']
            label_id = data['label_id']
            tmp = result.get(job_id, [])
            tmp.append(label_id)
            result[job_id] = tmp
        cursor.close()
    return result


@register('dashboard_job_host_summaries', version='1.0', format='json',
          description='Job host summaries used in jobs for automation-reports dashboard')
def dashboard_job_host_summaries(since: datetime, until: datetime, db, **kwargs) -> dict[
    int, list[AWXJobHostSummaryType]]:
    """
    Collect job host summaries for the dashboard.

    This collector retrieves host summary data for jobs executed within the specified date range.

    Args:
        since: Start of date range (inclusive)
        until: End of date range (exclusive)
        db: Database connection
        **kwargs: Additional parameters

    returns:
        Dict with keys:
            - unifiedjob_id: list of host summary dicts associated with the job

    Output format:
    {
        job_id_1: [
            {
                id: int,
                job_id: int,
                host_name: str,
                changed: int,
                dark: int,
                failures: int,
                ok: int,
                processed: int,
                skipped: int,
                failed: bool,
                ignored: int,
                rescued: int,
                host_id: int | None
            },
            ...],
        ...
    }
    """
    query = get_job_host_summaries_query(since, until)
    result = {}
    with db.cursor() as cursor:
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        for row in cursor.fetchall():
            data = dict(zip(columns, row))
            job_id = data['job_id']
            host_summary = {
                'id': data['id'],
                'job_id': data['job_id'],
                'host_id': data['host_id'],
                'host_name': data['host_name'],
                'changed': data['changed'],
                'dark': data['dark'],
                'failures': data['failures'],
                'ignored': data['ignored'],
                'ok': data['ok'],
                'processed': data['processed'],
                'rescued': data['rescued'],
                'skipped': data['skipped'],
                'failed': data['failed']
            }
            tmp = result.get(job_id, [])
            tmp.append(host_summary)
            result[job_id] = tmp
        cursor.close()
    return result


@register('dashboard_job_templates', version='1.0', format='json',
          description='Job template data for automation-reports dashboard')
def dashboard_job_templates(since: datetime | None, db, **kwargs) -> DashboardJobTemplateResultType:
    """
    Collect job templates for the dashboard.

    This collector retrieves newly created or updated job templates since the specified date.
    If 'since' is None, it retrieves all job templates (at initial sync).

    Args:
        since: Optional datetime to filter job templates created or modified since this date.
        db: Database connection
        **kwargs: Additional parameters

    Returns:
        dict with keys:
            - count: total number of job templates retrieved
            - results: list of job template dicts with job template data

    Output format:
    {
        count: int,
        results: [
            {
                id: int,
                name: str,
                description: str | None,
                created: datetime,
                modified: datetime,
            },... ]
    """

    query = get_job_templates_query(since)
    with db.cursor() as cursor:
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        results = []
        for row in cursor.fetchall():
            data = dict(zip(columns, row))
            result = {
                'id': data['id'],
                'name': data['name'],
                'description': data['description'],
                'created': data['created'],
                'modified': data['modified']
            }
            results.append(result)
        cursor.close()

    return {
        'count': len(results),
        'results': results
    }


@register('dashboard_jobs', version='1.0', format='json', description='Jobs for automation-reports dashboard')
def dashboard_jobs(since: datetime, until: datetime, db, **kwargs) -> DashboardJobsResultType:
    """
    Collect job data for the dashboard.

    This collector retrieves job data for jobs executed within the specified date range.

    Args:
        since: Start of date range (inclusive)
        until: End of date range (exclusive)
        db: Database connection
        **kwargs: Additional parameters

    Returns:
        dict with keys:
            - count: total number of jobs retrieved
            - results: list of job dicts with job data

    Output format:
        {
            count: int,
            results: [
            {
                id: int,
                name: str,
                unified_job_template_id: int | None,
                organization_id: int | None,
                started: datetime | None,
                finished: datetime | None,
                status: str,
                elapsed: Decimal,
                launched_by_id: int | None,
                launched_by_username : str | None,
                project_id: int | None,
                project_name: str | None,
                created: datetime,
                modified: datetime
            }, ... ] }

    """
    query = get_jobs_query(since, until)
    with db.cursor() as cursor:
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        results = []
        for row in cursor.fetchall():
            data = dict(zip(columns, row))
            result = {
                'id': data['id'],
                'name': data['name'],
                'unified_job_template_id': data['unified_job_template_id'],
                'organization_id': data['organization_id'],
                'started': data['started'],
                'finished': data['finished'],
                'status': data['status'],
                'elapsed': data['elapsed'],
                'launched_by_id': data['launched_by_id'],
                'launched_by_username': data['launched_by_username'],
                'project_id': data['project_id'],
                'project_name': data['project_name'],
                'created': data['created'],
                'modified': data['modified']
            }
            results.append(result)
        cursor.close()
    return {'count': len(results), 'results': results}
