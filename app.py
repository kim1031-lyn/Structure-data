import streamlit as st
import pandas as pd
import json
import re

# ----------------- 用户配置与状态初始化 -----------------
def init_user_db():
    if "user_db" not in st.session_state:
        st.session_state.user_db = {
            "man": {"password": "out", "is_admin": True},
        }
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "pending_user" not in st.session_state:
        st.session_state.pending_user = ""

init_user_db()

# ----------------- 登录逻辑 -----------------
if not st.session_state.authenticated:
    st.markdown("# 🔒 结构化数据助手 - 登录")
    username = st.text_input("用户名")
    password = st.text_input("密码", type="password")

    if st.button("登录"):
        user_db = st.session_state.user_db
        if username in user_db and user_db[username]["password"] == password:
            st.session_state.pending_user = username
            st.session_state.authenticated = True
            st.experimental_rerun()
        else:
            st.error("用户名或密码错误")
    st.stop()

# 登录成功后记录当前用户
if "username" not in st.session_state and st.session_state.pending_user:
    st.session_state.username = st.session_state.pending_user

# ----------------- 页面配置 -----------------
st.set_page_config(page_title="结构化数据助手", layout="wide")
st.markdown("""
<style>
h1, .stTitle {text-align: center;}
.stMarkdown, .stDataFrame, .stTextInput, .stTextArea, .stButton {padding: 0 2rem;}
.sidebar-title {font-size: 1.2rem; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# ----------------- 页面导航 -----------------
st.sidebar.markdown("## 📂 功能导航")
page = st.sidebar.radio("请选择功能模块：", ["首页", "管理后台"])

# ----------------- 首页 -----------------
if page == "首页":
    st.title("📊 结构化数据助手")

    st.markdown("""
    <div style="text-align: center;">
        <a href="https://search.google.com/test/rich-results" target="_blank">🔍 Google 富媒体测试工具</a> |
        <a href="https://validator.schema.org/" target="_blank">🧪 Schema.org 验证器</a> |
        <a href="https://chatgpt.com/" target="_blank">🤖 跳转 ChatGPT</a>
    </div>
    """, unsafe_allow_html=True)

    schema_data = [
        ["Organization", "描述公司、机构、品牌的基本信息", "name, logo, url, contactPoint, sameAs, address, foundingDate, founder", "企业首页、关于我们页"],
        ["Article", "普通文章内容", "headline, author, datePublished, dateModified, image, mainEntityOfPage, articleBody", "博客、新闻、知识型页面"],
        ["NewsArticle", "新闻文章", "headline, author, publisher, datePublished, dateline, articleSection", "新闻类网站"],
        ["Product", "产品信息", "name, image, description, sku, brand, offers, aggregateRating, review", "商品详情页、商城页面"],
        ["Review", "单个评价内容", "author, reviewBody, reviewRating, datePublished", "评论模块、服务评价区域"],
        ["AggregateRating", "汇总评价分数摘要", "ratingValue, reviewCount", "商品、服务、企业评价"],
        ["BreadcrumbList", "面包屑导航", "itemListElement（@type: ListItem, position, name, item）", "所有页面"],
        ["FAQPage", "FAQ 页面结构", "mainEntity（@type: Question 和 acceptedAnswer）", "常见问题、帮助中心页"],
        ["HowTo", "教程型页面", "name, step, totalTime, tool, supply", "教程类页面"],
        ["VideoObject", "视频内容", "name, description, uploadDate, thumbnailUrl, duration, embedUrl", "视频页"],
        ["LocalBusiness", "本地商户", "name, address, openingHours, telephone, geo, aggregateRating", "门店页"],
        ["Event", "事件类信息", "name, startDate, endDate, location, organizer, description, image", "活动页、会议页"],
        ["JobPosting", "招聘岗位", "title, description, datePosted, employmentType, hiringOrganization, jobLocation", "招聘页"],
        ["Recipe", "菜谱内容", "name, image, recipeIngredient, recipeInstructions, cookTime, nutrition", "食谱站点"],
        ["Person", "描述个人", "name, image, jobTitle, worksFor, sameAs", "关于作者、作者详情页"],
        ["Service", "服务类型说明", "name, serviceType, areaServed, provider, offers, description", "服务页、介绍页"],
        ["SoftwareApplication", "软件/APP 信息", "name, operatingSystem, applicationCategory, offers, aggregateRating", "APP介绍页、软件下载页"]
    ]

    st.subheader("📘 常见结构化数据类型一览表")
    df = pd.DataFrame(schema_data, columns=["Schema 类型", "用途 / 描述", "常用字段", "推荐页面类型/场景"])
    st.dataframe(df, use_container_width=True)

    st.subheader("✨ AI语料生成工具")
    schema_type = st.text_input("输入 Schema 类型，如：Product")
    if st.button("生成语料"):
        if schema_type.strip():
            prompt = f"请帮我生成一个全面的结构化数据（Schema.org）JSON-LD 格式，类型是 \"{schema_type}\"，字段尽量详细，包含所有适合展示在搜索引擎中的字段，结构清晰可编辑，并确保可通过 Google 富媒体测试工具验证。"
            st.code(prompt, language="text")
        else:
            st.warning("请输入 Schema 类型")

    st.subheader("🧠 结构化数据比对分析")
    col1, col2 = st.columns(2)
    with col1:
        original_schema = st.text_area("原始 Schema 粘贴区", height=300)
    with col2:
        new_schema = st.text_area("新生成 Schema 粘贴区", height=300)

    if st.button("分析重复字段"):
        try:
            original_fields = re.findall(r'"(\\w+)":', json.dumps(json.loads(original_schema)))
            new_fields = re.findall(r'"(\\w+)":', json.dumps(json.loads(new_schema)))
            repeated = sorted(set(original_fields) & set(new_fields))
            if repeated:
                st.success("重复字段：")
                st.code(", ".join(repeated))
            else:
                st.info("无重复字段")
        except Exception as e:
            st.error(f"解析失败，请确保 JSON 格式正确。\n\n错误信息: {e}")

# ----------------- 管理后台 -----------------
elif page == "管理后台":
    user_db = st.session_state.user_db
    current_user = st.session_state.username

    if not user_db.get(current_user, {}).get("is_admin"):
        st.error("🚫 您无权访问后台管理页面")
        st.stop()

    st.title("🛠 管理后台")
    st.markdown("当前用户：`{}`（管理员）".format(current_user))
    st.markdown("---")

    st.subheader("👥 用户管理")
    st.markdown("### 当前所有用户")
    user_table = pd.DataFrame([
        {"用户名": k, "是否管理员": "✅" if v["is_admin"] else "❌"} for k, v in user_db.items()
    ])
    st.table(user_table)

    st.markdown("### ➕ 添加新用户")
    new_user = st.text_input("新用户名")
    new_pass = st.text_input("新密码", type="password")
    is_admin = st.checkbox("是否设为管理员")
    if st.button("添加用户"):
        if new_user in user_db:
            st.warning("该用户已存在")
        elif new_user and new_pass:
            st.session_state.user_db[new_user] = {"password": new_pass, "is_admin": is_admin}
            st.success("用户添加成功！")
            st.experimental_rerun()
        else:
            st.error("请输入完整的用户名和密码")

    st.markdown("### 🔑 重置用户密码")
    selected_user = st.selectbox("选择用户", options=[u for u in user_db if u != current_user])
    reset_pass = st.text_input("新密码", type="password", key="resetpw")
    if st.button("重置密码"):
        if selected_user in user_db and reset_pass:
            user_db[selected_user]["password"] = reset_pass
            st.success(f"用户 `{selected_user}` 密码已重置")
        else:
            st.warning("请输入新密码")