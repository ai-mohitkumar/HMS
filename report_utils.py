# backend/report_utils.py
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
import io
from datetime import datetime
import json

def generate_health_report(user, vitals, symptoms, meds, appts):
    """
    Returns bytes of a simple PDF summarizing the supplied records.
    """
    mem = io.BytesIO()
    c = canvas.Canvas(mem, pagesize=letter)
    width, height = letter
    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, f"Health Report — {user.get('name','User')}")
    y -= 25
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Generated: {datetime.now().isoformat(sep=' ', timespec='seconds')}")
    y -= 30
    def draw_section(title, rows, formatter):
        nonlocal y
        c.setFont("Helvetica-Bold", 12); c.drawString(50, y, title); y -= 14
        c.setFont("Helvetica", 9)
        if not rows:
            c.drawString(60, y, "— none"); y -= 16
            return
        for r in rows:
            for line in formatter(r):
                if y < 80:
                    c.showPage(); y = height - 50
                c.drawString(60, y, line)
                y -= 12
            y -= 6
    draw_section("Vitals", vitals, lambda v: [f"{v['timestamp']} — {v['type']}: {v['value']} {v['unit']}"])
    draw_section("Symptoms", symptoms, lambda s: [f"{s['timestamp']} — {s['name']} ({s['system']}) severity={s['severity']}", f"Notes: {s['notes'] or '—'}"])
    draw_section("Medications", meds, lambda m: [f"{m['name']} {m['dose']} — {m['schedule']} (start {m['start_date'] or '—'})"])
    draw_section("Appointments", appts, lambda a: [f"{a['datetime']} — Dr. {a['doctor']} ({a['type']})"])
    c.showPage()
    c.save()
    mem.seek(0)
    return mem.read()

def generate_patient_bill(patient, caretakers, hospitality, checkups, bills):
    """
    Generate a professional patient bill/report PDF with patient details, caretaker info, hospitality, checkups, and billing.
    """
    mem = io.BytesIO()
    doc = SimpleDocTemplate(mem, pagesize=letter)
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, spaceAfter=20, alignment=1)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, spaceAfter=10)
    normal_style = styles['Normal']
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])

    story = []

    # Title
    story.append(Paragraph("Professional Patient Report & Bill", title_style))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    story.append(Spacer(1, 20))

    # Patient Information
    story.append(Paragraph("Patient Information", heading_style))
    patient_data = [
        ['Name', patient.get('name', 'N/A')],
        ['Date of Birth', patient.get('dob', 'N/A')],
        ['Gender', patient.get('gender', 'N/A')],
        ['Phone', patient.get('phone', 'N/A')],
        ['Email', patient.get('email', 'N/A')],
        ['Address', patient.get('address', 'N/A')],
        ['Emergency Contact', patient.get('emergency_contact', 'N/A')],
        ['Emergency Phone', patient.get('emergency_phone', 'N/A')],
        ['Blood Type', patient.get('blood_type', 'N/A')],
        ['Medical History', patient.get('medical_history', 'N/A')],
        ['Allergies', patient.get('allergies', 'N/A')]
    ]
    patient_table = Table(patient_data, colWidths=[120, 300])
    patient_table.setStyle(table_style)
    story.append(patient_table)
    story.append(Spacer(1, 20))

    # Caretaker Information
    if caretakers:
        story.append(Paragraph("Caretaker/Family Information", heading_style))
        caretaker_data = [['Name', 'Relationship', 'Phone', 'Email', 'Address']]
        for caretaker in caretakers:
            caretaker_data.append([
                caretaker.get('name', 'N/A'),
                caretaker.get('relationship', 'N/A'),
                caretaker.get('phone', 'N/A'),
                caretaker.get('email', 'N/A'),
                caretaker.get('address', 'N/A')
            ])
        caretaker_table = Table(caretaker_data, colWidths=[100, 80, 100, 120, 120])
        caretaker_table.setStyle(table_style)
        story.append(caretaker_table)
        story.append(Spacer(1, 20))

    # Hospitality Information
    if hospitality:
        story.append(Paragraph("Hospital Stay Information", heading_style))
        hosp_data = [['Admission Date', 'Discharge Date', 'Room Number', 'Room Type', 'Services', 'Daily Rate', 'Status']]
        for hosp in hospitality:
            hosp_data.append([
                hosp.get('admission_date', 'N/A'),
                hosp.get('discharge_date', 'N/A'),
                hosp.get('room_number', 'N/A'),
                hosp.get('room_type', 'N/A'),
                hosp.get('services', 'N/A'),
                f"${hosp.get('daily_rate', 0):.2f}",
                hosp.get('status', 'N/A')
            ])
        hosp_table = Table(hosp_data, colWidths=[80, 80, 80, 80, 100, 60, 60])
        hosp_table.setStyle(table_style)
        story.append(hosp_table)
        story.append(Spacer(1, 20))

    # Checkup/Medical Test Results
    if checkups:
        story.append(Paragraph("Medical Checkup Results", heading_style))
        checkup_data = [['Date', 'Test Type', 'Test Name', 'Value', 'Unit', 'Reference Range', 'Status', 'Performed By']]
        for checkup in checkups:
            checkup_data.append([
                checkup.get('timestamp', 'N/A')[:10],
                checkup.get('test_type', 'N/A'),
                checkup.get('test_name', 'N/A'),
                checkup.get('value', 'N/A'),
                checkup.get('unit', 'N/A'),
                checkup.get('reference_range', 'N/A'),
                checkup.get('result_status', 'N/A'),
                checkup.get('performed_by', 'N/A')
            ])
        checkup_table = Table(checkup_data, colWidths=[70, 80, 100, 60, 50, 100, 60, 80])
        checkup_table.setStyle(table_style)
        story.append(checkup_table)
        story.append(Spacer(1, 20))

    # Billing Information
    if bills:
        story.append(Paragraph("Billing Details", heading_style))
        for bill in bills:
            story.append(Paragraph(f"Bill Date: {bill.get('bill_date', 'N/A')[:10]}", normal_style))
            story.append(Paragraph(f"Payment Status: {bill.get('payment_status', 'N/A').title()}", normal_style))

            # Itemized charges
            itemized_charges = bill.get('itemized_charges', '[]')
            if itemized_charges:
                try:
                    charges = json.loads(itemized_charges)
                    if charges:
                        bill_data = [['Description', 'Quantity', 'Unit Price', 'Total']]
                        for charge in charges:
                            bill_data.append([
                                charge.get('description', 'N/A'),
                                str(charge.get('quantity', 1)),
                                f"${charge.get('unit_price', 0):.2f}",
                                f"${charge.get('total', 0):.2f}"
                            ])
                        bill_table = Table(bill_data, colWidths=[200, 60, 80, 80])
                        bill_table.setStyle(table_style)
                        story.append(bill_table)
                        story.append(Spacer(1, 10))
                except:
                    pass

            # Totals
            subtotal = bill.get('subtotal', 0)
            tax_rate = bill.get('tax_rate', 0.1)
            tax_amount = bill.get('tax_amount', 0)
            total_amount = bill.get('total_amount', 0)

            totals_data = [
                ['Subtotal', f"${subtotal:.2f}"],
                ['Tax Rate', f"{tax_rate*100:.1f}%"],
                ['Tax Amount', f"${tax_amount:.2f}"],
                ['Total Amount', f"${total_amount:.2f}"]
            ]
            totals_table = Table(totals_data, colWidths=[100, 100])
            totals_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
            ]))
            story.append(totals_table)
            story.append(Spacer(1, 20))

    # Footer
    story.append(Spacer(1, 30))
    story.append(Paragraph("Thank you for choosing our healthcare services.", normal_style))
    story.append(Paragraph("For any questions, please contact our billing department.", normal_style))

    doc.build(story)
    mem.seek(0)
    return mem.read()
