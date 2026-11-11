CREATE OR REPLACE VIEW v_job_salary AS
SELECT 
    j.id, 
    j.job_group, 
    j.job_level, 
    j.salary_unit,
    COALESCE((j.min_salary + j.max_salary) / 2, j.min_salary, j.max_salary) 
        * CASE WHEN j.salary_unit = 'USD' THEN 25000 ELSE 1 END
        / 1000000 AS salary_million_vnd
FROM jobs AS j
WHERE j.salary_unit IS NOT NULL;

CREATE OR REPLACE VIEW v_area_jobs AS
SELECT
    l.city,
    COUNT(DISTINCT l.job_id) AS n_jobs
FROM job_locations AS l
GROUP BY l.city;


CREATE OR REPLACE VIEW v_technology_jobs AS
SELECT
    t.technology,
    COUNT(*) AS n_jobs
FROM job_technologies AS t
GROUP BY t.technology

CREATE OR REPLACE VIEW v_active_jobs AS
SELECT *
FROM jobs
WHERE last_seen = (SELECT MAX(last_seen) FROM jobs)

CREATE OR REPLACE VIEW v_daily_jobs AS
SELECT
    d.batch_date
    (SELECT COUNT(*) FROM jobs WHERE first_seen = d.batch_date) AS new_jobs,
    (SELECT COUNT(*) FROM jobs WHERE first_seen <= d.batch_date AND last_seen >= d.batch_date) AS active_jobs
FROM (SELECT DISTINCT last_seen AS batch_date FROM jobs
    UNION
    SELECT DISTINCT first_seen FROM jobs) AS d