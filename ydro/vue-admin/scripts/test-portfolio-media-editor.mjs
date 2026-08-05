import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const root = new URL('../', import.meta.url)

function read(relativePath) {
  return readFileSync(new URL(relativePath, root), 'utf8')
}

const dynamicField = read('src/components/DynamicField.vue')
const mediaPicker = read('src/components/MediaLibraryPicker.vue')
const mediaApi = read('src/api/media.js')
const sectionEdit = read('src/views/SectionEditView.vue')
const portfolioSchema = read('../apps/sites/my_portfolio_site.py')

assert.match(dynamicField, /import MediaLibraryPicker/)
assert.match(dynamicField, /mediaErrorMessage/)
assert.match(dynamicField, /uploadMediaFile/)
assert.match(dynamicField, /isNestedImageSource/)
assert.match(dynamicField, /images\|gallery/)
assert.match(dynamicField, /field:\s*props\.pathPrefix \|\| fieldKey\.value/)
assert.match(dynamicField, /\.jpg,\.jpeg,\.png,\.webp,\.ico/)
assert.doesNotMatch(dynamicField, /image\/\*/)
assert.doesNotMatch(dynamicField, /svg/)
assert.match(dynamicField, /selectedFileName/)
assert.match(dynamicField, /clearMedia\(\)/)
assert.doesNotMatch(dynamicField, /deleteMediaFile/)

assert.match(mediaPicker, /deleteMediaFile/)
assert.match(mediaPicker, /mediaErrorMessage/)
assert.match(mediaPicker, /emit\('select', item\)/)
assert.match(mediaPicker, /siteId/)

assert.match(mediaApi, /file_required/)
assert.match(mediaApi, /file_too_large/)
assert.match(mediaApi, /invalid_media_type/)
assert.match(mediaApi, /site_not_found/)
assert.match(mediaApi, /permission_denied/)
assert.match(mediaApi, /media_upload_failed/)
assert.match(mediaApi, /\/api\/uploads\//)

assert.match(sectionEdit, /uploadContext/)
assert.match(sectionEdit, /siteId: siteId\.value/)
assert.match(sectionEdit, /sectionKey: section\.value\?\.key/)

assert.match(portfolioSchema, /field\("image", ".*", "image"\)/)
assert.match(portfolioSchema, /field\("image_alt"/)
assert.match(portfolioSchema, /field\("src", ".*", "image"\)/)
assert.match(portfolioSchema, /field\("logo_image"/)
assert.match(portfolioSchema, /field\("portrait_image"/)
assert.match(portfolioSchema, /field\("profile_image"/)
assert.match(portfolioSchema, /field\("illustration_image"/)
assert.match(portfolioSchema, /field\("contact_image"/)
assert.match(portfolioSchema, /"key": "cases"/)
assert.match(portfolioSchema, /"key": "gallery"/)

console.log('portfolio media editor checks passed')
