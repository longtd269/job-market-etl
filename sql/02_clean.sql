CREATE TABLE IF NOT EXISTS jobs (
    job_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    created_date DATE NULL,
    job_title VARCHAR(500) NOT NULL,
    job_group VARCHAR(50) NULL,
    job_level VARCHAR(20) NULL,
    company VARCHAR(500)  NULL,
    salary VARCHAR(100)  NULL,
    min_salary DECIMAL(15,2) NULL,
    max_salary DECIMAL(15,2) NULL,
    salary_unit VARCHAR(3) NULL,
    `address` TEXT NULL,
    link_description VARCHAR(500) NOT NULL,
    first_seen DATE NOT NULL,
    last_seen DATE NOT NULL,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (job_id),
    UNIQUE KEY uq_jobs_link (link_description),
    KEY idx_jobs_last_seen (last_seen)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS load_jobs_batch (
    row_id INT UNSIGNED NOT NULL,
    created_date DATE NULL,
    job_title VARCHAR(500) NOT NULL,
    job_group VARCHAR(50) NULL,
    job_level VARCHAR(20) NULL,
    company VARCHAR(500)  NULL,
    salary VARCHAR(100)  NULL,
    min_salary DECIMAL(15,2) NULL,
    max_salary DECIMAL(15,2) NULL,
    salary_unit VARCHAR(3) NULL,
    `address` TEXT NULL,
    link_description VARCHAR(500) NOT NULL,
    PRIMARY KEY (row_id),
    UNIQUE KEY uq_batch_link (link_description)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS job_locations (
    job_id INT UNSIGNED NOT NULL,
    location_order SMALLINT UNSIGNED NOT NULL,
    city VARCHAR(50) NOT NULL,
    district VARCHAR(100) NULL,
    PRIMARY KEY (job_id, location_order),
    KEY idx_job_locations_city (city),
    CONSTRAINT fk_job_locations_job FOREIGN KEY (job_id) REFERENCES jobs (job_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS job_technologies (
    job_id INT UNSIGNED NOT NULL,
    technology VARCHAR(50) NOT NULL,
    PRIMARY KEY (job_id, technology),
    KEY idx_job_technologies_tech (technology),
    CONSTRAINT fk_job_technologies_job FOREIGN KEY (job_id) REFERENCES jobs (job_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;