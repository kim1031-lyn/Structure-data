# app.py
import streamlit as st
import pandas as pd
import json
import re
import os
from datetime import datetime
import hashlib # 用于密码哈希

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
    if "ai_prompt_to_copy" not in st.session_state:
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
page = st.sidebar.radio("请选择功能模块：", ["首页", "结构化生成器", "管理后台", "JSON-LD 对比", "解析诊断", "外部资源", "高级功能"]) # 新增页面

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
    users_to_reset = [u for u in user_db if u != current_user]
    if not users_to_reset:
        st.info("没有其他用户可供重置密码。")
    else:
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


    st.markdown("### 🗑 删除用户")
    # 不允许删除当前登录用户，也不允许删除初始管理员 Eric (如果他是唯一管理员且用户数量为1)
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

        if st.button("🧪 使用示例模板") :
            if selected_schema in TEMPLATE_VALUES:
                for k, v in TEMPLATE_VALUES[selected_schema].items():
                    if k not in selected_fields:
                         selected_fields.append(k)
                    st.session_state[f"custom_{k}"] = v
                st.info(f"已加载 {selected_schema} 类型的示例模板。")
            else:
                st.warning(f"当前 {selected_schema} 类型没有可用的示例模板。")


        st.markdown("#### 🌐 选择社交平台（可多选）")
        selected_socials = st.multiselect("社交平台", list(SOCIAL_PLATFORMS.keys()), key="socials_multiselect")

        st.markdown("#### ➕ 添加自定义字段")
        custom_key = st.text_input("字段名（如 brand.color 或 myField[0].subField）", key="custom_key_input")
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
            input_key = f"input_{field.replace('.', '_').replace('[', '_').replace(']', '_')}"

            if "date" in field.lower():
                try:
                    default_date_obj = datetime.strptime(str(default_val), "%Y-%m-%d").date() if default_val else datetime.today().date()
                except ValueError:
                    default_date_obj = datetime.today().date()
                val = st.date_input(field, value=default_date_obj, key=input_key).isoformat()
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

            if val is not None:
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
                parts = re.split(r'\.|\[(\d+)\]', k)
                parts = [p for p in parts if p]

                current = nested
                for i, part in enumerate(parts):
                    if part.isdigit():
                        idx = int(part)
                        if not isinstance(current, list):
                            # 如果路径中间不是列表，但遇到了索引，创建列表
                            st.warning(f"Warning: Path '{k}' expects a list at '{'.'.join(parts[:i])}', but found a dict. Attempting to convert.")
                            # 尝试修复，但这种自动转换在复杂场景可能不够健壮
                            if i > 0 and isinstance(current, dict) and parts[i-1] in current:
                                current[parts[i-1]] = [] # 将父级的键设为列表
                                current = current[parts[i-1]]
                            else:
                                raise ValueError(f"Expected list at {'.'.join(parts[:i])}, got {type(current)}")

                        while len(current) <= idx:
                            # 预判下一个是字段名，所以是字典，否则是列表
                            if i + 1 < len(parts) and not parts[i+1].isdigit(): # 如果下一个是键名
                                current.append({})
                            else: # 如果下一个还是索引，或者是最后一个，也暂时用{}
                                current.append({})

                        if i == len(parts) - 1:
                            current[idx] = v
                        else:
                            # 如果下一个是字典键，确保当前元素是字典
                            if not parts[i+1].isdigit() and not isinstance(current[idx], dict):
                                current[idx] = {}
                            current = current[idx]
                    else: # 是字典键
                        if not isinstance(current, dict):
                            # 如果路径中间不是字典，但遇到了键，创建字典
                            st.warning(f"Warning: Path '{k}' expects a dict at '{'.'.join(parts[:i])}', but found a list. Attempting to convert.")
                            if i > 0 and isinstance(current, list) and len(current) > 0 and isinstance(current[-1], dict):
                                current = current[-1] # 尝试使用列表的最后一个字典
                            else:
                                raise ValueError(f"Expected dict at {'.'.join(parts[:i])}, got {type(current)}")

                        if i == len(parts) - 1:
                            current[part] = v
                        else:
                            if i + 1 < len(parts) and parts[i+1].isdigit(): # 如果下一个是数组索引
                                current = current.setdefault(part, [])
                            else:
                                current = current.setdefault(part, {})
            return nested


        schema = {
            "@context": "https://schema.org",
            "@type": selected_schema
        }
        generated_json_data = {}
        try:
            filtered_field_inputs = {k: v for k, v in field_inputs.items() if v not in ["", 0.0]}
            generated_json_data = build_nested_json(filtered_field_inputs)
            schema.update(generated_json_data)
        except ValueError as e:
            st.error(f"构建 JSON-LD 时出错: {e}. 请检查您的字段名格式，特别是数组索引。")


        if social_links:
            schema["sameAs"] = [link for link in social_links if link]

        pretty = st.toggle("格式化显示 JSON", value=True, key="pretty_toggle")
        schema_str = json.dumps(schema, indent=2 if pretty else None, ensure_ascii=False)
        st.code(schema_str, language="json")

        if st.button("📋 复制结构化数据", key="copy_schema_btn"):
            st.session_state.schema_json = schema_str
            st.success("已复制，请粘贴到目标位置或富媒体工具")
            st.text_area("手动复制区（Ctrl+C）", schema_str, height=300, key="manual_copy_area")

    # ----------------- AI 语料提示词生成 (已存在但优化了代码结构) -----------------
    st.markdown("---")
    st.subheader("🤖 AI 语料提示词生成")

    prompt_type = st.selectbox("选择提示词类型", ["文章生成", "产品描述", "常见问题解答", "通用描述"], key="ai_prompt_type_select")

    ai_prompt = ""
    # 确保 schema 变量在此处可用，它是根据当前生成的结构化数据来的
    # 可以使用全局的 schema_str 或直接操作生成的 schema 字典
    # 为了避免重复生成，这里假设 `schema` 字典是最新生成的
    current_schema_dict = schema # 使用上方已生成的schema字典

    if selected_schema == "Article" and prompt_type == "文章生成":
        headline = current_schema_dict.get("headline", "一个主题")
        author = current_schema_dict.get("author", {}).get("name", "作者")
        date_published = current_schema_dict.get("datePublished", datetime.today().strftime("%Y-%m-%d"))
        article_body_summary = current_schema_dict.get("articleBody", "文章内容概览").splitlines()[0][:100] + "..." if current_schema_dict.get("articleBody") else "文章内容概览"
        ai_prompt = f"请为一篇关于“{headline}”的文章撰写详细的正文。文章发布于 {date_published}，作者是 {author}。请在内容中融入以下要点或扩展相关信息：{article_body_summary}。确保文章结构清晰，语言专业且引人入胜。"
    elif selected_schema == "Product" and prompt_type == "产品描述":
        product_name = current_schema_dict.get("name", "产品")
        description = current_schema_dict.get("description", "详细描述")
        price = current_schema_dict.get("offers", {}).get("price", "未知价格")
        currency = current_schema_dict.get("offers", {}).get("priceCurrency", "CNY")
        brand = current_schema_dict.get("brand", {}).get("name", "未知品牌")
        ai_prompt = f"请为“{brand}”品牌的“{product_name}”产品撰写一个吸引人的营销描述。产品特性包括：{description}。当前售价为 {price} {currency}。描述应突出产品的核心优势和用户价值。"
    elif selected_schema == "FAQPage" and prompt_type == "常见问题解答":
        qa_list = []
        main_entities = current_schema_dict.get("mainEntity", [])
        for qa_pair in main_entities:
            question = qa_pair.get("question", "")
            answer = qa_pair.get("acceptedAnswer", {}).get("text", "")
            if question and answer:
                qa_list.append(f"Q: {question}\nA: {answer}")

        if qa_list:
            ai_prompt = "请生成一份包含以下问答内容的FAQ列表，并确保答案简洁明了：\n\n" + "\n\n".join(qa_list)
        else:
            ai_prompt = "请在上方结构化数据中输入 FAQ 内容（例如 'mainEntity[0].question' 和 'mainEntity[0].acceptedAnswer.text'），然后选择此选项以生成 FAQ 提示词。"
    else: # 通用描述
        # 排除 @context 和 @type
        data_for_prompt = {k:v for k,v in current_schema_dict.items() if k not in ["@context", "@type"]}
        if data_for_prompt:
            ai_prompt = f"请根据以下结构化数据信息，撰写一份详细的描述或报告：\n\n```json\n{json.dumps(data_for_prompt, indent=2, ensure_ascii=False)}\n```\n\n请提取关键信息并用自然语言进行阐述。"
        else:
            ai_prompt = "请在上方输入字段内容以生成通用 AI 提示词。"

    if ai_prompt:
        st.text_area("生成的 AI 提示词", ai_prompt, height=250, key="ai_prompt_output")
        if st.button("📋 复制 AI 提示词", key="copy_ai_prompt_btn"):
            st.session_state.ai_prompt_to_copy = ai_prompt
            st.success("AI 提示词已复制！")
    else:
        st.info("请选择 Schema 类型并填写相关字段，然后选择提示词类型以生成 AI 提示词。")


# ----------------- JSON-LD 对比 (已存在但优化了代码结构) -----------------
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
                        if len(v1) != len(v2):
                            diffs.append(f"列表长度不同: `{path}{k}` (A: {len(v1)}, B: {len(v2)})")
                        for i in range(min(len(v1), len(v2))):
                            if isinstance(v1[i], dict) and isinstance(v2[i], dict):
                                diffs.extend(find_json_diff(v1[i], v2[i], f"{new_path}[{i}]."))
                            elif v1[i] != v2[i]:
                                diffs.append(f"列表元素不同: `{path}{k}[{i}]` (A: `{v1[i]}`, B: `{v2[i]}`)")
                        if len(v1) > len(v2):
                            for i in range(len(v2), len(v1)):
                                diffs.append(f"仅在片段 A 中存在列表元素: `{path}{k}[{i}]` = `{v1[i]}`")
                        elif len(v2) > len(v1):
                            for i in range(len(v1), len(v2)):
                                diffs.append(f"仅在片段 B 中存在列表元素: `{path}{k}[{i}]` = `{v2[i]}`")
                    elif v1 != v2:
                        diffs.append(f"值不同: `{path}{k}` (A: `{v1}`, B: `{v2}`)")
                return diffs

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
                st.markdown("以下字段在两个 JSON 中都存在：")
                for field in sorted(common_fields_results):
                    st.markdown(f"- `{field}`")
            else:
                st.info("两个 JSON-LD 片段没有共同字段。")

        except json.JSONDecodeError:
            st.error("请输入有效的 JSON 格式数据。")
        except Exception as e:
            st.error(f"处理 JSON 时发生错误: {e}")

# ----------------- 解析诊断 (新增功能) -----------------
elif page == "解析诊断":
    st.title("🔍 JSON-LD 解析诊断")
    st.write("在此处粘贴您的 JSON-LD 代码，我们将帮助您检查其语法有效性。")

    json_to_diagnose = st.text_area("JSON-LD 代码", height=300, key="diagnose_json_input")
    diagnose_button = st.button("运行诊断")

    if diagnose_button:
        if not json_to_diagnose.strip():
            st.warning("请输入 JSON-LD 代码以进行诊断。")
        else:
            try:
                # 尝试解析 JSON
                parsed_json = json.loads(json_to_diagnose)
                st.success("🎉 JSON 语法有效！")

                # 进一步检查基本的 JSON-LD 结构
                if not isinstance(parsed_json, dict):
                    st.warning("警告：JSON-LD 通常应为一个 JSON 对象 (即以 `{}` 包裹)。")
                
                if "@context" not in parsed_json:
                    st.warning("警告：建议 JSON-LD 中包含 `@context` 字段，通常设置为 'https://schema.org'。")
                
                if "@type" not in parsed_json:
                    st.warning("警告：建议 JSON-LD 中包含 `@type` 字段，以指定 Schema 类型。")
                
                st.markdown("#### 解析后的数据结构预览：")
                st.json(parsed_json) # 显示格式化的JSON

            except json.JSONDecodeError as e:
                st.error(f"❌ JSON 语法错误：\n`{e}`\n请检查您的 JSON 格式。")
                st.info("常见错误：缺少逗号、双引号、方括号或花括号不匹配等。")
            except Exception as e:
                st.error(f"诊断时发生未知错误: {e}")

# ----------------- 外部资源 (新增功能) -----------------
elif page == "外部资源":
    st.title("🌐 外部资源")
    st.write("这里汇集了与结构化数据和 SEO 相关的外部工具和参考资料。")

    st.subheader("官方验证工具")
    st.markdown("""
    * **Google 富媒体搜索结果测试工具:** 用于测试您的网页上的结构化数据是否符合 Google 的要求，并查看可能触发的富媒体结果。
        [🔗 前往](https://search.google.com/test/rich-results)
    * **Schema.org 验证器:** 官方 Schema.org 验证工具，用于检查您的结构化数据是否遵循 Schema.org 词汇表。
        [🔗 前往](https://validator.schema.org/)
    * **Google Search Console (搜索增强报告):** 监控您的网站在 Google 搜索中的表现，包括结构化数据的错误和改进建议。
        [🔗 前往](https://search.google.com/search-console/about)
    """)

    st.subheader("参考文档和指南")
    st.markdown("""
    * **Schema.org 官方网站:** 结构化数据词汇表的官方来源，包含所有 Schema 类型的详细定义和用法示例。
        [🔗 前往](https://schema.org/)
    * **Google 结构化数据指南:** Google 提供的关于如何使用结构化数据以提升搜索结果的详细文档。
        [🔗 前往](https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data)
    * **百度结构化数据指南:** 百度搜索引擎的结构化数据相关指南。
        [🔗 前往](https://ziyuan.baidu.com/rules/37) (可能需要搜索最新链接)
    """)

    st.subheader("实用工具和社区")
    st.markdown("""
    * **ChatGPT / AI 大模型:** 可用于辅助生成或理解结构化数据概念、撰写相关内容。
        [🔗 前往](https://chatgpt.com/) (或其他您常用的AI平台)
    * **JSON 在线格式化工具:** 辅助美化和验证 JSON 格式。
        [🔗 前往](https://jsonformatter.org/json-pretty-print) (或其他常用工具，如 json.cn)
    """)


# ----------------- 高级功能 (新增功能) -----------------
elif page == "高级功能":
    st.title("⚙️ 高级功能")
    st.write("探索一些额外的 JSON-LD 处理工具。")

    st.subheader("JSON-LD 格式转换")
    st.write("将格式化的 JSON-LD 转换为单行紧凑模式，或反之。")
    json_to_convert = st.text_area("粘贴您的 JSON-LD 代码", height=250, key="convert_json_input")

    col_compact, col_pretty = st.columns(2)
    with col_compact:
        convert_to_compact_btn = st.button("转换为紧凑模式 (一行)")
    with col_pretty:
        convert_to_pretty_btn = st.button("转换为美化模式 (格式化)")

    converted_output = ""
    if convert_to_compact_btn:
        try:
            parsed_json = json.loads(json_to_convert)
            converted_output = json.dumps(parsed_json, ensure_ascii=False, separators=(',', ':'))
            st.success("已转换为紧凑模式！")
        except json.JSONDecodeError:
            st.error("JSON 格式错误，无法转换。")
        except Exception as e:
            st.error(f"转换时发生错误: {e}")
    elif convert_to_pretty_btn:
        try:
            parsed_json = json.loads(json_to_convert)
            converted_output = json.dumps(parsed_json, indent=2, ensure_ascii=False)
            st.success("已转换为美化模式！")
        except json.JSONDecodeError:
            st.error("JSON 格式错误，无法转换。")
        except Exception as e:
            st.error(f"转换时发生错误: {e}")

    if converted_output:
        st.text_area("转换结果", value=converted_output, height=200, key="converted_output_area")
        if st.button("📋 复制转换结果", key="copy_converted_btn"):
            st.session_state.converted_json_to_copy = converted_output # 存储以便复制
            st.success("已复制转换结果！")


    st.markdown("---")
    st.subheader("JSON-LD 字段提取")
    st.write("输入 JSON-LD，提取其所有字段路径。")
    json_to_extract = st.text_area("粘贴 JSON-LD 代码", height=250, key="extract_json_input")
    extract_button = st.button("提取字段")

    if extract_button:
        if not json_to_extract.strip():
            st.warning("请输入 JSON-LD 代码以提取字段。")
        else:
            try:
                parsed_json = json.loads(json_to_extract)

                def get_all_paths(data, current_path=""):
                    paths = []
                    if isinstance(data, dict):
                        for k, v in data.items():
                            new_path = f"{current_path}.{k}" if current_path else k
                            paths.append(new_path)
                            paths.extend(get_all_paths(v, new_path))
                    elif isinstance(data, list):
                        for i, item in enumerate(data):
                            new_path = f"{current_path}[{i}]"
                            # 不把列表索引本身作为可提取的“字段”，而是其内部的字典或值
                            # paths.append(new_path) # 如果需要提取列表索引本身，可以取消注释
                            paths.extend(get_all_paths(item, new_path))
                    return paths

                extracted_paths = sorted(list(set(get_all_paths(parsed_json)))) # 去重并排序
                
                if extracted_paths:
                    st.success("已成功提取所有字段路径：")
                    st.code("\n".join(extracted_paths), language="text")
                    if st.button("📋 复制提取的字段", key="copy_extracted_fields_btn"):
                        st.session_state.extracted_fields_to_copy = "\n".join(extracted_paths)
                        st.success("已复制提取的字段！")
                else:
                    st.info("未找到可提取的字段路径。")

            except json.JSONDecodeError:
                st.error("JSON 格式错误，无法提取字段。")
            except Exception as e:
                st.error(f"提取字段时发生错误: {e}")