/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

CREATE DATABASE IF NOT EXISTS `exam_system` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */;
USE `exam_system`;

CREATE TABLE IF NOT EXISTS `admins` (
  `admin_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `permission_level` varchar(50) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`admin_id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `admins_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `answer_choices` (
  `choice_id` int(11) NOT NULL AUTO_INCREMENT,
  `question_id` int(11) NOT NULL,
  `choice_label` varchar(10) DEFAULT NULL,
  `choice_text` longtext DEFAULT NULL,
  `display_order` int(11) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `is_rich_text` tinyint(1) DEFAULT 1,
  `media_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`choice_id`),
  KEY `question_id` (`question_id`),
  KEY `idx_answer_media` (`media_id`),
  CONSTRAINT `answer_choices_ibfk_1` FOREIGN KEY (`question_id`) REFERENCES `questions` (`question_id`) ON DELETE CASCADE,
  CONSTRAINT `answer_choices_ibfk_2` FOREIGN KEY (`media_id`) REFERENCES `question_media` (`media_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `answers` (
  `answer_id` int(11) NOT NULL AUTO_INCREMENT,
  `question_id` int(11) NOT NULL,
  `answer_type` enum('choice','true_false','text','numeric') NOT NULL,
  `answer_value` varchar(255) DEFAULT NULL,
  `points` decimal(5,2) DEFAULT NULL,
  `explanation` text DEFAULT NULL,
  `created_by` int(11) NOT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `is_rich_text` tinyint(1) DEFAULT 1,
  `explanation_html` longtext DEFAULT NULL,
  PRIMARY KEY (`answer_id`),
  KEY `question_id` (`question_id`),
  KEY `created_by` (`created_by`),
  CONSTRAINT `answers_ibfk_1` FOREIGN KEY (`question_id`) REFERENCES `questions` (`question_id`) ON DELETE CASCADE,
  CONSTRAINT `answers_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `audit_logs` (
  `log_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) DEFAULT NULL,
  `action` varchar(255) NOT NULL,
  `target_table` varchar(100) DEFAULT NULL,
  `target_id` int(11) DEFAULT NULL,
  `old_values` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`old_values`)),
  `new_values` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`new_values`)),
  `timestamp` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`log_id`),
  KEY `idx_audit_user` (`user_id`),
  CONSTRAINT `audit_logs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `captcha_sessions` (
  `session_id` varchar(255) NOT NULL,
  `captcha_text` varchar(10) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `expires_at` datetime DEFAULT NULL,
  `is_verified` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`session_id`),
  KEY `expires_at` (`expires_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `districts` (
  `district_id` int(11) NOT NULL AUTO_INCREMENT,
  `province_id` int(11) NOT NULL,
  `district_name` varchar(100) NOT NULL,
  `district_code` varchar(10) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`district_id`),
  UNIQUE KEY `province_id` (`province_id`,`district_name`),
  KEY `idx_district_province` (`province_id`),
  CONSTRAINT `districts_ibfk_1` FOREIGN KEY (`province_id`) REFERENCES `provinces` (`province_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `essay_grades` (
  `grade_id` int(11) NOT NULL AUTO_INCREMENT,
  `response_id` int(11) NOT NULL,
  `grader_id` int(11) NOT NULL,
  `grading_order` int(11) DEFAULT NULL,
  `is_first_grader` tinyint(1) DEFAULT NULL,
  `is_second_grader` tinyint(1) DEFAULT NULL,
  `is_third_grader` tinyint(1) DEFAULT NULL,
  `score` decimal(5,2) DEFAULT NULL,
  `feedback` text DEFAULT NULL,
  `grading_date` datetime DEFAULT NULL,
  `final_status` enum('pending','grading','completed') DEFAULT 'pending',
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`grade_id`),
  UNIQUE KEY `response_id` (`response_id`,`grader_id`),
  UNIQUE KEY `response_id_2` (`response_id`,`grading_order`),
  KEY `grader_id` (`grader_id`),
  CONSTRAINT `essay_grades_ibfk_1` FOREIGN KEY (`response_id`) REFERENCES `student_responses` (`response_id`) ON DELETE CASCADE,
  CONSTRAINT `essay_grades_ibfk_2` FOREIGN KEY (`grader_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `exam_attempts` (
  `attempt_id` int(11) NOT NULL AUTO_INCREMENT,
  `student_id` int(11) NOT NULL,
  `schedule_id` int(11) NOT NULL,
  `generated_paper_id` int(11) NOT NULL,
  `exam_session_id` int(11) NOT NULL,
  `subject_id` int(11) NOT NULL,
  `start_time` datetime NOT NULL,
  `end_time` datetime DEFAULT NULL,
  `submitted_time` datetime DEFAULT NULL,
  `is_submitted` tinyint(1) DEFAULT 0,
  `total_score` decimal(5,2) DEFAULT NULL,
  `selected_informatics_track` enum('computer_science','applied_informatics') DEFAULT NULL,
  `status` enum('ongoing','completed','graded','invalid') DEFAULT 'ongoing',
  `ip_address` varchar(50) DEFAULT NULL,
  `user_agent` text DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`attempt_id`),
  KEY `schedule_id` (`schedule_id`),
  KEY `generated_paper_id` (`generated_paper_id`),
  KEY `exam_session_id` (`exam_session_id`),
  KEY `subject_id` (`subject_id`),
  KEY `idx_exam_attempt_student` (`student_id`),
  KEY `idx_exam_attempt_status` (`status`),
  CONSTRAINT `exam_attempts_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `students` (`student_id`) ON DELETE CASCADE,
  CONSTRAINT `exam_attempts_ibfk_2` FOREIGN KEY (`schedule_id`) REFERENCES `exam_schedules` (`schedule_id`) ON DELETE CASCADE,
  CONSTRAINT `exam_attempts_ibfk_3` FOREIGN KEY (`generated_paper_id`) REFERENCES `generated_papers` (`generated_paper_id`) ON DELETE CASCADE,
  CONSTRAINT `exam_attempts_ibfk_4` FOREIGN KEY (`exam_session_id`) REFERENCES `exam_sessions` (`exam_session_id`) ON DELETE CASCADE,
  CONSTRAINT `exam_attempts_ibfk_5` FOREIGN KEY (`subject_id`) REFERENCES `subjects` (`subject_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `exam_papers` (
  `paper_id` int(11) NOT NULL AUTO_INCREMENT,
  `subject_id` int(11) NOT NULL,
  `exam_session_id` int(11) DEFAULT NULL,
  `paper_code` varchar(50) NOT NULL,
  `paper_version` int(11) DEFAULT 1,
  `total_points` decimal(5,2) DEFAULT 10.00,
  `is_published` tinyint(1) DEFAULT 0,
  `is_finalized` tinyint(1) DEFAULT 0,
  `randomization_enabled` tinyint(1) DEFAULT 1,
  `randomization_seed` int(11) DEFAULT NULL,
  `created_by` int(11) NOT NULL,
  `approved_by` int(11) DEFAULT NULL,
  `approval_date` datetime DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `reading_material` longtext DEFAULT NULL COMMENT 'Shared reading material for Vietnamese Language (Ngữ Văn) - Đọc Hiểu section',
  PRIMARY KEY (`paper_id`),
  UNIQUE KEY `paper_code` (`paper_code`),
  KEY `exam_session_id` (`exam_session_id`),
  KEY `created_by` (`created_by`),
  KEY `approved_by` (`approved_by`),
  KEY `idx_paper_subject` (`subject_id`),
  CONSTRAINT `exam_papers_ibfk_1` FOREIGN KEY (`subject_id`) REFERENCES `subjects` (`subject_id`) ON DELETE CASCADE,
  CONSTRAINT `exam_papers_ibfk_2` FOREIGN KEY (`exam_session_id`) REFERENCES `exam_sessions` (`exam_session_id`) ON DELETE SET NULL,
  CONSTRAINT `exam_papers_ibfk_3` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `exam_papers_ibfk_4` FOREIGN KEY (`approved_by`) REFERENCES `users` (`user_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `exam_results` (
  `result_id` int(11) NOT NULL AUTO_INCREMENT,
  `student_id` int(11) NOT NULL,
  `exam_session_id` int(11) NOT NULL,
  `subject_id` int(11) NOT NULL,
  `score` decimal(5,2) DEFAULT NULL,
  `grade` char(1) DEFAULT NULL,
  `status` enum('completed','failed') DEFAULT 'completed',
  `published` tinyint(1) DEFAULT 0,
  `published_date` datetime DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`result_id`),
  UNIQUE KEY `student_id` (`student_id`,`exam_session_id`,`subject_id`),
  KEY `exam_session_id` (`exam_session_id`),
  KEY `subject_id` (`subject_id`),
  KEY `idx_result_student` (`student_id`),
  CONSTRAINT `exam_results_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `students` (`student_id`) ON DELETE CASCADE,
  CONSTRAINT `exam_results_ibfk_2` FOREIGN KEY (`exam_session_id`) REFERENCES `exam_sessions` (`exam_session_id`) ON DELETE CASCADE,
  CONSTRAINT `exam_results_ibfk_3` FOREIGN KEY (`subject_id`) REFERENCES `subjects` (`subject_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `exam_schedules` (
  `schedule_id` int(11) NOT NULL AUTO_INCREMENT,
  `exam_session_id` int(11) NOT NULL,
  `subject_id` int(11) NOT NULL,
  `exam_date` date NOT NULL,
  `start_time` time NOT NULL,
  `end_time` time NOT NULL,
  `duration_minutes` int(11) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`schedule_id`),
  UNIQUE KEY `exam_session_id` (`exam_session_id`,`subject_id`,`exam_date`,`start_time`),
  KEY `subject_id` (`subject_id`),
  KEY `idx_schedule_session` (`exam_session_id`),
  CONSTRAINT `exam_schedules_ibfk_1` FOREIGN KEY (`exam_session_id`) REFERENCES `exam_sessions` (`exam_session_id`) ON DELETE CASCADE,
  CONSTRAINT `exam_schedules_ibfk_2` FOREIGN KEY (`subject_id`) REFERENCES `subjects` (`subject_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `exam_sessions` (
  `exam_session_id` int(11) NOT NULL AUTO_INCREMENT,
  `session_name` varchar(255) NOT NULL,
  `session_type` enum('official','test','makeup') DEFAULT 'official',
  `description` text DEFAULT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `is_published` tinyint(1) DEFAULT 0,
  `is_locked` tinyint(1) DEFAULT 0,
  `published_by` int(11) DEFAULT NULL,
  `published_date` datetime DEFAULT NULL,
  `created_by` int(11) NOT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`exam_session_id`),
  KEY `published_by` (`published_by`),
  KEY `created_by` (`created_by`),
  CONSTRAINT `exam_sessions_ibfk_1` FOREIGN KEY (`published_by`) REFERENCES `users` (`user_id`) ON DELETE SET NULL,
  CONSTRAINT `exam_sessions_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `generated_papers` (
  `generated_paper_id` int(11) NOT NULL AUTO_INCREMENT,
  `paper_id` int(11) NOT NULL,
  `paper_code_version` varchar(50) NOT NULL,
  `randomization_seed` int(11) DEFAULT NULL,
  `question_order` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`question_order`)),
  `generated_date` datetime DEFAULT current_timestamp(),
  `is_active` tinyint(1) DEFAULT 1,
  PRIMARY KEY (`generated_paper_id`),
  UNIQUE KEY `paper_code_version` (`paper_code_version`),
  KEY `paper_id` (`paper_id`),
  CONSTRAINT `generated_papers_ibfk_1` FOREIGN KEY (`paper_id`) REFERENCES `exam_papers` (`paper_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `makeup_registrations` (
  `registration_id` int(11) NOT NULL AUTO_INCREMENT,
  `student_id` int(11) NOT NULL,
  `exam_session_id` int(11) NOT NULL,
  `subject_id` int(11) NOT NULL,
  `request_date` datetime DEFAULT current_timestamp(),
  `requested_by` int(11) DEFAULT NULL,
  `approval_status` enum('pending','approved','rejected') DEFAULT 'pending',
  `approved_by` int(11) DEFAULT NULL,
  `approval_date` datetime DEFAULT NULL,
  `rejection_reason` text DEFAULT NULL,
  `scheduled_date` date DEFAULT NULL,
  `scheduled_start_time` time DEFAULT NULL,
  `scheduled_end_time` time DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`registration_id`),
  KEY `student_id` (`student_id`),
  KEY `exam_session_id` (`exam_session_id`),
  KEY `subject_id` (`subject_id`),
  KEY `requested_by` (`requested_by`),
  KEY `approved_by` (`approved_by`),
  CONSTRAINT `makeup_registrations_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `students` (`student_id`) ON DELETE CASCADE,
  CONSTRAINT `makeup_registrations_ibfk_2` FOREIGN KEY (`exam_session_id`) REFERENCES `exam_sessions` (`exam_session_id`) ON DELETE CASCADE,
  CONSTRAINT `makeup_registrations_ibfk_3` FOREIGN KEY (`subject_id`) REFERENCES `subjects` (`subject_id`) ON DELETE CASCADE,
  CONSTRAINT `makeup_registrations_ibfk_4` FOREIGN KEY (`requested_by`) REFERENCES `users` (`user_id`) ON DELETE SET NULL,
  CONSTRAINT `makeup_registrations_ibfk_5` FOREIGN KEY (`approved_by`) REFERENCES `users` (`user_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `media_upload_logs` (
  `log_id` int(11) NOT NULL AUTO_INCREMENT,
  `media_id` int(11) DEFAULT NULL,
  `upload_by` int(11) NOT NULL,
  `original_filename` varchar(500) DEFAULT NULL,
  `stored_filename` varchar(500) DEFAULT NULL,
  `file_path` varchar(1000) DEFAULT NULL,
  `file_size` int(11) DEFAULT NULL,
  `upload_date` timestamp NULL DEFAULT current_timestamp(),
  `is_active` tinyint(1) DEFAULT 1,
  PRIMARY KEY (`log_id`),
  KEY `media_id` (`media_id`),
  KEY `upload_by` (`upload_by`),
  CONSTRAINT `media_upload_logs_ibfk_1` FOREIGN KEY (`media_id`) REFERENCES `question_media` (`media_id`) ON DELETE CASCADE,
  CONSTRAINT `media_upload_logs_ibfk_2` FOREIGN KEY (`upload_by`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `provinces` (
  `province_id` int(11) NOT NULL AUTO_INCREMENT,
  `province_name` varchar(100) NOT NULL,
  `province_code` varchar(10) DEFAULT NULL,
  `region` varchar(50) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`province_id`),
  UNIQUE KEY `province_name` (`province_name`),
  UNIQUE KEY `province_code` (`province_code`),
  KEY `idx_province_name` (`province_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `question_comments` (
  `comment_id` int(11) NOT NULL AUTO_INCREMENT,
  `question_id` int(11) NOT NULL,
  `comment_text` text NOT NULL,
  `created_by` int(11) NOT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`comment_id`),
  KEY `question_id` (`question_id`),
  KEY `created_by` (`created_by`),
  CONSTRAINT `question_comments_ibfk_1` FOREIGN KEY (`question_id`) REFERENCES `questions` (`question_id`) ON DELETE CASCADE,
  CONSTRAINT `question_comments_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `question_edit_history` (
  `history_id` int(11) NOT NULL AUTO_INCREMENT,
  `question_id` int(11) NOT NULL,
  `edited_by` int(11) NOT NULL,
  `old_data` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`old_data`)),
  `new_data` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`new_data`)),
  `change_type` varchar(50) DEFAULT NULL,
  `edit_date` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`history_id`),
  KEY `question_id` (`question_id`),
  KEY `edited_by` (`edited_by`),
  CONSTRAINT `question_edit_history_ibfk_1` FOREIGN KEY (`question_id`) REFERENCES `questions` (`question_id`) ON DELETE CASCADE,
  CONSTRAINT `question_edit_history_ibfk_2` FOREIGN KEY (`edited_by`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `question_items` (
  `item_id` int(11) NOT NULL AUTO_INCREMENT,
  `question_id` int(11) NOT NULL,
  `item_label` varchar(10) NOT NULL,
  `item_text` longtext DEFAULT NULL,
  `correct_value` varchar(20) DEFAULT NULL,
  `display_order` int(11) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `is_rich_text` tinyint(1) DEFAULT 1,
  `media_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`item_id`),
  UNIQUE KEY `question_id` (`question_id`,`item_label`),
  KEY `idx_question_item_question` (`question_id`),
  KEY `media_id` (`media_id`),
  CONSTRAINT `question_items_ibfk_1` FOREIGN KEY (`question_id`) REFERENCES `questions` (`question_id`) ON DELETE CASCADE,
  CONSTRAINT `question_items_ibfk_2` FOREIGN KEY (`media_id`) REFERENCES `question_media` (`media_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `question_media` (
  `media_id` int(11) NOT NULL AUTO_INCREMENT,
  `question_id` int(11) DEFAULT NULL,
  `section_id` int(11) DEFAULT NULL,
  `passage_id` int(11) DEFAULT NULL,
  `media_type` enum('image','audio','video','document') DEFAULT 'image',
  `media_filename` varchar(500) NOT NULL,
  `media_path` varchar(1000) NOT NULL,
  `file_size` int(11) DEFAULT NULL,
  `mime_type` varchar(100) DEFAULT NULL,
  `alt_text` text DEFAULT NULL,
  `caption` text DEFAULT NULL,
  `display_order` int(11) DEFAULT NULL,
  `created_by` int(11) NOT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`media_id`),
  KEY `created_by` (`created_by`),
  KEY `idx_question_media` (`question_id`),
  KEY `idx_section_media` (`section_id`),
  KEY `idx_passage_media` (`passage_id`),
  KEY `idx_media_question` (`question_id`),
  KEY `idx_media_section` (`section_id`),
  CONSTRAINT `question_media_ibfk_1` FOREIGN KEY (`question_id`) REFERENCES `questions` (`question_id`) ON DELETE CASCADE,
  CONSTRAINT `question_media_ibfk_2` FOREIGN KEY (`section_id`) REFERENCES `question_sections` (`section_id`) ON DELETE CASCADE,
  CONSTRAINT `question_media_ibfk_3` FOREIGN KEY (`passage_id`) REFERENCES `question_passages` (`passage_id`) ON DELETE CASCADE,
  CONSTRAINT `question_media_ibfk_4` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `question_multi_section` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `question_id` int(11) NOT NULL,
  `section_id` int(11) NOT NULL,
  `display_order` int(11) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `question_id` (`question_id`,`section_id`),
  KEY `section_id` (`section_id`),
  CONSTRAINT `question_multi_section_ibfk_1` FOREIGN KEY (`question_id`) REFERENCES `questions` (`question_id`) ON DELETE CASCADE,
  CONSTRAINT `question_multi_section_ibfk_2` FOREIGN KEY (`section_id`) REFERENCES `question_sections` (`section_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `question_passages` (
  `passage_id` int(11) NOT NULL AUTO_INCREMENT,
  `section_id` int(11) DEFAULT NULL,
  `passage_text` longtext NOT NULL,
  `passage_title` varchar(255) DEFAULT NULL,
  `author_name` varchar(255) DEFAULT NULL,
  `source_info` varchar(500) DEFAULT NULL,
  `display_order` int(11) DEFAULT NULL,
  `is_visible` tinyint(1) DEFAULT 1,
  `created_by` int(11) NOT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`passage_id`),
  KEY `created_by` (`created_by`),
  KEY `idx_passage_section` (`section_id`),
  CONSTRAINT `question_passages_ibfk_1` FOREIGN KEY (`section_id`) REFERENCES `question_sections` (`section_id`) ON DELETE CASCADE,
  CONSTRAINT `question_passages_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `question_section_types` (
  `section_type_id` int(11) NOT NULL AUTO_INCREMENT,
  `section_type_name` varchar(100) NOT NULL,
  `section_type_key` varchar(50) NOT NULL,
  `description` text DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`section_type_id`),
  UNIQUE KEY `section_type_name` (`section_type_name`),
  UNIQUE KEY `section_type_key` (`section_type_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `question_sections` (
  `section_id` int(11) NOT NULL AUTO_INCREMENT,
  `paper_id` int(11) NOT NULL,
  `section_type_id` int(11) DEFAULT NULL,
  `section_name` varchar(255) DEFAULT NULL,
  `section_description` longtext DEFAULT NULL,
  `display_order` int(11) NOT NULL,
  `is_visible` tinyint(1) DEFAULT 1,
  `created_by` int(11) NOT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`section_id`),
  UNIQUE KEY `paper_id` (`paper_id`,`display_order`),
  KEY `created_by` (`created_by`),
  KEY `idx_section_paper` (`paper_id`),
  KEY `idx_section_type` (`section_type_id`),
  CONSTRAINT `question_sections_ibfk_1` FOREIGN KEY (`paper_id`) REFERENCES `exam_papers` (`paper_id`) ON DELETE CASCADE,
  CONSTRAINT `question_sections_ibfk_2` FOREIGN KEY (`section_type_id`) REFERENCES `question_section_types` (`section_type_id`) ON DELETE SET NULL,
  CONSTRAINT `question_sections_ibfk_3` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `question_templates` (
  `template_id` int(11) NOT NULL AUTO_INCREMENT,
  `question_id` int(11) DEFAULT NULL,
  `template_name` varchar(255) NOT NULL,
  `template_category` varchar(100) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `subject_id` int(11) DEFAULT NULL,
  `created_by` int(11) NOT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `is_active` tinyint(1) DEFAULT 1,
  PRIMARY KEY (`template_id`),
  UNIQUE KEY `template_name` (`template_name`),
  KEY `question_id` (`question_id`),
  KEY `created_by` (`created_by`),
  KEY `idx_category` (`template_category`),
  KEY `idx_subject` (`subject_id`),
  CONSTRAINT `question_templates_ibfk_1` FOREIGN KEY (`question_id`) REFERENCES `questions` (`question_id`) ON DELETE SET NULL,
  CONSTRAINT `question_templates_ibfk_2` FOREIGN KEY (`subject_id`) REFERENCES `subjects` (`subject_id`) ON DELETE SET NULL,
  CONSTRAINT `question_templates_ibfk_3` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `questions` (
  `question_id` int(11) NOT NULL AUTO_INCREMENT,
  `paper_id` int(11) NOT NULL,
  `question_number` int(11) NOT NULL,
  `question_text` longtext NOT NULL,
  `question_type` enum('multiple_choice','true_false','short_answer','essay') NOT NULL,
  `part` enum('part1','part2','part3','reading','writing','rc1','rc2','rf1','rf2','rf3','rs') NOT NULL,
  `points` decimal(5,2) DEFAULT NULL,
  `max_words` int(11) DEFAULT NULL,
  `max_chars` int(11) DEFAULT NULL,
  `answer_format` enum('choice','true_false_set','four_cell_text','essay_text') DEFAULT NULL,
  `informatics_track` enum('common','computer_science','applied_informatics') DEFAULT NULL,
  `display_order` int(11) DEFAULT NULL,
  `is_visible` tinyint(1) DEFAULT 1,
  `created_by` int(11) NOT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `section_id` int(11) DEFAULT NULL,
  `passage_id` int(11) DEFAULT NULL,
  `display_order_in_section` int(11) DEFAULT NULL,
  `is_rich_text` tinyint(1) DEFAULT 1,
  `difficulty_level` enum('easy','medium','hard','very_hard') DEFAULT 'medium',
  `bloom_level` enum('remember','understand','apply','analyze','evaluate','create') DEFAULT 'understand',
  `estimated_time_seconds` int(11) DEFAULT 60,
  `is_template` tinyint(1) DEFAULT 0,
  `template_category` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`question_id`),
  UNIQUE KEY `paper_id` (`paper_id`,`question_number`),
  KEY `created_by` (`created_by`),
  KEY `idx_question_section` (`section_id`),
  KEY `idx_question_passage` (`passage_id`),
  KEY `idx_question_by_section` (`section_id`),
  KEY `idx_question_by_passage` (`passage_id`),
  KEY `idx_question_difficulty` (`difficulty_level`),
  KEY `idx_question_bloom_level` (`bloom_level`),
  CONSTRAINT `questions_ibfk_1` FOREIGN KEY (`paper_id`) REFERENCES `exam_papers` (`paper_id`) ON DELETE CASCADE,
  CONSTRAINT `questions_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `questions_ibfk_3` FOREIGN KEY (`section_id`) REFERENCES `question_sections` (`section_id`) ON DELETE SET NULL,
  CONSTRAINT `questions_ibfk_4` FOREIGN KEY (`passage_id`) REFERENCES `question_passages` (`passage_id`) ON DELETE SET NULL,
  CONSTRAINT `questions_ibfk_5` FOREIGN KEY (`passage_id`) REFERENCES `question_passages` (`passage_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `result_queries` (
  `query_id` int(11) NOT NULL AUTO_INCREMENT,
  `cccd` varchar(20) NOT NULL,
  `date_of_birth` date NOT NULL,
  `phone` varchar(15) NOT NULL,
  `query_date` datetime DEFAULT current_timestamp(),
  `query_ip` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`query_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `rich_text_templates` (
  `template_id` int(11) NOT NULL AUTO_INCREMENT,
  `template_name` varchar(255) NOT NULL,
  `template_code` varchar(100) NOT NULL,
  `html_content` longtext NOT NULL,
  `preview_text` varchar(500) DEFAULT NULL,
  `category` varchar(100) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `created_by` int(11) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`template_id`),
  UNIQUE KEY `template_code` (`template_code`),
  KEY `created_by` (`created_by`),
  CONSTRAINT `rich_text_templates_ibfk_1` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `schools` (
  `school_id` int(11) NOT NULL AUTO_INCREMENT,
  `school_name` varchar(255) NOT NULL,
  `district_id` int(11) DEFAULT NULL,
  `province_id` int(11) DEFAULT NULL,
  `address` varchar(500) DEFAULT NULL,
  `phone` varchar(15) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`school_id`),
  UNIQUE KEY `school_name` (`school_name`),
  KEY `idx_school_location` (`province_id`,`district_id`),
  KEY `fk_schools_district_id` (`district_id`),
  CONSTRAINT `fk_schools_district_id` FOREIGN KEY (`district_id`) REFERENCES `districts` (`district_id`) ON DELETE SET NULL,
  CONSTRAINT `fk_schools_province_id` FOREIGN KEY (`province_id`) REFERENCES `provinces` (`province_id`) ON DELETE SET NULL,
  CONSTRAINT `schools_ibfk_1` FOREIGN KEY (`district_id`) REFERENCES `districts` (`district_id`) ON DELETE SET NULL,
  CONSTRAINT `schools_ibfk_2` FOREIGN KEY (`province_id`) REFERENCES `provinces` (`province_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `special_question_groups` (
  `group_id` int(11) NOT NULL AUTO_INCREMENT,
  `question_id` int(11) NOT NULL,
  `group_type` enum('common','computer_science','applied_informatics') NOT NULL,
  PRIMARY KEY (`group_id`),
  KEY `question_id` (`question_id`),
  CONSTRAINT `special_question_groups_ibfk_1` FOREIGN KEY (`question_id`) REFERENCES `questions` (`question_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `student_responses` (
  `response_id` int(11) NOT NULL AUTO_INCREMENT,
  `attempt_id` int(11) NOT NULL,
  `question_id` int(11) NOT NULL,
  `response_type` enum('choice','true_false','text','numeric','essay') NOT NULL,
  `response_value` longtext DEFAULT NULL,
  `marked_correct` tinyint(1) DEFAULT NULL,
  `points_earned` decimal(5,2) DEFAULT NULL,
  `grader_notes` text DEFAULT NULL,
  `submitted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`response_id`),
  UNIQUE KEY `attempt_id` (`attempt_id`,`question_id`),
  KEY `question_id` (`question_id`),
  KEY `idx_student_response_attempt` (`attempt_id`),
  CONSTRAINT `student_responses_ibfk_1` FOREIGN KEY (`attempt_id`) REFERENCES `exam_attempts` (`attempt_id`) ON DELETE CASCADE,
  CONSTRAINT `student_responses_ibfk_2` FOREIGN KEY (`question_id`) REFERENCES `questions` (`question_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `student_subject_registration` (
  `registration_id` int(11) NOT NULL AUTO_INCREMENT,
  `student_id` int(11) NOT NULL,
  `subject_id` int(11) NOT NULL,
  `exam_session_id` int(11) NOT NULL,
  `registration_date` datetime DEFAULT current_timestamp(),
  `registered_by` int(11) DEFAULT NULL,
  PRIMARY KEY (`registration_id`),
  UNIQUE KEY `student_id` (`student_id`,`subject_id`,`exam_session_id`),
  KEY `subject_id` (`subject_id`),
  KEY `exam_session_id` (`exam_session_id`),
  KEY `registered_by` (`registered_by`),
  CONSTRAINT `student_subject_registration_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `students` (`student_id`) ON DELETE CASCADE,
  CONSTRAINT `student_subject_registration_ibfk_2` FOREIGN KEY (`subject_id`) REFERENCES `subjects` (`subject_id`) ON DELETE CASCADE,
  CONSTRAINT `student_subject_registration_ibfk_3` FOREIGN KEY (`exam_session_id`) REFERENCES `exam_sessions` (`exam_session_id`) ON DELETE CASCADE,
  CONSTRAINT `student_subject_registration_ibfk_4` FOREIGN KEY (`registered_by`) REFERENCES `users` (`user_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `students` (
  `student_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `school_id` int(11) NOT NULL,
  `student_code` varchar(50) NOT NULL,
  `cccd` varchar(20) NOT NULL,
  `full_name` varchar(255) NOT NULL,
  `gender` enum('male','female','other') NOT NULL,
  `date_of_birth` date NOT NULL,
  `address` varchar(500) DEFAULT NULL,
  `phone` varchar(15) DEFAULT NULL,
  `class_name` varchar(50) DEFAULT NULL,
  `registration_date` datetime DEFAULT NULL,
  `profile_photo` longblob DEFAULT NULL,
  `profile_photo_filename` varchar(255) DEFAULT NULL,
  `permanent_address` varchar(500) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`student_id`),
  UNIQUE KEY `user_id` (`user_id`),
  UNIQUE KEY `cccd` (`cccd`),
  KEY `school_id` (`school_id`),
  KEY `idx_student_cccd` (`cccd`),
  KEY `idx_student_user` (`user_id`),
  CONSTRAINT `students_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `students_ibfk_2` FOREIGN KEY (`school_id`) REFERENCES `schools` (`school_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `subjects` (
  `subject_id` int(11) NOT NULL AUTO_INCREMENT,
  `subject_code` varchar(20) NOT NULL,
  `subject_name` varchar(100) NOT NULL,
  `group_code` varchar(20) DEFAULT NULL,
  `exam_type` enum('multiple_choice','essay','mixed') NOT NULL,
  `duration_minutes` int(11) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`subject_id`),
  UNIQUE KEY `subject_code` (`subject_code`),
  UNIQUE KEY `subject_name` (`subject_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `teachers` (
  `teacher_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `school_id` int(11) NOT NULL,
  `subject_specialty` varchar(100) DEFAULT NULL,
  `qualification_level` varchar(100) DEFAULT NULL,
  `approval_status` enum('pending','approved','rejected') DEFAULT 'pending',
  `approval_date` datetime DEFAULT NULL,
  `approved_by` int(11) DEFAULT NULL,
  `rejection_reason` text DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`teacher_id`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `school_id` (`school_id`),
  KEY `approved_by` (`approved_by`),
  CONSTRAINT `teachers_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `teachers_ibfk_2` FOREIGN KEY (`school_id`) REFERENCES `schools` (`school_id`) ON DELETE CASCADE,
  CONSTRAINT `teachers_ibfk_3` FOREIGN KEY (`approved_by`) REFERENCES `users` (`user_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `users` (
  `user_id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(100) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `password_hash` varchar(255) NOT NULL,
  `phone` varchar(15) DEFAULT NULL,
  `full_name` varchar(255) DEFAULT NULL,
  `role` enum('student','teacher','admin') NOT NULL,
  `school_id` int(11) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `is_first_login` tinyint(1) DEFAULT 1,
  `two_fa_secret` varchar(255) DEFAULT NULL,
  `two_fa_enabled` tinyint(1) DEFAULT 0,
  `last_login` datetime DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `username` (`username`),
  KEY `school_id` (`school_id`),
  KEY `idx_user_role` (`role`),
  CONSTRAINT `users_ibfk_1` FOREIGN KEY (`school_id`) REFERENCES `schools` (`school_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO subjects (subject_code, subject_name, group_code, exam_type, duration_minutes) VALUES
('TOAN', 'Toán', 'group1', 'multiple_choice', 90),
('NVVAN', 'Ngữ Văn', 'group1', 'essay', 120),
('VAT_LI', 'Vật Lí', 'group2', 'multiple_choice', 50),
('HOA_HO', 'Hóa Học', 'group2', 'multiple_choice', 50),
('SINH_H', 'Sinh Học', 'group2', 'multiple_choice', 50),
('DIA_LI', 'Địa Lí', 'group3', 'multiple_choice', 50),
('LICH_S', 'Lịch Sử', 'group3', 'multiple_choice', 50),
('GDKTVL', 'Giáo Dục Kinh Tế và Pháp Luật', 'group3', 'multiple_choice', 50),
('TIN_HO', 'Tin Học', 'group4', 'multiple_choice', 50),
('CNNG', 'Công Nghệ Công Nghiệp', 'group5', 'multiple_choice', 50),
('CNNN', 'Công Nghệ Nông Nghiệp', 'group5', 'multiple_choice', 50),
('TIENG_ANH', 'Tiếng Anh', 'language', 'multiple_choice', 50),
('TIENG_RU', 'Tiếng Nga', 'language', 'multiple_choice', 50),
('TIENG_PH', 'Tiếng Pháp', 'language', 'multiple_choice', 50),
('TIENG_TR', 'Tiếng Trung', 'language', 'multiple_choice', 50),
('TIENG_DU', 'Tiếng Đức', 'language', 'multiple_choice', 50),
('TIENG_NH', 'Tiếng Nhật', 'language', 'multiple_choice', 50),
('TIENG_HAN', 'Tiếng Hàn', 'language', 'multiple_choice', 50),
('MT', 'Miễn thi', 'group0', 'multiple_choice', 0);

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
