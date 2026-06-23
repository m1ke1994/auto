<template>
    <button class="burger" type="button" aria-label="меню" @click="emit('toggle')">
        <span class="burger__icon">
            <span></span>
            <span></span>
            <span></span>
        </span>
    </button>
</template>

<script setup>
const emit = defineEmits(['toggle']);
</script>

<style scoped>
.burger {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 38px;
    background: var(--card);
    background: color-mix(in srgb, var(--card) 70%, transparent);
    border: none;
    cursor: pointer;
    border-radius: 12px;
    box-shadow: 0 10px 18px var(--shadow);
    backdrop-filter: blur(10px);
    transition: transform 200ms ease, box-shadow 200ms ease, background 200ms ease;
}

.burger:hover {
    transform: translateY(-1px);
    box-shadow: 0 12px 20px var(--shadow);
}

.burger__icon {
    display: inline-flex;
    flex-direction: column;
    gap: 3px;
}

.burger__icon span {
    display: block;
    width: 18px;
    height: 2px;
    background: var(--text);
}
</style>
