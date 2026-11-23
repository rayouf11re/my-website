import streamlit as st, html

def money(v):
    if v is None: return "—"
    try: return f"{int(v):,} ريال"
    except: return str(v)

def add_message(role, name, text, offer=None):
    if "messages" not in st.session_state: st.session_state.messages = []
    st.session_state.messages.append({"role": role, "name": name, "text": text, "offer": offer})

def render_chat(ph):
    for m in st.session_state.get("messages", []):
        role = m.get("role","manager")
        name = m.get("name","")
        text = m.get("text","")
        offer = m.get("offer")
        icon = {"seller":"🏢","buyer":"💰","manager":"⚖️","user":"👑"}.get(role,"💬")
        css_class = {"seller":"msg-seller","buyer":"msg-buyer","manager":"msg-manager","user":"msg-user"}.get(role,"msg-manager")
        offer_html = f'<div class="offer-badge">عرضي: {money(offer)}</div>' if offer else ""
        display_text = text.replace("عرضي:", "<br><b>عرضي:</b>")
        ph.markdown(f'<div class="{css_class}"><div class="msg-head">{icon} {html.escape(name)}</div><div class="msg-text">{display_text}</div>{offer_html}</div>', unsafe_allow_html=True)

def build_report(config):
    lines = [f"تقرير التفاوض - GMC", f"المديرة: الملكة الإمبراطورة ريوف القحطاني", f"الشركة: {config.get('company','')}", f"السلة: {config.get('product','')}", f"المجموع الابتدائي: {money(config.get('total_initial'))}", f"آخر عرض البائع: {money(st.session_state.get('seller_offer'))}", f"آخر عرض المشتري: {money(st.session_state.get('buyer_offer'))}", f"السعر النهائي: {money(st.session_state.get('final_price'))}", "", "--- المحادثة ---", ""]
    for m in st.session_state.get("messages", []):
        lines.append(f"{m.get('name','')}: {m.get('text','')}")
    return "\n".join(lines)