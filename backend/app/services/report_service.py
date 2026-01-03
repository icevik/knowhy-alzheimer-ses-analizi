import os
import uuid
from datetime import datetime
from typing import Dict
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
from app.core.config import settings

# Türkçe karakter destekli fontları kaydet
FONT_PATH = "/usr/share/fonts/truetype/dejavu/"
try:
    pdfmetrics.registerFont(TTFont('DejaVu', os.path.join(FONT_PATH, 'DejaVuSans.ttf')))
    pdfmetrics.registerFont(TTFont('DejaVu-Bold', os.path.join(FONT_PATH, 'DejaVuSans-Bold.ttf')))
    TURKISH_FONT = 'DejaVu'
    TURKISH_FONT_BOLD = 'DejaVu-Bold'
except Exception as e:
    print(f"Font yüklenemedi, varsayılan font kullanılacak: {e}")
    TURKISH_FONT = 'Helvetica'
    TURKISH_FONT_BOLD = 'Helvetica-Bold'


class ReportService:
    def __init__(self):
        os.makedirs(settings.reports_dir, exist_ok=True)
    
    def _create_header_footer(self, canvas, doc):
        """Her sayfaya header ve footer ekle"""
        canvas.saveState()
        
        # Footer Sol
        footer_text = "KNOWHY Alzheimer Analiz Raporu"
        canvas.setFont(TURKISH_FONT, 8)
        canvas.setFillColor(colors.HexColor('#666666'))
        canvas.drawString(2*cm, 1.5*cm, footer_text)
        
        # Footer Orta - Web Sitesi
        canvas.drawCentredString(A4[0]/2, 1.5*cm, "www.knowhy.co")
        
        # Footer Sağ - Sayfa numarası
        page_num = f"Sayfa {doc.page}"
        canvas.drawRightString(A4[0] - 2*cm, 1.5*cm, page_num)
        
        # Alt çizgi
        canvas.setStrokeColor(colors.HexColor('#e0e0e0'))
        canvas.line(2*cm, 2*cm, A4[0] - 2*cm, 2*cm)
        
        canvas.restoreState()
    
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
        file_name = f"Knowhy_Rapor_{uuid.uuid4().hex[:8]}.pdf"
        file_path = os.path.join(settings.reports_dir, file_name)
        
        # PDF dokümanı oluştur
        doc = SimpleDocTemplate(
            file_path, 
            pagesize=A4,
            leftMargin=2*cm,
            rightMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2.5*cm
        )
        story = []
        
        # Stiller
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName=TURKISH_FONT_BOLD,
            fontSize=22,
            textColor=colors.HexColor('#1a365d'),
            spaceAfter=20,
            alignment=TA_CENTER,
            leading=28
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontName=TURKISH_FONT,
            fontSize=11,
            textColor=colors.HexColor('#4a5568'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontName=TURKISH_FONT_BOLD,
            fontSize=14,
            textColor=colors.HexColor('#2d3748'),
            spaceAfter=12,
            spaceBefore=20,
            borderPadding=5
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=TURKISH_FONT,
            fontSize=10,
            textColor=colors.HexColor('#2d3748'),
            alignment=TA_JUSTIFY,
            leading=14,
            spaceAfter=8
        )
        
        # ===== BAŞLIK =====
        story.append(Paragraph("SES ANALİZİ RAPORU", title_style))
        
        # Alt başlık
        date_str = datetime.now().strftime("%d %B %Y, %H:%M")
        story.append(Paragraph(f"Oluşturulma Tarihi: {date_str}", subtitle_style))
        
        # Ayırıcı çizgi
        story.append(Spacer(1, 0.2*inch))
        
        # ===== KATILIMCI BİLGİLERİ =====
        story.append(Paragraph("📋 KATILIMCI BİLGİLERİ", heading_style))
        
        group_colors = {
            'alzheimer': colors.HexColor('#e53e3e'),
            'mci': colors.HexColor('#dd6b20'),
            'control': colors.HexColor('#38a169')
        }
        group_type = participant_info.get('group_type', 'control').lower()
        group_color = group_colors.get(group_type, colors.HexColor('#4a5568'))
        
        participant_data = [
            ["Alan", "Değer"],
            ["İsim", participant_info.get('name', 'N/A')],
            ["Yaş", str(participant_info.get('age', 'N/A'))],
            ["Cinsiyet", participant_info.get('gender', 'N/A').capitalize()],
            ["Grup", participant_info.get('group_type', 'N/A').upper()],
            ["MMSE Skoru", str(participant_info.get('mmse_score', 'N/A')) if participant_info.get('mmse_score') else 'Belirtilmemiş']
        ]
        
        participant_table = Table(participant_data, colWidths=[4*cm, 12*cm])
        participant_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), TURKISH_FONT_BOLD),
            ('FONTNAME', (0, 1), (-1, -1), TURKISH_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
            ('BACKGROUND', (1, 4), (1, 4), group_color),
            ('TEXTCOLOR', (1, 4), (1, 4), colors.white),
        ]))
        story.append(participant_table)
        story.append(Spacer(1, 0.3*inch))
        
        # ===== TRANSKRİPT =====
        story.append(Paragraph("🎤 TRANSKRİPT", heading_style))
        transcript_text = transcript if transcript else "Transkript mevcut değil."
        # Transkripti kısalt (çok uzunsa)
        if len(transcript_text) > 2000:
            transcript_text = transcript_text[:2000] + "... [devamı kısaltıldı]"
        story.append(Paragraph(transcript_text, normal_style))
        story.append(Spacer(1, 0.3*inch))
        
        # ===== AKUSTİK ÖZELLİKLER =====
        story.append(Paragraph("🔊 AKUSTİK ÖZELLİKLER", heading_style))
        
        acoustic_data = [
            ["Metrik", "Değer", "Açıklama"],
            ["Süre", f"{acoustic_features.get('duration', 0):.2f} sn", "Toplam kayıt süresi"],
            ["Ortalama Pitch", f"{acoustic_features.get('pitch', {}).get('mean', 0):.2f} Hz", "Ses perdesi ortalaması"],
            ["Pitch Std Dev", f"{acoustic_features.get('pitch', {}).get('std', 0):.2f}", "Perde değişkenliği"],
            ["Ortalama Enerji", f"{acoustic_features.get('energy', {}).get('mean', 0):.4f}", "Ses şiddeti ortalaması"],
            ["Tempo", f"{acoustic_features.get('tempo', 0):.2f} BPM", "Konuşma ritmi"],
            ["Spektral Centroid", f"{acoustic_features.get('spectral', {}).get('centroid', 0):.2f}", "Ses parlaklığı"],
        ]
        
        if advanced_acoustic:
            acoustic_data.extend([
                ["Jitter (Local)", f"{advanced_acoustic.get('jitter', {}).get('local', 0):.4f}", "Perde titremesi"],
                ["Shimmer (Local)", f"{advanced_acoustic.get('shimmer', {}).get('local', 0):.4f}", "Şiddet titremesi"],
                ["HNR", f"{advanced_acoustic.get('hnr', 0):.2f} dB", "Harmoni/Gürültü oranı"],
                ["F1 Formant", f"{advanced_acoustic.get('formants', {}).get('F1', 0):.2f} Hz", "Birinci formant"],
                ["F2 Formant", f"{advanced_acoustic.get('formants', {}).get('F2', 0):.2f} Hz", "İkinci formant"],
                ["Duraklama Sayısı", str(advanced_acoustic.get('pause_analysis', {}).get('pause_count', 0)), "Toplam duraklama"],
                ["Ort. Duraklama", f"{advanced_acoustic.get('pause_analysis', {}).get('avg_pause_duration', 0):.2f} sn", "Ortalama duraklama süresi"],
            ])
        
        acoustic_table = Table(acoustic_data, colWidths=[4*cm, 4*cm, 8*cm])
        acoustic_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3182ce')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), TURKISH_FONT_BOLD),
            ('FONTNAME', (0, 1), (-1, -1), TURKISH_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ebf8ff')]),
        ]))
        story.append(acoustic_table)
        story.append(Spacer(1, 0.3*inch))
        
        # ===== DİLBİLİMSEL ANALİZ =====
        if linguistic_analysis:
            story.append(Paragraph("📝 DİLBİLİMSEL ANALİZ", heading_style))
            
            complexity_colors = {
                'low': colors.HexColor('#38a169'),
                'medium': colors.HexColor('#dd6b20'),
                'high': colors.HexColor('#e53e3e')
            }
            
            linguistic_data = [
                ["Metrik", "Değer"],
                ["Toplam Kelime", str(linguistic_analysis.get('word_count', 0))],
                ["Benzersiz Kelime", str(linguistic_analysis.get('unique_word_count', 0))],
                ["Type-Token Ratio", f"{linguistic_analysis.get('type_token_ratio', 0):.3f}"],
                ["Ortalama Cümle Uzunluğu", f"{linguistic_analysis.get('mean_length_utterance', 0):.2f} kelime"],
                ["Cümle Sayısı", str(linguistic_analysis.get('sentence_count', 0))],
                ["Hesitation Sayısı", str(linguistic_analysis.get('hesitation_count', 0))],
                ["Tekrar Sayısı", str(linguistic_analysis.get('repetition_count', 0))],
                ["Sözdizimsel Karmaşıklık", linguistic_analysis.get('syntactic_complexity', 'N/A').upper()],
            ]
            
            linguistic_table = Table(linguistic_data, colWidths=[8*cm, 8*cm])
            linguistic_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#38a169')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), TURKISH_FONT_BOLD),
                ('FONTNAME', (0, 1), (-1, -1), TURKISH_FONT),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0fff4')]),
            ]))
            story.append(linguistic_table)
            story.append(Spacer(1, 0.3*inch))
        
        # ===== DUYGU VE İÇERİK ANALİZİ =====
        if emotion_analysis and content_analysis:
            story.append(Paragraph("💭 DUYGU VE İÇERİK ANALİZİ", heading_style))
            
            tone_colors = {
                'pozitif': colors.HexColor('#38a169'),
                'negatif': colors.HexColor('#e53e3e'),
                'nötr': colors.HexColor('#718096')
            }
            tone = emotion_analysis.get('tone', 'nötr').lower()
            
            emotion_data = [
                ["Metrik", "Değer", "Yorumu"],
                ["Duygu Tonu", emotion_analysis.get('tone', 'N/A').capitalize(), self._get_tone_description(tone)],
                ["Duygu Yoğunluğu", f"{emotion_analysis.get('intensity', 0)}/10", self._get_intensity_description(emotion_analysis.get('intensity', 0))],
                ["Akıcılık Skoru", f"{content_analysis.get('fluency_score', 0)}/10", self._get_fluency_description(content_analysis.get('fluency_score', 0))],
                ["Tutarlılık Skoru", f"{content_analysis.get('coherence_score', 0)}/10", self._get_coherence_description(content_analysis.get('coherence_score', 0))],
            ]
            
            emotion_table = Table(emotion_data, colWidths=[4*cm, 3*cm, 9*cm])
            emotion_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#805ad5')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), TURKISH_FONT_BOLD),
                ('FONTNAME', (0, 1), (-1, -1), TURKISH_FONT),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#faf5ff')]),
            ]))
            story.append(emotion_table)
            story.append(Spacer(1, 0.3*inch))
        
        # ===== KLİNİK DEĞERLENDİRME (GEMİNİ RAPORU) =====
        if gemini_report:
            story.append(PageBreak())
            story.append(Paragraph("🏥 KLİNİK DEĞERLENDİRME VE YORUM", heading_style))
            story.append(Spacer(1, 0.1*inch))
            
            # Markdown'ı temizle ve HTML'e dönüştür
            cleaned_report = self._convert_markdown_to_html(gemini_report)
            
            # Gemini raporunu paragraflara böl
            paragraphs = cleaned_report.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    # Başlıkları tespit et (# ile başlayan veya tamamen büyük harf)
                    stripped = para.strip()
                    if stripped.startswith('#') or (len(stripped) > 3 and stripped.replace(' ', '').replace('.', '').replace(')', '').replace('(', '').isupper()):
                        section_style = ParagraphStyle(
                            'SectionTitle',
                            parent=styles['Heading3'],
                            fontName=TURKISH_FONT_BOLD,
                            fontSize=11,
                            textColor=colors.HexColor('#2d3748'),
                            spaceBefore=15,
                            spaceAfter=8
                        )
                        # # işaretlerini temizle
                        clean_title = stripped.lstrip('#').strip()
                        story.append(Paragraph(clean_title, section_style))
                    else:
                        story.append(Paragraph(stripped, normal_style))
        
        # ===== REPORT SONU =====
        story.append(Spacer(1, 1*inch))
        end_style = ParagraphStyle(
            'EndStyle',
            parent=styles['Normal'],
            fontName=TURKISH_FONT,
            fontSize=10,
            textColor=colors.HexColor('#718096'),
            alignment=TA_CENTER,
            leading=14
        )
        story.append(Paragraph("Powered by KNOWHY", end_style))
        story.append(Paragraph('www.knowhy.co', end_style))
        
        # PDF'i oluştur
        doc.build(story, onFirstPage=self._create_header_footer, onLaterPages=self._create_header_footer)
        
        return file_path
    
    def _get_tone_description(self, tone: str) -> str:
        descriptions = {
            'pozitif': 'Genel olarak olumlu ve iyimser bir ton',
            'negatif': 'Endişe veya olumsuzluk belirtileri mevcut',
            'nötr': 'Dengeli ve tarafsız bir ifade tarzı'
        }
        return descriptions.get(tone.lower(), 'Değerlendirme yapılamadı')
    
    def _get_intensity_description(self, intensity: int) -> str:
        if intensity <= 3:
            return 'Düşük duygusal ifade'
        elif intensity <= 6:
            return 'Orta düzeyde duygusal ifade'
        else:
            return 'Yoğun duygusal ifade'
    
    def _get_fluency_description(self, score: int) -> str:
        if score <= 3:
            return 'Konuşma akıcılığında belirgin zorluklar'
        elif score <= 6:
            return 'Orta düzeyde akıcılık, bazı duraklamalar'
        else:
            return 'İyi akıcılık, düzgün konuşma akışı'
    
    def _get_coherence_description(self, score: int) -> str:
        if score <= 3:
            return 'Tutarlılık sorunları mevcut'
        elif score <= 6:
            return 'Genel olarak tutarlı, bazı sapmalar'
        else:
            return 'Yüksek tutarlılık ve mantıksal bağlantı'
    
    def _convert_markdown_to_html(self, text: str) -> str:
        """Markdown işaretlerini ReportLab HTML'e dönüştür"""
        import re
        
        if not text:
            return text
        
        # **bold** -> <b>bold</b>
        text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
        
        # *italic* -> <i>italic</i>
        text = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', text)
        
        # __bold__ -> <b>bold</b>
        text = re.sub(r'__([^_]+)__', r'<b>\1</b>', text)
        
        # _italic_ -> <i>italic</i>
        text = re.sub(r'_([^_]+)_', r'<i>\1</i>', text)
        
        # - veya * ile başlayan liste öğeleri -> • ile değiştir
        text = re.sub(r'^[\-\*]\s+', '• ', text, flags=re.MULTILINE)
        
        # Sayılı liste (1. 2. 3.) -> olduğu gibi bırak
        
        # ═══ gibi dekoratif karakterleri kaldır
        text = re.sub(r'[═─━═]+', '', text)
        
        # Birden fazla boş satırı tek boş satıra indir
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text


report_service = ReportService()
