<script>
import { defineComponent, h } from 'vue'
import { formatRichText } from '../../utils/richText'

export default defineComponent({
  props: {
    content: { type: [String, Array], default: '' },
    tag: { type: String, default: 'div' },
  },
  setup(props) {
    return () => {
      const html = formatRichText(props.content)
      // A native vnode preserves sanitized rich text during both SSR and client rendering.
      return html ? h(props.tag, { class: 'rich-text', innerHTML: html }) : null
    }
  },
})
</script>
