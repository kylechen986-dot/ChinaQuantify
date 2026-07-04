<template>
  <el-card shadow="never">
    <template #header>系统设置</template>
    <el-form label-width="140px" class="settings-form">
      <el-form-item label="数据源">
        <el-select model-value="AKSHARE">
          <el-option label="AkShare" value="AKSHARE" />
          <el-option label="Tushare（后续）" value="TUSHARE" disabled />
        </el-select>
      </el-form-item>
      <el-form-item label="AI Provider">
        <el-select model-value="OPENAI">
          <el-option label="OpenAI" value="OPENAI" />
          <el-option label="Gemini（后续）" value="GEMINI" disabled />
        </el-select>
      </el-form-item>
      <el-form-item label="任务调度">
        <el-switch model-value inactive-text="MVP 暂未启用自动调度" />
      </el-form-item>
      <el-form-item label="说明">
        <el-text>
          第一版配置以环境变量为准，页面先作为配置可视化入口。敏感 Key 不在前端展示完整值。
        </el-text>
      </el-form-item>
    </el-form>
  </el-card>
</template>
