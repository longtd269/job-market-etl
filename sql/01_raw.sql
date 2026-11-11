-- Bronze, Stagging
-- columns csv: created_date	job_title	company	salary	address	time	link_description
CREATE TABLE IF NOT EXISTS raw_jobs (
    row_id INT UNSIGNED NOT NULL,
    created_date VARCHAR(20) NULL,
    job_title VARCHAR(500) NULL,
    company VARCHAR(500) NULL,
    salary VARCHAR(100) NULL,
    address TEXT NULL,
    `time` VARCHAR(100) NULL,
    link_description VARCHAR(1000) NULL,
    source_file VARCHAR(255) NOT NULL,
    loaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (row_id)
)  ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;