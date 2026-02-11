/*
 Navicat Premium Data Transfer

 Source Server         : 172.16.1.103_3306
 Source Server Type    : MySQL
 Source Server Version : 80044
 Source Host           : 172.16.1.103:3306
 Source Schema         : dw

 Target Server Type    : MySQL
 Target Server Version : 80044
 File Encoding         : 65001

 Date: 10/02/2026 21:53:49
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for etl_job_sql
-- ----------------------------
DROP TABLE IF EXISTS `etl_job_sql`;
CREATE TABLE `etl_job_sql`  (
  `id` int NOT NULL,
  `server_id` int NOT NULL COMMENT '目标服务器',
  `db_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '目标数据库',
  `sql_text` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT 'sql',
  `last_execution_time` datetime NULL DEFAULT NULL COMMENT '上次执行时间',
  `remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '备注'
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'ETL-作业类型-SQL' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for etl_job_sync
-- ----------------------------
DROP TABLE IF EXISTS `etl_job_sync`;
CREATE TABLE `etl_job_sync`  (
  `id` int NOT NULL,
  `param_server_id` int NULL DEFAULT NULL COMMENT '参数服务器',
  `param_db_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '参数数据库',
  `param_sql` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '取参数sql',
  `from_server_id` int NULL DEFAULT NULL COMMENT '来源服务器',
  `from_db_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '来源数据库',
  `from_sql` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '取数SQL',
  `before_write` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '写入前执行',
  `to_server_id` int NOT NULL COMMENT '目标服务器',
  `to_db_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '目标数据库',
  `to_table` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '目标表名',
  `to_columns` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '目标字段(逗号分隔,不带空格)',
  `after_write` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '写入完成后执行',
  `last_execution_time` datetime NULL DEFAULT NULL COMMENT '上次执行时间'
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'ETL-作业类型-数据同步' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for etl_log
-- ----------------------------
DROP TABLE IF EXISTS `etl_log`;
CREATE TABLE `etl_log`  (
  `id` bigint NOT NULL,
  `job_id` int NOT NULL COMMENT 'etl_job.id',
  `start_time` datetime NULL DEFAULT NULL COMMENT '开始时间',
  `end_time` datetime NULL DEFAULT NULL COMMENT '完成时间',
  `execution_status` int NULL DEFAULT NULL COMMENT '执行状态',
  `message` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '信息',
  `job_params` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '执行参数',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `job_id`(`job_id` ASC) USING BTREE,
  INDEX `id`(`id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'ETL-作业日志' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for etl_server
-- ----------------------------
DROP TABLE IF EXISTS `etl_server`;
CREATE TABLE `etl_server`  (
  `server_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `conn_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '连接类型(sqlite,mysql,mssql,oracle,pgsql,clickhouse)',
  `host` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `username` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `password` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `port` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `db_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'ETL-服务器列表' ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
