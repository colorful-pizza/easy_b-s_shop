/*
 Navicat MySQL Data Transfer

 Source Server         : localhost_3306
 Source Server Type    : MySQL
 Source Server Version : 80012
 Source Host           : localhost:3306
 Source Schema         : shop

 Target Server Type    : MySQL
 Target Server Version : 80012
 File Encoding         : 65001

 Date: 22/09/2025 16:51:37
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for customers
-- ----------------------------
DROP TABLE IF EXISTS `customers`;
CREATE TABLE `customers`  (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '客户ID',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '客户姓名/企业名称',
  `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '联系电话',
  `address` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '地址',
  `is_default` tinyint(1) NULL DEFAULT 0 COMMENT '是否默认客户（散户）：1-是，0-否',
  `status` enum('active','inactive') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'active' COMMENT '状态',
  `created_at` timestamp(0) NULL DEFAULT CURRENT_TIMESTAMP(0) COMMENT '创建时间',
  `remark` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '备注',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 5 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '客户表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of customers
-- ----------------------------
INSERT INTO `customers` VALUES (1, '散户', NULL, NULL, 1, 'active', '2025-09-19 17:57:30', '默认散户客户');
INSERT INTO `customers` VALUES (2, '张三', '13900139001', '某某小区1号楼', 0, 'active', '2025-09-19 17:57:30', '老客户');
INSERT INTO `customers` VALUES (3, '李四', '13900139002', '某某小区2号楼', 0, 'inactive', '2025-09-19 17:57:30', '会员客户');
INSERT INTO `customers` VALUES (4, '王五', '13900139003', '北京鸟巢体育馆', 0, 'active', '2025-09-20 10:49:33', '优质客户');

-- ----------------------------
-- Table structure for incoming_details
-- ----------------------------
DROP TABLE IF EXISTS `incoming_details`;
CREATE TABLE `incoming_details`  (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '明细ID',
  `incoming_id` int(11) NOT NULL COMMENT '进货ID',
  `product_id` int(11) NOT NULL COMMENT '商品ID',
  `quantity` int(11) NOT NULL COMMENT '进货数量',
  `cost_price` decimal(10, 2) NOT NULL COMMENT '进价',
  `amount` decimal(10, 2) NOT NULL COMMENT '小计金额',
  `production_date` date NULL DEFAULT NULL COMMENT '生产日期',
  `expiry_date` date NULL DEFAULT NULL COMMENT '过期日期',
  `batch_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '批次号',
  `remark` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '备注',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `incoming_id`(`incoming_id`) USING BTREE,
  INDEX `product_id`(`product_id`) USING BTREE,
  CONSTRAINT `incoming_details_ibfk_1` FOREIGN KEY (`incoming_id`) REFERENCES `incoming_orders` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `incoming_details_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 14 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '进货明细表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of incoming_details
-- ----------------------------
INSERT INTO `incoming_details` VALUES (2, 2, 4, 100, 2.40, 240.00, NULL, NULL, '232323', NULL);
INSERT INTO `incoming_details` VALUES (3, 3, 1, 100, 2.60, 260.00, NULL, NULL, NULL, NULL);
INSERT INTO `incoming_details` VALUES (4, 3, 2, 150, 2.50, 375.00, NULL, NULL, NULL, NULL);
INSERT INTO `incoming_details` VALUES (5, 3, 3, 60, 3.20, 192.00, NULL, NULL, NULL, NULL);
INSERT INTO `incoming_details` VALUES (6, 3, 4, 120, 2.20, 264.00, NULL, NULL, NULL, NULL);
INSERT INTO `incoming_details` VALUES (7, 3, 5, 200, 1.30, 260.00, NULL, NULL, NULL, NULL);
INSERT INTO `incoming_details` VALUES (8, 3, 6, 40, 3.90, 156.00, NULL, NULL, NULL, NULL);
INSERT INTO `incoming_details` VALUES (9, 3, 7, 60, 5.00, 300.00, NULL, NULL, NULL, NULL);
INSERT INTO `incoming_details` VALUES (10, 3, 8, 200, 3.80, 760.00, NULL, NULL, NULL, NULL);
INSERT INTO `incoming_details` VALUES (11, 3, 9, 60, 3.00, 180.00, NULL, NULL, NULL, NULL);
INSERT INTO `incoming_details` VALUES (12, 3, 10, 60, 6.50, 390.00, NULL, NULL, NULL, NULL);
INSERT INTO `incoming_details` VALUES (13, 4, 8, 100, 2.50, 250.00, NULL, NULL, NULL, NULL);

-- ----------------------------
-- Table structure for incoming_orders
-- ----------------------------
DROP TABLE IF EXISTS `incoming_orders`;
CREATE TABLE `incoming_orders`  (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '进货ID',
  `order_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '进货单号',
  `purchase_id` int(11) NULL DEFAULT NULL COMMENT '关联采购申请ID',
  `supplier_id` int(11) NOT NULL COMMENT '供应商ID',
  `total_amount` decimal(10, 2) NULL DEFAULT 0.00 COMMENT '总金额',
  `incoming_date` date NOT NULL COMMENT '进货日期',
  `user_id` int(11) NOT NULL COMMENT '操作人ID',
  `created_at` timestamp(0) NULL DEFAULT CURRENT_TIMESTAMP(0) COMMENT '创建时间',
  `remark` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '备注',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `order_no`(`order_no`) USING BTREE,
  INDEX `purchase_id`(`purchase_id`) USING BTREE,
  INDEX `supplier_id`(`supplier_id`) USING BTREE,
  INDEX `user_id`(`user_id`) USING BTREE,
  CONSTRAINT `incoming_orders_ibfk_1` FOREIGN KEY (`purchase_id`) REFERENCES `purchase_orders` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `incoming_orders_ibfk_2` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `incoming_orders_ibfk_3` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 5 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '进货表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of incoming_orders
-- ----------------------------
INSERT INTO `incoming_orders` VALUES (2, 'IN20250920174245', 3, 3, 240.00, '2025-09-20', 3, '2025-09-20 17:42:45', NULL);
INSERT INTO `incoming_orders` VALUES (3, 'IN20250921130700', 7, 5, 3137.00, '2025-09-21', 3, '2025-09-21 13:07:00', NULL);
INSERT INTO `incoming_orders` VALUES (4, 'IN20250922141435', 4, 3, 250.00, '2025-09-22', 3, '2025-09-22 14:14:35', NULL);

-- ----------------------------
-- Table structure for inventory
-- ----------------------------
DROP TABLE IF EXISTS `inventory`;
CREATE TABLE `inventory`  (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '库存ID',
  `product_id` int(11) NOT NULL COMMENT '商品ID',
  `quantity` int(11) NOT NULL DEFAULT 0 COMMENT '库存数量',
  `updated_at` timestamp(0) NULL DEFAULT CURRENT_TIMESTAMP(0) ON UPDATE CURRENT_TIMESTAMP(0) COMMENT '更新时间',
  `remark` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '备注',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `product_id`(`product_id`) USING BTREE,
  CONSTRAINT `inventory_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 11 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '库存表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of inventory
-- ----------------------------
INSERT INTO `inventory` VALUES (1, 1, 90, '2025-09-22 00:03:25', '初始库存');
INSERT INTO `inventory` VALUES (2, 2, 149, '2025-09-21 17:34:03', '初始库存');
INSERT INTO `inventory` VALUES (3, 3, 60, '2025-09-21 13:07:00', '初始库存');
INSERT INTO `inventory` VALUES (4, 4, 220, '2025-09-21 13:07:00', '初始库存');
INSERT INTO `inventory` VALUES (5, 5, 197, '2025-09-22 14:07:57', '初始库存');
INSERT INTO `inventory` VALUES (6, 6, 39, '2025-09-22 14:09:27', '初始库存');
INSERT INTO `inventory` VALUES (7, 7, 0, '2025-09-21 16:55:59', '初始库存');
INSERT INTO `inventory` VALUES (8, 8, 294, '2025-09-22 14:16:26', '初始库存');
INSERT INTO `inventory` VALUES (9, 9, 10, '2025-09-21 16:55:35', '初始库存');
INSERT INTO `inventory` VALUES (10, 10, 60, '2025-09-21 13:07:00', '初始库存');
INSERT INTO `inventory` VALUES (11, 11, 0, '2025-09-22 16:44:21', '初始库存');

-- ----------------------------
-- Table structure for inventory_check_details
-- ----------------------------
DROP TABLE IF EXISTS `inventory_check_details`;
CREATE TABLE `inventory_check_details`  (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '明细ID',
  `check_id` int(11) NOT NULL COMMENT '盘点ID',
  `product_id` int(11) NOT NULL COMMENT '商品ID',
  `book_quantity` int(11) NOT NULL COMMENT '账面数量',
  `actual_quantity` int(11) NOT NULL COMMENT '实际数量',
  `difference` int(11) NOT NULL COMMENT '差异数量（实际-账面）',
  `difference_type` enum('normal','gain','loss') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '差异类型：normal-正常，gain-盘盈，loss-盘亏',
  `handled` tinyint(1) NULL DEFAULT 0 COMMENT '是否已处理：1-是，0-否',
  `remark` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '备注',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `check_id`(`check_id`) USING BTREE,
  INDEX `product_id`(`product_id`) USING BTREE,
  CONSTRAINT `inventory_check_details_ibfk_1` FOREIGN KEY (`check_id`) REFERENCES `inventory_checks` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `inventory_check_details_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 29 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '库存盘点明细表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of inventory_check_details
-- ----------------------------
INSERT INTO `inventory_check_details` VALUES (1, 1, 7, 60, 60, 0, 'normal', 1, NULL);
INSERT INTO `inventory_check_details` VALUES (2, 1, 8, 200, 200, 0, 'normal', 1, NULL);
INSERT INTO `inventory_check_details` VALUES (3, 1, 5, 200, 200, 0, 'normal', 1, NULL);
INSERT INTO `inventory_check_details` VALUES (4, 1, 1, 100, 100, 0, 'normal', 1, NULL);
INSERT INTO `inventory_check_details` VALUES (5, 1, 6, 40, 40, 0, 'normal', 1, NULL);
INSERT INTO `inventory_check_details` VALUES (6, 1, 10, 60, 60, 0, 'normal', 1, NULL);
INSERT INTO `inventory_check_details` VALUES (7, 1, 3, 60, 60, 0, 'normal', 1, NULL);
INSERT INTO `inventory_check_details` VALUES (8, 1, 9, 60, 60, 0, 'normal', 1, NULL);
INSERT INTO `inventory_check_details` VALUES (9, 1, 2, 150, 150, 0, 'normal', 1, NULL);
INSERT INTO `inventory_check_details` VALUES (10, 1, 4, 220, 220, 0, 'normal', 1, NULL);
INSERT INTO `inventory_check_details` VALUES (11, 2, 8, 200, 200, 0, 'normal', 1, NULL);
INSERT INTO `inventory_check_details` VALUES (12, 2, 5, 200, 200, 0, 'normal', 1, NULL);
INSERT INTO `inventory_check_details` VALUES (13, 2, 1, 94, 94, 0, 'normal', 1, NULL);
INSERT INTO `inventory_check_details` VALUES (14, 2, 6, 40, 40, 0, 'normal', 1, NULL);
INSERT INTO `inventory_check_details` VALUES (15, 2, 10, 60, 60, 0, 'normal', 1, NULL);
INSERT INTO `inventory_check_details` VALUES (16, 2, 3, 60, 60, 0, 'normal', 1, NULL);
INSERT INTO `inventory_check_details` VALUES (17, 2, 9, 10, 10, 0, 'normal', 1, NULL);
INSERT INTO `inventory_check_details` VALUES (18, 2, 2, 149, 149, 0, 'normal', 1, NULL);
INSERT INTO `inventory_check_details` VALUES (19, 2, 4, 220, 220, 0, 'normal', 1, NULL);
INSERT INTO `inventory_check_details` VALUES (20, 3, 8, 295, 294, -1, 'loss', 1, NULL);
INSERT INTO `inventory_check_details` VALUES (21, 3, 5, 197, 197, 0, 'normal', 1, NULL);
INSERT INTO `inventory_check_details` VALUES (22, 3, 1, 90, 90, 0, 'normal', 1, NULL);
INSERT INTO `inventory_check_details` VALUES (23, 3, 6, 39, 39, 0, 'normal', 1, NULL);
INSERT INTO `inventory_check_details` VALUES (24, 3, 10, 60, 60, 0, 'normal', 1, NULL);
INSERT INTO `inventory_check_details` VALUES (25, 3, 3, 60, 60, 0, 'normal', 1, NULL);
INSERT INTO `inventory_check_details` VALUES (26, 3, 9, 10, 10, 0, 'normal', 1, NULL);
INSERT INTO `inventory_check_details` VALUES (27, 3, 2, 149, 149, 0, 'normal', 1, NULL);
INSERT INTO `inventory_check_details` VALUES (28, 3, 4, 220, 220, 0, 'normal', 1, NULL);
INSERT INTO `inventory_check_details` VALUES (29, 4, 8, 294, 294, 0, 'normal', 0, NULL);
INSERT INTO `inventory_check_details` VALUES (30, 4, 5, 197, 197, 0, 'normal', 0, NULL);
INSERT INTO `inventory_check_details` VALUES (31, 4, 1, 90, 90, 0, 'normal', 0, NULL);
INSERT INTO `inventory_check_details` VALUES (32, 4, 6, 39, 39, 0, 'normal', 0, NULL);
INSERT INTO `inventory_check_details` VALUES (33, 4, 10, 60, 60, 0, 'normal', 0, NULL);
INSERT INTO `inventory_check_details` VALUES (34, 4, 3, 60, 60, 0, 'normal', 0, NULL);
INSERT INTO `inventory_check_details` VALUES (35, 4, 9, 10, 10, 0, 'normal', 0, NULL);
INSERT INTO `inventory_check_details` VALUES (36, 4, 11, 0, 0, 0, 'normal', 0, NULL);
INSERT INTO `inventory_check_details` VALUES (37, 4, 2, 149, 149, 0, 'normal', 0, NULL);
INSERT INTO `inventory_check_details` VALUES (38, 4, 4, 220, 220, 0, 'normal', 0, NULL);

-- ----------------------------
-- Table structure for inventory_checks
-- ----------------------------
DROP TABLE IF EXISTS `inventory_checks`;
CREATE TABLE `inventory_checks`  (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '盘点ID',
  `check_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '盘点单号',
  `check_date` date NOT NULL COMMENT '盘点日期',
  `status` enum('ongoing','completed') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'ongoing' COMMENT '状态：ongoing-进行中，completed-已完成',
  `total_difference` int(11) NULL DEFAULT 0 COMMENT '总差异数量（正数盘盈，负数盘亏）',
  `user_id` int(11) NOT NULL COMMENT '盘点人ID',
  `created_at` timestamp(0) NULL DEFAULT CURRENT_TIMESTAMP(0) COMMENT '创建时间',
  `remark` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '备注',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `check_no`(`check_no`) USING BTREE,
  INDEX `user_id`(`user_id`) USING BTREE,
  CONSTRAINT `inventory_checks_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '库存盘点表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of inventory_checks
-- ----------------------------
INSERT INTO `inventory_checks` VALUES (1, 'CHK20250921132509', '2025-09-21', 'completed', 0, 3, '2025-09-21 13:25:09', NULL);
INSERT INTO `inventory_checks` VALUES (2, 'CHK20250921233438', '2025-09-21', 'completed', 0, 3, '2025-09-21 23:34:38', NULL);
INSERT INTO `inventory_checks` VALUES (3, 'CHK20250922141552', '2025-09-22', 'completed', -1, 3, '2025-09-22 14:15:52', NULL);
INSERT INTO `inventory_checks` VALUES (4, 'CHK20250922164913', '2025-09-22', 'ongoing', 0, 3, '2025-09-22 16:49:13', NULL);

-- ----------------------------
-- Table structure for outgoing_details
-- ----------------------------
DROP TABLE IF EXISTS `outgoing_details`;
CREATE TABLE `outgoing_details`  (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '明细ID',
  `outgoing_id` int(11) NOT NULL COMMENT '出货ID',
  `product_id` int(11) NOT NULL COMMENT '商品ID',
  `quantity` int(11) NOT NULL COMMENT '出货数量',
  `selling_price` decimal(10, 2) NOT NULL COMMENT '销售价格',
  `cost_price` decimal(10, 2) NOT NULL COMMENT '成本价格（进价）',
  `amount` decimal(10, 2) NOT NULL COMMENT '销售小计',
  `cost_amount` decimal(10, 2) NOT NULL COMMENT '成本小计',
  `profit` decimal(10, 2) NOT NULL COMMENT '利润',
  `remark` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '备注',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `outgoing_id`(`outgoing_id`) USING BTREE,
  INDEX `product_id`(`product_id`) USING BTREE,
  CONSTRAINT `outgoing_details_ibfk_1` FOREIGN KEY (`outgoing_id`) REFERENCES `outgoing_orders` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `outgoing_details_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 11 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '出货明细表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of outgoing_details
-- ----------------------------
INSERT INTO `outgoing_details` VALUES (1, 1, 9, 50, 3.80, 3.00, 190.00, 150.00, 40.00, NULL);
INSERT INTO `outgoing_details` VALUES (2, 2, 7, 60, 6.00, 5.00, 360.00, 300.00, 60.00, NULL);
INSERT INTO `outgoing_details` VALUES (3, 3, 1, 5, 3.50, 2.60, 17.50, 13.00, 4.50, NULL);
INSERT INTO `outgoing_details` VALUES (4, 4, 1, 1, 3.50, 2.60, 3.50, 2.60, 0.90, NULL);
INSERT INTO `outgoing_details` VALUES (5, 4, 2, 1, 3.50, 2.50, 3.50, 2.50, 1.00, NULL);
INSERT INTO `outgoing_details` VALUES (6, 5, 1, 4, 3.50, 2.60, 14.00, 10.40, 3.60, NULL);
INSERT INTO `outgoing_details` VALUES (7, 6, 8, 4, 4.50, 3.80, 18.00, 15.20, 2.80, NULL);
INSERT INTO `outgoing_details` VALUES (8, 6, 5, 3, 2.00, 1.30, 6.00, 3.90, 2.10, NULL);
INSERT INTO `outgoing_details` VALUES (9, 7, 8, 1, 4.50, 3.80, 4.50, 3.80, 0.70, NULL);
INSERT INTO `outgoing_details` VALUES (10, 7, 6, 1, 5.00, 3.90, 5.00, 3.90, 1.10, NULL);

-- ----------------------------
-- Table structure for outgoing_orders
-- ----------------------------
DROP TABLE IF EXISTS `outgoing_orders`;
CREATE TABLE `outgoing_orders`  (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '出货ID',
  `order_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '出货单号',
  `customer_id` int(11) NULL DEFAULT NULL COMMENT '客户ID',
  `total_amount` decimal(10, 2) NULL DEFAULT 0.00 COMMENT '总销售金额',
  `total_cost` decimal(10, 2) NULL DEFAULT 0.00 COMMENT '总成本金额',
  `profit` decimal(10, 2) NULL DEFAULT 0.00 COMMENT '利润',
  `sale_date` date NOT NULL COMMENT '销售日期',
  `user_id` int(11) NOT NULL COMMENT '操作人ID',
  `created_at` timestamp(0) NULL DEFAULT CURRENT_TIMESTAMP(0) COMMENT '创建时间',
  `remark` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '备注',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `order_no`(`order_no`) USING BTREE,
  INDEX `customer_id`(`customer_id`) USING BTREE,
  INDEX `user_id`(`user_id`) USING BTREE,
  CONSTRAINT `outgoing_orders_ibfk_1` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `outgoing_orders_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 8 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '出货表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of outgoing_orders
-- ----------------------------
INSERT INTO `outgoing_orders` VALUES (1, 'OUT20250921165535', 1, 190.00, 150.00, 40.00, '2025-09-21', 3, '2025-09-21 16:55:35', NULL);
INSERT INTO `outgoing_orders` VALUES (2, 'OUT20250921165559', 1, 360.00, 300.00, 60.00, '2025-09-21', 3, '2025-09-21 16:55:59', NULL);
INSERT INTO `outgoing_orders` VALUES (3, 'OUT20250921172707', 1, 17.50, 13.00, 4.50, '2025-09-21', 3, '2025-09-21 17:27:07', NULL);
INSERT INTO `outgoing_orders` VALUES (4, 'OUT20250921173403', 1, 7.00, 5.10, 1.90, '2025-09-21', 3, '2025-09-21 17:34:03', NULL);
INSERT INTO `outgoing_orders` VALUES (5, 'OUT20250922000325', 1, 14.00, 10.40, 3.60, '2025-09-21', 3, '2025-09-22 00:03:25', NULL);
INSERT INTO `outgoing_orders` VALUES (6, 'OUT20250922140757', 1, 24.00, 19.10, 4.90, '2025-09-22', 3, '2025-09-22 14:07:57', NULL);
INSERT INTO `outgoing_orders` VALUES (7, 'OUT20250922140927', 1, 9.50, 7.70, 1.80, '2025-09-22', 3, '2025-09-22 14:09:27', NULL);

-- ----------------------------
-- Table structure for products
-- ----------------------------
DROP TABLE IF EXISTS `products`;
CREATE TABLE `products`  (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '商品ID',
  `code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '商品编码',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '商品名称',
  `category` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '商品分类',
  `brand` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '品牌',
  `unit` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '件' COMMENT '单位',
  `selling_price` decimal(10, 2) NOT NULL COMMENT '销售价格',
  `status` enum('active','inactive') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'active' COMMENT '状态',
  `created_at` timestamp(0) NULL DEFAULT CURRENT_TIMESTAMP(0) COMMENT '创建时间',
  `remark` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '备注',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `code`(`code`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 11 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '商品表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of products
-- ----------------------------
INSERT INTO `products` VALUES (1, 'P001', '可口可乐330ml', '饮料', '可口可乐', '瓶', 3.50, 'active', '2025-09-19 17:57:30', '经典可乐');
INSERT INTO `products` VALUES (2, 'P002', '百事可乐330ml', '饮料', '百事', '瓶', 3.50, 'active', '2025-09-19 17:57:30', '百事可乐');
INSERT INTO `products` VALUES (3, 'P003', '康师傅红烧牛肉面', '方便食品', '康师傅', '包', 4.00, 'active', '2025-09-19 17:57:30', '经典口味');
INSERT INTO `products` VALUES (4, 'P004', '统一冰红茶500ml', '饮料', '统一', '瓶', 3.00, 'active', '2025-09-19 17:57:30', '冰红茶');
INSERT INTO `products` VALUES (5, 'P005', '农夫山泉550ml', '饮料', '农夫山泉', '瓶', 2.00, 'active', '2025-09-19 17:57:30', '天然水');
INSERT INTO `products` VALUES (6, 'P006', '士力架花生夹心巧克力', '零食', '士力架', '条', 5.00, 'active', '2025-09-19 17:57:30', '补充能量');
INSERT INTO `products` VALUES (7, 'P007', '乐事薯片黄瓜味', '零食', '乐事', '包', 6.00, 'inactive', '2025-09-19 17:57:30', '黄瓜味薯片');
INSERT INTO `products` VALUES (8, 'P008', '伊利纯牛奶250ml', '乳制品', '伊利', '盒', 4.50, 'active', '2025-09-19 17:57:30', '纯牛奶');
INSERT INTO `products` VALUES (9, 'P009', '旺仔牛奶245ml', '乳制品', '旺旺', '罐', 3.80, 'active', '2025-09-19 17:57:30', '复原乳');
INSERT INTO `products` VALUES (10, 'P010', '奥利奥饼干', '零食', '奥利奥', '包', 7.00, 'active', '2025-09-19 17:57:30', '夹心饼干');
INSERT INTO `products` VALUES (11, 'P011', '洁柔抽纸', '日用品', '洁柔', '包', 5.00, 'active', '2025-09-22 16:44:21', NULL);

-- ----------------------------
-- Table structure for purchase_details
-- ----------------------------
DROP TABLE IF EXISTS `purchase_details`;
CREATE TABLE `purchase_details`  (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '明细ID',
  `purchase_id` int(11) NOT NULL COMMENT '采购申请ID',
  `product_id` int(11) NOT NULL COMMENT '商品ID',
  `quantity` int(11) NOT NULL COMMENT '申请数量',
  `cost_price` decimal(10, 2) NOT NULL COMMENT '预计进价',
  `amount` decimal(10, 2) NOT NULL COMMENT '小计金额',
  `remark` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '备注',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `purchase_id`(`purchase_id`) USING BTREE,
  INDEX `product_id`(`product_id`) USING BTREE,
  CONSTRAINT `purchase_details_ibfk_1` FOREIGN KEY (`purchase_id`) REFERENCES `purchase_orders` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `purchase_details_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 28 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '采购申请明细表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of purchase_details
-- ----------------------------
INSERT INTO `purchase_details` VALUES (1, 1, 1, 100, 2.00, 200.00, NULL);
INSERT INTO `purchase_details` VALUES (2, 2, 3, 1000, 0.10, 100.00, NULL);
INSERT INTO `purchase_details` VALUES (3, 3, 4, 100, 2.40, 240.00, NULL);
INSERT INTO `purchase_details` VALUES (4, 4, 8, 100, 2.50, 250.00, NULL);
INSERT INTO `purchase_details` VALUES (5, 5, 8, 200, 3.80, 760.00, NULL);
INSERT INTO `purchase_details` VALUES (6, 6, 2, 400, 2.80, 1120.00, NULL);
INSERT INTO `purchase_details` VALUES (7, 6, 10, 50, 3.60, 180.00, NULL);
INSERT INTO `purchase_details` VALUES (18, 7, 1, 100, 2.60, 260.00, NULL);
INSERT INTO `purchase_details` VALUES (19, 7, 2, 150, 2.50, 375.00, NULL);
INSERT INTO `purchase_details` VALUES (20, 7, 3, 60, 3.20, 192.00, NULL);
INSERT INTO `purchase_details` VALUES (21, 7, 4, 120, 2.20, 264.00, NULL);
INSERT INTO `purchase_details` VALUES (22, 7, 5, 200, 1.30, 260.00, NULL);
INSERT INTO `purchase_details` VALUES (23, 7, 6, 40, 3.90, 156.00, NULL);
INSERT INTO `purchase_details` VALUES (24, 7, 7, 60, 5.00, 300.00, NULL);
INSERT INTO `purchase_details` VALUES (25, 7, 8, 200, 3.80, 760.00, NULL);
INSERT INTO `purchase_details` VALUES (26, 7, 9, 60, 3.00, 180.00, NULL);
INSERT INTO `purchase_details` VALUES (27, 7, 10, 60, 6.50, 390.00, NULL);

-- ----------------------------
-- Table structure for purchase_orders
-- ----------------------------
DROP TABLE IF EXISTS `purchase_orders`;
CREATE TABLE `purchase_orders`  (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '采购申请ID',
  `order_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '采购申请单号',
  `supplier_id` int(11) NOT NULL COMMENT '供应商ID',
  `status` enum('pending','approved','delivered','stock','paid','cancelled') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `total_amount` decimal(10, 2) NULL DEFAULT 0.00 COMMENT '总金额',
  `apply_user_id` int(11) NOT NULL COMMENT '申请人ID',
  `approve_user_id` int(11) NULL DEFAULT NULL COMMENT '审批人ID',
  `apply_time` timestamp(0) NULL DEFAULT CURRENT_TIMESTAMP(0) COMMENT '申请时间',
  `approve_time` timestamp(0) NULL DEFAULT NULL COMMENT '审批时间',
  `remark` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '备注',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `order_no`(`order_no`) USING BTREE,
  INDEX `supplier_id`(`supplier_id`) USING BTREE,
  INDEX `apply_user_id`(`apply_user_id`) USING BTREE,
  INDEX `approve_user_id`(`approve_user_id`) USING BTREE,
  CONSTRAINT `purchase_orders_ibfk_1` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `purchase_orders_ibfk_2` FOREIGN KEY (`apply_user_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `purchase_orders_ibfk_3` FOREIGN KEY (`approve_user_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 8 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '采购申请表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of purchase_orders
-- ----------------------------
INSERT INTO `purchase_orders` VALUES (1, 'PO20250920000319', 1, 'delivered', 200.00, 3, 3, '2025-09-20 00:03:20', '2025-09-20 00:04:16', NULL);
INSERT INTO `purchase_orders` VALUES (2, 'PO20250920000825', 2, 'cancelled', 100.00, 3, 3, '2025-09-20 00:08:25', '2025-09-20 00:08:35', NULL);
INSERT INTO `purchase_orders` VALUES (3, 'PO20250920103346', 3, 'paid', 240.00, 3, 3, '2025-09-20 10:33:46', '2025-09-20 10:33:59', NULL);
INSERT INTO `purchase_orders` VALUES (4, 'PO20250920173030', 3, 'paid', 250.00, 3, 3, '2025-09-20 17:30:30', '2025-09-20 17:30:40', NULL);
INSERT INTO `purchase_orders` VALUES (5, 'PO20250921121627', 4, 'approved', 760.00, 3, 3, '2025-09-21 12:16:28', '2025-09-21 12:16:57', NULL);
INSERT INTO `purchase_orders` VALUES (6, 'PO20250921121725', 1, 'pending', 1300.00, 3, NULL, '2025-09-21 12:17:26', NULL, NULL);
INSERT INTO `purchase_orders` VALUES (7, 'PO20250921130418', 5, 'stock', 3137.00, 3, 3, '2025-09-21 13:04:19', '2025-09-21 13:06:38', '一次大进货');

-- ----------------------------
-- Table structure for suppliers
-- ----------------------------
DROP TABLE IF EXISTS `suppliers`;
CREATE TABLE `suppliers`  (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '供应商ID',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '供应商名称',
  `contact_person` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '联系人',
  `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '联系电话',
  `address` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '地址',
  `status` enum('active','inactive') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'active' COMMENT '状态',
  `created_at` timestamp(0) NULL DEFAULT CURRENT_TIMESTAMP(0) COMMENT '创建时间',
  `remark` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '备注',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 6 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '供应商表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of suppliers
-- ----------------------------
INSERT INTO `suppliers` VALUES (1, '可口可乐公司', '王经理', '13700137001', '北京市朝阳区', 'active', '2025-09-19 17:57:30', '饮料供应商');
INSERT INTO `suppliers` VALUES (2, '康师傅食品', '李经理', '13700137002', '天津市开发区', 'active', '2025-09-19 17:57:30', '方便食品供应商');
INSERT INTO `suppliers` VALUES (3, '统一企业', '张经理', '13700137003', '上海市浦东区', 'active', '2025-09-19 17:57:30', '饮料食品供应商');
INSERT INTO `suppliers` VALUES (4, '蒙牛乳业', '赵经理', '13700137004', '内蒙古呼和浩特', 'active', '2025-09-19 17:57:30', '乳制品供应商');
INSERT INTO `suppliers` VALUES (5, '超级无敌供应商', '吴迪哥', '13913913913', '无敌路250号', 'active', '2025-09-21 13:02:57', '确实无敌');

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users`  (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户名',
  `password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '密码',
  `real_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '真实姓名',
  `role` enum('manager','staff') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'staff' COMMENT '角色：manager-店长，staff-店员',
  `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '联系电话',
  `status` enum('active','inactive') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT 'active' COMMENT '状态：active-启用，inactive-禁用',
  `created_at` timestamp(0) NULL DEFAULT CURRENT_TIMESTAMP(0) COMMENT '创建时间',
  `remark` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '备注',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `username`(`username`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 5 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '系统用户表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of users
-- ----------------------------
INSERT INTO `users` VALUES (2, 'staff01', 'e10adc3949ba59abbe56e057f20f883e', '店员01', 'staff', '13800138001', 'active', '2025-09-19 17:57:30', '普通店员');
INSERT INTO `users` VALUES (3, 'admin', 'e10adc3949ba59abbe56e057f20f883e', '管理员', 'manager', NULL, 'active', '2025-09-19 19:11:00', NULL);
INSERT INTO `users` VALUES (4, 'staff', 'e10adc3949ba59abbe56e057f20f883e', NULL, 'staff', NULL, 'active', '2025-09-19 19:11:00', NULL);

SET FOREIGN_KEY_CHECKS = 1;
