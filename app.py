import os
import streamlit as st
from google import genai
from google.genai import types
from PIL import Image

# -----------------------------------------------------------------------------
# Configuração Visual da Página Web
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SocratesAI - Tutor Acadêmico",
    page_icon="🎓",
    layout="wide"
)

# -----------------------------------------------------------------------------
# Prompt Pedagógico do Sistema (System Instruction)
# -----------------------------------------------------------------------------
SYSTEM_INSTRUCTION = """
Você é o "SocratesAI", um tutor acadêmico paciente, encorajador e especialista.
Seu objetivo é ajudar estudantes a entenderem conceitos e resolverem problemas.

DIRETRIZES OBRIGATÓRIAS:
1. NUNCA dê a resposta final nem resolva os exercícios diretamente.
2. Use o Método Socrático: faça perguntas direcionadas para induzir o raciocínio do aluno passo a passo.
3. Se o aluno errar, aponte em qual etapa o raciocínio dele falhou sem julgamentos e peça para ele revisar esse passo.
4. Explique usando analogias do cotidiano, Markdown e formatação LaTeX para fórmulas matemáticas quando relevante.
5. Finalize suas explicações com uma pergunta simples de verificação do aprendizado.
"""

# -----------------------------------------------------------------------------
# Configuração da Chave de API do Gemini
# -----------------------------------------------------------------------------
api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

if not api_key:
    st.error("🔑 Chave de API não encontrada! Adicione sua GEMINI_API_KEY nos Secrets do Streamlit Community Cloud.")
    st.stop()

@st.cache_resource
def get_gemini_client(key: str):
    return genai.Client(api_key=key)

client = get_gemini_client(api_key)

# -----------------------------------------------------------------------------
# Barra Lateral (Menu do Usuário)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("🎓 SocratesAI")
    st.caption("Tutor Acadêmico com Inteligência Artificial")
    st.divider()

    materia = st.selectbox(
        "Área de Estudo:",
        ["Geral", "Matemática / Física", "Programação & Computação", "Química / Biologia", "Humanas & Literatura"]
    )
    
    st.markdown("### 📎 Anexo para Análise")
    imagem_upload = st.file_uploader("Envie uma foto do exercício ou gráfico:", type=["jpg", "jpeg", "png"])
    
    st.divider()
    if st.button("🗑️ Limpar Conversa", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# -----------------------------------------------------------------------------
# Histórico da Conversa
# -----------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": f"Olá! Sou seu tutor acadêmico. Como posso ajudar você no estudo de **{materia}** hoje?"}
    ]

# Renderizar mensagens anteriores
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -----------------------------------------------------------------------------
# Processamento de Entrada do Usuário e Resposta do Gemini
# -----------------------------------------------------------------------------
if prompt := st.chat_input("Digite sua dúvida ou cole um problema para estudarmos..."):
    
    # Exibir mensagem do usuário
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Preparar dados para o Gemini
    conteudos = []
    
    if imagem_upload:
        img_pil = Image.open(imagem_upload)
        conteudos.append(img_pil)

    prompt_com_contexto = f"[Área: {materia}] {prompt}"
    conteudos.append(prompt_com_contexto)

    # Gerar resposta via Gemini
    with st.chat_message("assistant"):
        with st.spinner("Analisando e preparando a orientação pedagógica..."):
            try:
                config = types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.3
                )
                
                # Chamada com o modelo padrão estável
                resposta = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=conteudos,
                    config=config
                )
                
                texto_resposta = resposta.text
                st.markdown(texto_resposta)
                st.session_state.messages.append({"role": "assistant", "content": texto_resposta})
            except Exception as ex:
                st.error(f"Erro na comunicação com a API: {ex}")