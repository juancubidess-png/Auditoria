# Auditor de documentación legal — guía de ejecución

## Preparar (una sola vez)
    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements-dev.txt

## Ejecutar la aplicación (capa de presentación completa)
    export AIVEN_DB_PASSWORD='...'          # NO la muestre en capturas: ejecute `clear` antes
    # opcional: export RUTA_ACTAS='...' RUTA_ACUERDOS='...'
    clear
    python -m auditor                        # EVIDENCIA: ejecución del sistema final

## Pruebas, cobertura y rendimiento
    pytest -v                                # EVIDENCIA: pruebas unitarias
    coverage run -m pytest                   # usa .coveragerc
    coverage report -m                       # EVIDENCIA: cobertura en consola
    coverage html && xdg-open htmlcov/index.html   # EVIDENCIA: cobertura HTML
    python -m bench.benchmark                # EVIDENCIA: rendimiento y estrés

## SonarQube (con cobertura incluida)
    coverage xml
    docker start sonarqube        # espere 2-3 min
    docker run --rm --network host -v "$(pwd):/usr/src" sonarsource/sonar-scanner-cli \
      -Dsonar.token=SU_TOKEN -Dsonar.host.url=http://localhost:9000
    # (los demás parámetros se leen de sonar-project.properties)
