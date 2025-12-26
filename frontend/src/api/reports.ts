import client from './client'

export interface Statistics {
  total_participants: number
  group_counts: {
    alzheimer: number
    mci: number
    control: number
  }
  total_analyses: number
  average_mmse_scores: {
    alzheimer: number | null
    mci: number | null
    control: number | null
  }
}

export const getStatistics = async (): Promise<Statistics> => {
  const response = await client.get('/api/reports/statistics')
  return response.data
}

export const downloadReportPdf = async (analysisId: number): Promise<Blob> => {
  const response = await client.get(
    `/api/reports/pdf/${analysisId}`,
    { responseType: 'blob' }
  )
  return response.data
}

