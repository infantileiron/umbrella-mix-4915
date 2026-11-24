CREATE TABLE users (
    username VARCHAR(32) PRIMARY KEY,
    display_name VARCHAR(40) NOT NULL,
    password_hash VARCHAR(180) NOT NULL,
    role ENUM('owner','analyst','observer') NOT NULL
) CHARACTER SET utf8mb4;

CREATE TABLE tickets (
    code VARCHAR(32) PRIMARY KEY,
    branch ENUM('north','south') NOT NULL,
    worked_on DATE NOT NULL,
    ribs TINYINT UNSIGNED NOT NULL,
    fabric TINYINT UNSIGNED NOT NULL,
    mechanism TINYINT UNSIGNED NOT NULL,
    minutes SMALLINT UNSIGNED NOT NULL,
    note VARCHAR(180) NOT NULL,
    revision INT UNSIGNED NOT NULL DEFAULT 1,
    INDEX ticket_window (branch, worked_on)
) CHARACTER SET utf8mb4;

CREATE TABLE comparison_plans (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    plan_key VARCHAR(32) NOT NULL,
    version INT UNSIGNED NOT NULL,
    label VARCHAR(100) NOT NULL,
    focus_branch ENUM('north','south') NOT NULL,
    control_branch ENUM('north','south') NOT NULL,
    coefficient_ref ENUM('focus','control') NOT NULL,
    date_from DATE NOT NULL,
    date_to DATE NOT NULL,
    min_samples SMALLINT UNSIGNED NOT NULL,
    created_by VARCHAR(32) NOT NULL,
    UNIQUE KEY plan_version (plan_key, version),
    FOREIGN KEY (created_by) REFERENCES users (username)
) CHARACTER SET utf8mb4;

CREATE TABLE analysis_runs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    plan_id BIGINT UNSIGNED NOT NULL,
    status ENUM('queued','running','completed','failed') NOT NULL DEFAULT 'queued',
    snapshot JSON NOT NULL,
    snapshot_sha CHAR(64) NOT NULL,
    result JSON,
    failure VARCHAR(240),
    claim_token CHAR(32),
    claimed_at DATETIME(6),
    created_by VARCHAR(32) NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    finished_at DATETIME(6),
    INDEX queue_order (status, id),
    FOREIGN KEY (plan_id) REFERENCES comparison_plans (id),
    FOREIGN KEY (created_by) REFERENCES users (username)
) CHARACTER SET utf8mb4;

CREATE TABLE improvement_drafts (
    run_id BIGINT UNSIGNED PRIMARY KEY,
    action_text VARCHAR(1000) NOT NULL,
    status ENUM('draft','published') NOT NULL,
    edited_by VARCHAR(32) NOT NULL,
    edited_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    FOREIGN KEY (run_id) REFERENCES analysis_runs (id),
    FOREIGN KEY (edited_by) REFERENCES users (username)
) CHARACTER SET utf8mb4;

CREATE TABLE audit_events (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    actor VARCHAR(32) NOT NULL,
    action VARCHAR(36) NOT NULL,
    subject VARCHAR(64) NOT NULL,
    occurred_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4;
