-- 已有数据库增量升级脚本
-- 运行方式：mysql -u root -p llm_ppt_generator < database/upgrade_rag_outline.sql

USE llm_ppt_generator;

CREATE TABLE IF NOT EXISTS `uploaded_files` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '文件ID',
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
  `original_filename` VARCHAR(255) NOT NULL COMMENT '原始文件名',
  `stored_filename` VARCHAR(255) NOT NULL COMMENT '服务端存储文件名',
  `file_path` VARCHAR(1024) NOT NULL COMMENT '服务端文件路径',
  `file_type` VARCHAR(16) NOT NULL COMMENT '文件类型',
  `file_size` BIGINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '文件大小',
  `parse_status` ENUM('pending', 'success', 'failed') NOT NULL DEFAULT 'pending' COMMENT '解析状态',
  `parse_error` TEXT NULL COMMENT '解析失败原因',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
  PRIMARY KEY (`id`),
  KEY `idx_uploaded_files_user_created_at` (`user_id`, `created_at`),
  KEY `idx_uploaded_files_parse_status` (`parse_status`),
  CONSTRAINT `fk_uploaded_files_user`
    FOREIGN KEY (`user_id`) REFERENCES `Users` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='上传文件表';

DELIMITER $$

CREATE PROCEDURE add_column_if_missing(
  IN table_name_param VARCHAR(64),
  IN column_name_param VARCHAR(64),
  IN ddl_param TEXT
)
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = table_name_param
      AND COLUMN_NAME = column_name_param
  ) THEN
    SET @ddl_sql = ddl_param;
    PREPARE stmt FROM @ddl_sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
  END IF;
END$$

DELIMITER ;

CALL add_column_if_missing('PPT_Records', 'template_id', 'ALTER TABLE `PPT_Records` ADD COLUMN `template_id` VARCHAR(64) NULL COMMENT ''模板ID'' AFTER `points_cost`');
CALL add_column_if_missing('PPT_Records', 'outline_json', 'ALTER TABLE `PPT_Records` ADD COLUMN `outline_json` LONGTEXT NULL COMMENT ''确认后的大纲JSON'' AFTER `image_provider`');
CALL add_column_if_missing('PPT_Records', 'progress_step', 'ALTER TABLE `PPT_Records` ADD COLUMN `progress_step` VARCHAR(255) NULL COMMENT ''当前进度'' AFTER `outline_json`');
CALL add_column_if_missing('PPT_Records', 'download_url', 'ALTER TABLE `PPT_Records` ADD COLUMN `download_url` VARCHAR(1024) NULL COMMENT ''下载地址'' AFTER `file_path`');

DROP PROCEDURE add_column_if_missing;

ALTER TABLE `PPT_Records`
  MODIFY COLUMN `status` ENUM('outline_ready', 'generating', 'success', 'failed') NOT NULL DEFAULT 'generating' COMMENT '生成状态';
