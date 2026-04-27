#!/usr/bin/env python3
"""
解析每日情报 md 文件并生成网页
"""
import re
import os
from pathlib import Path

# 来源名称到 URL 的映射
SOURCE_URL_MAP = {
    "36氪": "https://36kr.com",
    "虎嗅/36氪": "https://36kr.com",
    "腾讯新闻": "https://news.qq.com",
    "新闻腾讯": "https://news.qq.com",
    "新浪财经": "https://finance.sina.com.cn",
    "新浪": "https://sina.com.cn",
    "知乎": "https://zhihu.com",
    "CSDN": "https://csdn.net",
    "CSDN/AI周报": "https://csdn.net",
    "AI周报": "https://ai.zhiding.cn",
    "AI资讯站": "https://ai.xianhuo.com",
    "IT之家": "https://ithome.com",
    "搜狐/SOHU": "https://sohu.com",
    "SOHU": "https://sohu.com",
    "搜狐": "https://sohu.com",
    "商业周刊": "https://businessweekly.com",
    "新华网": "https://xinhuanet.com",
    "网信办": "http://www.cac.gov.cn",
    "OpenClaw官网": "https://openclaw.cn",
    "行业盘点": "https://example.com",
    "QuestMobile": "https://questmobile.com",
    "中国日报": "https://chinadaily.com.cn",
    "winzheng/36kr": "https://36kr.com",
    "21经济/腾讯云": "https://21jingji.com",
    "腾讯云": "https://cloud.tencent.com",
    "商业周刊": "https://businessweekly.com",
    "cn-sec": "https://cn-sec.com",
    "aiproducthub": "https://aiproducthub.com",
    "技术栈/juejin": "https://juejin.cn",
    "juejin": "https://juejin.cn",
    "多个资讯源": "https://36kr.com",
}

def get_source_url(source):
    """获取来源对应的 URL"""
    # 清理来源名称（去掉括号内容）
    clean_source = re.sub(r'\([^)]*\)', '', source).strip()
    # 尝试直接匹配
    if clean_source in SOURCE_URL_MAP:
        return SOURCE_URL_MAP[clean_source]
    # 尝试部分匹配
    for key in SOURCE_URL_MAP:
        if key in clean_source:
            return SOURCE_URL_MAP[key]
    # 默认返回搜索引擎搜索
    return f"https://www.google.com/search?q={clean_source}+AI+新闻"

def parse_md_file(filepath):
    """解析单个每日情报 md 文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取日期 - 从文件名获取（这是情报归属日期）
    filename = filepath.name
    date_match = re.search(r'每日情报_(\d{4}-\d{2}-\d{2})', filename)
    file_date = date_match.group(1) if date_match else ''

    # 提取收集时间
    time_match = re.search(r'\*\*收集时间\*\*：(.+)', content)
    collect_time = time_match.group(1) if time_match else ''

    # 提取情报纪要
    summary_match = re.search(r'## 📋 情报纪要\s*\n+(.+?)(?=---|\n##|$)', content, re.DOTALL)
    summary = summary_match.group(1).strip() if summary_match else ''

    # 提取各类别情报
    items = []

    # 匹配表格行
    table_pattern = r'\|\s*时间\s*\|\s*类别\s*\|\s*事件\s*\|\s*关键信息\s*\|\s*来源\s*\|\s*备注\s*\|[\s\n]*\|[-:\s|]+\|[\s\n]*((?:\|.+\|\n?)+)'
    sections = re.split(r'### \w+、', content)

    for section in sections[1:]:  # 跳过第一个（通常是空内容）
        # 确定类别
        if '技术突破' in section[:20]:
            category = '技术突破'
        elif '产品动态' in section[:20]:
            category = '产品动态'
        elif '生态变化' in section[:20]:
            category = '生态变化'
        elif 'KOL观点' in section[:20]:
            category = 'KOL观点'
        elif '监管政策' in section[:20]:
            category = '监管政策'
        elif '用户数据' in section[:20]:
            category = '用户数据'
        else:
            continue

        # 提取表格内容
        rows = re.findall(r'\|\s*(\d{4}-\d{2}-\d{2}(?:-\d{2})?)\s*\|\s*[^|]+\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|', section)

        for row in rows:
            item_date, event, info, source, note = row
            source_clean = source.strip()
            items.append({
                'type': category,
                'date': file_date,  # 使用文件日期作为归属日期
                'event_date': item_date.strip(),  # 保留事件原始发生日期
                'title': event.strip(),
                'info': info.strip(),
                'source': source_clean,
                'source_url': get_source_url(source_clean),
                'note': note.strip()
            })

    return {
        'date': file_date,
        'collect_time': collect_time,
        'summary': summary,
        'items': items
    }

def main():
    # 源文件夹 - 相对于脚本所在目录的 source 文件夹
    script_dir = Path(__file__).parent
    source_dir = script_dir / 'source'

    # 获取所有每日情报文件
    md_files = sorted(source_dir.glob('每日情报_*.md'), reverse=True)

    print(f"找到 {len(md_files)} 个情报文件")

    all_data = []
    for f in md_files:
        print(f"解析: {f.name}")
        data = parse_md_file(f)
        all_data.append(data)
        print(f"  - 日期: {data['date']}, 条目: {len(data['items'])}")

    # 生成 HTML
    html = generate_html(all_data)

    # 输出到 deploy 文件夹
    output_dir = script_dir / 'deploy'
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / 'index.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n生成完成: {output_path}")

def generate_html(data_list):
    """生成完整 HTML 页面"""
    items_json = []
    for d in data_list:
        for item in d['items']:
            items_json.append({
                'type': item['type'],
                'title': item['title'],
                'date': item['date'],
                'info': item['info'],
                'source': item['source'],
                'source_url': item.get('source_url', ''),
                'note': item['note']
            })

    dates_json = [d['date'] for d in data_list]
    summaries_json = {d['date']: d['summary'] for d in data_list}

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AgentRadar - AI 每日情报</title>
    <style>
        :root {{
            --primary: #2563eb;
            --bg: #f8fafc;
            --card: #ffffff;
            --text: #1e293b;
            --text-light: #64748b;
            --border: #e2e8f0;
            --tech: #8b5cf6;
            --product: #10b981;
            --eco: #f59e0b;
            --kol: #ef4444;
            --policy: #6366f1;
            --data: #ec4899;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            min-height: 100vh;
        }}

        /* 头部 */
        header {{
            background: linear-gradient(135deg, #1e40af 0%, #2563eb 100%);
            color: white;
            padding: 24px 16px;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}

        header h1 {{
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 4px;
        }}

        header p {{
            font-size: 13px;
            opacity: 0.85;
        }}

        /* 日期导航 */
        .date-nav {{
            display: flex;
            gap: 8px;
            overflow-x: auto;
            padding: 12px 16px;
            background: white;
            border-bottom: 1px solid var(--border);
            scrollbar-width: none;
            -ms-overflow-style: none;
        }}

        .date-nav::-webkit-scrollbar {{ display: none; }}

        .date-btn {{
            flex-shrink: 0;
            padding: 8px 14px;
            border: 1px solid var(--border);
            border-radius: 20px;
            background: white;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
            white-space: nowrap;
        }}

        .date-btn:hover {{ border-color: var(--primary); color: var(--primary); }}
        .date-btn.active {{
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }}

        /* 分类筛选 */
        .filter-bar {{
            display: flex;
            gap: 8px;
            padding: 12px 16px;
            background: white;
            border-bottom: 1px solid var(--border);
            overflow-x: auto;
            scrollbar-width: none;
        }}

        .filter-bar::-webkit-scrollbar {{ display: none; }}

        .filter-btn {{
            flex-shrink: 0;
            padding: 6px 12px;
            border-radius: 16px;
            font-size: 12px;
            cursor: pointer;
            border: 1px solid var(--border);
            background: white;
            transition: all 0.2s;
        }}

        .filter-btn.active {{ color: white; border-color: transparent; }}
        .filter-btn[data-type="all"].active {{ background: var(--text); }}
        .filter-btn[data-type="技术突破"].active {{ background: var(--tech); }}
        .filter-btn[data-type="产品动态"].active {{ background: var(--product); }}
        .filter-btn[data-type="生态变化"].active {{ background: var(--eco); }}
        .filter-btn[data-type="KOL观点"].active {{ background: var(--kol); }}
        .filter-btn[data-type="监管政策"].active {{ background: var(--policy); }}
        .filter-btn[data-type="用户数据"].active {{ background: var(--data); }}

        /* 内容区域 */
        .content {{
            padding: 16px;
            max-width: 900px;
            margin: 0 auto;
        }}

        /* 日期分组 */
        .date-group {{
            margin-bottom: 32px;
        }}

        .date-header {{
            font-size: 14px;
            font-weight: 600;
            color: var(--text-light);
            margin-bottom: 12px;
            padding-left: 4px;
            border-left: 3px solid var(--primary);
        }}

        /* 情报卡片 */
        .card {{
            background: var(--card);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            border: 1px solid var(--border);
            cursor: pointer;
            transition: all 0.2s;
        }}

        .card:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.12);
            transform: translateY(-1px);
        }}

        .card-header {{
            display: flex;
            align-items: flex-start;
            gap: 10px;
            margin-bottom: 8px;
            flex-wrap: wrap;
        }}

        .card-type {{
            flex-shrink: 0;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 500;
            color: white;
        }}

        .card-type.技术突破 {{ background: var(--tech); }}
        .card-type.产品动态 {{ background: var(--product); }}
        .card-type.生态变化 {{ background: var(--eco); }}
        .card-type.KOL观点 {{ background: var(--kol); }}
        .card-type.监管政策 {{ background: var(--policy); }}
        .card-type.用户数据 {{ background: var(--data); }}

        .card-title {{
            font-size: 15px;
            font-weight: 600;
            flex: 1;
            min-width: 200px;
        }}

        .card-date {{
            font-size: 12px;
            color: var(--text-light);
            flex-shrink: 0;
        }}

        .card-info {{
            font-size: 14px;
            color: var(--text);
            margin-bottom: 8px;
            line-height: 1.5;
        }}

        .card-footer {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
            color: var(--text-light);
            flex-wrap: wrap;
            gap: 8px;
        }}

.card-source {{ background: #f1f5f9; padding: 2px 8px; border-radius: 4px; text-decoration: none; color: inherit; cursor: pointer; }}
        .card-source:hover {{ background: #e2e8f0; }}
        .card-note {{ font-style: italic; }}

        /* 展开详情 */
        .card-detail {{
            display: none;
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px dashed var(--border);
            font-size: 13px;
            color: var(--text-light);
        }}

        .card-detail p {{ margin-bottom: 6px; }}

        /* 摘要区 */
        .summary {{
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            border-radius: 12px;
            padding: 14px 16px;
            margin-bottom: 12px;
            border-left: 4px solid var(--eco);
        }}

        .summary-title {{
            font-size: 12px;
            font-weight: 600;
            color: #92400e;
            margin-bottom: 6px;
        }}

        .summary-text {{
            font-size: 14px;
            color: #78350f;
            line-height: 1.6;
        }}

        /* 统计 */
        .stats {{
            display: flex;
            gap: 12px;
            padding: 12px 16px;
            background: white;
            border-bottom: 1px solid var(--border);
            overflow-x: auto;
            font-size: 12px;
        }}

        .stat-item {{
            flex-shrink: 0;
            padding: 6px 12px;
            background: var(--bg);
            border-radius: 16px;
        }}

        .stat-label {{ color: var(--text-light); }}
        .stat-value {{ font-weight: 600; color: var(--primary); margin-left: 4px; }}

        /* 空状态 */
        .empty {{
            text-align: center;
            padding: 48px 16px;
            color: var(--text-light);
        }}

        .empty-icon {{ font-size: 48px; margin-bottom: 12px; }}

        /* 底部 */
        footer {{
            text-align: center;
            padding: 24px;
            color: var(--text-light);
            font-size: 12px;
        }}

        /* 移动端优化 */
        @media (max-width: 640px) {{
            header {{ padding: 16px; }}
            header h1 {{ font-size: 18px; }}
            .content {{ padding: 12px; }}
            .card {{ padding: 14px; }}
            .card-title {{ font-size: 14px; }}
        }}

        /* 密码保护页面 */
        #password-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #1e40af 0%, #2563eb 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
        }}

        #password-overlay.hidden {{
            display: none;
        }}

        .password-box {{
            background: white;
            padding: 40px;
            border-radius: 16px;
            text-align: center;
            max-width: 360px;
            width: 90%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}

        .password-box h2 {{
            font-size: 24px;
            margin-bottom: 8px;
            color: #1e293b;
        }}

        .password-box p {{
            font-size: 14px;
            color: #64748b;
            margin-bottom: 24px;
        }}

        .password-box input[type="password"] {{
            width: 100%;
            padding: 14px 16px;
            border: 2px solid #e2e8f0;
            border-radius: 10px;
            font-size: 16px;
            text-align: center;
            margin-bottom: 16px;
            transition: border-color 0.2s;
        }}

        .password-box input[type="password"]:focus {{
            outline: none;
            border-color: #2563eb;
        }}

        .password-box button {{
            width: 100%;
            padding: 14px;
            background: #2563eb;
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }}

        .password-box button:hover {{
            background: #1d4ed8;
        }}

        .password-error {{
            color: #ef4444;
            font-size: 13px;
            margin-top: 12px;
            display: none;
        }}

        .password-box input[type="password"].error {{
            border-color: #ef4444;
        }}
    </style>
</head>
<body>
    <!-- 密码保护层 -->
    <div id="password-overlay">
        <div class="password-box">
            <h2>🔒 AgentRadar</h2>
            <p>请输入访问密码</p>
            <input type="password" id="password-input" placeholder="输入密码..." onkeypress="if(event.key==='Enter')checkPassword()">
            <button onclick="checkPassword()">进入</button>
            <p class="password-error" id="password-error">密码错误，请重试</p>
        </div>
    </div>

    <!-- 主内容（默认隐藏） -->
    <div id="main-content" style="display:none">
    <header>
        <h1>🤖 AgentRadar</h1>
        <p>AI 每日情报 · 智能体行业动态</p>
    </header>

    <nav class="date-nav" id="dateNav"></nav>

    <div class="filter-bar" id="filterBar">
        <button class="filter-btn active" data-type="all">全部</button>
        <button class="filter-btn" data-type="技术突破">技术突破</button>
        <button class="filter-btn" data-type="产品动态">产品动态</button>
        <button class="filter-btn" data-type="生态变化">生态变化</button>
        <button class="filter-btn" data-type="KOL观点">KOL观点</button>
        <button class="filter-btn" data-type="监管政策">监管政策</button>
        <button class="filter-btn" data-type="用户数据">用户数据</button>
    </div>

    </div><!-- 关闭 main-content -->

    <div class="stats" id="stats"></div>

    <main class="content" id="content"></main>

    <footer>
        <p>数据来源：每日情报收集任务 | 更新于 <span id="updateTime"></span></p>
    </footer>

    </div><!-- 关闭 #main-content -->

    <script>
        // ===== 密码保护 =====
        const CORRECT_PASSWORD = 'agentradar2365'; // ← 修改这里设置密码

        function checkPassword() {{
            const input = document.getElementById('password-input');
            const overlay = document.getElementById('password-overlay');
            const mainContent = document.getElementById('main-content');
            const errorMsg = document.getElementById('password-error');

            if (input.value === CORRECT_PASSWORD) {{
                overlay.classList.add('hidden');
                mainContent.style.display = 'block';
                init(); // 验证成功后初始化
            }} else {{
                input.classList.add('error');
                errorMsg.style.display = 'block';
                input.value = '';
                input.focus();
            }}
        }}

        // 回车键支持
        document.getElementById('password-input').addEventListener('keypress', function(e) {{
            if (e.key === 'Enter') checkPassword();
        }});

        const intelligenceData = {dates_json};

        const summariesData = {summaries_json};

        const itemsData = {items_json};

        let currentFilter = 'all';
        let currentDate = null;

        function init() {{
            renderDateNav();
            renderStats();
            renderContent();
            document.getElementById('updateTime').textContent = new Date().toLocaleString('zh-CN');
        }}

        function renderDateNav() {{
            const nav = document.getElementById('dateNav');
            nav.innerHTML = `
                <button class="date-btn ${{!currentDate ? 'active' : ''}}" data-date="">全部</button>
                ${{intelligenceData.map(d => `
                    <button class="date-btn ${{currentDate === d ? 'active' : ''}}" data-date="${{d}}">
                        ${{d.slice(5)}}
                    </button>
                `).join('')}}
            `;

            nav.querySelectorAll('.date-btn').forEach(btn => {{
                btn.onclick = () => {{
                    currentDate = btn.dataset.date || null;
                    nav.querySelectorAll('.date-btn').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    renderStats();
                    renderContent();
                }};
            }});
        }}

        function renderStats() {{
            const stats = document.getElementById('stats');
            let filtered = itemsData;
            if (currentDate) {{
                filtered = filtered.filter(item => item.date.startsWith(currentDate));
            }}

            const typeCount = {{}};
            filtered.forEach(item => {{
                typeCount[item.type] = (typeCount[item.type] || 0) + 1;
            }});

            stats.innerHTML = `
                <span class="stat-item">
                    <span class="stat-label">总条目</span>
                    <span class="stat-value">${{filtered.length}}</span>
                </span>
                ${{Object.entries(typeCount).map(([type, count]) => `
                    <span class="stat-item">
                        <span class="stat-label">${{type}}</span>
                        <span class="stat-value">${{count}}</span>
                    </span>
                `).join('')}}
            `;
        }}

        function renderContent() {{
            const content = document.getElementById('content');

            let filteredItems = itemsData;
            if (currentDate) {{
                filteredItems = filteredItems.filter(item => item.date.startsWith(currentDate));
            }}

            if (currentFilter !== 'all') {{
                filteredItems = filteredItems.filter(item => item.type === currentFilter);
            }}

            if (filteredItems.length === 0) {{
                content.innerHTML = `
                    <div class="empty">
                        <div class="empty-icon">📭</div>
                        <p>暂无情报数据</p>
                    </div>
                `;
                return;
            }}

            // 按日期分组
            const grouped = {{}};
            filteredItems.forEach(item => {{
                const d = item.date.slice(0, 10);
                if (!grouped[d]) grouped[d] = [];
                grouped[d].push(item);
            }});

            const sortedDates = Object.keys(grouped).sort().reverse();

            content.innerHTML = sortedDates.map(date => {{
                const summary = summariesData[date];
                const items = grouped[date];

                return `
                    <div class="date-group">
                        <div class="date-header">${{date}}</div>
                        ${{summary ? `
                            <div class="summary">
                                <div class="summary-title">📋 情报纪要</div>
                                <div class="summary-text">${{summary}}</div>
                            </div>
                        ` : ''}}
                        ${{items.map(item => `
                            <div class="card" onclick="this.classList.toggle('expanded')">
                                <div class="card-header">
                                    <span class="card-type ${{item.type}}">${{item.type}}</span>
                                    <span class="card-title">${{item.title}}</span>
                                    <span class="card-date">${{item.date.slice(5)}}</span>
                                </div>
                                <div class="card-info">${{item.info}}</div>
                                <div class="card-footer">
                                    <a href="${{item.source_url}}" target="_blank" class="card-source" onclick="event.stopPropagation()">${{item.source}}</a>
                                    <span class="card-note">${{item.note || ''}}</span>
                                </div>
                                <div class="card-detail">
                                    <p>📅 ${{item.date}}</p>
                                    <p>📍 ${{item.note || '暂无备注'}}</p>
                                </div>
                            </div>
                        `).join('')}}
                    </div>
                `;
            }}).join('');
        }}

        // 筛选
        document.getElementById('filterBar').addEventListener('click', e => {{
            if (e.target.classList.contains('filter-btn')) {{
                currentFilter = e.target.dataset.type;
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                renderStats();
                renderContent();
            }}
        }});

        init();
    </script>
</body>
</html>'''

    # 替换数据
    html = html.replace('{dates_json}', str(dates_json))
    html = html.replace('{summaries_json}', str(summaries_json))
    html = html.replace('{items_json}', str(items_json))

    return html

if __name__ == '__main__':
    main()
