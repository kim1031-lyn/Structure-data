import streamlit as st
import pandas as pd
import json
import re
import os

USER_FILE = "users.json"

# ----------------- 用户持久化加载 -----------------
def load_user_db():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {"man": {"password": "out", "is_admin": True}}

# ----------------- 用户持久化保存 -----------------
def save_user_db(user_db):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(user_db, f, ensure_ascii=False, indent=2)

# ----------------- 初始化 -----------------
def init_user_db():
    if "user_db" not in st.session_state:
        st.session_state.user_db = load_user_db()
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = ""

init_user_db()
user_db = st.session_state.user_db

# ----------------- 登录逻辑 -----------------
if not st.session_state.authenticated:
    st.markdown("# 🔒 结构化数据助手 - 登录")
    username = st.text_input("用户名")
    password = st.text_input("密码", type="password")

    if st.button("登录"):
        if username in user_db and user_db[username]["password"] == password:
            st.session_state.username = username
            st.session_state.authenticated = True
            st.success("登录成功！请点击左侧导航栏选择功能模块。")
        else:
            st.error("用户名或密码错误")
    st.stop()

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

# ----------------- Schema 模板 -----------------
schema_templates = {
    "Article": {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": "",
        "image": {
            "@type": "ImageObject",
            "url": "",
            "width": "",
            "height": ""
        },
        "author": {
            "@type": "Person",
            "name": ""
        },
        "publisher": {
            "@type": "Organization",
            "name": "",
            "logo": {
                "@type": "ImageObject",
                "url": "",
                "width": "",
                "height": ""
            }
        },
        "datePublished": "",
        "sameAs": []
    },
    "Product": {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "",
        "image": "",
        "description": "",
        "sku": "",
        "brand": {"@type": "Brand", "name": ""},
        "offers": {
            "@type": "Offer",
            "priceCurrency": "USD",
            "price": "",
            "availability": "https://schema.org/InStock"
        },
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": "",
            "reviewCount": ""
        },
        "sameAs": []
    }
    # 可继续扩展更多模板类型
}

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

    st.subheader("📘 结构化数据类型选择与模板生成")
    schema_types = list(schema_templates.keys())
    selected_schema = st.selectbox("选择结构化数据类型：", schema_types)

    if selected_schema:
        schema_object = schema_templates[selected_schema]
        schema_json = json.dumps(schema_object, indent=2, ensure_ascii=False)
        edited_schema = st.text_area("结构化数据 JSON-LD 模板", schema_json, height=400)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.download_button("📋 复制", edited_schema, file_name=f"{selected_schema}.json", mime="application/json")
        with col2:
            if st.button("🔄 重置"):
                st.experimental_rerun()
        with col3:
            st.markdown("[🧪 Schema.org 验证器](https://validator.schema.org/)", unsafe_allow_html=True)
        with col4:
            st.markdown("[🔍 Google 富媒体测试](https://search.google.com/test/rich-results)", unsafe_allow_html=True)

        st.subheader("🔗 添加社交媒体链接 sameAs")
        same_as_links = st.text_area("请用逗号分隔社交媒体链接", placeholder="https://twitter.com/xxx, https://facebook.com/xxx")
        if same_as_links:
            try:
                links = [link.strip() for link in same_as_links.split(",") if link.strip()]
                schema_object["sameAs"] = links
                schema_json = json.dumps(schema_object, indent=2, ensure_ascii=False)
                st.success("社媒链接已添加")
                st.text_area("更新后的结构化数据：", schema_json, height=400)
            except Exception as e:
                st.error(f"解析链接失败：{e}")

# ----------------- 管理后台 -----------------
elif page == "管理后台":
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
            user_db[new_user] = {"password": new_pass, "is_admin": is_admin}
            save_user_db(user_db)
            st.success("用户添加成功！")
            st.experimental_rerun()
        else:
            st.error("请输入完整的用户名和密码")

    st.markdown("### 🔑 重置用户密码")
    selectable_users = [u for u in user_db if u != current_user]
    if selectable_users:
        selected_user = st.selectbox("选择用户", options=selectable_users)
        reset_pass = st.text_input("新密码", type="password", key="resetpw")
        if st.button("重置密码"):
            if selected_user in user_db and reset_pass:
                user_db[selected_user]["password"] = reset_pass
                save_user_db(user_db)
                st.success(f"用户 `{selected_user}` 密码已重置")
            else:
                st.warning("请输入新密码")
    else:
        st.info("暂无可重置的其他用户")
