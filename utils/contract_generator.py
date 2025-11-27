"""Contract/Agreement generation service for Roomies platform."""

import os
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY


class ContractGenerator:
    """Generate rental agreements/contracts as PDF."""
    
    def __init__(self, output_dir="static/contracts"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_rental_agreement(self, booking, room, student, owner):
        """Generate a comprehensive rental agreement PDF."""
        
        filename = f"Rental_Agreement_{booking.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        # Create PDF
        doc = SimpleDocTemplate(filepath, pagesize=A4,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=18)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
        styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=14, fontName='Helvetica-Bold'))
        styles.add(ParagraphStyle(name='Title', alignment=TA_CENTER, fontSize=16, fontName='Helvetica-Bold', spaceAfter=30))
        
        # Title
        title = Paragraph("<b>RESIDENTIAL RENTAL AGREEMENT</b>", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Agreement Date
        date_text = Paragraph(
            f"<b>Agreement Date:</b> {datetime.now().strftime('%d %B, %Y')}",
            styles['Normal']
        )
        elements.append(date_text)
        elements.append(Spacer(1, 12))
        
        # Parties Section
        parties_title = Paragraph("<b>PARTIES TO THIS AGREEMENT</b>", styles['Center'])
        elements.append(parties_title)
        elements.append(Spacer(1, 12))
        
        owner_details = f"""
        <b>THE OWNER (Landlord):</b><br/>
        Name: {owner.name}<br/>
        Email: {owner.email}<br/>
        Status: {'Verified' if owner.kyc_verified else 'Pending Verification'}<br/>
        <br/>
        <b>THE TENANT (Student):</b><br/>
        Name: {student.name}<br/>
        Email: {student.email}<br/>
        College: {student.college}<br/>
        Status: {'Verified' if student.verified else 'Pending Verification'}
        """
        elements.append(Paragraph(owner_details, styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Property Details
        property_title = Paragraph("<b>PROPERTY DETAILS</b>", styles['Center'])
        elements.append(property_title)
        elements.append(Spacer(1, 12))
        
        property_details = f"""
        <b>Property Address:</b> {room.title}, {room.location}<br/>
        <b>Property Type:</b> {room.property_type.title()}<br/>
        <b>Near College:</b> {room.college_nearby}<br/>
        <b>Amenities:</b> {room.amenities if room.amenities else 'As per property description'}
        """
        elements.append(Paragraph(property_details, styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Financial Terms
        financial_title = Paragraph("<b>FINANCIAL TERMS</b>", styles['Center'])
        elements.append(financial_title)
        elements.append(Spacer(1, 12))
        
        financial_data = [
            ['Description', 'Amount (₹)'],
            ['Monthly Rent', f'{booking.monthly_rent:,.2f}'],
            ['Security Deposit (Refundable)', f'{booking.security_deposit:,.2f}'],
            ['Booking Fee (Non-refundable)', f'{booking.booking_amount:,.2f}'],
            ['Platform Service Fee', f'{booking.platform_fee:,.2f}'],
            ['Total Amount Paid', f'{booking.total_paid:,.2f}'],
        ]
        
        financial_table = Table(financial_data, colWidths=[3.5*inch, 2*inch])
        financial_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(financial_table)
        elements.append(Spacer(1, 20))
        
        # Contract Period
        contract_title = Paragraph("<b>CONTRACT PERIOD</b>", styles['Center'])
        elements.append(contract_title)
        elements.append(Spacer(1, 12))
        
        contract_period = f"""
        <b>Start Date:</b> {booking.contract_start_date.strftime('%d %B, %Y')}<br/>
        <b>End Date:</b> {booking.contract_end_date.strftime('%d %B, %Y')}<br/>
        <b>Duration:</b> {booking.contract_duration_months} months<br/>
        <b>Move-in Date:</b> {booking.move_in_date.strftime('%d %B, %Y') if booking.move_in_date else 'To be confirmed'}
        """
        elements.append(Paragraph(contract_period, styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Terms and Conditions
        terms_title = Paragraph("<b>TERMS AND CONDITIONS</b>", styles['Center'])
        elements.append(terms_title)
        elements.append(Spacer(1, 12))
        
        terms = """
        <b>1. RENT PAYMENT</b><br/>
        1.1. Monthly rent is payable on or before the 1st day of each month.<br/>
        1.2. Payment should be made via the Roomies platform using approved payment methods.<br/>
        1.3. Grace period: 5 days. Late payment charge: ₹100 per day after grace period.<br/>
        1.4. Rent may be revised annually with 60 days prior notice.<br/>
        <br/>
        <b>2. SECURITY DEPOSIT</b><br/>
        2.1. Security deposit is refundable at the end of tenancy.<br/>
        2.2. Deductions may be made for damages, unpaid rent, or utility bills.<br/>
        2.3. Deposit will be refunded within 30 days of vacating the property.<br/>
        2.4. Normal wear and tear is acceptable and will not affect deposit.<br/>
        <br/>
        <b>3. TENANT RESPONSIBILITIES</b><br/>
        3.1. Maintain the property in good condition.<br/>
        3.2. Pay utility bills (electricity, water, internet) as per agreement.<br/>
        3.3. Obtain written permission for any structural modifications.<br/>
        3.4. Allow property inspection with 24-hour notice.<br/>
        3.5. Use property only for residential purposes.<br/>
        3.6. Comply with society/building rules and regulations.<br/>
        <br/>
        <b>4. OWNER RESPONSIBILITIES</b><br/>
        4.1. Provide peaceful possession of the property.<br/>
        4.2. Maintain structural integrity and common areas.<br/>
        4.3. Ensure all amenities listed are functional.<br/>
        4.4. Address major repairs within reasonable time.<br/>
        4.5. Provide 60 days notice for any major changes.<br/>
        <br/>
        <b>5. TERMINATION</b><br/>
        5.1. Either party may terminate with 60 days written notice.<br/>
        5.2. Early termination: Tenant forfeits one month rent (deducted from deposit).<br/>
        5.3. Immediate termination for breach of contract terms.<br/>
        5.4. Natural disasters/force majeure: Mutual discussion required.<br/>
        <br/>
        <b>6. PROHIBITED ACTIVITIES</b><br/>
        6.1. Subletting without owner consent.<br/>
        6.2. Illegal activities or disturbance to neighbors.<br/>
        6.3. Keeping pets without prior written permission.<br/>
        6.4. Smoking in non-designated areas.<br/>
        6.5. Overcrowding beyond agreed occupancy.<br/>
        <br/>
        <b>7. DISPUTE RESOLUTION</b><br/>
        7.1. Disputes should first be resolved through Roomies platform mediation.<br/>
        7.2. If unresolved, parties agree to arbitration under Indian Arbitration Act.<br/>
        7.3. Jurisdiction: Courts of the property location.<br/>
        <br/>
        <b>8. INSURANCE</b><br/>
        8.1. Owner maintains property insurance.<br/>
        8.2. Tenant advised to obtain renter's insurance for personal belongings.<br/>
        <br/>
        <b>9. NOTICES</b><br/>
        9.1. All notices to be sent via registered email or Roomies platform.<br/>
        9.2. Email to registered addresses considered valid communication.<br/>
        <br/>
        <b>10. ENTIRE AGREEMENT</b><br/>
        10.1. This agreement constitutes the entire understanding between parties.<br/>
        10.2. Any modifications must be in writing and signed by both parties.<br/>
        10.3. This agreement is governed by the laws of India.
        """
        elements.append(Paragraph(terms, styles['Justify']))
        elements.append(Spacer(1, 30))
        
        # Signatures
        elements.append(PageBreak())
        
        signature_title = Paragraph("<b>SIGNATURES</b>", styles['Center'])
        elements.append(signature_title)
        elements.append(Spacer(1, 30))
        
        signatures = f"""
        By signing below, both parties acknowledge that they have read, understood, and agree to abide by all terms and conditions of this agreement.<br/>
        <br/><br/>
        <b>OWNER/LANDLORD:</b><br/>
        Name: {owner.name}<br/>
        Signature: _______________________________<br/>
        Date: {datetime.now().strftime('%d %B, %Y')}<br/>
        <br/><br/><br/>
        <b>TENANT/STUDENT:</b><br/>
        Name: {student.name}<br/>
        Signature: _______________________________<br/>
        Date: {datetime.now().strftime('%d %B, %Y')}<br/>
        <br/><br/><br/>
        <b>WITNESS (Roomies Platform):</b><br/>
        Platform Representative<br/>
        Signature: _______________________________<br/>
        Date: {datetime.now().strftime('%d %B, %Y')}<br/>
        <br/><br/>
        <i>This is a digitally generated agreement facilitated by Roomies Platform.<br/>
        For queries, contact: support@roomies.in | +91-1234567890</i>
        """
        elements.append(Paragraph(signatures, styles['Normal']))
        
        # Build PDF
        doc.build(elements)
        
        return filepath


# Initialize contract generator
contract_generator = ContractGenerator()
