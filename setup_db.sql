-- MySQL setup script for AI Voice Calling Agent
-- Replace the placeholders with your actual .env values before running

CREATE DATABASE IF NOT EXISTS ai_voice_agent CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'your_mysql_user'@'localhost' IDENTIFIED BY 'your_mysql_password';

GRANT ALL PRIVILEGES ON ai_voice_agent.* TO 'your_mysql_user'@'localhost';

FLUSH PRIVILEGES;

USE ai_voice_agent;

CREATE TABLE IF NOT EXISTS call_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    conversation_type ENUM('customer_feedback', 'sales_inquiry', 'appointment_reminder', 'survey', 'support', 'general') NOT NULL,
    greeting TEXT NOT NULL,
    status ENUM('initiated', 'in_progress', 'completed', 'failed', 'no_answer') DEFAULT 'initiated',
    call_sid VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    started_at DATETIME,
    ended_at DATETIME,
    duration_seconds INT
);

CREATE TABLE IF NOT EXISTS conversation_transcripts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    call_log_id INT NOT NULL,
    speaker ENUM('bot', 'user') NOT NULL,
    message TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    intent_detected VARCHAR(100),
    confidence_score VARCHAR(10),
    FOREIGN KEY (call_log_id) REFERENCES call_logs(id)
);
