// The Selection module's steps, in order (pathways.api.selection.STEPS).
export const STEPS = [
  { key: 'scores', label: 'Scores & decision', icon: 'bar-chart-2' },
  { key: 'regrets', label: 'Regrets & thanks', icon: 'mail' },
  { key: 'green_sheet', label: 'Selection green sheet', icon: 'file-text' },
  { key: 'offers', label: 'Offers', icon: 'award' },
]

export const STEP_LABEL = Object.fromEntries(STEPS.map((s) => [s.key, s.label]))
