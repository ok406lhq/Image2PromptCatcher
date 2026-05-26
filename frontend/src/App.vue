<template>
  <div class="page">
    <header class="masthead">
      <p class="tag">AI IMAGE JOURNAL</p>
      <h1>{{ article?.title || 'GPT Image 2 图文精选' }}</h1>
      <p class="lead">{{ article?.intro }}</p>
      <div class="meta">
        <span>更新于 {{ formatUpdateTime(article?.updateAt) }}</span>
        <span>每天 09:00 / 23:00 自动抓取</span>
      </div>
    </header>

    <main>
      <div v-if="!article" class="loading">正在加载今日图文内容...</div>

      <section v-else class="feed">
        <article
          v-for="(item, index) in article.blocks"
          :key="`${item.image}-${index}`"
          class="card"
          :style="{ animationDelay: `${index * 50}ms` }"
        >
          <div class="thumb-wrap">
            <img
              class="thumb"
              :src="item.image"
              :alt="item.title"
              loading="lazy"
              @click="openPreview(item)"
            />
            <span class="chip">{{ item.section }}</span>
          </div>
          <div class="body">
            <h2>{{ item.title }}</h2>
            <p class="desc">{{ item.description }}</p>
            <div class="prompt-block">
              <div class="prompt-head">
                <p class="prompt-label">提示词</p>
                <button class="copy-btn" type="button" @click="copyPrompt(item.prompt, index)">
                  {{ copiedIndex === index ? '已复制' : '复制' }}
                </button>
              </div>
              <p class="prompt-text">{{ normalizePrompt(item.prompt) }}</p>
            </div>
          </div>
        </article>
      </section>
    </main>

    <footer class="footer" v-if="article">
      <a :href="article.source" target="_blank" rel="noopener noreferrer">查看原始仓库文档</a>
    </footer>

    <div v-if="previewOpen" class="lightbox" @click.self="closePreview">
      <button class="lightbox-close" type="button" @click="closePreview">×</button>
      <button class="lightbox-arrow left" type="button" @click="showPrevImage" :disabled="!hasPrevImage">←</button>
      <img class="lightbox-image" :src="currentPreviewImage" alt="预览图" />
      <button class="lightbox-arrow right" type="button" @click="showNextImage" :disabled="!hasNextImage">→</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'

interface ArticleBlock {
  section: string
  title: string
  description: string
  prompt: string
  image: string
}

interface Article {
  title: string
  intro: string
  blocks: ArticleBlock[]
  updateAt: string
  source: string
}

const article = ref<Article | null>(null)
const copiedIndex = ref<number | null>(null)
const previewOpen = ref(false)
const previewTitle = ref('')
const previewIndex = ref(0)

const fetchArticle = async () => {
  try {
    const response = await axios.get('/data/article.json')
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

onMounted(fetchArticle)

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

const galleryByTitle = computed(() => {
  const map: Record<string, string[]> = {}
  for (const item of article.value?.blocks || []) {
    if (!map[item.title]) map[item.title] = []
    map[item.title].push(item.image)
  }
  return map
})

const previewImages = computed(() => galleryByTitle.value[previewTitle.value] || [])
const currentPreviewImage = computed(() => previewImages.value[previewIndex.value] || '')
const hasNextImage = computed(() => previewIndex.value < previewImages.value.length - 1)
const hasPrevImage = computed(() => previewIndex.value > 0)

const openPreview = (item: ArticleBlock) => {
  const images = galleryByTitle.value[item.title] || [item.image]
  previewTitle.value = item.title
  previewIndex.value = Math.max(0, images.indexOf(item.image))
  previewOpen.value = true
}

const closePreview = () => {
  previewOpen.value = false
}

const showNextImage = () => {
  if (hasNextImage.value) previewIndex.value += 1
}

const showPrevImage = () => {
  if (hasPrevImage.value) previewIndex.value -= 1
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

.card:hover {
  transform: translateY(-6px);
  box-shadow: 0 18px 34px rgba(164, 95, 44, 0.2);
}

.thumb-wrap {
  position: relative;
}

.thumb {
  width: 100%;
  aspect-ratio: 4 / 3;
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

.prompt-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
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

.prompt-text {
  margin: 8px 0 0;
  color: #4a2f21;
  line-height: 1.6;
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.93rem;
  white-space: normal;
  display: -webkit-box;
  -webkit-line-clamp: 4;
  line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
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
}

.lightbox-image {
  max-width: min(1200px, 82vw);
  max-height: 84vh;
  border-radius: 12px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.45);
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

@media (max-width: 700px) {
  .masthead {
    padding-top: 48px;
  }

  .feed {
    grid-template-columns: 1fr;
  }
}
</style>
