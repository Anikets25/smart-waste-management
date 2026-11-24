-- ─────────────────────────────────────────────────────────────────────────
--  Smart Waste Management System — Full MySQL Database Schema
--
--  Run once to set up everything:
--    mysql -u root -p < database/schema.sql
--
--  Safe to re-run — uses CREATE TABLE IF NOT EXISTS and ALTER TABLE
--  only when columns do not already exist.
-- ─────────────────────────────────────────────────────────────────────────

CREATE DATABASE IF NOT EXISTS smart_waste_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE smart_waste_db;


-- ══════════════════════════════════════════════════════════════════════════
--  TABLE: admins
--  Administrators — created only via create_admin.py (no public registration)
-- ══════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS admins (
    id            INT           NOT NULL AUTO_INCREMENT,
    username      VARCHAR(80)   NOT NULL,
    password_hash VARCHAR(255)  NOT NULL,
    created_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_admins_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ══════════════════════════════════════════════════════════════════════════
--  TABLE: citizens
--  Public users who register themselves
-- ══════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS citizens (
    id            INT           NOT NULL AUTO_INCREMENT,
    name          VARCHAR(120)  NOT NULL,
    email         VARCHAR(180)  NOT NULL,
    phone         VARCHAR(20)   NULL DEFAULT NULL,
    password_hash VARCHAR(255)  NOT NULL,
    green_points  INT           NOT NULL DEFAULT 0,
    is_active     TINYINT(1)    NOT NULL DEFAULT 1,
    created_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
                                         ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_citizens_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ══════════════════════════════════════════════════════════════════════════
--  TABLE: staff
--  Collection staff — created by admins, NOT publicly registerable
-- ══════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS staff (
    id              INT           NOT NULL AUTO_INCREMENT,
    name            VARCHAR(120)  NOT NULL,
    email           VARCHAR(180)  NOT NULL,
    phone           VARCHAR(20)   NULL DEFAULT NULL,
    password_hash   VARCHAR(255)  NOT NULL,
    employee_id     VARCHAR(30)   NOT NULL,       -- e.g. STAFF-001
    zone            VARCHAR(100)  NULL DEFAULT NULL,
    is_active       TINYINT(1)    NOT NULL DEFAULT 1,
    created_by_admin INT          NULL DEFAULT NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
                                           ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_staff_email      (email),
    UNIQUE KEY uq_staff_employee   (employee_id),
    FOREIGN KEY fk_staff_admin (created_by_admin) REFERENCES admins(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ══════════════════════════════════════════════════════════════════════════
--  TABLE: complaints
--  One row per waste complaint. Extended from original schema.
-- ══════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS complaints (
    id                  INT           NOT NULL AUTO_INCREMENT,
    complaint_id        VARCHAR(30)   NOT NULL,
    citizen_id          INT           NULL DEFAULT NULL,   -- NULL = anonymous submission
    description         TEXT          NOT NULL,
    category            VARCHAR(50)   NOT NULL,
    location            VARCHAR(255)  NOT NULL,
    image_path          VARCHAR(255)  NULL DEFAULT NULL,
    after_image_path    VARCHAR(255)  NULL DEFAULT NULL,   -- uploaded by staff after cleaning
    status              ENUM(
                            'Submitted',
                            'Under Review',
                            'In Progress',
                            'Resolved'
                        ) NOT NULL DEFAULT 'Submitted',
    assigned_staff_id   INT           NULL DEFAULT NULL,
    green_points_awarded INT          NOT NULL DEFAULT 0,
    created_at          DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
                                               ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_complaints_complaint_id (complaint_id),
    INDEX idx_complaints_status      (status),
    INDEX idx_complaints_category    (category),
    INDEX idx_complaints_created     (created_at),
    INDEX idx_complaints_citizen     (citizen_id),
    INDEX idx_complaints_staff       (assigned_staff_id),

    FOREIGN KEY fk_complaint_citizen (citizen_id)
        REFERENCES citizens(id) ON DELETE SET NULL,
    FOREIGN KEY fk_complaint_staff (assigned_staff_id)
        REFERENCES staff(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ══════════════════════════════════════════════════════════════════════════
--  TABLE: green_points_log
--  Audit trail for every Green Points credit / debit
-- ══════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS green_points_log (
    id           INT          NOT NULL AUTO_INCREMENT,
    citizen_id   INT          NOT NULL,
    complaint_id INT          NULL DEFAULT NULL,  -- linked complaint if applicable
    points       INT          NOT NULL,            -- positive = credit, negative = debit
    reason       VARCHAR(200) NOT NULL,
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    INDEX idx_gp_citizen (citizen_id),
    FOREIGN KEY fk_gp_citizen (citizen_id)   REFERENCES citizens(id)   ON DELETE CASCADE,
    FOREIGN KEY fk_gp_complaint (complaint_id) REFERENCES complaints(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ══════════════════════════════════════════════════════════════════════════
--  TABLE: rewards
--  Reward items listed in the marketplace
-- ══════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS rewards (
    id           INT           NOT NULL AUTO_INCREMENT,
    name         VARCHAR(120)  NOT NULL,
    description  TEXT          NULL,
    points_cost  INT           NOT NULL,
    stock        INT           NOT NULL DEFAULT 0,
    is_active    TINYINT(1)    NOT NULL DEFAULT 1,
    created_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ══════════════════════════════════════════════════════════════════════════
--  TABLE: reward_redemptions
--  When a citizen redeems a reward
-- ══════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS reward_redemptions (
    id           INT      NOT NULL AUTO_INCREMENT,
    citizen_id   INT      NOT NULL,
    reward_id    INT      NOT NULL,
    points_spent INT      NOT NULL,
    status       ENUM('Pending','Approved','Rejected') NOT NULL DEFAULT 'Pending',
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    INDEX idx_rr_citizen (citizen_id),
    FOREIGN KEY fk_rr_citizen (citizen_id) REFERENCES citizens(id) ON DELETE CASCADE,
    FOREIGN KEY fk_rr_reward  (reward_id)  REFERENCES rewards(id)  ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ══════════════════════════════════════════════════════════════════════════
--  SEED DATA: Sample rewards for the marketplace
-- ══════════════════════════════════════════════════════════════════════════
INSERT IGNORE INTO rewards (id, name, description, points_cost, stock, is_active) VALUES
(1, 'Eco Carry Bag',       'Reusable cotton carry bag — reduce plastic use',  50,  100, 1),
(2, 'Seed Kit',            'Set of 5 vegetable seed packets for home garden', 80,   50, 1),
(3, 'Compost Bin',         'Home composting kit for wet waste',              150,   20, 1),
(4, 'Tree Sapling',        'Native tree sapling for planting',               100,   30, 1),
(5, 'Water Bottle (Steel)','Stainless steel water bottle',                   120,   40, 1);
