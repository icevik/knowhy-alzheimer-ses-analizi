import os
import uuid
from datetime import datetime
from typing import Dict
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import matplotlib
matplotlib.use('Agg')  # GUI olmadan çalışmak için
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
from app.core.config import settings


class ReportService:
    def __init__(self):
        os.makedirs(settings.reports_dir, exist_ok=True)
    
    def create_pdf_report(
        self,
        participant_info: Dict,
        transcript: str,
        acoustic_features: Dict,
        advanced_acoustic: Dict,
        linguistic_analysis: Dict,
        emotion_analysis: Dict,
        content_analysis: Dict,
        gemini_report: str | None = None
    ) -> str:
        """PDF rapor oluştur"""
        
        # Dosya adı
        file_name = f"rapor_{uuid.uuid4().hex[:8]}.pdf"
        file_path = os.path.join(settings.reports_dir, file_name)
        
        # PDF dokümanı oluştur
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        story = []
        
        # Stiller
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            spaceBefore=20
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#333333'),
            alignment=TA_JUSTIFY,
            leading=14
        )
        
        # Başlık
        story.append(Paragraph("SES ANALİZİ RAPORU", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Tarih
        date_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        story.append(Paragraph(f"<b>Tarih:</b> {date_str}", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Katılımcı bilgileri
        story.append(Paragraph("KATILIMCI BİLGİLERİ", heading_style))
        participant_data = [
            ["İsim:", participant_info.get('name', 'N/A')],
            ["Yaş:", str(participant_info.get('age', 'N/A'))],
            ["Cinsiyet:", participant_info.get('gender', 'N/A')],
            ["Grup:", participant_info.get('group_type', 'N/A').upper()],
            ["MMSE Skoru:", str(participant_info.get('mmse_score', 'N/A'))]
        ]
        participant_table = Table(participant_data, colWidths=[2*inch, 4*inch])
        participant_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        story.append(participant_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Transkript
        story.append(Paragraph("TRANSCRİPT", heading_style))
        transcript_text = transcript if transcript else "Transkript mevcut değil."
        story.append(Paragraph(transcript_text, normal_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Akustik özellikler tablosu
        story.append(Paragraph("AKUSTİK ÖZELLİKLER", heading_style))
        
        acoustic_data = [
            ["Metrik", "Değer"],
            ["Süre (sn)", f"{acoustic_features.get('duration', 0):.2f}"],
            ["Ortalama Pitch (Hz)", f"{acoustic_features.get('pitch', {}).get('mean', 0):.2f}"],
            ["Pitch Std Dev", f"{acoustic_features.get('pitch', {}).get('std', 0):.2f}"],
            ["Ortalama Enerji", f"{acoustic_features.get('energy', {}).get('mean', 0):.4f}"],
            ["Tempo (BPM)", f"{acoustic_features.get('tempo', 0):.2f}"],
            ["Spektral Centroid", f"{acoustic_features.get('spectral', {}).get('centroid', 0):.2f}"],
        ]
        
        if advanced_acoustic:
            acoustic_data.extend([
                ["Jitter (Local)", f"{advanced_acoustic.get('jitter', {}).get('local', 0):.4f}"],
                ["Shimmer (Local)", f"{advanced_acoustic.get('shimmer', {}).get('local', 0):.4f}"],
                ["HNR (dB)", f"{advanced_acoustic.get('hnr', 0):.2f}"],
                ["F1 Formant (Hz)", f"{advanced_acoustic.get('formants', {}).get('F1', 0):.2f}"],
                ["F2 Formant (Hz)", f"{advanced_acoustic.get('formants', {}).get('F2', 0):.2f}"],
                ["Duraklama Sayısı", str(advanced_acoustic.get('pause_analysis', {}).get('pause_count', 0))],
                ["Ort. Duraklama Süresi (sn)", f"{advanced_acoustic.get('pause_analysis', {}).get('avg_pause_duration', 0):.2f}"],
            ])
        
        acoustic_table = Table(acoustic_data, colWidths=[3*inch, 3*inch])
        acoustic_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))
        story.append(acoustic_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Dilbilimsel analiz
        if linguistic_analysis:
            story.append(Paragraph("DİLBİLİMSEL ANALİZ", heading_style))
            linguistic_data = [
                ["Metrik", "Değer"],
                ["Toplam Kelime", str(linguistic_analysis.get('word_count', 0))],
                ["Benzersiz Kelime", str(linguistic_analysis.get('unique_word_count', 0))],
                ["Type-Token Ratio", f"{linguistic_analysis.get('type_token_ratio', 0):.3f}"],
                ["Ortalama Cümle Uzunluğu", f"{linguistic_analysis.get('mean_length_utterance', 0):.2f}"],
                ["Cümle Sayısı", str(linguistic_analysis.get('sentence_count', 0))],
                ["Hesitation Sayısı", str(linguistic_analysis.get('hesitation_count', 0))],
                ["Tekrar Sayısı", str(linguistic_analysis.get('repetition_count', 0))],
                ["Sözdizimsel Karmaşıklık", linguistic_analysis.get('syntactic_complexity', 'N/A').upper()],
            ]
            
            linguistic_table = Table(linguistic_data, colWidths=[3*inch, 3*inch])
            linguistic_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
            ]))
            story.append(linguistic_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Duygu ve içerik analizi
        if emotion_analysis and content_analysis:
            story.append(Paragraph("DUYGU VE İÇERİK ANALİZİ", heading_style))
            emotion_data = [
                ["Metrik", "Değer"],
                ["Duygu Tonu", emotion_analysis.get('tone', 'N/A').upper()],
                ["Duygu Yoğunluğu", f"{emotion_analysis.get('intensity', 0)}/10"],
                ["Akıcılık Skoru", f"{content_analysis.get('fluency_score', 0)}/10"],
                ["Tutarlılık Skoru", f"{content_analysis.get('coherence_score', 0)}/10"],
            ]
            
            emotion_table = Table(emotion_data, colWidths=[3*inch, 3*inch])
            emotion_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
            ]))
            story.append(emotion_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Gemini raporu
        if gemini_report:
            story.append(PageBreak())
            story.append(Paragraph("KLİNİK DEĞERLENDİRME VE YORUM", heading_style))
            # Gemini raporunu paragraflara böl
            paragraphs = gemini_report.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    story.append(Paragraph(para.strip(), normal_style))
                    story.append(Spacer(1, 0.1*inch))
        
        # PDF'i oluştur
        doc.build(story)
        
        return file_path


report_service = ReportService()

