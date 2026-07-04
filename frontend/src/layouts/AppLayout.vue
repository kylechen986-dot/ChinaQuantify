<template>
  <el-container class="app-shell">
    <el-aside width="236px" class="sidebar">
      <div class="brand">
        <div class="brand-mark">CQ</div>
        <div>
          <div class="brand-title">ChinaQuantify</div>
          <div class="brand-subtitle">国内 ETF AI 量化研究</div>
        </div>
      </div>

      <el-menu :default-active="route.path" router class="nav-menu">
        <el-menu-item index="/dashboard">
          <el-icon><DataBoard /></el-icon>
          <span>总览</span>
        </el-menu-item>
        <el-menu-item index="/market">
          <el-icon><TrendCharts /></el-icon>
          <span>国内 ETF 行情</span>
        </el-menu-item>
        <el-menu-item index="/stocks">
          <el-icon><Star /></el-icon>
          <span>关注股票</span>
        </el-menu-item>
        <el-menu-item index="/strategy">
          <el-icon><Operation /></el-icon>
          <span>策略与信号</span>
        </el-menu-item>
        <el-menu-item index="/backtest">
          <el-icon><Histogram /></el-icon>
          <span>回测结果</span>
        </el-menu-item>
        <el-menu-item index="/report">
          <el-icon><Document /></el-icon>
          <span>AI 日报</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="topbar">
        <div>
          <div class="page-title">{{ title }}</div>
          <div class="page-subtitle">MVP 阶段：研究辅助，不自动下单</div>
        </div>
        <el-tag type="success" effect="plain">Local MVP</el-tag>
      </el-header>
      <el-main class="content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const title = computed(() => String(route.meta.title ?? 'ChinaQuantify'))
</script>
