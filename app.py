# app.py
import streamlit as st
import pandas as pd
import json
import re
import os
from datetime import datetime
import hashlib # 新增：用于密码哈希

USER_FILE = "users.json"

# ----------------- 用户持久化加载 -----------------
def load_user_db():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        # 初始用户 Eric 的密码也应是哈希过的
        # 假设 '1314' 的 SHA-256 哈希值
        initial_hashed_password = hashlib.sha256("1314".encode()).hexdigest()
        return {"Eric": {"password": initial_hashed_password, "is_admin": True}}

# ----------------- 用户持久化保存 -----------------
def save_user_db(user_db):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(user_db, f, ensure_ascii=False, indent=2)

# ----------------- 密码哈希函数 -----------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

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
    if "ai_prompt_to_copy" not in st.session_state: # 新增：用于复制AI提示词
        st.session_state.ai_prompt_to_copy = ""

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
            if username in user_db and user_db[username]["password"] == hash_password(password):
                st.session_state.username = username
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("用户名或密码错误")
    st.stop()

# ----------------- 页面导航 -----------------
st.sidebar.markdown("## 📂 功能导航")
page = st.sidebar.radio("请选择功能模块：", ["首页", "结构化生成器", "管理后台", "JSON-LD 对比"]) # 新增页面

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
    new_user = st.text_input("新用户名", key="new_user_input")
    new_pass = st.text_input("新密码", type="password", key="new_pass_input")
    is_admin = st.checkbox("是否设为管理员", key="is_admin_checkbox")
    if st.button("添加用户"):
        if new_user in user_db:
            st.warning("该用户已存在")
        elif new_user and new_pass:
            user_db[new_user] = {"password": hash_password(new_pass), "is_admin": is_admin}
            save_user_db(user_db)
            st.success("用户添加成功！")
            st.experimental_rerun()
        else:
            st.error("请输入完整的用户名和密码")

    st.markdown("### 🔑 重置用户密码")
    # 不允许重置当前登录用户的密码，或 Eric 初始用户的密码（如果 Eric 是唯一管理员，可能会导致锁定）
    users_to_reset = [u for u in user_db if u != current_user]
    # 如果 Eric 是初始管理员且只剩Eric一个用户，那么就不提供重置选项
    if current_user != "Eric" and user_db.get("Eric", {}).get("is_admin") and len(users_to_reset) == 0:
        st.info("没有其他用户可供重置密码。")
    elif users_to_reset:
        reset_user = st.selectbox("选择用户", users_to_reset, key="reset_user_select")
        new_password_for_reset = st.text_input("新密码", type="password", key="new_password_reset_input")
        if st.button("重置密码"):
            if reset_user and new_password_for_reset:
                user_db[reset_user]["password"] = hash_password(new_password_for_reset)
                save_user_db(user_db)
                st.success(f"用户 `{reset_user}` 的密码已更新！")
                st.experimental_rerun()
            else:
                st.error("请输入新密码。")
    else:
        st.info("没有其他用户可供重置密码。")


    st.markdown("### 🗑 删除用户")
    # 不允许删除当前登录用户，也不允许删除初始管理员 Eric (如果他是唯一管理员)
    deletable_users = [u for u in user_db if u != current_user and not (u == "Eric" and user_db["Eric"]["is_admin"] and len(user_db) == 1)]

    if deletable_users:
        delete_user = st.selectbox("选择要删除的用户", deletable_users, key="delete_user_select")
        if st.button("删除用户", key="delete_user_btn"):
            if delete_user:
                del user_db[delete_user]
                save_user_db(user_db)
                st.success(f"用户 `{delete_user}` 已删除！")
                st.experimental_rerun()
            else:
                st.warning("请选择一个用户进行删除。")
    else:
        st.info("没有其他用户可供删除。请确保至少保留一个管理员账户。")


# ----------------- 结构化生成器 -----------------
elif page == "结构化生成器":
    st.title("🧱 结构化数据生成器")

    SCHEMA_FIELDS = {
        "Product": ["name", "image", "description", "sku", "brand.name", "offers.price", "offers.priceCurrency"],
        "Article": ["headline", "author.name", "datePublished", "image", "articleBody"],
        "Organization": ["name", "url", "logo", "contactPoint.telephone", "contactPoint.contactType"],
        "Event": ["name", "startDate", "endDate", "location.name", "location.address", "organizer.name"],
        "Person": ["name", "jobTitle", "worksFor.name"],
        "FAQPage": ["mainEntity[0].question", "mainEntity[0].acceptedAnswer.text"], # 简化处理，只显示第一个Q&A
        "Review": ["author", "reviewBody", "reviewRating.ratingValue"],
        "Recipe": ["name", "recipeIngredient", "recipeInstructions", "cookTime"],
        "Service": ["name", "serviceType", "provider.name", "areaServed"],
        "SoftwareApplication": ["name", "applicationCategory", "operatingSystem"],
        "VideoObject": ["name", "description", "uploadDate", "thumbnailUrl"]
    }

    TEMPLATE_VALUES = {
        "Article": {
            "headline": "示例文章标题：探索人工智能的未来",
            "author.name": "张三",
            "datePublished": "2024-06-24",
            "image": "https://example.com/ai_future_image.jpg",
            "articleBody": "人工智能（AI）正在迅速改变我们的世界，从自动化日常任务到推动科学发现。本文将深入探讨AI的最新进展、未来趋势以及它对社会可能产生的影响。我们将讨论机器学习、深度学习、自然语言处理等关键技术，以及AI在医疗、金融、教育等领域的应用前景。"
        },
        "Product": {
            "name": "智能降噪耳机 Pro",
            "image": "https://example.com/headphone.jpg",
            "description": "沉浸式聆听体验，主动降噪技术，超长续航，舒适佩戴。",
            "sku": "SKU00123",
            "brand.name": "TechAudio",
            "offers.price": "199.99",
            "offers.priceCurrency": "USD"
        },
        "FAQPage": {
            "mainEntity[0].question": "什么是结构化数据？",
            "mainEntity[0].acceptedAnswer.text": "结构化数据是指按照预定义的数据模型进行组织和存储的数据，通常以表格形式呈现，具有明确的行和列。它易于搜索和分析，例如数据库中的数据。"
        }
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
        selected_schema = st.selectbox("选择 Schema 类型", list(SCHEMA_FIELDS.keys()), key="schema_type_select")
        st.markdown("#### 📌 可用字段（点击选中）")
        selected_fields = st.multiselect("字段选择", SCHEMA_FIELDS[selected_schema], key="fields_multiselect")

        if st.button("🧪 使用示例模板") : # 移除对 selected_schema 的限制，让模板按钮始终可用
            if selected_schema in TEMPLATE_VALUES:
                for k, v in TEMPLATE_VALUES[selected_schema].items():
                    if k not in selected_fields: # 避免重复添加
                         selected_fields.append(k)
                    st.session_state[f"custom_{k}"] = v
                st.info(f"已加载 {selected_schema} 类型的示例模板。")
            else:
                st.warning(f"当前 {selected_schema} 类型没有可用的示例模板。")


        st.markdown("#### 🌐 选择社交平台（可多选）")
        selected_socials = st.multiselect("社交平台", list(SOCIAL_PLATFORMS.keys()), key="socials_multiselect")

        st.markdown("#### ➕ 添加自定义字段")
        custom_key = st.text_input("字段名（如 brand.color 或 myField.subField）", key="custom_key_input")
        custom_val = st.text_input("字段值", key="custom_val_input")
        if st.button("添加字段") and custom_key:
            if custom_key not in selected_fields:
                selected_fields.append(custom_key)
            st.session_state[f"custom_{custom_key}"] = custom_val
            st.success(f"已添加字段 {custom_key}")

    field_inputs = {}
    with right:
        st.markdown("#### ✏️ 输入字段内容")
        for field in selected_fields:
            default_val = st.session_state.get(f"custom_{field}", "")
            input_key = f"input_{field.replace('.', '_').replace('[', '_').replace(']', '_')}" # 确保 key 唯一且合法
            
            if "date" in field.lower():
                try:
                    # 尝试将 default_val 转换为 datetime 对象
                    default_date = datetime.strptime(str(default_val), "%Y-%m-%d").date() if default_val else datetime.today().date()
                except ValueError:
                    default_date = datetime.today().date()
                val = st.date_input(field, value=default_date, key=input_key).isoformat()
            elif "url" in field.lower() or "image" in field.lower() or "logo" in field.lower():
                val = st.text_input(field, value=default_val, placeholder="https://example.com/path", key=input_key)
                if val and not (val.startswith("http://") or val.startswith("https://")):
                    st.warning(f"字段 {field} 应为合法 URL (以 http:// 或 https:// 开头)")
            elif "price" in field.lower() and "currency" not in field.lower():
                try:
                    val = st.number_input(field, value=float(default_val) if default_val else 0.0, format="%.2f", key=input_key)
                except ValueError:
                    val = st.number_input(field, value=0.0, format="%.2f", key=input_key)
            elif "ratingValue" in field.lower():
                 try:
                    val = st.number_input(field, min_value=1.0, max_value=5.0, value=float(default_val) if default_val else 4.0, step=0.1, key=input_key)
                 except ValueError:
                    val = st.number_input(field, min_value=1.0, max_value=5.0, value=4.0, step=0.1, key=input_key)
            elif "articleBody" in field or "description" in field or "reviewBody" in field or "recipeInstructions" in field:
                val = st.text_area(field, value=default_val, height=150, key=input_key)
            else:
                val = st.text_input(field, value=default_val, key=input_key)
            
            if val is not None: # 确保值不为空，特别是对于数字输入
                field_inputs[field] = val

        social_links = []
        if selected_socials:
            st.markdown("#### 🔗 填写社交链接")
            for platform in selected_socials:
                social_input_key = f"social_{platform.lower()}_input"
                url = st.text_input(f"{platform} 链接", placeholder=SOCIAL_PLATFORMS[platform], key=social_input_key)
                if url:
                    if not (url.startswith("http://") or url.startswith("https://")):
                        st.warning(f"{platform} 链接需为有效 URL (以 http:// 或 https:// 开头)")
                    social_links.append(url)

        st.markdown("#### 📄 实时 JSON-LD 模板")

        def build_nested_json(flat_dict):
            nested = {}
            for k, v in flat_dict.items():
                # 处理数组索引，例如 mainEntity[0].question
                parts = re.split(r'\.|\[(\d+)\]', k)
                parts = [p for p in parts if p] # 过滤空字符串

                current = nested
                for i, part in enumerate(parts):
                    if part.isdigit(): # 是数组索引
                        idx = int(part)
                        if not isinstance(current, list):
                            raise ValueError(f"Expected list at {'.'.join(parts[:i])}, got {type(current)}")
                        while len(current) <= idx:
                            current.append({}) # 填充空字典或列表，取决于下一个部分
                        if i == len(parts) - 1:
                            current[idx] = v
                        else:
                            # 预判下一个是字段名，所以是字典
                            if not isinstance(current[idx], dict):
                                current[idx] = {}
                            current = current[idx]
                    else: # 是字典键
                        if not isinstance(current, dict):
                            raise ValueError(f"Expected dict at {'.'.join(parts[:i])}, got {type(current)}")
                        if i == len(parts) - 1:
                            current[part] = v
                        else:
                            # 预判下一个是索引，所以是列表，否则是字典
                            if i + 1 < len(parts) and parts[i+1].isdigit():
                                current = current.setdefault(part, [])
                            else:
                                current = current.setdefault(part, {})
            return nested


        schema = {
            "@context": "https://schema.org",
            "@type": selected_schema
        }
        try:
            # 过滤掉空的字段值，避免生成大量空键
            filtered_field_inputs = {k: v for k, v in field_inputs.items() if v not in ["", 0.0]}
            schema.update(build_nested_json(filtered_field_inputs))
        except ValueError as e:
            st.error(f"构建 JSON-LD 时出错: {e}. 请检查您的字段名格式，特别是数组索引。")


        if social_links:
            schema["sameAs"] = [link for link in social_links if link] # 过滤空链接

        pretty = st.toggle("格式化显示 JSON", value=True) # 默认格式化显示
        schema_str = json.dumps(schema, indent=2 if pretty else None, ensure_ascii=False)
        st.code(schema_str, language="json")

        if st.button("📋 复制结构化数据"):
            st.session_state.schema_json = schema_str
            st.success("已复制，请粘贴到目标位置或富媒体工具")
            st.text_area("手动复制区（Ctrl+C）", schema_str, height=300)

    # ----------------- AI 语料提示词生成 (新增功能) -----------------
    st.markdown("---")
    st.subheader("🤖 AI 语料提示词生成")

    prompt_type = st.selectbox("选择提示词类型", ["文章生成", "产品描述", "常见问题解答", "通用描述"], key="ai_prompt_type_select")

    ai_prompt = ""
    # 根据已生成的 schema 数据构建提示词
    if selected_schema == "Article" and prompt_type == "文章生成":
        headline = field_inputs.get("headline", "一个主题")
        author = field_inputs.get("author.name", "作者")
        date_published = field_inputs.get("datePublished", datetime.today().strftime("%Y-%m-%d"))
        article_body_summary = field_inputs.get("articleBody", "文章内容概览").splitlines()[0][:100] + "..." # 取前100字
        ai_prompt = f"请为一篇关于“{headline}”的文章撰写详细的正文。文章发布于 {date_published}，作者是 {author}。请在内容中融入以下要点或扩展相关信息：{article_body_summary}。确保文章结构清晰，语言专业且引人入胜。"
    elif selected_schema == "Product" and prompt_type == "产品描述":
        product_name = field_inputs.get("name", "产品")
        description = field_inputs.get("description", "详细描述")
        price = field_inputs.get("offers.price", "未知价格")
        currency = field_inputs.get("offers.priceCurrency", "CNY")
        brand = field_inputs.get("brand.name", "未知品牌")
        ai_prompt = f"请为“{brand}”品牌的“{product_name}”产品撰写一个吸引人的营销描述。产品特性包括：{description}。当前售价为 {price} {currency}。描述应突出产品的核心优势和用户价值。"
    elif selected_schema == "FAQPage" and prompt_type == "常见问题解答":
        qa_list = []
        # 尝试从构建的schema中提取Q&A，这里需要更灵活地处理多个mainEntity
        # 简单示例：如果能从 field_inputs 提取到，就用它
        try:
            # 假设 build_nested_json 已经正确处理了 mainEntity[0].question
            # 直接从生成的schema结构中提取
            main_entity_list = schema.get("mainEntity", [])
            for i, qa_pair in enumerate(main_entity_list):
                question = qa_pair.get("question", f"问题 {i+1}")
                answer = qa_pair.get("acceptedAnswer", {}).get("text", f"答案 {i+1}")
                if question and answer:
                    qa_list.append(f"Q: {question}\nA: {answer}")
        except Exception:
            pass # 如果解析失败，则跳过
        
        if qa_list:
            ai_prompt = "请生成一份包含以下问答内容的FAQ列表，并确保答案简洁明了：\n\n" + "\n\n".join(qa_list)
        else:
            ai_prompt = "请在上方结构化数据中输入 FAQ 内容（如 'mainEntity[0].question' 和 'mainEntity[0].acceptedAnswer.text'），然后选择此选项以生成 FAQ 提示词。"

    else: # 通用描述
        json_data_for_prompt = {k:v for k,v in field_inputs.items() if v not in ["", 0.0]}
        if json_data_for_prompt:
            ai_prompt = f"请根据以下结构化数据信息，撰写一份详细的描述或报告：\n\n```json\n{json.dumps(json_data_for_prompt, indent=2, ensure_ascii=False)}\n```\n\n请提取关键信息并用自然语言进行阐述。"
        else:
            ai_prompt = "请在上方输入字段内容以生成通用 AI 提示词。"

    if ai_prompt:
        st.text_area("生成的 AI 提示词", ai_prompt, height=250, key="ai_prompt_output")
        if st.button("📋 复制 AI 提示词", key="copy_ai_prompt_btn"):
            st.session_state.ai_prompt_to_copy = ai_prompt
            st.success("AI 提示词已复制！")
    else:
        st.info("请选择 Schema 类型并填写相关字段，然后选择提示词类型以生成 AI 提示词。")


# ----------------- JSON-LD 对比 (新增页面) -----------------
elif page == "JSON-LD 对比":
    st.title("⚖️ JSON-LD 对比分析")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("JSON-LD 片段 A")
        json_a_str = st.text_area("在此处粘贴第一个 JSON-LD", height=350, key="json_a_input")
    with col2:
        st.subheader("JSON-LD 片段 B")
        json_b_str = st.text_area("在此处粘贴第二个 JSON-LD", height=350, key="json_b_input")

    compare_button = st.button("🔬 对比 JSON")

    if compare_button:
        try:
            json_a = json.loads(json_a_str)
            json_b = json.loads(json_b_str)

            st.subheader("对比结果")

            # 递归查找差异的辅助函数
            def find_json_diff(dict1, dict2, path=""):
                diffs = []
                # 检查键在 dict1 但不在 dict2
                for k in set(dict1.keys()) - set(dict2.keys()):
                    diffs.append(f"仅在片段 A 中存在: `{path}{k}` = `{dict1[k]}`")
                # 检查键在 dict2 但不在 dict1
                for k in set(dict2.keys()) - set(dict1.keys()):
                    diffs.append(f"仅在片段 B 中存在: `{path}{k}` = `{dict2[k]}`")

                # 检查共同键的值
                for k in set(dict1.keys()) & set(dict2.keys()):
                    new_path = f"{path}{k}." if path else f"{k}."
                    v1 = dict1[k]
                    v2 = dict2[k]

                    if isinstance(v1, dict) and isinstance(v2, dict):
                        diffs.extend(find_json_diff(v1, v2, new_path))
                    elif isinstance(v1, list) and isinstance(v2, list):
                        # 对列表的简单比较：检查元素数量和每个对应元素
                        if len(v1) != len(v2):
                            diffs.append(f"列表长度不同: `{path}{k}` (A: {len(v1)}, B: {len(v2)})")
                        for i in range(min(len(v1), len(v2))):
                            # 如果元素是字典，则递归比较
                            if isinstance(v1[i], dict) and isinstance(v2[i], dict):
                                diffs.extend(find_json_diff(v1[i], v2[i], f"{new_path}[{i}]."))
                            elif v1[i] != v2[i]:
                                diffs.append(f"列表元素不同: `{path}{k}[{i}]` (A: `{v1[i]}`, B: `{v2[i]}`)")
                        # 处理超出长度的元素
                        if len(v1) > len(v2):
                            for i in range(len(v2), len(v1)):
                                diffs.append(f"仅在片段 A 中存在列表元素: `{path}{k}[{i}]` = `{v1[i]}`")
                        elif len(v2) > len(v1):
                            for i in range(len(v1), len(v2)):
                                diffs.append(f"仅在片段 B 中存在列表元素: `{path}{k}[{i}]` = `{v2[i]}`")
                    elif v1 != v2:
                        diffs.append(f"值不同: `{path}{k}` (A: `{v1}`, B: `{v2}`)")
                return diffs

            # 查找共同字段的辅助函数 (返回所有共同字段的路径)
            def find_common_fields(dict1, dict2, path=""):
                common_fields = []
                for k in set(dict1.keys()) & set(dict2.keys()):
                    new_path = f"{path}{k}"
                    common_fields.append(new_path)
                    v1 = dict1[k]
                    v2 = dict2[k]
                    if isinstance(v1, dict) and isinstance(v2, dict):
                        common_fields.extend(find_common_fields(v1, v2, f"{new_path}."))
                    elif isinstance(v1, list) and isinstance(v2, list):
                        # 对于列表中的字典，继续查找共同字段
                        for i in range(min(len(v1), len(v2))):
                            if isinstance(v1[i], dict) and isinstance(v2[i], dict):
                                common_fields.extend(find_common_fields(v1[i], v2[i], f"{new_path}[{i}]."))
                return common_fields


            diff_results = find_json_diff(json_a, json_b)
            common_fields_results = find_common_fields(json_a, json_b)


            if diff_results:
                st.warning("发现差异：")
                for diff in diff_results:
                    st.markdown(f"- {diff}")
            else:
                st.success("两个 JSON-LD 片段完全相同。")

            st.markdown("---")
            st.subheader("共同字段")
            if common_fields_results:
                # 为了更好看，可以将其按层级展示或者简单列出
                st.markdown("以下字段在两个 JSON 中都存在：")
                for field in sorted(common_fields_results):
                    st.markdown(f"- `{field}`")
            else:
                st.info("两个 JSON-LD 片段没有共同字段。")

        except json.JSONDecodeError:
            st.error("请输入有效的 JSON 格式数据。")
        except Exception as e:
            st.error(f"处理 JSON 时发生错误: {e}")