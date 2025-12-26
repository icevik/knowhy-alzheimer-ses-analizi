import librosa
import numpy as np
import parselmouth
from typing import Dict
from scipy import signal


class AdvancedAudioService:
    @staticmethod
    def extract_advanced_features(audio_path: str) -> Dict:
        """Gelişmiş akustik özellikler çıkar: jitter, shimmer, HNR, formantlar"""
        try:
            y, sr = librosa.load(audio_path, sr=None)
            duration = librosa.get_duration(y=y, sr=sr)
        except Exception as e:
            # Librosa yükleme hatası
            return {
                "jitter": {"local": 0.0, "rap": 0.0, "ppq5": 0.0},
                "shimmer": {"local": 0.0, "apq3": 0.0, "apq5": 0.0},
                "hnr": 0.0,
                "formants": {"F1": 0.0, "F2": 0.0, "F3": 0.0, "F4": 0.0},
                "speech_rate_audio": 0.0,
                "voiced_ratio": 0.0,
                "pause_analysis": {
                    "total_pause_time": 0.0,
                    "pause_count": 0,
                    "avg_pause_duration": 0.0,
                    "pause_percentage": 0.0
                },
                "voice_onset_time": 0.0
            }
        
        # Parselmouth ile ses analizi
        try:
            sound = parselmouth.Sound(audio_path)
        except Exception as e:
            # Parselmouth başarısız olursa, sadece librosa ile temel özellikler döndür
            rms = librosa.feature.rms(y=y)[0]
            return {
                "jitter": {"local": 0.0, "rap": 0.0, "ppq5": 0.0},
                "shimmer": {"local": 0.0, "apq3": 0.0, "apq5": 0.0},
                "hnr": 0.0,
                "formants": {"F1": 0.0, "F2": 0.0, "F3": 0.0, "F4": 0.0},
                "speech_rate_audio": 0.0,
                "voiced_ratio": 0.0,
                "pause_analysis": {
                    "total_pause_time": 0.0,
                    "pause_count": 0,
                    "avg_pause_duration": 0.0,
                    "pause_percentage": 0.0
                },
                "voice_onset_time": 0.0
            }
        
        # Pitch analizi - Praat standartlarına uygun
        try:
            pitch = sound.to_pitch()
        except Exception:
            pitch = None
        pitch_values = pitch.selected_array['frequency']
        pitch_values = pitch_values[pitch_values > 0]  # Sıfır olmayan değerler
        
        # Jitter (pitch varyasyonu) - Praat metodolojisi
        jitter_local = 0.0
        jitter_rap = 0.0
        jitter_ppq5 = 0.0
        
        if len(pitch_values) > 1:
            # Period değerlerini hesapla (1/frequency)
            periods = 1.0 / pitch_values
            periods = periods[periods > 0]  # Geçerli period değerleri
            
            if len(periods) > 1:
                mean_period = np.mean(periods)
                
                if mean_period > 0:
                    # Local Jitter: ardışık period farklarının ortalaması / ortalama period
                    period_diffs = np.abs(np.diff(periods))
                    jitter_local = np.mean(period_diffs) / mean_period
                    
                    # RAP (Relative Average Perturbation) - 3 noktalı ortalama
                    if len(periods) >= 3:
                        rap_diffs = []
                        for i in range(len(periods) - 2):
                            # 3 noktalı ortalama
                            local_avg = np.mean(periods[i:i+3])
                            # Ortadaki değerin ortalamadan sapması
                            rap_diffs.append(abs(periods[i+1] - local_avg))
                        jitter_rap = np.mean(rap_diffs) / mean_period if len(rap_diffs) > 0 else 0.0
                    
                    # PPQ5 (5-point Period Perturbation Quotient)
                    if len(periods) >= 5:
                        ppq5_diffs = []
                        for i in range(len(periods) - 4):
                            # 5 noktalı ortalama
                            local_avg = np.mean(periods[i:i+5])
                            # Ortadaki (3.) değerin ortalamadan sapması
                            ppq5_diffs.append(abs(periods[i+2] - local_avg))
                        jitter_ppq5 = np.mean(ppq5_diffs) / mean_period if len(ppq5_diffs) > 0 else 0.0
        
        # Shimmer (amplitud varyasyonu) - Praat metodolojisi
        shimmer_local = 0.0
        shimmer_apq3 = 0.0
        shimmer_apq5 = 0.0
        
        try:
            # Intensity değerlerini al (dB cinsinden)
            intensity = sound.to_intensity()
            intensity_values = intensity.values[0]
            
            # Pitch frame'leri ile eşleştirmek için zaman bazlı örnekleme
            # Pitch ve intensity aynı zaman noktalarında olmayabilir
            pitch_times = pitch.ts()
            intensity_times = intensity.ts()
            
            # Pitch zamanlarına karşılık gelen intensity değerlerini bul
            aligned_intensity = []
            for pt in pitch_times:
                # En yakın intensity zamanını bul
                idx = np.argmin(np.abs(intensity_times - pt))
                aligned_intensity.append(intensity_values[idx])
            
            aligned_intensity = np.array(aligned_intensity)
            aligned_intensity = aligned_intensity[aligned_intensity > 0]  # Pozitif değerler
            
            if len(aligned_intensity) > 1:
                mean_amp = np.mean(aligned_intensity)
                
                if mean_amp > 0:
                    # Local Shimmer: ardışık amplitud farklarının ortalaması / ortalama amplitud
                    amp_diffs = np.abs(np.diff(aligned_intensity))
                    shimmer_local = np.mean(amp_diffs) / mean_amp
                    
                    # APQ3 (3-point Amplitude Perturbation Quotient)
                    if len(aligned_intensity) >= 3:
                        apq3_diffs = []
                        for i in range(len(aligned_intensity) - 2):
                            # 3 noktalı ortalama
                            local_avg = np.mean(aligned_intensity[i:i+3])
                            # Ortadaki değerin ortalamadan sapması
                            apq3_diffs.append(abs(aligned_intensity[i+1] - local_avg))
                        shimmer_apq3 = np.mean(apq3_diffs) / mean_amp if len(apq3_diffs) > 0 else 0.0
                    
                    # APQ5 (5-point Amplitude Perturbation Quotient)
                    if len(aligned_intensity) >= 5:
                        apq5_diffs = []
                        for i in range(len(aligned_intensity) - 4):
                            # 5 noktalı ortalama
                            local_avg = np.mean(aligned_intensity[i:i+5])
                            # Ortadaki (3.) değerin ortalamadan sapması
                            apq5_diffs.append(abs(aligned_intensity[i+2] - local_avg))
                        shimmer_apq5 = np.mean(apq5_diffs) / mean_amp if len(apq5_diffs) > 0 else 0.0
        except Exception as e:
            # Fallback: basit RMS tabanlı shimmer
            try:
                rms = librosa.feature.rms(y=y)[0]
                rms = rms[rms > 0]
                if len(rms) > 1:
                    mean_rms = np.mean(rms)
                    if mean_rms > 0:
                        amp_diffs = np.abs(np.diff(rms))
                        shimmer_local = np.mean(amp_diffs) / mean_rms
            except:
                pass
        
        # HNR (Harmonic-to-Noise Ratio)
        hnr = 0.0
        try:
            hnr_praat = sound.to_harmonicity()
            hnr_values = hnr_praat.values[0]
            hnr_values = hnr_values[~np.isnan(hnr_values)]
            hnr_values = hnr_values[hnr_values > -50]  # Mantıklı değerler
            if len(hnr_values) > 0:
                hnr = float(np.mean(hnr_values))
        except:
            # Fallback: librosa ile basit HNR hesabı
            harmonic, percussive = librosa.effects.hpss(y)
            if np.var(harmonic) > 0:
                hnr = 10 * np.log10(np.var(harmonic) / (np.var(percussive) + 1e-10))
        
        # Formantlar (F1-F4)
        formants = {"F1": 0.0, "F2": 0.0, "F3": 0.0, "F4": 0.0}
        try:
            formant = sound.to_formant_burg(time_step=0.01)
            # Ortalama formant değerlerini al
            times = formant.ts()
            f1_values = []
            f2_values = []
            f3_values = []
            f4_values = []
            
            for t in times:
                try:
                    f1 = formant.get_value_at_time(1, t)
                    f2 = formant.get_value_at_time(2, t)
                    f3 = formant.get_value_at_time(3, t)
                    f4 = formant.get_value_at_time(4, t)
                    
                    if f1 > 0:
                        f1_values.append(f1)
                    if f2 > 0:
                        f2_values.append(f2)
                    if f3 > 0:
                        f3_values.append(f3)
                    if f4 > 0:
                        f4_values.append(f4)
                except:
                    continue
            
            if f1_values:
                formants["F1"] = float(np.mean(f1_values))
            if f2_values:
                formants["F2"] = float(np.mean(f2_values))
            if f3_values:
                formants["F3"] = float(np.mean(f3_values))
            if f4_values:
                formants["F4"] = float(np.mean(f4_values))
        except:
            pass
        
        # Speech Rate - sesli segmentlerin oranı ve pitch değişim hızı
        duration = librosa.get_duration(y=y, sr=sr)
        
        # Voiced segment sayısı ve toplam süresi
        try:
            if pitch is not None:
                pitch_times = pitch.ts()
                total_frames = len(pitch.selected_array['frequency'])
            else:
                pitch_times = []
                total_frames = 0
        except Exception:
            pitch_times = []
            total_frames = 0
        
        voiced_frames = len(pitch_values)
        
        # Voiced ratio (sesli segment oranı)
        voiced_ratio = voiced_frames / total_frames if total_frames > 0 else 0.0
        
        # Pitch değişim hızı (pitch contour'un değişim sayısı)
        if len(pitch_values) > 1:
            pitch_changes = np.sum(np.abs(np.diff(pitch_values)) > 10)  # 10 Hz'den fazla değişim
            speech_rate_audio = pitch_changes / duration if duration > 0 else 0.0
        else:
            speech_rate_audio = 0.0
        
        # Pause Analysis - Enerji tabanlı duraklama tespiti
        rms = librosa.feature.rms(y=y)[0]
        
        # Threshold: RMS'in ortalamasının altında kalan bölgeler
        rms_mean = np.mean(rms)
        rms_std = np.std(rms)
        rms_threshold = rms_mean - 0.5 * rms_std  # Ortalamanın altında
        
        pause_segments = []
        in_pause = False
        pause_start = 0
        
        # Frame süresini hesapla
        hop_length = len(y) // len(rms)
        frame_duration = hop_length / sr
        
        for i, energy in enumerate(rms):
            if energy < rms_threshold and not in_pause:
                # Duraklama başladı
                in_pause = True
                pause_start = i * frame_duration
            elif energy >= rms_threshold and in_pause:
                # Duraklama bitti
                in_pause = False
                pause_duration = (i * frame_duration) - pause_start
                if pause_duration > 0.1:  # 100ms'den uzun duraklamalar
                    pause_segments.append(pause_duration)
        
        # Son duraklamayı kontrol et (ses dosyasının sonunda duraklama varsa)
        if in_pause:
            pause_duration = duration - pause_start
            if pause_duration > 0.1:
                pause_segments.append(pause_duration)
        
        total_pause_time = sum(pause_segments)
        pause_count = len(pause_segments)
        avg_pause_duration = np.mean(pause_segments) if pause_segments else 0.0
        
        # Voice Onset Time (VOT) - İlk sesli segmentin başlangıcı
        vot = 0.0
        try:
            # RMS kullanarak ilk sesli bölümü bul
            if len(rms) > 0:
                rms_threshold_vot = np.percentile(rms, 25)  # Alt %25'in üstü
                
                # İlk sesli bölümü bul (threshold'u geçen ilk nokta)
                for i, energy in enumerate(rms):
                    if energy > rms_threshold_vot:
                        # Bu noktadan önceki sessizlik süresini hesapla
                        vot = i * frame_duration
                        break
                
                # Alternatif: Pitch'in başladığı nokta
                if len(pitch_values) > 0 and pitch is not None:
                    try:
                        pitch_times = pitch.ts()
                        if len(pitch_times) > 0:
                            first_voiced_time = pitch_times[0]
                            vot = min(vot, float(first_voiced_time)) if vot > 0 else float(first_voiced_time)
                    except:
                        pass
        except:
            vot = 0.0
        
        return {
            "jitter": {
                "local": float(jitter_local),
                "rap": float(jitter_rap),
                "ppq5": float(jitter_ppq5)
            },
            "shimmer": {
                "local": float(shimmer_local),
                "apq3": float(shimmer_apq3),
                "apq5": float(shimmer_apq5)
            },
            "hnr": float(hnr),
            "formants": formants,
            "speech_rate_audio": float(speech_rate_audio),
            "voiced_ratio": float(voiced_ratio),
            "pause_analysis": {
                "total_pause_time": float(total_pause_time),
                "pause_count": pause_count,
                "avg_pause_duration": float(avg_pause_duration),
                "pause_percentage": float((total_pause_time / duration * 100) if duration > 0 else 0.0)
            },
            "voice_onset_time": float(vot)
        }


advanced_audio_service = AdvancedAudioService()

