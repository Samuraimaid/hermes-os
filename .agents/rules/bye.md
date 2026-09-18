# Regla de Cierre de Sesión: Comando "Bye"

Cuando el usuario escriba **"Bye"** (o "bye") al finalizar una jornada o sesión de trabajo:

1. **Guardar y commitear**:
   - Asegurar que todo el código modificado esté sincronizado y funcional.
   - Ejecutar `git add .` y crear un commit descriptivo de los avances logrados en la sesión.
2. **Actualizar el historial**:
   - Documentar en `docs/CONTEXTO.md` el resumen de lo construido y el siguiente paso acordado.
3. **Cerrar la aplicación**:
   - Detener los contenedores Docker en ejecución (`docker compose stop`).
4. **Apagar el PC**:
   - Ejecutar el comando del sistema operativo para apagar la máquina (`shutdown /s /t 15`).
