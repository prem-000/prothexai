import os
from io import BytesIO
from datetime import datetime

# Safe Absolute Path Resolution
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOGO_PATH = os.path.join(BASE_DIR, "logo", "logo.png")

def generate_medical_pdf(data: dict):
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.units import inch

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor("#2C3E50"),
        alignment=2, # Right Align for corporate look
        spaceAfter=0
    )
    
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor("#2980B9"),
        spaceBefore=12,
        spaceAfter=6
    )
    
    body_style = styles['Normal']
    
    disclaimer_style = ParagraphStyle(
        'DisclaimerStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        italic=True,
        alignment=1
    )
    
    elements = []
    
    # 1. Logo
    if os.path.exists(LOGO_PATH):
        try:
            # Maintain aspect ratio with fixed width
            logo = Image(LOGO_PATH, width=1.5*inch, height=1.5*inch, kind='proportional')
            logo.hAlign = 'LEFT'
            elements.append(logo)
            elements.append(Spacer(1, 0.2*inch))
        except Exception:
            pass

    # 2. Report Title
    title_paragraph = Paragraph(
        "<b>Prosthetic Biomechanical Analysis Report</b>",
        title_style
    )
    elements.append(title_paragraph)
    elements.append(Spacer(1, 0.1 * inch))

    # 2. Sub-Branding Line
    elements.append(
        Paragraph(
            "<font size=10 color='#7f8c8d'>Prothexa AI Clinical Mobility Platform</font>",
            styles["Normal"]
        )
    )
    elements.append(Spacer(1, 0.1 * inch))

    # 3. Thin Divider Line
    divider = Table([[""]], colWidths=[6 * inch])
    divider.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -1), 1, colors.HexColor("#2C3E50"))
    ]))
    elements.append(divider)
    elements.append(Spacer(1, 0.3 * inch))
    
    # 4. Patient Info
    patient_info = [
        [Paragraph(f"<b>Patient Name:</b> {data['patient_name']}", body_style), 
         Paragraph(f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}", body_style)],
        [Paragraph(f"<b>Age:</b> {data['patient_age']}", body_style), 
         Paragraph(f"<b>Report ID:</b> PBAR-{datetime.now().strftime('%H%M%S')}", body_style)]
    ]
    
    info_table = Table(patient_info, colWidths=[3 * inch, 3 * inch])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.2 * inch))
    
    # Clinical Profile Table
    elements.append(Paragraph("Patient Clinical Profile", header_style))
    clinical = data.get('clinical_profile', {})
    
    clinical_data = [
        ["Parameter", "Value"],
        ["Gender", clinical.get("gender", "N/A")],
        ["Height", f"{clinical.get('height_cm', 'N/A')} cm"],
        ["Weight", f"{clinical.get('weight_kg', 'N/A')} kg"],
        ["BMI", f"{clinical.get('bmi', 'N/A')}"],
        ["Blood Pressure", f"{clinical.get('blood_pressure', 'N/A')} mmHg"],
        ["Blood Sugar", f"{clinical.get('blood_sugar_mg_dl', 'N/A')} mg/dL"],
        ["Existing Conditions", ", ".join(clinical.get('medical_conditions', [])) if clinical.get('medical_conditions') else "None"]
    ]
    
    # Risk Highlighting for Clinical Data
    bmi_val = clinical.get('bmi', 0)
    sugar_val = clinical.get('blood_sugar_mg_dl', 0)
    bp_sys = int(clinical.get('blood_pressure', '120/80').split('/')[0])

    clin_table = Table(clinical_data, colWidths=[2.5 * inch, 3.5 * inch])
    clin_table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#ECF0F1")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]
    
    if bmi_val > 30:
        clin_table_style.append(('TEXTCOLOR', (1, 4), (1, 4), colors.red))
        clinical_data[4][1] += " (Obesity Risk)"
    if bp_sys > 140:
        clin_table_style.append(('TEXTCOLOR', (1, 5), (1, 5), colors.red))
        clinical_data[5][1] += " (Hypertension Alert)"
    if sugar_val > 180:
        clin_table_style.append(('TEXTCOLOR', (1, 6), (1, 6), colors.red))
        clinical_data[6][1] += " (Hyperglycemia Risk)"
        
    clin_table.setStyle(TableStyle(clin_table_style))
    elements.append(clin_table)
    elements.append(Spacer(1, 0.2 * inch))

    # Metrics Table
    elements.append(Paragraph("Gait Metrics Summary", header_style))
    metrics = data.get('metrics', {})
    classification = data.get('classification', {})

    table_data = [
        ["Metric", "Value", "Interpretation"],
        ["Step Length", f"{metrics.get('avg_step_length_cm', 'N/A')} cm", "Normal" if metrics.get('avg_step_length_cm', 0) >= 30 else "Low"],
        ["Cadence", f"{metrics.get('avg_cadence_spm', 'N/A')} spm", "Normal" if metrics.get('avg_cadence_spm', 0) >= 70 else "Low"],
        ["Walking Speed", f"{metrics.get('avg_walking_speed_mps', 'N/A')} m/s", "Optimal" if metrics.get('avg_walking_speed_mps', 0) >= 0.7 else "Reduced"],
        ["Gait Symmetry", f"{metrics.get('avg_gait_symmetry_index', 'N/A')}", "Excellent" if metrics.get('avg_gait_symmetry_index', 0) >= 0.9 else "Monitor"],
        ["Skin Temp", f"{metrics.get('avg_skin_temperature_c', 'N/A')} °C", "Stable" if metrics.get('avg_skin_temperature_c', 0) <= 34 else "Alert"],
        ["Pressure Distribution", f"{metrics.get('avg_pressure_distribution_index', 'N/A')}", "Balanced" if metrics.get('avg_pressure_distribution_index', 0) >= 0.8 else "Imbalanced"],
        ["Skin Moisture", f"{metrics.get('avg_skin_moisture', 'N/A')} %", "Low Risk" if metrics.get('avg_skin_moisture', 0) <= 70 else "High Risk"]
    ]
    
    metrics_table = Table(table_data, colWidths=[2 * inch, 1.5 * inch, 2.5 * inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#ECF0F1")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(metrics_table)
    elements.append(Spacer(1, 0.2 * inch))

    # Risk Classification Section
    elements.append(Paragraph("Risk Classification", header_style))
    risk_data = [
        ["Factor", "Status"],
        ["Gait Abnormality", classification.get("gait_abnormality", "N/A")],
        ["Skin Irritation Risk", classification.get("skin_risk", "N/A")],
        ["Prosthetic Health Score", f"{classification.get('prosthetic_health_score', 'N/A')}/100"],
        ["Overall Clinical Risk", classification.get("overall_clinical_risk", "Low")]
    ]
    risk_table = Table(risk_data, colWidths=[3 * inch, 3 * inch])
    risk_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (1, 4), (1, 4), colors.orange if classification.get("overall_clinical_risk") == "Moderate" else colors.red if classification.get("overall_clinical_risk") == "High" else colors.green),
    ]))
    elements.append(risk_table)
    elements.append(Spacer(1, 0.3 * inch))
    
    # Clinical Analysis Section
    elements.append(Paragraph("Clinical Analysis Summary", header_style))
    analysis_data = data.get('analysis', [])
    
    if isinstance(analysis_data, list):
        for line in analysis_data:
             elements.append(Paragraph(line, body_style))
             elements.append(Spacer(1, 0.05 * inch))
    else:
        # Fallback for old data or string format
        analysis_text = str(analysis_data).replace('\n', '<br/>')
        elements.append(Paragraph(analysis_text, body_style))
    elements.append(Spacer(1, 0.4 * inch))
    
    # Medical Disclaimer
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph("This AI-generated report is for information purposes only and does not replace professional medical consultation.", disclaimer_style))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer
