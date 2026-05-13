// ===== 智董籌碼選股站 - 前端互動 =====

document.addEventListener('DOMContentLoaded', function() {
    // 表格排序功能
    initTableSort();

    // 自動刷新提示
    showUpdateTime();
});

// 表格點擊表頭排序
function initTableSort() {
    const tables = document.querySelectorAll('.data-table');
    tables.forEach(table => {
        const headers = table.querySelectorAll('thead th');
        headers.forEach((header, index) => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => sortTable(table, index));
        });
    });
}

function sortTable(table, colIndex) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));

    // 判斷排序方向
    const currentDir = table.getAttribute('data-sort-dir') === 'asc' ? 'desc' : 'asc';
    table.setAttribute('data-sort-dir', currentDir);

    rows.sort((a, b) => {
        const aVal = getCellValue(a, colIndex);
        const bVal = getCellValue(b, colIndex);

        if (!isNaN(aVal) && !isNaN(bVal)) {
            return currentDir === 'asc' ? aVal - bVal : bVal - aVal;
        }
        return currentDir === 'asc' 
            ? String(aVal).localeCompare(String(bVal))
            : String(bVal).localeCompare(String(aVal));
    });

    rows.forEach(row => tbody.appendChild(row));
}

function getCellValue(row, index) {
    const cell = row.cells[index];
    if (!cell) return '';
    let text = cell.textContent.trim();
    // 移除 % 和 , 轉數字
    text = text.replace(/,/g, '').replace(/%/g, '');
    const num = parseFloat(text);
    return isNaN(num) ? text : num;
}

// 顯示資料更新時間
function showUpdateTime() {
    const footer = document.querySelector('.footer');
    if (footer) {
        const now = new Date();
        const timeStr = now.toLocaleString('zh-TW', {
            year: 'numeric', month: '2-digit', day: '2-digit',
            hour: '2-digit', minute: '2-digit'
        });
        // 頁面載入時間（非資料時間，資料時間在 footer 中）
        console.log('頁面載入時間:', timeStr);
    }
}

// 個股頁面：切換時間區間
function changeTimeRange(days) {
    // 預留給未來擴展：切換 K 線時間區間
    console.log('切換時間區間:', days, '天');
}

// 匯出 CSV
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;

    let csv = [];
    const rows = table.querySelectorAll('tr');

    rows.forEach(row => {
        let cols = row.querySelectorAll('td, th');
        let rowData = [];
        cols.forEach(col => rowData.push(col.textContent.trim()));
        csv.push(rowData.join(','));
    });

    const csvContent = '\uFEFF' + csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
}
