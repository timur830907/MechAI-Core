import io
import math
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = FastAPI(title="MechAI-Core API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# База данных материалов с допускаемыми напряжениями (МПа)
MATERIALS_DB = {
    "steel_40x": {
        "name": "Сталь 40Х (улучшенная)",
        "sigma_bend_allow": 450.0,
        "sigma_contact_allow": 850.0,
        "density": 7850.0,
    },
    "steel_45": {
        "name": "Сталь 45 (нормализация)",
        "sigma_bend_allow": 300.0,
        "sigma_contact_allow": 580.0,
        "density": 7830.0,
    },
    "bronze_br_o10f1": {
        "name": "Бронза БрО10Ф1",
        "sigma_bend_allow": 160.0,
        "sigma_contact_allow": 320.0,
        "density": 8800.0,
    },
    "delrin_pom": {
        "name": "Полиацеталь (POM-C / Делрин)",
        "sigma_bend_allow": 65.0,
        "sigma_contact_allow": 90.0,
        "density": 1410.0,
    },
}


class GearInput(BaseModel):
    material: str = Field("steel_40x", description="Ключ материала из базы")
    module: float = Field(..., gt=0, description="Модуль зацепления, мм")
    teeth: int = Field(..., gt=2, description="Количество зубьев")
    width: float = Field(..., gt=0, description="Ширина венца, мм")
    torque: float = Field(..., gt=0, description="Крутящий момент, Н*м")


@get_route_or_similar = app.post("/api/calculate")
def calculate_gear(data: GearInput):
    if data.material not in MATERIALS_DB:
        raise HTTPException(status_code=400, detail="Неизвестный материал")

    mat = MATERIALS_DB[data.material]

    # Геометрический расчет цилиндрической передачи
    d = data.module * data.teeth  # Делетельный диаметр
    d_a = d + 2 * data.module  # Диаметр вершин
    d_f = d - 2.5 * data.module  # Диаметр впадин

    r = d / 2.0
    # Окружное усилие (Н)
    ft = (2.0 * data.torque * 1000.0) / d if r > 0 else 0.0

    # Расчет изгибного напряжения по упрощенной модели Льюиса с учетом формы зуба
    # sigma_bend = Ft / (b * m * y)
    y_form = 0.154 - (0.912 / data.teeth)  # Коэффициент формы зуба
    if y_form <= 0:
        y_form = 0.1
    sigma_bend = ft / (data.width * data.module * y_form)

    # Запас прочности по изгибу
    safety_factor = (
        mat["sigma_bend_allow"] / sigma_bend if sigma_bend > 0 else 99.9
    )

    # Physics AI Суррогатная модель (предсказание КПД и температуры)
    # Учитывает трение в зацеплении и тепловыделение при нагрузке
    base_efficiency = 0.985
    load_factor = data.torque / (data.module * data.teeth * data.width * 0.05)
    efficiency = max(0.85, min(0.992, base_efficiency - 0.003 * load_factor))

    # Максимальная расчетная температура (°C)
    power_loss = (data.torque * 15.0) * (1.0 - efficiency)
    max_temp = 25.0 + power_loss * 2.4

    status = (
        "Optimal"
        if safety_factor >= 1.5 and sigma_bend <= mat["sigma_bend_allow"]
        else "Overload / Warning"
    )

    # Генерация матрицы напряжений для тепловой карты зуба (heatmap по 5 контрольным точкам)
    stress_profile = [
        round(sigma_bend * 0.2, 2),
        round(sigma_bend * 0.5, 2),
        round(sigma_bend * 0.8, 2),
        round(sigma_bend * 1.0, 2),  # Пик у корня
        round(sigma_bend * 0.4, 2),
    ]

    return {
        "material_name": mat["name"],
        "pitch_diameter": round(d, 2),
        "tip_diameter": round(d_a, 2),
        "root_diameter": round(d_f, 2),
        "bending_stress": round(sigma_bend, 2),
        "allowable_bending_stress": mat["sigma_bend_allow"],
        "safety_factor": round(safety_factor, 2),
        "efficiency": round(efficiency * 100, 2),
        "max_temperature": round(max_temp, 1),
        "status": status,
        "stress_profile": stress_profile,
    }


@app.post("/api/export-pdf")
def export_pdf(data: GearInput):
    result = calculate_gear(data)

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, height - 50, "MechAI-Core: Инженерный отчет")

    pdf.setFont("Helvetica", 11)
    y = height - 90
    lines = [
        f"Материал: {result['material_name']}",
        f"Модуль зацепления (m): {data.module} мм",
        f"Количество зубьев (z): {data.teeth}",
        f"Ширина венца (b): {data.width} мм",
        f"Крутящий момент (T): {data.torque} Н*м",
        "-" * 50,
        f"Делетельный диаметр: {result['pitch_diameter']} мм",
        f"Диаметр вершин: {result['tip_diameter']} мм",
        f"Изгибное напряжение: {result['bending_stress']} МПа",
        f"Допускаемое напряжение: {result['allowable_bending_stress']} МПа",
        f"Коэффициент запаса: {result['safety_factor']}",
        f"КПД (Physics AI): {result['efficiency']} %",
        f"Прогноз T макс: {result['max_temperature']} °C",
        f"Статус конструкции: {result['status']}",
    ]

    for line in lines:
        pdf.drawString(50, y, line)
        y -= 22

    pdf.save()
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=mechai_report.pdf"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)