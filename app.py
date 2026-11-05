"""Streamlit UI for Gerador de Escalas — imports all logic from database.py and logic.py."""
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
)
from logic import calcular_horas_turno, gerar_escala_automatica

# ==========================================
# UI HELPERS
# ==========================================

def render_availability_selector(prefix, defaults=None):
    """Render a 7-day availability selector and return the list of chosen values."""
    if defaults is None:
        defaults = ["Livre"] * 7

    dias = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    opcoes = ["Livre", "Só Manhã", "Só Tarde", "Indisponível", "Folga", "Férias", "Específico"]
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
    st.title("☕ Gerenciador de Escalas - Cafe")
    st.subheader("Acesso à Plataforma")

    tab_login, tab_register = st.tabs(["🔑 Login", "📝 Cadastrar Novo Cafe"])

    with tab_login:
        with st.form("form_login"):
            email_login = st.text_input("Email")
            senha_login = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                user = verify_credentials(email_login, senha_login)
                if user:
                    st.session_state['user'] = user
                    st.session_state['tenant_id'] = user['tenant_id']
                    st.rerun()
                else:
                    st.error("Email ou senha incorretos.")

    with tab_register:
        with st.form("form_register"):
            nome_cafe_reg = st.text_input("Nome do Cafe")
            email_reg = st.text_input("Email do Admin")
            senha_reg = st.text_input("Senha", type="password")
            senha_conf = st.text_input("Confirmar Senha", type="password")
            if st.form_submit_button("Cadastrar Cafe"):
                if senha_reg != senha_conf:
                    st.error("As senhas não coincidem.")
                elif not nome_cafe_reg or not email_reg or not senha_reg:
                    st.error("Preencha todos os campos.")
                else:
                    try:
                        new_tid = criar_cafe(nome_cafe_reg, email_reg)
                        create_user(new_tid, email_reg, senha_reg, role="admin")
                        st.success("Cafe cadastrado! Faça login para continuar.")
                    except Exception as e:
                        st.error(f"Erro ao cadastrar: {e}")

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

aba1, aba2, aba3 = st.tabs(["👥 Gestão do Time", "⚙️ Setup da Semana", "📅 Rascunho e Aprovação"])

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
            adicionar_funcionario(TENANT_ID, nome_novo, cargo_novo, contrato_novo, h_min_nova, h_max_nova, dias_selecionados)
            st.success(f"{nome_novo} adicionado!")
            st.session_state['novo_k'] += 1
            st.rerun()

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
            with st.form("form_setup_semana"):
                st.write("Defina quem entra na escala esta semana e ajuste as metas de horas.")

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

                    if vai_trabalhar:
                        total_horas_planejadas += horas_alvo

                    disp_dict = {d[0]: d[1] for d in dias_map}
                    inputs_semana[row['nome']] = {
                        "vai_trabalhar": vai_trabalhar,
                        "horas_alvo": horas_alvo,
                        "cargo": row['cargo'],
                        "disponibilidade": disp_dict,
                    }
                    st.divider()

                if st.form_submit_button("Confirmar Horas da Semana"):
                    st.session_state['config_semana'] = inputs_semana
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
            df_escala, constraints_warnings = gerar_escala_automatica(config_semana, turnos_padrao)
            st.session_state['roster_df'] = df_escala
            st.session_state['constraints_warnings'] = constraints_warnings
            st.rerun()

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
            horas_atuais = {nome: 0.0 for nome in config_sem.keys() if config_sem[nome]['vai_trabalhar']}

            for idx, row in roster_editado.iterrows():
                func = row['Funcionário']
                if func in horas_atuais:
                    horas_atuais[func] += calcular_horas_turno(str(row['Horário']))

            for func, horas in horas_atuais.items():
                alvo = config_sem[func]['horas_alvo']
                if horas > alvo:
                    st.error(f"🔴 {func}: {horas}h (Alvo: {alvo}h)")
                elif horas < alvo - 2:
                    st.info(f"🔵 {func}: {horas}h (Alvo: {alvo}h)")
                else:
                    st.success(f"🟢 {func}: {horas}h (Alvo: {alvo}h)")

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
            with st.expander("⚠️ Avisos de Regras Trabalhistas", expanded=True):
                for w in constraints_warnings:
                    if "clopening" in w or "limite semanal" in w or "keyholder" in w:
                        st.error(w)
                    else:
                        st.warning(w)
