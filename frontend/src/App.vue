<template>
  <div class="page">
    <header class="masthead">
      <img class="site-logo" src="/logo.webp" alt="anomo" />
      <p class="tag">AI IMAGE JOURNAL</p>
      <h1>{{ article?.title || 'GPT Image 2 图文精选' }}</h1>
      <p class="lead">{{ article?.intro }}</p>
      <div class="meta">
        <span>更新于 {{ formatUpdateTime(article?.updateAt) }}</span>
        <span>每天 09:00 / 23:00 自动抓取</span>
      </div>
      <div class="history-panel" v-if="article?.recentHistory?.length">
        <button class="history-main-link" type="button" @click="selectVersion('latest')">最近历史更新</button>
        <div class="history-list">
          <button
            v-for="item in article.recentHistory"
            :key="item.sha"
            class="history-btn"
            type="button"
            @click="selectVersion(item.sha)"
            :class="{ active: activeVersionKey === item.sha }"
            :title="`${item.message} (${formatUpdateTime(item.date)})`"
          >
            {{ historyButtonLabel(item.sha) }}
          </button>
        </div>
      </div>
    </header>

    <main>
      <div v-if="!article" class="loading">正在加载今日图文内容...</div>

      <section v-else :class="['feed', { refreshing: isRefreshing }]">
        <article
          v-for="(item, index) in visibleBlocks"
          :key="`${item.image}-${index}`"
          class="card"
          :style="cardAnimStyle(index)"
        >
          <div class="thumb-wrap">
            <img
              class="thumb"
              :src="proxyImageUrl(item.image)"
              :alt="item.title"
              loading="lazy"
              @click="openPreview(item)"
            />
            <span class="chip">{{ item.section }}</span>
          </div>
          <div class="body">
            <h2>{{ item.title }}</h2>
            <div class="desc-row">
              <p class="desc" :title="item.description">{{ item.description }}</p>
              <button class="copy-desc-btn" type="button" @click="copyDescription(item.description, index)">
                {{ copiedDescIndex === index ? '已复制描述' : '复制描述' }}
              </button>
            </div>
            <div class="prompt-block">
              <div class="prompt-head">
                <p class="prompt-label">提示词 <span v-if="item.publishedAt" class="published-at">{{ item.publishedAt }}</span></p>
                <div class="actions">
                  <a
                    v-if="item.xUrl"
                    class="x-link"
                    :href="item.xUrl"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    via X
                  </a>
                  <button
                    class="fav-btn"
                    type="button"
                    :class="{ active: isBookmarked(index, activeVersionKey) }"
                    :title="isBookmarked(index, activeVersionKey) ? '取消收藏' : '收藏'"
                    @click="toggleBookmark(item, index)"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path
                        d="M5 4C5 2.89543 5.89543 2 7 2H17C18.1046 2 19 2.89543 19 4V21L12 17L5 21V4Z"
                        :fill="isBookmarked(index, activeVersionKey) ? 'currentColor' : 'none'"
                        stroke="currentColor"
                        stroke-width="2"
                        stroke-linejoin="round"
                      />
                    </svg>
                  </button>
                  <button class="copy-btn" type="button" @click="copyPrompt(item.prompt, index)">
                    {{ copiedIndex === index ? '已复制' : '复制' }}
                  </button>
                </div>
              </div>
              <p class="prompt-text" @click="openPromptModal(item.prompt, index)">{{ normalizePrompt(item.prompt) }}</p>
              <div class="meta-row">
                <span v-if="item.author">作者：{{ item.author }}</span>
                <span v-if="item.language">语言：{{ item.language }}</span>
              </div>
            </div>
          </div>
        </article>
      </section>
    </main>

    <footer class="footer" v-if="article">
      <a :href="article.source" target="_blank" rel="noopener noreferrer">查看原始仓库文档</a>
    </footer>

    <!-- 右侧收藏面板 - 桌面端 -->
    <aside v-if="bookmarks.length > 0" class="bookmark-panel">
      <div class="bookmark-panel-header">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
          <path d="M5 4C5 2.89543 5.89543 2 7 2H17C18.1046 2 19 2.89543 19 4V21L12 17L5 21V4Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round" fill="currentColor"/>
        </svg>
        <span>收藏 ({{ bookmarks.length }})</span>
      </div>
      <div class="bookmark-panel-list">
        <button
          v-for="(b, bi) in bookmarks"
          :key="`${b.blockIndex}-${b.versionKey}`"
          class="bookmark-item"
          type="button"
          @click="handleBookmarkClick(b)"
        >
          <img class="bookmark-thumb" :src="proxyImageUrl(b.image)" :alt="b.title" loading="lazy" />
          <span class="bookmark-title">{{ b.title }}</span>
          <button
            class="bookmark-remove"
            type="button"
            title="移除收藏"
            @click.stop="bookmarks = bookmarks.filter((_, i) => i !== bi)"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </button>
      </div>
    </aside>

    <!-- 移动端收藏入口按钮 + 抽屉 -->
    <button
      v-if="bookmarks.length > 0"
      class="bookmark-mobile-entry"
      type="button"
      :class="{ active: bookmarkMobileOpen }"
      @click="bookmarkMobileOpen = !bookmarkMobileOpen"
      title="收藏列表"
    >
      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
        <path d="M5 4C5 2.89543 5.89543 2 7 2H17C18.1046 2 19 2.89543 19 4V21L12 17L5 21V4Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round" fill="currentColor"/>
      </svg>
      {{ bookmarks.length }}
    </button>

    <div v-if="bookmarkMobileOpen && bookmarks.length > 0" class="bookmark-mobile-overlay" @click.self="bookmarkMobileOpen = false">
      <div class="bookmark-mobile-drawer">
        <div class="bookmark-mobile-header">
          <span>收藏 ({{ bookmarks.length }})</span>
          <button class="bookmark-mobile-close" type="button" @click="bookmarkMobileOpen = false">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="bookmark-mobile-list">
          <button
            v-for="(b, bi) in bookmarks"
            :key="`m-${b.blockIndex}-${b.versionKey}`"
            class="bookmark-item"
            type="button"
            @click="bookmarkMobileOpen = false; handleBookmarkClick(b)"
          >
            <img class="bookmark-thumb" :src="proxyImageUrl(b.image)" :alt="b.title" loading="lazy" />
            <span class="bookmark-title">{{ b.title }}</span>
            <button
              class="bookmark-remove"
              type="button"
              title="移除收藏"
              @click.stop="bookmarks = bookmarks.filter((_, i) => i !== bi)"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </button>
        </div>
      </div>
    </div>

    <div v-if="previewOpen" class="lightbox" @click="closePreview" @wheel="handleWheel">
      <button class="lightbox-close" type="button" @click.stop="closePreview">×</button>
      <button class="lightbox-arrow left" type="button" @click.stop="showPrevImage" :disabled="!hasPrevImage">←</button>
      <div class="lightbox-image-wrapper" @mousedown.stop="startDrag" @mousemove.stop="drag" @mouseup.stop="endDrag" @mouseleave.stop="endDrag" @click.stop>
        <img
          class="lightbox-image"
          :src="proxyImageUrl(currentPreviewImage)"
          alt="预览图"
          :style="imageTransformStyle"
          @dragstart.prevent
        />
      </div>
      <button class="lightbox-arrow right" type="button" @click.stop="showNextImage" :disabled="!hasNextImage">→</button>
      <div class="lightbox-controls" @click.stop>
        <button class="lightbox-zoom-btn" type="button" @click.stop="zoomOut" title="缩小">−</button>
        <span class="lightbox-zoom-level">{{ Math.round(imageScale * 100) }}%</span>
        <button class="lightbox-zoom-btn" type="button" @click.stop="zoomIn" title="放大">+</button>
        <button class="lightbox-reset-btn" type="button" @click.stop="resetImage" title="重置">⊡</button>
      </div>
    </div>

    <button
      v-if="showBackToTop"
      class="back-to-top"
      type="button"
      @click="scrollToTop"
      title="回到顶部"
    >
      ↑
    </button>

    <div v-if="promptModalOpen" class="prompt-modal-overlay" @click.self="closePromptModal">
      <div class="prompt-modal" :class="{ show: promptModalOpen }">
        <div class="prompt-modal-header">
          <h3>提示词详情</h3>
          <button class="prompt-modal-close" type="button" @click="closePromptModal">×</button>
        </div>
        <div class="prompt-modal-content">
          <p class="prompt-modal-text">{{ fullPromptText }}</p>
        </div>
        <div class="prompt-modal-footer">
          <button class="prompt-modal-copy-btn" type="button" @click="copyFullPrompt">
            {{ copiedFullPrompt ? '已复制' : '复制提示词' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted, nextTick } from 'vue'
import axios from 'axios'

interface ArticleBlock {
  section: string
  title: string
  description: string
  prompt: string
  image: string
  xUrl?: string
  publishedAt?: string
  author?: string
  language?: string
}

interface BookmarkItem {
  image: string
  title: string
  prompt: string
  section: string
  blockIndex: number
  versionKey: string
}

interface Article {
  title: string
  intro: string
  blocks: ArticleBlock[]
  updateAt: string
  source: string
  historyPage?: string
  recentHistory?: {
    sha: string
    message: string
    date: string
    url: string
  }[]
  historyVersions?: {
    sha: string
    message: string
    date: string
    title: string
    intro: string
    blocks: ArticleBlock[]
  }[]
}

const article = ref<Article | null>(null)
const copiedIndex = ref<number | null>(null)
const copiedDescIndex = ref<number | null>(null)
const previewOpen = ref(false)
const previewTitle = ref('')
const previewIndex = ref(0)
const activeVersionKey = ref('latest')
const isRefreshing = ref(false)
const showBackToTop = ref(false)
const scrollThreshold = 600
const promptModalOpen = ref(false)
const fullPromptText = ref('')
const currentPromptIndex = ref<number | null>(null)
const copiedFullPrompt = ref(false)
const imageScale = ref(1)
const imagePosition = ref({ x: 0, y: 0 })
const isDragging = ref(false)
const dragStart = ref({ x: 0, y: 0 })
const minScale = 0.5
const maxScale = 3

const bookmarks = ref<BookmarkItem[]>([])
const bookmarkMobileOpen = ref(false)

const isBookmarked = (index: number, versionKey: string): boolean => {
  return bookmarks.value.some(
    (b) => b.blockIndex === index && b.versionKey === versionKey
  )
}

const PROXY_HOSTS = ['cms-assets.youmind.com', 'marketing-assets.youmind.com']

const proxyImageUrl = (url: string): string => {
  if (!url) return url
  try {
    const hostname = new URL(url).hostname
    if (PROXY_HOSTS.includes(hostname)) {
      return `/api/proxy-image?url=${encodeURIComponent(url)}`
    }
  } catch {}
  return url
}

const fetchArticle = async () => {
  try {
    const dataUrl = `${import.meta.env.BASE_URL}data/article.json`
    const response = await axios.get(dataUrl)
    article.value = response.data
  } catch (error) {
    console.error('Failed to fetch article:', error)
  }
}

const formatUpdateTime = (isoString?: string) => {
  if (!isoString) return '--'
  return new Date(isoString).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const handleScroll = () => {
  showBackToTop.value = window.scrollY > scrollThreshold
}

const scrollToTop = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const openPromptModal = (prompt: string, index: number) => {
  fullPromptText.value = normalizePrompt(prompt)
  currentPromptIndex.value = index
  promptModalOpen.value = true
  copiedFullPrompt.value = false
}

const closePromptModal = () => {
  promptModalOpen.value = false
  currentPromptIndex.value = null
  copiedFullPrompt.value = false
}

const copyFullPrompt = async () => {
  await navigator.clipboard.writeText(fullPromptText.value || '')
  copiedFullPrompt.value = true
  window.setTimeout(() => {
    if (copiedFullPrompt.value) copiedFullPrompt.value = false
  }, 1200)
}

const handleWheel = (e: WheelEvent) => {
  e.preventDefault()
  const delta = e.deltaY > 0 ? -0.1 : 0.1
  const newScale = Math.min(maxScale, Math.max(minScale, imageScale.value + delta))
  imageScale.value = newScale
}

const zoomIn = () => {
  imageScale.value = Math.min(maxScale, imageScale.value + 0.2)
}

const zoomOut = () => {
  imageScale.value = Math.max(minScale, imageScale.value - 0.2)
}

const resetImage = () => {
  imageScale.value = 1
  imagePosition.value = { x: 0, y: 0 }
}

const startDrag = (e: MouseEvent) => {
  if (imageScale.value <= 1) return
  isDragging.value = true
  dragStart.value = { x: e.clientX - imagePosition.value.x, y: e.clientY - imagePosition.value.y }
}

const drag = (e: MouseEvent) => {
  if (!isDragging.value) return
  e.preventDefault()
  imagePosition.value = {
    x: e.clientX - dragStart.value.x,
    y: e.clientY - dragStart.value.y,
  }
}

const endDrag = () => {
  isDragging.value = false
}

const closePreview = () => {
  previewOpen.value = false
  resetImage()
}

const showNextImage = () => {
  if (hasNextImage.value) {
    previewIndex.value += 1
    resetImage()
  }
}

const showPrevImage = () => {
  if (hasPrevImage.value) {
    previewIndex.value -= 1
    resetImage()
  }
}

onMounted(() => {
  fetchArticle()
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})

const normalizePrompt = (prompt?: string) => {
  if (!prompt) return '请在源文档对应章节查看完整提示词。'
  const normalized = prompt.replace(/^提示词[:：]?/i, '').replace(/\s+/g, ' ').trim()
  return normalized || '请在源文档对应章节查看完整提示词。'
}

const copyPrompt = async (prompt: string, index: number) => {
  await navigator.clipboard.writeText(prompt || '')
  copiedIndex.value = index
  window.setTimeout(() => {
    if (copiedIndex.value === index) copiedIndex.value = null
  }, 1200)
}

const copyDescription = async (description: string, index: number) => {
  await navigator.clipboard.writeText(description || '')
  copiedDescIndex.value = index
  window.setTimeout(() => {
    if (copiedDescIndex.value === index) copiedDescIndex.value = null
  }, 1200)
}

const galleryByTitle = computed(() => {
  const map: Record<string, string[]> = {}
  for (const item of visibleBlocks.value || []) {
    if (!map[item.title]) map[item.title] = []
    map[item.title].push(item.image)
  }
  return map
})

const visibleBlocks = computed(() => {
  if (!article.value) return []
  if (activeVersionKey.value === 'latest') return article.value.blocks
  const target = article.value.historyVersions?.find((v) => v.sha === activeVersionKey.value)
  return target?.blocks || article.value.blocks
})

const selectVersion = (key: string) => {
  isRefreshing.value = true
  activeVersionKey.value = key
  window.setTimeout(() => {
    isRefreshing.value = false
  }, 420)
}

const toggleBookmark = (item: ArticleBlock, index: number) => {
  const vk = activeVersionKey.value
  if (isBookmarked(index, vk)) {
    bookmarks.value = bookmarks.value.filter(
      (b) => !(b.blockIndex === index && b.versionKey === vk)
    )
  } else {
    bookmarks.value.push({
      image: item.image,
      title: item.title,
      prompt: item.prompt,
      section: item.section,
      blockIndex: index,
      versionKey: vk,
    })
  }
}

const handleBookmarkClick = async (item: BookmarkItem) => {
  if (activeVersionKey.value !== item.versionKey) {
    selectVersion(item.versionKey)
    await nextTick()
    await nextTick()
  }
  const cards = document.querySelectorAll('.card')
  if (cards[item.blockIndex]) {
    cards[item.blockIndex].scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
}

const historyLabels = computed(() => {
  const labels: Record<string, string> = {}
  const counters: Record<string, number> = {}
  const records = [...(article.value?.recentHistory || [])]
  records.reverse()

  for (const item of records) {
    const date = item.date ? new Date(item.date) : null
    const ymd = date && !Number.isNaN(date.getTime())
      ? date.toISOString().slice(0, 10)
      : 'unknown-date'
    counters[ymd] = (counters[ymd] || 0) + 1
    labels[item.sha] = `${ymd}-v${counters[ymd]}`
  }

  return labels
})

const historyButtonLabel = (sha: string) => historyLabels.value[sha] || sha

const cardAnimStyle = (index: number) => {
  const stagger = index * 50
  const base = isRefreshing.value ? 30 : 0
  return { animationDelay: `${stagger + base}ms` }
}

const previewImages = computed(() => galleryByTitle.value[previewTitle.value] || [])
const currentPreviewImage = computed(() => previewImages.value[previewIndex.value] || '')
const hasNextImage = computed(() => previewIndex.value < previewImages.value.length - 1)
const hasPrevImage = computed(() => previewIndex.value > 0)

const imageTransformStyle = computed(() => ({
  transform: `translate(${imagePosition.value.x}px, ${imagePosition.value.y}px) scale(${imageScale.value})`,
  cursor: isDragging.value ? 'grabbing' : imageScale.value > 1 ? 'grab' : 'default',
}))

const openPreview = (item: ArticleBlock) => {
  const images = galleryByTitle.value[item.title] || [item.image]
  previewTitle.value = item.title
  previewIndex.value = Math.max(0, images.indexOf(item.image))
  previewOpen.value = true
}
</script>

<style scoped>
:global(body) {
  margin: 0;
}

:global(*) {
  box-sizing: border-box;
}

.page {
  min-height: 100vh;
  color: #2f1b14;
  background:
    radial-gradient(circle at top right, rgba(255, 214, 166, 0.45), transparent 40%),
    radial-gradient(circle at left 20%, rgba(255, 236, 205, 0.7), transparent 35%),
    #fffaf2;
  font-family: Georgia, Cambria, 'Times New Roman', serif;
  padding-bottom: 56px;
}

.masthead {
  max-width: 1040px;
  margin: 0 auto;
  padding: 64px 24px 32px;
  text-align: center;
}

.site-logo {
  width: 72px;
  height: 72px;
  border-radius: 16px;
  margin-bottom: 14px;
}

.tag {
  margin: 0;
  letter-spacing: 0.14em;
  color: #9c5a2f;
  font-size: 12px;
  font-family: 'Trebuchet MS', 'Gill Sans', sans-serif;
}

h1 {
  margin: 10px 0 12px;
  font-size: clamp(2rem, 4vw, 3.1rem);
  line-height: 1.15;
}

.lead {
  margin: 0;
  max-width: 760px;
  color: #6d4b3a;
  font-size: 1.1rem;
  line-height: 1.7;
}

.meta {
  margin-top: 18px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.meta span {
  border: 1px solid #e7c39f;
  background: #fff2df;
  color: #7e5133;
  border-radius: 999px;
  padding: 6px 12px;
  font: 600 13px/1.2 'Trebuchet MS', sans-serif;
}

.history-panel {
  margin-top: 14px;
  display: grid;
  gap: 10px;
}

.history-main-link {
  width: fit-content;
  border: 1px solid #d8b496;
  background: #fff;
  color: #7e4a2a;
  border-radius: 999px;
  padding: 8px 14px;
  font: 700 13px/1.2 'Trebuchet MS', sans-serif;
  text-decoration: none;
  cursor: pointer;
}

.history-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.history-btn {
  border: 1px solid #e6c6aa;
  background: #fff4e6;
  color: #8d5532;
  border-radius: 999px;
  padding: 4px 10px;
  text-decoration: none;
  font: 600 12px/1.2 'Trebuchet MS', sans-serif;
  cursor: pointer;
}

.history-btn.active {
  background: #e9c3a1;
  color: #5a2f16;
}

.loading {
  text-align: center;
  padding: 80px 24px;
  color: #8e6040;
}

.feed {
  max-width: 1040px;
  margin: 0 auto;
  padding: 8px 24px 24px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(290px, 1fr));
  gap: 24px;
}

.card {
  background: #fff;
  border: 1px solid #f2d3b7;
  border-radius: 18px;
  overflow: hidden;
  box-shadow: 0 12px 30px rgba(164, 95, 44, 0.11);
  animation: reveal 0.55s ease both;
  transition: transform 260ms ease, box-shadow 260ms ease;
}

.feed.refreshing .card {
  animation-name: refreshReveal;
  animation-duration: 0.48s;
  animation-timing-function: ease;
  animation-fill-mode: both;
}

.card:hover {
  transform: translateY(-6px);
  box-shadow: 0 18px 34px rgba(164, 95, 44, 0.2);
}

.thumb-wrap {
  position: relative;
}

.thumb {
  width: 100%;
  aspect-ratio: 3 / 4;
  object-fit: cover;
  display: block;
  transition: transform 380ms ease;
  cursor: zoom-in;
}

.card:hover .thumb {
  transform: scale(1.03);
}

.chip {
  position: absolute;
  left: 12px;
  bottom: 12px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(62, 34, 21, 0.78);
  color: #fff;
  font: 600 12px/1.2 'Trebuchet MS', sans-serif;
}

.body {
  padding: 18px;
}

h2 {
  margin: 0;
  font-size: 1.25rem;
  line-height: 1.35;
}

.desc {
  margin: 10px 0 0;
  color: #6a4a39;
  line-height: 1.65;
  white-space: normal;
  word-break: break-word;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.desc-row {
  display: grid;
  gap: 8px;
}

.copy-desc-btn {
  width: fit-content;
  border: 1px solid #e5c4a6;
  background: #fff;
  color: #8b4b21;
  border-radius: 999px;
  padding: 4px 10px;
  font: 600 12px/1.2 'Trebuchet MS', sans-serif;
  cursor: pointer;
}

.prompt-block {
  margin-top: 14px;
  border-radius: 12px;
  background: #fff7ec;
  border: 1px solid #f2dcc4;
  padding: 12px;
}

.prompt-label {
  margin: 0;
  color: #a25f31;
  font: 700 12px/1.2 'Trebuchet MS', sans-serif;
  letter-spacing: 0.06em;
}

.published-at {
  margin-left: 8px;
  font-weight: 500;
  color: #9f6c47;
  font-size: 11px;
}

.prompt-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.x-link {
  border: 1px solid #d8b496;
  background: linear-gradient(135deg, #fff, #fbeee1);
  color: #7c4624;
  border-radius: 999px;
  padding: 4px 10px;
  font: 600 12px/1.2 'Trebuchet MS', sans-serif;
  text-decoration: none;
}

.copy-btn {
  border: 1px solid #e5c4a6;
  background: #fff;
  color: #8b4b21;
  border-radius: 999px;
  padding: 4px 10px;
  font: 600 12px/1.2 'Trebuchet MS', sans-serif;
  cursor: pointer;
}

.fav-btn {
  border: 1px solid #e5c4a6;
  background: #fff;
  color: #c4956a;
  border-radius: 999px;
  padding: 4px 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s ease, background 0.2s ease, border-color 0.2s ease, transform 0.15s ease;
}

.fav-btn:hover {
  border-color: #d89c5c;
  color: #b87640;
  transform: scale(1.08);
}

.fav-btn.active {
  background: #fff4e6;
  border-color: #d89c5c;
  color: #c4702a;
}

.prompt-text {
  margin: 8px 0 0;
  color: #4a2f21;
  line-height: 1.6;
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.93rem;
  white-space: normal;
  display: -webkit-box;
  -webkit-line-clamp: 5;
  line-clamp: 5;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.meta-row {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.meta-row span {
  border: 1px solid #efd4be;
  background: #fff;
  color: #8a5633;
  border-radius: 999px;
  padding: 4px 10px;
  font: 600 12px/1.2 'Trebuchet MS', sans-serif;
}

.lightbox {
  position: fixed;
  inset: 0;
  background: rgba(19, 11, 7, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1200;
  padding: 24px;
  overflow: hidden;
}

.lightbox-image-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: visible;
  pointer-events: none;
}

.lightbox-image {
  max-width: min(1200px, 82vw);
  max-height: 84vh;
  border-radius: 12px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.45);
  transition: transform 0.1s ease;
  user-select: none;
  -webkit-user-drag: none;
  pointer-events: auto;
}

.lightbox-arrow,
.lightbox-close {
  position: absolute;
  border: 0;
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
  width: 44px;
  height: 44px;
  border-radius: 999px;
  cursor: pointer;
  font-size: 26px;
}

.lightbox-close {
  top: 22px;
  right: 22px;
}

.lightbox-arrow.left {
  left: max(16px, calc(50vw - 620px));
}

.lightbox-arrow.right {
  right: max(16px, calc(50vw - 620px));
}

.lightbox-arrow:disabled {
  opacity: 0.35;
  cursor: default;
}

.lightbox-controls {
  position: absolute;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(8px);
  padding: 8px 16px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.lightbox-zoom-btn {
  border: none;
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  font-size: 20px;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 300;
}

.lightbox-zoom-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.1);
}

.lightbox-zoom-btn:active {
  transform: scale(0.95);
}

.lightbox-zoom-level {
  color: #fff;
  font: 600 13px/1 'Trebuchet MS', sans-serif;
  min-width: 50px;
  text-align: center;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.lightbox-reset-btn {
  border: none;
  background: rgba(255, 170, 100, 0.3);
  color: #fff;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  font-size: 18px;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: 8px;
}

.lightbox-reset-btn:hover {
  background: rgba(255, 170, 100, 0.45);
  transform: rotate(90deg);
}

.lightbox-reset-btn:active {
  transform: rotate(90deg) scale(0.95);
}

.footer {
  max-width: 1040px;
  margin: 8px auto 0;
  padding: 0 24px;
}

.footer a {
  color: #9d5127;
  text-decoration: none;
  border-bottom: 1px dashed currentColor;
}

/* 收藏面板 - 桌面端 */
.bookmark-panel {
  position: fixed;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 360px;
  max-height: 60vh;
  background: #fffaf2;
  border: 1px solid #f2d3b7;
  border-radius: 18px;
  box-shadow: 0 12px 30px rgba(164, 95, 44, 0.11);
  z-index: 500;
  overflow: hidden;
  display: none;
  flex-direction: column;
  transition: opacity 0.3s ease, transform 0.3s ease;
}

@media (min-width: 1280px) {
  .bookmark-panel {
    display: flex;
  }
}

.bookmark-panel-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 14px;
  border-bottom: 1px solid #efd4be;
  background: linear-gradient(135deg, #fff7ec, #fff0e0);
  font: 700 13px/1.2 'Trebuchet MS', sans-serif;
  color: #8b5a2b;
  flex-shrink: 0;
}

.bookmark-panel-list {
  overflow-y: auto;
  flex: 1;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.bookmark-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px;
  border: 1px solid transparent;
  border-radius: 12px;
  background: transparent;
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease;
  text-align: left;
  width: 100%;
}

.bookmark-item:hover {
  background: #fff7ec;
  border-color: #f2dcc4;
}

.bookmark-thumb {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  object-fit: cover;
  flex-shrink: 0;
  border: 1px solid #efd4be;
}

.bookmark-title {
  flex: 1;
  font: 600 12px/1.3 'Trebuchet MS', sans-serif;
  color: #6a4a39;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bookmark-remove {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  border: none;
  background: transparent;
  color: #c4956a;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s ease, color 0.2s ease;
  opacity: 0;
}

.bookmark-item:hover .bookmark-remove {
  opacity: 1;
}

.bookmark-remove:hover {
  background: rgba(168, 113, 74, 0.15);
  color: #7a4a24;
}

/* 移动端收藏 */
.bookmark-mobile-entry {
  position: fixed;
  right: 24px;
  bottom: 92px;
  width: 56px;
  height: 56px;
  border: 1px solid #f2d3b7;
  background: rgba(255, 250, 242, 0.95);
  color: #c4702a;
  border-radius: 50%;
  font: 700 11px/1 'Trebuchet MS', sans-serif;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(164, 95, 44, 0.25);
  transition: transform 0.2s ease, background 0.2s ease;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1px;
}

.bookmark-mobile-entry:hover {
  background: rgba(255, 240, 220, 1);
  transform: translateY(-3px);
}

.bookmark-mobile-entry.active {
  background: #fff4e6;
  border-color: #d89c5c;
}

.bookmark-mobile-overlay {
  position: fixed;
  inset: 0;
  background: rgba(19, 11, 7, 0.5);
  backdrop-filter: blur(4px);
  z-index: 1400;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  animation: overlayFadeIn 0.25s ease;
}

.bookmark-mobile-drawer {
  width: 100%;
  max-width: 500px;
  max-height: 55vh;
  background: #fffaf2;
  border-radius: 20px 20px 0 0;
  border: 1px solid #f2d3b7;
  box-shadow: 0 -8px 40px rgba(164, 95, 44, 0.15);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transform: translateY(100%);
  animation: slideUp 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}

@keyframes slideUp {
  to {
    transform: translateY(0);
  }
}

.bookmark-mobile-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-bottom: 1px solid #efd4be;
  background: linear-gradient(135deg, #fff7ec, #fff0e0);
  font: 700 14px/1.2 'Trebuchet MS', sans-serif;
  color: #8b5a2b;
  flex-shrink: 0;
}

.bookmark-mobile-close {
  border: none;
  background: transparent;
  color: #a8714a;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s ease, color 0.2s ease;
}

.bookmark-mobile-close:hover {
  background: rgba(168, 113, 74, 0.15);
  color: #7a4a24;
}

.bookmark-mobile-list {
  overflow-y: auto;
  flex: 1;
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

@media (min-width: 1280px) {
  .bookmark-mobile-entry,
  .bookmark-mobile-overlay {
    display: none;
  }
}

@keyframes reveal {
  from {
    opacity: 0;
    transform: translateY(14px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes refreshReveal {
  from {
    opacity: 0;
    transform: translateY(10px) scale(0.985);
    filter: blur(1px);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
    filter: blur(0);
  }
}

@media (max-width: 700px) {
  .masthead {
    padding-top: 48px;
  }

  .feed {
    grid-template-columns: 1fr;
  }
}

.back-to-top {
  position: fixed;
  right: 24px;
  bottom: 24px;
  width: 56px;
  height: 56px;
  border: none;
  background: rgba(164, 95, 44, 0.9);
  color: #fff;
  border-radius: 50%;
  font-size: 28px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(164, 95, 44, 0.4);
  transition: transform 0.2s ease, background 0.2s ease, opacity 0.3s ease;
  z-index: 1000;
  opacity: 0.95;
}

.back-to-top:hover {
  background: rgba(164, 95, 44, 1);
  transform: translateY(-3px);
  opacity: 1;
}

.back-to-top:active {
  transform: translateY(-1px);
}

.prompt-text {
  margin: 8px 0 0;
  color: #4a2f21;
  line-height: 1.6;
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.93rem;
  white-space: normal;
  display: -webkit-box;
  -webkit-line-clamp: 5;
  line-clamp: 5;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
  transition: color 0.2s ease, background 0.2s ease;
  padding: 4px 8px;
  border-radius: 6px;
}

.prompt-text:hover {
  background: rgba(255, 198, 151, 0.3);
  color: #8b5a2b;
}

.prompt-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(19, 11, 7, 0.75);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1300;
  padding: 24px;
  animation: overlayFadeIn 0.25s ease;
}

.prompt-modal {
  background: linear-gradient(135deg, #fffaf2 0%, #fff5e6 100%);
  border-radius: 20px;
  box-shadow: 0 25px 80px rgba(164, 95, 44, 0.25);
  width: 100%;
  max-width: 700px;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transform: scale(0.92) translateY(20px);
  opacity: 0;
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.3s ease;
}

.prompt-modal.show {
  transform: scale(1) translateY(0);
  opacity: 1;
}

.prompt-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 24px;
  border-bottom: 1px solid #efd4be;
  background: linear-gradient(135deg, #fff7ec, #fff0e0);
}

.prompt-modal-header h3 {
  margin: 0;
  color: #8b5a2b;
  font-size: 1.2rem;
  font-weight: 700;
  font-family: Georgia, Cambria, serif;
}

.prompt-modal-close {
  border: none;
  background: transparent;
  color: #a8714a;
  font-size: 32px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease, transform 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.prompt-modal-close:hover {
  background: rgba(168, 113, 74, 0.15);
  color: #7a4a24;
  transform: rotate(90deg);
}

.prompt-modal-content {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
  max-height: 60vh;
}

.prompt-modal-text {
  margin: 0;
  color: #4a2f21;
  line-height: 1.8;
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.95rem;
  white-space: pre-wrap;
  word-break: break-word;
}

.prompt-modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #efd4be;
  background: linear-gradient(135deg, #fff7ec, #fff0e0);
  display: flex;
  justify-content: flex-end;
}

.prompt-modal-copy-btn {
  border: 2px solid #d89c5c;
  background: linear-gradient(135deg, #ffb380, #ff9955);
  color: #fff;
  border-radius: 999px;
  padding: 10px 24px;
  font: 700 14px/1.2 'Trebuchet MS', sans-serif;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
  box-shadow: 0 4px 12px rgba(255, 153, 85, 0.35);
}

.prompt-modal-copy-btn:hover {
  background: linear-gradient(135deg, #ffa666, #ff8844);
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(255, 153, 85, 0.45);
}

.prompt-modal-copy-btn:active {
  transform: translateY(0);
}

@keyframes overlayFadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>
