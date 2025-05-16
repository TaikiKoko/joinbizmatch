CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32)
);

INSERT INTO alembic_version VALUES ('b196d9f6f2fc');

CREATE TABLE IF NOT EXISTS announcement (
    id INTEGER,
    title VARCHAR(128),
    content TEXT,
    created_at TIMESTAMP,
    is_public BOOLEAN
);


CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER,
    name VARCHAR(100),
    email VARCHAR(120),
    subject VARCHAR(200),
    message TEXT,
    created_at TIMESTAMP,
    is_read BOOLEAN
);


CREATE TABLE IF NOT EXISTS users (
    id INTEGER,
    username VARCHAR(64),
    email VARCHAR(120),
    password_hash VARCHAR(128),
    user_type VARCHAR(20),
    avatar_url VARCHAR(200),
    is_active BOOLEAN,
    is_admin BOOLEAN,
    last_seen TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

INSERT INTO users VALUES ('1', 'koukeisha', 'koukeisha@example.com', 'pbkdf2:sha256:600000$fx4RDYMwDm5uQhot$04abbbb56ac794e6028b06730f42a98f973e5e5880941c828a677a71a9d017e8', 'successor', 'static/uploads/profile_images/successor/133833998322487253.jpg', 'True', 'False', '2025-05-14 10:56:29.746959', '2025-05-14 10:56:29.746959', '2025-05-14 11:07:10.054429');
INSERT INTO users VALUES ('2', 'kigyou', 'kigyou@example.com', 'pbkdf2:sha256:600000$DJrWeTHj1R2X1tNz$0ec7151daa3f05ca661177ef8beaa1cd0d433bf5a42a5395f7b7e180bc36f729', 'company', 'static/uploads/profile_images/company/133842513004791929.jpg', 'True', 'False', '2025-05-14 11:12:16.180049', '2025-05-14 11:12:16.180049', '2025-05-14 11:13:08.172225');
INSERT INTO users VALUES ('3', 'company', 'company@example.com', 'pbkdf2:sha256:600000$ph15Fz5E97Dcq0Ri$6f9dbea421cba8e6ade0483e516556cd58d827f785a0e22917002f68364e0211', 'company', 'static/uploads/profile_images/company/133876317596633012.jpg', 'True', 'False', '2025-05-14 11:16:05.933390', '2025-05-14 11:16:05.933390', '2025-05-14 11:16:54.598696');
INSERT INTO users VALUES ('4', 'kagome', 'kagome@example.com', 'pbkdf2:sha256:600000$LgK52IiHczNJrXht$19418df698fed782aaf202782444ba06dccf9e61d2606d170ece9799ba3239ac', 'company', 'static/uploads/profile_images/company/133849487056704329.jpg', 'True', 'False', '2025-05-14 11:24:38.567493', '2025-05-14 11:24:38.567493', '2025-05-14 11:25:24.795482');

CREATE TABLE IF NOT EXISTS blocked_users (
    id INTEGER,
    blocker_id INTEGER,
    blocked_id INTEGER,
    created_at TIMESTAMP
);


CREATE TABLE IF NOT EXISTS chat_rooms (
    id INTEGER,
    user1_id INTEGER,
    user2_id INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    last_message_at TIMESTAMP
);

INSERT INTO chat_rooms VALUES ('1', '2', '1', '2025-05-14 11:13:30.811195', '2025-05-14 11:13:41.976702', '2025-05-14 11:13:41.972703');
INSERT INTO chat_rooms VALUES ('2', '4', '1', '2025-05-14 11:29:32.903331', '2025-05-14 11:29:57.239464', '2025-05-14 11:29:57.238927');
INSERT INTO chat_rooms VALUES ('3', '3', '1', '2025-05-16 09:39:12.021580', '2025-05-16 09:39:15.932885', '2025-05-16 09:39:15.932885');

CREATE TABLE IF NOT EXISTS companies (
    id INTEGER,
    user_id INTEGER,
    name VARCHAR(100),
    description TEXT,
    industry VARCHAR(100),
    location VARCHAR(100),
    website VARCHAR(200),
    employee_count INTEGER,
    established_year INTEGER,
    annual_revenue INTEGER,
    operating_profit INTEGER,
    capital INTEGER,
    business_description TEXT,
    succession_reason TEXT,
    desired_conditions TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    is_profile_completed BOOLEAN,
    image_path VARCHAR(200),
    short_description VARCHAR(200),
    homepage VARCHAR(200),
    instagram VARCHAR(200),
    twitter VARCHAR(200)
);

INSERT INTO companies VALUES ('1', '2', 'カモメ株式会社', NULL, 'manufacturing', '新潟県', NULL, '111', '1999', '1000', '10', '100', 'aaa', 'aaaaaaaaaaaaaa', 'aaaaaaaaaaaa', '2025-05-14 11:12:16.238571', '2025-05-14 11:13:08.183104', 'True', 'profile_images/company/133842513004791929.jpg', 'aaaaaaaaaa', NULL, NULL, NULL);
INSERT INTO companies VALUES ('2', '3', '企業太郎', NULL, 'retail', '神奈川県', NULL, '11', '1989', '111', '11', '1', 'aaaaaaaaaa', 'aaaaa', 'aaaaa', '2025-05-14 11:16:05.936005', '2025-05-14 11:16:54.598696', 'True', 'profile_images/company/133876317596633012.jpg', 'aaa', NULL, NULL, NULL);
INSERT INTO companies VALUES ('3', '4', 'カガメ株式会社', NULL, 'service', '新潟県', NULL, '11', '1999', '200', '20', '1', 'aaa', 'aaa', 'aaa', '2025-05-14 11:24:38.572891', '2025-05-14 11:25:24.801690', 'True', 'profile_images/company/133849487056704329.jpg', 'aaa', NULL, NULL, NULL);

CREATE TABLE IF NOT EXISTS email_verification (
    id INTEGER,
    user_id INTEGER,
    new_email VARCHAR(120),
    token VARCHAR(100),
    created_at TIMESTAMP,
    is_used BOOLEAN
);


CREATE TABLE IF NOT EXISTS notes (
    id INTEGER,
    user_id INTEGER,
    title VARCHAR(100),
    content TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);


CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER,
    user_id INTEGER,
    type VARCHAR(50),
    message TEXT,
    link VARCHAR(255),
    read BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);


CREATE TABLE IF NOT EXISTS sellers (
    id INTEGER,
    user_id INTEGER,
    name VARCHAR(100),
    company_name VARCHAR(100),
    position VARCHAR(100),
    phone VARCHAR(20),
    representative_name VARCHAR(100),
    establishment_year INTEGER,
    capital INTEGER,
    employees INTEGER,
    annual_sales INTEGER,
    business_description TEXT,
    reason_for_sale TEXT,
    desired_successor TEXT,
    asking_price INTEGER,
    is_verified BOOLEAN,
    is_active BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);


CREATE TABLE IF NOT EXISTS successors (
    id INTEGER,
    user_id INTEGER,
    name VARCHAR(100),
    age INTEGER,
    gender VARCHAR(20),
    location VARCHAR(100),
    description TEXT,
    desired_industry VARCHAR(20),
    desired_location VARCHAR(20),
    investment_capacity VARCHAR(50),
    management_experience TEXT,
    industry_experience TEXT,
    is_public BOOLEAN,
    image_filename VARCHAR(255),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

INSERT INTO successors VALUES ('1', '1', '後継者太郎', '55', '男性', '福井県', 'aaaaaaaaaaa', 'service', '青森県', '～1000万円', 'aaaa', '', 'True', 'profile_images/successor/133833998322487253.jpg', '2025-05-14 10:56:29.805488', '2025-05-14 11:07:10.057427');

CREATE TABLE IF NOT EXISTS company_favorites (
    user_id INTEGER,
    company_id INTEGER,
    created_at TIMESTAMP
);

INSERT INTO company_favorites VALUES ('1', '1', '2025-05-14 11:14:18.901060');
INSERT INTO company_favorites VALUES ('1', '2', '2025-05-16 09:39:10.853455');

CREATE TABLE IF NOT EXISTS company_successor_matches (
    id INTEGER,
    company_id INTEGER,
    successor_id INTEGER,
    status VARCHAR(20),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);


CREATE TABLE IF NOT EXISTS messages (
    id INTEGER,
    chat_room_id INTEGER,
    sender_id INTEGER,
    recipient_id INTEGER,
    content TEXT,
    is_read BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

INSERT INTO messages VALUES ('1', '1', '1', '2', 'aaa', 'True', '2025-05-14 11:13:34.111867', '2025-05-14 11:13:39.864565');
INSERT INTO messages VALUES ('2', '1', '2', '1', 'aaa', 'True', '2025-05-14 11:13:41.972703', '2025-05-14 11:13:42.017430');
INSERT INTO messages VALUES ('3', '2', '1', '4', 'aaa', 'True', '2025-05-14 11:29:36.626269', '2025-05-14 11:29:48.846028');
INSERT INTO messages VALUES ('4', '2', '4', '1', 'aaa', 'True', '2025-05-14 11:29:57.238927', '2025-05-14 11:29:58.231277');
INSERT INTO messages VALUES ('5', '3', '1', '3', 'aaa', 'False', '2025-05-16 09:39:15.932885', '2025-05-16 09:39:15.947124');

CREATE TABLE IF NOT EXISTS successor_favorites (
    user_id INTEGER,
    successor_id INTEGER,
    created_at TIMESTAMP
);


CREATE TABLE IF NOT EXISTS attachments (
    id INTEGER,
    message_id INTEGER,
    file_path VARCHAR(255),
    original_filename VARCHAR(255),
    file_type VARCHAR(50),
    file_size INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);


