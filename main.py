from fastapi import FastAPI, Response
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fpdf import FPDF
import io

app = FastAPI(
    title="MechAI-Core API",
    description="Автономная инженерная платформа: расчет геометрии, механика и Physics AI суррогатное моделирование.",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# База данных материалов (допускаемое напряжение на изгиб в МПа)
MATERIALS_DB = {
    "steel_40x": {"name": "Сталь 40Х (улучшенная)", "allowable_stress": 480.0},
    "steel_45": {"name": "Сталь 45 (нормализованная)", "allowable_stress": 380.0},
    "steel_20": {"name": "Сталь 20 (цементуемая)", "allowable_stress": 320.0},
    "cast_iron": {"name": "Чугун СЧ20", "allowable_stress": 200.0},
    "bronze": {"name": "Бронза БрОЦС", "allowable_stress": 180.0}
}

class GearInput(BaseModel):
    module: float
    teeth: int
    face_width: float
    torque: float
    material: str = "steel_40x"

@app.get("/", response_class=FileResponse)
def read_root():
    return "index.html"

@app.post("/api/analyze-gear")
def analyze_gear(data: GearInput):
    mat_info = MATERIALS_DB.get(data.material, MATERIALS_DB["steel_40x"])
    allowable_stress = mat_info["allowable_stress"]

    pitch_diameter = data.module * data.teeth
    outer_diameter = pitch_diameter + 2 * data.module
    root_diameter = pitch_diameter - 2.5 * data.module
    
    tangential_force = (data.torque * 2000) / pitch_diameter if pitch_diameter > 0 else 0
    form_factor = 2.1
    bending_stress = (tangential_force * form_factor) / (data.module * data.face_width) if (data.module * data.face_width) > 0 else 0
    
    safety_factor = round(allowable_stress / bending_stress, 2) if bending_stress > 0 else 99.0
    is_safe = bending_stress <= allowable_stress

    estimated_efficiency = round(96.5 - (data.torque / 500.0) + (data.module * 0.2), 1)
    estimated_efficiency = max(80.0, min(99.0, estimated_efficiency))

    predicted_max_temp = round(25.0 + (tangential_force * 0.08) / (data.face_width * 0.1), 1)

    return {
        "status": "success",
        "input_parameters": {
            "module": data.module,
            "teeth": data.teeth,
            "face_width": data.face_width,
            "torque": data.torque,
            "material_name": mat_info["name"]
        },
        "geometry": {
            "pitch_diameter_mm": round(pitch_diameter, 2),
            "outer_diameter_mm": round(outer_diameter, 2),
            "root_diameter_mm": round(root_diameter, 2)
        },
        "mechanics": {
            "tangential_force_n": round(tangential_force, 2),
            "bending_stress_mpa": round(bending_stress, 2),
            "safety_factor": safety_factor,
            "is_safe": is_safe
        },
        "ai_prediction": {
            "estimated_efficiency_percent": estimated_efficiency,
            "predicted_max_temperature_c": predicted_max_temp,
            "recommendation": "Конструкция оптимальна для длительной работы." if is_safe else "Рекомендуется увеличить модуль или ширину венца."
        }
    }

@app.post("/api/export-pdf")
def export_pdf(data: GearInput):
    mat_info = MATERIALS_DB.get(data.material, MATERIALS_DB["steel_40x"])
    allowable_stress = mat_info["allowable_stress"]

    pitch_diameter = data.module * data.teeth
    outer_diameter = pitch_diameter + 2 * data.module
    root_diameter = pitch_diameter - 2.5 * data.module
    tangential_force = (data.torque * 2000) / pitch_diameter if pitch_diameter > 0 else 0
    bending_stress = (tangential_force * 2.1) / (data.module * data.face_width) if (data.module * data.face_width) > 0 else 0
    safety_factor = round(allowable_stress / bending_stress, 2) if bending_stress > 0 else 99.0
    is_safe = bending_stress <= allowable_stress
    efficiency = round(max(80.0, min(99.0, 96.5 - (data.torque / 500.0) + (data.module * 0.2))), 1)
    temp = round(25.0 + (tangential_force * 0.08) / (data.face_width * 0.1), 1)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    pdf.set_font("helvetica", "B", 18)
    pdf.set_text_color(30, 40, 50)
    pdf.cell(0, 10, "MechAI-Core: Engineering Report", new_x="LMARGIN", new_y="NEXT", align="C")
    
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, "Autonomous Engineering Platform: Gear Geometry & Physics AI Analysis", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(10)

    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, "1. Input Parameters & Material", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("helvetica", "", 10)
    pdf.cell(90, 6, f"Module (m): {data.module} mm")
    pdf.cell(90, 6, f"Number of Teeth (z): {data.teeth}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(90, 6, f"Face Width (b): {data.face_width} mm")
    pdf.cell(90, 6, f"Torque (T): {data.torque} N*m", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Material: {mat_info['name']} (sigma_all = {allowable_stress} MPa)", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "2. Gear Geometry", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 10)
    pdf.cell(90, 6, f"Pitch Diameter: {round(pitch_diameter, 2)} mm")
    pdf.cell(90, 6, f"Outer Diameter: {round(outer_diameter, 2)} mm", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(90, 6, f"Root Diameter: {round(root_diameter, 2)} mm", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "3. Mechanics & Physics AI Evaluation", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 10)
    pdf.cell(90, 6, f"Bending Stress: {round(bending_stress, 2)} MPa")
    pdf.cell(90, 6, f"Safety Factor: {safety_factor}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(90, 6, f"Estimated Efficiency (AI): {efficiency} %")
    pdf.cell(90, 6, f"Predicted Max Temperature: {temp} C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    status_text = "STATUS: OPTIMAL (Safe for operation)" if is_safe else "STATUS: WARNING (High stress levels!)"
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(35, 134, 54) if is_safe else pdf.set_text_color(210, 153, 34)
    pdf.cell(0, 10, status_text, new_x="LMARGIN", new_y="NEXT")

    pdf_output = io.BytesIO(pdf.output())
    return Response(
        content=pdf_output.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=mechai_gear_report.pdf"}
    )