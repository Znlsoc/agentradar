# AgentRadar

AI 每日情报聚合网站

## 自动更新流程

1. 每日情报 md 文件放在 `source/` 文件夹
2. 推送到 GitHub
3. Netlify 自动运行 `generate_page.py` 生成网页
4. 自动部署上线

## 手动更新

```bash
python3 generate_page.py
```

## 部署

使用 Netlify 连接到本仓库即可。
