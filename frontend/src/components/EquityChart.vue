<template>
  <div ref="chartRef" class="chart"></div>
</template>

<script setup lang="ts">
import * as echarts from 'echarts'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps<{
  data: Array<{ date: string; equity: number }>
}>()

const chartRef = ref<HTMLDivElement>()
let chart: echarts.ECharts | undefined

function renderChart() {
  if (!chartRef.value) return
  chart ??= echarts.init(chartRef.value)
  chart.setOption({
    grid: { left: 44, right: 24, top: 24, bottom: 36 },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: props.data.map((item) => item.date), boundaryGap: false },
    yAxis: { type: 'value', scale: true },
    series: [
      {
        name: '净值',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        data: props.data.map((item) => item.equity),
        lineStyle: { color: '#1f7aec', width: 3 },
        areaStyle: { color: 'rgba(31, 122, 236, 0.12)' },
      },
    ],
  })
}

onMounted(() => {
  renderChart()
  window.addEventListener('resize', renderChart)
})

watch(() => props.data, renderChart, { deep: true })

onBeforeUnmount(() => {
  window.removeEventListener('resize', renderChart)
  chart?.dispose()
})
</script>
