import os
import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
from gtts import gTTS
import io

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
# Função de Pop-up Modal para Dicas de Estudo
# -----------------------------------------------------------------------------
@st.dialog("💡 Guia de Uso & Dicas Socráticas")
def abrir_modal_dicas():
    st.write("### Como aproveitar ao máximo seu tutor:")
    st.markdown("""
    - **Não peça respostas diretas:** O tutor foi projetado para te guiar a pensar sozinho!
    - **Envie fotos:** Caso tenha uma questão ou gráfico impresso, faça upload da imagem.
    - **Mude o tom:** Use os botões de atalho para pedir analogias ou simplificações.
    """)
    if st.button("Entendido! Let's study 🚀"):
        st.rerun()

# -----------------------------------------------------------------------------
# Barra Lateral (Menu do Usuário Dinâmico)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("🎓 SocratesAI")
    st.caption("Tutor Acadêmico Interativo")
    st.divider()

    materia = st.selectbox(
        "📚 Área de Estudo:",
        ["Geral", "Matemática / Física", "Programação & Computação", "Química / Biologia", "Humanas & Literatura"]
    )
    
    st.markdown("### 📎 Anexo para Análise")
    imagem_upload = st.file_uploader("Envie foto de um exercício/gráfico:", type=["jpg", "jpeg", "png"])
    
    if imagem_upload:
        st.image(imagem_upload, caption="Imagem Anexada", use_container_width=True)

    st.divider()

    if "total_perguntas" not in st.session_state:
        st.session_state.total_perguntas = 0

    col1, col2 = st.columns(2)
    col1.metric("Interações", st.session_state.total_perguntas)
    col2.metric("Status", "Ativo 🟢")

    st.divider()
    
    if st.button("💡 Dicas de Estudo", use_container_width=True):
        abrir_modal_dicas()

    if st.button("🗑️ Limpar Conversa", use_container_width=True):
        st.session_state.messages = []
        st.session_state.total_perguntas = 0
        st.rerun()

# -----------------------------------------------------------------------------
# Histórico da Conversa e Inicialização
# -----------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": f"Olá! Sou seu tutor acadêmico. Como posso ajudar você no estudo de **{materia}** hoje?"}
    ]

# 1. RENDERIZAR TODO O HISTÓRICO DE CHAT PRIMEIRO
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "audio" in msg:
            st.audio(msg["audio"], format="audio/mp3")

# 2. ATALHOS RÁPIDOS DE SUGESTÕES (Abaixo do histórico)
st.markdown("##### ⚡ Ações Rápidas:")
sugestao = st.pills(
    label="Sugestões de comandos",
    options=[
        "Me dê uma dica sem responder",
        "Explique como se eu tivesse 10 anos",
        "Crie um exemplo prático do cotidiano",
        "Entendi! Pode me passar um exercício parecido?"
    ],
    label_visibility="collapsed"
)

# 3. CAMPO DE ENTRADA DO USUÁRIO
prompt_input = st.chat_input("Digite sua dúvida ou cole um problema para estudarmos...")

# Definir qual entrada processar (Chat Input ou Botão de Sugestão)
prompt = prompt_input if prompt_input else sugestao

# -----------------------------------------------------------------------------
# Processamento da Pergunta e Geração da Resposta
# -----------------------------------------------------------------------------
if prompt:
    st.session_state.total_perguntas += 1
    
    if "entendi" in prompt.lower() or "consegui" in prompt.lower():
        st.balloons()

    # Adicionar e exibir a pergunta do usuário
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Preparar conteúdos para a API do Gemini
    conteudos = []
    if imagem_upload:
        img_pil = Image.open(imagem_upload)
        conteudos.append(img_pil)

    prompt_com_contexto = f"[Área: {materia}] {prompt}"
    conteudos.append(prompt_com_contexto)

    # Exibir a resposta do assistente IMEDIATAMENTE ABAIXO da pergunta do usuário
    with st.chat_message("assistant"):
        with st.status("🧠 SocratesAI está pensando...", expanded=True) as status:
            status.write("🔍 Lendo e interpretando o seu problema...")
            
            try:
                config = types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.3
                )
                
                resposta = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=conteudos,
                    config=config
                )
                
                texto_resposta = resposta.text
                status.write("💡 Formando orientação pedagógica socrática...")
                status.update(label="Resposta gerada com sucesso!", state="complete", expanded=False)
                
                # Renderiza a resposta em texto
                st.markdown(texto_resposta)

                # Gerar áudio
                try:
                    tts = gTTS(text=texto_resposta[:300], lang='pt', slow=False)
                    fp = io.BytesIO()
                    tts.write_to_fp(fp)
                    fp.seek(0)
                    audio_bytes = fp.read()
                    st.audio(audio_bytes, format="audio/mp3")
                    st.session_state.messages.append({"role": "assistant", "content": texto_resposta, "audio": audio_bytes})
                except Exception:
                    st.session_state.messages.append({"role": "assistant", "content": texto_resposta})

            except Exception as ex:
                status.update(label="Ocorreu um erro!", state="error")
                st.error(f"Erro na comunicação com a API: {ex}")