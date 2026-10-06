import { callMethod } from './api'

export const scoringService = {
  getApplicationForReview(application) {
    return callMethod('pathways.api.scoring.get_application_for_review', { application })
  },
  getRubricForJobOpening(jobOpening, stage) {
    return callMethod('pathways.api.scoring.get_rubric_for_job_opening', { job_opening: jobOpening, stage })
  },
  submitShortlistingScore(data) {
    return callMethod('pathways.api.scoring.submit_shortlisting_score', data)
  },
  submitInterviewAssessment(data) {
    return callMethod('pathways.api.scoring.submit_interview_assessment', data)
  },
  consolidateScores(interview) {
    return callMethod('pathways.api.scoring.consolidate_scores', { interview })
  },
}
