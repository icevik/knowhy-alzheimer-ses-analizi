import client from './client'

export interface AnalysisResult {
  id: number
  participant_id: number
  transcript: string
  acoustic_features: {
    duration: number
    energy: { mean: number; max: number }
    pitch: { mean: number; std: number }
    mfcc: { mean: number[]; std: number[] }
    spectral: {
      centroid: number
      rolloff: number
      zero_crossing_rate: number
    }
    tempo: number
  }
  advanced_acoustic?: {
    jitter: { local: number; rap: number; ppq5: number }
    shimmer: { local: number; apq3: number; apq5: number }
    hnr: number
    formants: { F1: number; F2: number; F3: number; F4: number }
    speech_rate_audio: number
    pause_analysis: {
      total_pause_time: number
      pause_count: number
      avg_pause_duration: number
      pause_percentage: number
    }
    voice_onset_time: number
  }
  linguistic_analysis?: {
    word_count: number
    unique_word_count: number
    type_token_ratio: number
    diversity_score: number
    mean_length_utterance: number
    sentence_count: number
    avg_sentence_length: number
    hesitation_markers: string[]
    hesitation_count: number
    hesitation_ratio: number
    repetitions: Array<{ word: string; count: number; position: number }>
    repetition_count: number
    repetition_ratio: number
    conjunction_count: number
    conjunction_ratio: number
    syntactic_complexity: string
  }
  emotion_analysis: {
    tone: string
    intensity: number
    emotions: string[]
  }
  content_analysis: {
    word_count: number
    unique_words: number
    fluency_score: number
    coherence_score: number
  }
  gemini_report?: string
  report_pdf_path?: string
  created_at: string
}

export const analyzeAudio = async (
  participantId: number,
  file: File
): Promise<AnalysisResult> => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('participant_id', participantId.toString())
  
  const response = await client.post(
    '/api/analyze/',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 300000, // 5 dakika timeout (analiz uzun sürebilir)
    }
  )
  return response.data
}

export const getAnalysisResult = async (
  analysisId: number
): Promise<AnalysisResult> => {
  const response = await client.get(`/api/results/${analysisId}`)
  return response.data
}

export interface AnalysisListItem {
  id: number
  participant_id: number
  transcript: string
  emotion_analysis: {
    tone: string
    intensity: number
    emotions: string[]
  }
  content_analysis: {
    word_count: number
    unique_words: number
    fluency_score: number
    coherence_score: number
  }
  has_gemini_report?: boolean
  has_pdf?: boolean
  created_at: string
}

export interface AnalysesListResponse {
  total: number
  items: AnalysisListItem[]
}

export const getAllAnalyses = async (
  limit: number = 100,
  offset: number = 0
): Promise<AnalysesListResponse> => {
  const response = await client.get(`/api/results/?limit=${limit}&offset=${offset}`)
  return response.data
}

export const deleteAnalysis = async (analysisId: number): Promise<void> => {
  await client.delete(`/api/results/${analysisId}`)
}

