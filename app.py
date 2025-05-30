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
        return {"Eric": {"password": "1314", "is_admin": True}}

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

    st.markdown("""
    <div style="text-align: center;">
        <a href="https://search.google.com/test/rich-results" target="_blank">🔍 Google 富媒体测试工具</a> |
        <a href="https://validator.schema.org/" target="_blank">🧪 Schema.org 验证器</a> |
        <a href="https://chatgpt.com/" target="_blank">🤖 跳转 ChatGPT</a>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("📘 常见结构化数据类型一览表")
    schema_data = pd.DataFrame([
        ["Product", "产品结构化", "name, image, sku, brand, offers"],
        ["Article", "文章结构化", "headline, author, datePublished"],
        ["Organization", "组织机构", "name, url, logo, contactPoint"],
        ["Event", "事件", "name, startDate, endDate, location"],
        ["FAQPage", "常见问答", "mainEntity.question, acceptedAnswer.text"],
        ["Review", "评价", "author, reviewBody, reviewRating"]
    ], columns=["Schema 类型", "描述", "字段示例"])
    st.dataframe(schema_data, use_container_width=True)

# ----------------- 管理后台 -----------------
elif page == "管理后台":
    current_user = st.session_state.username
    if not user_db.get(current_user, {}).get("is_admin"):
        st.error("🚫 您无权访问后台管理页面")
        st.stop()

    st.title("🛠 管理后台")
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
    reset_user = st.selectbox("选择用户", [u for u in user_db if u != current_user])
    new_password = st.text_input("新密码", type="password")
    if st.button("重置密码"):
        if reset_user and new_password:
            user_db[reset_user]["password"] = new_password
            save_user_db(user_db)
            st.success(f"用户 `{reset_user}` 的密码已更新！")

# ----------------- 结构化生成器 -----------------
elif page == "结构化生成器":
    st.title("🧱 结构化数据生成器")

    SCHEMA_FIELDS = {
        "Product": ["name", "image", "description", "sku", "brand.name", "offers.price", "offers.priceCurrency"],
        "Article": ["headline", "author.name", "datePublished", "image", "articleBody"],
        "Organization": ["name", "url", "logo", "contactPoint.telephone", "contactPoint.contactType"],
        "Event": ["name", "startDate", "endDate", "location.name", "location.address", "organizer.name"],
        "Person": ["name", "jobTitle", "worksFor.name"],
        "FAQPage": ["mainEntity.name", "mainEntity.acceptedAnswer.text"],
        "Review": ["author", "reviewBody", "reviewRating.ratingValue"],
        "Recipe": ["name", "recipeIngredient", "recipeInstructions", "cookTime"],
        "Service": ["name", "serviceType", "provider.name", "areaServed"],
        "SoftwareApplication": ["name", "applicationCategory", "operatingSystem"],
        "VideoObject": ["name", "description", "uploadDate", "thumbnailUrl"]
    }

    SOCIAL_PLATFORMS = {
        "Facebook": "https://facebook.com/",
        "Instagram": "https://instagram.com/",
        "LinkedIn": "https://linkedin.com/in/",
        "Twitter": "https://twitter.com/",
        "YouTube": "https://youtube.com/",
        "WhatsApp": "https://wa.me/"
    }

    left, right = st.columns([1, 1])

    with left:
        selected_schema = st.selectbox("选择 Schema 类型", list(SCHEMA_FIELDS.keys()))
        st.markdown("#### 📌 可用字段（点击选中）")
        selected_fields = st.multiselect("字段选择", SCHEMA_FIELDS[selected_schema])
        st.markdown("#### 🌐 选择社交平台（可多选）")
        selected_socials = st.multiselect("社交平台", list(SOCIAL_PLATFORMS.keys()))

        st.markdown("#### ➕ 添加自定义字段")
        custom_key = st.text_input("字段名（如 brand.color）")
        custom_val = st.text_input("字段默认值")
        if st.button("添加字段") and custom_key:
            selected_fields.append(custom_key)
            st.session_state[f"custom_{custom_key}"] = custom_val
            st.success(f"已添加字段 {custom_key}")

    field_inputs = {}
    with right:
        st.markdown("#### ✏️ 输入字段内容")
        for field in selected_fields:
            default_val = st.session_state.get(f"custom_{field}", "")
            field_inputs[field] = st.text_input(field, value=default_val)

        social_links = []
        if selected_socials:
            st.markdown("#### 🔗 填写社交链接")
            for platform in selected_socials:
                url = st.text_input(f"{platform} 链接", placeholder=SOCIAL_PLATFORMS[platform])
                if url:
                    social_links.append(url)

        st.markdown("#### 📄 实时 JSON-LD 模板")

        def build_nested_json(flat_dict):
            nested = {}
            for k, v in flat_dict.items():
                keys = k.split(".")
                current = nested
                for i, key in enumerate(keys):
                    if i == len(keys) - 1:
                        current[key] = v
                    else:
                        current = current.setdefault(key, {})
            return nested

        schema = {
            "@context": "https://schema.org",
            "@type": selected_schema
        }
        schema.update(build_nested_json(field_inputs))
        if social_links:
            schema["sameAs"] = social_links

        schema_str = json.dumps(schema, indent=2, ensure_ascii=False)
        st.code(schema_str, language="json")

        if st.button("📋 复制结构化数据"):
            st.session_state.schema_json = schema_str
            st.success("已复制，请粘贴到目标位置或富媒体工具")
            st.text_area("手动复制区（Ctrl+C）", schema_str, height=300)