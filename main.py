from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np

app = FastAPI(title="AI Engineering & Geometry API", version="1.0")

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

# --- 1. ФУНКЦИЯ РАСЧЕТА ГЕОМЕТРИИ ШЕСТЕРНИ ---
def calculate_gear_geometry(module: float, teeth: int, face_width: float) -> dict:
    """Вычисляет основные геометрические параметры цилиндрической шестерни."""
    pitch_diameter = module * teeth
    outer_diameter = pitch_diameter + 2 * module
    root_diameter = pitch_diameter - 2.5 * module
    volume = np.pi * (outer_diameter / 2)**2 * face_width # мм^3
    
    return {
        "pitch_diameter_mm": round(pitch_diameter, 2),
        "outer_diameter_mm": round(outer_diameter, 2),
        "root_diameter_mm": round(root_diameter, 2),
        "approx_volume_mm3": round(volume, 2)
    }

# --- 2. ФУНКЦИЯ ИБП/МЕХАНИЧЕСКОГО РАСЧЕТА (FEA суррогат) ---
def calculate_mechanical_stress(module: float, teeth: int, torque: float) -> dict:
    """Оценивает максимальное контактное напряжение и напряжение изгиба."""
    pitch_radius = (module * teeth) / 2 / 1000  # переводим в метры
    force_tangent = torque / pitch_radius if pitch_radius > 0 else 0
    
    # Упрощенная инженерная оценка напряжений (МПа)
    bending_stress = force_tangent / (module * 10) * 1.5 
    contact_stress = np.sqrt(force_tangent * 1e6) * 0.8
    
    safety_factor = 350 / max(bending_stress, 1) # Условный предел текучести стали 350 МПа
    
    return {
        "bending_stress_mpa": round(bending_stress, 2),
        "contact_stress_mpa": round(contact_stress, 2),
        "safety_factor": round(safety_factor, 2),
        "is_safe": safety_factor > 1.5
    }

# --- 3. ФУНКЦИЯ ИИ-ПРЕДСКАЗАНИЯ ФИЗИКИ (Physics AI Mock) ---
def evaluate_physics_ai(geometry_data: dict, stress_data: dict) -> dict:
    """Имитирует работу быстрой суррогатной ИИ-модели для оценки тепловыделения и КПД."""
    # Нейросеть мгновенно оценивает параметры на основе «обученной» базы
    efficiency = 97.5 - (stress_data["bending_stress_mpa"] * 0.01)
    max_temperature = 25.0 + (stress_data["contact_stress_mpa"] * 0.15)
    
    return {
        "ai_model_version": "PhysicsAI-v1.2-surrogate",
        "estimated_efficiency_percent": round(max(min(efficiency, 99.9), 80.0), 2),
        "predicted_max_temperature_c": round(max_temperature, 1),
        "status": "Optimal" if stress_data["is_safe"] else "Warning: Overload"
    }

# --- API ЭНДПОИНТЫ ---
@app.post("/api/analyze-gear")
def analyze_gear_endpoint(data: GearRequest):
    """Главный эндпоинт, объединяющий все функции расчета узла."""
    geometry = calculate_gear_geometry(data.module, data.teeth, data.face_width)
    stress = calculate_mechanical_stress(data.module, data.teeth, data.torque)
    ai_physics = evaluate_physics_ai(geometry, stress)
    
    return {
        "geometry": geometry,
        "mechanics": stress,
        "ai_prediction": ai_physics
    }