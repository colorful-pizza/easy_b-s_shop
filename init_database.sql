/*
 Navicat MySQL Data Transfer

 Source Server         : localhost_3306
 Source Server Type    : MySQL
 Source Server Version : 50726
 Source Host           : localhost:3306
 Source Schema         : shop

 Target Server Type    : MySQL
 Target Server Version : 50726
 File Encoding         : 65001

 Date: 04/09/2025 13:47:40
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for products
-- ----------------------------
DROP TABLE IF EXISTS `products`;
CREATE TABLE `products`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `selling_price` decimal(10, 2) NOT NULL,
  `cost_price` decimal(10, 2) NOT NULL,
  `stock` int(11) NOT NULL DEFAULT 0,
  `image_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = MyISAM AUTO_INCREMENT = 11 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of products
-- ----------------------------
INSERT INTO `products` VALUES (1, '可口可乐', 3.50, 2.00, 100, 'https://image2.suning.cn/b2c/catentries/000000000155267597_3_800x800.jpg');
INSERT INTO `products` VALUES (2, '百事可乐', 3.50, 1.80, 150, 'https://ts1.tc.mm.bing.net/th/id/OIP-C.NyZRGrlL_134noy4VduHOwHaHa?rs=1&pid=ImgDetMain&o=7&rm=3');
INSERT INTO `products` VALUES (3, '康师傅方便面', 4.00, 2.50, 120, 'https://ts3.tc.mm.bing.net/th/id/OIP-C.dJ4IUc-Dy0_Tb_ay6g9TYAHaHV?rs=1&pid=ImgDetMain&o=7&rm=3');
INSERT INTO `products` VALUES (4, '统一冰红茶', 3.00, 1.50, 85, 'https://ts3.tc.mm.bing.net/th/id/OIP-C.Tiit74vaOf0ziGdwnw-qjQHaHa?rs=1&pid=ImgDetMain&o=7&rm=3');
INSERT INTO `products` VALUES (5, '农夫山泉矿泉水', 2.00, 0.80, 200, 'https://ts1.tc.mm.bing.net/th/id/OIP-C.mLXqLw7FsO-RXtoAOhU40wHaHa?rs=1&pid=ImgDetMain&o=7&rm=3');
INSERT INTO `products` VALUES (6, '士力架巧克力', 5.00, 3.00, 50, 'https://m.360buyimg.com/mobilecms/s750x750_jfs/t1/101629/32/15320/122795/5e7064afEde14ab46/de7ba84994f1c91f.jpg!q80.dpg');
INSERT INTO `products` VALUES (7, '乐事薯片', 6.00, 3.50, 60, 'https://ts2.tc.mm.bing.net/th/id/OIP-C.m7Z7bSWHnJ2VmIvxp2J-JgHaHa?rs=1&pid=ImgDetMain&o=7&rm=3');
INSERT INTO `products` VALUES (8, '伊利纯牛奶', 4.50, 3.00, 110, 'https://ts4.tc.mm.bing.net/th/id/OIP-C.1f4T9-2cuUlUAg0UppvaMQAAAA?rs=1&pid=ImgDetMain&o=7&rm=3');
INSERT INTO `products` VALUES (9, '旺仔牛奶', 3.80, 2.20, 95, 'https://ts1.tc.mm.bing.net/th/id/OIP-C.RC81ndwSNHzVLjDKF5AzdAHaHa?rs=1&pid=ImgDetMain&o=7&rm=3');
INSERT INTO `products` VALUES (10, '奥利奥饼干', 7.00, 4.50, 50, 'https://ts3.tc.mm.bing.net/th/id/OIP-C.bXOPSnkUrqOfHibzrXjU7wHaHa?rs=1&pid=ImgDetMain&o=7&rm=3');

-- ----------------------------
-- Table structure for purchase_details
-- ----------------------------
DROP TABLE IF EXISTS `purchase_details`;
CREATE TABLE `purchase_details`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `order_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '关联的采购单号',
  `product_id` int(11) NOT NULL COMMENT '商品ID',
  `quantity` int(11) NOT NULL COMMENT '采购数量（正数）',
  `amount` decimal(10, 2) NOT NULL COMMENT '采购金额（quantity*商品cost_price，存储为负值）',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `order_no`(`order_no`) USING BTREE,
  INDEX `product_id`(`product_id`) USING BTREE
) ENGINE = MyISAM AUTO_INCREMENT = 12 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of purchase_details
-- ----------------------------
INSERT INTO `purchase_details` VALUES (1, 'po1', 1, 100, 200.00);
INSERT INTO `purchase_details` VALUES (2, 'po1', 2, 80, 144.00);
INSERT INTO `purchase_details` VALUES (3, 'po1', 3, 120, 300.00);
INSERT INTO `purchase_details` VALUES (4, 'po2', 4, 90, 135.00);
INSERT INTO `purchase_details` VALUES (5, 'po2', 5, 200, 160.00);
INSERT INTO `purchase_details` VALUES (6, 'po2', 6, 60, 180.00);
INSERT INTO `purchase_details` VALUES (7, 'po3', 7, 70, 245.00);
INSERT INTO `purchase_details` VALUES (8, 'po3', 8, 110, 330.00);
INSERT INTO `purchase_details` VALUES (9, 'po3', 9, 95, 209.00);
INSERT INTO `purchase_details` VALUES (10, 'po3', 10, 50, 225.00);
INSERT INTO `purchase_details` VALUES (11, 'PO20250904134409', 2, 75, 135.00);

-- ----------------------------
-- Table structure for purchase_orders
-- ----------------------------
DROP TABLE IF EXISTS `purchase_orders`;
CREATE TABLE `purchase_orders`  (
  `order_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '采购单号（如PO20230903001）',
  `total_amount` decimal(10, 2) NOT NULL COMMENT '订单总金额（负数，表示支出）',
  `order_time` datetime(0) NOT NULL COMMENT '下单时间',
  `user_id` int(11) NOT NULL COMMENT '操作人ID',
  PRIMARY KEY (`order_no`) USING BTREE,
  INDEX `user_id`(`user_id`) USING BTREE
) ENGINE = MyISAM CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of purchase_orders
-- ----------------------------
INSERT INTO `purchase_orders` VALUES ('po1', 644.00, '2025-09-03 17:07:26', 1);
INSERT INTO `purchase_orders` VALUES ('po2', 475.00, '2025-09-03 17:08:12', 2);
INSERT INTO `purchase_orders` VALUES ('po3', 325.00, '2025-09-03 17:08:42', 1);
INSERT INTO `purchase_orders` VALUES ('PO20250904134409', 135.00, '2025-09-04 13:44:09', 1);

-- ----------------------------
-- Table structure for sales_details
-- ----------------------------
DROP TABLE IF EXISTS `sales_details`;
CREATE TABLE `sales_details`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `order_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '关联的销售单号',
  `product_id` int(11) NOT NULL COMMENT '商品ID',
  `quantity` int(11) NOT NULL COMMENT '销售数量（正数）',
  `amount` decimal(10, 2) NOT NULL COMMENT '销售金额（quantity*商品selling_price，存储为正值）',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `order_no`(`order_no`) USING BTREE,
  INDEX `product_id`(`product_id`) USING BTREE
) ENGINE = MyISAM AUTO_INCREMENT = 6 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of sales_details
-- ----------------------------
INSERT INTO `sales_details` VALUES (1, 'SO20250904133550', 4, 2, 6.00);
INSERT INTO `sales_details` VALUES (2, 'SO20250904133656', 4, 3, 9.00);
INSERT INTO `sales_details` VALUES (3, 'SO20250904133656', 2, 5, 17.50);
INSERT INTO `sales_details` VALUES (4, 'SO20250904134352', 6, 10, 50.00);
INSERT INTO `sales_details` VALUES (5, 'SO20250904134352', 7, 10, 60.00);

-- ----------------------------
-- Table structure for sales_orders
-- ----------------------------
DROP TABLE IF EXISTS `sales_orders`;
CREATE TABLE `sales_orders`  (
  `order_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL COMMENT '销售单号（如SO20230903001）',
  `customer_id` int(11) NULL DEFAULT NULL COMMENT '客户ID（如有客户表）',
  `total_amount` decimal(10, 2) NOT NULL COMMENT '订单总金额（正数，表示收入）',
  `order_time` datetime(0) NOT NULL COMMENT '下单时间',
  `user_id` int(11) NOT NULL COMMENT '操作人ID',
  PRIMARY KEY (`order_no`) USING BTREE,
  INDEX `user_id`(`user_id`) USING BTREE
) ENGINE = MyISAM CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of sales_orders
-- ----------------------------
INSERT INTO `sales_orders` VALUES ('SO20250904133550', NULL, 6.00, '2025-09-04 13:35:50', 1);
INSERT INTO `sales_orders` VALUES ('SO20250904133656', NULL, 26.50, '2025-09-04 13:36:57', 1);
INSERT INTO `sales_orders` VALUES ('SO20250904134352', NULL, 110.00, '2025-09-04 13:43:52', 1);

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `role` enum('manager','staff') CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `username`(`username`) USING BTREE
) ENGINE = MyISAM AUTO_INCREMENT = 3 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_bin ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of users
-- ----------------------------
INSERT INTO `users` VALUES (1, 'manager', '1d0258c2440a8d19e716292b231e3190', 'manager');
INSERT INTO `users` VALUES (2, 'staff', 'e10adc3949ba59abbe56e057f20f883e', 'staff');

SET FOREIGN_KEY_CHECKS = 1;
