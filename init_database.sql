/*
 便利店进销存系统数据库
 
 数据库设计说明：
 1. 系统操作用户管理（店员、店长等）
 2. 客户管理（默认散户，可添加其他客户）
 3. 供应商管理
 4. 商品管理
 5. 采购申请管理（状态：待定、批准、已交付、已付、已取消）
 6. 进货管理（实际进货记录，含生产日期和过期日期）
 7. 出货管理（销售记录，含进价用于计算利润）
 8. 库存管理
 9. 库存盘点管理（盘盈盘亏记录）

 创建时间: 2025-09-18
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 删除现有表（如果存在）
DROP TABLE IF EXISTS `inventory_check_details`;
DROP TABLE IF EXISTS `inventory_checks`;
DROP TABLE IF EXISTS `outgoing_details`;
DROP TABLE IF EXISTS `outgoing_orders`;
DROP TABLE IF EXISTS `incoming_details`;
DROP TABLE IF EXISTS `incoming_orders`;
DROP TABLE IF EXISTS `purchase_details`;
DROP TABLE IF EXISTS `purchase_orders`;
DROP TABLE IF EXISTS `inventory`;
DROP TABLE IF EXISTS `products`;
DROP TABLE IF EXISTS `suppliers`;
DROP TABLE IF EXISTS `customers`;
DROP TABLE IF EXISTS `users`;

-- ----------------------------
-- 系统用户表（店员、店长等）
-- ----------------------------
CREATE TABLE `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `username` varchar(50) NOT NULL COMMENT '用户名',
  `password` varchar(255) NOT NULL COMMENT '密码',
  `real_name` varchar(50) DEFAULT NULL COMMENT '真实姓名',
  `role` enum('manager','staff') NOT NULL DEFAULT 'staff' COMMENT '角色：manager-店长，staff-店员',
  `phone` varchar(20) DEFAULT NULL COMMENT '联系电话',
  `status` enum('active','inactive') DEFAULT 'active' COMMENT '状态：active-启用，inactive-禁用',
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `remark` text COMMENT '备注',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统用户表';

-- ----------------------------
-- 客户表（默认散户，可添加其他客户）
-- ----------------------------
CREATE TABLE `customers` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '客户ID',
  `name` varchar(100) NOT NULL COMMENT '客户姓名/企业名称',
  `phone` varchar(20) DEFAULT NULL COMMENT '联系电话',
  `address` varchar(255) DEFAULT NULL COMMENT '地址',
  `is_default` tinyint(1) DEFAULT 0 COMMENT '是否默认客户（散户）：1-是，0-否',
  `status` enum('active','inactive') DEFAULT 'active' COMMENT '状态',
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `remark` text COMMENT '备注',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='客户表';

-- ----------------------------
-- 供应商表
-- ----------------------------
CREATE TABLE `suppliers` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '供应商ID',
  `name` varchar(100) NOT NULL COMMENT '供应商名称',
  `contact_person` varchar(50) DEFAULT NULL COMMENT '联系人',
  `phone` varchar(20) DEFAULT NULL COMMENT '联系电话',
  `address` varchar(255) DEFAULT NULL COMMENT '地址',
  `status` enum('active','inactive') DEFAULT 'active' COMMENT '状态',
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `remark` text COMMENT '备注',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='供应商表';

-- ----------------------------
-- 商品表
-- ----------------------------
CREATE TABLE `products` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '商品ID',
  `code` varchar(50) DEFAULT NULL COMMENT '商品编码',
  `name` varchar(100) NOT NULL COMMENT '商品名称',
  `category` varchar(50) DEFAULT NULL COMMENT '商品分类',
  `brand` varchar(50) DEFAULT NULL COMMENT '品牌',
  `unit` varchar(10) DEFAULT '件' COMMENT '单位',
  `selling_price` decimal(10, 2) NOT NULL COMMENT '销售价格',
  `status` enum('active','inactive') DEFAULT 'active' COMMENT '状态',
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `remark` text COMMENT '备注',
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品表';

-- ----------------------------
-- 库存表
-- ----------------------------
CREATE TABLE `inventory` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '库存ID',
  `product_id` int(11) NOT NULL COMMENT '商品ID',
  `quantity` int(11) NOT NULL DEFAULT 0 COMMENT '库存数量',
  `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `remark` text COMMENT '备注',
  PRIMARY KEY (`id`),
  UNIQUE KEY `product_id` (`product_id`),
  FOREIGN KEY (`product_id`) REFERENCES `products`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='库存表';

-- ----------------------------
-- 采购申请表
-- ----------------------------
CREATE TABLE `purchase_orders` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '采购申请ID',
  `order_no` varchar(50) NOT NULL COMMENT '采购申请单号',
  `supplier_id` int(11) NOT NULL COMMENT '供应商ID',
  `status` enum('pending','approved','delivered','stock','paid','cancelled') DEFAULT 'pending' COMMENT '状态：pending-待定，approved-批准，delivered-已交付，stock-已入库，paid-已付，cancelled-已取消',
  `total_amount` decimal(10, 2) DEFAULT 0 COMMENT '总金额',
  `apply_user_id` int(11) NOT NULL COMMENT '申请人ID',
  `approve_user_id` int(11) DEFAULT NULL COMMENT '审批人ID',
  `apply_time` timestamp DEFAULT CURRENT_TIMESTAMP COMMENT '申请时间',
  `approve_time` timestamp NULL DEFAULT NULL COMMENT '审批时间',
  `remark` text COMMENT '备注',
  PRIMARY KEY (`id`),
  UNIQUE KEY `order_no` (`order_no`),
  FOREIGN KEY (`supplier_id`) REFERENCES `suppliers`(`id`),
  FOREIGN KEY (`apply_user_id`) REFERENCES `users`(`id`),
  FOREIGN KEY (`approve_user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='采购申请表';

-- ----------------------------
-- 采购申请明细表
-- ----------------------------
CREATE TABLE `purchase_details` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '明细ID',
  `purchase_id` int(11) NOT NULL COMMENT '采购申请ID',
  `product_id` int(11) NOT NULL COMMENT '商品ID',
  `quantity` int(11) NOT NULL COMMENT '申请数量',
  `cost_price` decimal(10, 2) NOT NULL COMMENT '预计进价',
  `amount` decimal(10, 2) NOT NULL COMMENT '小计金额',
  `remark` text COMMENT '备注',
  PRIMARY KEY (`id`),
  FOREIGN KEY (`purchase_id`) REFERENCES `purchase_orders`(`id`),
  FOREIGN KEY (`product_id`) REFERENCES `products`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='采购申请明细表';

-- ----------------------------
-- 进货表（实际进货记录）
-- ----------------------------
CREATE TABLE `incoming_orders` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '进货ID',
  `order_no` varchar(50) NOT NULL COMMENT '进货单号',
  `purchase_id` int(11) DEFAULT NULL COMMENT '关联采购申请ID',
  `supplier_id` int(11) NOT NULL COMMENT '供应商ID',
  `total_amount` decimal(10, 2) DEFAULT 0 COMMENT '总金额',
  `incoming_date` date NOT NULL COMMENT '进货日期',
  `user_id` int(11) NOT NULL COMMENT '操作人ID',
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `remark` text COMMENT '备注',
  PRIMARY KEY (`id`),
  UNIQUE KEY `order_no` (`order_no`),
  FOREIGN KEY (`purchase_id`) REFERENCES `purchase_orders`(`id`),
  FOREIGN KEY (`supplier_id`) REFERENCES `suppliers`(`id`),
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='进货表';

-- ----------------------------
-- 进货明细表
-- ----------------------------
CREATE TABLE `incoming_details` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '明细ID',
  `incoming_id` int(11) NOT NULL COMMENT '进货ID',
  `product_id` int(11) NOT NULL COMMENT '商品ID',
  `quantity` int(11) NOT NULL COMMENT '进货数量',
  `cost_price` decimal(10, 2) NOT NULL COMMENT '进价',
  `amount` decimal(10, 2) NOT NULL COMMENT '小计金额',
  `production_date` date DEFAULT NULL COMMENT '生产日期',
  `expiry_date` date DEFAULT NULL COMMENT '过期日期',
  `batch_no` varchar(50) DEFAULT NULL COMMENT '批次号',
  `remark` text COMMENT '备注',
  PRIMARY KEY (`id`),
  FOREIGN KEY (`incoming_id`) REFERENCES `incoming_orders`(`id`),
  FOREIGN KEY (`product_id`) REFERENCES `products`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='进货明细表';

-- ----------------------------
-- 出货表（销售记录）
-- ----------------------------
CREATE TABLE `outgoing_orders` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '出货ID',
  `order_no` varchar(50) NOT NULL COMMENT '出货单号',
  `customer_id` int(11) DEFAULT NULL COMMENT '客户ID',
  `total_amount` decimal(10, 2) DEFAULT 0 COMMENT '总销售金额',
  `total_cost` decimal(10, 2) DEFAULT 0 COMMENT '总成本金额',
  `profit` decimal(10, 2) DEFAULT 0 COMMENT '利润',
  `sale_date` date NOT NULL COMMENT '销售日期',
  `user_id` int(11) NOT NULL COMMENT '操作人ID',
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `remark` text COMMENT '备注',
  PRIMARY KEY (`id`),
  UNIQUE KEY `order_no` (`order_no`),
  FOREIGN KEY (`customer_id`) REFERENCES `customers`(`id`),
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='出货表';

-- ----------------------------
-- 出货明细表
-- ----------------------------
CREATE TABLE `outgoing_details` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '明细ID',
  `outgoing_id` int(11) NOT NULL COMMENT '出货ID',
  `product_id` int(11) NOT NULL COMMENT '商品ID',
  `quantity` int(11) NOT NULL COMMENT '出货数量',
  `selling_price` decimal(10, 2) NOT NULL COMMENT '销售价格',
  `cost_price` decimal(10, 2) NOT NULL COMMENT '成本价格（进价）',
  `amount` decimal(10, 2) NOT NULL COMMENT '销售小计',
  `cost_amount` decimal(10, 2) NOT NULL COMMENT '成本小计',
  `profit` decimal(10, 2) NOT NULL COMMENT '利润',
  `remark` text COMMENT '备注',
  PRIMARY KEY (`id`),
  FOREIGN KEY (`outgoing_id`) REFERENCES `outgoing_orders`(`id`),
  FOREIGN KEY (`product_id`) REFERENCES `products`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='出货明细表';

-- ----------------------------
-- 库存盘点表
-- ----------------------------
CREATE TABLE `inventory_checks` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '盘点ID',
  `check_no` varchar(50) NOT NULL COMMENT '盘点单号',
  `check_date` date NOT NULL COMMENT '盘点日期',
  `status` enum('ongoing','completed') DEFAULT 'ongoing' COMMENT '状态：ongoing-进行中，completed-已完成',
  `total_difference` int(11) DEFAULT 0 COMMENT '总差异数量（正数盘盈，负数盘亏）',
  `user_id` int(11) NOT NULL COMMENT '盘点人ID',
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `remark` text COMMENT '备注',
  PRIMARY KEY (`id`),
  UNIQUE KEY `check_no` (`check_no`),
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='库存盘点表';

-- ----------------------------
-- 库存盘点明细表
-- ----------------------------
CREATE TABLE `inventory_check_details` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '明细ID',
  `check_id` int(11) NOT NULL COMMENT '盘点ID',
  `product_id` int(11) NOT NULL COMMENT '商品ID',
  `book_quantity` int(11) NOT NULL COMMENT '账面数量',
  `actual_quantity` int(11) NOT NULL COMMENT '实际数量',
  `difference` int(11) NOT NULL COMMENT '差异数量（实际-账面）',
  `difference_type` enum('normal','gain','loss') NOT NULL COMMENT '差异类型：normal-正常，gain-盘盈，loss-盘亏',
  `handled` tinyint(1) DEFAULT 0 COMMENT '是否已处理：1-是，0-否',
  `remark` text COMMENT '备注',
  PRIMARY KEY (`id`),
  FOREIGN KEY (`check_id`) REFERENCES `inventory_checks`(`id`),
  FOREIGN KEY (`product_id`) REFERENCES `products`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='库存盘点明细表';

-- ----------------------------
-- 插入初始数据
-- ----------------------------

-- 插入系统用户
INSERT INTO `users` (`username`, `password`, `real_name`, `role`, `phone`, `remark`) VALUES
('admin', 'e10adc3949ba59abbe56e057f20f883e', '系统管理员', 'manager', '13800138000', '系统初始管理员'),
('staff01', 'e10adc3949ba59abbe56e057f20f883e', '店员01', 'staff', '13800138001', '普通店员');

-- 插入默认客户（散户）
INSERT INTO `customers` (`name`, `phone`, `address`, `is_default`, `remark`) VALUES
('散户', NULL, NULL, 1, '默认散户客户'),
('张三', '13900139001', '某某小区1号楼', 0, '老客户'),
('李四', '13900139002', '某某小区2号楼', 0, '会员客户');

-- 插入供应商
INSERT INTO `suppliers` (`name`, `contact_person`, `phone`, `address`, `remark`) VALUES
('可口可乐公司', '王经理', '13700137001', '北京市朝阳区', '饮料供应商'),
('康师傅食品', '李经理', '13700137002', '天津市开发区', '方便食品供应商'),
('统一企业', '张经理', '13700137003', '上海市浦东区', '饮料食品供应商'),
('蒙牛乳业', '赵经理', '13700137004', '内蒙古呼和浩特', '乳制品供应商');

-- 插入商品
INSERT INTO `products` (`code`, `name`, `category`, `brand`, `unit`, `selling_price`, `remark`) VALUES
('P001', '可口可乐330ml', '饮料', '可口可乐', '瓶', 3.50, '经典可乐'),
('P002', '百事可乐330ml', '饮料', '百事', '瓶', 3.50, '百事可乐'),
('P003', '康师傅红烧牛肉面', '方便食品', '康师傅', '包', 4.00, '经典口味'),
('P004', '统一冰红茶500ml', '饮料', '统一', '瓶', 3.00, '冰红茶'),
('P005', '农夫山泉550ml', '饮料', '农夫山泉', '瓶', 2.00, '天然水'),
('P006', '士力架花生夹心巧克力', '零食', '士力架', '条', 5.00, '补充能量'),
('P007', '乐事薯片黄瓜味', '零食', '乐事', '包', 6.00, '黄瓜味薯片'),
('P008', '伊利纯牛奶250ml', '乳制品', '伊利', '盒', 4.50, '纯牛奶'),
('P009', '旺仔牛奶245ml', '乳制品', '旺旺', '罐', 3.80, '复原乳'),
('P010', '奥利奥饼干', '零食', '奥利奥', '包', 7.00, '夹心饼干');

-- 初始化库存（所有商品库存为0）
INSERT INTO `inventory` (`product_id`, `quantity`, `remark`) 
SELECT `id`, 0, '初始库存' FROM `products`;

SET FOREIGN_KEY_CHECKS = 1;
