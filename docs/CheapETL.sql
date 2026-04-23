SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for etl_error_handling_config
-- ----------------------------
DROP TABLE IF EXISTS `etl_error_handling_config`;
CREATE TABLE `etl_error_handling_config`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `error_pattern` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `pattern_desc` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `action_type` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `action_params` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 6 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for etl_job_check
-- ----------------------------
DROP TABLE IF EXISTS `etl_job_check`;
CREATE TABLE `etl_job_check`  (
  `id` int(0) NOT NULL,
  `server_id` int(0) NULL DEFAULT NULL COMMENT '目标服务器',
  `db_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '目标数据库',
  `check_sql` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '校验SQL(只取第一行第一列的值, 值不为\'\'时发送通知)',
  `robot_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '通知机器人id',
  `last_execution_time` datetime(0) NULL DEFAULT NULL COMMENT '上次执行时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'ETL-作业类型-数据校验' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for etl_job_sql
-- ----------------------------
DROP TABLE IF EXISTS `etl_job_sql`;
CREATE TABLE `etl_job_sql`  (
  `id` int(0) NOT NULL,
  `server_id` int(0) NOT NULL COMMENT '目标服务器',
  `db_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '目标数据库',
  `sql_text` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT 'sql',
  `last_execution_time` datetime(0) NULL DEFAULT NULL COMMENT '上次执行时间',
  `remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '备注'
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'ETL-作业类型-SQL' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for etl_job_sync
-- ----------------------------
DROP TABLE IF EXISTS `etl_job_sync`;
CREATE TABLE `etl_job_sync`  (
  `id` int(0) NOT NULL,
  `param_server_id` int(0) NULL DEFAULT NULL COMMENT '参数服务器',
  `param_db_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '参数数据库',
  `param_sql` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '取参数sql',
  `from_server_id` int(0) NULL DEFAULT NULL COMMENT '来源服务器',
  `from_db_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '来源数据库',
  `from_sql` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '取数SQL',
  `to_server_id` int(0) NOT NULL COMMENT '目标服务器',
  `to_db_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '目标数据库',
  `to_table` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '目标表名',
  `before_write` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '写入前执行',
  `note` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '备注',
  `to_columns` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '目标字段(逗号分隔,不带空格)',
  `after_write` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '写入完成后执行',
  `last_execution_time` datetime(0) NULL DEFAULT NULL COMMENT '上次执行时间'
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'ETL-作业类型-数据同步' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for etl_log
-- ----------------------------
DROP TABLE IF EXISTS `etl_log`;
CREATE TABLE `etl_log`  (
  `id` bigint(0) NOT NULL,
  `job_id` int(0) NOT NULL COMMENT 'etl_job.id',
  `start_time` datetime(0) NULL DEFAULT NULL COMMENT '开始时间',
  `end_time` datetime(0) NULL DEFAULT NULL COMMENT '完成时间',
  `execution_status` int(0) NULL DEFAULT NULL COMMENT '执行状态',
  `message` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '信息',
  `job_params` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '执行参数',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `job_id`(`job_id`) USING BTREE,
  INDEX `id`(`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'ETL-作业日志' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for etl_robot
-- ----------------------------
DROP TABLE IF EXISTS `etl_robot`;
CREATE TABLE `etl_robot`  (
  `robot_id` int(0) NOT NULL,
  `access_token` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `secret` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`robot_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'ETL-钉钉机器人' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for etl_robot_message
-- ----------------------------
DROP TABLE IF EXISTS `etl_robot_message`;
CREATE TABLE `etl_robot_message`  (
  `robot_id` int(0) NOT NULL,
  `send_time` datetime(0) NULL DEFAULT NULL,
  `text` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'ETL-钉钉机器人消息记录' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for etl_server
-- ----------------------------
DROP TABLE IF EXISTS `etl_server`;
CREATE TABLE `etl_server`  (
  `server_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `server_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '名称',
  `conn_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '连接类型(sqlite,mysql,mssql,oracle,pgsql,clickhouse)',
  `host` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `username` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `password` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `port` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `db_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'ETL-服务器列表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- View structure for ETL日志
-- ----------------------------
DROP VIEW IF EXISTS `ETL日志`;
CREATE ALGORITHM = UNDEFINED SQL SECURITY DEFINER VIEW `ETL日志` AS select timestampdiff(SECOND,`etl_log`.`start_time`,`etl_log`.`end_time`) AS `用时`,`etl_log`.`job_id` AS `job_id`,`etl_log`.`start_time` AS `开始时间`,`etl_log`.`end_time` AS `结束时间`,(case when (`etl_log`.`execution_status` = 1) then '排队中' when (`etl_log`.`execution_status` = 2) then '执行中' when (`etl_log`.`execution_status` = 3) then '执行成功' when (`etl_log`.`execution_status` = -(1)) then '执行失败' else concat(`etl_log`.`execution_status`,'') end) AS `执行状态`,`etl_log`.`message` AS `作业信息`,`etl_log`.`job_params` AS `执行参数`,`etl_log`.`id` AS `id` from `etl_log` where (`etl_log`.`start_time` >= (now() - interval 7 day)) order by `etl_log`.`id` desc;

SET FOREIGN_KEY_CHECKS = 1;
