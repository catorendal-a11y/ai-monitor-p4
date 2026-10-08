// Generate fixed RGB565 robot frames and BGRA logo images from the SVG sources.
// Run with Node.js and sharp installed; generated C++ is committed with sources.
const fs = require('fs');
const path = require('path');
const sharp = require('sharp');
const root = path.resolve(__dirname, '..');
const source = path.join(root, 'assets/nova');
const destination = path.join(root, 'src/ui');
const names = ['work', 'done', 'low', 'critical', 'sleep', 'blink'];
const header = ['#pragma once', '#include <lvgl.h>', 'namespace nova_assets {'];
const cpp = ['// Generated from assets/nova/*.svg by scripts/generate_nova_assets.cjs.', '#include "nova_assets.h"', 'namespace nova_assets {'];
function emit(name, pixels, width, height, format, stride) {
  header.push(`extern const lv_image_dsc_t ${name};`);
  cpp.push(`alignas(4) static const uint8_t ${name}_pixels[] = {`);
  for (let i = 0; i < pixels.length; i += 24)
    cpp.push('  ' + [...pixels.subarray(i, i + 24)].map(value => '0x' + value.toString(16).padStart(2, '0')).join(',') + ',');
  cpp.push('};', `const lv_image_dsc_t ${name} = { {LV_IMAGE_HEADER_MAGIC, ${format}, 0, ${width}, ${height}, ${stride}, 0}, sizeof(${name}_pixels), ${name}_pixels, nullptr, nullptr };`);
}
(async () => {
  for (const name of names) {
    const {data, info} = await sharp(path.join(source, name + '.svg')).removeAlpha().raw().toBuffer({resolveWithObject:true});
    const rgb565 = Buffer.alloc(info.width * info.height * 2);
    for (let i = 0; i < info.width * info.height; ++i) {
      const offset = i * info.channels;
      const value = (data[offset] >> 3) << 11 | (data[offset + 1] >> 2) << 5 | data[offset + 2] >> 3;
      rgb565.writeUInt16LE(value, i * 2);
    }
    emit(name, rgb565, info.width, info.height, 'LV_COLOR_FORMAT_RGB565', info.width * 2);
  }
  for (const brand of ['openai', 'zcode']) for (const size of [24, 42, 48]) {
    const inner = brand === 'zcode' ? Math.round(size * 2 / 3) : size;
    const padding = Math.floor((size - inner) / 2);
    let pipeline = sharp(path.join(source, brand + '-logo-white.svg')).resize(inner,inner,{fit:'contain',background:{r:0,g:0,b:0,alpha:0}});
    if (inner !== size) pipeline = pipeline.extend({top:padding,bottom:size-inner-padding,left:padding,right:size-inner-padding,background:{r:0,g:0,b:0,alpha:0}});
    const {data} = await pipeline.ensureAlpha().raw().toBuffer({resolveWithObject:true});
    const bgra = Buffer.from(data);
    for (let i = 0; i < bgra.length; i += 4) { bgra[i] = data[i + 2]; bgra[i + 2] = data[i]; }
    emit(brand + size, bgra, size, size, 'LV_COLOR_FORMAT_ARGB8888', size * 4);
  }
  header.push('const lv_image_dsc_t* logo_for(const char* provider, unsigned size);', '}');
  cpp.push('const lv_image_dsc_t* logo_for(const char* provider, unsigned size) {',
    '  if (!provider) return nullptr;',
    '  if (strcmp(provider, "codex") == 0) return size == 24 ? &openai24 : (size == 42 ? &openai42 : &openai48);',
    '  if (strcmp(provider, "zcode") == 0) return size == 24 ? &zcode24 : (size == 42 ? &zcode42 : &zcode48);',
    '  return nullptr;', '}', '}');
  cpp.splice(2, 0, '#include <cstring>');
  fs.writeFileSync(path.join(destination, 'nova_assets.h'), header.join('\n') + '\n');
  fs.writeFileSync(path.join(destination, 'nova_assets.cpp'), cpp.join('\n') + '\n');
  console.log('Generated 6 robot frames and 6 original-logo images.');
})().catch(error => { console.error(error.message); process.exit(1); });
