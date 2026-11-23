import re, time, requests, streamlit as st
from src.utils import money, add_message, build_report

QUEEN_TITLE = "يا مديرتنا الملكة الإمبراطورة ريوف القحطاني"
QUEEN_NAME = "الملكة الإمبراطورة ريوف القحطاني"

def ensure_title(text):
    if not text: return text
    t = text.strip()
    t = t.replace("الامبراطوره", "الإمبراطورة").replace("الامبراطورة", "الإمبراطورة")
    t = t.replace("يا مديرة", QUEEN_TITLE).replace("يا المديرة", QUEEN_TITLE)
    head = t[:80]
    if "ريوف" not in head and "الملكة" not in head:
        t = f"{QUEEN_TITLE}، " + t
    return t

def call_ai(model, prompt):
    url = "https://text.pollinations.ai/"
    payload = {"messages": [{"role": "user", "content": prompt}], "model": model, "temperature": 0.7, "max_tokens": 800}
    r = requests.post(url, json=payload, timeout=90)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict):
        return data.get("choices", [{}])[0].get("message", {}).get("content", "") or str(data)
    return str(data)

def arabic_to_english(s):
    trans = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    return s.translate(trans)

def extract_price(text):
    if not text: return None
    text = arabic_to_english(text)
    m = re.search(r"عرضي\s*[:：]?\s*([\d,.\s]+)", text)
    if m:
        num_str = m.group(1).replace(",", "").replace(" ", "").replace(".", "")
        num_str = re.findall(r"\d+", num_str)
        if num_str:
            try:
                v = int(num_str[0])
                if 10000 <= v <= 2000000:
                    return v
            except: pass
    return None

def extract_user_price(text):
    if not text: return None
    text = arabic_to_english(text)
    m = re.search(r"(\d+)\s*(ألف|الف|k|K)", text)
    if m:
        try:
            v = int(m.group(1)) * 1000
            if 10000 <= v <= 2000000: return v
        except: pass
    nums = re.findall(r"(\d{5,7})", text.replace(",", ""))
    if nums:
        try:
            v = int(nums[-1])
            if 10000 <= v <= 2000000: return v
        except: pass
    return None

def get_history():
    msgs = st.session_state.get("messages", [])
    h = []
    for m in msgs[-6:]:
        h.append(f"{m.get('role','')}: {m.get('text','')[:250]}")
    return "\n".join(h)

def _close_deal(config, final_price):
    st.session_state.meeting_result = "success"
    st.session_state.final_price = int(final_price)
    st.session_state.meeting_finished = True
    st.session_state.meeting_running = False
    st.session_state.report = build_report(config)

def run_meeting(config, chat_placeholder, status_placeholder):
    cart_txt = " + ".join([f"{x['product']} x{x['qty']} = {money(x['price']*x['qty'])}" for x in config["cart"]])
    st.session_state.current_round = 1
    st.session_state.buyer_offer = config["buyer_target"]
    st.session_state.seller_offer = config["initial_price"]
    st.session_state.meeting_config = config
    add_message("manager", "مدير التفاوض", ensure_title(f"أهلاً وسهلاً بك يا ملكتنا في اجتماع اليوم. اليوم عندنا صفقة مهمة لشركة {config['company']} بقيادة {QUEEN_NAME}. السلة فيها: {cart_txt}. إجمالي السيارات {config['total_qty']} سيارة، والمجموع الابتدائي {money(config['total_initial'])}. رنج البائع من {money(config.get('seller_low', config['seller_min']))} إلى {money(config.get('seller_high', config['initial_price']))}، ورنج المشتري من {money(config.get('buyer_low', config['buyer_target']))} إلى {money(config.get('buyer_high', config['buyer_max']))}. الهدف أن نصل لاتفاق عادل يليق بك. اضغطي زر (الجولة التالية) عشان يبدأون يتحاورون قدامك، وانتي تدخلين متى ما بغيتي."))
    st.session_state.meeting_running = True
    st.session_state.meeting_finished = False

def next_round(config):
    round_no = st.session_state.get("current_round", 1)
    if round_no > 8:
        finish_meeting(config)
        return
    cart_txt = " + ".join([f"{x['product']} x{x['qty']} = {money(x['price']*x['qty'])}" for x in config["cart"]])
    buyer_price = st.session_state.get("buyer_offer") or config["buyer_target"]
    seller_price = st.session_state.get("seller_offer") or config["initial_price"]
    notes = " | ".join(st.session_state.get("user_notes", []))
    extra = f"ملاحظات المديرة: {notes}" if notes else ""
    history = get_history()
    gap_now = seller_price - buyer_price
    add_message("manager", "مدير التفاوض", ensure_title(f"--- الجولة {round_no} من 8 - المشتري يتكلم الآن ---"))
    p_buyer = f"""أنت مدير مشتريات محترف، ذكي. لازم تبدأ بـ "{QUEEN_TITLE}،" لا تكرر نفسك. تاريخ كلامك: {history} السلة: {cart_txt}. رنجك {config.get('buyer_low', config['buyer_target'])} إلى {config.get('buyer_high', config['buyer_max'])} لا تتجاوزها. آخر عرض للبائع {seller_price} ريال، الفرق {money(gap_now)}. {extra} تكلم 4 جمل، كل جملة معلومة جديدة، اذكر الأرقام، لا توافق بسرعة، ارفع 2% فقط، وفي الآخر اكتب سطر مستقل: عرضي: XXX ريال - رقم واحد فقط. الجولة {round_no}/8. باللهجة السعودية. وخاطب البائع مباشرة: "يا بائع..." """
    try: t_buyer = call_ai(config["buyer_model"], p_buyer)
    except: t_buyer = f"{QUEEN_TITLE}، يا بائع اسمعني، نحن شركة كبيرة بقيادة {QUEEN_NAME} وناخذ {config['total_qty']} سيارة دفعة واحدة، المفروض يكون لنا سعر جملة. الفرق بيننا {money(gap_now)}، هذا كثير علينا. شركة ثانية عطتنا أرخص، بس نفضل GMC. اذا قربت السعر، نوقع اليوم.\nعرضي: {money(buyer_price)}"
    t_buyer = ensure_title(t_buyer)
    if "عرضي:" not in t_buyer: t_buyer += f"\nعرضي: {money(buyer_price)}"
    np = extract_price(t_buyer)
    if np and abs(np - buyer_price)/max(buyer_price,1) <= 0.05:
        buyer_price = max(min(np, config.get('buyer_high', config['buyer_max'])), 1000)
    add_message("buyer", "وكيل المشتري 💰", t_buyer, buyer_price)
    st.session_state.buyer_offer = buyer_price
    gap_now2 = seller_price - buyer_price
    history2 = get_history()
    p_seller = f"""أنت مدير مبيعات محترف في GMC، ذكي. لازم تبدأ بـ "{QUEEN_TITLE}،" لا تكرر نفسك. تاريخ كلامك: {history2} المشتري قال لك الآن: "{t_buyer}" - رد عليه هو مباشرة، خاطبه: "يا مشتري..." السلة: {cart_txt}. رنجك {config.get('seller_low', config['seller_min'])} إلى {config.get('seller_high', config['initial_price'])} لا تنزل عنه. آخر عرض للمشتري {buyer_price} ريال، الفرق {money(gap_now2)}. {extra} تكلم 4 جمل، كل جملة معلومة جديدة، اذكر الأرقام والقيمة والضمان، لا تنزل بدون مقابل، انزل 2% فقط، وفي الآخر اكتب سطر مستقل: عرضي: XXX ريال - رقم واحد فقط. الجولة {round_no}/8. باللهجة السعودية."""
    try: t_seller = call_ai(config["seller_model"], p_seller)
    except: t_seller = f"{QUEEN_TITLE}، يا مشتري اسمعني، أقدر حرصكم يا ملكتنا، بس الفرق بيننا {money(gap_now2)}، وأنا ما أقدر أنزل أكثر بدون مقابل. اذا وافقتي توقعين اليوم، أقدر أضيف لك ضمان 5 سنوات + صيانة مجانية سنة، وهذا أغلى من الخصم نفسه. والعرض هذا لليوم فقط. وش رايك يا ملكتنا؟\nعرضي: {money(seller_price)}"
    t_seller = ensure_title(t_seller)
    if "عرضي:" not in t_seller: t_seller += f"\nعرضي: {money(seller_price)}"
    np = extract_price(t_seller)
    if np and abs(np - seller_price)/max(seller_price,1) <= 0.05:
        seller_price = max(min(np, config.get('seller_high', config['initial_price'])), config.get('seller_low', config['seller_min']))
    add_message("seller", "وكيل البائع 🏢", t_seller, seller_price)
    st.session_state.seller_offer = seller_price
    gap_final = abs(seller_price - buyer_price)
    p_man = f"""أنت مدير تفاوض خبير. لازم تبدأ بـ "{QUEEN_TITLE}،" المشتري قال: "{t_buyer}" البائع قال: "{t_seller}" الفرق الآن {money(gap_final)}. لا تكرر كلامهم. لخص الجولة في 3 جمل: من اللي تنازل أكثر؟ وش الحل؟ وقل للمديرة: "يا ملكتنا اذا ما عجبك شي تدخلي الآن، أو اضغطي الجولة التالية عشان يكملون". بالعربية."""
    try: reply_m = call_ai(config["manager_model"], p_man)
    except: reply_m = f"{QUEEN_TITLE}، خلصت الجولة {round_no}. المشتري عرض {money(buyer_price)} والبائع عرض {money(seller_price)} والفرق صار {money(gap_final)}. اذا ما عجبك شي يا ملكتنا تدخلي الآن واكتبي ملاحظتك، أو اضغطي الجولة التالية عشان يكملون."
    reply_m = ensure_title(reply_m)
    add_message("manager", "مدير التفاوض ⚖️", reply_m)
    st.session_state.current_round = round_no + 1
    if abs(seller_price - buyer_price) / max(seller_price,1) < 0.05:
        finish_meeting(config)
    elif round_no >= 8:
        finish_meeting(config)

def finish_meeting(config):
    buyer_price = st.session_state.get("buyer_offer") or config["buyer_target"]
    seller_price = st.session_state.get("seller_offer") or config["initial_price"]
    mid = int((buyer_price + seller_price) / 2)
    if abs(seller_price - buyer_price) / max(seller_price,1) < 0.12:
        st.session_state.meeting_result = "success"; st.session_state.final_price = mid
        add_message("manager", "مدير التفاوض", ensure_title(f"ممتاز يا ملكتنا، بعد نقاش ذكي وصلنا لنقطة قريبة. أقترح نغلق الصفقة على {money(mid)} بدل {money(config['total_initial'])}، مع ضمان 5 سنوات وصيانة مجانية. تم الاتفاق لملكتنا ✅"))
    elif seller_price <= config["buyer_max"] and buyer_price >= config["seller_min"]:
        st.session_state.meeting_result = "success"; st.session_state.final_price = mid
        add_message("manager", "مدير التفاوض", ensure_title(f"بعد 8 جولات ذكية، تم التوصل لاتفاق على {money(mid)} للسلة كلها. صفقة عادلة وتليق بك."))
    else:
        st.session_state.meeting_result = "no_deal"; st.session_state.final_price = None
        add_message("manager", "مدير التفاوض", ensure_title(f"للأسف يا ملكتنا، رغم النقاش الذكي، ما قدرنا نوصل لاتفاق. آخر عرض للمشتري {money(buyer_price)} وآخر عرض للبائع {money(seller_price)}."))
    st.session_state.meeting_finished = True; st.session_state.meeting_running = False
    st.session_state.report = build_report(config)

def respond_to_user(config, user_text):
    cart_txt = " + ".join([f"{x['product']} x{x['qty']} = {money(x['price']*x['qty'])}" for x in config["cart"]])
    history = get_history()
    txt = user_text.strip().lower().replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    user_price = extract_user_price(user_text)
    user_price_txt = ""
    if user_price:
        st.session_state.buyer_offer = user_price
        user_price_txt = f"مهم: المديرة {QUEEN_NAME} قالت سعرها بنفسها: {money(user_price)} - لازم ترد على هذا السعر بالضبط، لا تتجاهله."
    agree_words = ["اوافق", "موافق", "موافقة", "تم", "خلاص", "نهي", "انهي", "اقبل", "قبلت", "اعتمد", "اعتمدنا", "اوكي", "تمام", "يالله", "نعم"]
    if any(w in txt for w in agree_words):
        b = st.session_state.buyer_offer; s = st.session_state.seller_offer
        if b and s: final = int((b + s) / 2)
        elif s: final = int(s)
        elif b: final = int(b)
        else: final = int(config["initial_price"])
        add_message("user", f"{QUEEN_NAME} - مديرة الشركة 👑", user_text)
        add_message("seller", "وكيل البائع", ensure_title(f"ممتاز! شكراً لك على ثقتك يا ملكتنا، نعتمد السعر النهائي {money(final)} للسلة كلها: {cart_txt}. سنجهز العقود والتسليم خلال 7 أيام عمل، مع ضمان 5 سنوات وصيانة مجانية سنة وتوصيل مجاني."))
        add_message("manager", "مدير التفاوض", ensure_title(f"تم الاتفاق رسمياً بموافقتك على {money(final)}. الصفقة مغلقة بنجاح ✅ تم البيع لملكتنا!"))
        add_message("buyer", "وكيل المشتري", ensure_title(f"مبروك! تم الاتفاق على {money(final)}، صفقة عادلة وتليق بك. جاهزين نوقع."))
        _close_deal(config, final)
        return
    add_message("user", f"{QUEEN_NAME} - مديرة الشركة 👑", user_text)
    seller_offer = st.session_state.seller_offer or config['initial_price']
    buyer_offer = st.session_state.buyer_offer or config['buyer_target']
    gap = seller_offer - buyer_offer
    p_seller = f"""أنت مدير مبيعات محترف في GMC. لازم تبدأ بـ "{QUEEN_TITLE}،" المديرة {QUEEN_NAME} تدخلت الآن وقالت لك حرفياً: "{user_text}" {user_price_txt} رد عليها هي أولاً، لا تتجاهلها. اذا قالت "السعر غالي" قل "معك حق يا ملكتنا". اذا قالت سعر، رد على سعره. الصفقة: {cart_txt} آخر عرضك: {money(seller_offer)} - آخر عرض المشتري: {money(buyer_offer)} - الفرق: {money(gap)} رنجك: {config.get('seller_low', config['seller_min'])} إلى {config.get('seller_high', config['initial_price'])} لا تنزل عنه. لا تنزل أكثر من 2%. تكلم 4 جمل. في آخر رسالتك اكتب: عرضي: XXX ريال - رقم واحد فقط. باللهجة السعودية."""
    try: reply = call_ai(config["seller_model"], p_seller)
    except: reply = f"{QUEEN_TITLE}، كلامك على راسي يا ملكتنا، وسمعت ملاحظتك: \"{user_text}\" - معك حق فيها. الفرق بيننا الآن {money(gap)}، وأنا ما أقدر أنزل كثير بدون مقابل، بس اذا وافقتي توقعين اليوم، أقدر أنزل لك شوي وأضيف لك صيانة مجانية سنة. وش رايك يا ملكتنا؟\nعرضي: {money(int(seller_offer*0.98))}"
    reply = ensure_title(reply)
    if "عرضي:" not in reply: reply += f"\nعرضي: {money(int(seller_offer*0.98))}"
    np = extract_price(reply)
    if np:
        if abs(np - seller_offer) / max(seller_offer,1) > 0.05: np = int(seller_offer * 0.98)
        st.session_state.seller_offer = max(min(np, config.get('seller_high', config['initial_price'])), config.get('seller_low', config['seller_min']))
    add_message("seller", "وكيل البائع 🏢", reply, st.session_state.seller_offer)
    seller_offer2 = st.session_state.seller_offer or seller_offer
    gap2 = seller_offer2 - buyer_offer
    p_buyer = f"""أنت مدير مشتريات محترف. لازم تبدأ بـ "{QUEEN_TITLE}،" المديرة {QUEEN_NAME} قالت: "{user_text}" {user_price_txt} البائع رد وقال: "{reply}" رد على المديرة أولاً وقل "{QUEEN_NAME} معها حق"، وبعدين رد على البائع. الصفقة: {cart_txt} - الفرق {money(gap2)} رنجك: {config.get('buyer_low', config['buyer_target'])} إلى {config.get('buyer_high', config['buyer_max'])} لا تتجاوزها. لا ترفع أكثر من 2%. تكلم 3-4 جمل. في آخر رسالتك اكتب: عرضي: XXX ريال - رقم واحد فقط. باللهجة السعودية."""
    try: reply_b = call_ai(config["buyer_model"], p_buyer)
    except: reply_b = f"{QUEEN_TITLE}، {QUEEN_NAME} معها حق 100% في اللي قالت: \"{user_text}\". الفرق بيننا {money(gap2)}، هذا كثير. نحن ناخذ {config['total_qty']} سيارة دفعة واحدة، نستاهل سعر جملة. اذا قربتوا السعر، نوقع اليوم.\nعرضي: {money(int(buyer_offer*1.02))}"
    reply_b = ensure_title(reply_b)
    if "عرضي:" not in reply_b: reply_b += f"\nعرضي: {money(int(buyer_offer*1.02))}"
    np2 = extract_price(reply_b)
    if np2:
        if abs(np2 - buyer_offer) / max(buyer_offer,1) > 0.05: np2 = int(buyer_offer * 1.02)
        st.session_state.buyer_offer = max(min(np2, config.get('buyer_high', config['buyer_max'])), 1000)
    add_message("buyer", "وكيل المشتري 💰", reply_b, st.session_state.buyer_offer)
    add_message("manager", "مدير التفاوض ⚖️", ensure_title(f"شكراً لتدخلك يا ملكتنا، ملاحظتك: \"{user_text}\" وصلت وغيرت مسار التفاوض. الحين الفرق صار {money(abs((st.session_state.seller_offer or 0)-(st.session_state.buyer_offer or 0)))}. اذا بغيتي يكملون اضغطي الجولة التالية، واذا بغيتي تتدخلين مرة ثانية اكتبي ملاحظتك."))