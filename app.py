import streamlit as st
import html, base64
from pathlib import Path
from src.utils import money, add_message, render_chat
from src.meeting import run_meeting, respond_to_user, next_round, finish_meeting

st.set_page_config(page_title="التفاوض الذكي | GMC", page_icon="👑", layout="wide", initial_sidebar_state="collapsed")
BASE_DIR = Path(__file__).parent
IMAGE_PATH = BASE_DIR / "assets" / "gmc-truck.jpg"
CSS_PATH = BASE_DIR / "styles" / "style.css"
TRUCK_IMAGE = base64.b64encode(IMAGE_PATH.read_bytes()).decode("utf-8") if IMAGE_PATH.exists() else ""

defaults = {"messages": [], "cart": [], "meeting_running": False, "meeting_finished": False, "meeting_result": None, "final_price": None, "buyer_offer": None, "seller_offer": None, "report": "", "meeting_error": None, "user_notes": [], "current_round": 1}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

css = CSS_PATH.read_text(encoding="utf-8") if CSS_PATH.exists() else ""
if TRUCK_IMAGE:
    css += f"\n.hero {{ background: url(\"data:image/jpeg;base64,{TRUCK_IMAGE}\") center / cover no-repeat !important; position: relative; overflow:hidden; }}\n.hero::before {{ content:''; position:absolute; inset:0; background: linear-gradient(90deg, rgba(5,12,20,.10) 0%, rgba(5,12,20,.55) 55%, rgba(8,14,22,.95) 100%); }}\n.hero-content {{ position:relative; z-index:2; }}"
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

st.markdown("""<div class="topbar"><div class="nav-text">👑 مركز التفاوض - الملكة الإمبراطورة ريوف القحطاني</div><div class="topbar-right"><div><div class="logo">GMC</div><div class="small-muted">SMART NEGOTIATION CENTER</div></div></div></div>""", unsafe_allow_html=True)
st.markdown("""<div class="hero"><div class="hero-content"><h1>التفاوض الذكي</h1><p>أهلاً بمديرتنا الملكة الإمبراطورة ريوف القحطاني 👑<br>اختاري سياراتك، حددي الرنج، وشاركي بنفسك في التفاوض</p><div class="hero-tag">تفاوض ذكي · سعر أفضل · لملكتنا</div><div class="hero-label">GMC - SMART NEGOTIATION</div></div></div>""", unsafe_allow_html=True)

st.markdown('<div class="section-heading">🛒 سلة المشتريات - اختاري أكثر من منتج</div>', unsafe_allow_html=True)
CAR_PRICES = {"GMC Sierra Denali": 257000, "GMC Sierra AT4": 230000, "GMC Yukon Denali": 320000, "GMC Yukon AT4": 290000, "GMC Terrain Denali": 165000, "GMC Acadia Denali": 185000, "GMC Hummer EV": 480000, "GMC Canyon AT4": 195000}
c1,c2,c3,c4 = st.columns([2.2,1,1,1])
with c1: sel_car = st.selectbox("اختاري السيارة", list(CAR_PRICES.keys()), format_func=lambda x: f"{x} - {CAR_PRICES[x]:,} ريال")
with c2: sel_qty = st.number_input("العدد", min_value=1, value=1, step=1)
with c3: sel_price = st.number_input("سعر الحبة", min_value=1, value=CAR_PRICES[sel_car], step=1000)
with c4:
    st.write(""); st.write("")
    if st.button("➕ أضف للسلة", use_container_width=True):
        st.session_state.cart.append({"product": sel_car, "qty": int(sel_qty), "price": int(sel_price)}); st.rerun()

if st.session_state.cart:
    st.markdown('<div class="cart-box">', unsafe_allow_html=True)
    total_cart = 0; total_qty = 0
    for i, item in enumerate(st.session_state.cart):
        sub = item["price"] * item["qty"]; total_cart += sub; total_qty += item["qty"]
        cc1,cc2,cc3,cc4,cc5 = st.columns([2.2,1,1,1,0.6])
        with cc1: st.markdown(f"**{item['product']}**")
        with cc2: st.markdown(f"{item['price']:,} ريال")
        with cc3: st.markdown(f"العدد: {item['qty']}")
        with cc4: st.markdown(f"**{sub:,} ريال**")
        with cc5:
            if st.button("🗑️", key=f"del_{i}"): st.session_state.cart.pop(i); st.rerun()
        st.markdown("<hr style='margin:4px 0;border-color:#22344a'>", unsafe_allow_html=True)
    st.markdown(f"""<div class="cart-total">إجمالي السلة: {total_qty} سيارة &nbsp; | &nbsp; المجموع: <span style="color:#f3d69e">{total_cart:,} ريال</span></div>""", unsafe_allow_html=True)
    if st.button("🗑️ مسح السلة كلها"): st.session_state.cart = []; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("السلة فاضية يا ملكتنا - اختاري سيارة واضغطي أضف للسلة.")
    total_cart = 0; total_qty = 0

st.markdown('<div class="section-heading">إعداد التفاوض - الرنج</div>', unsafe_allow_html=True)
with st.expander("إعدادات الاجتماع والرنج", expanded=True):
    e1,e2 = st.columns(2)
    with e1:
        company = st.selectbox("اسم الشركة", ["شركة مصنع ديانا الطبية","شركة الجميح للسيارات","شركة التوكيلات العالمية","شركة عبداللطيف جميل","شركة نجيب أوتو"])
        st.markdown("**🏢 رنج البائع - GMC**")
        st.caption("البائع يتحرك داخل هذا الرنج فقط")
        s1,s2 = st.columns(2)
        with s1:
            seller_low = st.number_input("من - أقل سعر للبائع", min_value=10000, max_value=2000000, value=int(total_cart*0.8) if total_cart else 100000, step=5000, key="seller_low_input", format="%d")
        with s2:
            seller_high = st.number_input("إلى - أعلى سعر للبائع", min_value=10000, max_value=2000000, value=int(total_cart) if total_cart else 200000, step=5000, key="seller_high_input", format="%d")
        st.success(f"البائع: من {seller_low:,} إلى {seller_high:,} ريال")
        buyer_model = st.selectbox("نموذج وكيل المشتري", ["openai","mistral"])
        seller_model = st.selectbox("نموذج وكيل البائع", ["mistral","openai"])
    with e2:
        st.markdown("**💰 رنج المشتري - شركتك**")
        st.caption("هذا رنجك انتي يا ملكتنا")
        b1,b2 = st.columns(2)
        with b1:
            buyer_low = st.number_input("من - أقل سعر لك", min_value=10000, max_value=2000000, value=int(total_cart*0.7) if total_cart else 80000, step=5000, key="buyer_low_input", format="%d")
        with b2:
            buyer_high = st.number_input("إلى - أعلى سعر لك", min_value=10000, max_value=2000000, value=int(total_cart*0.85) if total_cart else 150000, step=5000, key="buyer_high_input", format="%d")
        st.info(f"انتي: من {buyer_low:,} إلى {buyer_high:,} ريال")
        manager_model = st.selectbox("نموذج مدير التفاوض", ["openai","mistral"])
    st.caption("اكتبي الأرقام في المربعات - كل مربع لحاله - ما عاد فيه أرقام تدخل في بعض.")

config = {"company": company.strip(), "cart": list(st.session_state.cart), "total_initial": int(total_cart), "total_qty": int(total_qty), "product": " + ".join([f"{x['product']} x{x['qty']}" for x in st.session_state.cart]) if st.session_state.cart else "لا يوجد", "initial_price": int(seller_high), "seller_min": int(seller_low), "seller_low": int(seller_low), "seller_high": int(seller_high), "buyer_target": int(buyer_low), "buyer_max": int(buyer_high), "buyer_low": int(buyer_low), "buyer_high": int(buyer_high), "buyer_model": buyer_model, "seller_model": seller_model, "manager_model": manager_model, "language": "Arabic"}
valid = len(st.session_state.cart) > 0
err = None
if not valid: err = "أضيفي سيارة واحدة على الأقل للسلة قبل بدء الاجتماع يا ملكتنا."
elif buyer_low > buyer_high: valid=False; err="رنج المشتري غلط - مربع (من) أكبر من (إلى)."
elif seller_low > seller_high: valid=False; err="رنج البائع غلط - مربع (من) أكبر من (إلى)."
if err: st.warning(err)

st.markdown('<div class="section-heading">غرفة الاجتماع المباشر - شاركي معهم يا ملكتنا</div>', unsafe_allow_html=True)
left,center,right = st.columns([1.2,3.2,1.25], gap="medium")
with left:
    st.markdown("""<div class="panel"><div class="panel-header"><span>معلومات الصفقة</span><span>👑</span></div>""", unsafe_allow_html=True)
    if TRUCK_IMAGE: st.markdown(f'<img class="deal-image" src="data:image/jpeg;base64,{TRUCK_IMAGE}">', unsafe_allow_html=True)
    cart_html = "".join([f'<div class="deal-row"><span>{html.escape(x["product"])} x{x["qty"]}</span><strong>{money(x["price"]*x["qty"])}</strong></div>' for x in st.session_state.cart])
    st.markdown(f"""<div class="deal-body"><div style="font-size:15px;font-weight:900;margin-bottom:8px;">👑 الملكة الإمبراطورة ريوف القحطاني<br>{html.escape(company)}</div>{cart_html}<div class="deal-row"><span>إجمالي السيارات</span><strong>{total_qty} سيارة</strong></div><div class="deal-row"><span>المجموع الكلي</span><strong style="color:#f3d69e;font-size:15px;">{money(total_cart)}</strong></div><div class="deal-row"><span>رنج البائع</span><strong>{seller_low:,} - {seller_high:,} ريال</strong></div><div class="deal-row"><span>رنج المشتري</span><strong>{buyer_low:,} - {buyer_high:,} ريال</strong></div></div></div>""", unsafe_allow_html=True)
    st.markdown("""<div class="status-box"><div class="small-muted">حالة الاجتماع</div>""", unsafe_allow_html=True)
    if st.session_state.meeting_running: st.markdown('<div class="status-value">● الاجتماع جارٍ</div>', unsafe_allow_html=True)
    elif st.session_state.meeting_finished: st.markdown('<div class="status-value">● انتهى الاجتماع</div>', unsafe_allow_html=True)
    else: st.markdown('<div class="status-value">● بانتظار البدء</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with center:
    st.markdown("""<div class="panel"><div class="panel-header"><span>غرفة المحادثة والتفاوض</span><span style="color:#48c99a;font-size:10px;">● LIVE ROOM 👑</span></div>""", unsafe_allow_html=True)
    chat_placeholder = st.empty()
    with chat_placeholder.container(): render_chat(st.empty())
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div class="user-participate">👑 شاركي في التفاوض يا الملكة الإمبراطورة ريوف القحطاني</div>', unsafe_allow_html=True)
    st.caption("اكتبي ملاحظتك هنا - بيوقفون ويردون عليكي انتي أولاً")
    user_msg = st.text_input("اكتبي رسالتك للوكلاء...", placeholder="اكتبي رسالتك يا ملكتنا ريوف... مثال: السعر غالي، ابيها بـ 200 ألف...", label_visibility="collapsed", key="user_input")
    ub1,ub2,ub3 = st.columns(3)
    with ub1:
        if st.button("📩 أرسل رسالتي - أتدخل", use_container_width=True, disabled=not user_msg.strip()):
            st.session_state.user_notes.append(user_msg.strip())
            try: respond_to_user(config, user_msg.strip())
            except Exception as e: add_message("manager","مدير التفاوض", f"تم استلام ملاحظتك يا ملكتنا: {user_msg.strip()}")
            st.rerun()
    with ub2:
        if st.button("💸 السعر غالي", use_container_width=True):
            txt = "السعر غالي مرة، نبي خصم أكبر"
            st.session_state.user_notes.append(txt)
            try: respond_to_user(config, txt)
            except: pass
            st.rerun()
    with ub3:
        if st.button("✅ أوافق - تم البيع", use_container_width=True):
            txt = "أوافق"
            st.session_state.user_notes.append(txt)
            try: respond_to_user(config, txt)
            except: pass
            st.rerun()

with right:
    st.markdown("""<div class="panel"><div class="panel-header"><span>متابعة العروض</span><span>↗</span></div><div class="deal-body">""", unsafe_allow_html=True)
    st.markdown(f"""<div class="deal-row"><span>آخر عرض للمشتري</span><strong style="color:#61b5ee">{money(st.session_state.buyer_offer) if st.session_state.buyer_offer else "—"}</strong></div><div class="deal-row"><span>آخر عرض للبائع</span><strong style="color:#d8b477">{money(st.session_state.seller_offer) if st.session_state.seller_offer else "—"}</strong></div></div></div>""", unsafe_allow_html=True)
    st.markdown("""<div class="result-box"><h4>🏆 النتيجة النهائية</h4>""", unsafe_allow_html=True)
    if st.session_state.meeting_result=="success": st.markdown(f'<div class="result-price">{money(st.session_state.final_price)}</div><div class="small-muted">تم تأكيد الاتفاق من الطرفين</div>', unsafe_allow_html=True)
    elif st.session_state.meeting_result=="no_deal": st.markdown('<div class="result-price" style="font-size:17px;">لا يوجد اتفاق</div><div class="small-muted">انتهى الاجتماع دون إتمام الصفقة</div>', unsafe_allow_html=True)
    else: st.markdown('<div class="result-price" style="font-size:17px;">بانتظار الاتفاق...</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div class="big-buttons-label">⚡ تحكم بالاجتماع - انتي المديرة</div>', unsafe_allow_html=True)
if st.session_state.meeting_running and not st.session_state.meeting_finished:
    st.info(f"الجولة الحالية: {st.session_state.get('current_round',1)} من 8 - اضغطي الجولة التالية عشان يتحاورون، أو اكتبي ملاحظتك فوق وتدخلي.")
    n1,n2 = st.columns([2,1])
    with n1:
        if st.button("▶  الجولة التالية - خليهم يتحاورون", type="primary", use_container_width=True):
            try: next_round(config)
            except Exception as e: st.error(str(e))
            st.rerun()
    with n2:
        if st.button("⏹️  انهاء الاجتماع", use_container_width=True):
            finish_meeting(config); st.rerun()

b1,b2,b3 = st.columns([2,1.2,1.2])
with b1: start_clicked = st.button("▶  بدء اجتماع التفاوض", type="primary", use_container_width=True, disabled=not valid or st.session_state.meeting_running)
with b2: reset_clicked = st.button("🔄  اجتماع جديد - مسح الكل", use_container_width=True)
with b3:
    if st.session_state.report: st.download_button("📥  تحميل تقرير الاجتماع", data=st.session_state.report, file_name="GMC_Negotiation_Report.txt", mime="text/plain", use_container_width=True)
    else: st.button("📥  تحميل تقرير الاجتماع", disabled=True, use_container_width=True)
st.caption("بدء الاجتماع = ترحيب فقط | الجولة التالية = جولة حوار كاملة | اكتبي ملاحظة = تتدخلين وتوقفينهم")

if reset_clicked:
    for k in ["messages","meeting_result","final_price","buyer_offer","seller_offer","report","meeting_error","user_notes"]: st.session_state[k]=[] if k in ["messages","user_notes"] else None
    st.session_state.cart=[]; st.session_state.meeting_running=False; st.session_state.meeting_finished=False; st.session_state.current_round=1; st.rerun()
if start_clicked:
    st.session_state.messages=[]; st.session_state.user_notes=[]; st.session_state.meeting_running=True; st.session_state.meeting_finished=False; st.session_state.meeting_result=None; st.session_state.final_price=None; st.session_state.buyer_offer=None; st.session_state.seller_offer=None; st.session_state.report=""; st.session_state.meeting_error=None; st.session_state.current_round=1
    try: run_meeting(config, chat_placeholder, st.empty())
    except Exception as e: st.session_state.meeting_running=False; add_message("manager","مدير التفاوض",f"حدث خطأ: {str(e)}"); st.error(str(e))
    st.rerun()

if st.session_state.meeting_result == "success" and st.session_state.final_price:
    total_initial = config["total_initial"] if 'config' in locals() else total_cart
    saved = total_initial - st.session_state.final_price
    saved_pct = round(saved / total_initial * 100, 1) if total_initial else 0
    cart_list = "".join([f"<div class='deal-row'><span>{x['product']} x{x['qty']}</span><strong>{money(x['price']*x['qty'])}</strong></div>" for x in st.session_state.cart])
    st.balloons()
    st.markdown(f"""
    <div class="deal-success-box">
        <div class="deal-success-title">🎉 تم البيع بنجاح - تم الاتفاق ✅</div>
        <div class="deal-success-sub">مبروك يا مديرتنا الملكة الإمبراطورة ريوف القحطاني 👑 تم إغلاق الصفقة رسمياً</div>
        <div class="deal-success-price">{money(st.session_state.final_price)}</div>
        <div class="deal-success-detail">السعر النهائي المتفق عليه للسلة كلها</div>
        <div class="deal-success-grid">
            <div><span>السعر الابتدائي</span><strong>{money(total_initial)}</strong></div>
            <div><span>السعر النهائي</span><strong style="color:#48c99a">{money(st.session_state.final_price)}</strong></div>
            <div><span>إجمالي التوفير</span><strong style="color:#f3d69e">وفّرتي {money(saved)} ({saved_pct}%)</strong></div>
            <div><span>عدد السيارات</span><strong>{sum(x['qty'] for x in st.session_state.cart) if st.session_state.cart else 0} سيارة</strong></div>
        </div>
        <div class="deal-success-cart">{cart_list}</div>
        <div class="deal-success-note">✅ يشمل: ضمان 5 سنوات + صيانة مجانية سنة + توصيل مجاني + تجهيز العقود خلال 7 أيام عمل</div>
        <div class="deal-success-note2">الصفقة مغلقة - لإجراء صفقة جديدة اضغطي "اجتماع جديد"</div>
    </div>
    """, unsafe_allow_html=True)
    contract = f"""عقد بيع - GMC SMART NEGOTIATION CENTER\n================================\nالمديرة: الملكة الإمبراطورة ريوف القحطاني\nالشركة: {company}\nالسيارات:\n{chr(10).join([f"- {x['product']} x{x['qty']} = {money(x['price']*x['qty'])}" for x in st.session_state.cart])}\nالسعر الابتدائي: {money(total_initial)}\nالسعر النهائي المتفق عليه: {money(st.session_state.final_price)}\nالتوفير: {money(saved)} ({saved_pct}%)\nالحالة: تم البيع بنجاح ✅\nالمزايا: ضمان 5 سنوات + صيانة مجانية سنة + توصيل مجاني\n================================\nتم الاتفاق من الطرفين في غرفة التفاوض الذكي.\n"""
    st.download_button("📄 تحميل عقد البيع", data=contract, file_name="GMC_Sale_Contract.txt", mime="text/plain", use_container_width=True, type="primary")

if st.session_state.meeting_result == "no_deal":
    st.markdown(f"""<div class="deal-fail-box"><div class="deal-fail-title">❌ لم يتم الاتفاق</div><div>انتهى الاجتماع دون إتمام الصفقة يا ملكتنا. آخر عرض للمشتري {money(st.session_state.buyer_offer or 0)} وآخر عرض للبائع {money(st.session_state.seller_offer or 0)}</div></div>""", unsafe_allow_html=True)

st.markdown("""<div class="footer">GMC · SMART NEGOTIATION CENTER · 👑 REOUF AL-QAHTANI<br><br>AUTONOMOUS AGENTS · COMMERCIAL INTELLIGENCE</div>""", unsafe_allow_html=True)