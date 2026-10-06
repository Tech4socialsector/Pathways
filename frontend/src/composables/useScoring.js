import { ref } from 'vue'
import { scoringService } from '@/services/scoring'

export function useApplicationReview() {
  const review = ref(null)
  const rubric = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function fetchReview(application) {
    loading.value = true
    error.value = null
    try {
      review.value = await scoringService.getApplicationForReview(application)
      if (review.value?.track) {
        rubric.value = await scoringService.getRubricForJobOpening(review.value.job_opening, 'Shortlisting')
      }
    } catch (e) {
      error.value = e
    } finally {
      loading.value = false
    }
  }

  return { review, rubric, loading, error, fetchReview }
}
