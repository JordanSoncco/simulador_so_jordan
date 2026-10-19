# 🖥️ Simulador de Sistemas Operativos: Planificación y Concurrencia

> **Autor:** Jordan Oliber Soncco Machaca  
> **Curso:** Sistemas Operativos — Grupo A  
> **Docente:** Ing. Donia Alizandra Ruelas Acero  
> **Institución:** Universidad Nacional del Altiplano (UNA Puno)  
> **Escuela:** Ingeniería de Sistemas — Semestre V  

---

## 📖 Descripción General

Este proyecto es una aplicación interactiva de escritorio desarrollada en **Python** con **CustomTkinter** y **Matplotlib**, diseñada con una arquitectura modular y una interfaz moderna tipo Bento UI dividida en 3 zonas visuales bien diferenciadas:

1. **📥 Zona 1: Entrada de Datos y Configuración** (Carga de procesos manual o vía `.txt`, configuración de políticas y quantum).
2. **🎯 Zona 2: Espacio de Simulación** (Lienzo interactivo del Plano de Gantt 2D, Cola de Procesos por Unidad de Tiempo y animaciones vectoriales de concurrencia).
3. **📊 Zona 3: Información, Resultados y Análisis** (Métricas finales, fórmulas paso a paso en KaTeX/LaTeX, monitores de semáforos en tiempo real y bitácora/traza de eventos).

---

## 🧩 Módulos del Sistema

### 📊 Módulo 1: Políticas de Planificación de la CPU
Simulación determinista y visualización paso a paso de los 4 algoritmos clásicos de planificación de procesos:

- **FCFS** (*First-Come, First-Served* - No Expulsivo).
- **SJF** (*Shortest Job First* - No Expulsivo).
- **SRTF** (*Shortest Remaining Time First* - Expulsivo).
- **Round Robin** (*Turno Rotatorio con Quantum configurable* - Expulsivo).

#### Características destacadas:
- **Plano de Gantt Cartesiano 2D**: Visualización nítida con bloques coloreados por proceso y marca roja `+` en el tiempo de finalización ($T.F.$).
- **Herramientas de Navegación**: Zoom interactivo (Lupa rectangular, botones Zoom +/-), Desplazamiento (Modo Mover con la mano, arrastre con Clic Derecho/Central) y **barras de desplazamiento vertical y horizontal (Scrollbars)**.
- **Cola de Procesos por Unidad de Tiempo**: Eje temporal sincronizado que desglosa en cada instante $t$ qué proceso ocupa la CPU y cuáles esperan en la cola de listos.
- **Cuadro de Métricas**: Tiempos de Llegada ($T.LL$), Servicio ($T.S.$), Finalización ($T.F.$), Retorno ($T.R.$) y Espera ($T.E.$).
- **Fórmulas Matemáticas Paso a Paso**: Desglose explícito de sumatorias y cálculo de promedios ($T\bar{R}$ y $T\bar{E}$).
- **Comparativa Multialgorítmica**: Ventana emergente que ejecuta simultáneamente las 4 políticas sobre la misma carga de trabajo y premia a la más eficiente.
- **Importación / Exportación**: Carga de cargas de trabajo desde archivos `.txt` y exportación del plano en alta resolución (`.png`).

---

### 🔄 Módulo 2: Problemas Clásicos de Concurrencia y Sincronización
Modelado multihilo (`threading`, `Event`, `Semaphore`, `Lock`) de los 5 problemas fundamentales de sincronización entre procesos, con personajes vectoriales animados:

1. **🏭 Problema del Productor - Consumidor (Búfer Acotado Circular)**:
   - Capacidad $N = 8$, sincronizado con `mutex`, `empty` y `full`.
   - Personajes: Obreros productores y consumidores vestidos con overoles, cascos y animación de depósito/retiro de cajas numeradas.
2. **📚 Problema de Lectores - Escritores (Exclusión Mutua de Base de Datos)**:
   - Lecturas simultáneas concurrentes y acceso en exclusión mutua estricta para escritores mediante `wrt` y `mutex_lectores`.
   - Personajes: Lectores sentados consultando libros y escritores de pie con pluma y pergamino.
3. **🍝 Problema de los Filósofos Comensales (Prevención de Interbloqueo)**:
   - 5 filósofos alternando entre pensar y comer espagueti con 5 tenedores compartidos.
   - Algoritmo con semáforo contador `camarero` (límite de 4 filósofos simultáneos) que evita completamente el *Deadlock* y la inanición.
   - Personajes: Filósofos con túnicas, barbas, platos de fideos y globos de pensamiento filosófico ($\pi$, $\infty$, $\text{Logos}$, $\text{Ética}$).
4. **💈 Problema del Barbero Dormilón**:
   - 1 barbero, 1 silla de corte y 5 sillas en la sala de espera sincronizados con `clientes` y `mutex`.
   - Animación de sueño ($Zzz$), tijeras en movimiento al cortar cabello y clientes que entran o se retiran si la sala está llena.
5. **🚬 Problema de los Fumadores de Cigarrillos**:
   - 1 agente mediador y 3 fumadores con ingredientes fijos (Tabaco, Papel, Fósforos).
   - Animación de ingredientes sobre la mesa, personajes armando y bocanadas de humo ondulante al fumar.

---

## 📁 Estructura del Código

```text
simulador_so_jordan/
├── main.py                     # Punto de entrada principal
├── requirements.txt            # Dependencias del proyecto
├── README.md                   # Documentación oficial
├── .gitignore                  # Exclusiones de control de versiones
├── procesos_ejemplo.txt        # Dataset de prueba (4 procesos)
├── procesos_ejemplo_15.txt     # Dataset de prueba mediano (15 procesos)
├── procesos_ejemplo_25.txt     # Dataset de prueba grande (25 procesos)
├── planificacion/              # MÓDULO 1: Planificación de Procesos
│   ├── __init__.py
│   ├── algoritmos.py           # Motores de FCFS, SJF, SRTF y Round Robin
│   ├── graficador_gantt.py     # Renderizado Matplotlib (Gantt, Cola, Fórmulas)
│   └── vista_planificacion.py  # Vista gráfica e interacción de usuario
└── concurrencia/               # MÓDULO 2: Concurrencia y Sincronización
    ├── __init__.py
    ├── base_simulacion.py      # Estructura común, hilos y controles
    ├── panel_concurrencia.py   # Selector de problemas clásicos
    ├── graficos_personajes.py  # Renderizado de personajes vectoriales
    ├── productor_consumidor.py # 1. Búfer acotado
    ├── lectores_escritores.py  # 2. Lectores y Escritores
    ├── filosofos_comensales.py # 3. Filósofos comensales
    ├── barbero_dormilon.py     # 4. Barbero dormilón
    └── fumadores.py            # 5. Fumadores
```

---

## 🚀 Requisitos e Instalación

### Prerrequisitos
- **Python 3.10** o superior instalado en el sistema.
- Gestor de paquetes `pip`.

### 1. Clonar el repositorio
```bash
git clone https://github.com/JordanSoncco/simulador_so_jordan.git
cd simulador_so_jordan
```

### 2. (Opcional) Crear un entorno virtual
```bash
python -m venv venv
# En Windows:
.\venv\Scripts\activate
# En Linux/macOS:
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Ejecutar el simulador
```bash
python main.py
```

---

## 📄 Licencia y Derechos de Autor
Desarrollado con fines académicos por **Jordan Oliber Soncco Machaca** para el curso de **Sistemas Operativos** en la **Universidad Nacional del Altiplano (UNA Puno)**.
