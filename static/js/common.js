// 便利店进销存系统 - 公共JavaScript文件

// 用户权限配置
const menuConfig = {
  manager: [
    { id: "sales", name: "商品销售", icon: "💰", url: "/sales" },
    { id: "inventory", name: "库存查询", icon: "📦", url: "/inventory" },
    { id: "products", name: "商品管理", icon: "🛍️", url: "/products" },
    { id: "purchase", name: "采购管理", icon: "📋", url: "/purchase" },
    { id: "payables", name: "应付结算", icon: "💳", url: "/payables" },
    { id: "incoming", name: "进货管理", icon: "📥", url: "/incoming" },
    { id: "customers", name: "客户管理", icon: "👥", url: "/customers" },
    { id: "suppliers", name: "供应商管理", icon: "🏢", url: "/suppliers" },
    { id: "stockcheck", name: "库存盘点", icon: "📊", url: "/stockcheck" },
    { id: "reports", name: "报表分析", icon: "📈", url: "/reports" },
  ],
  staff: [
    { id: "sales", name: "商品销售", icon: "💰", url: "/sales" },
    { id: "inventory", name: "库存查询", icon: "📦", url: "/inventory" },
    { id: "incoming", name: "进货管理", icon: "📥", url: "/incoming" },
    { id: "stockcheck", name: "库存盘点", icon: "📊", url: "/stockcheck" },
  ],
};

// 检查登录状态
function checkLogin() {
  const isLoggedIn = localStorage.getItem("isLoggedIn");
  const userStr = localStorage.getItem("user");

  if (
    !isLoggedIn ||
    isLoggedIn !== "true" ||
    !userStr ||
    userStr === "undefined"
  ) {
    window.location.href = "/login";
    return null;
  }

  try {
    return JSON.parse(userStr);
  } catch (error) {
    console.error("解析用户信息失败:", error);
    localStorage.removeItem("user");
    localStorage.removeItem("isLoggedIn");
    window.location.href = "/login";
    return null;
  }
}

// 生成菜单
function generateMenu(role, currentPage = "") {
  const menuList = document.getElementById("menuList");
  if (!menuList) return;

  const menus = menuConfig[role] || [];

  menuList.innerHTML = menus
    .map(
      (menu) => `
        <li class="menu-item ${menu.id === currentPage ? "active" : ""}">
            <a href="${menu.url}" class="menu-link">
                <span class="menu-icon">${menu.icon}</span>
                <span class="menu-text">${menu.name}</span>
            </a>
        </li>
    `
    )
    .join("");
}

// 初始化公共页面功能
function initCommonPage(currentPage = "") {
  const user = checkLogin();
  if (!user) return;

  // 显示用户信息
  const userInfoElement = document.getElementById("userInfo");
  if (userInfoElement) {
    userInfoElement.textContent = `${user.username} (${
      user.role === "manager" ? "管理员" : "店员"
    })`;
  }

  // 生成菜单
  generateMenu(user.role, currentPage);

  // 绑定退出登录事件
  const logoutBtn = document.getElementById("logoutBtn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", logout);
  }
}

// 退出登录
async function logout() {
  try {
    await fetch("/api/auth/logout", { method: "POST" });
  } catch (error) {
    console.error("退出登录失败:", error);
  }

  localStorage.removeItem("user");
  localStorage.removeItem("isLoggedIn");
  window.location.href = "/login";
}

// 加载仪表盘数据（仅用于首页）
async function loadDashboardData() {
  try {
    const response = await fetch("/api/reports/dashboard");
    const data = await response.json();

    if (data.success) {
      const dashboardData = data.data;

      const todaySalesElement = document.getElementById("todaySales");
      if (todaySalesElement) {
        todaySalesElement.textContent = `¥${dashboardData.today_sales.total_sales.toFixed(
          2
        )}`;
      }

      const stockAlertsElement = document.getElementById("stockAlerts");
      if (stockAlertsElement) {
        stockAlertsElement.textContent =
          dashboardData.inventory_stats.zero_stock +
          dashboardData.inventory_stats.low_stock;
      }

      const monthlyProfitElement = document.getElementById("monthlyProfit");
      if (monthlyProfitElement) {
        monthlyProfitElement.textContent = `¥${dashboardData.this_month_sales.total_profit.toFixed(
          2
        )}`;
      }

      // 待处理订单数
      const pendingOrdersElement = document.getElementById("pendingOrders");
      if (
        pendingOrdersElement &&
        typeof dashboardData.pending_orders === "number"
      ) {
        pendingOrdersElement.textContent = `${dashboardData.pending_orders}`;
      }
    }
  } catch (error) {
    console.error("加载仪表盘数据失败:", error);
  }
}

// 工具函数：格式化日期
function formatDate(date) {
  if (!date) return "";
  const d = new Date(date);
  return d.toISOString().split("T")[0];
}

// 工具函数：格式化金额
function formatMoney(amount) {
  return `¥${parseFloat(amount || 0).toFixed(2)}`;
}

// 工具函数：显示加载状态
function showLoading(element) {
  if (element) {
    element.innerHTML = '<div class="loading"></div>';
  }
}

// 工具函数：显示错误信息
function showError(message, container) {
  if (container) {
    container.innerHTML = `<div class="error-message">${message}</div>`;
  }
}

// 工具函数：显示成功信息
function showSuccess(message, container) {
  if (container) {
    container.innerHTML = `<div class="success-message">${message}</div>`;
  }
}
