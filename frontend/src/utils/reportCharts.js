// Reports page charts: ECharts setup, the option for each chart kind and
// the PNG / CSV downloads. Data, colours and the table behind each chart
// come from the API (pathways.api.reports), so the page, the CSV and the
// Excel export always match.
//
// Kinds: pie, donut (part-to-whole) · bar (ranked) · funnel (stages
// reached) · column (ordered bins) · stacked (groups by stage) · line (time).
import * as echarts from 'echarts/core'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import { GraphicComponent, GridComponent, LegendComponent, TitleComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { saveBlob } from '@/services/api'

echarts.use([PieChart, BarChart, LineChart, GraphicComponent, GridComponent, LegendComponent, TitleComponent, TooltipComponent, CanvasRenderer])

export { echarts }

// Chart ink: text never takes a series colour.
const INK = { primary: '#111827', secondary: '#52514e', muted: '#898781', grid: '#e1e0d9', baseline: '#c3c2b7', surface: '#ffffff' }
// The PNG: title block on top, chart below.
const EXPORT = { pad: 40, titleHeight: 96 }

function fontFamily() {
  return getComputedStyle(document.body).fontFamily || 'sans-serif'
}

function escapeHtml(text) {
  return String(text ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c])
}

export function percent(value, total) {
  if (!total || !value) return '0'
  const pct = (value * 100) / total
  return pct < 1 ? '<1' : String(Math.round(pct))
}

function plural(n) {
  return `${n} application${n === 1 ? '' : 's'}`
}

function tooltipBase(font) {
  return {
    confine: true,
    backgroundColor: '#ffffff',
    borderColor: INK.grid,
    textStyle: { color: INK.primary, fontFamily: font, fontSize: 12 },
    extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,.08); border-radius: 8px;',
  }
}

function tooltipHtml(title, lines) {
  return [`<div style="font-weight:600;margin-bottom:2px">${escapeHtml(title)}</div>`, ...lines].join('<br>')
}

function sliceTooltip(chart, slice) {
  const share = chart.kind === 'funnel' ? `${percent(slice.value, chart.total)}% of applied` : `${percent(slice.value, chart.total)}%`
  const lines = [`${plural(slice.value)} · ${share}`]
  if (slice.track) lines.push(`<span style="color:${INK.secondary}">Track: ${escapeHtml(slice.track)}</span>`)
  for (const d of slice.detail || []) lines.push(`<span style="color:${INK.secondary}">${escapeHtml(d.label)}: ${d.value}</span>`)
  return tooltipHtml(slice.label, lines)
}

function axisLabel(font, extra = {}) {
  return { color: INK.secondary, fontFamily: font, ...extra }
}

const valueAxis = (font) => ({
  type: 'value',
  minInterval: 1,
  axisLabel: { color: INK.muted, fontFamily: font },
  splitLine: { lineStyle: { color: INK.grid } },
})

const shadowPointer = { type: 'shadow', shadowStyle: { color: 'rgba(0,0,0,0.04)' } }

const LABEL_SIZE = 12
let measureCtx = null

/**
 * Category labels for a horizontal axis, cut with an ellipsis to fit
 * `maxWidth` px, and the width the widest one needs. Measured here rather
 * than with ECharts' axisLabel.width/overflow, which mis-placed them.
 */
function fitLabels(labels, font, maxWidth) {
  measureCtx = measureCtx || document.createElement('canvas').getContext('2d')
  measureCtx.font = `${LABEL_SIZE}px ${font}`
  const measure = (text) => measureCtx.measureText(text).width
  let widest = 0
  const fitted = labels.map((label) => {
    let text = String(label ?? '')
    if (measure(text) > maxWidth) {
      while (text.length > 1 && measure(`${text}…`) > maxWidth) text = text.slice(0, -1)
      text = `${text.trimEnd()}…`
    }
    widest = Math.max(widest, measure(text))
    return text
  })
  return { fitted, width: Math.ceil(widest) }
}

// The fitted labels go straight into the axis data (tooltips read the full
// label by dataIndex); interval 0 so no row ever loses its label.
function categoryLabels(labels, font, maxWidth) {
  const { fitted, width } = fitLabels(labels, font, maxWidth)
  return { data: fitted, axisLabel: axisLabel(font, { fontSize: LABEL_SIZE, margin: 10, interval: 0 }), width }
}

// ---------------------------------------------------------------- kinds

function pie(chart, { font, forExport }) {
  const donut = chart.kind === 'donut'
  const size = forExport ? 340 : 280
  const centerY = forExport ? EXPORT.titleHeight + size / 2 + 10 : size / 2
  const option = {
    tooltip: { ...tooltipBase(font), trigger: 'item', formatter: (p) => sliceTooltip(chart, p.data.slice) },
    series: [
      {
        type: 'pie',
        radius: donut ? (forExport ? [84, 140] : ['44%', '68%']) : forExport ? 140 : '68%',
        center: ['50%', centerY],
        avoidLabelOverlap: true,
        stillShowZeroSum: false,
        // 2px surface gap between slices.
        itemStyle: { borderColor: INK.surface, borderWidth: 2 },
        label: { formatter: '{c}', color: INK.secondary, fontSize: forExport ? 14 : 12, fontFamily: font },
        labelLine: { length: 10, length2: 8, lineStyle: { color: INK.baseline } },
        emphasis: { scaleSize: 4, label: { fontWeight: 'bold', color: INK.primary } },
        data: chart.slices.map((s) => ({
          name: s.label,
          value: s.value,
          slice: s,
          itemStyle: { color: s.color, ...(s.value ? {} : { borderWidth: 0 }) },
          ...(s.value ? {} : { label: { show: false }, labelLine: { show: false } }),
        })),
      },
    ],
  }
  if (donut) {
    // The total in the hole.
    option.graphic = [
      {
        type: 'text',
        left: 'center',
        top: centerY - (forExport ? 26 : 20),
        silent: true,
        style: {
          text: `{v|${chart.total}}\n{l|applications}`,
          align: 'center',
          rich: {
            v: { fontSize: forExport ? 30 : 22, fontWeight: 'bold', fill: INK.primary, fontFamily: font, lineHeight: forExport ? 36 : 28 },
            l: { fontSize: forExport ? 14 : 11, fill: INK.muted, fontFamily: font },
          },
        },
      },
    ]
  }
  return { option, height: forExport ? EXPORT.titleHeight + size + 20 : size }
}

function bar(chart, { font, forExport, width }) {
  const funnel = chart.kind === 'funnel'
  // Labels get a fixed column (containLabel clipped long titles on wide screens).
  const labels = categoryLabels(
    chart.slices.map((s) => s.label),
    font,
    Math.min(420, Math.max(80, width * (funnel ? 0.25 : 0.4))),
  )
  const top = forExport ? EXPORT.titleHeight : 4
  const option = {
    tooltip: {
      ...tooltipBase(font),
      trigger: 'axis',
      axisPointer: shadowPointer,
      formatter: (params) => sliceTooltip(chart, chart.slices[params[0].dataIndex]),
    },
    grid: { left: labels.width + 14 + (forExport ? EXPORT.pad : 0), right: funnel ? 110 : 48, top, bottom: 28 },
    xAxis: { ...valueAxis(font), ...(funnel ? { max: chart.total || 1, axisLabel: { show: false }, splitLine: { show: false } } : {}) },
    yAxis: {
      type: 'category',
      inverse: true,
      data: labels.data,
      axisTick: { show: false },
      axisLine: { lineStyle: { color: INK.baseline } },
      axisLabel: labels.axisLabel,
    },
    series: [
      {
        type: 'bar',
        barMaxWidth: funnel ? 30 : 18,
        // Rounded data end, square at the baseline.
        data: chart.slices.map((s) => ({ value: s.value, itemStyle: { color: s.color, borderRadius: [0, 4, 4, 0] } })),
        label: {
          show: true,
          position: 'right',
          color: INK.secondary,
          fontFamily: font,
          formatter: funnel ? (p) => `${p.value}  ·  ${percent(p.value, chart.total)}%` : '{c}',
        },
        emphasis: { disabled: true },
      },
    ],
  }
  const row = funnel ? 46 : 32
  return { option, height: top + chart.slices.length * row + 36 }
}

function column(chart, { font, forExport }) {
  // Room above the tallest bar for its value label.
  const top = forExport ? EXPORT.titleHeight + 16 : 28
  const option = {
    tooltip: {
      ...tooltipBase(font),
      trigger: 'axis',
      axisPointer: shadowPointer,
      formatter: (params) => sliceTooltip(chart, chart.slices[params[0].dataIndex]),
    },
    grid: { left: forExport ? EXPORT.pad + 8 : 8, right: forExport ? EXPORT.pad : 8, top, bottom: 8, containLabel: true },
    xAxis: {
      type: 'category',
      data: chart.slices.map((s) => s.label),
      axisTick: { show: false },
      axisLine: { lineStyle: { color: INK.baseline } },
      axisLabel: axisLabel(font, { interval: 0, hideOverlap: true }),
    },
    yAxis: valueAxis(font),
    series: [
      {
        type: 'bar',
        barMaxWidth: 44,
        data: chart.slices.map((s) => ({ value: s.value, itemStyle: { color: s.color, borderRadius: [4, 4, 0, 0] } })),
        label: { show: true, position: 'top', color: INK.secondary, fontFamily: font },
        emphasis: { disabled: true },
      },
    ],
  }
  return { option, height: forExport ? EXPORT.titleHeight + 320 : 300 }
}

function stacked(chart, { font, forExport, width }) {
  const labels = categoryLabels(chart.categories, font, Math.min(forExport ? 260 : 180, Math.max(70, width * 0.3)))
  const totals = chart.categories.map((_c, i) => chart.series.reduce((sum, s) => sum + s.values[i], 0))
  const top = forExport ? EXPORT.titleHeight : 4
  const option = {
    tooltip: {
      ...tooltipBase(font),
      trigger: 'axis',
      axisPointer: shadowPointer,
      formatter: (params) => {
        const i = params[0].dataIndex
        const lines = [plural(totals[i])]
        for (const s of chart.series) {
          if (!s.values[i]) continue
          const dot = `<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${s.color};margin-right:6px"></span>`
          lines.push(`${dot}${escapeHtml(s.label)}: ${s.values[i]}`)
        }
        return tooltipHtml(chart.categories[i], lines)
      },
    },
    grid: { left: labels.width + 14 + (forExport ? EXPORT.pad : 0), right: 48, top, bottom: forExport ? 70 : 28 },
    xAxis: valueAxis(font),
    yAxis: {
      type: 'category',
      inverse: true,
      data: labels.data,
      axisTick: { show: false },
      axisLine: { lineStyle: { color: INK.baseline } },
      axisLabel: labels.axisLabel,
    },
    series: [
      ...chart.series.map((s) => ({
        name: s.label,
        type: 'bar',
        stack: 'total',
        barMaxWidth: 26,
        data: s.values,
        // 1px surface gap between segments.
        itemStyle: { color: s.color, borderColor: INK.surface, borderWidth: 1 },
        emphasis: { focus: 'series' },
      })),
      {
        // Invisible cap that carries the row total at the end of the stack.
        name: '__total',
        type: 'bar',
        stack: 'total',
        data: totals.map(() => 0),
        label: { show: true, position: 'right', color: INK.secondary, fontFamily: font, formatter: (p) => totals[p.dataIndex] },
        silent: true,
      },
    ],
  }
  if (forExport) option.legend = exportLegend(chart.series.map((s) => s.label), font, { bottom: 20 })
  return { option, height: top + chart.categories.length * 48 + (forExport ? 90 : 36) }
}

function rgba(hex, alpha) {
  const n = parseInt(String(hex).replace('#', ''), 16)
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${alpha})`
}

function line(chart, { font, forExport }) {
  // The brand colour (Pathways Settings), sent with the chart.
  const color = chart.color || '#920c24'
  const top = forExport ? EXPORT.titleHeight : 16
  const option = {
    tooltip: {
      ...tooltipBase(font),
      trigger: 'axis',
      axisPointer: { type: 'line', lineStyle: { color: INK.baseline } },
      formatter: (params) => {
        const p = chart.points[params[0].dataIndex]
        return tooltipHtml((chart.unit === 'week' ? 'Week of ' : '') + p.label, [plural(p.value)])
      },
    },
    // Right padding: the last x label is centred on the plot's edge.
    grid: { left: forExport ? EXPORT.pad + 8 : 8, right: forExport ? EXPORT.pad + 24 : 36, top, bottom: 8, containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: chart.points.map((p) => p.label),
      axisTick: { show: false },
      axisLine: { lineStyle: { color: INK.baseline } },
      axisLabel: axisLabel(font, { hideOverlap: true }),
    },
    yAxis: valueAxis(font),
    series: [
      {
        type: 'line',
        data: chart.points.map((p) => p.value),
        lineStyle: { width: 2, color },
        itemStyle: { color, borderColor: INK.surface, borderWidth: 2 },
        // Markers only for short series; the crosshair covers the rest.
        showSymbol: chart.points.length <= 31,
        symbolSize: 8,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: rgba(color, 0.2) },
            { offset: 1, color: rgba(color, 0.02) },
          ]),
        },
      },
    ],
  }
  return { option, height: forExport ? EXPORT.titleHeight + 320 : 260 }
}

const BUILDERS = { pie, donut: pie, bar, funnel: bar, column, stacked, line }

/**
 * { option, height, width? } for a chart. `width` is the drawing width on
 * screen (axis labels size to it); `forExport` lays out the PNG: title on
 * top and, for pies, a legend with counts below.
 */
export function chartOption(chart, { forExport = false, width = 600 } = {}) {
  const font = fontFamily()
  const exportWidth = ['bar', 'stacked', 'line'].includes(chart.kind) ? 1200 : 960
  const built = BUILDERS[chart.kind](chart, { font, forExport, width: forExport ? exportWidth : width })
  built.option.animationDuration = forExport ? 0 : 400
  built.option.textStyle = { fontFamily: font }
  if (!forExport) return built

  built.option.title = {
    text: chart.title,
    subtext: chart.subtitle,
    left: EXPORT.pad,
    top: 24,
    textStyle: { color: INK.primary, fontSize: 22, fontWeight: 'bold', fontFamily: font },
    subtextStyle: { color: INK.secondary, fontSize: 14, fontFamily: font },
  }
  if (chart.kind === 'pie' || chart.kind === 'donut') {
    const legendTop = built.height + 10
    built.option.legend = exportLegend(
      chart.slices.map((s) => s.label),
      font,
      { top: legendTop },
      (name) => {
        const s = chart.slices.find((x) => x.label === name)
        return `${s.value} (${percent(s.value, chart.total)}%)`
      },
    )
    built.height = legendTop + legendRows(chart.slices, exportWidth - 2 * EXPORT.pad) * 30 + 30
  }
  return { ...built, width: exportWidth }
}

function exportLegend(names, font, position, valueFor) {
  return {
    ...position,
    left: EXPORT.pad,
    right: EXPORT.pad,
    data: names,
    selectedMode: false,
    icon: 'circle',
    itemWidth: 12,
    itemHeight: 12,
    itemGap: 22,
    formatter: (name) => {
      // Braces would read as rich-text markup.
      const safe = name.replace(/[{}|]/g, ' ')
      return valueFor ? `{n|${safe}}  {v|${valueFor(name)}}` : `{n|${safe}}`
    },
    textStyle: {
      fontFamily: font,
      rich: { n: { color: INK.primary, fontSize: 14, fontFamily: font }, v: { color: INK.muted, fontSize: 14, fontFamily: font } },
    },
  }
}

// Rough legend height for the PNG: items laid out left to right in `width`.
function legendRows(slices, width) {
  let rows = 1
  let used = 0
  for (const s of slices) {
    const item = (s.label.length + String(s.value).length + 8) * 7.2 + 34
    if (used && used + item > width) {
      rows += 1
      used = 0
    }
    used += item
  }
  return rows
}

/** Legend entries shown under a chart on the page ([] when the axis labels say it all). */
export function legendItems(chart) {
  if (chart.kind === 'pie' || chart.kind === 'donut') {
    return chart.slices.map((s) => ({ label: s.label, color: s.color, value: s.value, share: `${percent(s.value, chart.total)}%` }))
  }
  if (chart.kind === 'stacked') {
    return chart.series.map((s) => {
      const value = s.values.reduce((a, b) => a + b, 0)
      return { label: s.label, color: s.color, value, share: `${percent(value, chart.total)}%` }
    })
  }
  return []
}

function fileStem(chart) {
  const slug = chart.title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
  return `${slug || 'chart'}-${new Date().toISOString().slice(0, 10)}`
}

/** The chart with its title (and legend) as a PNG, drawn off-screen. */
export function downloadChartPng(chart) {
  const { option, height, width } = chartOption(chart, { forExport: true })
  const el = document.createElement('div')
  el.style.cssText = `position:fixed;left:-20000px;top:0;width:${width}px;height:${height}px;`
  document.body.appendChild(el)
  const instance = echarts.init(el, null, { renderer: 'canvas', width, height })
  try {
    instance.setOption({ ...option, animation: false, backgroundColor: INK.surface })
    saveBlob(instance.getDataURL({ type: 'png', pixelRatio: 2, backgroundColor: INK.surface }), `${fileStem(chart)}.png`)
  } finally {
    instance.dispose()
    el.remove()
  }
}

/** The chart's table as a CSV (shares as percentages). */
export function downloadChartCsv(chart) {
  // A leading = + - @ would run as a formula in Excel.
  const cell = (value) => {
    const text = String(value ?? '')
    return `"${(/^[=+\-@]/.test(text) ? `'${text}` : text).replace(/"/g, '""')}"`
  }
  const { header, rows, percent: pctCols } = chart.table
  const lines = [
    header.map(cell).join(','),
    ...rows.map((row) => row.map((v, i) => cell(pctCols.includes(i) ? (v * 100).toFixed(1) : v)).join(',')),
  ]
  saveBlob(new Blob(['﻿' + lines.join('\r\n')], { type: 'text/csv;charset=utf-8' }), `${fileStem(chart)}.csv`)
}
