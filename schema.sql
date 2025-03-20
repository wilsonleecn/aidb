
DROP TABLE IF EXISTS ServerGroupMapping;
DROP TABLE IF EXISTS ServerGroup;
DROP TABLE IF EXISTS Service;
DROP TABLE IF EXISTS ServerHost;
DROP TABLE IF EXISTS ServerHostGroup;
DROP TABLE IF EXISTS Domain;

CREATE TABLE Domain (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE ServerHostGroup (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    domain_id BIGINT UNSIGNED NOT NULL,
    name VARCHAR(255) NOT NULL,
    FOREIGN KEY (domain_id) REFERENCES Domain(id) ON DELETE CASCADE
);

CREATE TABLE ServerHost (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    domain_id BIGINT UNSIGNED NOT NULL,
    hostname VARCHAR(255) NOT NULL,
    server_host_group_id BIGINT UNSIGNED NOT NULL,
    ip_address VARCHAR(255),
    os VARCHAR(255),
    location VARCHAR(255),
    vars TEXT,
    FOREIGN KEY (domain_id) REFERENCES Domain(id) ON DELETE CASCADE,
    FOREIGN KEY (server_host_group_id) REFERENCES ServerHostGroup(id) ON DELETE CASCADE
);

CREATE TABLE Service (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    domain_id BIGINT UNSIGNED NOT NULL,
    name VARCHAR(255) NOT NULL,
    service_type VARCHAR(255),
    docker BOOLEAN,
    service_package_name VARCHAR(255),
    service_config_file TEXT,
    service_deploy_dir VARCHAR(255),
    status_port INT,
    management_endpoint VARCHAR(255),
    FOREIGN KEY (domain_id) REFERENCES Domain(id) ON DELETE CASCADE
);

CREATE TABLE ServerGroup (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    domain_id BIGINT UNSIGNED NOT NULL,
    name VARCHAR(255) NOT NULL,
    FOREIGN KEY (domain_id) REFERENCES Domain(id) ON DELETE CASCADE
);

CREATE TABLE ServerGroupMapping (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    domain_id BIGINT UNSIGNED NOT NULL,
    server_group_id BIGINT UNSIGNED NOT NULL,
    server_host_group_id BIGINT UNSIGNED NOT NULL,
    service_id BIGINT UNSIGNED NOT NULL,
    FOREIGN KEY (domain_id) REFERENCES Domain(id) ON DELETE CASCADE,
    FOREIGN KEY (server_group_id) REFERENCES ServerGroup(id) ON DELETE CASCADE,
    FOREIGN KEY (server_host_group_id) REFERENCES ServerHostGroup(id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES Service(id) ON DELETE CASCADE
);
