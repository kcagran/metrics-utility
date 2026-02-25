from datetime import datetime


def get_where_clause(since: datetime, until: datetime) -> str:
    """
    Generate SQL WHERE clause for filtering jobs by execution date range.
    Excludes sync jobs and includes only jobs with status 'failed' or 'successful'.

    Args:
        since: Start of date range (inclusive)
        until: End of date range (exclusive)

    Returns:
        SQL WHERE clause string
    """
    return f"""
            WHERE uj.launch_type != 'sync'
            AND (uj.status='failed' OR uj.status = 'successful')
            AND uj.modified >= '{since.isoformat()}'
            AND uj.modified < '{until.isoformat()}'
        """


def get_job_templates_query(since: datetime | None) -> str:
    """
    Generate SQL query to fetch job templates.

    Args:
        since: Start of date range (exclusive). If None, fetch all job templates.

    Returns:
        SQL query string

    Database schema:
        - main_unifiedjobtemplate
        - main_jobtemplate (to filter only job templates)
    """
    where_clause = f" WHERE ujt.modified > '{since.isoformat()}'" if since else ""
    return f"""
           SELECT ujt.id,
                  ujt.name,
                  ujt.description,
                  ujt.created,
                  ujt.modified
           FROM main_unifiedjobtemplate ujt
           JOIN main_jobtemplate jt on jt.unifiedjobtemplate_ptr_id = ujt.id
           {where_clause}
           """


def get_job_labels_query(since: datetime, until: datetime) -> str:
    """
    Generate SQL query to fetch job labels for jobs executed within the specified date range.

    Args:
        since: Start of date range (inclusive)
        until: End of date range (exclusive)

    Returns:
        SQL query string

    Database schema:
        - main_unifiedjob_labels
        - main_unifiedjob (for filtering by date range)
    """
    where_clause = get_where_clause(since, until)
    return f"""
            SELECT  
                l.unifiedjob_id,
                l.label_id
            FROM main_unifiedjob_labels l
            JOIN main_unifiedjob uj on uj.id = l.unifiedjob_id
            {where_clause}
           ORDER BY l.unifiedjob_id
        """


def get_job_host_summaries_query(since: datetime, until: datetime) -> str:
    """
    Generate SQL query to fetch job host summaries for jobs executed within the specified date range.

    Args:
        since: Start of date range (inclusive)
        until: End of date range (exclusive)

    Returns:
        SQL query string

    Database schema:
        - main_jobhostsummary
        - main_unifiedjob (for filtering by date range)
    """
    where_clause = get_where_clause(since, until)
    return f"""
         SELECT  
            hs.id,
	        hs.host_name,
	        hs.changed,
	        hs.dark,
	        hs.failures,
	        hs.ok,
	        hs.processed,
	        hs.skipped,
	        hs.failed,
	        hs.ignored,
	        hs.rescued,
	        hs.host_id,
	        hs.job_id
        FROM main_jobhostsummary hs
        JOIN main_unifiedjob uj on uj.id = hs.job_id
         {where_clause}
         order by hs.job_id
        """


def get_jobs_query(since: datetime, until: datetime) -> str:
    """
    Generate SQL query to fetch jobs executed within the specified date range.

    Args:
        since: Start of date range (inclusive)
        until: End of date range (exclusive)

    Returns:
        SQL query string

    Database schema:
        - main_unifiedjob
        - main_job
        - main_unifiedjobtemplate
        - auth_user
        - main_project
        - main_unifiedjobtemplate
    """
    where_clause = get_where_clause(since, until)
    return f"""
         SELECT 
	        uj.id,
            COALESCE(ujt.name, uj.name) as name,
	        uj.unified_job_template_id,
	        uj.organization_id,
	        uj.started,
            uj.finished,
            uj.status,
            uj.elapsed,
	        CASE 
                WHEN 
                    uj.launch_type ='manual' or uj.launch_type ='relaunch' then u.id 
                ELSE null
	        END as launched_by_id,
	        CASE 
		        WHEN 
			        uj.launch_type ='manual' or uj.launch_type ='relaunch' then u.username 
		        ELSE null
	        END as launched_by_username,
	        mj.project_id,
	        ujp.name as project_name,
	        uj.created,
	        uj.modified
        FROM main_unifiedjob uj
        JOIN main_job mj on mj.unifiedjob_ptr_id = uj.id
        LEFT JOIN main_unifiedjobtemplate ujt ON ujt.id = uj.unified_job_template_id
        LEFT JOIN auth_user u on u.id = uj.created_by_id
        LEFT JOIN main_project pj on pj.unifiedjobtemplate_ptr_id = mj.project_id
        LEFT JOIN main_unifiedjobtemplate ujp on ujp.id = mj.project_id
         {where_clause}
         order by uj.modified
        """
