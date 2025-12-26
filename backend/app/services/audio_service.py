import librosa
import numpy as np
from typing import Dict


class AudioService:
    @staticmethod
    def extract_features(audio_path: str) -> Dict:
        """librosa ile ses dosyasından akustik özellikler çıkar (optimize edilmiş)"""
        # Sabit sample rate ile yükle (hız optimizasyonu)
        TARGET_SR = 22050
        y, sr = librosa.load(audio_path, sr=TARGET_SR, mono=True)
        
        # Temel özellikler
        duration = librosa.get_duration(y=y, sr=sr)
        print(f"[Audio] Yuklendi: {duration:.1f}s, {len(y)} sample", flush=True)
        
        # Enerji (RMS)
        rms = librosa.feature.rms(y=y)[0]
        mean_energy = float(np.mean(rms))
        max_energy = float(np.max(rms))
        
        # Temel frekans (pitch) - pyin daha hızlı ve doğru
        try:
            # pyin kullan - daha hızlı
            f0, voiced_flag, voiced_probs = librosa.pyin(
                y, 
                fmin=librosa.note_to_hz('C2'), 
                fmax=librosa.note_to_hz('C7'),
                sr=sr,
                frame_length=2048
            )
            pitch_values = f0[~np.isnan(f0)] if f0 is not None else np.array([])
            mean_pitch = float(np.mean(pitch_values)) if len(pitch_values) > 0 else 0.0
            std_pitch = float(np.std(pitch_values)) if len(pitch_values) > 0 else 0.0
        except Exception as e:
            print(f"[Audio] Pitch analizi hatası: {e}", flush=True)
            mean_pitch = 0.0
            std_pitch = 0.0
        
        # MFCC (Mel-frequency cepstral coefficients)
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_mean = [float(x) for x in np.mean(mfccs, axis=1)]
        mfcc_std = [float(x) for x in np.std(mfccs, axis=1)]
        
        # Spektral özellikler
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        mean_spectral_centroid = float(np.mean(spectral_centroids))
        
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        mean_spectral_rolloff = float(np.mean(spectral_rolloff))
        
        zero_crossing_rate = librosa.feature.zero_crossing_rate(y)[0]
        mean_zcr = float(np.mean(zero_crossing_rate))
        
        # Tempo (BPM) - uzun dosyalarda yavaş olabilir, opsiyonel
        try:
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            tempo = float(tempo) if tempo else 0.0
        except Exception:
            tempo = 0.0
        
        return {
            "duration": duration,
            "sample_rate": int(sr),
            "energy": {
                "mean": mean_energy,
                "max": max_energy
            },
            "pitch": {
                "mean": mean_pitch,
                "std": std_pitch
            },
            "mfcc": {
                "mean": mfcc_mean,
                "std": mfcc_std
            },
            "spectral": {
                "centroid": mean_spectral_centroid,
                "rolloff": mean_spectral_rolloff,
                "zero_crossing_rate": mean_zcr
            },
            "tempo": tempo
        }


audio_service = AudioService()

