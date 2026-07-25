
"""Bot conversacional de cultura general e historia mundial con Groq.

Ejecución local:
    pip install -r requirements.txt
    streamlit run main.py

La API key se escribe en la barra lateral. No se guarda en este archivo.
"""

from groq import Groq
import streamlit as st


# ---------------------------------------------------------------------------
# 1. Configuración general
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Oráculo Global",
    page_icon="🌍",
    layout="centered",
)

# El primer modelo es el solicitado. Se incluye una alternativa porque Groq
# anunció el retiro de Llama 3.3 70B para planes free/developer.
MODELOS = {
    "Llama 3.3 70B — solicitado": "llama-3.3-70b-versatile",
    "GPT-OSS 120B — alternativa futura": "openai/gpt-oss-120b",
}

PROMPT_SISTEMA = """
Eres Oráculo Global, un asistente educativo especializado en cultura general
e historia mundial.

Reglas de respuesta:
1. Responde en español, salvo que el usuario solicite otro idioma.
2. Explica con claridad y adapta el nivel de detalle a la pregunta.
3. En historia, incluye fechas, lugares, protagonistas y contexto cuando sean
   relevantes.
4. Distingue entre hechos ampliamente aceptados, interpretaciones históricas
   y asuntos controvertidos.
5. No inventes datos, citas ni fuentes. Si no estás seguro, dilo claramente.
6. No presentes correlaciones como relaciones causales sin evidencia.
7. Cuando ayude a comprender, usa una cronología breve o viñetas.
8. Termina las respuestas extensas con una síntesis de una o dos frases.
9. No tienes navegación web en esta aplicación. Si preguntan por sucesos muy
   recientes, advierte que la información puede necesitar verificación.
"""

PREGUNTAS_SUGERIDAS = [
    "¿Cuáles fueron las principales causas de la caída del Imperio romano de Occidente?",
    "Explícame la Revolución francesa mediante una cronología breve.",
    "¿Qué diferencias existían entre las civilizaciones maya, azteca e inca?",
    "¿Cómo cambió la Ruta de la Seda la historia mundial?",
]


# ---------------------------------------------------------------------------
# 2. Estado de la conversación
# ---------------------------------------------------------------------------
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

if "pregunta_sugerida" not in st.session_state:
    st.session_state.pregunta_sugerida = None


def seleccionar_pregunta(pregunta: str) -> None:
    """Guarda una pregunta de ejemplo para enviarla en el siguiente ciclo."""
    st.session_state.pregunta_sugerida = pregunta


def limpiar_conversacion() -> None:
    """Elimina únicamente el historial visible de la sesión actual."""
    st.session_state.mensajes = []
    st.session_state.pregunta_sugerida = None


# ---------------------------------------------------------------------------
# 3. Barra lateral
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Configuración")

    api_key = st.text_input(
        "Groq API key",
        type="password",
        placeholder="gsk_...",
        help="La clave permanece en la sesión del navegador y no se escribe en el código.",
    )

    nombre_modelo = st.selectbox("Modelo", options=list(MODELOS.keys()))
    modelo = MODELOS[nombre_modelo]

    temperatura = st.slider(
        "Creatividad",
        min_value=0.0,
        max_value=1.0,
        value=0.3,
        step=0.1,
        help="Valores bajos favorecen respuestas más consistentes y factuales.",
    )

    max_tokens = st.slider(
        "Extensión máxima",
        min_value=256,
        max_value=2048,
        value=1024,
        step=256,
        help="Cantidad máxima aproximada de tokens generados por respuesta.",
    )

    turnos_memoria = st.slider(
        "Turnos recordados",
        min_value=2,
        max_value=20,
        value=10,
        help="Limitar el historial ayuda a controlar el consumo de tokens.",
    )

    st.button(
        "Limpiar conversación",
        on_click=limpiar_conversacion,
        use_container_width=True,
    )

    if modelo == "llama-3.3-70b-versatile":
        st.warning(
            "Groq anunció el retiro de Llama 3.3 70B para planes free/developer "
            "el 16 de agosto de 2026. Si deja de responder, selecciona "
            "GPT-OSS 120B."
        )


# ---------------------------------------------------------------------------
# 4. Interfaz principal
# ---------------------------------------------------------------------------
st.title("🌍 Oráculo Global")
st.subheader("Cultura general e historia mundial")
st.write(
    "Pregunta por civilizaciones, personajes, procesos históricos, geografía, "
    "ciencia, arte o acontecimientos que hayan transformado el mundo."
)

st.info(
    "Este asistente puede equivocarse. Verifica fechas, cifras y afirmaciones "
    "importantes con fuentes académicas o institucionales."
)

if not st.session_state.mensajes:
    with st.chat_message("assistant"):
        st.markdown(
            "¡Hola! Puedo ayudarte a explorar la historia y la cultura general. "
            "Puedes escribir una pregunta o elegir uno de estos ejemplos:"
        )

    columnas = st.columns(2)
    for indice, pregunta_ejemplo in enumerate(PREGUNTAS_SUGERIDAS):
        columnas[indice % 2].button(
            pregunta_ejemplo,
            key=f"sugerencia_{indice}",
            on_click=seleccionar_pregunta,
            args=(pregunta_ejemplo,),
            use_container_width=True,
        )

# Mostramos el historial guardado en la sesión.
for mensaje in st.session_state.mensajes:
    with st.chat_message(mensaje["role"]):
        st.markdown(mensaje["content"])

pregunta_escrita = st.chat_input("Escribe tu pregunta...")
pregunta = st.session_state.pregunta_sugerida or pregunta_escrita
st.session_state.pregunta_sugerida = None


# ---------------------------------------------------------------------------
# 5. Consulta a Groq y respuesta transmitida en tiempo real
# ---------------------------------------------------------------------------
if pregunta:
    if not api_key.strip():
        st.warning("Escribe tu Groq API key en la barra lateral para comenzar.")
        st.stop()

    # Guardamos y mostramos el mensaje del usuario.
    st.session_state.mensajes.append(
        {"role": "user", "content": pregunta}
    )
    with st.chat_message("user"):
        st.markdown(pregunta)

    # Enviamos solo los turnos más recientes para controlar el contexto y costo.
    mensajes_recientes = st.session_state.mensajes[-(turnos_memoria * 2) :]
    mensajes_api = [
        {"role": "system", "content": PROMPT_SISTEMA},
        *mensajes_recientes,
    ]

    with st.chat_message("assistant"):
        contenedor_respuesta = st.empty()
        respuesta_completa = ""

        try:
            cliente = Groq(api_key=api_key.strip())
            flujo = cliente.chat.completions.create(
                model=modelo,
                messages=mensajes_api,
                temperature=temperatura,
                max_completion_tokens=max_tokens,
                top_p=1,
                stream=True,
            )

            # Cada fragmento recibido se agrega a la respuesta visible.
            for fragmento in flujo:
                texto = fragmento.choices[0].delta.content or ""
                respuesta_completa += texto
                contenedor_respuesta.markdown(respuesta_completa + " ▌")

            contenedor_respuesta.markdown(respuesta_completa)
            st.session_state.mensajes.append(
                {"role": "assistant", "content": respuesta_completa}
            )

        except Exception as error:
            # Quitamos el último mensaje para no dejar una conversación incompleta.
            st.session_state.mensajes.pop()
            contenedor_respuesta.empty()
            st.error(
                "No fue posible obtener una respuesta de Groq. "
                f"Tipo de error: {type(error).__name__}. "
                "Revisa la API key, el modelo seleccionado y los límites de tu cuenta."
            )

