# 自动选课与自动评教爬虫（通用可配置）

本项目提供一个通用、可配置的爬虫框架，帮助你在指定网站上实现：
- 自动登录
- 自动抢/选课
- 自动评教（自动填表并提交）

由于各个学校/系统的实现差异很大，本项目通过 YAML 配置来适配目标网站的：
- 登录页面与表单字段
- 课程列表和“选课/报名”链接的选择器
- 评教列表、评教页面表单的选择器及填表策略

你只需要根据目标网站的 HTML 结构和接口，填好配置文件即可使用。

重要提示：请确保你的使用符合目标网站的服务条款与当地法律法规。本项目仅用于学习与个人研究。

## 功能概览

- 会话保持：基于 requests.Session 维护 Cookie
- 登录：支持在登录页提取 CSRF/隐藏字段并提交
- 自动选课：
  - 抓取课程列表页
  - 解析课程条目（可配置 CSS 选择器）
  - 支持按关键词或课程 ID 过滤目标课程
  - 支持直接点击“选课链接”或通过 POST 提交选课表单
- 自动评教：
  - 抓取待评教列表
  - 打开评教页面，自动识别 form
  - 自动选择单选题最高分、选择题最后一个选项（可改）、填充文本域默认内容
  - 提交表单
- 定时启动：支持设置“在某个时间点开始执行”（用于抢课场景）

## 快速开始

1. 安装依赖（建议使用 Python 3.9+）：

```
pip install -r requirements.txt
```

2. 复制配置模板并根据你的目标网站调整：

```
cp config.example.yaml config.yaml
```

3. 运行（立即执行）：

- 自动选课
```
python run.py -c config.yaml --mode enroll
```
或（未安装到环境时）
```
PYTHONPATH=src python -m auto_crawler.cli -c config.yaml --mode enroll
```

- 自动评教
```
python run.py -c config.yaml --mode evaluate
```
或
```
PYTHONPATH=src python -m auto_crawler.cli -c config.yaml --mode evaluate
```

- 先选课再评教
```
python run.py -c config.yaml --mode both
```
或
```
PYTHONPATH=src python -m auto_crawler.cli -c config.yaml --mode both
```

4. 定时启动（例如在 2025-01-01 08:59:55 开始）：

```
python run.py -c config.yaml --mode enroll --at "2025-01-01 08:59:55"
```
或
```
PYTHONPATH=src python -m auto_crawler.cli -c config.yaml --mode enroll --at "2025-01-01 08:59:55"
```

## 配置说明（config.yaml）

见 config.example.yaml，核心结构如下：

- credentials：账号密码
- site.base_url：站点根地址
- site.login：登录相关配置（登录页、提交地址、表单字段名、可从页面提取的 CSRF 等）
- site.enroll：选课相关（列表页、条目选择器、过滤条件、提交方式）
- site.evaluate：评教相关（列表页、条目与进入评教页的链接选择器、表单选择器与填表策略）

该配置力求通用，但每个网站实现不同，可能需要你根据目标站实际结构微调选择器与字段名。

## 重要建议

- 抢课通常在固定时刻开放，建议配合 --at 参数提前运行并在那一刻自动开始。
- 如遇验证码/二次验证，本项目提供了钩子位置；你需要自行接入第三方识别或改为手动先登录后再启动脚本。
- 默认填表策略较为保守（单选题选“最大值”），可在配置中调整。

## 目录结构

```
.
├── README.md
├── requirements.txt
├── config.example.yaml
└── src
    └── auto_crawler
        ├── __init__.py
        ├── cli.py
        ├── config.py
        ├── http.py
        ├── auto_enroll.py
        ├── auto_evaluate.py
        └── utils.py
```

## 免责声明

- 使用本项目造成的任何后果由使用者自行承担。
- 请遵守学校与网站的使用规范，合理合规地使用本项目。
