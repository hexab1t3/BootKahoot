# BootKahoot
Es una app para contestar automaticamente un kahoot a travez de gemini, Se necesita una apikey de gemini la cual se obtiene en google ai studio.
Despues de ingresar la apikey puedes buscar una lista de los modelos de gemini que puedes usar, selecciona uno y dale conectar, 
despues tendras que mapear la pantalla donde muestran preguntas y opciones, y mapearas despues los botones de tu kahoot(donde te deja responder)
te dira la interfaz el orden. Despues de eso solo debes esperar a que aparesca la pregunta y opciones y presionar la tecla " K " y el boot se encargara 
de enviar la imagen a gemini y dar click automaticamente a la respuesta. 
En promedio gemini flash 2.5 tarda de 3-4 seg en responder y 10 milisegundos en dar click o menos; si lo que buscas es rapidez


## Instalación (Windows)
1. Descarga `KahootBot-Instalador.zip` y extráelo.
2. Doble clic en `Instalar.bat` (instala Python si hace falta, las librerías y crea un acceso directo "Kahoot Bot" en el Escritorio).
3. Abre "Kahoot Bot" desde el Escritorio (pide permisos de administrador para detectar la tecla K).

## Novedades (modo rápido)
- Usa el SDK nuevo `google-genai` con "thinking" desactivado y la captura reducida: Gemini Flash responde bastante más rápido.
- Sin pausas artificiales en el click.
- **Modo AUTO** (casilla o tecla `F8`): detecta cuando aparece una pregunta nueva y responde sola, sin pulsar `K`. Si no hay pregunta en pantalla, no hace nada.
- Manual sigue funcionando con la tecla `K`.
- Si ya tenías instalado, vuelve a ejecutar `Instalar.bat` para actualizar las librerías.
