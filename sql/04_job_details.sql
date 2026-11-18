CREATE TABLE IF NOT EXISTS job_details (
    job_id         INT UNSIGNED NOT NULL,
    description    TEXT         NULL,
    requirements   TEXT         NULL,
    benefits       TEXT         NULL,
    summary        TEXT         NULL,
    summary_model  VARCHAR(50)  NULL,
    fetched_at     DATETIME     NOT NULL,
    summarized_at  DATETIME     NULL,
    PRIMARY KEY (job_id),
    CONSTRAINT fk_job_details_job FOREIGN KEY (job_id) REFERENCES jobs (job_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;