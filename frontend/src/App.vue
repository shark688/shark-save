<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import {
  AlertCircle,
  ArrowDownToLine,
  CheckCircle2,
  Clipboard,
  Crown,
  Gauge,
  Loader2,
  LockKeyhole,
  Play,
  ShieldCheck,
  Sparkles,
  Wand2,
  Zap,
} from 'lucide-vue-next'
import { analyzeVideo, createDownloadJob, getJob } from './api'

const url = ref('')
const video = ref(null)
const selectedFormatId = ref('')
const analyzing = ref(false)
const starting = ref(false)
const error = ref('')
const notice = ref('')
const job = ref(null)
let pollTimer = null

const selectedFormat = computed(() => {
  if (!video.value) return null
  return video.value.formats.find((item) => item.id === selectedFormatId.value) || null
})

const jobRunning = computed(() => job.value?.status === 'queued' || job.value?.status === 'downloading')
const canStart = computed(() => Boolean(video.value && selectedFormatId.value && !starting.value && !jobRunning.value))

function resetJob() {
  job.value = null
  if (pollTimer) {
    window.clearInterval(pollTimer)
    pollTimer = null
  }
}

function normalizeError(message) {
  return message || '操作失败，请稍后重试。'
}

async function pasteFromClipboard() {
  error.value = ''
  notice.value = ''
  try {
    const text = await navigator.clipboard.readText()
    url.value = text.trim()
    notice.value = '已粘贴链接，可以开始解析。'
  } catch {
    error.value = '浏览器没有授权读取剪贴板，请手动粘贴链接。'
  }
}

async function analyze() {
  error.value = ''
  notice.value = ''
  resetJob()
  if (!url.value.trim()) {
    error.value = '请先粘贴一个公开视频链接。'
    return
  }
  analyzing.value = true
  video.value = null
  selectedFormatId.value = ''
  try {
    const result = await analyzeVideo(url.value.trim())
    video.value = result
    selectedFormatId.value = result.formats?.[0]?.id || ''
    notice.value = result.warning || '解析完成，选择清晰度后即可下载。'
  } catch (err) {
    error.value = normalizeError(err.message)
  } finally {
    analyzing.value = false
  }
}

async function startDownload() {
  if (!canStart.value) return
  error.value = ''
  notice.value = ''
  starting.value = true
  try {
    job.value = await createDownloadJob(url.value.trim(), selectedFormatId.value, selectedFormat.value?.label)
    await pollJob()
    if (!pollTimer && jobRunning.value) {
      pollTimer = window.setInterval(pollJob, 1000)
    }
  } catch (err) {
    error.value = normalizeError(err.message)
  } finally {
    starting.value = false
  }
}

async function pollJob() {
  if (!job.value) return
  try {
    job.value = await getJob(job.value.id)
    if (job.value.status === 'completed') {
      notice.value = '下载完成，文件已准备好。'
      if (pollTimer) {
        window.clearInterval(pollTimer)
        pollTimer = null
      }
      return
    }
    if (job.value.status === 'failed') {
      error.value = job.value.error || '下载失败，请换一个链接或格式重试。'
      if (pollTimer) {
        window.clearInterval(pollTimer)
        pollTimer = null
      }
      return
    }
  } catch (err) {
    error.value = normalizeError(err.message)
    if (pollTimer) {
      window.clearInterval(pollTimer)
      pollTimer = null
    }
  }
}

function downloadFile() {
  if (!job.value?.download_url) return
  window.location.href = job.value.download_url
}

function formatDuration(seconds) {
  if (!seconds) return '未知时长'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${String(secs).padStart(2, '0')}`
}

function formatBytes(bytes) {
  if (!bytes) return '大小未知'
  const units = ['B', 'KB', 'MB', 'GB']
  let value = bytes
  let index = 0
  while (value >= 1024 && index < units.length - 1) {
    value /= 1024
    index += 1
  }
  return `${value.toFixed(value >= 10 ? 0 : 1)} ${units[index]}`
}

function formatSpeed(bytes) {
  if (!bytes) return ''
  return `${formatBytes(bytes)}/s`
}

onBeforeUnmount(resetJob)
</script>

<template>
  <main class="relative min-h-screen overflow-hidden text-slate-50">
    <div class="subtle-grid pointer-events-none absolute inset-x-0 top-0 h-[460px] opacity-60"></div>

    <header class="relative z-10 mx-auto flex w-full max-w-7xl items-center justify-between px-5 py-5 sm:px-8">
      <div class="flex items-center gap-3">
        <div class="flex h-11 w-11 items-center justify-center rounded-lg bg-action text-white shadow-glow">
          <Play class="h-5 w-5 fill-current" aria-hidden="true" />
        </div>
        <div>
          <p class="text-lg font-black tracking-normal">SharkSave</p>
          <p class="text-xs font-medium text-slate-400">公开视频下载工作台</p>
        </div>
      </div>
      <div class="hidden items-center gap-3 text-sm text-slate-300 sm:flex">
        <span class="inline-flex items-center gap-2 rounded-full border border-white/10 px-3 py-2">
          <ShieldCheck class="h-4 w-4 text-signal" aria-hidden="true" />
          公开链接优先
        </span>
        <span class="inline-flex items-center gap-2 rounded-full border border-premium/30 px-3 py-2 text-premium">
          <Crown class="h-4 w-4" aria-hidden="true" />
          Pro 能力预留
        </span>
      </div>
    </header>

    <section class="relative z-10 mx-auto grid min-h-[calc(100vh-92px)] w-full max-w-7xl items-center gap-10 px-5 pb-12 pt-4 sm:px-8 lg:grid-cols-[1.02fr_0.98fr]">
      <div class="max-w-3xl">
        <div class="mb-5 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-slate-200">
          <Zap class="h-4 w-4 text-action" aria-hidden="true" />
          更快解析、选择清晰度、保存到本地
        </div>
        <h1 class="max-w-3xl text-4xl font-black leading-tight tracking-normal text-white sm:text-5xl lg:text-6xl">
          把公开视频链接变成本地文件。
        </h1>
        <p class="mt-5 max-w-2xl text-base leading-7 text-slate-300 sm:text-lg">
          面向手机和桌面使用的下载工作台。第一版专注公开链接下载闭环，后续可扩展批量下载、字幕翻译、视频总结和付费队列。
        </p>

        <div class="mt-8 grid gap-3 sm:grid-cols-3">
          <div class="rounded-lg border border-white/10 bg-white/[0.045] p-4">
            <Gauge class="mb-3 h-5 w-5 text-signal" aria-hidden="true" />
            <p class="text-sm font-bold text-white">格式可选</p>
            <p class="mt-1 text-sm text-slate-400">解析可用清晰度与封装格式</p>
          </div>
          <div class="rounded-lg border border-white/10 bg-white/[0.045] p-4">
            <LockKeyhole class="mb-3 h-5 w-5 text-premium" aria-hidden="true" />
            <p class="text-sm font-bold text-white">边界清晰</p>
            <p class="mt-1 text-sm text-slate-400">不绕过 DRM 或权限限制</p>
          </div>
          <div class="rounded-lg border border-white/10 bg-white/[0.045] p-4">
            <Wand2 class="mb-3 h-5 w-5 text-action" aria-hidden="true" />
            <p class="text-sm font-bold text-white">可扩展</p>
            <p class="mt-1 text-sm text-slate-400">为 AI 和付费能力预留入口</p>
          </div>
        </div>
      </div>

      <section class="glass-panel rounded-[1.5rem] p-4 sm:p-6" aria-labelledby="download-panel-title">
        <div class="mb-5 flex items-start justify-between gap-4">
          <div>
            <p class="text-sm font-bold uppercase tracking-[0.16em] text-action">Download Console</p>
            <h2 id="download-panel-title" class="mt-2 text-2xl font-black text-white">粘贴链接开始</h2>
          </div>
          <div class="rounded-lg border border-white/10 bg-white/5 p-3">
            <ArrowDownToLine class="h-5 w-5 text-signal" aria-hidden="true" />
          </div>
        </div>

        <div class="space-y-4">
          <label class="block">
            <span class="mb-2 block text-sm font-semibold text-slate-200">公开视频链接</span>
            <div class="flex flex-col gap-3 sm:flex-row">
              <input
                v-model="url"
                class="min-h-[52px] flex-1 rounded-lg border border-white/10 bg-black/30 px-4 text-base text-white outline-none transition-colors placeholder:text-slate-500 focus:border-action focus:ring-2 focus:ring-action/30"
                type="url"
                placeholder="https://..."
                autocomplete="off"
                @keydown.enter="analyze"
              />
              <button
                class="inline-flex min-h-[52px] items-center justify-center gap-2 rounded-lg border border-white/10 px-4 text-sm font-bold text-slate-100 transition-colors duration-200 hover:border-signal hover:bg-signal/10 focus:outline-none focus:ring-2 focus:ring-signal/40"
                type="button"
                @click="pasteFromClipboard"
              >
                <Clipboard class="h-4 w-4" aria-hidden="true" />
                粘贴
              </button>
            </div>
          </label>

          <button
            class="inline-flex min-h-[54px] w-full items-center justify-center gap-2 rounded-lg bg-action px-5 text-base font-black text-white shadow-glow transition-colors duration-200 hover:bg-rose-600 focus:outline-none focus:ring-2 focus:ring-action/50 disabled:cursor-not-allowed disabled:opacity-60"
            type="button"
            :disabled="analyzing"
            @click="analyze"
          >
            <Loader2 v-if="analyzing" class="h-5 w-5 animate-spin" aria-hidden="true" />
            <Sparkles v-else class="h-5 w-5" aria-hidden="true" />
            {{ analyzing ? '正在解析' : '立即解析' }}
          </button>

          <p v-if="error" class="rounded-lg border border-action/40 bg-action/10 px-4 py-3 text-sm leading-6 text-rose-100" role="alert">
            <AlertCircle class="mr-2 inline h-4 w-4 align-[-3px]" aria-hidden="true" />
            {{ error }}
          </p>
          <p v-if="notice && !error" class="rounded-lg border border-signal/30 bg-signal/10 px-4 py-3 text-sm leading-6 text-cyan-50" role="status">
            <CheckCircle2 class="mr-2 inline h-4 w-4 align-[-3px]" aria-hidden="true" />
            {{ notice }}
          </p>
        </div>

        <div v-if="video" class="mt-6 border-t border-white/10 pt-6">
          <div class="flex gap-4">
            <img
              v-if="video.thumbnail"
              class="h-24 w-36 rounded-lg object-cover"
              :src="video.thumbnail"
              :alt="`${video.title} 缩略图`"
            />
            <div class="min-w-0 flex-1">
              <p class="truncate text-lg font-black text-white">{{ video.title }}</p>
              <p class="mt-2 text-sm text-slate-400">
                {{ video.platform || '未知平台' }} · {{ formatDuration(video.duration) }}
              </p>
              <p class="mt-3 text-xs font-semibold text-slate-500">
                仅处理公开链接。请确认你拥有保存该内容的权利。
              </p>
            </div>
          </div>

          <label class="mt-5 block">
            <span class="mb-2 block text-sm font-semibold text-slate-200">选择清晰度</span>
            <select
              v-if="video.formats.length"
              v-model="selectedFormatId"
              class="min-h-[52px] w-full rounded-lg border border-white/10 bg-black/40 px-4 text-white outline-none transition-colors focus:border-action focus:ring-2 focus:ring-action/30"
            >
              <option v-for="format in video.formats" :key="format.id" :value="format.id">
                {{ format.label }} · {{ format.ext || 'auto' }} · {{ formatBytes(format.filesize) }}
              </option>
            </select>
            <p
              v-else
              class="rounded-lg border border-premium/35 bg-premium/10 px-4 py-3 text-sm leading-6 text-amber-50"
              role="status"
            >
              当前没有可直接下载的格式。B 站等平台常见音视频分离流，需要服务端安装 ffmpeg 后才能合并下载。
            </p>
          </label>

          <button
            class="mt-4 inline-flex min-h-[54px] w-full items-center justify-center gap-2 rounded-lg bg-white px-5 text-base font-black text-ink transition-colors duration-200 hover:bg-slate-200 focus:outline-none focus:ring-2 focus:ring-white/50 disabled:cursor-not-allowed disabled:opacity-60"
            type="button"
            :disabled="!canStart"
            @click="startDownload"
          >
            <Loader2 v-if="starting" class="h-5 w-5 animate-spin" aria-hidden="true" />
            <ArrowDownToLine v-else class="h-5 w-5" aria-hidden="true" />
            {{ starting ? '正在创建任务' : '开始下载' }}
          </button>
        </div>

        <div v-if="job" class="mt-6 rounded-lg border border-white/10 bg-black/20 p-4">
          <div class="flex items-center justify-between gap-3">
            <div>
              <p class="text-sm font-bold text-white">任务状态：{{ job.status }}</p>
              <p class="mt-1 text-xs text-slate-400">{{ job.quality_label || '默认格式' }}</p>
            </div>
            <span class="rounded-full border border-white/10 px-3 py-1 text-xs font-bold text-slate-300">
              {{ Math.round(job.progress || 0) }}%
            </span>
          </div>
          <div class="mt-4 h-3 overflow-hidden rounded-full bg-white/10">
            <div
              class="h-full rounded-full bg-gradient-to-r from-action via-premium to-signal transition-all duration-300"
              :style="{ width: `${Math.max(0, Math.min(100, job.progress || 0))}%` }"
            ></div>
          </div>
          <div class="mt-3 flex flex-wrap gap-3 text-xs text-slate-400">
            <span>{{ formatBytes(job.downloaded_bytes) }} / {{ formatBytes(job.total_bytes) }}</span>
            <span v-if="job.speed">{{ formatSpeed(job.speed) }}</span>
            <span v-if="job.eta">剩余 {{ Math.round(job.eta) }} 秒</span>
          </div>
          <button
            v-if="job.download_url"
            class="mt-4 inline-flex min-h-[48px] w-full items-center justify-center gap-2 rounded-lg bg-signal px-4 font-black text-ink transition-colors duration-200 hover:bg-cyan-300 focus:outline-none focus:ring-2 focus:ring-signal/50"
            type="button"
            @click="downloadFile"
          >
            <CheckCircle2 class="h-5 w-5" aria-hidden="true" />
            下载文件
          </button>
        </div>
      </section>
    </section>

    <section class="relative z-10 border-t border-white/10 bg-black/20 px-5 py-10 sm:px-8">
      <div class="mx-auto grid max-w-7xl gap-4 md:grid-cols-3">
        <div class="rounded-lg border border-premium/25 bg-premium/10 p-5">
          <Crown class="mb-3 h-5 w-5 text-premium" aria-hidden="true" />
          <p class="font-black text-white">Pro：批量队列</p>
          <p class="mt-2 text-sm leading-6 text-slate-300">后续可加入批量链接、并发队列和更快处理通道。</p>
        </div>
        <div class="rounded-lg border border-signal/25 bg-signal/10 p-5">
          <Sparkles class="mb-3 h-5 w-5 text-signal" aria-hidden="true" />
          <p class="font-black text-white">AI：总结与字幕</p>
          <p class="mt-2 text-sm leading-6 text-slate-300">下载闭环稳定后，可扩展字幕提取、翻译和视频摘要。</p>
        </div>
        <div class="rounded-lg border border-white/10 bg-white/[0.045] p-5">
          <ShieldCheck class="mb-3 h-5 w-5 text-action" aria-hidden="true" />
          <p class="font-black text-white">合规：公开内容</p>
          <p class="mt-2 text-sm leading-6 text-slate-300">不提供绕过权限、付费墙或 DRM 的能力。</p>
        </div>
      </div>
    </section>
  </main>
</template>
