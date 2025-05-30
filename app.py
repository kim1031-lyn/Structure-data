import streamlit as st
import pandas as pd
import json
import re
import os
import copy

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
    if "schema_json" not in st.session_state:
        st.session_state.schema_json = ""
    if "same_as_links" not in st.session_state:
        st.session_state.same_as_links = []

init_user_db()
user_db = st.session_state.user_db

# ----------------- 页面配置 -----------------
st.set_page_config(page_title="结构化数据助手", layout="wide")
st.markdown("""
<style>
h1, .stTitle {text-align: center;}
.stMarkdown, .stDataFrame, .stTextInput, .stTextArea, .stButton {padding: 0 2rem;}
.sidebar-title {font-size: 1.2rem; font-weight: bold;}
.login-box {
  max-width: 400px;
  margin: 5rem auto;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 0 20px rgba(0,0,0,0.1);
  background-color: #f9f9f9;
  text-align: center;
}
.login-box h1 {
  margin-bottom: 1.5rem;
}
</style>
""", unsafe_allow_html=True)

# ----------------- 登录逻辑 -----------------
if not st.session_state.authenticated:
    with st.container():
        st.markdown("""
        <div class="login-box">
            <h1>🔒 结构化数据助手 - 登录</h1>
        </div>
        """, unsafe_allow_html=True)

        username = st.text_input("用户名", key="username_input")
        password = st.text_input("密码", type="password", key="password_input")
        login_clicked = st.button("登录")

        if login_clicked:
            if username in user_db and user_db[username]["password"] == password:
                st.session_state.username = username
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("用户名或密码错误")
    st.stop()

# ----------------- 页面导航 -----------------
st.sidebar.markdown("## 📂 功能导航")
page = st.sidebar.radio("请选择功能模块：", ["首页", "结构化生成器", "管理后台"])

# ----------------- 首页 -----------------
if page == "首页":
    st.title("📊 结构化数据助手")
    # 此处保留你原有首页的全部内容
    st.markdown("欢迎使用结构化数据助手。")

# ----------------- 管理后台 -----------------
elif page == "管理后台":
    current_user = st.session_state.username
    if not user_db.get(current_user, {}).get("is_admin"):
        st.error("🚫 您无权访问后台管理页面")
        st.stop()
    st.title("🛠 管理后台")
    st.write("功能略……")

# ----------------- 结构化生成器 -----------------
elif page == "结构化生成器":
    st.title("🧱 结构化数据生成器")
    st.markdown("本工具可视化构建结构化数据 JSON-LD，支持多类型 Schema，字段嵌套、自定义字段与社交信息嵌入。")

    SCHEMA_TEMPLATES = {
        "Product": {
            "name": "text",
            "image": "text",
            "description": "text",
            "sku": "text",
            "brand": {
                "@type": "Brand",
                "name": "text"
            }
        },
        "Article": {
            "headline": "text",
            "author": {
                "@type": "Person",
                "name": "text"
            },
            "datePublished": "text",
            "image": "text"
        },
        "Event": {
            "name": "text",
            "startDate": "text",
            "endDate": "text",
            "location": {
                "@type": "Place",
                "name": "text",
                "address": "text"
            },
            "organizer": {
                "@type": "Organization",
                "name": "text"
            }
        },
        "JobPosting": {
            "title": "text",
            "description": "text",
            "datePosted": "text",
            "employmentType": "text",
            "hiringOrganization": {
                "@type": "Organization",
                "name": "text"
            },
            "jobLocation": {
                "@type": "Place",
                "address": "text"
            }
        }
    }

    form_state = {}

    def render_fields(schema, container, path=""):
        for key, val in schema.items():
            full_key = f"{path}.{key}" if path else key
            if isinstance(val, dict):
                with container.expander(f"嵌套字段: {key}", expanded=False):
                    render_fields(val, container, full_key)
            else:
                form_state[full_key] = container.text_input(full_key)

    schema_type_choice = st.selectbox("选择 Schema 类型", list(SCHEMA_TEMPLATES.keys()))
    base_schema = {
        "@context": "https://schema.org",
        "@type": schema_type_choice
    }

    st.subheader("📝 填写字段内容")
    render_fields(SCHEMA_TEMPLATES[schema_type_choice], st)

    st.subheader("➕ 添加自定义字段")
    custom_key = st.text_input("字段名（如 brand.color）")
    custom_val = st.text_input("字段值")
    if st.button("添加字段") and custom_key and custom_val:
        form_state[custom_key] = custom_val
        st.success(f"已添加字段 `{custom_key}`")

    st.subheader("🌐 社交信息")
    use_social = st.checkbox("启用社交联系方式")
    social_links = []
    contact_points = []

    if use_social:
        with st.expander("填写社交与联系信息"):
            fb = st.text_input("Facebook")
            ins = st.text_input("Instagram")
            li = st.text_input("LinkedIn")
            tw = st.text_input("Twitter")
            wa = st.text_input("WhatsApp")
            site = st.text_input("官网")
            email = st.text_input("邮箱")
            phone = st.text_input("电话")

            for val in [fb, ins, li, tw, wa, site]:
                if val.strip():
                    social_links.append(val.strip())
            if email:
                contact_points.append({"@type": "ContactPoint", "contactType": "Email", "email": email})
            if phone:
                contact_points.append({"@type": "ContactPoint", "contactType": "Phone", "telephone": phone})

    def build_nested_json(form_data):
        result = {}
        for k, v in form_data.items():
            keys = k.split(".")
            current = result
            for i, part in enumerate(keys):
                if i == len(keys) - 1:
                    current[part] = v
                else:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
        return result

    final_schema = copy.deepcopy(base_schema)
    final_schema.update(build_nested_json(form_state))
    if social_links:
        final_schema["sameAs"] = social_links
    if contact_points:
        final_schema["contactPoint"] = contact_points

    st.subheader("📄 生成结果")
    schema_json_str = json.dumps(final_schema, indent=2, ensure_ascii=False)
    st.code(schema_json_str, language="json")
    st.download_button("📥 下载 JSON 文件", schema_json_str, file_name=f"{schema_type_choice}.json", mime="application/json")