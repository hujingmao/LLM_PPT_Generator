-- 基于大模型的 PPT 自动生成系统数据库初始化脚本
-- 运行方式：mysql -u root -p < database/schema.sql

CREATE DATABASE IF NOT EXISTS llm_ppt_generator
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE llm_ppt_generator;

-- 用户表：保存登录信息、积分余额和账户状态。
CREATE TABLE IF NOT EXISTS `Users` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `username` VARCHAR(64) NOT NULL COMMENT '用户名',
  `email` VARCHAR(255) NULL COMMENT '邮箱',
  `password_hash` VARCHAR(255) NOT NULL COMMENT '密码哈希',
  `points_balance` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '积分余额',
  `account_balance` DECIMAL(10, 2) NOT NULL DEFAULT 0.00 COMMENT '累计充值金额',
  `status` ENUM('active', 'disabled') NOT NULL DEFAULT 'active' COMMENT '账户状态',
  `last_login_at` DATETIME NULL COMMENT '最后登录时间',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_users_username` (`username`),
  UNIQUE KEY `uk_users_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 充值订单表：保留模拟支付闭环，便于展示商业化能力。
CREATE TABLE IF NOT EXISTS `Recharge_Orders` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '订单ID',
  `order_no` VARCHAR(64) NOT NULL COMMENT '业务订单号',
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
  `amount` DECIMAL(10, 2) NOT NULL COMMENT '充值金额',
  `points` INT UNSIGNED NOT NULL COMMENT '到账积分',
  `status` ENUM('pending', 'paid', 'failed', 'closed') NOT NULL DEFAULT 'pending' COMMENT '订单状态',
  `pay_channel` VARCHAR(32) NOT NULL DEFAULT 'mock' COMMENT '支付渠道',
  `paid_at` DATETIME NULL COMMENT '支付完成时间',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_recharge_orders_order_no` (`order_no`),
  KEY `idx_recharge_orders_user_id` (`user_id`),
  KEY `idx_recharge_orders_status_created_at` (`status`, `created_at`),
  CONSTRAINT `fk_recharge_orders_user`
    FOREIGN KEY (`user_id`) REFERENCES `Users` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='充值订单表';

-- 上传文件表：记录用户上传资料的基本信息和解析状态。
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

-- PPT 生成记录表：保存大纲、进度、文件路径、下载地址和积分消耗。
CREATE TABLE IF NOT EXISTS `PPT_Records` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '记录ID',
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
  `ppt_topic` VARCHAR(255) NOT NULL COMMENT 'PPT主题',
  `scene` VARCHAR(64) NULL COMMENT '使用场景',
  `style` VARCHAR(64) NULL COMMENT '生成风格',
  `page_count` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '生成页数',
  `points_cost` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '消耗积分',
  `template_id` VARCHAR(64) NULL COMMENT '模板ID',
  `template_name` VARCHAR(255) NULL COMMENT '模板名称',
  `image_provider` VARCHAR(32) NULL COMMENT '配图来源',
  `outline_json` LONGTEXT NULL COMMENT '确认后的大纲JSON',
  `progress_step` VARCHAR(255) NULL COMMENT '当前进度',
  `error_message` TEXT NULL COMMENT '失败原因',
  `file_path` VARCHAR(1024) NULL COMMENT 'PPT文件路径',
  `download_url` VARCHAR(1024) NULL COMMENT '下载地址',
  `status` ENUM('outline_ready', 'generating', 'success', 'failed') NOT NULL DEFAULT 'generating' COMMENT '生成状态',
  `generated_at` DATETIME NULL COMMENT '生成完成时间',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_ppt_records_user_created_at` (`user_id`, `created_at`),
  KEY `idx_ppt_records_status_created_at` (`status`, `created_at`),
  CONSTRAINT `fk_ppt_records_user`
    FOREIGN KEY (`user_id`) REFERENCES `Users` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='PPT生成记录表';
