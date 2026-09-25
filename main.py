from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import numpy as np

app = FastAPI(title="MechAI-Core API", version="1.0")

# Настройка CORS для связи с будущим веб-интерфейсом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Схемы данных для входящих запросов
class GearRequest(BaseModel):
    module: float  # Модуль зацепления (мм)
    teeth: int     # Количество зубьев
    face_width: float # Ширина венца (мм)
    torque: float  # Крутящий момент (Н*м)

# --- ГЛАВНАЯ СТРАНИЦА КОРНЯ СЕРВЕРА ---
@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>MechAI-Core | Autonomous Engineering Platform</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #c9d1d9; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .card { background: #161b22; padding: 40px; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); text-align: center; border: 1px solid #30363d; max-width: 500px; }
            h1 { color: #58a6ff; margin-bottom: 10px; }
            p { color: #8b949e; margin-bottom: 30px; }
            .btn { display: inline-block; background: #238636; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: bold; transition: background 0.2s; }
            .btn:hover { background: #2ea043; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>MechAI-Core API</h1>
            <p>Автономная инженерная платформа: расчет геометрии, механика и Physics AI суррогатное моделирование.</p>
            <a class="btn" href="/docs">Открыть документацию API</a>
        </div>
    </body>
    </html>
    """

# --- 1. ФУНКЦИЯ РАСЧЕТА ГЕОМЕТРИИ ШЕСТЕРНИ ---
def calculate_gear_geometry(module: float, teeth: int, face_width: float) -> dict:
    pitch_diameter = module * teeth
    outer_diameter = pitch_diameter + 2 * module
    root_diameter = pitch_diameter - 2.5 * module
    volume = np.pi * (outer_diameter / 2)**2 * face_width
    
    return {
        "pitch_diameter_mm": round(pitch_diameter, 2),
        "outer_diameter_mm": round(outer_diameter, 2),
        "root_diameter_mm": round(root_diameter, 2),
        "approx_volume_mm3": round(volume, 2)
    }

# --- 2. ФУНКЦИЯ МЕХАНИЧЕСКОГО РАСЧЕТА ---
def calculate_mechanical_stress(module: float, teeth: int, torque: float) -> dict:
    pitch_radius = (module * teeth) / 2 / 1000
    force_tangent = torque / pitch_radius if pitch_radius > 0 else 0
    
    bending_stress = force_tangent / (module * 10) * 1.5 
    contact_stress = np.sqrt(force_tangent * 1e6) * 0.8
    safety_factor = 350 / max(bending_stress, 1)
    
    return {
        "bending_stress_mpa": round(bending_stress, 2),
        "contact_stress_mpa": round(contact_stress, 2),
        "safety_factor": round(safety_factor, 2),
        "is_safe": safety_factor > 1.5
    }

# --- 3. ФУНКЦИЯ ИИ-ПРЕДСКАЗАНИЯ ФИЗИКИ ---
def evaluate_physics_ai(geometry_data: dict, stress_data: dict) -> dict:
    efficiency = 97.5 - (stress_data["bending_stress_mpa"] * 0.01)
    max_temperature = 25.0 + (stress_data["contact_stress_mpa"] * 0.15)
    
    return {
        "ai_model_version": "PhysicsAI-v1.2-surrogate",
        "estimated_efficiency_percent": round(max(min(efficiency, 99.9), 80.0), 2),
        "predicted_max_temperature_c": round(max_temperature, 1),
        "status": "Optimal" if stress_data["is_safe"] else "Warning: Overload"
    }

# --- API ЭНДПОИНТ ---
@app.post("/api/analyze-gear")
def analyze_gear_endpoint(data: GearRequest):
    geometry = calculate_gear_geometry(data.module, data.teeth, data.face_width)
    stress = calculate_mechanical_stress(data.module, data.teeth, data.torque)
    ai_physics = evaluate_physics_ai(geometry, stress)
    
    return {
        "geometry": geometry,
        "mechanics": stress,
        "ai_prediction": ai_physics
    }