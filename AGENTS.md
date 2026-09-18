# Reglas y Comandos de Hermes OS

## Comando especial "Bye"

Cuando el usuario envíe el mensaje **"Bye"** (o "bye"):
1. **Guardar todo y hacer commit**:
   - Asegurar que todo el código modificado esté sincronizado y comprobado.
   - Ejecutar `git add .` y crear un commit descriptivo de los avances logrados en la sesión.
2. **Actualizar el historial**:
   - Documentar en `docs/CONTEXTO.md` el resumen de lo construido y el siguiente paso acordado.
3. **Cerrar la aplicación**:
   - Detener los contenedores Docker en ejecución (`docker compose stop`).
4. **Apagar el PC**:
   - Ejecutar el comando para apagar el sistema (`shutdown /s /t 15`).
