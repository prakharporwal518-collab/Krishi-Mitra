// Copies shared assets into the frontend so it can run fully in the browser (Netlify):
//   backend/data/*.json -> src/data/, samples/*.jpg -> public/samples/
import { cpSync, mkdirSync, readdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')
const copy = (from, to, filter = () => true) => {
  mkdirSync(to, { recursive: true })
  for (const f of readdirSync(from).filter(filter)) cpSync(join(from, f), join(to, f))
}
copy(join(root, '../backend/data'), join(root, 'src/data'), (f) => f.endsWith('.json'))
copy(join(root, '../samples'), join(root, 'public/samples'), (f) => /\.(jpe?g|png)$/i.test(f))
console.log('assets synced')
