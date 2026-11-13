"""Streamlit UI for Escala Staff Rota — imports all logic from database.py and logic.py."""
import datetime
import io
import os
import re
import streamlit as st
import pandas as pd

from database import (
    init_db,
    get_funcionarios_ativos,
    adicionar_funcionario,
    atualizar_funcionario,
    desativar_funcionario,
    get_cafe_by_id,
    criar_cafe,
    create_user,
    verify_credentials,
    get_all_users,
    reset_password,
    salvar_roster,
    get_rosters,
    get_roster_by_id,
    deletar_roster,
    get_shift_templates,
    save_shift_templates,
    seed_shift_templates,
    build_turnos_padrao,
    build_slot_config,
    get_weekly_setup,
    save_weekly_setup,
    build_config_semana,
    get_date_headcount_overrides,
    save_date_headcount_override,
    delete_date_headcount_override,
    get_cafe_min_dias_folga,
    set_cafe_min_dias_folga,
)
from logic import calcular_horas_turno, gerar_escala_automatica, gerar_pdf_escala, gerar_excel_escala
from billing_logic import (
    is_pro,
    get_plan_tier,
    get_employee_limit,
    check_feature_gate,
    create_stripe_checkout_session,
    get_subscription,
    upsert_subscription,
)


# ==========================================
# CACHED DB WRAPPERS  (avoid repeated round-trips to Supabase on every rerun)
# ==========================================

@st.cache_data(ttl=300)
def _cached_cafe(cafe_id, _v=0):
    """Cache cafe lookup for 5 min — changes very rarely."""
    return get_cafe_by_id(cafe_id)


@st.cache_data(ttl=60)
def _cached_funcionarios(tenant_id, _v=0):
    """Cache employee list for 60 s; _v is a cache-bust counter incremented on every write."""
    return get_funcionarios_ativos(tenant_id)


@st.cache_data(ttl=30)
def _cached_rosters(tenant_id, _v=0):
    """Cache roster list for 30 s; _v is incremented on save/delete."""
    return get_rosters(tenant_id)


def _trial_expired(tenant_id):
    """Return True when a non-Pro tenant is beyond the 7-day trial."""
    if is_pro(tenant_id):
        return False
    cafe = _cached_cafe(tenant_id)
    created_at = (cafe or {}).get("created_at") if isinstance(cafe, dict) else None
    if not created_at:
        return False
    try:
        started = created_at if isinstance(created_at, datetime.datetime) else datetime.datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
        now = datetime.datetime.now(started.tzinfo) if started.tzinfo else datetime.datetime.now()
        return now - started > datetime.timedelta(days=15)
    except (TypeError, ValueError, OverflowError):
        return False


def _render_plan_cards(tenant_id, key_prefix, button_prefix, cafe_name=""):
    """Render the three self-serve monthly plans and start checkout."""
    _plan_options = [
        ("starter", "Starter", "€19,90/mo", "Up to 10 staff"),
        ("standard", "Standard", "€39/mo", "Up to 20 staff"),
        ("plus", "Plus", "€65/mo", "Up to 40 staff"),
    ]
    _plan_cols = st.columns(3)
    for _plan_col, (_plan_tier, _plan_name, _plan_price, _plan_limit) in zip(_plan_cols, _plan_options):
        with _plan_col:
            st.markdown(
                f"""<div style="background:#151025;border:1px solid rgba(167,139,250,.28);border-radius:14px;padding:1rem;min-height:110px">
                <div style="color:#f6f4ff;font-size:1.15rem;font-weight:700">{_plan_name}</div>
                <div style="color:#a78bfa;font-size:1.4rem;font-weight:700;margin:.35rem 0">{_plan_price}</div>
                <div style="color:#b8b0ce;font-size:.85rem">{_plan_limit}</div></div>""",
                unsafe_allow_html=True,
            )
            if st.button(f"{button_prefix} — {_plan_price}", key=f"{key_prefix}_{_plan_tier}", type="primary", use_container_width=True):
                try:
                    _base = os.environ.get("APP_URL", "https://your-app.streamlit.app")
                    _url = create_stripe_checkout_session(tenant_id, _plan_tier, f"{_base}?upgraded=1", _base, cafe_name=cafe_name)
                    st.markdown(f"[➡️ Continue to checkout]({_url})")
                except KeyError:
                    st.warning("Payments temporarily unavailable. Please try again later or contact support.")
                except Exception:
                    st.error("Could not start checkout. Please try again later or contact support.")

# ==========================================
# UI HELPERS
# ==========================================

def render_availability_selector(prefix, defaults=None):
    """Render a 7-day availability selector and return the list of chosen values."""
    if defaults is None:
        defaults = ["Livre"] * 7

    dias = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    opcoes = ["Livre", "Só Manhã", "Só Tarde", "Indisponível", "Específico"]
    _opcoes_display = {
        "Livre": "Available", "Só Manhã": "Morning only",
        "Só Tarde": "Afternoon only", "Indisponível": "Unavailable", "Específico": "Custom",
    }
    _dias_display = {"Seg": "Mon", "Ter": "Tue", "Qua": "Wed", "Qui": "Thu", "Sex": "Fri", "Sáb": "Sat", "Dom": "Sun"}
    resultados = []

    st.write("**Weekly Availability**")
    cols1 = st.columns(4)
    cols2 = st.columns(4)
    todas_cols = cols1 + cols2

    for i, dia in enumerate(dias):
        with todas_cols[i]:
            val_padrao = defaults[i]
            idx_opcao = opcoes.index("Livre")
            texto_especifico = ""

            if val_padrao in opcoes:
                idx_opcao = opcoes.index(val_padrao)
            elif val_padrao and "Específico" in val_padrao:
                idx_opcao = opcoes.index("Específico")
                texto_especifico = val_padrao.replace("Específico: ", "")
            elif val_padrao in ("Folga", "Férias"):
                idx_opcao = opcoes.index("Indisponível")
            elif not val_padrao or val_padrao == "0" or val_padrao == "False":
                idx_opcao = opcoes.index("Indisponível")

            selecao = st.selectbox(
                _dias_display.get(dia, dia),
                opcoes,
                index=idx_opcao,
                key=f"{prefix}_sel_{dia}",
                format_func=lambda o: _opcoes_display.get(o, o),
            )

            if selecao == "Específico":
                sh_def, sm_def, eh_def, em_def = 9, 0, 17, 0
                if texto_especifico:
                    _t = re.findall(r'(\d{1,2}):(\d{2})', texto_especifico)
                    if len(_t) == 2:
                        sh_def, sm_def = int(_t[0][0]), int(_t[0][1])
                        eh_def, em_def = int(_t[1][0]), int(_t[1][1])
                st.caption("From:")
                _ch, _cm = st.columns(2)
                sh = _ch.number_input("H", 0, 23, sh_def, 1, format="%02d", key=f"{prefix}_sh_{dia}", label_visibility="collapsed")
                sm = _cm.number_input("M", 0, 59, sm_def, 5, format="%02d", key=f"{prefix}_sm_{dia}", label_visibility="collapsed")
                st.caption("To:")
                _eh, _em = st.columns(2)
                eh = _eh.number_input("H", 0, 23, eh_def if texto_especifico else 18, 1, format="%02d", key=f"{prefix}_eh_{dia}", label_visibility="collapsed")
                em = _em.number_input("M", 0, 59, em_def if texto_especifico else 15, 5, format="%02d", key=f"{prefix}_em_{dia}", label_visibility="collapsed")
                resultados.append(f"Específico: {int(sh):02d}:{int(sm):02d} - {int(eh):02d}:{int(em):02d}")
            else:
                resultados.append(selecao)

    return resultados


# ==========================================
# APP SETUP
# ==========================================
st.set_page_config(page_title="Escala", page_icon="⬡", layout="wide")

# Run init_db only once per browser session — not on every Streamlit rerun.
# On Supabase, every _get_conn() is a network round-trip (~200-400 ms);
# init_db sends 6+ DDL statements, so skipping it after the first run saves 1-2 s.
if 'db_initialized' not in st.session_state:
    init_db()
    st.session_state['db_initialized'] = True

if 'user' not in st.session_state:
    st.session_state['user'] = None

# ------------------------------------------
# AUTH GATE: Login / Register
# ------------------------------------------
if st.session_state['user'] is None:
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
    [data-testid="stAppViewContainer"] > .main {
        background: #0d0a1a;
        min-height: 100vh;
    }
    [data-testid="stHeader"] { background: transparent !important; }
    [data-testid="stDecoration"] { display: none; }
    [data-testid="stToolbar"] { display: none; }
    section[data-testid="stMain"] [data-testid="stForm"] {
        background: rgba(20, 14, 42, 0.97);
        border-radius: 20px;
        padding: 2.5rem 2.2rem 2rem 2.2rem;
        border: 1px solid rgba(139, 92, 246, 0.2);
        box-shadow: 0 0 0 1px rgba(139,92,246,0.06), 0 32px 80px rgba(0,0,0,0.6);
    }
    [data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(90deg, #6d28d9, #8b5cf6) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        letter-spacing: 0.3px;
        padding: 0.6rem 0 !important;
        transition: opacity 0.15s;
    }
    [data-testid="stFormSubmitButton"] > button:hover { opacity: 0.85; }
    .login-brand {
        text-align: center;
        margin-bottom: 1.8rem;
    }
    .login-hex {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 52px; height: 52px;
        background: linear-gradient(135deg, #6d28d9, #8b5cf6);
        border-radius: 14px;
        font-size: 26px;
        margin-bottom: 12px;
        box-shadow: 0 4px 20px rgba(139,92,246,0.4);
    }
    .login-wordmark {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        font-size: 28px;
        letter-spacing: -0.04em;
        color: #f0ecff;
        display: block;
        margin-bottom: 4px;
    }
    .login-tagline {
        font-family: 'Outfit', sans-serif;
        font-size: 13px;
        color: #7c6fa8;
        letter-spacing: 0.02em;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([3, 2, 3])
    with col_login:
        st.markdown("""
        <div class="login-brand">
            <div class="login-hex">⬡</div>
            <span class="login-wordmark">escala</span>
            <span class="login-tagline">Café rota management · Dublin</span>
        </div>
        """, unsafe_allow_html=True)
        with st.form("form_login"):
            email_login = st.text_input("Email", placeholder="you@cafe.com")
            senha_login = st.text_input("Password", type="password", placeholder="••••••••")
            if st.form_submit_button("Sign in", use_container_width=True):
                user = verify_credentials(email_login, senha_login)
                if user:
                    st.session_state['user'] = user
                    st.session_state['tenant_id'] = user['tenant_id']
                    st.rerun()
                else:
                    st.error("Incorrect email or password.")

    st.stop()

# ------------------------------------------
# AUTHENTICATED: resolve tenant + sidebar
# ------------------------------------------
TENANT_ID = st.session_state['tenant_id']
_user = st.session_state['user']

if _user.get('role') != 'superadmin' and get_subscription(TENANT_ID).get('plano', 'free') == 'free':
    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background: #0d0a1a; }
    .trial-wall { max-width: 980px; margin: 8vh auto 0; text-align: center; }
    .trial-wall h1 { color: #f6f4ff; font-size: 2.6rem; letter-spacing: -.04em; }
    .trial-wall p { color: #b8b0ce; font-size: 1.1rem; }
    </style>
    <div class="trial-wall">
      <h1>Start your 7-day trial</h1>
      <p>Choose a plan to generate compliant rotas. Card required, cancel anytime.</p>
    </div>
    """, unsafe_allow_html=True)
    _render_plan_cards(TENANT_ID, "trial_wall_upgrade", "Start trial")
    st.stop()

# Version counters — incremented after each write so @st.cache_data misses and re-fetches.
if 'equipe_v' not in st.session_state:
    st.session_state['equipe_v'] = 0
if 'roster_v' not in st.session_state:
    st.session_state['roster_v'] = 0

_cafe = _cached_cafe(TENANT_ID)
_cafe_nome = _cafe['name'] if _cafe else "Cafe"
_tier = get_plan_tier(TENANT_ID)
_is_pro = is_pro(TENANT_ID)
_emp_limit = get_employee_limit(TENANT_ID)
_tier_labels = {"free": "Free", "starter": "Starter", "standard": "Standard", "plus": "Plus", "network": "Network"}
_tier_label = _tier_labels.get(_tier, _tier.title())
_limit_label = "Unlimited" if _emp_limit is None else str(_emp_limit)

# Post-payment redirect: Stripe sends back ?upgraded=1
if st.query_params.get("upgraded") == "1":
    st.session_state["_upgrade_msg"] = True
    st.query_params.clear()
    st.rerun()

with st.sidebar:
    st.markdown(f"### ☕ {_cafe_nome}")
    st.write(f"👤 {_user['email']}")
    st.write(f"🔖 {_user['role'].capitalize()}")
    st.divider()
    _semana_ativa = st.session_state.get("semana_key", "")
    if _semana_ativa:
        st.caption(f"📋 **Week:** {_semana_ativa}")
        st.divider()
    if _user.get('role') == 'superadmin':
        if 'nc_k' not in st.session_state:
            st.session_state['nc_k'] = 0
        _nck = st.session_state['nc_k']
        with st.expander("➕ Register New Café"):
            with st.form(f"form_novo_cafe_{_nck}"):
                _nc_nome = st.text_input("Café Name", key=f"nc_nome_{_nck}")
                _nc_email = st.text_input("Admin Email", key=f"nc_email_{_nck}")
                _nc_senha = st.text_input("Password", type="password", key=f"nc_senha_{_nck}")
                _nc_conf = st.text_input("Confirm Password", type="password", key=f"nc_conf_{_nck}")
                if st.form_submit_button("Create"):
                    if _nc_senha != _nc_conf:
                        st.error("Passwords do not match.")
                    elif not _nc_nome or not _nc_email or not _nc_senha:
                        st.error("Please fill in all fields.")
                    else:
                        try:
                            _ntid = criar_cafe(_nc_nome, _nc_email)
                            create_user(_ntid, _nc_email, _nc_senha, role="admin")
                            upsert_subscription(_ntid, "starter", None)
                            st.success(f"'{_nc_nome}' created!")
                            st.session_state['nc_k'] += 1
                            st.rerun()
                        except Exception as _e:
                            st.error(f"Erro: {_e}")

        if 'rp_k' not in st.session_state:
            st.session_state['rp_k'] = 0
        _rpk = st.session_state['rp_k']
        with st.expander("🔑 Reset Password"):
            _all_users = get_all_users()
            if _all_users.empty:
                st.caption("No users found.")
            else:
                _user_opts = [
                    f"{r['email']} ({r['cafe_nome']})"
                    for _, r in _all_users.iterrows()
                ]
                with st.form(f"form_reset_pw_{_rpk}"):
                    _rp_sel = st.selectbox("User", _user_opts, key=f"rp_sel_{_rpk}")
                    _rp_nova = st.text_input("New Password", type="password", key=f"rp_nova_{_rpk}")
                    _rp_conf = st.text_input("Confirm", type="password", key=f"rp_conf_{_rpk}")
                    if st.form_submit_button("Reset"):
                        if not _rp_nova or len(_rp_nova) < 6:
                            st.error("Password must be at least 6 characters.")
                        elif _rp_nova != _rp_conf:
                            st.error("Passwords do not match.")
                        else:
                            _rp_email = _rp_sel.split(" (")[0]
                            if reset_password(_rp_email, _rp_nova):
                                st.success(f"Password for {_rp_email} reset.")
                                st.session_state['rp_k'] += 1
                                st.rerun()
                            else:
                                st.error("User not found.")
    if _user.get('role') != 'superadmin':
        st.divider()
        st.caption(f"Plan: **{_tier_label}** · Staff limit: **{_limit_label}**")
        if _tier == "free":
            with st.expander("⭐ Upgrade Plan"):
                st.markdown(
                    "**Unlocks:**\n"
                    "- 🖨️ PDF Export\n"
                    "- 📊 Analytics\n"
                    "- 💾 Rota History\n"
                    "- 👥 Scaled staff limits"
                )
                st.markdown("All plans include a 7-day free trial · card required · cancel anytime")
                _plan_cols = st.columns(3)
                _upgrade_options = [("starter", "Starter", "€19,90/mo"), ("standard", "Standard", "€39/mo"), ("plus", "Plus", "€65/mo")]
                for _plan_col, (_plan_tier, _plan_name, _plan_price) in zip(_plan_cols, _upgrade_options):
                    with _plan_col:
                        if st.button(f"{_plan_name}\n{_plan_price}", key=f"upgrade_{_plan_tier}", type="primary"):
                            try:
                                _base = os.environ.get("APP_URL", "https://your-app.streamlit.app")
                                url = create_stripe_checkout_session(TENANT_ID, _plan_tier, f"{_base}?upgraded=1", _base)
                                st.markdown(f"[➡️ Continue to payment]({url})")
                            except KeyError:
                                st.warning("Payments temporarily unavailable. Please try again later or contact support.")
                            except Exception:
                                st.error("Could not start checkout. Please try again later or contact support.")
    st.divider()
    if st.button("🚪 Sign out"):
        st.session_state['user'] = None
        st.session_state['tenant_id'] = None
        st.rerun()

st.markdown('''<div style="display:flex;align-items:center;gap:12px;margin-bottom:4px">
  <svg width="28" height="32" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
    <polygon points="24,4 41.32,14 41.32,34 24,44 6.68,34 6.68,14" fill="rgba(139,92,246,0.2)" stroke="#a78bfa" stroke-width="2.5" stroke-linejoin="round"/>
    <polygon points="24,12 34.39,18 34.39,30 24,36 13.61,30 13.61,18" fill="none" stroke="rgba(167,139,250,0.4)" stroke-width="1" stroke-linejoin="round"/>
  </svg>
  <span style="font-size:28px;font-weight:700;letter-spacing:-0.04em;color:#f6f4ff">escala</span>
</div>''', unsafe_allow_html=True)
st.markdown('''<style>
[data-testid="stAppViewContainer"] { background: #0a0a0f; }
[data-testid="stHeader"] { background: rgba(10,10,15,0.9) !important; backdrop-filter: blur(12px); border-bottom: 1px solid rgba(255,255,255,0.08); }
[data-testid="stSidebar"] { background: #111018 !important; border-right: 1px solid rgba(255,255,255,0.07); }
.stTabs [data-baseweb="tab-list"] { background: transparent; border-bottom: 1px solid rgba(255,255,255,0.1); gap: 4px; }
.stTabs [data-baseweb="tab"] { background: transparent; color: #9892ae; border: none; border-radius: 8px 8px 0 0; padding: 10px 18px; font-weight: 500; font-size: 13px; }
.stTabs [aria-selected="true"] { background: rgba(139,92,246,0.15) !important; color: #a78bfa !important; border-bottom: 2px solid #8b5cf6; }
button[kind="primary"] { background: linear-gradient(90deg,#7c3aed,#9c5cf7) !important; border: none !important; }
</style>''', unsafe_allow_html=True)
if st.session_state.pop("_upgrade_msg", False):
    st.success("🎉 Payment confirmed! Your Roster Café Pro plan is now active.")

aba2, aba3, aba1, aba_config, aba4, aba5 = st.tabs([
    "⚙️ Weekly Setup", "📅 Weekly Rota", "👥 Team", "🕒 Shifts", "📊 History", "📖 Help",
])

lista_cargos_oficiais = ["Manager", "Assistant Manager", "Head Barista", "Barista"]

# ------------------------------------------
# ABA 1: GESTÃO DO TIME
# ------------------------------------------
with aba1:
    st.header("Current Team")
    df_equipe = _cached_funcionarios(TENANT_ID, st.session_state['equipe_v'])

    espaco_esq, col_tabela, espaco_dir = st.columns([1, 6, 1])
    with col_tabela:
        if not df_equipe.empty:
            _cols_tabela = ['nome', 'cargo', 'tipo_contrato', 'horas_min', 'horas_max']
            if 'nivel' in df_equipe.columns:
                _cols_tabela.append('nivel')
            if 'preferencia_turno' in df_equipe.columns:
                _cols_tabela.append('preferencia_turno')
            st.dataframe(df_equipe[_cols_tabela], use_container_width=True)
        else:
            st.info("No staff added yet.")
            st.button("➕ Add first staff member", key="cta_add_first", type="primary")

    st.divider()
    col1, col_espaco, col2 = st.columns([4, 1, 4])

    with col1:
        st.subheader("➕ Add Staff Member")
        if 'novo_k' not in st.session_state:
            st.session_state['novo_k'] = 0
        _nk = st.session_state['novo_k']

        nome_novo = st.text_input("Nome", key=f"novo_nome_{_nk}")
        c_cargo, c_contrato = st.columns(2)
        cargo_novo = c_cargo.selectbox("Cargo", lista_cargos_oficiais, key=f"novo_cargo_{_nk}")
        contrato_novo = c_contrato.selectbox("Contrato", ["Full-time", "Part-time"], key=f"novo_contrato_{_nk}")

        c_min, c_max = st.columns(2)
        h_min_nova = c_min.number_input("Min Hours", min_value=0, max_value=60, value=20, key=f"novo_hmin_{_nk}")
        h_max_nova = c_max.number_input("Max Hours", min_value=0, max_value=60, value=39, key=f"novo_hmax_{_nk}")

        nivel_novo = st.selectbox("Level", ["experiente", "novato"], key=f"novo_nivel_{_nk}",
                                  format_func=lambda x: "Experienced" if x == "experiente" else "Trainee",
                                  help="Trainee: cannot share an opening or closing block with another trainee.")

        pref_novo = st.selectbox(
            "Shift Preference", ["Sem preferência", "Manhã", "Tarde"],
            key=f"novo_pref_{_nk}",
            format_func=lambda x: {"Sem preferência": "No preference", "Manhã": "Morning", "Tarde": "Afternoon"}.get(x, x),
            help="Soft constraint — the scheduler tries to respect this but never violates contracts, keyholder, or WTI rules.",
        )

        dias_selecionados = render_availability_selector(f"novo_{_nk}")

        if st.button("Add", key=f"novo_btn_{_nk}") and nome_novo:
            _cur_count = len(df_equipe) if not df_equipe.empty else 0
            if _emp_limit is not None and _cur_count >= _emp_limit:
                st.error(f"Staff limit reached: your plan supports up to {_emp_limit} active staff. Upgrade Plan in the sidebar to add more.")
            else:
                try:
                    adicionar_funcionario(TENANT_ID, nome_novo, cargo_novo, contrato_novo, h_min_nova, h_max_nova, dias_selecionados, nivel_novo, pref_novo)
                    st.success(f"{nome_novo} added!")
                    st.session_state['equipe_v'] += 1
                    st.session_state['novo_k'] += 1
                    st.rerun()
                except ValueError as _ve:
                    if "limite_funcionarios" in str(_ve):
                        st.error(f"Staff limit reached: your plan supports up to {_emp_limit} active staff. Upgrade Plan in the sidebar.")
                    else:
                        st.error("Could not save staff member. Please try again.")

    with col2:
        st.subheader("✏️ Edit or Remove")
        if not df_equipe.empty:
            func_selecionado = st.selectbox("Select a staff member", df_equipe['nome'].tolist())
            dados_atuais = df_equipe[df_equipe['nome'] == func_selecionado].iloc[0]

            _pfx = f"ed_{func_selecionado}"
            nome_ed = st.text_input("Nome", value=dados_atuais['nome'], key=f"{_pfx}_nome")
            c_cargo_ed, c_contrato_ed = st.columns(2)
            idx_cargo = lista_cargos_oficiais.index(dados_atuais['cargo']) if dados_atuais['cargo'] in lista_cargos_oficiais else 3
            cargo_ed = c_cargo_ed.selectbox("Cargo", lista_cargos_oficiais, index=idx_cargo, key=f"{_pfx}_cargo")
            idx_contrato = 0 if dados_atuais['tipo_contrato'] == "Full-time" else 1
            contrato_ed = c_contrato_ed.selectbox("Contrato", ["Full-time", "Part-time"], index=idx_contrato, key=f"{_pfx}_contrato")

            c_min_ed, c_max_ed = st.columns(2)
            h_min_ed = c_min_ed.number_input("Min Hours", min_value=0, max_value=60, value=int(dados_atuais['horas_min']), key=f"{_pfx}_hmin")
            h_max_ed = c_max_ed.number_input("Max Hours", min_value=0, max_value=60, value=int(dados_atuais['horas_max']), key=f"{_pfx}_hmax")

            _nivel_atual = str(dados_atuais.get('nivel', 'experiente') or 'experiente')
            _nivel_opts = ["experiente", "novato"]
            _nivel_idx = _nivel_opts.index(_nivel_atual) if _nivel_atual in _nivel_opts else 0
            nivel_ed = st.selectbox("Level", _nivel_opts, index=_nivel_idx, key=f"{_pfx}_nivel",
                                    format_func=lambda x: "Experienced" if x == "experiente" else "Trainee",
                                    help="Trainee: cannot share an opening or closing block with another trainee.")

            _pref_atual = str(dados_atuais.get('preferencia_turno', 'Sem preferência') or 'Sem preferência')
            _pref_opts = ["Sem preferência", "Manhã", "Tarde"]
            _pref_idx = _pref_opts.index(_pref_atual) if _pref_atual in _pref_opts else 0
            pref_ed = st.selectbox(
                "Shift Preference", _pref_opts, index=_pref_idx, key=f"{_pfx}_pref",
                format_func=lambda x: {"Sem preferência": "No preference", "Manhã": "Morning", "Tarde": "Afternoon"}.get(x, x),
                help="Soft constraint — the scheduler tries to respect this but never violates contracts, keyholder, or WTI rules.",
            )

            dias_atuais = [
                dados_atuais['d_seg'], dados_atuais['d_ter'], dados_atuais['d_qua'],
                dados_atuais['d_qui'], dados_atuais['d_sex'], dados_atuais['d_sab'], dados_atuais['d_dom']
            ]
            dias_ed = render_availability_selector(_pfx, dias_atuais)

            col_btn1, col_btn2 = st.columns(2)
            if col_btn1.button("💾 Save", key=f"{_pfx}_salvar"):
                atualizar_funcionario(TENANT_ID, int(dados_atuais['id_funcionario']), nome_ed, cargo_ed, contrato_ed, h_min_ed, h_max_ed, dias_ed, nivel_ed, pref_ed)
                st.success("Updated!")
                st.session_state['equipe_v'] += 1
                for _sk in [k for k in st.session_state if k.startswith(f"ed_{func_selecionado}")]:
                    del st.session_state[_sk]
                st.rerun()
            if col_btn2.button("❌ Deactivate", key=f"{_pfx}_desativar"):
                desativar_funcionario(TENANT_ID, int(dados_atuais['id_funcionario']))
                st.session_state['equipe_v'] += 1
                st.warning("Deactivated.")
                st.rerun()

# ------------------------------------------
# ABA CONFIG: TURNOS E CAPACIDADE
# ------------------------------------------
with aba_config:
    st.header("🕒 Shift Settings")
    _templates = get_shift_templates(TENANT_ID)
    if _templates.empty:
        _templates = seed_shift_templates(TENANT_ID)

    _template_rows = []
    for _, _row in _templates.iterrows():
        _template_rows.append({
            "Day": _row["dia"],
            "Start": _row["hora_inicio"],
            "End": _row["hora_fim"],
            "Closing": bool(_row["fechamento"]),
            "Headcount": int(_row["headcount"]),
            "Optional": _row["prioridade"] == "optional",
            "Active": bool(_row["ativo"]),
        })

    _edited_templates = st.data_editor(
        pd.DataFrame(_template_rows),
        column_config={
            "Day": st.column_config.SelectboxColumn("Day", options=["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"], required=True),
            "Start": st.column_config.TextColumn("Start", help="Format HH:MM"),
            "End": st.column_config.TextColumn("End", help="Format HH:MM"),
            "Closing": st.column_config.CheckboxColumn("Closing"),
            "Headcount": st.column_config.NumberColumn("Headcount", min_value=1, max_value=6, step=1, format="%d"),
            "Optional": st.column_config.CheckboxColumn("Optional"),
            "Active": st.column_config.CheckboxColumn("Active"),
        },
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        key="shift_templates_editor",
    )
    if st.button("💾 Save Shifts", type="primary"):
        _rows_to_save = []
        _template_errors = []
        for _, _row in _edited_templates.iterrows():
            _day = _row.get("Day")
            _start = _row.get("Start")
            _end = _row.get("End")
            _active = _row.get("Active", True)
            if pd.isna(_day) or pd.isna(_start) or pd.isna(_end) or pd.isna(_active) or not bool(_active):
                continue
            _day, _start, _end = str(_day).strip(), str(_start).strip(), str(_end).strip()
            if _day not in ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]:
                _template_errors.append(f"Invalid day: {_day}")
                continue
            if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", _start) or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", _end):
                _template_errors.append(f"Invalid time: {_start}–{_end}")
                continue
            _rows_to_save.append({
                "dia": _day,
                "hora_inicio": _start,
                "hora_fim": _end,
                "fechamento": bool(_row.get("Closing", False)) if not pd.isna(_row.get("Closing", False)) else False,
                "headcount": max(1, min(6, int(_row.get("Headcount", 1)) if not pd.isna(_row.get("Headcount", 1)) else 1)),
                "prioridade": "optional" if (not pd.isna(_row.get("Optional", False)) and bool(_row.get("Optional", False))) else "essential",
                "ativo": True,
            })
        if _template_errors:
            for _error in _template_errors:
                st.error(_error)
        elif not _rows_to_save:
            st.error("Keep at least one active shift.")
        else:
            save_shift_templates(TENANT_ID, _rows_to_save)
            st.session_state.pop("turnos_padrao", None)
            st.session_state.pop("slot_config", None)
            st.session_state.pop("roster_df", None)
            st.success("Shift settings saved.")
            st.rerun()

# ------------------------------------------
# ABA 2: SETUP DA SEMANA
# ------------------------------------------
with aba2:
    if _trial_expired(TENANT_ID):
        st.warning("⏰ Your 7-day trial has ended. Choose a plan to keep generating rotas.")
        _render_plan_cards(TENANT_ID, "trial_upgrade_setup", "Choose")
        st.stop()
    st.header("Weekly Selection & Budget")
    esp_esq, col_setup, esp_dir = st.columns([1, 4, 1])

    with col_setup:
        if not df_equipe.empty:
            if "weekly_setup_loaded" not in st.session_state:
                _saved_setup = get_weekly_setup(TENANT_ID)
                st.session_state["weekly_setup_loaded"] = True
                if _saved_setup:
                    st.session_state["weekly_setup_overrides"] = _saved_setup.get("employees", {})
                    st.session_state["margem_horas"] = float(_saved_setup.get("margem_horas", 2.0))
                    st.session_state["semana_key"] = str(_saved_setup.get("semana_key", ""))
                    st.session_state["config_semana"] = build_config_semana(TENANT_ID, _saved_setup)

            _weekly_overrides = st.session_state.get("weekly_setup_overrides", {})
            total_horas_planejadas = 0
            dias_semana_opts = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
            with st.form("form_setup_semana"):
                st.write("Select who is on the rota this week and adjust target hours.")
                semana_key = st.text_input(
                    "Week label",
                    value=st.session_state.get("semana_key", ""),
                    placeholder="e.g. Week 45",
                    key="semana_key_input",
                )
                margem_horas = st.number_input(
                    "Hour tolerance (± target)", min_value=0.0, max_value=10.0,
                    value=float(st.session_state.get("margem_horas", 2.0)), step=0.5, key="margem_horas_input",
                    help="Alert if actual hours fall outside this margin from the target."
                )
                st.divider()

                inputs_semana = {}
                for index, row in df_equipe.iterrows():
                    c_info, c_check, c_horas = st.columns([3, 1, 2])

                    dias_map = [
                        ("Seg", row['d_seg']), ("Ter", row['d_ter']), ("Qua", row['d_qua']),
                        ("Qui", row['d_qui']), ("Sex", row['d_sex']), ("Sáb", row['d_sab']), ("Dom", row['d_dom'])
                    ]
                    disp_formatada = [f"{dia}({val})" for dia, val in dias_map if val != "Indisponível"]
                    dias_str = ", ".join(disp_formatada)
                    if not dias_str:
                        dias_str = "Unavailable all days"

                    _override = _weekly_overrides.get(row['nome'], {})
                    _vai_trabalhar_default = bool(_override.get("vai_trabalhar", True))
                    c_info.write(f"**{row['nome']}** ({row['cargo']})  \n*Disp: {dias_str}*" if _vai_trabalhar_default else f"**{row['nome']}**")
                    vai_trabalhar = c_check.checkbox("Schedule", key=f"chk_{row['nome']}", value=_vai_trabalhar_default)

                    if vai_trabalhar:
                        horas_alvo = c_horas.number_input("Target Hours", min_value=0, max_value=60, value=int(_override.get("horas_alvo", row['horas_max'])), key=f"hrs_{row['nome']}")
                        c_folga, c_ferias, c_treino, c_htreino = st.columns([2, 2, 2, 1])
                        dias_folga_sel = c_folga.multiselect("🏖️ Day Off", dias_semana_opts, default=list(_override.get("dias_folga", [])), key=f"folga_{row['nome']}")
                        dias_ferias_sel = c_ferias.multiselect("✈️ Holiday", dias_semana_opts, default=list(_override.get("dias_ferias", [])), key=f"ferias_{row['nome']}")
                        dias_treino_sel = c_treino.multiselect("📚 Training", dias_semana_opts, default=list(_override.get("dias_treinamento", [])), key=f"treino_{row['nome']}")
                        horas_treino = c_htreino.number_input("Training h.", min_value=0.0, max_value=40.0, value=float(_override.get("horas_treinamento", 0)), key=f"htreino_{row['nome']}", help="Total training hours this week.")
                    else:
                        horas_alvo = int(_override.get("horas_alvo", row['horas_max']))
                        dias_folga_sel = list(_override.get("dias_folga", []))
                        dias_ferias_sel = list(_override.get("dias_ferias", []))
                        dias_treino_sel = list(_override.get("dias_treinamento", []))
                        horas_treino = float(_override.get("horas_treinamento", 0))

                    if vai_trabalhar:
                        total_horas_planejadas += horas_alvo

                    disp_dict = {d[0]: d[1] for d in dias_map}
                    inputs_semana[row['nome']] = {
                        "vai_trabalhar": vai_trabalhar,
                        "horas_alvo": horas_alvo,
                        "horas_min": float(row['horas_min']),
                        "horas_max": float(row['horas_max']),
                        "cargo": row['cargo'],
                        "tipo_contrato": str(row.get('tipo_contrato', 'Full-time') or 'Full-time'),
                        "nivel": str(row['nivel']) if 'nivel' in df_equipe.columns else 'experiente',
                        "preferencia_turno": str(row.get('preferencia_turno', 'Sem preferência') or 'Sem preferência'),
                        "disponibilidade": disp_dict,
                        "dias_folga": list(dias_folga_sel),
                        "dias_ferias": list(dias_ferias_sel),
                        "dias_treinamento": list(dias_treino_sel),
                        "horas_treinamento": float(horas_treino),
                    }
                    st.divider()

                if st.form_submit_button("Confirm Weekly Hours"):
                    conflitos = []
                    for nome, cfg in inputs_semana.items():
                        dias_overlap = set(cfg["dias_folga"]) & set(cfg["dias_treinamento"])
                        if dias_overlap:
                            conflitos.append(f"{nome}: {', '.join(sorted(dias_overlap))} marked as both Day Off and Training.")
                        dias_overlap2 = set(cfg["dias_ferias"]) & set(cfg["dias_treinamento"])
                        if dias_overlap2:
                            conflitos.append(f"{nome}: {', '.join(sorted(dias_overlap2))} marked as both Holiday and Training.")
                    if conflitos:
                        for c in conflitos:
                            st.warning(f"⚠️ Conflito: {c}")
                    else:
                        _overrides_to_save = {
                            "semana_key": semana_key.strip(),
                            "margem_horas": float(margem_horas),
                            "employees": {
                                nome: {
                                    key: cfg[key]
                                    for key in ("vai_trabalhar", "horas_alvo", "dias_folga", "dias_ferias", "dias_treinamento", "horas_treinamento")
                                }
                                for nome, cfg in inputs_semana.items()
                            },
                        }
                        if not _overrides_to_save["semana_key"]:
                            st.warning("Enter a label to identify the week.")
                        else:
                            save_weekly_setup(TENANT_ID, _overrides_to_save["semana_key"], _overrides_to_save)
                            st.session_state["weekly_setup_overrides"] = _overrides_to_save["employees"]
                            st.session_state["semana_key"] = _overrides_to_save["semana_key"]
                            st.session_state['config_semana'] = build_config_semana(TENANT_ID, _overrides_to_save)
                            st.session_state['margem_horas'] = margem_horas
                            st.success("Setup saved! Go to '📅 Weekly Rota' to generate the schedule.")

            st.subheader("📊 Budget Status")
            progresso = total_horas_planejadas / 305.0 if total_horas_planejadas <= 305 else 1.0
            st.progress(progresso)
            if total_horas_planejadas < 290:
                st.warning(f"Total: {total_horas_planejadas}h (Below target).")
            elif 290 <= total_horas_planejadas <= 300:
                st.success(f"Total: {total_horas_planejadas}h (On target).")
            elif 300 < total_horas_planejadas <= 305:
                st.warning(f"Total: {total_horas_planejadas}h (Within margin).")
            else:
                st.error(f"Total: {total_horas_planejadas}h (Over budget).")

            with st.expander("📅 Headcount exceptions by date", expanded=False):
                _dho_wkmap = {0: "Seg", 1: "Ter", 2: "Qua", 3: "Qui", 4: "Sex", 5: "Sáb", 6: "Dom"}
                _dho_date = st.date_input("Data", value=datetime.date.today(), key="dho_date")
                _dho_wd = _dho_wkmap[_dho_date.weekday()]
                _dho_all_turnos = st.session_state.get("turnos_padrao") or build_turnos_padrao(TENANT_ID)
                _dho_shifts = _dho_all_turnos.get(_dho_wd, [])
                if _dho_shifts:
                    _dho_shift_sel = st.selectbox("Shift", _dho_shifts, key="dho_shift")
                    _dho_hc = st.number_input("Headcount override", min_value=1, max_value=20, value=1, step=1, key="dho_hc")
                    if st.button("💾 Save override", key="dho_save"):
                        save_date_headcount_override(TENANT_ID, _dho_date.strftime("%Y-%m-%d"), _dho_shift_sel, int(_dho_hc))
                        st.success("Override saved.")
                        st.rerun()
                else:
                    st.info(f"No shifts configured for {_dho_wd}. Set up shifts in the Shifts tab.")
                # Derive 7 dates for the ISO week containing the selected date
                _dho_week_start = _dho_date - datetime.timedelta(days=_dho_date.weekday())
                _dho_week_dates = [
                    (_dho_week_start + datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)
                ]
                _dho_existing = get_date_headcount_overrides(TENANT_ID, _dho_week_dates)
                if _dho_existing:
                    st.write("**Overrides for the selected week:**")
                    st.dataframe(
                        pd.DataFrame([
                            {"Date": r["override_date"], "Shift": r["shift_label"], "Headcount": r["headcount"]}
                            for r in _dho_existing
                        ]),
                        hide_index=True,
                        use_container_width=True,
                    )
                    for _dho_r in _dho_existing:
                        _dho_rc1, _dho_rc2, _dho_rc3, _dho_rc4 = st.columns([2, 3, 1, 1])
                        _dho_rc1.caption(_dho_r["override_date"])
                        _dho_rc2.caption(_dho_r["shift_label"])
                        _dho_rc3.caption(str(_dho_r["headcount"]))
                        if _dho_rc4.button("🗑️", key=f"dho_del_{_dho_r['id']}"):
                            delete_date_headcount_override(TENANT_ID, _dho_r["override_date"], _dho_r["shift_label"])
                            st.rerun()
                else:
                    st.caption("No overrides for the selected week.")
        else:
            st.warning("Add staff in the '👥 Team' tab first.")

# ------------------------------------------
# ABA 3: ROSTER E PAINEL DE HORAS
# ------------------------------------------
with aba3:
    if _trial_expired(TENANT_ID):
        st.warning("⏰ Your 7-day trial has ended. Choose a plan to keep generating rotas.")
        _render_plan_cards(TENANT_ID, "trial_upgrade_rota", "Choose")
        st.stop()
    st.header("📅 Weekly Rota")

    _fallback_turnos_padrao = {
        "Seg": ["07:00 - 12:00", "07:00 - 14:00", "07:30 - 15:00", "08:00 - 16:00", "09:00 - 18:15 (Fechamento)", "12:00 - 18:15 (Fechamento)", "14:00 - 18:15 (Fechamento)"],
        "Ter": ["07:00 - 12:00", "07:00 - 14:00", "07:30 - 15:00", "08:00 - 16:00", "09:00 - 18:15 (Fechamento)", "12:00 - 18:15 (Fechamento)", "14:00 - 18:15 (Fechamento)"],
        "Qua": ["06:30 - 12:00", "07:00 - 14:00", "07:30 - 15:00", "08:00 - 16:00", "09:00 - 18:15 (Fechamento)", "12:00 - 18:15 (Fechamento)", "14:00 - 18:15 (Fechamento)"],
        "Qui": ["07:00 - 12:00", "07:00 - 14:00", "07:30 - 15:00", "08:00 - 16:00", "09:00 - 18:15 (Fechamento)", "12:00 - 18:15 (Fechamento)", "14:00 - 18:15 (Fechamento)"],
        "Sex": ["07:00 - 12:00", "07:00 - 14:00", "07:30 - 15:00", "08:00 - 16:00", "09:00 - 18:15 (Fechamento)", "12:00 - 18:15 (Fechamento)", "14:00 - 18:15 (Fechamento)"],
        "Sáb": ["07:30 - 14:00", "07:30 - 15:00", "09:00 - 18:15 (Fechamento)", "12:00 - 18:15 (Fechamento)", "14:00 - 18:15 (Fechamento)"],
        "Dom": ["07:30 - 14:00", "07:30 - 15:00", "09:00 - 18:15 (Fechamento)", "12:00 - 18:15 (Fechamento)", "14:00 - 18:15 (Fechamento)"],
    }

    if "turnos_padrao" not in st.session_state:
        _db_turnos = build_turnos_padrao(TENANT_ID)
        st.session_state["turnos_padrao"] = _db_turnos or _fallback_turnos_padrao
    if "slot_config" not in st.session_state:
        _db_slots = build_slot_config(TENANT_ID)
        if _db_slots:
            st.session_state["slot_config"] = _db_slots
        else:
            st.session_state["slot_config"] = {
                (_d_init, _s_init): {
                    "headcount": 1,
                    "priority": "optional" if "08:00 - 16:00" in _s_init else "essential",
                }
                for _d_init, _t_init in _fallback_turnos_padrao.items()
                for _s_init in _t_init
            }
    turnos_padrao = st.session_state["turnos_padrao"]

    df_equipe_atual = _cached_funcionarios(TENANT_ID, st.session_state.get('equipe_v', 0))
    lista_nomes = df_equipe_atual['nome'].tolist() if not df_equipe_atual.empty else []
    lista_nomes.append("Someone (Other Store)")

    if st.button("🤖 Generate Auto Rota", type="primary", use_container_width=True):
        config_semana = st.session_state.get('config_semana', {})
        if not config_semana:
            st.error("Go to '⚙️ Weekly Setup' and click 'Confirm Weekly Hours' first.")
        else:
            margem = st.session_state.get('margem_horas', 2.0)
            # patch slot_config with any date-specific overrides
            _base_sc = st.session_state.get('slot_config') or {}
            _patched_sc = dict(_base_sc)  # shallow copy — don't mutate session state
            _weekday_map = {0: "Seg", 1: "Ter", 2: "Qua", 3: "Qui", 4: "Sex", 5: "Sáb", 6: "Dom"}
            _today = datetime.date.today()
            _week_start = st.session_state.get(
                "semana_inicio_date", _today - datetime.timedelta(days=_today.weekday())
            )
            _week_dates = [
                (_week_start + datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)
            ]
            _dho_rows = get_date_headcount_overrides(TENANT_ID, _week_dates)
            for _row in _dho_rows:
                _wd = _weekday_map[datetime.date.fromisoformat(_row["override_date"]).weekday()]
                _key = (_wd, _row["shift_label"])
                if _key in _patched_sc:
                    _patched_sc[_key] = dict(_patched_sc[_key])  # don't mutate nested dict
                    _patched_sc[_key]["headcount"] = _row["headcount"]
            df_escala, constraints_warnings = gerar_escala_automatica(
                config_semana, turnos_padrao, margem,
                slot_config=_patched_sc,
                min_dias_folga=get_cafe_min_dias_folga(TENANT_ID),
            )
            st.session_state['roster_df'] = df_escala
            st.session_state['constraints_warnings'] = constraints_warnings
            st.rerun()

    col_btn_vazio, col_btn_reset = st.columns([5, 1])

    if col_btn_vazio.button("🗑️ Manual skeleton"):
        linhas_roster = [
            {"Dia": dia, "Horário": turno, "Funcionário": "To Fill"}
            for dia, turnos in turnos_padrao.items()
            for turno in turnos
        ]
        st.session_state['roster_df'] = pd.DataFrame(linhas_roster)
        st.rerun()

    if 'roster_df' in st.session_state:
        with st.expander("⬇️ Export Rota", expanded=True):
            _rdf = st.session_state['roster_df']
            _semana_lbl = st.session_state.get('_last_semana_label', '')
            ec1, ec2, ec3 = st.columns(3)
            ec1.download_button("📄 CSV", _rdf.to_csv(index=False).encode('utf-8'), "escala.csv", "text/csv")
            _xls_nati = gerar_excel_escala(_rdf, st.session_state.get('config_semana'), _cafe_nome, _semana_lbl)
            ec2.download_button("📊 Excel", _xls_nati, "escala.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            if check_feature_gate(TENANT_ID, "pdf_export"):
                ec3.download_button("🖨️ PDF", gerar_pdf_escala(_rdf, _cafe_nome, _semana_lbl), "escala.pdf", "application/pdf")
            else:
                ec3.info("🔒 PDF — Pro")

    if col_btn_reset.button("🔄", help="Reset rota"):
        for _key in ('roster_df', 'constraints_warnings'):
            st.session_state.pop(_key, None)
        st.rerun()

    if 'roster_df' in st.session_state:
        st.write("### 📝 Ajuste Manual e Status")

        col_tabela_roster, espaco, col_horas = st.columns([5, 1, 3])

        with col_tabela_roster:
            roster_editado = st.data_editor(
                st.session_state['roster_df'],
                column_config={
                    "Dia": st.column_config.TextColumn("Dia"),
                    "Horário": st.column_config.TextColumn("Horário"),
                    "Funcionário": st.column_config.SelectboxColumn("Assigned Staff", options=["To Fill"] + lista_nomes),
                },
                num_rows="dynamic",
                hide_index=True,
                use_container_width=True,
            )

        with col_horas:
            st.write("⏱️ **Live Hours**")
            config_sem = st.session_state.get('config_semana', {})
            margem_disp = st.session_state.get('margem_horas', 2.0)
            horas_atuais = {nome: 0.0 for nome in config_sem.keys() if config_sem[nome]['vai_trabalhar']}

            for idx, row in roster_editado.iterrows():
                func = row['Funcionário']
                if func in horas_atuais:
                    horas_atuais[func] += calcular_horas_turno(str(row['Horário']))

            for func, horas in horas_atuais.items():
                cfg = config_sem[func]
                alvo = cfg['horas_alvo']
                h_treino = cfg.get('horas_treinamento', 0.0) if cfg.get('dias_treinamento') else 0.0
                total = horas + h_treino
                treino_note = f" +{h_treino:.0f}h training" if h_treino else ""
                label = f"{func}: {total:.1f}h{treino_note} (Target: {alvo}h ± {margem_disp:.0f}h)"
                if total > alvo + margem_disp:
                    st.error(f"🔴 {label}")
                elif total < alvo - margem_disp:
                    st.info(f"🔵 {label}")
                else:
                    st.success(f"🟢 {label}")

        st.subheader("🚨 Rule Warnings")
        tem_erro_fechamento, tem_gaps = False, False

        for dia in turnos_padrao.keys():
            turnos_fecho_dia = roster_editado[
                (roster_editado['Dia'] == dia) & (roster_editado['Horário'].fillna('').str.contains("Fechamento"))
            ]
            nomes_no_fecho = turnos_fecho_dia['Funcionário'].tolist()
            if "To Fill" in nomes_no_fecho or "Someone (Other Store)" in nomes_no_fecho:
                tem_gaps = True

            cargos_fecho = df_equipe_atual[df_equipe_atual['nome'].isin(nomes_no_fecho)]['cargo'].tolist()
            if not any(cargo in ["Manager", "Assistant Manager", "Head Barista"] for cargo in cargos_fecho) and len(cargos_fecho) > 0:
                st.error(f"❌ **Closing error ({dia}):** No Manager, Assistant Manager, or Head Barista scheduled.")
                tem_erro_fechamento = True

        if tem_gaps:
            st.warning("⚠️ **Gaps found:** Empty shifts or assigned to 'Someone'.")
        if not tem_erro_fechamento and not tem_gaps:
            st.success("✅ All clear! No rule violations and no gaps.")

        constraints_warnings = st.session_state.get('constraints_warnings', [])
        if constraints_warnings:
            # CP-SAT solver status shown as a standalone banner
            _cpsat = [w for w in constraints_warnings if w.startswith("CP-SAT:")]
            for _cs in _cpsat:
                st.info(f"ℹ️ {_cs}")

            _erros = [w for w in constraints_warnings if any(k in w for k in (
                "turno não atribuído", "limite semanal", "mínimo semanal",
                "clopening inválido", "fechamento sem keyholder"
            ))]
            # >4.5h recommendation and CP-SAT lines go to info; >6h mandatory break stays in warns
            _infos = [w for w in constraints_warnings if "recomendada" in w]
            _warns = [w for w in constraints_warnings
                      if w not in _erros and w not in _infos and not w.startswith("CP-SAT:")]

            if _erros or _warns or _infos:
                label = f"⚠️ Labour Rules ({len(_erros)} error(s), {len(_warns)} warning(s), {len(_infos)} info)"
                with st.expander(label, expanded=bool(_erros)):
                    for w in _erros:
                        st.error(w)
                    for w in _warns:
                        st.warning(w)
                    for w in _infos:
                        st.info(w)

        st.divider()
        if check_feature_gate(TENANT_ID, "roster_history"):
            _sal_col1, _sal_col2 = st.columns([4, 1])
            semana_label = _sal_col1.text_input("", placeholder="Week name (e.g. Week 03/11)", key="semana_label_input", label_visibility="collapsed")
            if _sal_col2.button("💾 Save", key="btn_salvar_roster"):
                if not semana_label.strip():
                    st.warning("Give the week a name before saving.")
                else:
                    dados_json = roster_editado.to_json(orient="records", force_ascii=False)
                    salvar_roster(TENANT_ID, semana_label.strip(), dados_json)
                    st.session_state['_last_semana_label'] = semana_label.strip()
                    st.session_state['roster_v'] += 1
                    st.success(f"Rota '{semana_label}' saved! See full history in the '📊 History' tab.")
                    st.rerun()
        else:
            st.caption("🔒 Save to rota history — available on the Pro plan. Upgrade in the sidebar.")

# ------------------------------------------
# ABA 4: ANÁLISE
# ------------------------------------------
with aba4:
    st.header("📊 History & Analytics")

    st.subheader("💾 Saved Rotas")
    if not check_feature_gate(TENANT_ID, "roster_history"):
        st.info("🔒 Rota History saves every week for auditing and comparison — available on the Pro plan. Upgrade in the sidebar.")
    else:
        df_rosters = _cached_rosters(TENANT_ID, st.session_state['roster_v'])
        if df_rosters.empty:
            st.info("No rotas saved yet. Generate a rota and save it in the '📅 Weekly Rota' tab.")
        else:
            for _, r_row in df_rosters.iterrows():
                r_col1, r_col2, r_col3 = st.columns([3, 2, 1])
                r_col1.write(f"**{r_row['semana']}**")
                r_col2.caption(r_row['criado_em'][:16])
                btn_load = r_col3.button("📂", key=f"hist_load_{r_row['id']}", help="Load")
                btn_del = r_col3.button("🗑️", key=f"hist_del_{r_row['id']}", help="Delete")
                if btn_load:
                    dados = get_roster_by_id(TENANT_ID, int(r_row['id']))
                    if dados:
                        st.session_state['roster_df'] = pd.read_json(dados, orient="records")
                        st.rerun()
                if btn_del:
                    deletar_roster(TENANT_ID, int(r_row['id']))
                    st.session_state['roster_v'] += 1
                    st.rerun()

    st.divider()
    st.subheader("📈 Weekly Analysis")
    if not check_feature_gate(TENANT_ID, "analytics"):
        st.info("🔒 The Analytics panel shows coverage, gaps and hours per staff member — available on the Pro plan. Upgrade in the sidebar.")
    elif 'roster_df' not in st.session_state:
        st.info("Generate or load a rota in the '📅 Weekly Rota' tab first.")
    else:
        _df_an = st.session_state['roster_df']
        _cfg_an = st.session_state.get('config_semana', {})

        total_turnos = len(_df_an)
        preenchidos = len(_df_an[_df_an['Funcionário'] != 'To Fill'])
        gaps = total_turnos - preenchidos
        cobertura = preenchidos / total_turnos * 100 if total_turnos else 0

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Total Shifts", total_turnos)
        col_m2.metric("Filled", preenchidos)
        col_m3.metric("Gaps", gaps, delta=f"-{gaps}" if gaps else None, delta_color="inverse")
        col_m4.metric("Coverage", f"{cobertura:.0f}%")

        st.divider()
        col_c1, col_c2 = st.columns(2)

        with col_c1:
            st.write("⏱️ **Hours per Staff vs. Target**")
            if _cfg_an:
                _horas_fn = {}
                for _, _r in _df_an.iterrows():
                    _fn = _r['Funcionário']
                    if _fn != 'To Fill' and _fn in _cfg_an:
                        _horas_fn[_fn] = _horas_fn.get(_fn, 0.0) + calcular_horas_turno(str(_r['Horário']))
                if _horas_fn:
                    _df_horas = pd.DataFrame([
                        {"Staff": fn,
                         "Assigned": round(h, 1),
                         "Target": _cfg_an[fn]['horas_alvo']}
                        for fn, h in _horas_fn.items()
                    ]).set_index("Staff")
                    st.bar_chart(_df_horas)
                else:
                    st.info("No hours assigned yet.")
            else:
                st.caption("Complete the setup in '⚙️ Weekly Setup' to see the comparison against target.")

        with col_c2:
            st.write("📅 **Coverage by Day**")
            _dias_ordem = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
            _prench_dia = _df_an[_df_an['Funcionário'] != 'To Fill'].groupby('Dia').size()
            _gap_dia = _df_an[_df_an['Funcionário'] == 'To Fill'].groupby('Dia').size()
            _df_cob = pd.DataFrame({
                "Filled": _prench_dia,
                "Gaps": _gap_dia,
            }).fillna(0).reindex(_dias_ordem).fillna(0)
            st.bar_chart(_df_cob)

# ------------------------------------------
# ABA 5: AJUDA
# ------------------------------------------
with aba5:
    if _user.get('role') in ('admin', 'superadmin'):
        st.subheader("⚙️ Café settings")
        _min_dias_folga = st.number_input(
            "Minimum days off per employee per week",
            min_value=1,
            max_value=7,
            value=get_cafe_min_dias_folga(TENANT_ID),
            step=1,
            key="cafe_min_dias_folga",
        )
        if st.button("Save", key="save_cafe_min_dias_folga"):
            try:
                set_cafe_min_dias_folga(TENANT_ID, _min_dias_folga)
                st.success("Minimum days off saved.")
            except Exception as _e:
                st.error(f"Could not save setting: {_e}")
        st.divider()

    st.markdown("""
    <div style="
        background: linear-gradient(135deg,#1a0a3e 0%,#3b1278 60%,#6b2fa0 100%);
        border-radius:14px; padding:2rem 2rem 1.75rem; margin-bottom:1.5rem;
        color:#f0e6ff;
    ">
        <div style="font-size:0.75rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
                    color:#c4a8f0;margin-bottom:.4rem">escala</div>
        <div style="font-size:1.6rem;font-weight:700;margin-bottom:.5rem">
            Welcome! 👋
        </div>
        <div style="font-size:.95rem;opacity:.85;max-width:60ch;line-height:1.6">
            escala is built to make café rota management faster and fairer.
            Here you'll find everything you need to get the most out of each feature.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("🗺️ What each tab does")
    _ov1, _ov2, _ov3, _ov4 = st.columns(4)
    _ov1.info("**👥 Team**\nAdd and edit staff. Set permanent availability and contract hours.")
    _ov2.info("**⚙️ Weekly Setup**\nConfigure this week's exceptions: days off, holidays, training and hour tolerance.")
    _ov3.info("**📅 Weekly Rota**\nGenerate, adjust and export the rota. Review labour rule warnings.")
    _ov4.info("**📊 History**\nCoverage metrics and hours per staff member vs. target.")

    st.divider()

    with st.expander("👥 Team tab", expanded=False):
        st.markdown("#### Adding a new staff member")
        st.markdown("""
1. Fill in **Name**, **Role** and **Contract Type**.
2. Set **Min Hours** and **Max Hours** per week — the scheduler never exceeds these limits.
3. Configure **permanent availability** day by day (see table below).
4. Click **Add**.
        """)
        _d1, _d2 = st.columns(2)
        with _d1:
            st.markdown("**Availability options**")
            st.markdown("""
| Option | Meaning |
|---|---|
| **Available** | Any shift that day |
| **Morning only** | Shifts ending by 14:00 |
| **Afternoon only** | Shifts starting from 12:00 |
| **Unavailable** | Fixed day off — never scheduled |
| **Custom** | Exact hours window |
            """)
        with _d2:
            st.markdown("**Contract types**")
            st.markdown("""
| Contract | Typical hours |
|---|---|
| Full-time | Min 35 / Max 39 h/week |
| Part-time | Min 16 / Max 25 h/week |
            """)
        st.info("💡 **Tip:** Mark days as *Unavailable* for days the person never works. The scheduler handles this automatically without needing any entry in Weekly Setup.")
        st.markdown("#### Editing or deactivating")
        st.markdown("In the right panel, select a name, change the fields and click **Save**. For someone who has left, use **Deactivate** — the record is kept but they no longer appear in the rota.")

    with st.expander("⚙️ Weekly Setup tab", expanded=False):
        st.markdown("#### Always configure the current week before generating a rota")
        st.markdown("""
1. **Hour tolerance (± target)** — how many hours above or below the target are acceptable before triggering a warning. Default: 2h.
2. **For each staff member**, fill in this week's exceptions:
        """)
        _e1, _e2, _e3, _e4 = st.columns(4)
        _e1.success("🏖️ **Day Off**\nDays off this week only (one-off swap).")
        _e2.success("✈️ **Holiday**\nDays the person is on annual leave.")
        _e3.success("📚 **Training**\nDays in training — not included in the rota.")
        _e4.success("⏱️ **Training h.**\nTotal training hours — count toward the weekly total.")
        st.markdown("""
3. Adjust **Target Hours** if the week is atypical (bank holiday, short week…).
4. Click **Confirm Weekly Hours** — only after this does the scheduler have data to work with.
        """)
        st.warning("⚠️ You cannot mark the same day as both Day Off and Training — the system blocks this and explains the conflict.")
        st.info("💡 Weekly setup is **not automatically saved** between weeks — you always start fresh in Weekly Setup each week.")

    with st.expander("📅 Weekly Rota tab", expanded=False):
        st.markdown("#### The three main buttons")
        _b1, _b2, _b3 = st.columns(3)
        _b1.info("🗑️ **Manual Skeleton**\nCreates the table with all shifts set to *To Fill*. Fill in manually.")
        _b2.info("🤖 **Generate Auto Rota**\nThe scheduler distributes the team across shifts respecting availability, contracts and labour rules.")
        _b3.info("🔄 **Reset**\nClears the draft so you can start over.")

        st.markdown("#### Manual adjustments")
        st.markdown("""
After generating, you can edit the table: click the **Assigned Staff** cell and change the name.
Shifts showing **To Fill** are ones the scheduler could not fill — handle those first.
The **Live Hours** panel on the right confirms each person's weekly total.
        """)

        st.markdown("#### Export")
        st.markdown("Click the **⬇️ Export Rota** panel to download in three formats:")
        _x1, _x2, _x3 = st.columns(3)
        _x1.success("📄 **CSV** — open in Excel or Google Sheets.")
        _x2.success("📊 **Excel** — formatted .xlsx file.")
        _x3.success("🖨️ **PDF** — A4 landscape, ideal for printing or sending.")

        st.markdown("#### Rota History")
        st.markdown("""
1. Give the week a name (e.g. *Week 47 — Nov 2026*) and click **Save**.
2. In *Saved Rotas*, use 📂 to load or 🗑️ to delete a previous week.
        """)

    with st.expander("📊 History tab", expanded=False):
        st.markdown("""
The analytics panel updates automatically whenever the rota changes in the Weekly Rota tab.

| Metric | What it shows |
|---|---|
| **Total Shifts** | All shifts configured for the week |
| **Filled** | How many have an assigned staff member |
| **Gaps** | Shifts still *To Fill* — the goal is zero |
| **Coverage %** | Percentage of filled shifts. Target: 100% |

The **Hours per Staff vs. Target** chart only appears after you configure the week in Weekly Setup.
        """)

    st.divider()

    st.subheader("⚠️ Warnings explained")

    st.markdown("The app automatically checks labour rules after generating the rota. Warnings have three levels:")
    _av1, _av2, _av3 = st.columns(3)
    _av1.error("🔴 **Errors** — Serious situations to resolve before approving the rota (shift without a keyholder, hours limit exceeded).")
    _av2.warning("🟡 **Warnings** — Situations to review but that don't block (hours outside margin, clopening).")
    _av3.info("🔵 **Info** — Best-practice recommendations (breaks on long shifts).")

    st.markdown("#### Most common warnings")
    with st.expander("🔴 Shift unassigned — no eligible keyholder"):
        st.markdown("""
**What it means:** Closing shifts require a **Manager**, **Assistant Manager** or **Head Barista**.
If none of these are available that day, the shift cannot be filled.

**How to fix:** Check in the Team tab that the person with the right role has that day as *Available* or *Custom*.
If not, manually assign the shift in the table.
        """)
    with st.expander("🔴 Invalid clopening"):
        st.markdown("""
**What it means:** The person closed one day (shift ends after 17:00) and is scheduled to open
the next day with less than 11h of rest between shifts — prohibited by labour law.

**How to fix:** Swap the opening shift with another person who has enough rest time.
        """)
    with st.expander("🔴 Closing shift without a keyholder"):
        st.markdown("""
**What it means:** A closing shift has been assigned to someone who does not have
closing authorisation (role is not Manager or Head Barista).

**How to fix:** Manually assign the shift to someone with the appropriate role.
        """)
    with st.expander("🟡 Hours above/below the margin"):
        st.markdown("""
**What it means:** The person's total hours fell outside the comfort zone
(*Target ± Tolerance* set in Weekly Setup). It doesn't violate the contract, but it's not ideal.

**How to fix:** Manually adjust a shift, or increase the tolerance in Weekly Setup if acceptable.
        """)
    with st.expander("🟡 7 consecutive days without a day off (WTI)"):
        st.markdown("""
**What it means:** The person has been scheduled all 7 days of the week with no rest day —
this violates the minimum of 1 rest day per week required by law.

**How to fix:** Mark at least 1 day as *Day Off* in Weekly Setup or *Unavailable* in the Team tab.
        """)
    with st.expander("🔵 Shift >6h — mandatory 30-min break (WTI)"):
        st.markdown("""
**What it means:** A shift of more than 6 hours requires a 30-minute break by law.
The app warns but cannot enforce the break — you need to communicate this to the person.

**Suggestion:** Consider splitting the shift in two or ensuring the break is marked in the schedule.
        """)
    with st.expander("🔵 Shift >4.5h — 15-min break recommended"):
        st.markdown("""
**What it means:** Best-practice recommendation for shifts between 4.5h and 6h.
Not legally required but good practice for team wellbeing.
        """)

    st.divider()

    st.subheader("✅ Recommended weekly workflow")
    _f1, _f2, _f3, _f4 = st.columns(4)
    _f1.success("**1️⃣ Team**\nUpdate the team if someone joined, left or changed role.")
    _f2.success("**2️⃣ Weekly Setup**\nConfigure days off, holidays and training for this week. Confirm.")
    _f3.success("**3️⃣ Weekly Rota**\nGenerate the auto rota. Review warnings. Adjust manually if needed. Export.")
    _f4.success("**4️⃣ History**\nConfirm coverage is at 100% and hours are balanced.")

    if not _is_pro:
        st.info("💡 **On a paid plan** your café gets a larger staff limit. Upgrade in the sidebar.")
