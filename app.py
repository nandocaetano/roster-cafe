"""Streamlit UI for Gerador de Escalas — imports all logic from database.py and logic.py."""
import io
import re
import streamlit as st
import pandas as pd

import json

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
    salvar_roster,
    get_rosters,
    get_roster_by_id,
    deletar_roster,
)
from logic import calcular_horas_turno, gerar_escala_automatica, gerar_pdf_escala

# ==========================================
# UI HELPERS
# ==========================================

def render_availability_selector(prefix, defaults=None):
    """Render a 7-day availability selector and return the list of chosen values."""
    if defaults is None:
        defaults = ["Livre"] * 7

    dias = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    opcoes = ["Livre", "Só Manhã", "Só Tarde", "Indisponível", "Específico"]
    resultados = []

    st.write("**Disponibilidade na Semana**")
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

            selecao = st.selectbox(dia, opcoes, index=idx_opcao, key=f"{prefix}_sel_{dia}")

            if selecao == "Específico":
                sh_def, sm_def, eh_def, em_def = 9, 0, 17, 0
                if texto_especifico:
                    _t = re.findall(r'(\d{1,2}):(\d{2})', texto_especifico)
                    if len(_t) == 2:
                        sh_def, sm_def = int(_t[0][0]), int(_t[0][1])
                        eh_def, em_def = int(_t[1][0]), int(_t[1][1])
                st.caption("De:")
                _ch, _cm = st.columns(2)
                sh = _ch.number_input("H", 0, 23, sh_def, 1, format="%02d", key=f"{prefix}_sh_{dia}", label_visibility="collapsed")
                sm = _cm.number_input("M", 0, 59, sm_def, 5, format="%02d", key=f"{prefix}_sm_{dia}", label_visibility="collapsed")
                st.caption("Até:")
                _eh, _em = st.columns(2)
                eh = _eh.number_input("H", 0, 23, eh_def, 1, format="%02d", key=f"{prefix}_eh_{dia}", label_visibility="collapsed")
                em = _em.number_input("M", 0, 59, em_def, 5, format="%02d", key=f"{prefix}_em_{dia}", label_visibility="collapsed")
                resultados.append(f"Específico: {int(sh):02d}:{int(sm):02d} - {int(eh):02d}:{int(em):02d}")
            else:
                resultados.append(selecao)

    return resultados


# ==========================================
# APP SETUP
# ==========================================
st.set_page_config(page_title="Gerador de Escalas", layout="wide")
init_db()

if 'user' not in st.session_state:
    st.session_state['user'] = None

# ------------------------------------------
# AUTH GATE: Login / Register
# ------------------------------------------
if st.session_state['user'] is None:
    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] > .main {
        background: linear-gradient(135deg, #1a0a3e 0%, #3b1278 55%, #6b2fa0 100%);
        min-height: 100vh;
    }
    [data-testid="stHeader"] { background: transparent !important; }
    [data-testid="stDecoration"] { display: none; }
    [data-testid="stToolbar"] { display: none; }
    section[data-testid="stMain"] [data-testid="stForm"] {
        background: rgba(18, 15, 35, 0.96);
        border-radius: 18px;
        padding: 2.5rem 2.2rem 2rem 2.2rem;
        border: 1px solid rgba(140, 90, 200, 0.25);
        box-shadow: 0 28px 72px rgba(0, 0, 0, 0.55);
    }
    [data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(90deg, #7c3aed, #9c5cf7) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        letter-spacing: 0.4px;
        transition: opacity 0.15s;
    }
    [data-testid="stFormSubmitButton"] > button:hover {
        opacity: 0.88;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([3, 2, 3])
    with col_login:
        st.markdown("<h2 style='text-align:center;margin-bottom:4px'>☕ Gerenciador de Escalas</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center;color:#a78bfa;margin-bottom:1.2rem'>Acesso à Plataforma</p>", unsafe_allow_html=True)
        with st.form("form_login"):
            email_login = st.text_input("Email", placeholder="voce@cafe.com")
            senha_login = st.text_input("Senha", type="password", placeholder="••••••••")
            if st.form_submit_button("Entrar", use_container_width=True):
                user = verify_credentials(email_login, senha_login)
                if user:
                    st.session_state['user'] = user
                    st.session_state['tenant_id'] = user['tenant_id']
                    st.rerun()
                else:
                    st.error("Email ou senha incorretos.")

    st.stop()

# ------------------------------------------
# AUTHENTICATED: resolve tenant + sidebar
# ------------------------------------------
TENANT_ID = st.session_state['tenant_id']
_user = st.session_state['user']
_cafe = get_cafe_by_id(TENANT_ID)
_cafe_nome = _cafe['name'] if _cafe else "Cafe"

with st.sidebar:
    st.markdown(f"### ☕ {_cafe_nome}")
    st.write(f"👤 {_user['email']}")
    st.write(f"🔖 {_user['role'].capitalize()}")
    st.divider()
    if _user.get('role') == 'superadmin':
        with st.expander("➕ Registrar Novo Cafe"):
            with st.form("form_novo_cafe_sidebar"):
                _nc_nome = st.text_input("Nome do Cafe", key="nc_nome")
                _nc_email = st.text_input("Email do Admin", key="nc_email")
                _nc_senha = st.text_input("Senha", type="password", key="nc_senha")
                _nc_conf = st.text_input("Confirmar Senha", type="password", key="nc_conf")
                if st.form_submit_button("Cadastrar"):
                    if _nc_senha != _nc_conf:
                        st.error("As senhas não coincidem.")
                    elif not _nc_nome or not _nc_email or not _nc_senha:
                        st.error("Preencha todos os campos.")
                    else:
                        try:
                            _ntid = criar_cafe(_nc_nome, _nc_email)
                            create_user(_ntid, _nc_email, _nc_senha, role="admin")
                            st.success(f"'{_nc_nome}' cadastrado!")
                        except Exception as _e:
                            st.error(f"Erro: {_e}")
    st.divider()
    if st.button("🚪 Logout"):
        st.session_state['user'] = None
        st.session_state['tenant_id'] = None
        st.rerun()

st.title("☕ Gerenciador de Escalas - Cafe")

aba1, aba2, aba3, aba4, aba5 = st.tabs(["👥 Gestão do Time", "⚙️ Setup da Semana", "📅 Rascunho e Aprovação", "📊 Análise", "📖 Ajuda"])

lista_cargos_oficiais = ["Manager", "Assistant Manager", "Head Barista", "Barista"]

# ------------------------------------------
# ABA 1: GESTÃO DO TIME
# ------------------------------------------
with aba1:
    st.header("Equipe Atual")
    df_equipe = get_funcionarios_ativos(TENANT_ID)

    espaco_esq, col_tabela, espaco_dir = st.columns([1, 6, 1])
    with col_tabela:
        if not df_equipe.empty:
            st.dataframe(df_equipe[['nome', 'cargo', 'tipo_contrato', 'horas_min', 'horas_max']], use_container_width=True)
        else:
            st.info("Nenhum funcionário cadastrado ainda.")

    st.divider()
    col1, col_espaco, col2 = st.columns([4, 1, 4])

    with col1:
        st.subheader("➕ Novo Funcionário")
        if 'novo_k' not in st.session_state:
            st.session_state['novo_k'] = 0
        _nk = st.session_state['novo_k']

        nome_novo = st.text_input("Nome", key=f"novo_nome_{_nk}")
        c_cargo, c_contrato = st.columns(2)
        cargo_novo = c_cargo.selectbox("Cargo", lista_cargos_oficiais, key=f"novo_cargo_{_nk}")
        contrato_novo = c_contrato.selectbox("Contrato", ["Full-time", "Part-time"], key=f"novo_contrato_{_nk}")

        c_min, c_max = st.columns(2)
        h_min_nova = c_min.number_input("Horas Mín.", min_value=0, max_value=60, value=20, key=f"novo_hmin_{_nk}")
        h_max_nova = c_max.number_input("Horas Máx.", min_value=0, max_value=60, value=39, key=f"novo_hmax_{_nk}")

        dias_selecionados = render_availability_selector(f"novo_{_nk}")

        if st.button("Cadastrar", key=f"novo_btn_{_nk}") and nome_novo:
            try:
                adicionar_funcionario(TENANT_ID, nome_novo, cargo_novo, contrato_novo, h_min_nova, h_max_nova, dias_selecionados)
                st.success(f"{nome_novo} adicionado!")
                st.session_state['novo_k'] += 1
                st.rerun()
            except ValueError as _ve:
                if "limite_funcionarios" in str(_ve):
                    st.error("Limite de 20 funcionários atingido para esta licença. Contacte o suporte para fazer upgrade.")
                else:
                    st.error(f"Erro ao cadastrar: {_ve}")

    with col2:
        st.subheader("✏️ Editar ou Remover")
        if not df_equipe.empty:
            func_selecionado = st.selectbox("Selecione um funcionário", df_equipe['nome'].tolist())
            dados_atuais = df_equipe[df_equipe['nome'] == func_selecionado].iloc[0]

            _pfx = f"ed_{func_selecionado}"
            nome_ed = st.text_input("Nome", value=dados_atuais['nome'], key=f"{_pfx}_nome")
            c_cargo_ed, c_contrato_ed = st.columns(2)
            idx_cargo = lista_cargos_oficiais.index(dados_atuais['cargo']) if dados_atuais['cargo'] in lista_cargos_oficiais else 3
            cargo_ed = c_cargo_ed.selectbox("Cargo", lista_cargos_oficiais, index=idx_cargo, key=f"{_pfx}_cargo")
            idx_contrato = 0 if dados_atuais['tipo_contrato'] == "Full-time" else 1
            contrato_ed = c_contrato_ed.selectbox("Contrato", ["Full-time", "Part-time"], index=idx_contrato, key=f"{_pfx}_contrato")

            c_min_ed, c_max_ed = st.columns(2)
            h_min_ed = c_min_ed.number_input("Horas Mín.", min_value=0, max_value=60, value=int(dados_atuais['horas_min']), key=f"{_pfx}_hmin")
            h_max_ed = c_max_ed.number_input("Horas Máx.", min_value=0, max_value=60, value=int(dados_atuais['horas_max']), key=f"{_pfx}_hmax")

            dias_atuais = [
                dados_atuais['d_seg'], dados_atuais['d_ter'], dados_atuais['d_qua'],
                dados_atuais['d_qui'], dados_atuais['d_sex'], dados_atuais['d_sab'], dados_atuais['d_dom']
            ]
            dias_ed = render_availability_selector(_pfx, dias_atuais)

            col_btn1, col_btn2 = st.columns(2)
            if col_btn1.button("💾 Salvar", key=f"{_pfx}_salvar"):
                atualizar_funcionario(TENANT_ID, int(dados_atuais['id_funcionario']), nome_ed, cargo_ed, contrato_ed, h_min_ed, h_max_ed, dias_ed)
                st.success("Atualizado!")
                for _sk in [k for k in st.session_state if k.startswith(f"ed_{func_selecionado}")]:
                    del st.session_state[_sk]
                st.rerun()
            if col_btn2.button("❌ Desativar", key=f"{_pfx}_desativar"):
                desativar_funcionario(TENANT_ID, int(dados_atuais['id_funcionario']))
                st.warning("Removido.")
                st.rerun()

# ------------------------------------------
# ABA 2: SETUP DA SEMANA
# ------------------------------------------
with aba2:
    st.header("Seleção Semanal e Budget")
    esp_esq, col_setup, esp_dir = st.columns([1, 4, 1])

    with col_setup:
        if not df_equipe.empty:
            total_horas_planejadas = 0
            dias_semana_opts = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
            with st.form("form_setup_semana"):
                st.write("Defina quem entra na escala esta semana e ajuste as metas de horas.")
                margem_horas = st.number_input(
                    "Margem de horas tolerada (± alvo)", min_value=0.0, max_value=10.0,
                    value=2.0, step=0.5, key="margem_horas_input",
                    help="Alerta se as horas reais saírem desta margem do alvo."
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
                        dias_str = "Indisponível todos os dias"

                    c_info.write(f"**{row['nome']}** ({row['cargo']})  \n*Disp: {dias_str}*")
                    vai_trabalhar = c_check.checkbox("Escalar", key=f"chk_{row['nome']}", value=True)
                    horas_alvo = c_horas.number_input("Horas Alvo", min_value=0, max_value=60, value=int(row['horas_max']), key=f"hrs_{row['nome']}")

                    c_folga, c_ferias, c_treino, c_htreino = st.columns([2, 2, 2, 1])
                    dias_folga_sel = c_folga.multiselect("🏖️ Folga", dias_semana_opts, default=[], key=f"folga_{row['nome']}")
                    dias_ferias_sel = c_ferias.multiselect("✈️ Férias", dias_semana_opts, default=[], key=f"ferias_{row['nome']}")
                    dias_treino_sel = c_treino.multiselect("📚 Treinamento", dias_semana_opts, default=[], key=f"treino_{row['nome']}")
                    horas_treino = c_htreino.number_input("H. Treino", min_value=0, max_value=40, value=0, key=f"htreino_{row['nome']}", help="Total horas de treinamento esta semana.")

                    if vai_trabalhar:
                        total_horas_planejadas += horas_alvo

                    disp_dict = {d[0]: d[1] for d in dias_map}
                    inputs_semana[row['nome']] = {
                        "vai_trabalhar": vai_trabalhar,
                        "horas_alvo": horas_alvo,
                        "horas_min": float(row['horas_min']),
                        "horas_max": float(row['horas_max']),
                        "cargo": row['cargo'],
                        "disponibilidade": disp_dict,
                        "dias_folga": list(dias_folga_sel),
                        "dias_ferias": list(dias_ferias_sel),
                        "dias_treinamento": list(dias_treino_sel),
                        "horas_treinamento": float(horas_treino),
                    }
                    st.divider()

                if st.form_submit_button("Confirmar Horas da Semana"):
                    conflitos = []
                    for nome, cfg in inputs_semana.items():
                        dias_overlap = set(cfg["dias_folga"]) & set(cfg["dias_treinamento"])
                        if dias_overlap:
                            conflitos.append(f"{nome}: {', '.join(sorted(dias_overlap))} marcado como Folga e Treinamento.")
                        dias_overlap2 = set(cfg["dias_ferias"]) & set(cfg["dias_treinamento"])
                        if dias_overlap2:
                            conflitos.append(f"{nome}: {', '.join(sorted(dias_overlap2))} marcado como Férias e Treinamento.")
                    if conflitos:
                        for c in conflitos:
                            st.warning(f"⚠️ Conflito: {c}")
                    else:
                        st.session_state['config_semana'] = inputs_semana
                        st.session_state['margem_horas'] = margem_horas
                        st.success("Setup salvo! Vá para a Aba 3 gerar a escala.")

            st.subheader("📊 Status do Budget")
            progresso = total_horas_planejadas / 305.0 if total_horas_planejadas <= 305 else 1.0
            st.progress(progresso)
            if total_horas_planejadas < 290:
                st.warning(f"Total: {total_horas_planejadas}h (Abaixo do ideal).")
            elif 290 <= total_horas_planejadas <= 300:
                st.success(f"Total: {total_horas_planejadas}h (Perfeito).")
            elif 300 < total_horas_planejadas <= 305:
                st.warning(f"Total: {total_horas_planejadas}h (Margem de erro).")
            else:
                st.error(f"Total: {total_horas_planejadas}h (Estourado).")
        else:
            st.warning("Cadastre os funcionários na Aba 1 primeiro.")

# ------------------------------------------
# ABA 3: ROSTER E PAINEL DE HORAS
# ------------------------------------------
with aba3:
    st.header("📅 Escala da Semana")

    turnos_padrao = {
        "Seg": ["07:00 - 12:00", "07:00 - 14:00", "07:30 - 15:00", "08:00 - 16:00", "09:00 - 18:15 (Fechamento)", "12:00 - 18:15 (Fechamento)", "14:00 - 18:15 (Fechamento)"],
        "Ter": ["07:00 - 12:00", "07:00 - 14:00", "07:30 - 15:00", "08:00 - 16:00", "09:00 - 18:15 (Fechamento)", "12:00 - 18:15 (Fechamento)", "14:00 - 18:15 (Fechamento)"],
        "Qua": ["06:30 - 12:00", "07:00 - 14:00", "07:00 - 14:00", "07:30 - 15:00", "09:00 - 18:15 (Fechamento)", "12:00 - 18:15 (Fechamento)", "14:00 - 18:15 (Fechamento)"],
        "Qui": ["07:00 - 12:00", "07:00 - 14:00", "07:30 - 15:00", "08:00 - 16:00", "09:00 - 18:15 (Fechamento)", "12:00 - 18:15 (Fechamento)", "14:00 - 18:15 (Fechamento)"],
        "Sex": ["07:00 - 12:00", "07:00 - 14:00", "07:30 - 15:00", "08:00 - 16:00", "09:00 - 18:15 (Fechamento)", "12:00 - 18:15 (Fechamento)", "14:00 - 18:15 (Fechamento)"],
        "Sáb": ["07:30 - 14:00", "07:30 - 15:00", "09:00 - 18:15 (Fechamento)", "12:00 - 18:15 (Fechamento)", "14:00 - 18:15 (Fechamento)"],
        "Dom": ["07:30 - 14:00", "07:30 - 15:00", "09:00 - 18:15 (Fechamento)", "12:00 - 18:15 (Fechamento)", "14:00 - 18:15 (Fechamento)"],
    }

    df_equipe_atual = get_funcionarios_ativos(TENANT_ID)
    lista_nomes = df_equipe_atual['nome'].tolist() if not df_equipe_atual.empty else []
    lista_nomes.append("Someone (Outra Loja)")

    col_btn_vazio, col_btn_auto, col_btn_reset = st.columns(3)

    if col_btn_vazio.button("🗑️ Gerar Esqueleto Vazio"):
        linhas_roster = [
            {"Dia": dia, "Horário": turno, "Funcionário": "A Preencher"}
            for dia, turnos in turnos_padrao.items()
            for turno in turnos
        ]
        st.session_state['roster_df'] = pd.DataFrame(linhas_roster)
        st.rerun()

    if col_btn_auto.button("🤖 Gerar Escala Automática", type="primary"):
        config_semana = st.session_state.get('config_semana', {})
        if not config_semana:
            st.error("Erro: Vá na Aba 2 e clique em 'Confirmar Horas da Semana' primeiro.")
        else:
            margem = st.session_state.get('margem_horas', 2.0)
            df_escala, constraints_warnings = gerar_escala_automatica(config_semana, turnos_padrao, margem)
            st.session_state['roster_df'] = df_escala
            st.session_state['constraints_warnings'] = constraints_warnings
            st.rerun()

    if 'roster_df' in st.session_state:
        with st.expander("⬇️ Exportar Escala"):
            _rdf = st.session_state['roster_df']
            _semana_lbl = st.session_state.get('_last_semana_label', '')
            ec1, ec2, ec3 = st.columns(3)
            ec1.download_button("📄 CSV", _rdf.to_csv(index=False).encode('utf-8'), "escala.csv", "text/csv")
            _xls = io.BytesIO()
            _rdf.to_excel(_xls, index=False, engine='openpyxl')
            ec2.download_button("📊 Excel", _xls.getvalue(), "escala.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            ec3.download_button("🖨️ PDF", gerar_pdf_escala(_rdf, _cafe_nome, _semana_lbl), "escala.pdf", "application/pdf")

    if col_btn_reset.button("🔄 Resetar Aba"):
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
                    "Funcionário": st.column_config.SelectboxColumn("Funcionário Atribuído", options=["A Preencher"] + lista_nomes),
                },
                num_rows="dynamic",
                hide_index=True,
                use_container_width=True,
            )

        with col_horas:
            st.write("⏱️ **Horas Dinâmicas**")
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
                treino_note = f" +{h_treino:.0f}h treino" if h_treino else ""
                label = f"{func}: {total:.1f}h{treino_note} (Alvo: {alvo}h ± {margem_disp:.0f}h)"
                if total > alvo + margem_disp:
                    st.error(f"🔴 {label}")
                elif total < alvo - margem_disp:
                    st.info(f"🔵 {label}")
                else:
                    st.success(f"🟢 {label}")

        st.subheader("🚨 Avisos de Regras")
        tem_erro_fechamento, tem_gaps = False, False

        for dia in turnos_padrao.keys():
            turnos_fecho_dia = roster_editado[
                (roster_editado['Dia'] == dia) & (roster_editado['Horário'].fillna('').str.contains("Fechamento"))
            ]
            nomes_no_fecho = turnos_fecho_dia['Funcionário'].tolist()
            if "A Preencher" in nomes_no_fecho or "Someone (Outra Loja)" in nomes_no_fecho:
                tem_gaps = True

            cargos_fecho = df_equipe_atual[df_equipe_atual['nome'].isin(nomes_no_fecho)]['cargo'].tolist()
            if not any(cargo in ["Manager", "Assistant Manager", "Head Barista"] for cargo in cargos_fecho) and len(cargos_fecho) > 0:
                st.error(f"❌ **Erro no Fechamento ({dia}):** Nenhum Manager, Assistant ou Head Barista escalado.")
                tem_erro_fechamento = True

        if tem_gaps:
            st.warning("⚠️ **Gaps Encontrados:** Turnos vazios ou designados a 'Someone'.")
        if not tem_erro_fechamento and not tem_gaps:
            st.success("✅ Tudo Certo! Nenhuma regra quebrada e sem gaps.")

        constraints_warnings = st.session_state.get('constraints_warnings', [])
        if constraints_warnings:
            _erros = [w for w in constraints_warnings if any(k in w for k in (
                "turno não atribuído", "limite semanal", "mínimo semanal",
                "clopening inválido", "fechamento sem keyholder"
            ))]
            _infos = [w for w in constraints_warnings if "recomendada" in w]
            _warns = [w for w in constraints_warnings if w not in _erros and w not in _infos]
            label = f"⚠️ Avisos de Regras Trabalhistas ({len(_erros)} erro(s), {len(_warns)} aviso(s), {len(_infos)} info)"
            with st.expander(label, expanded=bool(_erros)):
                for w in _erros:
                    st.error(w)
                for w in _warns:
                    st.warning(w)
                for w in _infos:
                    st.info(w)

        st.divider()
        st.subheader("💾 Histórico de Escalas")
        col_salvar, col_historico = st.columns([2, 3])

        with col_salvar:
            st.write("**Salvar escala atual**")
            semana_label = st.text_input("Rótulo da semana", placeholder="ex: Semana 03/11", key="semana_label_input")
            if st.button("💾 Salvar Escala", key="btn_salvar_roster"):
                if not semana_label.strip():
                    st.warning("Digite um rótulo para identificar a semana.")
                else:
                    dados_json = roster_editado.to_json(orient="records", force_ascii=False)
                    salvar_roster(TENANT_ID, semana_label.strip(), dados_json)
                    st.session_state['_last_semana_label'] = semana_label.strip()
                    st.success(f"Escala '{semana_label}' salva!")
                    st.rerun()

        with col_historico:
            st.write("**Escalas salvas**")
            df_rosters = get_rosters(TENANT_ID)
            if df_rosters.empty:
                st.info("Nenhuma escala salva ainda.")
            else:
                for _, r_row in df_rosters.iterrows():
                    r_col1, r_col2, r_col3 = st.columns([3, 2, 1])
                    r_col1.write(f"**{r_row['semana']}**")
                    r_col2.caption(r_row['criado_em'][:16])
                    btn_load = r_col3.button("📂", key=f"load_{r_row['id']}", help="Carregar")
                    btn_del = r_col3.button("🗑️", key=f"del_{r_row['id']}", help="Apagar")
                    if btn_load:
                        dados = get_roster_by_id(TENANT_ID, int(r_row['id']))
                        if dados:
                            st.session_state['roster_df'] = pd.read_json(dados, orient="records")
                            st.rerun()
                    if btn_del:
                        deletar_roster(TENANT_ID, int(r_row['id']))
                        st.rerun()

# ------------------------------------------
# ABA 4: ANÁLISE
# ------------------------------------------
with aba4:
    st.header("📊 Análise da Semana")

    if 'roster_df' not in st.session_state:
        st.info("Gere ou carregue uma escala na Aba 3 primeiro.")
    else:
        _df_an = st.session_state['roster_df']
        _cfg_an = st.session_state.get('config_semana', {})

        total_turnos = len(_df_an)
        preenchidos = len(_df_an[_df_an['Funcionário'] != 'A Preencher'])
        gaps = total_turnos - preenchidos
        cobertura = preenchidos / total_turnos * 100 if total_turnos else 0

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Total de Turnos", total_turnos)
        col_m2.metric("Preenchidos", preenchidos)
        col_m3.metric("Gaps", gaps, delta=f"-{gaps}" if gaps else None, delta_color="inverse")
        col_m4.metric("Cobertura", f"{cobertura:.0f}%")

        st.divider()
        col_c1, col_c2 = st.columns(2)

        with col_c1:
            st.write("⏱️ **Horas por Funcionário vs. Alvo**")
            if _cfg_an:
                _horas_fn = {}
                for _, _r in _df_an.iterrows():
                    _fn = _r['Funcionário']
                    if _fn != 'A Preencher' and _fn in _cfg_an:
                        _horas_fn[_fn] = _horas_fn.get(_fn, 0.0) + calcular_horas_turno(str(_r['Horário']))
                if _horas_fn:
                    _df_horas = pd.DataFrame([
                        {"Funcionário": fn,
                         "Atribuídas": round(h, 1),
                         "Alvo": _cfg_an[fn]['horas_alvo']}
                        for fn, h in _horas_fn.items()
                    ]).set_index("Funcionário")
                    st.bar_chart(_df_horas)
                else:
                    st.info("Nenhuma hora atribuída ainda.")
            else:
                st.caption("Configure a semana na Aba 2 para ver comparativo com alvo.")

        with col_c2:
            st.write("📅 **Cobertura por Dia**")
            _dias_ordem = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
            _prench_dia = _df_an[_df_an['Funcionário'] != 'A Preencher'].groupby('Dia').size()
            _gap_dia = _df_an[_df_an['Funcionário'] == 'A Preencher'].groupby('Dia').size()
            _df_cob = pd.DataFrame({
                "Preenchidos": _prench_dia,
                "Gaps": _gap_dia,
            }).fillna(0).reindex(_dias_ordem).fillna(0)
            st.bar_chart(_df_cob)

# ------------------------------------------
# ABA 5: AJUDA
# ------------------------------------------
with aba5:
    # ── Boas-vindas ──
    st.markdown("""
    <div style="
        background: linear-gradient(135deg,#1a0a3e 0%,#3b1278 60%,#6b2fa0 100%);
        border-radius:14px; padding:2rem 2rem 1.75rem; margin-bottom:1.5rem;
        color:#f0e6ff;
    ">
        <div style="font-size:0.75rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
                    color:#c4a8f0;margin-bottom:.4rem">Gerenciador de Escalas</div>
        <div style="font-size:1.6rem;font-weight:700;margin-bottom:.5rem">
            Bem-vindo! 👋
        </div>
        <div style="font-size:.95rem;opacity:.85;max-width:60ch;line-height:1.6">
            Este app foi pensado para tornar a gestão de escalas do café mais rápida e justa.
            Aqui encontras tudo o que precisas saber para tirar o máximo partido de cada funcionalidade.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Visão geral das abas ──
    st.subheader("🗺️ O que faz cada aba")
    _ov1, _ov2, _ov3, _ov4 = st.columns(4)
    _ov1.info("**👥 Aba 1 — Equipa**\nCadastra e edita funcionários. Define disponibilidade permanente e horas de contrato.")
    _ov2.info("**⚙️ Aba 2 — Semana**\nConfigura exceções desta semana: folga, férias, treinamento e margem de horas.")
    _ov3.info("**📅 Aba 3 — Escala**\nGera, ajusta e exporta a escala. Vê os avisos de regras trabalhistas.")
    _ov4.info("**📊 Aba 4 — Análise**\nMétricas de cobertura e comparativo de horas por funcionário.")

    st.divider()

    # ── ABA 1 ──
    with st.expander("👥 Aba 1 — Gestão do Time", expanded=False):
        st.markdown("#### Cadastrar um novo funcionário")
        st.markdown("""
1. Preenche **Nome**, **Cargo** e **Tipo de Contrato**.
2. Define as **Horas Mín.** e **Horas Máx.** semanais — o robô nunca passa estes limites.
3. Configura a **disponibilidade permanente** dia a dia (ver tabela abaixo).
4. Clica **Cadastrar**.
        """)
        _d1, _d2 = st.columns(2)
        with _d1:
            st.markdown("**Opções de disponibilidade**")
            st.markdown("""
| Opção | Significado |
|---|---|
| **Livre** | Qualquer turno nesse dia |
| **Só Manhã** | Turnos que acabam até às 14h |
| **Só Tarde** | Turnos a partir das 12h |
| **Indisponível** | Folga fixa — nunca escalado |
| **Específico** | Intervalo exato de horas |
            """)
        with _d2:
            st.markdown("**Tipos de contrato**")
            st.markdown("""
| Contrato | Horas habituais |
|---|---|
| Full-time | Mín 35 / Máx 39 h/semana |
| Part-time | Mín 16 / Máx 25 h/semana |
            """)
        st.info("💡 **Dica:** Marca como *Indisponível* os dias que a pessoa nunca trabalha. O robô trata a folga automaticamente sem configurares nada na Aba 2.")
        st.markdown("#### Editar ou desativar")
        st.markdown("No painel da direita, seleciona o nome, altera os campos e clica **Salvar**. Para alguém que saiu da equipa, usa **Desativar** — o registo fica guardado mas deixa de aparecer na escala.")

    # ── ABA 2 ──
    with st.expander("⚙️ Aba 2 — Setup da Semana", expanded=False):
        st.markdown("#### Antes de gerar a escala, configura sempre a semana atual")
        st.markdown("""
1. **Margem de horas tolerada (± alvo)** — quantas horas acima ou abaixo do alvo são aceitáveis antes de gerar aviso. Padrão: 2h.
2. **Para cada funcionário**, preenche as exceções desta semana:
        """)
        _e1, _e2, _e3, _e4 = st.columns(4)
        _e1.success("🏖️ **Folga**\nDias de folga só esta semana (troca pontual).")
        _e2.success("✈️ **Férias**\nDias em que a pessoa está de férias.")
        _e3.success("📚 **Treinamento**\nDias em formação — não entra na escala.")
        _e4.success("⏱️ **H. Treino**\nTotal de horas de formação — contam no total semanal.")
        st.markdown("""
3. Ajusta **Horas Alvo, Mín e Máx** se a semana for atípica (feriado, semana curta…).
4. Clica **Guardar Configuração da Semana** — só depois disto o robô tem dados para trabalhar.
        """)
        st.warning("⚠️ Não podes marcar o mesmo dia em Folga e Treinamento ao mesmo tempo — o sistema bloqueia e explica o conflito.")
        st.info("💡 As configurações da semana **não ficam guardadas** — começas sempre do zero na Aba 2 a cada semana.")

    # ── ABA 3 ──
    with st.expander("📅 Aba 3 — Rascunho e Aprovação", expanded=False):
        st.markdown("#### Os três botões principais")
        _b1, _b2, _b3 = st.columns(3)
        _b1.info("🗑️ **Gerar Esqueleto Vazio**\nCria a tabela com todos os turnos a *A Preencher*. Para preencher à mão.")
        _b2.info("🤖 **Gerar Escala Automática**\nO robô distribui a equipa pelos turnos respeitando disponibilidade, contratos e regras trabalhistas.")
        _b3.info("🔄 **Resetar Aba**\nApaga o rascunho para começares de novo.")

        st.markdown("#### Ajuste manual")
        st.markdown("""
Depois de gerar, podes editar a tabela: clica na célula **Funcionário Atribuído** e altera o nome.
Turnos com **A Preencher** são os que o robô não conseguiu preencher — trata esses primeiro.
O painel **Horas Dinâmicas** à direita confirma o total semanal de cada pessoa.
        """)

        st.markdown("#### Exportar Escala")
        st.markdown("Clica no painel **⬇️ Exportar Escala** para descarregar em três formatos:")
        _x1, _x2, _x3 = st.columns(3)
        _x1.success("📄 **CSV** — para abrir em Excel ou Google Sheets.")
        _x2.success("📊 **Excel** — ficheiro .xlsx formatado.")
        _x3.success("🖨️ **PDF** — A4 horizontal, ideal para imprimir ou enviar.")

        st.markdown("#### Histórico de Escalas")
        st.markdown("""
1. Dá um nome à semana (ex: *Semana 47 — Nov 2026*) e clica **Guardar Escala Atual**.
2. Na coluna *Escalas Salvas*, usa 📂 para carregar ou 🗑️ para apagar uma semana anterior.
        """)

    # ── ABA 4 ──
    with st.expander("📊 Aba 4 — Análise", expanded=False):
        st.markdown("""
A aba de análise atualiza automaticamente sempre que a escala muda na Aba 3.

| Métrica | O que mostra |
|---|---|
| **Total de Turnos** | Todos os turnos da semana configurados |
| **Preenchidos** | Quantos têm uma pessoa atribuída |
| **Gaps** | Turnos ainda *A Preencher* — o objetivo é zero |
| **Cobertura %** | Percentagem de turnos preenchidos. Ideal: 100% |

O gráfico **Horas por Funcionário vs. Alvo** só aparece depois de configurares a semana na Aba 2.
        """)

    st.divider()

    # ── AVISOS E REGRAS ──
    st.subheader("⚠️ Avisos explicados")

    st.markdown("O app verifica automaticamente as regras trabalhistas depois de gerar a escala. Os avisos têm três níveis:")
    _av1, _av2, _av3 = st.columns(3)
    _av1.error("🔴 **Erros** — Situações sérias que deves resolver antes de aprovar a escala (turno sem keyholder, limite de horas ultrapassado).")
    _av2.warning("🟡 **Avisos** — Situações a rever mas que não bloqueiam (horas fora da margem, clopening).")
    _av3.info("🔵 **Infos** — Recomendações de boas práticas (pausas em turnos longos).")

    st.markdown("#### Avisos mais comuns")
    with st.expander("🔴 Turno não atribuído — nenhum keyholder elegível"):
        st.markdown("""
**O que significa:** Os turnos de fecho precisam de um **Manager**, **Assistant Manager** ou **Head Barista**.
Se nenhum destes estiver disponível nesse dia, o turno fica por preencher.

**Como resolver:** Verifica na Aba 1 se a pessoa com o cargo correto tem esse dia como *Livre* ou *Específico*.
Se não tiver, ajusta manualmente o turno na tabela.
        """)
    with st.expander("🔴 Clopening inválido"):
        st.markdown("""
**O que significa:** A pessoa fechou num dia (turno termina depois das 17h) e está escalada para abrir
no dia seguinte com menos de 11h de descanso entre turnos — proibido por lei trabalhista.

**Como resolver:** Troca o turno de abertura por outra pessoa com descanso suficiente.
        """)
    with st.expander("🔴 Fechamento sem keyholder"):
        st.markdown("""
**O que significa:** Há um turno de fecho que foi atribuído a alguém que não tem autorização
para fechar (cargo não é Manager nem Head Barista).

**Como resolver:** Atribui manualmente o turno a alguém com cargo adequado.
        """)
    with st.expander("🟡 Horas acima/abaixo da margem"):
        st.markdown("""
**O que significa:** O total de horas da pessoa saiu da zona de conforto
(*Alvo ± Margem* definida na Aba 2). Não viola o contrato, mas está fora do ideal.

**Como resolver:** Ajusta manualmente um turno, ou aumenta a margem na Aba 2 se for aceitável.
        """)
    with st.expander("🟡 7 dias consecutivos sem folga (WTI)"):
        st.markdown("""
**O que significa:** A pessoa foi escalada todos os 7 dias da semana sem nenhum dia de descanso —
viola o mínimo de 1 dia de descanso semanal por lei.

**Como resolver:** Marca pelo menos 1 dia como *Folga* na Aba 2 ou *Indisponível* na Aba 1.
        """)
    with st.expander("🔵 Turno >6h — pausa de 30 min obrigatória (WTI)"):
        st.markdown("""
**O que significa:** Turno com mais de 6 horas exige uma pausa de 30 minutos por lei.
O app avisa mas não pode forçar a pausa — tens de comunicar à pessoa.

**Sugestão:** Considera dividir o turno em dois ou garantir que a pausa está marcada no horário.
        """)
    with st.expander("🔵 Turno >4.5h — pausa de 15 min recomendada"):
        st.markdown("""
**O que significa:** Recomendação de boas práticas para turnos entre 4.5h e 6h.
Não é obrigatório por lei mas é boa prática para o bem-estar da equipa.
        """)

    st.divider()

    # ── FLUXO RECOMENDADO ──
    st.subheader("✅ Fluxo recomendado a cada semana")
    _f1, _f2, _f3, _f4 = st.columns(4)
    _f1.success("**1️⃣ Aba 1**\nAtualiza a equipa se alguém entrou, saiu ou mudou de cargo.")
    _f2.success("**2️⃣ Aba 2**\nConfigura folgas, férias e treinamentos desta semana. Guarda.")
    _f3.success("**3️⃣ Aba 3**\nGera a escala automática. Revê os avisos. Ajusta manualmente se necessário. Exporta.")
    _f4.success("**4️⃣ Aba 4**\nConfirma que a cobertura está a 100% e as horas estão equilibradas.")

    st.info("💡 **Limite de licença:** O plano atual suporta até **20 funcionários ativos** por café. Contacta o suporte se precisares de expandir.")
