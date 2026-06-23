<script setup>
import { computed } from "vue";
import { formatRichText } from "../../utils/richText";

const props = defineProps({
  content: {
    type: [String, Array],
    default: "",
  },
  tag: {
    type: String,
    default: "div",
  },
});

const formattedContent = computed(() => formatRichText(props.content));
</script>

<template>
  <component
    :is="tag"
    v-if="formattedContent"
    class="rich-text"
    v-html="formattedContent"
  />
</template>
