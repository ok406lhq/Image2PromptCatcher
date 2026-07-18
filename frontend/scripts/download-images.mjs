import { readFileSync, writeFileSync, mkdirSync } from 'fs'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const distDir = join(__dirname, '..', 'dist')
const articlePath = join(distDir, 'data', 'article.json')
const imagesDir = join(distDir, 'download-images')

let article
try {
  article = JSON.parse(readFileSync(articlePath, 'utf-8'))
} catch (e) {
  console.error('Failed to read article.json:', e.message)
  process.exit(1)
}

const allBlocks = [...article.blocks]
if (article.historyVersions) {
  for (const v of article.historyVersions) {
    allBlocks.push(...v.blocks)
  }
}

const imageUrls = [...new Set(allBlocks.map(b => b.image).filter(Boolean))]
console.log(`Total unique images: ${imageUrls.length}`)

mkdirSync(imagesDir, { recursive: true })

function getExt(url) {
  try {
    const raw = new URL(url).pathname.split('/').pop() || ''
    const parts = raw.split('.')
    if (parts.length >= 2) {
      const ext = parts.pop().toLowerCase().replace('jpeg', 'jpg')
      if (ext.length <= 5) return ext
    }
  } catch {}
  return 'png'
}

const manifest = {}
let count = 0
let skipped = 0
const failed = []

for (const url of imageUrls) {
  const ext = getExt(url)
  const filename = `${count + 1}.${ext}`

  try {
    const resp = await fetch(url, { signal: AbortSignal.timeout(15000) })
    if (resp.ok) {
      const buffer = Buffer.from(await resp.arrayBuffer())
      writeFileSync(join(imagesDir, filename), buffer)
      manifest[url] = filename
      count++
      process.stdout.write(`\rOK ${count}`)
    } else if (resp.status === 404) {
      skipped++
      process.stdout.write(`\r404 ${skipped}`)
      failed.push(`${resp.status} ${url.slice(0, 80)}`)
    } else {
      skipped++
      process.stdout.write(`\r${resp.status} ${skipped}`)
      failed.push(`${resp.status} ${url.slice(0, 80)}`)
    }
  } catch (e) {
    skipped++
    process.stdout.write(`\rERR ${skipped}`)
    failed.push(`ERR ${e.message.slice(0, 80)}`)
  }
}

writeFileSync(join(imagesDir, 'manifest.json'), JSON.stringify(manifest, null, 2))
console.log(`\n\nDone: ${count} downloaded, ${skipped} failed/skipped`)

if (failed.length > 0) {
  console.log('\nFailed URLs:')
  failed.forEach(f => console.log('  ' + f))
}
